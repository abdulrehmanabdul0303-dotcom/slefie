"""
URL configuration for user authentication.
"""
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    # CSRF token
    path('csrf/', views.csrf_token_view, name='csrf_token'),
    
    # Authentication
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # User profile
    path('me/', views.me_view, name='user_profile'),
    path('profile/', views.UserProfileView.as_view(), name='user_profile_update'),
    
    # Password management
    path('password/change/', views.PasswordChangeView.as_view(), name='password_change'),
    path('password/reset/', views.PasswordResetRequestView.as_view(), name='password_reset_request'),
    path('password/reset/confirm/', views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    
    # Email verification
    path('verify/', views.EmailVerificationView.as_view(), name='email_verification'),
    path('verify/resend/', views.ResendVerificationView.as_view(), name='resend_verification'),
    
    # OAuth
    path('google/', views.GoogleOAuthView.as_view(), name='google_oauth'),
    
    # Account management
    path('delete/', views.DeleteAccountView.as_view(), name='delete_account'),
]