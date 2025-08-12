from rest_framework import serializers
from .models import SavedClass

class SavedClassSerializer(serializers.ModelSerializer):
    title = serializers.SerializerMethodField()

    class Meta:
        model = SavedClass
        fields = ['id', 'title', 'notes', 'pinned_date', 'created_at', 'plan']

    def get_title(self, obj):
        return obj.plan.title


class SetTitleSerializer(serializers.Serializer):
    plan_id = serializers.IntegerField()
    title = serializers.CharField()
