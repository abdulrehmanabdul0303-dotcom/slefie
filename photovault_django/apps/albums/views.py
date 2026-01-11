"""
Views for album management.
"""
from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator

from .models import Album, AlbumImage
from .serializers import AlbumSerializer, AlbumDetailSerializer, AlbumImageSerializer
from apps.images.models import Image


class AlbumListCreateView(generics.ListCreateAPIView):
    """
    List and create albums.
    """
    serializer_class = AlbumSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Album.objects.filter(user=self.request.user).order_by('-created_at')
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class AlbumDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Get, update, or delete an album.
    """
    serializer_class = AlbumDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Album.objects.filter(user=self.request.user)
    
    def destroy(self, request, *args, **kwargs):
        album = self.get_object()
        
        # Remove images from album (don't delete the images themselves)
        album.images.clear()
        
        # Delete the album
        album.delete()
        
        return Response(status=status.HTTP_204_NO_CONTENT)


class AlbumImagesView(generics.ListAPIView):
    """
    List images in an album.
    """
    serializer_class = AlbumImageSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        album_id = self.kwargs['pk']
        album = get_object_or_404(Album, pk=album_id, user=self.request.user)
        return AlbumImage.objects.filter(album=album).order_by('order', 'added_at')


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def add_images_to_album(request, pk):
    """
    Add images to an album.
    """
    album = get_object_or_404(Album, pk=pk, user=request.user)
    image_ids = request.data.get('image_ids', [])
    
    if not isinstance(image_ids, list) or not image_ids:
        return Response({'error': 'image_ids must be a non-empty list'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Verify all images belong to the user
    images = Image.objects.filter(id__in=image_ids, user=request.user)
    if len(images) != len(image_ids):
        return Response({'error': 'Some images not found or access denied'}, status=status.HTTP_400_BAD_REQUEST)
    
    added_count = 0
    for image in images:
        album_image, created = AlbumImage.objects.get_or_create(
            album=album,
            image=image,
            defaults={'order': 0}
        )
        if created:
            added_count += 1
    
    return Response({
        'message': f'Added {added_count} images to album',
        'total_images': album.images.count()
    })


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def remove_images_from_album(request, pk):
    """
    Remove images from an album.
    """
    album = get_object_or_404(Album, pk=pk, user=request.user)
    image_ids = request.data.get('image_ids', [])
    
    if not isinstance(image_ids, list) or not image_ids:
        return Response({'error': 'image_ids must be a non-empty list'}, status=status.HTTP_400_BAD_REQUEST)
    
    removed_count = AlbumImage.objects.filter(
        album=album,
        image_id__in=image_ids
    ).delete()[0]
    
    return Response({
        'message': f'Removed {removed_count} images from album',
        'total_images': album.images.count()
    })


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def set_album_cover(request, pk):
    """
    Set album cover image.
    """
    album = get_object_or_404(Album, pk=pk, user=request.user)
    image_id = request.data.get('image_id')
    
    if not image_id:
        return Response({'error': 'image_id is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Verify image exists and belongs to user
    image = get_object_or_404(Image, pk=image_id, user=request.user)
    
    # Verify image is in the album
    if not album.images.filter(id=image_id).exists():
        return Response({'error': 'Image is not in this album'}, status=status.HTTP_400_BAD_REQUEST)
    
    album.cover_image = image
    album.save()
    
    return Response({'message': 'Album cover updated'})


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def reorder_album_images(request, pk):
    """
    Reorder images in an album.
    """
    album = get_object_or_404(Album, pk=pk, user=request.user)
    image_orders = request.data.get('image_orders', [])
    
    # image_orders should be [{'image_id': 1, 'order': 0}, {'image_id': 2, 'order': 1}, ...]
    if not isinstance(image_orders, list):
        return Response({'error': 'image_orders must be a list'}, status=status.HTTP_400_BAD_REQUEST)
    
    updated_count = 0
    for item in image_orders:
        image_id = item.get('image_id')
        order = item.get('order', 0)
        
        try:
            album_image = AlbumImage.objects.get(album=album, image_id=image_id)
            album_image.order = order
            album_image.save()
            updated_count += 1
        except AlbumImage.DoesNotExist:
            continue
    
    return Response({
        'message': f'Updated order for {updated_count} images'
    })


class AlbumsByDateView(APIView):
    """
    Get auto-generated albums by date.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        from django.db.models import Count
        from datetime import datetime, date
        from apps.images.models import Image
        
        # Group images by date taken (or created date if no EXIF)
        user_images = Image.objects.filter(user=request.user)
        
        # Group by date
        date_groups = {}
        for image in user_images:
            # Use taken_at if available, otherwise use created_at
            image_date = image.taken_at.date() if image.taken_at else image.created_at.date()
            date_key = image_date.strftime('%Y-%m-%d')
            
            if date_key not in date_groups:
                date_groups[date_key] = {
                    'date': image_date,
                    'images': [],
                    'count': 0
                }
            
            date_groups[date_key]['images'].append(image)
            date_groups[date_key]['count'] += 1
        
        # Create album data
        albums = []
        for date_key, group in date_groups.items():
            if group['count'] > 0:  # Only include dates with images
                albums.append({
                    'id': f"date_{date_key}",
                    'name': f"Photos from {group['date'].strftime('%B %d, %Y')}",
                    'description': f"{group['count']} photos taken on this date",
                    'image_count': group['count'],
                    'date': date_key,
                    'cover_image': group['images'][0].id if group['images'] else None,
                    'type': 'auto_date'
                })
        
        # Sort by date (newest first)
        albums.sort(key=lambda x: x['date'], reverse=True)
        
        return Response({
            'message': f'Found {len(albums)} date-based albums',
            'albums': albums
        })


