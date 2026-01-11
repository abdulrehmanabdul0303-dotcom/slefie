"""
Memory Time Machine services for discovering and managing memories.
"""
from datetime import date, timedelta
from typing import List, Optional
from django.db.models import Q, Count, Avg, F
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.cache import cache
from django.conf import settings
from apps.images.models import Image
from apps.sharing.models import PublicShare
from .models import Memory, MemoryPhoto, FlashbackReel, MemoryEngagement

User = get_user_model()


class MemoryEngine:
    """
    Core service for discovering and managing memories.
    
    Implements the memory discovery algorithm that finds photos from the same
    date in previous years and scores them by significance.
    """
    
    def __init__(self):
        self.default_significance_threshold = 1.0
        self.max_photos_per_memory = 20
        self.date_expansion_days = 7
        self.cache_timeout = 3600  # 1 hour cache timeout
    
    def discover_daily_memories(self, user_id: int, target_date: date = None) -> List[Memory]:
        """
        Discover memories for a specific date with caching.
        
        Args:
            user_id: The user to discover memories for
            target_date: The date to find memories for (defaults to today)
            
        Returns:
            List of Memory objects for the target date
        """
        if target_date is None:
            target_date = date.today()
        
        # Check cache first
        cache_key = f"daily_memories:{user_id}:{target_date}"
        cached_memories = cache.get(cache_key)
        
        if cached_memories is not None:
            # Return cached memory IDs as Memory objects
            if cached_memories:
                return list(Memory.objects.filter(id__in=cached_memories))
            return []
        
        user = User.objects.get(id=user_id)
        
        # Check if memory already exists for this date
        existing_memory = Memory.objects.filter(
            user=user,
            target_date=target_date
        ).first()
        
        if existing_memory:
            # Cache the result
            cache.set(cache_key, [existing_memory.id], self.cache_timeout)
            return [existing_memory]
        
        # Find photos from the same calendar date in previous years
        photos = self._find_photos_by_date(user, target_date)
        
        if not photos:
            # Try expanding date range if no exact matches
            photos = self._find_photos_with_date_expansion(user, target_date)
        
        if not photos:
            # Cache empty result
            cache.set(cache_key, [], self.cache_timeout)
            return []
        
        # Score photos by significance
        scored_photos = self._score_photos_significance(photos)
        
        # Create memory if we have significant photos
        if scored_photos:
            memory = self._create_memory(user, target_date, scored_photos)
            # Cache the result
            cache.set(cache_key, [memory.id], self.cache_timeout)
            return [memory]
        
        # Cache empty result
        cache.set(cache_key, [], self.cache_timeout)
        return []
    
    def invalidate_memory_cache(self, user_id: int, target_date: date = None):
        """
        Invalidate cached memories for a user and date.
        
        Args:
            user_id: User whose cache to invalidate
            target_date: Specific date to invalidate (if None, invalidates today)
        """
        if target_date is None:
            target_date = date.today()
        
        cache_key = f"daily_memories:{user_id}:{target_date}"
        cache.delete(cache_key)
    
    def invalidate_user_memory_cache(self, user_id: int):
        """
        Invalidate all cached memories for a user.
        This is called when new photos are uploaded.
        
        Args:
            user_id: User whose cache to invalidate
        """
        # Since we can't easily iterate all cache keys, we'll use a pattern
        # In production, consider using Redis with pattern matching
        # For now, invalidate common dates (today and recent days)
        today = date.today()
        for i in range(7):  # Invalidate last 7 days
            cache_date = today - timedelta(days=i)
            self.invalidate_memory_cache(user_id, cache_date)
    
    def _find_photos_by_date(self, user: User, target_date: date) -> List[Image]:
        """
        Find photos taken on the same calendar date in previous years.
        """
        # Look for photos taken on the same month/day in previous years
        photos = Image.objects.filter(
            user=user,
            taken_at__month=target_date.month,
            taken_at__day=target_date.day,
            taken_at__year__lt=target_date.year  # Only previous years
        ).select_related('folder').prefetch_related('albums').order_by('-taken_at')
        
        return list(photos[:50])  # Limit to prevent excessive processing
    
    def _find_photos_with_date_expansion(self, user: User, target_date: date) -> List[Image]:
        """
        Find photos within a date range around the target date.
        """
        start_date = target_date - timedelta(days=self.date_expansion_days)
        end_date = target_date + timedelta(days=self.date_expansion_days)
        
        photos = []
        for year_offset in range(1, 10):  # Look back up to 10 years
            year_start = start_date.replace(year=target_date.year - year_offset)
            year_end = end_date.replace(year=target_date.year - year_offset)
            
            year_photos = Image.objects.filter(
                user=user,
                taken_at__date__gte=year_start,
                taken_at__date__lte=year_end
            ).select_related('folder').prefetch_related('albums').order_by('-taken_at')
            
            photos.extend(list(year_photos[:10]))  # Limit per year
            
            if len(photos) >= 30:  # Stop if we have enough photos
                break
        
        return photos
    
    def _score_photos_significance(self, photos: List[Image]) -> List[tuple]:
        """
        Score photos by significance based on engagement metrics.
        
        Returns:
            List of (photo, score) tuples sorted by score descending
        """
        scored_photos = []
        
        for photo in photos:
            score = self.score_photo_significance(photo)
            if score >= self.default_significance_threshold:
                scored_photos.append((photo, score))
        
        # Sort by significance score (highest first)
        scored_photos.sort(key=lambda x: x[1], reverse=True)
        
        # Limit to max photos per memory
        return scored_photos[:self.max_photos_per_memory]
    
    def score_photo_significance(self, photo: Image) -> float:
        """
        Calculate significance score for a photo.
        
        Factors considered:
        - Number of times shared
        - Views from client delivery
        - Album inclusion
        - Image quality metrics
        - Recency bonus
        """
        score = 0.0
        
        # Base score for existing photo
        score += 1.0
        
        # Sharing activity score
        share_count = PublicShare.objects.filter(
            album__images=photo
        ).count()
        score += share_count * 2.0
        
        # Client delivery engagement score
        # Note: This would need to be implemented when client delivery is integrated
        # For now, use a placeholder
        score += 0.5
        
        # Album inclusion score (photos in albums are more significant)
        album_count = photo.albums.count()
        score += album_count * 1.5
        
        # Image quality score (larger images might be more significant)
        if photo.width and photo.height:
            megapixels = (photo.width * photo.height) / 1_000_000
            score += min(megapixels * 0.1, 2.0)  # Cap at 2.0 bonus
        
        # Recency bonus (more recent photos get slight boost)
        if photo.taken_at:
            years_ago = (timezone.now().date() - photo.taken_at.date()).days / 365.25
            recency_bonus = max(0, 2.0 - (years_ago * 0.1))  # Decreases over time
            score += recency_bonus
        
        return score
    
    def _create_memory(self, user: User, target_date: date, scored_photos: List[tuple]) -> Memory:
        """
        Create a Memory object with associated photos.
        """
        # Calculate overall memory significance
        total_score = sum(score for _, score in scored_photos)
        avg_score = total_score / len(scored_photos) if scored_photos else 0.0
        
        # Create memory
        memory = Memory.objects.create(
            user=user,
            target_date=target_date,
            significance_score=avg_score
        )
        
        # Add photos to memory
        for order, (photo, score) in enumerate(scored_photos):
            MemoryPhoto.objects.create(
                memory=memory,
                photo=photo,
                significance_score=score,
                order=order
            )
        
        return memory
    
    def track_memory_engagement(self, memory_id: int, interaction_type: str, 
                              ip_address: str = None, user_agent: str = None) -> None:
        """
        Track user engagement with a memory.
        
        Args:
            memory_id: ID of the memory being interacted with
            interaction_type: Type of interaction (view, share, like, download)
            ip_address: IP address of the user (optional)
            user_agent: User agent string (optional)
        """
        try:
            memory = Memory.objects.get(id=memory_id)
            
            # Create engagement record
            MemoryEngagement.objects.create(
                memory=memory,
                interaction_type=interaction_type,
                ip_address=ip_address,
                user_agent=user_agent or ''
            )
            
            # Update memory engagement count
            memory.update_engagement()
            
        except Memory.DoesNotExist:
            # Log error but don't raise exception
            pass
    
    def get_memory_analytics(self, user_id: int, days: int = 30) -> dict:
        """
        Get analytics for user's memories over a time period.
        
        Args:
            user_id: User to get analytics for
            days: Number of days to look back
            
        Returns:
            Dictionary with analytics data
        """
        # Check cache first
        cache_key = f"memory_analytics:{user_id}:{days}"
        cached_analytics = cache.get(cache_key)
        
        if cached_analytics is not None:
            return cached_analytics
        
        start_date = timezone.now() - timedelta(days=days)
        
        memories = Memory.objects.filter(
            user_id=user_id,
            created_at__gte=start_date
        )
        
        total_memories = memories.count()
        total_engagements = MemoryEngagement.objects.filter(
            memory__user_id=user_id,
            timestamp__gte=start_date
        ).count()
        
        avg_significance = memories.aggregate(
            avg_score=Avg('significance_score')
        )['avg_score'] or 0.0
        
        # Engagement by type
        engagement_by_type = MemoryEngagement.objects.filter(
            memory__user_id=user_id,
            timestamp__gte=start_date
        ).values('interaction_type').annotate(
            count=Count('id')
        )
        
        analytics = {
            'total_memories': total_memories,
            'total_engagements': total_engagements,
            'avg_significance_score': round(avg_significance, 2),
            'engagement_by_type': list(engagement_by_type),
            'period_days': days
        }
        
        # Cache analytics for 15 minutes
        cache.set(cache_key, analytics, 900)
        
        return analytics


