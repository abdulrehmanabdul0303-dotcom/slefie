"""
Admin configuration for audit logging.
"""
from django.contrib import admin
from .models import AuditEvent, SecurityAlert


@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
    """
    Admin interface for audit events.
    """
    list_display = ('timestamp', 'user', 'category', 'event_type', 'success', 'ip_address')
    list_filter = ('category', 'event_type', 'success', 'timestamp')
    search_fields = ('user__email', 'event_type', 'ip_address', 'resource_type')
    readonly_fields = ('timestamp',)
    ordering = ('-timestamp',)
    
    fieldsets = (
        ('Event Information', {
            'fields': ('user', 'category', 'event_type', 'timestamp')
        }),
        ('Request Context', {
            'fields': ('ip_address', 'user_agent')
        }),
        ('Resource Details', {
            'fields': ('resource_type', 'resource_id', 'details')
        }),
        ('Outcome', {
            'fields': ('success', 'error_message')
        }),
    )
    
    def has_add_permission(self, request):
        """Audit events should not be manually created."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Audit events should not be modified."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Only superusers can delete audit events."""
        return request.user.is_superuser


@admin.register(SecurityAlert)
class SecurityAlertAdmin(admin.ModelAdmin):
    """
    Admin interface for security alerts.
    """
    list_display = ('title', 'severity', 'status', 'user', 'created_at')
    list_filter = ('severity', 'status', 'created_at')
    search_fields = ('title', 'description', 'user__email', 'ip_address')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Alert Information', {
            'fields': ('title', 'description', 'severity', 'status')
        }),
        ('Related Data', {
            'fields': ('user', 'ip_address', 'related_events')
        }),
        ('Resolution', {
            'fields': ('resolved_at', 'resolved_by')
        }),
        ('Metadata', {
            'fields': ('details', 'created_at', 'updated_at')
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """Auto-set resolved_by when status changes to resolved."""
        if obj.status == 'RESOLVED' and not obj.resolved_by:
            obj.resolved_by = request.user
            if not obj.resolved_at:
                from django.utils import timezone
                obj.resolved_at = timezone.now()
        super().save_model(request, obj, form, change)