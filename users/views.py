from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import (
    UserSignupSerializer,
    ForgotPasswordRequestSerializer,
    ForgotPasswordVerifySerializer,
    SetNewPasswordSerializer,
    UserProfileSerializer,
    UserUpdateSerializer,
    AboutDetailsSerializer
)
from payments.utils import start_free_trial
from django.utils import timezone
from datetime import timedelta
from .models import User

# User signup
class UserSignupView(APIView):
    def post(self, request):
        serializer = UserSignupSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "User registered successfully."}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Protected view for testing JWT
class ProtectedView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"message": "You are authenticated!"})

# Accept free trial
class AcceptFreeTrialView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        if user.trial_start and user.trial_end and timezone.now() < user.trial_end:
            return Response({"error": "Trial already active."}, status=status.HTTP_400_BAD_REQUEST)

        start_free_trial(user)

        return Response({
            "message": "Free trial started successfully.",
            "trial_start": user.trial_start,
            "trial_end": user.trial_end,
            "account_type": user.account_type,
        }, status=status.HTTP_200_OK)

# Request OTP for password reset
class ForgotPasswordRequestView(APIView):
    def post(self, request):
        serializer = ForgotPasswordRequestSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            response = Response({"message": "Verification code sent to email."})
            response.set_cookie(
                key='reset_email',
                value=request.data['email'],
                httponly=True,
                max_age=600,
                samesite='Lax'
            )
            return response
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Verify OTP
class ForgotPasswordVerifyView(APIView):
    def post(self, request):
        email = request.COOKIES.get('reset_email')
        if not email:
            return Response({"error": "Email not found in session. Please request OTP again."}, status=status.HTTP_400_BAD_REQUEST)

        code = request.data.get('code', '').strip()
        serializer = ForgotPasswordVerifySerializer(data={'code': code})
        serializer.context['request'] = request

        if serializer.is_valid():
            try:
                user = User.objects.get(email=email, reset_code=code)
            except User.DoesNotExist:
                return Response({"error": "Invalid code for the current session."}, status=status.HTTP_400_BAD_REQUEST)

            if user.reset_code_created and timezone.now() > user.reset_code_created + timedelta(minutes=10):
                return Response({"error": "The reset code has expired. Please request a new one."}, status=status.HTTP_400_BAD_REQUEST)

            response = Response({"message": "Verification code is valid."})
            response.set_cookie(
                key='otp_verified',
                value='true',
                httponly=True,
                max_age=600,
                samesite='Lax'
            )
            return response
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Reset password after OTP verification
class ResetPasswordView(APIView):
    def post(self, request):
        email = request.COOKIES.get('reset_email')
        otp_verified = request.COOKIES.get('otp_verified')

        if not email or otp_verified != 'true':
            return Response({"error": "Session expired or unauthorized. Please verify OTP again."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = SetNewPasswordSerializer(data=request.data, context={'email_from_cookie': email})
        if serializer.is_valid():
            serializer.save()
            response = Response({"message": "Password has been reset successfully."})
            response.delete_cookie('reset_email')
            response.delete_cookie('otp_verified')
            return response
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Logout
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh_token")
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"detail": "Logout successful."}, status=status.HTTP_205_RESET_CONTENT)
        except Exception:
            return Response({"error": "Invalid refresh token."}, status=status.HTTP_400_BAD_REQUEST)

# User profile
class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)

    def put(self, request):
        serializer = UserUpdateSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# About/Details update
class AboutDetailsUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AboutDetailsSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "About and details saved successfully."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
