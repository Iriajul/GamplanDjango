from django.urls import path
from .views import CreateCheckoutSessionView, stripe_webhook, ManageSubscriptionView, UpdateSubscriptionView, CancelSubscriptionView

urlpatterns = [
    path('create-checkout-session/', CreateCheckoutSessionView.as_view(), name='create-checkout-session'),
    path('webhook/', stripe_webhook, name='stripe-webhook'),
    path('subscription/manage/', ManageSubscriptionView.as_view(), name='manage-subscription'),
    path('update-subscription/', UpdateSubscriptionView.as_view(), name='update-subscription'),
    path('cancel-subscription/', CancelSubscriptionView.as_view(), name='cancel-subscription'),
]