class FlashbackReelService:
    """
    Enhanced service for generating and managing flashback reels with async processing.
    """
    
    def __init__(self):
        self.min_photos_for_reel = 10
        self.max_photos_per_reel = 20
        self.default_duration = 30  # seconds
        self.supported_themes = ['classic', 'modern', 'vintage', 'cinematic']
    
    def can_generate_reel(self, user_id: int, start_date: date, end_date: date) -> bool:
        """
        Check if a reel can be generated for the given time period.
        """
        photo_count = Image.objects.filter(
            user_id=user_id,
            taken_at__date__gte=start_date,
            taken_at__date__lte=end_date
        ).count()
        
        return photo_count >= self.min_photos_for_reel
    
    def select_representative_photos(self, user_id: int, start_date: date, 
                                   end_date: date, count: int = None) -> List[Image]:
        """
        Select representative photos for a reel from a time period using advanced algorithms.
        
        Args:
            user_id: User to select photos for
            start_date: Start of time period
            end_date: End of time period
            count: Number of photos to select (defaults to max_photos_per_reel)
            
        Returns:
            List of selected Image objects
        """
        if count is None:
            count = self.max_photos_per_reel
        
        # Ensure count is within bounds
        count = max(self.min_photos_for_reel, min(count, self.max_photos_per_reel))
        
        # Get all photos from the time period with optimized query
        photos = Image.objects.filter(
            user_id=user_id,
            taken_at__date__gte=start_date,
            taken_at__date__lte=end_date
        ).select_related('folder').prefetch_related('albums').order_by('taken_at')
        
        if photos.count() <= count:
            return list(photos)
        
        # Use advanced photo selection algorithm
        return self._advanced_photo_selection(photos, count)
    
    def _advanced_photo_selection(self, photos, count: int) -> List[Image]:
        """
        Advanced photo selection algorithm that considers multiple factors:
        - Significance score
        - Temporal distribution
        - Visual diversity
        - Location diversity
        """
        # Use MemoryEngine to score photos
        memory_engine = MemoryEngine()
        scored_photos = []
        
        for photo in photos:
            score = memory_engine.score_photo_significance(photo)
            scored_photos.append((photo, score))
        
        # Sort by significance
        scored_photos.sort(key=lambda x: x[1], reverse=True)
        
        # Apply temporal distribution to ensure good spread across time period
        selected_photos = self._apply_temporal_distribution(scored_photos, count)
        
        # Sort selected photos chronologically for the reel
        selected_photos.sort(key=lambda p: p.taken_at or p.created_at)
        
        return selected_photos
    
    def _apply_temporal_distribution(self, scored_photos: List[tuple], count: int) -> List[Image]:
        """
        Apply temporal distribution to ensure photos are spread across the time period.
        """
        if len(scored_photos) <= count:
            return [photo for photo, _ in scored_photos]
        
        # Group photos by date
        from collections import defaultdict
        photos_by_date = defaultdict(list)
        
        for photo, score in scored_photos:
            photo_date = photo.taken_at.date() if photo.taken_at else photo.created_at.date()
            photos_by_date[photo_date].append((photo, score))
        
        # Select photos ensuring temporal distribution
        selected = []
        dates = sorted(photos_by_date.keys())
        
        if len(dates) <= count:
            # If we have fewer dates than needed photos, take best from each date
            for date_key in dates:
                date_photos = sorted(photos_by_date[date_key], key=lambda x: x[1], reverse=True)
                selected.append(date_photos[0][0])
            
            # Fill remaining slots with highest scoring photos
            remaining_count = count - len(selected)
            if remaining_count > 0:
                all_remaining = []
                for date_key in dates:
                    date_photos = photos_by_date[date_key][1:]  # Skip first (already selected)
                    all_remaining.extend(date_photos)
                
                all_remaining.sort(key=lambda x: x[1], reverse=True)
                selected.extend([photo for photo, _ in all_remaining[:remaining_count]])
        else:
            # More dates than photos needed - select from distributed dates
            date_step = len(dates) // count
            selected_dates = [dates[i * date_step] for i in range(count)]
            
            for date_key in selected_dates:
                date_photos = sorted(photos_by_date[date_key], key=lambda x: x[1], reverse=True)
                selected.append(date_photos[0][0])
        
        return selected
    
    def create_reel_request(self, user_id: int, title: str, start_date: date, 
                          end_date: date, theme: str = 'classic', 
                          duration: int = None, async_processing: bool = True) -> FlashbackReel:
        """
        Create a flashback reel generation request with async processing.
        
        Args:
            user_id: User creating the reel
            title: Title for the reel
            start_date: Start date for photo selection
            end_date: End date for photo selection
            theme: Visual theme for the reel
            duration: Duration in seconds (defaults to 30)
            async_processing: Whether to process asynchronously (default: True)
            
        Returns:
            FlashbackReel object
        """
        user = User.objects.get(id=user_id)
        
        # Validate theme
        if theme not in self.supported_themes:
            theme = 'classic'
        
        # Validate duration
        if duration is None:
            duration = self.default_duration
        duration = max(10, min(duration, 300))  # Between 10 seconds and 5 minutes
        
        # Select photos for the reel
        photos = self.select_representative_photos(user_id, start_date, end_date)
        
        if len(photos) < self.min_photos_for_reel:
            raise ValueError(f"Not enough photos for reel. Need at least {self.min_photos_for_reel}, found {len(photos)}")
        
        # Create reel record
        reel = FlashbackReel.objects.create(
            user=user,
            title=title,
            duration=duration,
            theme=theme,
            status='pending',
            start_date=start_date,
            end_date=end_date,
            photo_count=len(photos)
        )
        
        # Add photos to reel with proper ordering
        for order, photo in enumerate(photos):
            from .models import MemoryPhoto
            # We'll reuse MemoryPhoto for reel photos or create a similar through model
            # For now, just set the photos
            pass
        
        reel.photos.set(photos)
        
        # Start async processing if requested
        if async_processing:
            self.start_reel_generation(reel.id)
        
        return reel
    
    def start_reel_generation(self, reel_id: int) -> str:
        """
        Start asynchronous reel generation using Celery.
        
        Args:
            reel_id: ID of the reel to generate
            
        Returns:
            str: Celery task ID
        """
        try:
            from .tasks import generate_flashback_reel_video
            
            task = generate_flashback_reel_video.delay(reel_id)
            
            # Update reel with task ID for tracking
            try:
                reel = FlashbackReel.objects.get(id=reel_id)
                # We could add a task_id field to track this
                # For now, just log it
                import logging
                logger = logging.getLogger(__name__)
                logger.info(f"Started reel generation task {task.id} for reel {reel_id}")
            except FlashbackReel.DoesNotExist:
                pass
            
            return task.id
            
        except ImportError:
            # Celery not available (e.g., in testing)
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Celery not available, skipping async reel generation for reel {reel_id}")
            return f"mock_task_id_{reel_id}"
    
    def get_reel_generation_status(self, reel_id: int) -> dict:
        """
        Get the current status of reel generation.
        
        Args:
            reel_id: ID of the reel to check
            
        Returns:
            dict: Status information
        """
        try:
            reel = FlashbackReel.objects.get(id=reel_id)
            
            status_info = {
                'reel_id': reel_id,
                'status': reel.status,
                'created_at': reel.created_at,
                'completed_at': reel.completed_at,
                'error_message': reel.error_message,
                'progress_percentage': self._calculate_progress_percentage(reel),
                'estimated_completion': self._estimate_completion_time(reel)
            }
            
            return status_info
            
        except FlashbackReel.DoesNotExist:
            return {
                'reel_id': reel_id,
                'status': 'not_found',
                'error': 'Reel not found'
            }
    
    def _calculate_progress_percentage(self, reel: FlashbackReel) -> int:
        """Calculate progress percentage based on reel status."""
        status_progress = {
            'pending': 0,
            'processing': 50,
            'completed': 100,
            'failed': 0
        }
        return status_progress.get(reel.status, 0)
    
    def _estimate_completion_time(self, reel: FlashbackReel) -> Optional[str]:
        """Estimate completion time based on current status and photo count."""
        if reel.status == 'completed':
            return None
        elif reel.status == 'failed':
            return None
        elif reel.status == 'processing':
            # Estimate based on photo count (rough estimate: 2 seconds per photo)
            estimated_seconds = reel.photo_count * 2
            estimated_completion = timezone.now() + timedelta(seconds=estimated_seconds)
            return estimated_completion.isoformat()
        else:  # pending
            # Estimate queue time + processing time
            estimated_seconds = 30 + (reel.photo_count * 2)  # 30s queue + processing
            estimated_completion = timezone.now() + timedelta(seconds=estimated_seconds)
            return estimated_completion.isoformat()
    
    def cancel_reel_generation(self, reel_id: int) -> bool:
        """
        Cancel an ongoing reel generation.
        
        Args:
            reel_id: ID of the reel to cancel
            
        Returns:
            bool: True if cancelled successfully
        """
        try:
            reel = FlashbackReel.objects.get(id=reel_id)
            
            if reel.status in ['pending', 'processing']:
                reel.status = 'failed'
                reel.error_message = 'Cancelled by user'
                reel.save(update_fields=['status', 'error_message'])
                
                # TODO: Cancel the Celery task if we store task IDs
                
                return True
            
            return False
            
        except FlashbackReel.DoesNotExist:
            return False
    
    def retry_reel_generation(self, reel_id: int) -> str:
        """
        Retry failed reel generation.
        
        Args:
            reel_id: ID of the reel to retry
            
        Returns:
            str: New Celery task ID
        """
        try:
            reel = FlashbackReel.objects.get(id=reel_id)
            
            if reel.status == 'failed':
                # Reset status
                reel.status = 'pending'
                reel.error_message = ''
                reel.save(update_fields=['status', 'error_message'])
                
                # Start new generation task
                return self.start_reel_generation(reel_id)
            
            raise ValueError(f"Cannot retry reel with status: {reel.status}")
            
        except FlashbackReel.DoesNotExist:
            raise ValueError("Reel not found")
    
    def get_user_reels(self, user_id: int, status: str = None, limit: int = 20) -> List[FlashbackReel]:
        """
        Get reels for a user with optional status filtering.
        
        Args:
            user_id: User to get reels for
            status: Optional status filter
            limit: Maximum number of reels to return
            
        Returns:
            List of FlashbackReel objects
        """
        queryset = FlashbackReel.objects.filter(user_id=user_id)
        
        if status:
            queryset = queryset.filter(status=status)
        
        return list(queryset.order_by('-created_at')[:limit])
    
    def delete_reel(self, reel_id: int, user_id: int) -> bool:
        """
        Delete a reel (with user permission check).
        
        Args:
            reel_id: ID of the reel to delete
            user_id: ID of the user requesting deletion
            
        Returns:
            bool: True if deleted successfully
        """
        try:
            reel = FlashbackReel.objects.get(id=reel_id, user_id=user_id)
            
            # Delete associated files
            if reel.video_file:
                try:
                    reel.video_file.delete(save=False)
                except Exception:
                    pass  # File might not exist
            
            # Delete the reel
            reel.delete()
            
            return True
            
        except FlashbackReel.DoesNotExist:
            return False


