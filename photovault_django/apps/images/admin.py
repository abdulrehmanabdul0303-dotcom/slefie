"""
Admin configuration for images app.
"""
from django.contrib import admin
from .models import Image, Folder, ImageTag, FaceDetection, ImageProcessingJob


@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    """
    Admin configuration for Image model.
    """
    list_display = ('original_filename', 'user', 'folder', 'size_bytes', 'width', 'height', 'created_at')
    list_filter = ('content_type', 'created_at', 'taken_at', 'camera_make')
    search_fields = ('original_filename', 'user__email', 'location_text', 'camera_make', 'camera_model')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('user', 'folder', 'original_filename', 'content_type', 'size_bytes')
        }),
        ('Dimensions', {
            'fields': ('width', 'height')
        }),
        ('Location', {
            'fields': ('gps_lat', 'gps_lng', 'location_text')
        }),
        ('Storage', {
            'fields': ('storage_key', 'thumb_storage_key', 'checksum_sha256', 'phash_hex')
        }),
        ('Camera Info', {
            'fields': ('camera_make', 'camera_model', 'taken_at')
        }),
        ('AI/ML', {
            'fields': ('embedding_json',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at', 'checksum_sha256', 'size_bytes', 'width', 'height')


@admin.register(Folder)
class FolderAdmin(admin.ModelAdmin):
    """
    Admin configuration for Folder model.
    """
    list_display = ('name', 'user', 'parent_folder', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'user__email')
    ordering = ('user', 'name')


@admin.register(ImageTag)
class ImageTagAdmin(admin.ModelAdmin):
    """
    Admin configuration for ImageTag model.
    """
    list_display = ('tag', 'image', 'source', 'confidence', 'created_at')
    list_filter = ('source', 'created_at')
    search_fields = ('tag', 'image__original_filename', 'image__user__email')
    ordering = ('-created_at',)


@admin.register(FaceDetection)
class FaceDetectionAdmin(admin.ModelAdmin):
    """
    Admin configuration for FaceDetection model.
    """
    list_display = ('face_id', 'image', 'person_cluster', 'confidence', 'created_at')
    list_filter = ('confidence', 'created_at')
    search_fields = ('face_id', 'image__original_filename', 'image__user__email')
    ordering = ('-created_at',)


@admin.register(ImageProcessingJob)
class ImageProcessingJobAdmin(admin.ModelAdmin):
    """
    Admin configuration for ImageProcessingJob model.
    """
    list_display = ('job_type', 'image', 'status', 'created_at', 'completed_at')
    list_filter = ('job_type', 'status', 'created_at')
    search_fields = ('image__original_filename', 'image__user__email', 'celery_task_id')
    ordering = ('-created_at',)
    
    readonly_fields = ('created_at', 'started_at', 'completed_at')