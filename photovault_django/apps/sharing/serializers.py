"""
Serializers for sharing system.
"""
from rest_framework import serializers
from django.utils import timezone
from datetime import timedelta
from .models import PublicShare, ShareAccess, FaceClaimSession


class ShareCreateSerializer(serializers.Serializer):
    """
    Serializer for creating share links.
    """
    album_id = serializers.IntegerField()
    expires_in_hours = serializers.IntegerField(default=24, min_value=1, max_value=8760)  # Max 1 year
    scope = serializers.ChoiceField(choices=PublicShare.SCOPE_CHOICES, default='view')
    share_type = serializers.ChoiceField(choices=PublicShare.SHARE_TYPE_CHOICES, default='PUBLIC')
    max_views = serializers.IntegerField(required=False, allow_null=True, min_value=1)
    require_face = serializers.BooleanField(default=False)
    
    def validate_album_id(self, value):
        from apps.albums.models import Album
        try:
            album = Album.objects.get(id=value, user=self.context['request'].user)
            return album
        except Album.DoesNotExist:
            raise serializers.ValidationError("Album not found or access denied.")
    
    def validate(self, attrs):
        if attrs['share_type'] == 'FACE_CLAIM' and not attrs['require_face']:
            attrs['require_face'] = True
        return attrs


class PublicShareSerializer(serializers.ModelSerializer):
    """
    Serializer for public share information.
    """
    album_name = serializers.CharField(source='album.name', read_only=True)
    album_description = serializers.CharField(source='album.description', read_only=True)
    creator_name = serializers.CharField(source='created_by.name', read_only=True)
    is_expired = serializers.ReadOnlyField()
    is_valid = serializers.ReadOnlyField()
    share_url = serializers.SerializerMethodField()
    
    class Meta:
        model = PublicShare
        fields = (
            'id', 'album_name', 'album_description', 'creator_name',
            'scope', 'share_type', 'expires_at', 'max_views', 'view_count',
            'require_face', 'is_expired', 'is_valid', 'share_url',
            'created_at'
        )
    
    def get_share_url(self, obj):
        if hasattr(obj, 'raw_token') and obj.raw_token:
            frontend_url = self.context.get('frontend_url', 'http://localhost:3000')
            return f"{frontend_url}/shared/{obj.raw_token}"
        return None


class ShareAccessSerializer(serializers.ModelSerializer):
    """
    Serializer for share access logs.
    """
    album_name = serializers.CharField(source='share.album.name', read_only=True)
    
    class Meta:
        model = ShareAccess
        fields = (
            'id', 'album_name', 'ip_address', 'user_agent',
            'face_verified', 'face_confidence', 'accessed_at'
        )


class SharedAlbumViewSerializer(serializers.Serializer):
    """
    Serializer for viewing shared albums (public endpoint).
    """
    album = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()
    share_info = serializers.SerializerMethodField()
    
    def get_album(self, obj):
        from apps.albums.serializers import AlbumSerializer
        return AlbumSerializer(obj.album).data
    
    def get_images(self, obj):
        from apps.images.serializers import ImageListSerializer
        images = obj.album.images.all().order_by('-created_at')
        return ImageListSerializer(images, many=True).data
    
    def get_share_info(self, obj):
        return {
            'scope': obj.scope,
            'share_type': obj.share_type,
            'require_face': obj.require_face,
            'expires_at': obj.expires_at,
            'view_count': obj.view_count,
            'max_views': obj.max_views,
        }


class FaceClaimUploadSerializer(serializers.Serializer):
    """
    Serializer for face claim image upload.
    """
    image = serializers.ImageField()
    
    def validate_image(self, value):
        # Validate file size (max 10MB for face images)
        max_size = 10 * 1024 * 1024
        if value.size > max_size:
            raise serializers.ValidationError("Image size cannot exceed 10MB.")
        
        # Validate file type
        allowed_types = ['image/jpeg', 'image/jpg', 'image/png']
        if value.content_type not in allowed_types:
            raise serializers.ValidationError("Only JPEG and PNG images are allowed.")
        
        return value


class FaceClaimVerifySerializer(serializers.Serializer):
    """
    Serializer for face claim verification.
    """
    session_token = serializers.CharField(max_length=64)
    
    def validate_session_token(self, value):
        try:
            session = FaceClaimSession.objects.get(session_token=value)
            if not session.is_valid:
                raise serializers.ValidationError("Session expired or invalid.")
            return session
        except FaceClaimSession.DoesNotExist:
            raise serializers.ValidationError("Invalid session token.")