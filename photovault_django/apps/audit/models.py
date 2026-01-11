"""
Audit logging models for tracking security events and user actions.
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import json

User = get_user_model()


class AuditEvent(models.Model):
    """
    Model for tracking security events and user actions.
    """
    
    # Event categories
    CATEGORY_CHOICES = [
        ('AUTH', 'Authentication'),
        ('MEDIA', 'Media Management'),
        ('ALBUM', 'Album Management'),
        ('SHARE', 'Sharing'),
        ('SECURITY', 'Security'),
        ('ADMIN', 'Administration'),
    ]
    
    # Event types
    EVENT_CHOICES = [
        # Authentication events
        ('LOGIN_SUCCESS', 'Login Success'),
        ('LOGIN_FAILED', 'Login Failed'),
        ('LOGOUT', 'Logout'),
        ('REGISTER', 'User Registration'),
        ('EMAIL_VERIFY', 'Email Verification'),
        ('PASSWORD_RESET_REQUEST', 'Password Reset Request'),
        ('PASSWORD_RESET_COMPLETE', 'Password Reset Complete'),
        ('ACCOUNT_LOCKED', 'Account Locked'),
        ('ACCOUNT_UNLOCKED', 'Account Unlocked'),
        
        # Media events
        ('MEDIA_UPLOAD', 'Media Upload'),
        ('MEDIA_DELETE', 'Media Delete'),
        ('MEDIA_VIEW', 'Media View'),
        ('MEDIA_DOWNLOAD', 'Media Download'),
        
        # Album events
        ('ALBUM_CREATE', 'Album Create'),
        ('ALBUM_DELETE', 'Album Delete'),
        ('ALBUM_MEMBER_ADD', 'Album Member Add'),
        ('ALBUM_MEMBER_REMOVE', 'Album Member Remove'),
        ('ALBUM_ROLE_CHANGE', 'Album Role Change'),
        
        # Sharing events
        ('SHARE_CREATE', 'Share Create'),
        ('SHARE_ACCESS', 'Share Access'),
        ('SHARE_DELETE', 'Share Delete'),
        
        # Security events
        ('SUSPICIOUS_ACTIVITY', 'Suspicious Activity'),
        ('RATE_LIMIT_HIT', 'Rate Limit Hit'),
        ('UNAUTHORIZED_ACCESS', 'Unauthorized Access'),
    ]
    
    # Core fields
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    event_type = models.CharField(max_length=30, choices=EVENT_CHOICES)
    
    # Request context
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    # Event details
    resource_type = models.CharField(max_length=50, blank=True)  # e.g., 'Album', 'Media'
    resource_id = models.CharField(max_length=100, blank=True)   # ID of the resource
    details = models.JSONField(default=dict, blank=True)        # Additional event data
    
    # Outcome
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)
    
    # Timestamp
    timestamp = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'audit_events'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['category', '-timestamp']),
            models.Index(fields=['event_type', '-timestamp']),
            models.Index(fields=['ip_address', '-timestamp']),
            models.Index(fields=['-timestamp']),
        ]
    
    def __str__(self):
        user_str = self.user.email if self.user else 'Anonymous'
        return f"{self.timestamp} - {user_str} - {self.event_type}"
    
    @classmethod
    def log_event(cls, event_type, user=None, request=None, resource_type='', 
                  resource_id='', details=None, success=True, error_message=''):
        """
        Convenience method to log an audit event.
        """
        # Determine category from event type
        category_map = {
            'LOGIN_SUCCESS': 'AUTH',
            'LOGIN_FAILED': 'AUTH',
            'LOGOUT': 'AUTH',
            'REGISTER': 'AUTH',
            'EMAIL_VERIFY': 'AUTH',
            'PASSWORD_RESET_REQUEST': 'AUTH',
            'PASSWORD_RESET_COMPLETE': 'AUTH',
            'ACCOUNT_LOCKED': 'SECURITY',
            'ACCOUNT_UNLOCKED': 'SECURITY',
            'MEDIA_UPLOAD': 'MEDIA',
            'MEDIA_DELETE': 'MEDIA',
            'MEDIA_VIEW': 'MEDIA',
            'MEDIA_DOWNLOAD': 'MEDIA',
            'ALBUM_CREATE': 'ALBUM',
            'ALBUM_DELETE': 'ALBUM',
            'ALBUM_MEMBER_ADD': 'ALBUM',
            'ALBUM_MEMBER_REMOVE': 'ALBUM',
            'ALBUM_ROLE_CHANGE': 'ALBUM',
            'SHARE_CREATE': 'SHARE',
            'SHARE_ACCESS': 'SHARE',
            'SHARE_DELETE': 'SHARE',
            'SUSPICIOUS_ACTIVITY': 'SECURITY',
            'RATE_LIMIT_HIT': 'SECURITY',
            'UNAUTHORIZED_ACCESS': 'SECURITY',
        }
        
        category = category_map.get(event_type, 'SECURITY')
        
        # Extract request context
        ip_address = None
        user_agent = ''
        
        if request:
            # Get real IP (considering proxies)
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip_address = x_forwarded_for.split(',')[0].strip()
            else:
                ip_address = request.META.get('REMOTE_ADDR')
            
            user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Create audit event
        return cls.objects.create(
            user=user,
            category=category,
            event_type=event_type,
            ip_address=ip_address,
            user_agent=user_agent,
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id else '',
            details=details or {},
            success=success,
            error_message=error_message
        )


class SecurityAlert(models.Model):
    """
    Model for tracking security alerts and suspicious activities.
    """
    
    SEVERITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    ]
    
    STATUS_CHOICES = [
        ('OPEN', 'Open'),
        ('INVESTIGATING', 'Investigating'),
        ('RESOLVED', 'Resolved'),
        ('FALSE_POSITIVE', 'False Positive'),
    ]
    
    # Alert details
    title = models.CharField(max_length=200)
    description = models.TextField()
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN')
    
    # Related data
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    related_events = models.ManyToManyField(AuditEvent, blank=True)
    
    # Metadata
    details = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='resolved_alerts'
    )
    
    class Meta:
        db_table = 'security_alerts'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['severity', '-created_at']),
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['user', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.severity} - {self.title}"