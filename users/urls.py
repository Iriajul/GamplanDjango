from django.urls import path
from .views import (
    UserSignupView,
    ForgotPasswordRequestView,
    ForgotPasswordVerifyView,
    ResetPasswordView,
    LogoutView,
    ProtectedView,
    AcceptFreeTrialView,
    UserProfileView,
    AboutDetailsUpdateView
)
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('signup/', UserSignupView.as_view(), name='user-signup'),
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('forgot-password/', ForgotPasswordRequestView.as_view(), name='forgot-password'), 
    path('verify-code/', ForgotPasswordVerifyView.as_view(), name='verify-code'),            
    path('reset-password/', ResetPasswordView.as_view(), name='reset-password'),             
    path('protected/', ProtectedView.as_view(), name='protected'),
    path('logout/', LogoutView.as_view(), name='user-logout'),
    path('trial/accept/', AcceptFreeTrialView.as_view(), name='accept-free-trial'),
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    path('profile/about-details/', AboutDetailsUpdateView.as_view(), name='about-details'),
]
