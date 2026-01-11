"""
Admin configuration for sharing app.
"""
from django.contrib import admin
from .models import PublicShare, ShareAccess, FaceClaimSession, FaceClaimAudit


@admin.register(PublicShare)
class PublicShareAdmin(admin.ModelAdmin):
    """
    Admin configuration for PublicShare model.
    """
    list_display = ('album', 'created_by', 'share_type', 'scope', 'view_count', 'max_views', 'expires_at', 'revoked')
    list_filter = ('share_type', 'scope', 'revoked', 'require_face', 'created_at', 'expires_at')
    search_fields = ('album__name', 'created_by__email', 'token_hash')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('created_by', 'album', 'share_type', 'scope')
        }),
        ('Access Control', {
            'fields': ('expires_at', 'max_views', 'view_count', 'revoked')
        }),
        ('Security', {
            'fields': ('token_hash', 'ip_lock', 'user_agent_lock')
        }),
        ('Face Verification', {
            'fields': ('require_face', 'face_claim_verified', 'face_claim_attempts', 'face_claim_lock_until')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at', 'token_hash', 'view_count')


@admin.register(ShareAccess)
class ShareAccessAdmin(admin.ModelAdmin):
    """
    Admin configuration for ShareAccess model.
    """
    list_display = ('share', 'ip_address', 'face_verified', 'face_confidence', 'accessed_at')
    list_filter = ('face_verified', 'accessed_at')
    search_fields = ('share__album__name', 'ip_address', 'user_agent')
    ordering = ('-accessed_at',)
    
    readonly_fields = ('accessed_at',)


@admin.register(FaceClaimSession)
class FaceClaimSessionAdmin(admin.ModelAdmin):
    """
    Admin configuration for FaceClaimSession model.
    """
    list_display = ('share', 'session_token', 'ip_address', 'created_at', 'expires_at')
    list_filter = ('created_at', 'expires_at')
    search_fields = ('share__album__name', 'session_token', 'ip_address')
    ordering = ('-created_at',)
    
    readonly_fields = ('created_at',)


@admin.register(FaceClaimAudit)
class FaceClaimAuditAdmin(admin.ModelAdmin):
    """
    Admin configuration for FaceClaimAudit model.
    """
    list_display = ('share', 'attempt_type', 'success', 'confidence_score', 'ip_address', 'created_at')
    list_filter = ('attempt_type', 'success', 'created_at')
    search_fields = ('share__album__name', 'ip_address', 'matched_face_id')
    ordering = ('-created_at',)
    
    readonly_fields = ('created_at',)