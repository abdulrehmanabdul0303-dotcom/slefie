"""
Admin interface for Feature Flags.
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import FeatureFlag, FeatureFlagUsage, FeatureFlagOverride


@admin.register(FeatureFlag)
class FeatureFlagAdmin(admin.ModelAdmin):
    """
    Admin interface for Feature Flags.
    """
    list_display = [
        'name', 'key', 'flag_type', 'is_active', 'rollout_percentage', 
        'usage_count', 'created_at', 'expires_at'
    ]
    list_filter = ['flag_type', 'is_active', 'created_at', 'tags']
    search_fields = ['name', 'key', 'description']
    readonly_fields = ['created_at', 'updated_at', 'usage_count']
    
    fieldsets = [
        ('Basic Information', {
            'fields': ['name', 'key', 'description', 'tags']
        }),
        ('Configuration', {
            'fields': ['flag_type', 'is_active', 'rollout_percentage', 'environments']
        }),
        ('Experiment Settings', {
            'fields': ['experiment_config'],
            'classes': ['collapse'],
        }),
        ('Access Control', {
            'fields': ['user_whitelist'],
            'classes': ['collapse'],
        }),
        ('Metadata', {
            'fields': ['created_by', 'created_at', 'updated_at', 'expires_at'],
            'classes': ['collapse'],
        }),
    ]
    
    filter_horizontal = ['user_whitelist']
    
    def usage_count(self, obj):
        """Display usage count with link to analytics."""
        count = obj.usage_logs.count()
        if count > 0:
            url = reverse('admin:feature_flags_featureflagusage_changelist')
            return format_html(
                '<a href="{}?flag__id__exact={}">{} uses</a>',
                url, obj.id, count
            )
        return '0 uses'
    usage_count.short_description = 'Usage'
    
    def get_queryset(self, request):
        """Optimize queryset with prefetch."""
        return super().get_queryset(request).prefetch_related('usage_logs')
    
    actions = ['enable_flags', 'disable_flags', 'create_2090_flags']
    
    def enable_flags(self, request, queryset):
        """Enable selected flags."""
        count = queryset.update(is_active=True)
        self.message_user(request, f'{count} flags enabled.')
    enable_flags.short_description = 'Enable selected flags'
    
    def disable_flags(self, request, queryset):
        """Disable selected flags."""
        count = queryset.update(is_active=False)
        self.message_user(request, f'{count} flags disabled.')
    disable_flags.short_description = 'Disable selected flags'
    
    def create_2090_flags(self, request, queryset):
        """Create predefined 2090 feature flags."""
        from .models import PHOTOVAULT_2090_FEATURES
        
        created_count = 0
        for key, config in PHOTOVAULT_2090_FEATURES.items():
            flag, created = FeatureFlag.objects.get_or_create(
                key=key,
                defaults={
                    'name': config['name'],
                    'description': config['description'],
                    'flag_type': config['flag_type'],
                    'is_active': False,  # Start disabled for safety
                    'tags': config['tags'],
                    'environments': ['DEVELOPMENT', 'STAGING'],  # Start in dev/staging
                    'created_by': request.user,
                }
            )
            if created:
                created_count += 1
        
        self.message_user(request, f'{created_count} PhotoVault 2090 flags created.')
    create_2090_flags.short_description = 'Create PhotoVault 2090 feature flags'


@admin.register(FeatureFlagUsage)
class FeatureFlagUsageAdmin(admin.ModelAdmin):
    """
    Admin interface for Feature Flag Usage analytics.
    """
    list_display = [
        'flag', 'user', 'enabled', 'variant', 'environment', 
        'ip_address', 'timestamp'
    ]
    list_filter = [
        'enabled', 'environment', 'timestamp', 
        ('flag', admin.RelatedOnlyFieldListFilter),
    ]
    search_fields = ['flag__name', 'flag__key', 'user__email', 'ip_address']
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'
    
    def has_add_permission(self, request):
        """Disable manual creation."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Make read-only."""
        return False


@admin.register(FeatureFlagOverride)
class FeatureFlagOverrideAdmin(admin.ModelAdmin):
    """
    Admin interface for Feature Flag Overrides.
    """
    list_display = [
        'user', 'flag', 'enabled', 'variant', 'is_active_status', 
        'created_by', 'created_at', 'expires_at'
    ]
    list_filter = ['enabled', 'created_at', 'expires_at']
    search_fields = ['user__email', 'flag__name', 'flag__key']
    readonly_fields = ['created_at']
    
    fieldsets = [
        ('Override Configuration', {
            'fields': ['user', 'flag', 'enabled', 'variant']
        }),
        ('Metadata', {
            'fields': ['reason', 'created_by', 'created_at', 'expires_at']
        }),
    ]
    
    def is_active_status(self, obj):
        """Display if override is currently active."""
        if obj.is_active():
            return format_html('<span style="color: green;">✓ Active</span>')
        else:
            return format_html('<span style="color: red;">✗ Expired</span>')
    is_active_status.short_description = 'Status'
    
    actions = ['extend_expiry', 'remove_expiry']
    
    def extend_expiry(self, request, queryset):
        """Extend expiry by 30 days."""
        from datetime import timedelta
        
        for override in queryset:
            if override.expires_at:
                override.expires_at += timedelta(days=30)
            else:
                override.expires_at = timezone.now() + timedelta(days=30)
            override.save()
        
        count = queryset.count()
        self.message_user(request, f'{count} overrides extended by 30 days.')
    extend_expiry.short_description = 'Extend expiry by 30 days'
    
    def remove_expiry(self, request, queryset):
        """Remove expiry (make permanent)."""
        count = queryset.update(expires_at=None)
        self.message_user(request, f'{count} overrides made permanent.')
    remove_expiry.short_description = 'Remove expiry (make permanent)'


# Custom admin site configuration
admin.site.site_header = 'PhotoVault 2090 Feature Management'
admin.site.site_title = 'PhotoVault Admin'
admin.site.index_title = 'Feature Flag Administration'