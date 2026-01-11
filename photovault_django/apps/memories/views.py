from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.http import Http404
from datetime import date
from .models import Memory, FlashbackReel, MemoryEngagement, MemoryPreferences
from .serializers import (
    MemorySerializer, FlashbackReelSerializer, 
    MemoryEngagementSerializer, MemoryPreferencesSerializer
)
from .services import MemoryEngine, MemoryMetadataService


class MemoryViewSet(viewsets.ModelViewSet):
    """ViewSet for Memory model"""
    serializer_class = MemorySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Memory.objects.filter(user=self.request.user)


class FlashbackReelViewSet(viewsets.ModelViewSet):
    """ViewSet for FlashbackReel model"""
    serializer_class = FlashbackReelSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return FlashbackReel.objects.filter(user=self.request.user)


class DailyMemoriesView(APIView):
    """API view for daily memories discovery"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """
        Get daily memories for the current user.
        
        Query parameters:
        - date: Target date (YYYY-MM-DD format, defaults to today)
        """
        try:
            # Parse target date from query params
            date_str = request.query_params.get('date')
            if date_str:
                target_date = date.fromisoformat(date_str)
            else:
                target_date = date.today()
            
            # Discover memories using MemoryEngine
            memory_engine = MemoryEngine()
            memories = memory_engine.discover_daily_memories(request.user.id, target_date)
            
            # Serialize memories
            serializer = MemorySerializer(memories, many=True)
            
            return Response({
                'target_date': target_date,
                'memories': serializer.data,
                'count': len(memories)
            })
            
        except ValueError as e:
            return Response(
                {'error': f'Invalid date format: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': f'Failed to discover memories: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class MemoryDetailView(APIView):
    """API view for memory details with photo metadata"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, memory_id):
        """Get detailed memory information including photo metadata"""
        # Verify memory belongs to user (this will raise Http404 if not found)
        memory = get_object_or_404(Memory, id=memory_id, user=request.user)
        
        try:
            # Get memory context and metadata
            memory_context = MemoryMetadataService.get_memory_context(memory)
            engagement_summary = MemoryMetadataService.get_engagement_summary(memory)
            
            # Get photo metadata for all photos in memory
            photos_metadata = []
            for memory_photo in memory.memoryphoto_set.all():
                photo_metadata = MemoryMetadataService.extract_photo_metadata(memory_photo.photo)
                photo_metadata['significance_score'] = memory_photo.significance_score
                photo_metadata['order'] = memory_photo.order
                photos_metadata.append(photo_metadata)
            
            # Serialize memory
            memory_serializer = MemorySerializer(memory)
            
            return Response({
                'memory': memory_serializer.data,
                'context': memory_context,
                'engagement': engagement_summary,
                'photos_metadata': photos_metadata
            })
            
        except Exception as e:
            return Response(
                {'error': f'Failed to get memory details: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class MemoryEngagementView(APIView):
    """API view for memory engagement tracking"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, memory_id):
        """
        Track user engagement with a memory.
        
        Request body:
        - interaction_type: Type of interaction (view, share, like, download)
        """
        # Verify memory belongs to user (this will raise Http404 if not found)
        memory = get_object_or_404(Memory, id=memory_id, user=request.user)
        
        try:
            # Get interaction type from request
            interaction_type = request.data.get('interaction_type')
            if not interaction_type:
                return Response(
                    {'error': 'interaction_type is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate interaction type
            valid_types = ['view', 'share', 'like', 'download']
            if interaction_type not in valid_types:
                return Response(
                    {'error': f'Invalid interaction_type. Must be one of: {valid_types}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Track engagement using MemoryEngine
            memory_engine = MemoryEngine()
            
            # Get client IP and user agent
            ip_address = self._get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            memory_engine.track_memory_engagement(
                memory_id=memory_id,
                interaction_type=interaction_type,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            return Response({
                'message': 'Engagement tracked successfully',
                'memory_id': memory_id,
                'interaction_type': interaction_type
            })
            
        except Exception as e:
            return Response(
                {'error': f'Failed to track engagement: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _get_client_ip(self, request):
        """Extract client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class MemoryAnalyticsView(APIView):
    """API view for memory analytics"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """
        Get memory analytics for the current user.
        
        Query parameters:
        - days: Number of days to look back (default: 30)
        """
        try:
            # Parse days parameter
            days = int(request.query_params.get('days', 30))
            if days <= 0:
                days = 30
            
            # Get analytics using MemoryEngine
            memory_engine = MemoryEngine()
            analytics = memory_engine.get_memory_analytics(request.user.id, days)
            
            return Response(analytics)
            
        except ValueError:
            return Response(
                {'error': 'Invalid days parameter. Must be a positive integer.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': f'Failed to get analytics: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class MemoryPreferencesView(APIView):
    """API view for memory preferences"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get memory preferences for the current user"""
        try:
            preferences, created = MemoryPreferences.objects.get_or_create(
                user=request.user
            )
            
            serializer = MemoryPreferencesSerializer(preferences)
            return Response(serializer.data)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to get preferences: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def post(self, request):
        """Update memory preferences for the current user"""
        try:
            preferences, created = MemoryPreferences.objects.get_or_create(
                user=request.user
            )
            
            serializer = MemoryPreferencesSerializer(preferences, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            else:
                return Response(
                    {'error': 'Invalid data', 'details': serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            return Response(
                {'error': f'Failed to update preferences: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )