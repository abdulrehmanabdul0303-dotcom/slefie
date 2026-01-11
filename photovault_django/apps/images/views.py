"""
Views for image management.
"""
from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.http import HttpResponse, Http404
from django.db.models import Q
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator

from .models import Image, Folder, ImageTag
from .serializers import (
    ImageSerializer,
    ImageListSerializer,
    ImageUploadSerializer,
    BulkImageUploadSerializer,
    ImageUpdateSerializer,
    ImageSearchSerializer,
    FolderSerializer,
    ImageTagSerializer,
)
from .services import ImageService, StorageService


class ImageListView(generics.ListAPIView):
    """
    List user's images with filtering and pagination.
    """
    serializer_class = ImageListSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = Image.objects.filter(user=self.request.user).select_related('folder')
        
        # Filter by folder
        folder_id = self.request.query_params.get('folder')
        if folder_id:
            queryset = queryset.filter(folder_id=folder_id)
        
        # Filter by date range
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        if date_from:
            queryset = queryset.filter(taken_at__gte=date_from)
        if date_to:
            queryset = queryset.filter(taken_at__lte=date_to)
        
        # Filter by location
        has_location = self.request.query_params.get('has_location')
        if has_location == 'true':
            queryset = queryset.filter(gps_lat__isnull=False, gps_lng__isnull=False)
        elif has_location == 'false':
            queryset = queryset.filter(Q(gps_lat__isnull=True) | Q(gps_lng__isnull=True))
        
        # Order by taken_at or created_at
        order_by = self.request.query_params.get('order_by', '-created_at')
        if order_by in ['-created_at', 'created_at', '-taken_at', 'taken_at']:
            queryset = queryset.order_by(order_by)
        
        return queryset


class ImageDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Get, update, or delete a specific image.
    """
    serializer_class = ImageSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Image.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return ImageUpdateSerializer
        return ImageSerializer
    
    def destroy(self, request, *args, **kwargs):
        image = self.get_object()
        
        # Delete physical files
        StorageService.delete_image_files(image)
        
        # Delete database record
        image.delete()
        
        return Response(status=status.HTTP_204_NO_CONTENT)


class ImageUploadView(APIView):
    """
    Upload a single image.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @method_decorator(ratelimit(key='user', rate='100/h', method='POST'))
    def post(self, request):
        serializer = ImageUploadSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            file = serializer.validated_data['file']
            folder = serializer.validated_data.get('folder')
            tags = serializer.validated_data.get('tags', [])
            
            try:
                # Process and save image
                image = ImageService.process_upload(request.user, file, folder)
                
                # Add tags if provided
                if tags:
                    for tag_name in tags:
                        ImageTag.objects.get_or_create(
                            image=image,
                            tag=tag_name.lower().strip(),
                            defaults={'source': 'user'}
                        )
                
                # Start background processing
                ImageService.start_background_processing(image)
                
                return Response(
                    ImageSerializer(image).data,
                    status=status.HTTP_201_CREATED
                )
                
            except Exception as e:
                return Response(
                    {'error': f'Upload failed: {str(e)}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BulkImageUploadView(APIView):
    """
    Upload multiple images at once.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @method_decorator(ratelimit(key='user', rate='10/h', method='POST'))
    def post(self, request):
        serializer = BulkImageUploadSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            files = serializer.validated_data['files']
            folder = serializer.validated_data.get('folder')
            
            results = []
            errors = []
            
            for file in files:
                try:
                    image = ImageService.process_upload(request.user, file, folder)
                    ImageService.start_background_processing(image)
                    results.append(ImageListSerializer(image).data)
                except Exception as e:
                    errors.append({
                        'filename': file.name,
                        'error': str(e)
                    })
            
            return Response({
                'uploaded': results,
                'errors': errors,
                'total_uploaded': len(results),
                'total_errors': len(errors)
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ImageSearchView(APIView):
    """
    Search images with various filters.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        serializer = ImageSearchSerializer(data=request.query_params)
        if serializer.is_valid():
            results = ImageService.search_images(request.user, serializer.validated_data)
            
            # Paginate results
            from django.core.paginator import Paginator
            paginator = Paginator(results, 20)
            page_number = request.query_params.get('page', 1)
            page_obj = paginator.get_page(page_number)
            
            return Response({
                'results': ImageListSerializer(page_obj.object_list, many=True).data,
                'count': paginator.count,
                'num_pages': paginator.num_pages,
                'current_page': page_obj.number,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous(),
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ImageFileView(APIView):
    """
    Serve image files (encrypted).
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, pk):
        image = get_object_or_404(Image, pk=pk, user=request.user)
        
        try:
            # Get image type (full or thumbnail)
            image_type = request.query_params.get('type', 'full')
            
            if image_type == 'thumb' and image.thumb_storage_key:
                file_data = StorageService.get_image_file(image.thumb_storage_key, request.user)
            else:
                file_data = StorageService.get_image_file(image.storage_key, request.user)
            
            response = HttpResponse(file_data, content_type=image.content_type or 'image/jpeg')
            response['Content-Disposition'] = f'inline; filename="{image.original_filename or "image.jpg"}"'
            return response
            
        except Exception as e:
            raise Http404("Image not found or access denied")


class FolderListCreateView(generics.ListCreateAPIView):
    """
    List and create folders.
    """
    serializer_class = FolderSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Folder.objects.filter(user=self.request.user).order_by('name')
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class FolderDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Get, update, or delete a folder.
    """
    serializer_class = FolderSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Folder.objects.filter(user=self.request.user)
    
    def destroy(self, request, *args, **kwargs):
        folder = self.get_object()
        
        # Move images to parent folder or root
        folder.images.update(folder=folder.parent_folder)
        
        # Move subfolders to parent folder or root
        folder.subfolders.update(parent_folder=folder.parent_folder)
        
        folder.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def add_image_tags(request, pk):
    """
    Add tags to an image.
    """
    image = get_object_or_404(Image, pk=pk, user=request.user)
    tags = request.data.get('tags', [])
    
    if not isinstance(tags, list):
        return Response({'error': 'Tags must be a list'}, status=status.HTTP_400_BAD_REQUEST)
    
    created_tags = []
    for tag_name in tags:
        tag_name = tag_name.lower().strip()
        if tag_name:
            tag, created = ImageTag.objects.get_or_create(
                image=image,
                tag=tag_name,
                defaults={'source': 'user'}
            )
            if created:
                created_tags.append(tag)
    
    return Response({
        'message': f'Added {len(created_tags)} new tags',
        'tags': ImageTagSerializer(created_tags, many=True).data
    })


@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def remove_image_tag(request, pk, tag_id):
    """
    Remove a tag from an image.
    """
    image = get_object_or_404(Image, pk=pk, user=request.user)
    tag = get_object_or_404(ImageTag, pk=tag_id, image=image)
    
    tag.delete()
    return Response({'message': 'Tag removed'}, status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def bulk_delete_images(request):
    """
    Delete multiple images at once.
    """
    image_ids = request.data.get('image_ids', [])
    
    if not isinstance(image_ids, list) or not image_ids:
        return Response({'error': 'image_ids must be a non-empty list'}, status=status.HTTP_400_BAD_REQUEST)
    
    images = Image.objects.filter(id__in=image_ids, user=request.user)
    deleted_count = 0
    
    for image in images:
        try:
            StorageService.delete_image_files(image)
            image.delete()
            deleted_count += 1
        except Exception as e:
            # Log error but continue with other images
            pass
    
    return Response({
        'message': f'Deleted {deleted_count} images',
        'deleted_count': deleted_count
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def image_stats(request):
    """
    Get image statistics for the user.
    """
    user_images = Image.objects.filter(user=request.user)
    
    stats = {
        'total_images': user_images.count(),
        'total_size_bytes': sum(img.size_bytes or 0 for img in user_images),
        'images_with_location': user_images.filter(gps_lat__isnull=False, gps_lng__isnull=False).count(),
        'images_with_faces': user_images.filter(faces__isnull=False).distinct().count(),
        'total_tags': ImageTag.objects.filter(image__user=request.user).count(),
        'unique_tags': ImageTag.objects.filter(image__user=request.user).values('tag').distinct().count(),
    }
    
    # Calculate total size in MB
    stats['total_size_mb'] = round(stats['total_size_bytes'] / (1024 * 1024), 2)
    
    return Response(stats)