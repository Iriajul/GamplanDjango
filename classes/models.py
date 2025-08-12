from django.db import models
from django.conf import settings
from plans.models import Plan

class SavedClass(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    plan = models.OneToOneField(Plan, on_delete=models.CASCADE, related_name='saved_class')
    title = models.CharField(max_length=255)
    notes = models.TextField(blank=True, null=True)
    pinned_date = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'django"."saved_class'

    def __str__(self):
        return f"{self.title} - {self.user.email}"
