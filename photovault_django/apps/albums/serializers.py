"""
Serializers for album management.
"""
from rest_framework import serializers
from .models import Album, AlbumImage
from apps.images.serializers import ImageListSerializer


class AlbumSerializer(serializers.ModelSerializer):
    """
    Serializer for album list and creation.
    """
    image_count = serializers.ReadOnlyField()
    cover_image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Album
        fields = (
            'id', 'name', 'description', 'album_type', 'location_text',
            'gps_lat', 'gps_lng', 'start_date', 'end_date', 'is_auto_generated',
            'image_count', 'cover_image_url', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'is_auto_generated', 'created_at', 'updated_at')
    
    def get_cover_image_url(self, obj):
        if obj.cover_image and obj.cover_image.thumb_storage_key:
            return f"/api/images/{obj.cover_image.id}/file/?type=thumb"
        return None


class AlbumDetailSerializer(AlbumSerializer):
    """
    Detailed serializer for album with images.
    """
    images = serializers.SerializerMethodField()
    
    class Meta(AlbumSerializer.Meta):
        fields = AlbumSerializer.Meta.fields + ('images',)
    
    def get_images(self, obj):
        album_images = AlbumImage.objects.filter(album=obj).order_by('order', 'added_at')
        images = [ai.image for ai in album_images]
        return ImageListSerializer(images, many=True).data


class AlbumImageSerializer(serializers.ModelSerializer):
    """
    Serializer for album-image relationship.
    """
    image = ImageListSerializer(read_only=True)
    
    class Meta:
        model = AlbumImage
        fields = ('id', 'image', 'order', 'added_at')


class AlbumCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating albums.
    """
    class Meta:
        model = Album
        fields = ('name', 'description', 'album_type', 'location_text', 'gps_lat', 'gps_lng')
    
    def validate_name(self, value):
        user = self.context['request'].user
        if Album.objects.filter(user=user, name=value).exists():
            raise serializers.ValidationError("Album with this name already exists.")
        return value