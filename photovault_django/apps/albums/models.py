"""
Album models for PhotoVault.
"""
from django.db import models
from django.conf import settings


class Album(models.Model):
    """
    Album model for organizing images.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='albums')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    
    # Album types
    ALBUM_TYPES = [
        ('manual', 'Manual'),
        ('auto_date', 'Auto by Date'),
        ('auto_location', 'Auto by Location'),
        ('auto_person', 'Auto by Person'),
    ]
    album_type = models.CharField(max_length=32, choices=ALBUM_TYPES, default='manual')
    
    # Location data
    location_text = models.CharField(max_length=512, blank=True, null=True)
    gps_lat = models.FloatField(blank=True, null=True)
    gps_lng = models.FloatField(blank=True, null=True)
    
    # Date range for auto albums
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    
    # Auto-generation flag
    is_auto_generated = models.BooleanField(default=False)
    
    # Cover image
    cover_image = models.ForeignKey(
        'images.Image',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='cover_for_albums'
    )
    
    # Person cluster for person albums
    person_cluster = models.ForeignKey(
        'users.PersonCluster',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='albums'
    )
    
    # Many-to-many relationship with images
    images = models.ManyToManyField(
        'images.Image',
        through='AlbumImage',
        related_name='albums'
    )
    
    # Face-based sharing settings
    face_share_enabled = models.BooleanField(default=False)
    face_threshold = models.FloatField(default=0.45)
    face_encoding_version = models.IntegerField(default=1)
    
    # Fallback authentication for face sharing
    allow_fallback_auth = models.BooleanField(default=False)
    fallback_pin_hash = models.CharField(max_length=128, blank=True, null=True)
    max_failed_attempts = models.IntegerField(default=5)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'albums'
        unique_together = ['user', 'name']
        indexes = [
            models.Index(fields=['user', 'album_type']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['is_auto_generated']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.name}"
    
    @property
    def image_count(self):
        """Get the number of images in this album."""
        return self.images.count()
    
    @property
    def has_location(self):
        """Check if album has GPS coordinates."""
        return self.gps_lat is not None and self.gps_lng is not None


class AlbumImage(models.Model):
    """
    Through model for Album-Image many-to-many relationship.
    """
    album = models.ForeignKey(Album, on_delete=models.CASCADE)
    image = models.ForeignKey('images.Image', on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)
    
    # Order within album
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        db_table = 'album_images'
        unique_together = ['album', 'image']
        indexes = [
            models.Index(fields=['album', 'order']),
            models.Index(fields=['added_at']),
        ]
    
    def __str__(self):
        return f"{self.album.name} - {self.image.original_filename}"