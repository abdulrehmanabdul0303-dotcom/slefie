from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from apps.images.models import Image
from apps.sharing.models import PublicShare

User = get_user_model()

REEL_STATUS_CHOICES = [
    ('pending', 'Pending'),
    ('processing', 'Processing'),
    ('completed', 'Completed'),
    ('failed', 'Failed'),
]

INTERACTION_TYPE_CHOICES = [
    ('view', 'View'),
    ('share', 'Share'),
    ('like', 'Like'),
    ('download', 'Download'),
]


class Memory(models.Model):
    """
    Represents a collection of photos from a specific date in the past,
    surfaced as "on this day" memories for user engagement.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='memories')
    target_date = models.DateField(help_text="The 'on this day' date for this memory")
    photos = models.ManyToManyField(Image, through='MemoryPhoto', related_name='memories')
    significance_score = models.FloatField(
        default=0.0,
        help_text="Calculated score based on engagement metrics and photo importance"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    last_viewed = models.DateTimeField(null=True, blank=True)
    engagement_count = models.IntegerField(default=0)
    
    class Meta:
        unique_together = ['user', 'target_date']
        indexes = [
            models.Index(fields=['user', 'target_date']),
            models.Index(fields=['significance_score']),
            models.Index(fields=['created_at']),
        ]
        verbose_name_plural = "Memories"
    
    def __str__(self):
        return f"Memory for {self.user.username} - {self.target_date}"
    
    def update_engagement(self):
        """Update engagement count based on interactions"""
        self.engagement_count = self.memory_engagements.count()
        self.last_viewed = timezone.now()
        self.save(update_fields=['engagement_count', 'last_viewed'])


class MemoryPhoto(models.Model):
    """
    Through model for Memory-Photo relationship with additional metadata.
    """
    memory = models.ForeignKey(Memory, on_delete=models.CASCADE)
    photo = models.ForeignKey(Image, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0, help_text="Display order within the memory")
    significance_score = models.FloatField(
        default=0.0,
        help_text="Individual photo significance within this memory"
    )
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['memory', 'photo']
        ordering = ['order', '-significance_score']
        indexes = [
            models.Index(fields=['memory', 'order']),
            models.Index(fields=['significance_score']),
        ]
    
    def __str__(self):
        return f"{self.memory} - Photo {self.photo.id}"


class FlashbackReel(models.Model):
    """
    Automatically generated video reels from photo collections,
    designed for sharing and client engagement.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='flashback_reels')
    title = models.CharField(max_length=200)
    photos = models.ManyToManyField(Image, related_name='flashback_reels')
    video_file = models.FileField(upload_to='reels/', null=True, blank=True)
    duration = models.IntegerField(default=30, help_text="Duration in seconds")
    theme = models.CharField(max_length=50, default='classic')
    status = models.CharField(max_length=20, choices=REEL_STATUS_CHOICES, default='pending')
    share_link = models.OneToOneField(
        PublicShare, 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL,
        related_name='flashback_reel'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True, help_text="Error details if generation failed")
    
    # Metadata for reel generation
    start_date = models.DateField(help_text="Start date of photos included in reel")
    end_date = models.DateField(help_text="End date of photos included in reel")
    photo_count = models.PositiveIntegerField(default=0)
    
    class Meta:
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['start_date', 'end_date']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Flashback Reel: {self.title} ({self.status})"
    
    def mark_completed(self):
        """Mark reel as completed and set completion timestamp"""
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save(update_fields=['status', 'completed_at'])
    
    def mark_failed(self, error_message=""):
        """Mark reel as failed with optional error message"""
        self.status = 'failed'
        self.error_message = error_message
        self.save(update_fields=['status', 'error_message'])


class MemoryEngagement(models.Model):
    """
    Tracks user interactions with memories for analytics and future prioritization.
    """
    memory = models.ForeignKey(Memory, on_delete=models.CASCADE, related_name='memory_engagements')
    interaction_type = models.CharField(max_length=20, choices=INTERACTION_TYPE_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, help_text="Browser/client information")
    
    class Meta:
        indexes = [
            models.Index(fields=['memory', 'timestamp']),
            models.Index(fields=['interaction_type']),
            models.Index(fields=['timestamp']),
        ]
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.interaction_type} - {self.memory} at {self.timestamp}"


class MemoryNotification(models.Model):
    """
    Tracks memory notifications sent to users for engagement tracking.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='memory_notifications')
    memory = models.ForeignKey(Memory, on_delete=models.CASCADE, related_name='notifications')
    sent_at = models.DateTimeField(auto_now_add=True)
    clicked_at = models.DateTimeField(null=True, blank=True)
    notification_type = models.CharField(max_length=50, default='daily_memory')
    
    class Meta:
        indexes = [
            models.Index(fields=['user', 'sent_at']),
            models.Index(fields=['memory']),
        ]
        ordering = ['-sent_at']
    
    def __str__(self):
        return f"Notification to {self.user.username} for {self.memory}"
    
    def mark_clicked(self):
        """Mark notification as clicked"""
        self.clicked_at = timezone.now()
        self.save(update_fields=['clicked_at'])


class MemoryPreferences(models.Model):
    """
    User preferences for Memory Time Machine feature.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='memory_preferences')
    
    # Notification preferences
    enable_notifications = models.BooleanField(default=True)
    notification_frequency = models.CharField(
        max_length=20,
        choices=[
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
            ('monthly', 'Monthly'),
        ],
        default='daily'
    )
    
    # Privacy preferences
    include_private_albums = models.BooleanField(default=False)
    auto_generate_reels = models.BooleanField(default=True)
    
    # Exclusions
    excluded_date_ranges = models.JSONField(
        default=list,
        help_text="List of date ranges to exclude from memories"
    )
    excluded_albums = models.ManyToManyField(
        'albums.Album',
        blank=True,
        related_name='excluded_from_memories'
    )
    
    # Feature opt-out
    feature_enabled = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Memory Preferences"
    
    def __str__(self):
        return f"Memory preferences for {self.user.username}"