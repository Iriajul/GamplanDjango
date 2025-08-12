from rest_framework import serializers
from .models import Plan


class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = '__all__'
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class ChatMessageSerializer(serializers.Serializer):
    plan_id = serializers.IntegerField(required=False)  # optional, reserved for future
    message = serializers.CharField()


class PlanSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = ['id', 'title', 'is_saved', 'pinned_date', 'created_at', 'updated_at']

