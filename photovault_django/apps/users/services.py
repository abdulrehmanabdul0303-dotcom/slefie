"""
Services for user management.
"""
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import secrets

from .models import EmailVerificationToken


class EmailService:
    """
    Service for sending emails.
    """
    
    @staticmethod
    def send_verification_email(user):
        """
        Send email verification email.
        """
        # Create verification token
        token = secrets.token_urlsafe(32)
        expires_at = timezone.now() + timedelta(hours=24)
        
        EmailVerificationToken.objects.create(
            user=user,
            token=token,
            expires_at=expires_at
        )
        
        # Determine frontend URL
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
        verification_url = f"{frontend_url}/auth/verify-email?token={token}"
        
        # Send email
        subject = 'Verify your PhotoVault account'
        
        # HTML email template
        html_message = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Verify Your Email</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #007bff; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background: #f9f9f9; }}
                .button {{ display: inline-block; padding: 12px 24px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; }}
                .footer {{ padding: 20px; text-align: center; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>PhotoVault</h1>
                </div>
                <div class="content">
                    <h2>Verify Your Email Address</h2>
                    <p>Hi {user.name or user.email},</p>
                    <p>Thank you for creating a PhotoVault account! Please click the button below to verify your email address:</p>
                    <p style="text-align: center; margin: 30px 0;">
                        <a href="{verification_url}" class="button">Verify Email Address</a>
                    </p>
                    <p>Or copy and paste this link into your browser:</p>
                    <p style="word-break: break-all; background: #eee; padding: 10px; border-radius: 3px;">
                        {verification_url}
                    </p>
                    <p><strong>This link will expire in 24 hours.</strong></p>
                    <p>If you didn't create an account, please ignore this email.</p>
                </div>
                <div class="footer">
                    <p>Best regards,<br>The PhotoVault Team</p>
                    <p>This is an automated message, please do not reply.</p>
                </div>
            </div>
        </body>
        </html>
        '''
        
        # Plain text fallback
        text_message = f'''
        Hi {user.name or user.email},
        
        Thank you for creating a PhotoVault account! Please click the link below to verify your email address:
        
        {verification_url}
        
        This link will expire in 24 hours.
        
        If you didn't create an account, please ignore this email.
        
        Best regards,
        The PhotoVault Team
        '''
        
        try:
            from django.core.mail import EmailMultiAlternatives
            
            msg = EmailMultiAlternatives(
                subject=subject,
                body=text_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email]
            )
            msg.attach_alternative(html_message, "text/html")
            msg.send()
            
            return True
        except Exception as e:
            # Log error but don't expose details
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to send verification email to {user.email}: {e}")
            return False
    
    @staticmethod
    def send_password_reset_email(user, token):
        """
        Send password reset email.
        """
        # Determine frontend URL
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
        reset_url = f"{frontend_url}/auth/reset-password?token={token}"
        
        subject = 'Reset your PhotoVault password'
        
        # HTML email template
        html_message = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Reset Your Password</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #dc3545; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background: #f9f9f9; }}
                .button {{ display: inline-block; padding: 12px 24px; background: #dc3545; color: white; text-decoration: none; border-radius: 5px; }}
                .footer {{ padding: 20px; text-align: center; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>PhotoVault</h1>
                </div>
                <div class="content">
                    <h2>Reset Your Password</h2>
                    <p>Hi {user.name or user.email},</p>
                    <p>We received a request to reset your PhotoVault password. Click the button below to create a new password:</p>
                    <p style="text-align: center; margin: 30px 0;">
                        <a href="{reset_url}" class="button">Reset Password</a>
                    </p>
                    <p>Or copy and paste this link into your browser:</p>
                    <p style="word-break: break-all; background: #eee; padding: 10px; border-radius: 3px;">
                        {reset_url}
                    </p>
                    <p><strong>This link will expire in 1 hour.</strong></p>
                    <p>If you didn't request a password reset, please ignore this email. Your password will remain unchanged.</p>
                </div>
                <div class="footer">
                    <p>Best regards,<br>The PhotoVault Team</p>
                    <p>This is an automated message, please do not reply.</p>
                </div>
            </div>
        </body>
        </html>
        '''
        
        # Plain text fallback
        text_message = f'''
        Hi {user.name or user.email},
        
        We received a request to reset your PhotoVault password. Click the link below to create a new password:
        
        {reset_url}
        
        This link will expire in 1 hour.
        
        If you didn't request a password reset, please ignore this email. Your password will remain unchanged.
        
        Best regards,
        The PhotoVault Team
        '''
        
        try:
            from django.core.mail import EmailMultiAlternatives
            
            msg = EmailMultiAlternatives(
                subject=subject,
                body=text_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email]
            )
            msg.attach_alternative(html_message, "text/html")
            msg.send()
            
            return True
        except Exception as e:
            # Log error but don't expose details
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to send password reset email to {user.email}: {e}")
            return False

class EncryptionService:
    """
    Service for handling user data encryption.
    """
    
    @staticmethod
    def generate_dek():
        """
        Generate a Data Encryption Key for the user.
        """
        from cryptography.fernet import Fernet
        return Fernet.generate_key().decode('utf-8')
    
    @staticmethod
    def encrypt_dek(dek, user_password):
        """
        Encrypt the DEK with user's password.
        """
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
        from cryptography.fernet import Fernet
        import base64
        import os
        
        # Generate salt
        salt = os.urandom(16)
        
        # Derive key from password
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(user_password.encode()))
        
        # Encrypt DEK
        fernet = Fernet(key)
        encrypted_dek = fernet.encrypt(dek.encode())
        
        # Combine salt and encrypted DEK
        combined = base64.b64encode(salt + encrypted_dek).decode('utf-8')
        return combined
    
    @staticmethod
    def decrypt_dek(encrypted_dek, user_password):
        """
        Decrypt the DEK with user's password.
        """
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
        from cryptography.fernet import Fernet
        import base64
        
        try:
            # Decode combined data
            combined = base64.b64decode(encrypted_dek.encode())
            salt = combined[:16]
            encrypted_data = combined[16:]
            
            # Derive key from password
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(user_password.encode()))
            
            # Decrypt DEK
            fernet = Fernet(key)
            dek = fernet.decrypt(encrypted_data).decode('utf-8')
            return dek
        except Exception:
            raise ValueError("Invalid password or corrupted DEK")