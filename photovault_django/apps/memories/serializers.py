from rest_framework import serializers
from .models import Memory, FlashbackReel, MemoryEngagement, MemoryPreferences, MemoryPhoto


class MemoryPhotoSerializer(serializers.ModelSerializer):
    """Serializer for MemoryPhoto through model"""
    
    class Meta:
        model = MemoryPhoto
        fields = ['photo', 'order', 'significance_score']


class MemorySerializer(serializers.ModelSerializer):
    """Serializer for Memory model"""
    photos = MemoryPhotoSerializer(source='memoryphoto_set', many=True, read_only=True)
    
    class Meta:
        model = Memory
        fields = [
            'id', 'target_date', 'photos', 'significance_score',
            'created_at', 'last_viewed', 'engagement_count'
        ]
        read_only_fields = ['id', 'created_at', 'last_viewed', 'engagement_count']


class FlashbackReelSerializer(serializers.ModelSerializer):
    """Serializer for FlashbackReel model"""
    
    class Meta:
        model = FlashbackReel
        fields = [
            'id', 'title', 'photos', 'video_file', 'duration', 'theme',
            'status', 'share_link', 'created_at', 'completed_at',
            'start_date', 'end_date', 'photo_count'
        ]
        read_only_fields = [
            'id', 'video_file', 'status', 'share_link', 'created_at',
            'completed_at', 'photo_count'
        ]


class MemoryEngagementSerializer(serializers.ModelSerializer):
    """Serializer for MemoryEngagement model"""
    
    class Meta:
        model = MemoryEngagement
        fields = ['id', 'memory', 'interaction_type', 'timestamp']
        read_only_fields = ['id', 'timestamp']


class MemoryPreferencesSerializer(serializers.ModelSerializer):
    """Serializer for MemoryPreferences model"""
    
    class Meta:
        model = MemoryPreferences
        fields = [
            'enable_notifications', 'notification_frequency',
            'include_private_albums', 'auto_generate_reels',
            'excluded_date_ranges', 'excluded_albums', 'feature_enabled'
        ]