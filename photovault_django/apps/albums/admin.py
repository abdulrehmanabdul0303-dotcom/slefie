"""
Admin configuration for albums app.
"""
from django.contrib import admin
from .models import Album, AlbumImage


@admin.register(Album)
class AlbumAdmin(admin.ModelAdmin):
    """
    Admin configuration for Album model.
    """
    list_display = ('name', 'user', 'album_type', 'image_count', 'is_auto_generated', 'created_at')
    list_filter = ('album_type', 'is_auto_generated', 'created_at')
    search_fields = ('name', 'user__email', 'description')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('user', 'name', 'description', 'album_type')
        }),
        ('Location', {
            'fields': ('location_text', 'gps_lat', 'gps_lng')
        }),
        ('Date Range', {
            'fields': ('start_date', 'end_date')
        }),
        ('Settings', {
            'fields': ('is_auto_generated', 'cover_image', 'person_cluster')
        }),
        ('Face Sharing', {
            'fields': ('face_share_enabled', 'face_threshold', 'allow_fallback_auth')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')


@admin.register(AlbumImage)
class AlbumImageAdmin(admin.ModelAdmin):
    """
    Admin configuration for AlbumImage model.
    """
    list_display = ('album', 'image', 'order', 'added_at')
    list_filter = ('added_at',)
    search_fields = ('album__name', 'image__original_filename')
    ordering = ('album', 'order', 'added_at')
    
    readonly_fields = ('added_at',)