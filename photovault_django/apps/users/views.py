"""
Views for user authentication and management.
"""
from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import login, logout
from django.utils import timezone
from django.conf import settings
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import secrets
from datetime import timedelta

from .models import User, EmailVerificationToken, PasswordResetToken
from .serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    UserSerializer,
    UserUpdateSerializer,
    PasswordChangeSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    EmailVerificationSerializer,
    GoogleOAuthSerializer,
)
from .services import EmailService


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def csrf_token_view(request):
    """
    Get CSRF token for frontend.
    """
    from django.middleware.csrf import get_token
    return Response({
        'csrfToken': get_token(request)
    })


@method_decorator(csrf_exempt, name='dispatch')
class RegisterView(APIView):
    """
    User registration endpoint.
    """
    permission_classes = [permissions.AllowAny]
    
    @method_decorator(ratelimit(key='ip', rate='5/m', method='POST'))
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Send verification email
            EmailService.send_verification_email(user)
            
            return Response({
                'message': 'Registration successful. Please check your email to verify your account.',
                'user_id': user.id
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(csrf_exempt, name='dispatch')
class LoginView(APIView):
    """
    User login endpoint.
    """
    permission_classes = [permissions.AllowAny]
    
    @method_decorator(ratelimit(key='ip', rate='10/m', method='POST'))
    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            # Check if email is verified
            if not user.email_verified:
                return Response({
                    'detail': 'Email not verified. Please check your email and verify your account.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            access_token = refresh.access_token
            
            # Update last login
            user.last_login = timezone.now()
            user.save(update_fields=['last_login'])
            
            return Response({
                'access_token': str(access_token),
                'refresh_token': str(refresh),
                'user': UserSerializer(user).data
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    """
    User logout endpoint.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh_token')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            
            return Response({'message': 'Logout successful'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    Get and update user profile.
    """
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user
    
    def get_serializer_class(self):
        if self.request.method == 'PATCH':
            return UserUpdateSerializer
        return UserSerializer


class PasswordChangeView(APIView):
    """
    Change user password.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            
            return Response({'message': 'Password changed successfully'}, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(csrf_exempt, name='dispatch')
class PasswordResetRequestView(APIView):
    """
    Request password reset.
    """
    permission_classes = [permissions.AllowAny]
    
    @method_decorator(ratelimit(key='ip', rate='3/m', method='POST'))
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            
            try:
                user = User.objects.get(email=email)
                
                # Create reset token
                token = secrets.token_urlsafe(32)
                expires_at = timezone.now() + timedelta(hours=1)
                
                PasswordResetToken.objects.create(
                    user=user,
                    token=token,
                    expires_at=expires_at
                )
                
                # Send reset email
                EmailService.send_password_reset_email(user, token)
                
            except User.DoesNotExist:
                pass  # Don't reveal if email exists
            
            return Response({
                'message': 'If the email exists, a password reset link has been sent.'
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(csrf_exempt, name='dispatch')
class PasswordResetConfirmView(APIView):
    """
    Confirm password reset.
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if serializer.is_valid():
            token = serializer.validated_data['token']
            new_password = serializer.validated_data['new_password']
            
            try:
                reset_token = PasswordResetToken.objects.get(token=token)
                
                if not reset_token.is_valid:
                    return Response({
                        'error': 'Invalid or expired token'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Reset password
                user = reset_token.user
                user.set_password(new_password)
                user.unlock_account()  # Unlock account if locked
                user.save()
                
                # Mark token as used
                reset_token.used = True
                reset_token.save()
                
                return Response({
                    'message': 'Password reset successful'
                }, status=status.HTTP_200_OK)
                
            except PasswordResetToken.DoesNotExist:
                return Response({
                    'error': 'Invalid token'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(csrf_exempt, name='dispatch')
class EmailVerificationView(APIView):
    """
    Verify email address.
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = EmailVerificationSerializer(data=request.data)
        if serializer.is_valid():
            token = serializer.validated_data['token']
            
            try:
                verification_token = EmailVerificationToken.objects.get(token=token)
                
                if not verification_token.is_valid:
                    return Response({
                        'error': 'Invalid or expired token'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Verify email
                user = verification_token.user
                user.email_verified = True
                user.save()
                
                # Mark token as used
                verification_token.used = True
                verification_token.save()
                
                return Response({
                    'message': 'Email verified successfully'
                }, status=status.HTTP_200_OK)
                
            except EmailVerificationToken.DoesNotExist:
                return Response({
                    'error': 'Invalid token'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(csrf_exempt, name='dispatch')
class ResendVerificationView(APIView):
    """
    Resend email verification.
    """
    permission_classes = [permissions.AllowAny]
    
    @method_decorator(ratelimit(key='ip', rate='3/m', method='POST'))
    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({
                'error': 'Email is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(email=email)
            if user.email_verified:
                return Response({
                    'message': 'Email is already verified'
                }, status=status.HTTP_200_OK)
            
            # Send verification email
            EmailService.send_verification_email(user)
            
        except User.DoesNotExist:
            pass  # Don't reveal if email exists
        
        return Response({
            'message': 'If the email exists and is not verified, a verification link has been sent.'
        }, status=status.HTTP_200_OK)


@method_decorator(csrf_exempt, name='dispatch')
class GoogleOAuthView(APIView):
    """
    Google OAuth authentication.
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = GoogleOAuthSerializer(data=request.data)
        if serializer.is_valid():
            access_token = serializer.validated_data['access_token']
            
            try:
                # Verify Google access token
                google_user_info = self.verify_google_token(access_token)
                
                if not google_user_info:
                    return Response({
                        'error': 'Invalid Google access token'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Extract user information
                google_id = google_user_info.get('id')
                email = google_user_info.get('email')
                name = google_user_info.get('name', email.split('@')[0])
                
                # Check if user exists with this Google ID
                try:
                    user = User.objects.get(google_id=google_id)
                except User.DoesNotExist:
                    # Check if user exists with this email
                    try:
                        user = User.objects.get(email=email)
                        # Link Google account to existing user
                        user.google_id = google_id
                        user.email_verified = True  # Google emails are verified
                        user.save()
                    except User.DoesNotExist:
                        # Create new user
                        from .services import EncryptionService
                        
                        # Generate a random password for Google users
                        import secrets
                        random_password = secrets.token_urlsafe(32)
                        
                        # Generate and encrypt DEK
                        dek = EncryptionService.generate_dek()
                        encrypted_dek = EncryptionService.encrypt_dek(dek, random_password)
                        
                        user = User.objects.create_user(
                            username=email,
                            email=email,
                            name=name,
                            google_id=google_id,
                            email_verified=True,
                            dek_encrypted_b64=encrypted_dek
                        )
                        user.set_password(random_password)
                        user.save()
                
                # Generate JWT tokens
                from rest_framework_simplejwt.tokens import RefreshToken
                refresh = RefreshToken.for_user(user)
                
                return Response({
                    'access_token': str(refresh.access_token),
                    'refresh_token': str(refresh),
                    'user': UserSerializer(user).data
                }, status=status.HTTP_200_OK)
                
            except Exception as e:
                return Response({
                    'error': 'Google OAuth authentication failed',
                    'details': str(e)
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def verify_google_token(self, access_token):
        """
        Verify Google access token and get user info.
        """
        try:
            import requests
            
            # Verify token with Google
            response = requests.get(
                f'https://www.googleapis.com/oauth2/v1/userinfo?access_token={access_token}',
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return None
                
        except Exception as e:
            print(f"Google token verification error: {e}")
            return None


class DeleteAccountView(APIView):
    """
    Delete user account.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def delete(self, request):
        user = request.user
        
        # TODO: Implement proper account deletion
        # This should delete all user data including images, albums, etc.
        
        user.delete()
        
        return Response({
            'message': 'Account deleted successfully'
        }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def me_view(request):
    """
    Get current user information.
    """
    serializer = UserSerializer(request.user)
    return Response(serializer.data)