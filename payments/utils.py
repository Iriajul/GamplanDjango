from django.utils import timezone
from datetime import timedelta
from .models import Subscription

def has_active_subscription_or_trial(user):
    # Check active Stripe subscription
    try:
        subscription = Subscription.objects.get(user=user)
        if subscription.is_active and subscription.current_period_end and subscription.current_period_end > timezone.now():
            return True
    except Subscription.DoesNotExist:
        pass

    # Check free trial period on User model
    now = timezone.now()
    if user.trial_start and user.trial_end and user.trial_start <= now <= user.trial_end:
        return True

    return False


def start_free_trial(user):
    trial_start = timezone.now()
    trial_end = trial_start + timedelta(days=7)

    # Update User trial fields and set account type to standard
    user.trial_start = trial_start
    user.trial_end = trial_end
    user.save(update_fields=['trial_start', 'trial_end'])

    # Create or update Subscription model for the user as 'standard'
    Subscription.objects.update_or_create(
        user=user,
        defaults={
            'is_active': True,
            'current_period_end': trial_end,
            'plan': 'standard',  # Make sure your Subscription model has this 'plan' field
        }
    )
