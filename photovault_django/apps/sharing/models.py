"""
Sharing models for PhotoVault.
"""
from django.db import models
from django.conf import settings
from django.utils import timezone
import hashlib
import secrets


class PublicShare(models.Model):
    """
    Public share links for albums.
    """
    # Creator of the share
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='shares')
    album = models.ForeignKey('albums.Album', on_delete=models.CASCADE, related_name='shares')
    
    # Share token (hashed for security)
    token_hash = models.CharField(max_length=64, unique=True, db_index=True)
    raw_token = models.CharField(max_length=32, null=True, blank=True)  # Store temporarily for response
    
    # Share settings
    SCOPE_CHOICES = [
        ('view', 'View Only'),
        ('download', 'View and Download'),
    ]
    scope = models.CharField(max_length=32, choices=SCOPE_CHOICES, default='view')
    expires_at = models.DateTimeField()
    revoked = models.BooleanField(default=False)
    
    # Usage tracking
    max_views = models.IntegerField(null=True, blank=True)
    view_count = models.IntegerField(default=0)
    
    # Share Links 2.0 Features
    watermark_enabled = models.BooleanField(default=False)
    watermark_text = models.CharField(max_length=100, blank=True)
    watermark_opacity = models.FloatField(default=0.3)
    
    # Analytics
    total_views = models.IntegerField(default=0)
    unique_visitors = models.IntegerField(default=0)
    last_accessed = models.DateTimeField(null=True, blank=True)
    
    # Security restrictions
    ip_lock = models.CharField(max_length=64, null=True, blank=True)
    user_agent_lock = models.CharField(max_length=256, null=True, blank=True)
    
    # Face-based sharing
    require_face = models.BooleanField(default=False)
    SHARE_TYPE_CHOICES = [
        ('PUBLIC', 'Public Link'),
        ('FACE_CLAIM', 'Face Verification Required'),
    ]
    share_type = models.CharField(max_length=20, choices=SHARE_TYPE_CHOICES, default='PUBLIC')
    
    # Face claim verification
    face_claim_verified = models.BooleanField(default=False)
    face_claim_embedding_json = models.JSONField(null=True, blank=True)
    face_claim_attempts = models.IntegerField(default=0)
    face_claim_last_attempt = models.DateTimeField(null=True, blank=True)
    face_claim_lock_until = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'public_shares'
        indexes = [
            models.Index(fields=['token_hash']),
            models.Index(fields=['created_by', 'created_at']),
            models.Index(fields=['expires_at', 'revoked']),
        ]
    
    def __str__(self):
        return f"Share: {self.album.name} by {self.created_by.email}"
    
    @property
    def user(self):
        """Alias for created_by for compatibility."""
        return self.created_by
    
    @property
    def is_expired(self):
        """Check if share link is expired."""
        return timezone.now() > self.expires_at
    
    @property
    def is_valid(self):
        """Check if share link is valid (not revoked, not expired, under view limit)."""
        if self.revoked or self.is_expired:
            return False
        
        if self.max_views and self.view_count >= self.max_views:
            return False
        
        return True
    
    @property
    def views_remaining(self):
        """Get number of views remaining."""
        if not self.max_views:
            return "Unlimited"
        return max(0, self.max_views - self.view_count)
    
    @property
    def time_remaining(self):
        """Get time remaining until expiry."""
        if not self.expires_at:
            return "Never expires"
        
        remaining = self.expires_at - timezone.now()
        if remaining.total_seconds() <= 0:
            return "Expired"
        
        days = remaining.days
        hours, remainder = divmod(remaining.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        
        if days > 0:
            return f"{days} days, {hours} hours"
        elif hours > 0:
            return f"{hours} hours, {minutes} minutes"
        else:
            return f"{minutes} minutes"
    
    def generate_token(self):
        """Generate a new share token."""
        raw_token = secrets.token_urlsafe(24)
        self.raw_token = raw_token
        self.token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        self.save(update_fields=['raw_token', 'token_hash'])
        return raw_token
    
    def verify_token(self, token):
        """Verify a token against the stored hash."""
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        return self.token_hash == token_hash
    
    def increment_view_count(self, ip_address=None, user_agent=None):
        """Increment view count and log access."""
        if not self.is_valid:
            return False
        
        self.view_count += 1
        self.total_views += 1
        self.last_accessed = timezone.now()
        self.save(update_fields=['view_count', 'total_views', 'last_accessed'])
        
        # Log the access
        if ip_address:
            ShareAccess.objects.create(
                share=self,
                ip_address=ip_address,
                user_agent=user_agent or '',
            )
        
        return True
    
    def generate_qr_code(self, base_url="https://photovault.com"):
        """Generate QR code for the share link."""
        import qrcode
        from io import BytesIO
        import base64
        
        share_url = f"{base_url}/share/{self.raw_token}"
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(share_url)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return f"data:image/png;base64,{img_str}"
    
    def extend_expiry(self, hours=24):
        """Extend share expiry by specified hours."""
        from datetime import timedelta
        self.expires_at += timedelta(hours=hours)
        self.save(update_fields=['expires_at'])
    
    def reset_view_count(self):
        """Reset view count (admin function)."""
        self.view_count = 0
        self.save(update_fields=['view_count'])
    
    def revoke(self):
        """Revoke the share link."""
        self.revoked = True
        self.save(update_fields=['revoked'])


class ShareAccess(models.Model):
    """
    Track access to shared albums.
    """
    share = models.ForeignKey(PublicShare, on_delete=models.CASCADE, related_name='access_logs')
    ip_address = models.GenericIPAddressField()
    user_agent = models.CharField(max_length=512, blank=True)
    accessed_at = models.DateTimeField(auto_now_add=True)
    
    # Face verification details (if applicable)
    face_verified = models.BooleanField(default=False)
    face_confidence = models.FloatField(null=True, blank=True)
    
    class Meta:
        db_table = 'share_access_logs'
        indexes = [
            models.Index(fields=['share', 'accessed_at']),
            models.Index(fields=['ip_address', 'accessed_at']),
        ]
    
    def __str__(self):
        return f"Access to {self.share.album.name} from {self.ip_address}"


class FaceClaimSession(models.Model):
    """
    Temporary session for face claim verification.
    """
    share = models.ForeignKey(PublicShare, on_delete=models.CASCADE, related_name='face_claim_sessions')
    session_token = models.CharField(max_length=64, unique=True, db_index=True)
    
    # Face data
    face_embedding_json = models.JSONField()
    verified_face_id = models.CharField(max_length=255, null=True, blank=True)
    
    # Session details
    ip_address = models.GenericIPAddressField()
    user_agent = models.CharField(max_length=512, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    
    class Meta:
        db_table = 'face_claim_sessions'
        indexes = [
            models.Index(fields=['session_token']),
            models.Index(fields=['share', 'created_at']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f"Face claim session for {self.share.album.name}"
    
    @property
    def is_expired(self):
        """Check if session is expired."""
        return timezone.now() > self.expires_at
    
    @property
    def is_valid(self):
        """Check if session is valid."""
        return not self.is_expired


class FaceClaimAudit(models.Model):
    """
    Audit log for face claim attempts.
    """
    share = models.ForeignKey(PublicShare, on_delete=models.CASCADE, related_name='face_claim_audits')
    
    ATTEMPT_TYPE_CHOICES = [
        ('FACE_UPLOAD', 'Face Upload'),
        ('FACE_CAMERA', 'Face Camera'),
        ('VERIFY', 'Verification'),
    ]
    attempt_type = models.CharField(max_length=20, choices=ATTEMPT_TYPE_CHOICES)
    success = models.BooleanField()
    
    # Face matching details
    confidence_score = models.FloatField(null=True, blank=True)
    matched_face_id = models.CharField(max_length=255, null=True, blank=True)
    
    # Request details
    ip_address = models.GenericIPAddressField()
    user_agent = models.CharField(max_length=512, blank=True)
    
    # Timestamp
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'face_claim_audits'
        indexes = [
            models.Index(fields=['share', 'created_at']),
            models.Index(fields=['ip_address', 'created_at']),
            models.Index(fields=['success', 'created_at']),
        ]
    
    def __str__(self):
        status = "Success" if self.success else "Failed"
        return f"Face claim {status} for {self.share.album.name}"