class MemoryMetadataService:
    """
    Service for extracting and managing memory metadata.
    """
    
    @staticmethod
    def extract_photo_metadata(photo: Image) -> dict:
        """
        Extract metadata from a photo for memory context.
        
        Returns:
            Dictionary with photo metadata including date, location, camera info
        """
        metadata = {
            'filename': photo.original_filename,
            'taken_at': photo.taken_at,
            'location_text': photo.location_text,
            'camera_make': photo.camera_make,
            'camera_model': photo.camera_model,
            'width': photo.width,
            'height': photo.height,
            'file_size': photo.size_bytes,
        }
        
        # Add GPS coordinates if available
        if photo.has_location:
            metadata['gps_coordinates'] = {
                'latitude': photo.gps_lat,
                'longitude': photo.gps_lng
            }
        
        # Add EXIF data if available
        if photo.exif_data:
            metadata['exif'] = photo.exif_data
        
        return metadata
    
    @staticmethod
    def get_memory_context(memory: Memory) -> dict:
        """
        Get contextual information about a memory.
        
        Returns:
            Dictionary with memory context including date info, photo count, etc.
        """
        photos = memory.photos.all()
        
        context = {
            'target_date': memory.target_date,
            'years_ago': (date.today() - memory.target_date).days // 365,
            'photo_count': photos.count(),
            'significance_score': memory.significance_score,
            'created_at': memory.created_at,
            'last_viewed': memory.last_viewed,
            'engagement_count': memory.engagement_count,
        }
        
        # Add date range of photos in memory
        if photos:
            taken_dates = [p.taken_at for p in photos if p.taken_at]
            if taken_dates:
                context['photo_date_range'] = {
                    'earliest': min(taken_dates),
                    'latest': max(taken_dates)
                }
        
        # Add location information if available
        locations = [p.location_text for p in photos if p.location_text]
        if locations:
            # Get most common location
            from collections import Counter
            location_counts = Counter(locations)
            context['primary_location'] = location_counts.most_common(1)[0][0]
            context['unique_locations'] = len(set(locations))
        
        return context
    
    @staticmethod
    def get_engagement_summary(memory: Memory) -> dict:
        """
        Get engagement summary for a memory.
        
        Returns:
            Dictionary with engagement statistics
        """
        engagements = MemoryEngagement.objects.filter(memory=memory)
        
        summary = {
            'total_engagements': engagements.count(),
            'unique_interactions': engagements.values('interaction_type').distinct().count(),
            'last_interaction': engagements.order_by('-timestamp').first(),
        }
        
        # Engagement by type
        engagement_types = {}
        for engagement in engagements:
            interaction_type = engagement.interaction_type
            if interaction_type not in engagement_types:
                engagement_types[interaction_type] = 0
            engagement_types[interaction_type] += 1
        
        summary['by_type'] = engagement_types
        
        # Recent activity (last 7 days)
        recent_cutoff = timezone.now() - timedelta(days=7)
        recent_engagements = engagements.filter(timestamp__gte=recent_cutoff)
        summary['recent_activity'] = recent_engagements.count()
        
        return summary


