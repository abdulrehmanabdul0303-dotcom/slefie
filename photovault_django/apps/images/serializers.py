"""
Serializers for image management.
"""
from rest_framework import serializers
from .models import Image, Folder, ImageTag, FaceDetection


class FolderSerializer(serializers.ModelSerializer):
    """
    Serializer for folder management.
    """
    image_count = serializers.SerializerMethodField()
    subfolder_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Folder
        fields = ('id', 'name', 'parent_folder', 'image_count', 'subfolder_count', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')
    
    def get_image_count(self, obj):
        return obj.images.count()
    
    def get_subfolder_count(self, obj):
        return obj.subfolders.count()


class ImageTagSerializer(serializers.ModelSerializer):
    """
    Serializer for image tags.
    """
    class Meta:
        model = ImageTag
        fields = ('id', 'tag', 'confidence', 'source', 'created_at')
        read_only_fields = ('id', 'created_at')


class FaceDetectionSerializer(serializers.ModelSerializer):
    """
    Serializer for face detection results.
    """
    person_name = serializers.CharField(source='person_cluster.name', read_only=True)
    
    class Meta:
        model = FaceDetection
        fields = ('id', 'bbox_x', 'bbox_y', 'bbox_width', 'bbox_height', 
                 'confidence', 'face_id', 'person_cluster', 'person_name', 'created_at')
        read_only_fields = ('id', 'created_at')


class ImageSerializer(serializers.ModelSerializer):
    """
    Serializer for image metadata.
    """
    tags = ImageTagSerializer(many=True, read_only=True)
    faces = FaceDetectionSerializer(many=True, read_only=True)
    folder_name = serializers.CharField(source='folder.name', read_only=True)
    file_size_mb = serializers.ReadOnlyField()
    has_location = serializers.ReadOnlyField()
    
    class Meta:
        model = Image
        fields = (
            'id', 'original_filename', 'content_type', 'size_bytes', 'file_size_mb',
            'width', 'height', 'gps_lat', 'gps_lng', 'location_text', 'has_location',
            'storage_key', 'thumb_storage_key', 'checksum_sha256', 'phash_hex',
            'camera_make', 'camera_model', 'taken_at', 'folder', 'folder_name',
            'tags', 'faces', 'created_at', 'updated_at'
        )
        read_only_fields = (
            'id', 'storage_key', 'thumb_storage_key', 'checksum_sha256', 'phash_hex',
            'size_bytes', 'width', 'height', 'content_type', 'created_at', 'updated_at'
        )


class ImageListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for image lists.
    """
    folder_name = serializers.CharField(source='folder.name', read_only=True)
    file_size_mb = serializers.ReadOnlyField()
    tag_count = serializers.SerializerMethodField()
    face_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Image
        fields = (
            'id', 'original_filename', 'content_type', 'file_size_mb',
            'width', 'height', 'gps_lat', 'gps_lng', 'location_text',
            'thumb_storage_key', 'camera_make', 'camera_model', 'taken_at',
            'folder', 'folder_name', 'tag_count', 'face_count', 'created_at'
        )
    
    def get_tag_count(self, obj):
        return obj.tags.count()
    
    def get_face_count(self, obj):
        return obj.faces.count()


class ImageUploadSerializer(serializers.Serializer):
    """
    Serializer for image upload.
    """
    file = serializers.ImageField()
    folder = serializers.IntegerField(required=False, allow_null=True)
    tags = serializers.ListField(
        child=serializers.CharField(max_length=100),
        required=False,
        allow_empty=True
    )
    
    def validate_folder(self, value):
        if value is not None:
            try:
                folder = Folder.objects.get(id=value, user=self.context['request'].user)
                return folder
            except Folder.DoesNotExist:
                raise serializers.ValidationError("Folder not found or access denied.")
        return None
    
    def validate_file(self, value):
        # Validate file size
        max_size = 50 * 1024 * 1024  # 50MB
        if value.size > max_size:
            raise serializers.ValidationError("File size cannot exceed 50MB.")
        
        # Validate file type
        allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']
        if value.content_type not in allowed_types:
            raise serializers.ValidationError("Unsupported file type. Allowed: JPEG, PNG, GIF, WEBP.")
        
        return value


class BulkImageUploadSerializer(serializers.Serializer):
    """
    Serializer for bulk image upload.
    """
    files = serializers.ListField(
        child=serializers.ImageField(),
        min_length=1,
        max_length=50  # Limit bulk uploads
    )
    folder = serializers.IntegerField(required=False, allow_null=True)
    
    def validate_folder(self, value):
        if value is not None:
            try:
                folder = Folder.objects.get(id=value, user=self.context['request'].user)
                return folder
            except Folder.DoesNotExist:
                raise serializers.ValidationError("Folder not found or access denied.")
        return None


class ImageUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating image metadata.
    """
    class Meta:
        model = Image
        fields = ('folder', 'location_text', 'gps_lat', 'gps_lng')
    
    def validate_folder(self, value):
        if value is not None:
            if value.user != self.context['request'].user:
                raise serializers.ValidationError("Folder access denied.")
        return value


class ImageSearchSerializer(serializers.Serializer):
    """
    Serializer for image search parameters.
    """
    query = serializers.CharField(required=False, allow_blank=True)
    folder = serializers.IntegerField(required=False, allow_null=True)
    tags = serializers.ListField(
        child=serializers.CharField(max_length=100),
        required=False,
        allow_empty=True
    )
    date_from = serializers.DateField(required=False, allow_null=True)
    date_to = serializers.DateField(required=False, allow_null=True)
    has_location = serializers.BooleanField(required=False, allow_null=True)
    has_faces = serializers.BooleanField(required=False, allow_null=True)
    camera_make = serializers.CharField(required=False, allow_blank=True)
    camera_model = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, attrs):
        date_from = attrs.get('date_from')
        date_to = attrs.get('date_to')
        
        if date_from and date_to and date_from > date_to:
            raise serializers.ValidationError("date_from cannot be after date_to")
        
        return attrs