"""
Image models for PhotoVault.
"""
from django.db import models
from django.conf import settings
import json


class Folder(models.Model):
    """
    Folder model for organizing images.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='folders')
    name = models.CharField(max_length=255)
    parent_folder = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subfolders')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'folders'
        unique_together = ['user', 'name', 'parent_folder']
        indexes = [
            models.Index(fields=['user', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.name}"


class Image(models.Model):
    """
    Image model for storing photo metadata and references.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='images')
    folder = models.ForeignKey(Folder, on_delete=models.SET_NULL, null=True, blank=True, related_name='images')
    
    # File information
    original_filename = models.CharField(max_length=512, null=True, blank=True)
    content_type = models.CharField(max_length=100, null=True, blank=True)
    size_bytes = models.BigIntegerField(null=True, blank=True)
    
    # Image dimensions
    width = models.IntegerField(null=True, blank=True)
    height = models.IntegerField(null=True, blank=True)
    
    # GPS and location data
    gps_lat = models.FloatField(null=True, blank=True)
    gps_lng = models.FloatField(null=True, blank=True)
    location_text = models.CharField(max_length=512, null=True, blank=True)
    
    # Storage keys
    storage_key = models.CharField(max_length=1024)  # Path to encrypted file
    thumb_storage_key = models.CharField(max_length=1024, null=True, blank=True)  # Path to thumbnail
    
    # Checksums and hashes
    checksum_sha256 = models.CharField(max_length=64, db_index=True)
    phash_hex = models.CharField(max_length=16, null=True, blank=True)  # Perceptual hash
    
    # AI/ML embeddings
    embedding_json = models.JSONField(null=True, blank=True)  # CLIP embeddings for semantic search
    
    # EXIF and metadata
    exif_data = models.JSONField(null=True, blank=True)
    camera_make = models.CharField(max_length=100, null=True, blank=True)
    camera_model = models.CharField(max_length=100, null=True, blank=True)
    taken_at = models.DateTimeField(null=True, blank=True)  # From EXIF
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'images'
        unique_together = ['user', 'checksum_sha256']
        indexes = [
            models.Index(fields=['user', 'folder', 'created_at']),
            models.Index(fields=['user', 'taken_at']),
            models.Index(fields=['checksum_sha256']),
            models.Index(fields=['gps_lat', 'gps_lng']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.original_filename or self.storage_key}"
    
    @property
    def embedding(self):
        """Get embedding as list."""
        if self.embedding_json:
            return json.loads(self.embedding_json) if isinstance(self.embedding_json, str) else self.embedding_json
        return None
    
    @embedding.setter
    def embedding(self, value):
        """Set embedding from list."""
        if value is not None:
            self.embedding_json = json.dumps(value) if isinstance(value, list) else value
        else:
            self.embedding_json = None
    
    @property
    def has_location(self):
        """Check if image has GPS coordinates."""
        return self.gps_lat is not None and self.gps_lng is not None
    
    @property
    def file_size_mb(self):
        """Get file size in MB."""
        if self.size_bytes:
            return round(self.size_bytes / (1024 * 1024), 2)
        return None
    
    @property
    def filename(self):
        """Get display filename."""
        return self.original_filename or f"image_{self.id}.jpg"
    
    @property
    def file_size(self):
        """Get file size in bytes."""
        return self.size_bytes or 0
    
    @property
    def date_taken(self):
        """Get date taken (alias for taken_at)."""
        return self.taken_at
    
    @property
    def file_path(self):
        """Get file path from storage key."""
        # For development, assume storage_key is relative path
        import os
        from django.conf import settings
        
        if hasattr(settings, 'MEDIA_ROOT'):
            return os.path.join(settings.MEDIA_ROOT, self.storage_key)
        return self.storage_key
    
    def get_thumbnail_data(self):
        """Get thumbnail image data."""
        # For development, return a simple placeholder or original data
        try:
            if hasattr(self, '_thumbnail_data'):
                return self._thumbnail_data
            
            # Try to read from file
            import os
            if os.path.exists(self.file_path):
                with open(self.file_path, 'rb') as f:
                    return f.read()
            
            # Return placeholder image data
            return self._get_placeholder_image()
        except Exception:
            return self._get_placeholder_image()
    
    def get_preview_data(self):
        """Get preview image data."""
        # For development, return original data or placeholder
        try:
            if hasattr(self, '_preview_data'):
                return self._preview_data
            
            # Try to read from file
            import os
            if os.path.exists(self.file_path):
                with open(self.file_path, 'rb') as f:
                    return f.read()
            
            # Return placeholder image data
            return self._get_placeholder_image()
        except Exception:
            return self._get_placeholder_image()
    
    def get_original_data(self):
        """Get original image data."""
        try:
            if hasattr(self, '_original_data'):
                return self._original_data
            
            # Try to read from file
            import os
            if os.path.exists(self.file_path):
                with open(self.file_path, 'rb') as f:
                    return f.read()
            
            # Return placeholder image data
            return self._get_placeholder_image()
        except Exception:
            return self._get_placeholder_image()
    
    def _get_placeholder_image(self):
        """Generate a simple placeholder image."""
        try:
            from PIL import Image as PILImage, ImageDraw, ImageFont
            import io
            
            # Create a simple placeholder
            img = PILImage.new('RGB', (400, 300), color='lightgray')
            draw = ImageDraw.Draw(img)
            
            # Add text
            text = f"Image {self.id}"
            try:
                font = ImageFont.load_default()
            except:
                font = None
            
            # Get text size and center it
            if font:
                bbox = draw.textbbox((0, 0), text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
            else:
                text_width, text_height = 100, 20
            
            x = (400 - text_width) // 2
            y = (300 - text_height) // 2
            
            draw.text((x, y), text, fill='black', font=font)
            
            # Convert to bytes
            output = io.BytesIO()
            img.save(output, format='JPEG', quality=80)
            return output.getvalue()
            
        except Exception:
            # Fallback: return minimal JPEG header
            return b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0\x00\x11\x08\x01,\x01\x90\x03\x01"\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\xff\xc4\x00\x14\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00\x3f\x00\xaa\xff\xd9'


class ImageTag(models.Model):
    """
    Tags for images (user-defined or AI-generated).
    """
    image = models.ForeignKey(Image, on_delete=models.CASCADE, related_name='tags')
    tag = models.CharField(max_length=100)
    confidence = models.FloatField(default=1.0)  # For AI-generated tags
    source = models.CharField(max_length=20, choices=[
        ('user', 'User'),
        ('ai', 'AI Generated'),
        ('exif', 'EXIF Data'),
    ], default='user')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'image_tags'
        unique_together = ['image', 'tag']
        indexes = [
            models.Index(fields=['image', 'tag']),
            models.Index(fields=['tag']),
        ]
    
    def __str__(self):
        return f"{self.image} - {self.tag}"


class FaceDetection(models.Model):
    """
    Face detection results for images.
    """
    image = models.ForeignKey(Image, on_delete=models.CASCADE, related_name='faces')
    person_cluster = models.ForeignKey(
        'users.PersonCluster', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='face_detections'
    )
    
    # Bounding box coordinates (normalized 0-1)
    bbox_x = models.FloatField()
    bbox_y = models.FloatField()
    bbox_width = models.FloatField()
    bbox_height = models.FloatField()
    
    # Face embedding for recognition
    face_embedding_json = models.JSONField()
    confidence = models.FloatField()
    
    # Face ID for tracking
    face_id = models.CharField(max_length=255, db_index=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'face_detections'
        indexes = [
            models.Index(fields=['image', 'face_id']),
            models.Index(fields=['person_cluster']),
        ]
    
    def __str__(self):
        return f"Face in {self.image} - {self.face_id}"
    
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


class ImageProcessingJob(models.Model):
    """
    Background job tracking for image processing.
    """
    image = models.ForeignKey(Image, on_delete=models.CASCADE, related_name='processing_jobs')
    job_type = models.CharField(max_length=50, choices=[
        ('thumbnail', 'Thumbnail Generation'),
        ('face_detection', 'Face Detection'),
        ('embedding', 'Embedding Generation'),
        ('exif_extraction', 'EXIF Extraction'),
        ('duplicate_detection', 'Duplicate Detection'),
    ])
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ], default='pending')
    
    # Job details
    celery_task_id = models.CharField(max_length=255, null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    result_data = models.JSONField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'image_processing_jobs'
        indexes = [
            models.Index(fields=['image', 'job_type']),
            models.Index(fields=['status', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.job_type} for {self.image} - {self.status}"