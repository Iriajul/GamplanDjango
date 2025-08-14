from rest_framework import serializers
from .models import User
from django.utils import timezone
from datetime import timedelta
import random
from django.core.mail import send_mail
from django.conf import settings

# Serializers for user registration and password reset functionalities
class UserSignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)
    agree_terms = serializers.BooleanField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'confirm_password', 'agree_terms']

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match.")
        if not data.get('agree_terms'):
            raise serializers.ValidationError("You must agree to the Terms & Privacy Policy.")
        return data

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        validated_data.pop('agree_terms')
        return User.objects.create_user(**validated_data)

# Request OTP for password reset
class ForgotPasswordRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("User with this email does not exist.")
        return value

    def save(self):
        email = self.validated_data['email']
        user = User.objects.get(email=email)
        code = str(random.randint(100000, 999999))
        user.reset_code = code
        user.reset_code_created = timezone.now()
        user.save()

        send_mail(
            subject="Your Password Reset Code",
            message=f"Hi {user.username},\n\nYour password reset code is: {code}\n\nThis code will expire in 10 minutes.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
        return code

# Verify the OTP code
class ForgotPasswordVerifySerializer(serializers.Serializer):
    code = serializers.CharField(max_length=6)

    def validate(self, data):
        try:
            user = User.objects.get(reset_code=data['code'])
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid code.")

        if user.reset_code_created and timezone.now() > user.reset_code_created + timedelta(minutes=10):
            raise serializers.ValidationError("The reset code has expired. Please request a new one.")

        # Store the email in the context (view will put it into a cookie)
        self.context['verified_email'] = user.email
        return data

# Set new password after OTP verification
class SetNewPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match.")

        email = self.context.get('email_from_cookie')
        if not email:
            raise serializers.ValidationError("Session expired. Please verify the OTP again.")

        try:
            user = User.objects.get(email=email)
            if not user.reset_code:
                raise serializers.ValidationError("OTP not verified or already used.")
        except User.DoesNotExist:
            raise serializers.ValidationError("User does not exist.")
        return data

    def save(self):
        email = self.context.get('email_from_cookie')
        user = User.objects.get(email=email)
        user.set_password(self.validated_data['new_password'])
        user.reset_code = None
        user.reset_code_created = None
        user.save()
        return user
    
# User profile serializers    
class UserProfileSerializer(serializers.ModelSerializer):
    """For viewing profile info with full CDN URL"""
    profile_picture = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['username', 'email', 'about', 'account_type', 'profile_picture']  
        read_only_fields = ['email', 'account_type']

    def get_profile_picture(self, obj):
        if obj.profile_picture:
            # Prepend BunnyCDN URL
            return f"{settings.BUNNY_CDN_URL}/{obj.profile_picture}"
        return None
    
# Serializer for updating about and details fields
class AboutDetailsSerializer(serializers.ModelSerializer):
    """For popup about/details editing only"""
    class Meta:
        model = User
        fields = ['about', 'details']
        extra_kwargs = {
            'about': {'required': False},
            'details': {'required': False},
        }

class UserUpdateSerializer(serializers.ModelSerializer):
    """For updating profile fields"""
    class Meta:
        model = User
        fields = ['username', 'about', 'profile_picture']
        extra_kwargs = {
            'username': {'required': False},
            'about': {'required': False},
            'profile_picture': {'required': False},
        }
    
    # Prepend BunnyCDN URL when updating profile_picture
    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.profile_picture:
            data['profile_picture'] = f"{settings.BUNNY_CDN_URL}/{instance.profile_picture}"
        return data        