from django.db import models
from django.conf import settings
from django.contrib.postgres.fields import ArrayField

class Plan(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=255, default="Untitled Plan")
    conversation = models.JSONField(default=list)
    is_saved = models.BooleanField(default=False)
    pinned_date = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} - {self.user.email}"

    class Meta:
        db_table = 'django"."plan' 
   
    