class AlbumsByLocationView(APIView):
    """
    Get auto-generated albums by location.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        from django.db.models import Count
        from apps.images.models import Image
        
        # Group images by location (using location_text or GPS coordinates)
        user_images = Image.objects.filter(
            user=request.user
        ).exclude(
            location_text__isnull=True, 
            gps_lat__isnull=True
        )
        
        # Group by location
        location_groups = {}
        for image in user_images:
            # Use location_text if available, otherwise create from GPS
            if image.location_text:
                location_key = image.location_text.strip()
            elif image.gps_lat and image.gps_lng:
                # Round GPS to create location groups
                lat_rounded = round(image.gps_lat, 2)
                lng_rounded = round(image.gps_lng, 2)
                location_key = f"Location {lat_rounded}, {lng_rounded}"
            else:
                continue
            
            if location_key not in location_groups:
                location_groups[location_key] = {
                    'location': location_key,
                    'images': [],
                    'count': 0
                }
            
            location_groups[location_key]['images'].append(image)
            location_groups[location_key]['count'] += 1
        
        # Create album data
        albums = []
        for location_key, group in location_groups.items():
            if group['count'] > 1:  # Only include locations with multiple images
                albums.append({
                    'id': f"location_{hash(location_key) % 1000000}",
                    'name': f"Photos from {group['location']}",
                    'description': f"{group['count']} photos taken at this location",
                    'image_count': group['count'],
                    'location': location_key,
                    'cover_image': group['images'][0].id if group['images'] else None,
                    'type': 'auto_location'
                })
        
        # Sort by image count (most photos first)
        albums.sort(key=lambda x: x['image_count'], reverse=True)
        
        return Response({
            'message': f'Found {len(albums)} location-based albums',
            'albums': albums
        })


class AlbumsByPersonView(APIView):
    """
    Get auto-generated albums by person.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        from django.db.models import Count
        from apps.images.models import Image, FaceDetection
        from apps.users.models import PersonCluster
        
        # Get person clusters for this user
        person_clusters = PersonCluster.objects.filter(user=request.user)
        
        albums = []
        
        # Create albums for each person cluster
        for cluster in person_clusters:
            # Find images with faces matching this person
            # Get face detections that belong to this cluster (simplified approach)
            cluster_faces = FaceDetection.objects.filter(
                image__user=request.user
            )
            
            # Group images by person using face similarity (simplified)
            person_images = []
            for face in cluster_faces:
                if face.image not in person_images:
                    # Simple clustering: if face embedding exists and is similar
                    if (face.face_embedding and cluster.face_embedding and 
                        self.calculate_face_similarity(face.face_embedding, cluster.face_embedding) > 0.7):
                        person_images.append(face.image)
            
            if len(person_images) > 1:  # Only include persons with multiple photos
                albums.append({
                    'id': f"person_{cluster.id}",
                    'name': cluster.name or f"Person {cluster.id}",
                    'description': f"{len(person_images)} photos of this person",
                    'image_count': len(person_images),
                    'person_id': cluster.id,
                    'confidence': cluster.confidence_score,
                    'cover_image': person_images[0].id if person_images else None,
                    'type': 'auto_person'
                })
        
        # If no person clusters exist, create basic grouping
        if not albums:
            # Group by face similarity (basic implementation)
            face_detections = FaceDetection.objects.filter(
                image__user=request.user
            ).exclude(face_embedding_json__isnull=True)
            
            # Simple face grouping
            face_groups = {}
            for face in face_detections:
                # Use face_id as a simple grouping mechanism
                person_key = f"unknown_person_{face.id % 10}"  # Simple grouping
                
                if person_key not in face_groups:
                    face_groups[person_key] = []
                
                if face.image not in face_groups[person_key]:
                    face_groups[person_key].append(face.image)
            
            # Create albums for face groups
            for person_key, images in face_groups.items():
                if len(images) > 1:
                    albums.append({
                        'id': person_key,
                        'name': f"Unknown Person {person_key.split('_')[-1]}",
                        'description': f"{len(images)} photos of this person",
                        'image_count': len(images),
                        'person_id': person_key,
                        'confidence': 0.5,
                        'cover_image': images[0].id if images else None,
                        'type': 'auto_person'
                    })
        
        # Sort by image count (most photos first)
        albums.sort(key=lambda x: x['image_count'], reverse=True)
        
        return Response({
            'message': f'Found {len(albums)} person-based albums',
            'albums': albums
        })
    
    def calculate_face_similarity(self, embedding1, embedding2):
        """Calculate similarity between two face embeddings."""
        try:
            import numpy as np
            
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # Calculate cosine similarity
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            return float((similarity + 1) / 2)  # Convert to 0-1 range
            
        except Exception:
            return 0.0