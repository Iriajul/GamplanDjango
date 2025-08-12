from django.db import models
from django.conf import settings

class Subscription(models.Model):
    PLAN_CHOICES = [
        ('standard', 'Standard'),  # free trial users
        ('pro', 'Pro'),            # paid subscribers
    ]

    PLAN_TYPE_CHOICES = [
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
        (None, 'N/A'),  # For free trial or if not set
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    stripe_customer_id = models.CharField(max_length=255, blank=True, null=True)
    stripe_subscription_id = models.CharField(max_length=255, blank=True, null=True)
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default='standard')
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPE_CHOICES, blank=True, null=True, default=None)
    is_active = models.BooleanField(default=False)
    current_period_end = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"Subscription for {self.user.email}"

    class Meta:
        db_table = 'django"."subscriptions'
