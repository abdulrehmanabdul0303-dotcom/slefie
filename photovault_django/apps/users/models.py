"""
User models for PhotoVault.
"""
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from datetime import timedelta
import json


class User(AbstractUser):
    """
    Custom User model with PhotoVault-specific fields.
    """
    email = models.EmailField(unique=True, db_index=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    
    # OAuth fields
    google_id = models.CharField(max_length=255, unique=True, null=True, blank=True, db_index=True)
    
    # Encryption key for user's data
    dek_encrypted_b64 = models.TextField(help_text="Data Encryption Key (encrypted)")
    
    # Face recognition
    face_embedding_json = models.JSONField(null=True, blank=True)
    
    # Admin status
    is_admin = models.BooleanField(default=False)
    
    # Email verification
    email_verified = models.BooleanField(default=False)
    
    # Account lockout protection
    failed_login_attempts = models.IntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    class Meta:
        db_table = 'users'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['google_id']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return self.email
    
    @property
    def is_locked(self):
        """Check if account is currently locked."""
        if self.locked_until:
            return timezone.now() < self.locked_until
        return False
    
    def lock_account(self, duration_minutes=30):
        """Lock account for specified duration."""
        self.locked_until = timezone.now() + timedelta(minutes=duration_minutes)
        self.save(update_fields=['locked_until'])
    
    def unlock_account(self):
        """Unlock account and reset failed attempts."""
        self.failed_login_attempts = 0
        self.locked_until = None
        self.save(update_fields=['failed_login_attempts', 'locked_until'])
    
    def increment_failed_attempts(self):
        """Increment failed login attempts and lock if threshold reached."""
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= 5:
            self.lock_account()
        self.save(update_fields=['failed_login_attempts'])
    
    def reset_failed_attempts(self):
        """Reset failed login attempts on successful login."""
        if self.failed_login_attempts > 0:
            self.failed_login_attempts = 0
            self.save(update_fields=['failed_login_attempts'])
    
    @property
    def face_embedding(self):
        """Get face embedding as list."""
        if self.face_embedding_json:
            return json.loads(self.face_embedding_json) if isinstance(self.face_embedding_json, str) else self.face_embedding_json
        return None
    
    @face_embedding.setter
    def face_embedding(self, value):
        """Set face embedding from list."""
        if value is not None:
            self.face_embedding_json = json.dumps(value) if isinstance(value, list) else value
        else:
            self.face_embedding_json = None


class PersonCluster(models.Model):
    """
    Person clusters for face recognition grouping.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='person_clusters')
    name = models.CharField(max_length=255)
    face_embedding_json = models.JSONField()
    representative_face_id = models.CharField(max_length=255, null=True, blank=True)
    confidence_score = models.FloatField(default=0.0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'person_clusters'
        unique_together = ['user', 'name']
        indexes = [
            models.Index(fields=['user', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.name}"
    
    @property
    def label(self):
        """Alias for name field for compatibility."""
        return self.name
    
    @label.setter
    def label(self, value):
        """Alias for name field for compatibility."""
        self.name = value
    
    @property
    def face_embedding(self):
        """Get face embedding as list."""
        if self.face_embedding_json:
            return json.loads(self.face_embedding_json) if isinstance(self.face_embedding_json, str) else self.face_embedding_json
        return None
    
    @face_embedding.setter
    def face_embedding(self, value):
        """Set face embedding from list."""
        if value is not None:
            self.face_embedding_json = json.dumps(value) if isinstance(value, list) else value
        else:
            self.face_embedding_json = None


class EmailVerificationToken(models.Model):
    """
    Email verification tokens.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='verification_tokens')
    token = models.CharField(max_length=255, unique=True, db_index=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'email_verification_tokens'
    
    def __str__(self):
        return f"Verification token for {self.user.email}"
    
    @property
    def is_expired(self):
        """Check if token is expired."""
        return timezone.now() > self.expires_at
    
    @property
    def is_valid(self):
        """Check if token is valid (not used and not expired)."""
        return not self.used and not self.is_expired


class PasswordResetToken(models.Model):
    """
    Password reset tokens.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_reset_tokens')
    token = models.CharField(max_length=255, unique=True, db_index=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'password_reset_tokens'
    
    def __str__(self):
        return f"Password reset token for {self.user.email}"
    
    @property
    def is_expired(self):
        """Check if token is expired."""
        return timezone.now() > self.expires_at
    
    @property
    def is_valid(self):
        """Check if token is valid (not used and not expired)."""
        return not self.used and not self.is_expired