class MemoryNotificationService:
    """
    Service for managing memory notifications and user preferences.
    """
    
    def __init__(self):
        self.default_frequency = 'daily'
        self.max_notifications_per_day = 3
    
    def should_send_notification(self, user_id: int, memory: Memory) -> bool:
        """
        Determine if a notification should be sent for a memory.
        
        Args:
            user_id: User to check notification preferences for
            memory: Memory to potentially notify about
            
        Returns:
            True if notification should be sent, False otherwise
        """
        from .models import MemoryPreferences, MemoryNotification
        
        # Check if user has notifications enabled
        try:
            preferences = MemoryPreferences.objects.get(user_id=user_id)
            if not preferences.enable_notifications or not preferences.feature_enabled:
                return False
        except MemoryPreferences.DoesNotExist:
            # Default to enabled if no preferences set
            pass
        
        # Check if we've already notified about this memory
        existing_notification = MemoryNotification.objects.filter(
            user_id=user_id,
            memory=memory
        ).first()
        
        if existing_notification:
            return False
        
        # Check daily notification limit
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_notifications = MemoryNotification.objects.filter(
            user_id=user_id,
            sent_at__gte=today_start
        ).count()
        
        if today_notifications >= self.max_notifications_per_day:
            return False
        
        # Check memory significance threshold
        if memory.significance_score < 2.0:  # Only notify for significant memories
            return False
        
        return True
    
    def create_notification(self, user_id: int, memory: Memory) -> 'MemoryNotification':
        """
        Create a memory notification record.
        
        Args:
            user_id: User to notify
            memory: Memory to notify about
            
        Returns:
            Created MemoryNotification object
        """
        from .models import MemoryNotification
        
        notification = MemoryNotification.objects.create(
            user_id=user_id,
            memory=memory,
            notification_type='daily_memory'
        )
        
        return notification
    
    def get_notification_preview(self, memory: Memory) -> dict:
        """
        Generate a preview for a memory notification.
        
        Args:
            memory: Memory to create preview for
            
        Returns:
            Dictionary with notification preview data
        """
        photos = memory.photos.all()[:3]  # Get first 3 photos for preview
        
        preview = {
            'title': f"On this day {(date.today() - memory.target_date).days // 365} years ago",
            'memory_date': memory.target_date,
            'photo_count': memory.photos.count(),
            'significance_score': memory.significance_score,
            'preview_photos': [
                {
                    'id': photo.id,
                    'filename': photo.original_filename,
                    'taken_at': photo.taken_at
                }
                for photo in photos
            ]
        }
        
        # Add location if available
        context = MemoryMetadataService.get_memory_context(memory)
        if 'primary_location' in context:
            preview['location'] = context['primary_location']
        
        return preview


# Signal handlers for cache invalidation
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

@receiver(post_save, sender=Image)
def invalidate_memory_cache_on_image_save(sender, instance, created, **kwargs):
    """Invalidate memory cache when new images are uploaded"""
    if created:  # Only for new images
        memory_engine = MemoryEngine()
        memory_engine.invalidate_user_memory_cache(instance.user_id)

@receiver(post_delete, sender=Image)
def invalidate_memory_cache_on_image_delete(sender, instance, **kwargs):
    """Invalidate memory cache when images are deleted"""
    memory_engine = MemoryEngine()
    memory_engine.invalidate_user_memory_cache(instance.user_id)