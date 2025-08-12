from rest_framework import serializers
from .models import Subscription

class SubscriptionSerializer(serializers.ModelSerializer):
    plan_display = serializers.CharField(source='get_plan_display', read_only=True)
    plan_type_display = serializers.CharField(source='get_plan_type_display', read_only=True)
    price = serializers.SerializerMethodField()
    formatted_expiry = serializers.SerializerMethodField()

    class Meta:
        model = Subscription
        fields = [
            'plan',
            'plan_display',
            'plan_type',
            'plan_type_display',
            'is_active',
            'current_period_end',
            'price',
            'formatted_expiry',
        ]

    def get_price(self, obj):
        # Define prices for each plan_type; adjust amounts if needed
        price_map = {
            ('pro', 'monthly'): 10.50,
            ('pro', 'yearly'): 40.50,
            ('standard', None): 0.00,
        }
        amount = price_map.get((obj.plan, obj.plan_type), 0.00)
        return f"{amount}$"

    def get_formatted_expiry(self, obj):
        if obj.current_period_end:
            return obj.current_period_end.strftime("%m/%d/%y")
        return "N/A"


