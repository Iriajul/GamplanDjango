import os
import stripe
import logging
from datetime import datetime

from django.conf import settings
from django.http import HttpResponse
from django.utils.timezone import make_aware
from django.views.decorators.csrf import csrf_exempt

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions

from .models import Subscription
from .serializers import SubscriptionSerializer  # <-- import your serializer

stripe.api_key = settings.STRIPE_SECRET_KEY
logger = logging.getLogger(__name__)

# Load your Stripe price IDs from environment
MONTHLY_PRICE_ID = os.getenv('STRIPE_PRICE_MONTHLY')
YEARLY_PRICE_ID = os.getenv('STRIPE_PRICE_YEARLY')


class CreateCheckoutSessionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        price_id = request.data.get('price_id')  # should be monthly or yearly Stripe price ID

        try:
            # Create or retrieve Stripe customer
            if not hasattr(user, 'subscription') or not user.subscription.stripe_customer_id:
                customer = stripe.Customer.create(email=user.email)
                subscription, _ = Subscription.objects.get_or_create(user=user)
                subscription.stripe_customer_id = customer.id
                subscription.plan = "standard"  # default until payment confirmed
                subscription.plan_type = None
                subscription.save()
            else:
                customer = stripe.Customer.retrieve(user.subscription.stripe_customer_id)

            # Create Stripe Checkout session
            checkout_session = stripe.checkout.Session.create(
                customer=customer.id,
                payment_method_types=['card'],
                line_items=[{
                    'price': price_id,
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=settings.FRONTEND_DOMAIN + '/dashboard',
                cancel_url=settings.FRONTEND_DOMAIN + '/pricing',
            )
            return Response({'checkout_url': checkout_session.url})

        except Exception as e:
            logger.error(f"Error creating checkout session: {e}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ManageSubscriptionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        try:
            subscription = Subscription.objects.get(user=user)
        except Subscription.DoesNotExist:
            # Return default "free" or no subscription data
            default_data = {
                "plan": "standard",
                "plan_display": "Standard",
                "plan_type": None,
                "plan_type_display": "N/A",
                "is_active": False,
                "current_period_end": None,
                "price": "0$",
                "formatted_expiry": "N/A",
            }
            return Response(default_data, status=status.HTTP_200_OK)

        serializer = SubscriptionSerializer(subscription)
        return Response(serializer.data, status=status.HTTP_200_OK)


@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
    except (ValueError, stripe.error.SignatureVerificationError) as e:
        logger.error(f"Webhook signature verification failed: {e}")
        return HttpResponse(status=400)

    from users.models import User  # avoid circular import issues

    # Helper function to determine plan_type from price_id
    def get_plan_type_from_price(price_id):
        if price_id == MONTHLY_PRICE_ID:
            return 'monthly'
        elif price_id == YEARLY_PRICE_ID:
            return 'yearly'
        return None

    # Handle subscription created or updated
    if event['type'] in ['customer.subscription.created', 'customer.subscription.updated']:
        subscription_data = event['data']['object']
        logger.info(f"Received subscription event: {subscription_data}")

        stripe_customer_id = subscription_data.get('customer')
        stripe_subscription_id = subscription_data.get('id')
        is_active = subscription_data.get('status') == 'active'

        # Extract current_period_end and price_id from subscription items
        items = subscription_data.get('items', {}).get('data', [])
        current_period_end_ts = None
        price_id = None

        if items and isinstance(items, list):
            current_period_end_ts = items[0].get('current_period_end')
            price_info = items[0].get('price', {})
            price_id = price_info.get('id')

        current_period_end = (
            make_aware(datetime.fromtimestamp(current_period_end_ts))
            if current_period_end_ts else None
        )

        try:
            subscription = Subscription.objects.get(stripe_customer_id=stripe_customer_id)
        except Subscription.DoesNotExist:
            try:
                user = User.objects.get(subscription__stripe_customer_id=stripe_customer_id)
            except User.DoesNotExist:
                logger.warning(f"No user found for Stripe customer ID: {stripe_customer_id}")
                return HttpResponse(status=200)

            subscription = Subscription.objects.create(
                user=user,
                stripe_customer_id=stripe_customer_id,
                plan='standard',
                plan_type=None,
            )

        subscription.stripe_subscription_id = stripe_subscription_id
        subscription.is_active = is_active
        subscription.plan = 'pro' if is_active else 'standard'
        subscription.plan_type = get_plan_type_from_price(price_id)
        subscription.current_period_end = current_period_end
        subscription.save()

    # Handle invoice.paid to update current_period_end reliably
    elif event['type'] == 'invoice.paid':
        invoice = event['data']['object']
        subscription_id = invoice.get('subscription')

        if subscription_id:
            # Retrieve fresh subscription data from Stripe
            stripe_sub = stripe.Subscription.retrieve(subscription_id)
            current_period_end_ts = stripe_sub.get('current_period_end')
            current_period_end = (
                make_aware(datetime.fromtimestamp(current_period_end_ts))
                if current_period_end_ts else None
            )

            # Get the price_id from subscription items
            items = stripe_sub.get('items', {}).get('data', [])
            price_id = None
            if items and isinstance(items, list):
                price_info = items[0].get('price', {})
                price_id = price_info.get('id')

            try:
                subscription = Subscription.objects.get(stripe_subscription_id=subscription_id)
            except Subscription.DoesNotExist:
                logger.warning(f"No subscription found for Stripe subscription ID: {subscription_id}")
                return HttpResponse(status=200)

            subscription.current_period_end = current_period_end
            subscription.is_active = stripe_sub.get('status') == 'active'
            subscription.plan = 'pro' if subscription.is_active else 'standard'
            subscription.plan_type = get_plan_type_from_price(price_id)
            subscription.save()

    # Handle subscription cancellation
    elif event['type'] == 'customer.subscription.deleted':
        subscription_data = event['data']['object']
        stripe_customer_id = subscription_data.get('customer')

        try:
            subscription = Subscription.objects.get(stripe_customer_id=stripe_customer_id)
            subscription.is_active = False
            subscription.plan = 'standard'
            subscription.plan_type = None
            subscription.current_period_end = None
            subscription.save()
        except Subscription.DoesNotExist:
            logger.warning(f"Subscription to delete not found for Stripe customer ID: {stripe_customer_id}")

    return HttpResponse(status=200)

class UpdateSubscriptionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        new_price_id = request.data.get('price_id')
        if not new_price_id:
            return Response({'error': 'New price_id required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            subscription = Subscription.objects.get(user=user)
            stripe_sub_id = subscription.stripe_subscription_id
            if not stripe_sub_id:
                return Response({'error': 'No active subscription found'}, status=status.HTTP_400_BAD_REQUEST)

            # Retrieve current Stripe subscription
            stripe_sub = stripe.Subscription.retrieve(stripe_sub_id)

            # Assume only one subscription item
            sub_item_id = stripe_sub['items']['data'][0]['id']

            # Update subscription item to new price
            updated_sub = stripe.Subscription.modify(
                stripe_sub_id,
                items=[{
                    'id': sub_item_id,
                    'price': new_price_id,
                }],
                proration_behavior='create_prorations',  # prorate the change
            )

            return Response({'message': 'Subscription updated', 'subscription': updated_sub})

        except Subscription.DoesNotExist:
            return Response({'error': 'Subscription not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error updating subscription: {e}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class CancelSubscriptionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        try:
            subscription = Subscription.objects.get(user=user)
            stripe_sub_id = subscription.stripe_subscription_id
            if not stripe_sub_id:
                return Response({'error': 'No active subscription to cancel'}, status=status.HTTP_400_BAD_REQUEST)

            # Cancel subscription at period end
            canceled_sub = stripe.Subscription.modify(
                stripe_sub_id,
                cancel_at_period_end=True
            )

            return Response({'message': 'Subscription cancellation scheduled at period end', 'subscription': canceled_sub})

        except Subscription.DoesNotExist:
            return Response({'error': 'Subscription not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error cancelling subscription: {e}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
