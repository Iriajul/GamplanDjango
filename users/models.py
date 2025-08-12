from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
from datetime import timedelta

class UserManager(BaseUserManager):
    def create_user(self, username, email, password=None):
        if not email:
            raise ValueError('Users must have an email address')
        email = self.normalize_email(email)
        user = self.model(username=username, email=email)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password):
        user = self.create_user(username, email, password)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    reset_code = models.CharField(max_length=6, blank=True, null=True)
    reset_code_created = models.DateTimeField(blank=True, null=True)
    

    # Free trial fields
    trial_start = models.DateTimeField(blank=True, null=True)
    trial_end = models.DateTimeField(blank=True, null=True)

    # Profile related fields
    about = models.TextField(blank=True, null=True)
    details = models.TextField(blank=True, null=True)  # For popup extra info, not shown on profile page
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    objects = UserManager()

    class Meta:
        db_table = 'django"."users'

    def __str__(self):
        return self.email

    def is_trial_active(self):
        """Returns True if user is currently in free trial period."""
        now = timezone.now()
        return self.trial_end is not None and now <= self.trial_end

    @property
    def account_type(self):
        """
        Dynamically returns the user's account type:
         - 'Pro' if user has an active paid subscription
         - 'Standard' if user is on active free trial or standard subscription
         - 'Free' otherwise
        """
        now = timezone.now()

        # Import here to avoid circular import issues
        from payments.models import Subscription

        try:
            subscription = Subscription.objects.get(user=self)
            if subscription.is_active and subscription.current_period_end and subscription.current_period_end > now:
                if subscription.plan == 'pro':
                    return 'Pro'
                elif subscription.plan == 'standard':
                    return 'Standard'
        except Subscription.DoesNotExist:
            pass

        # Check free trial
        if self.is_trial_active():
            return 'Standard'

        # Default fallback
        return 'Free'
