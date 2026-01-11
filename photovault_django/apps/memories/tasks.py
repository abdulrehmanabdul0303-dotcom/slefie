"""
Celery tasks for Memory Time Machine background processing.

These tasks handle asynchronous operations like:
- Flashback reel video generation
- Memory discovery batch processing
- Notification sending
"""
import logging
from datetime import date, timedelta
from typing import List, Optional
from celery import shared_task
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.files.base import ContentFile
from .models import FlashbackReel, Memory, MemoryNotification
from .services import FlashbackReelService, MemoryEngine, MemoryNotificationService

User = get_user_model()
logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def generate_flashback_reel_video(self, reel_id: int):
    """
    Generate video file for a flashback reel.
    
    This task handles the asynchronous video generation process:
    1. Retrieve reel and photos
    2. Generate video using external service or local processing
    3. Update reel status and file
    4. Handle errors and retries
    
    Args:
        reel_id: ID of the FlashbackReel to process
        
    Returns:
        dict: Task result with status and details
    """
    try:
        logger.info(f"Starting video generation for reel {reel_id}")
        
        # Get the reel
        try:
            reel = FlashbackReel.objects.get(id=reel_id)
        except FlashbackReel.DoesNotExist:
            logger.error(f"Reel {reel_id} not found")
            return {'status': 'error', 'message': 'Reel not found'}
        
        # Update status to processing
        reel.status = 'processing'
        reel.save(update_fields=['status'])
        
        # Get photos for the reel
        photos = list(reel.photos.all().order_by('memoryphoto__order'))
        
        if not photos:
            logger.error(f"No photos found for reel {reel_id}")
            reel.mark_failed("No photos available for reel generation")
            return {'status': 'error', 'message': 'No photos available'}
        
        # Generate video (placeholder implementation)
        # In production, this would integrate with a video generation service
        video_content = _generate_video_placeholder(reel, photos)
        
        # Save video file
        video_filename = f"flashback_reel_{reel_id}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.mp4"
        reel.video_file.save(
            video_filename,
            ContentFile(video_content),
            save=False
        )
        
        # Mark as completed
        reel.mark_completed()
        
        logger.info(f"Successfully generated video for reel {reel_id}")
        
        # Create share link if auto-sharing is enabled
        _create_reel_share_link(reel)
        
        return {
            'status': 'success',
            'reel_id': reel_id,
            'video_file': reel.video_file.name if reel.video_file else None,
            'duration': reel.duration,
            'photo_count': len(photos)
        }
        
    except Exception as exc:
        logger.error(f"Error generating video for reel {reel_id}: {str(exc)}")
        
        # Update reel status
        try:
            reel = FlashbackReel.objects.get(id=reel_id)
            reel.mark_failed(f"Video generation failed: {str(exc)}")
        except FlashbackReel.DoesNotExist:
            pass
        
        # Retry if we haven't exceeded max retries
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying video generation for reel {reel_id} (attempt {self.request.retries + 1})")
            raise self.retry(countdown=60 * (2 ** self.request.retries))  # Exponential backoff
        
        return {
            'status': 'error',
            'reel_id': reel_id,
            'message': str(exc),
            'retries': self.request.retries
        }


@shared_task
def batch_discover_memories(user_ids: List[int] = None, target_date: date = None):
    """
    Batch process memory discovery for multiple users.
    
    This task can be run daily to discover memories for all users
    or a specific subset of users.
    
    Args:
        user_ids: List of user IDs to process (if None, processes all users)
        target_date: Date to discover memories for (defaults to today)
        
    Returns:
        dict: Summary of batch processing results
    """
    if target_date is None:
        target_date = date.today()
    
    logger.info(f"Starting batch memory discovery for date {target_date}")
    
    # Get users to process
    if user_ids:
        users = User.objects.filter(id__in=user_ids, is_active=True)
    else:
        users = User.objects.filter(is_active=True)
    
    memory_engine = MemoryEngine()
    results = {
        'processed_users': 0,
        'memories_created': 0,
        'errors': 0,
        'target_date': str(target_date)
    }
    
    for user in users:
        try:
            memories = memory_engine.discover_daily_memories(user.id, target_date)
            results['processed_users'] += 1
            results['memories_created'] += len(memories)
            
            logger.debug(f"Discovered {len(memories)} memories for user {user.id}")
            
        except Exception as e:
            logger.error(f"Error discovering memories for user {user.id}: {str(e)}")
            results['errors'] += 1
    
    logger.info(f"Batch memory discovery completed: {results}")
    return results


@shared_task
def send_memory_notifications(user_ids: List[int] = None):
    """
    Send memory notifications to users who have significant memories.
    
    This task checks for users with significant memories and sends
    notifications based on their preferences.
    
    Args:
        user_ids: List of user IDs to process (if None, processes all users)
        
    Returns:
        dict: Summary of notification sending results
    """
    logger.info("Starting memory notification sending")
    
    # Get users to process
    if user_ids:
        users = User.objects.filter(id__in=user_ids, is_active=True)
    else:
        users = User.objects.filter(is_active=True)
    
    notification_service = MemoryNotificationService()
    results = {
        'processed_users': 0,
        'notifications_sent': 0,
        'skipped': 0,
        'errors': 0
    }
    
    today = date.today()
    
    for user in users:
        try:
            results['processed_users'] += 1
            
            # Get today's memories for the user
            memories = Memory.objects.filter(
                user=user,
                target_date=today,
                significance_score__gte=2.0  # Only significant memories
            )
            
            for memory in memories:
                if notification_service.should_send_notification(user.id, memory):
                    # Create notification record
                    notification = notification_service.create_notification(user.id, memory)
                    
                    # In production, this would send actual email/push notification
                    logger.info(f"Would send notification to {user.email} for memory {memory.id}")
                    
                    results['notifications_sent'] += 1
                else:
                    results['skipped'] += 1
                    
        except Exception as e:
            logger.error(f"Error sending notifications for user {user.id}: {str(e)}")
            results['errors'] += 1
    
    logger.info(f"Memory notification sending completed: {results}")
    return results


@shared_task
def cleanup_old_memories(days_to_keep: int = 365):
    """
    Clean up old memories and associated data.
    
    This maintenance task removes old memories that are no longer needed
    to keep the database size manageable.
    
    Args:
        days_to_keep: Number of days of memories to keep
        
    Returns:
        dict: Summary of cleanup results
    """
    logger.info(f"Starting memory cleanup (keeping {days_to_keep} days)")
    
    cutoff_date = timezone.now() - timedelta(days=days_to_keep)
    
    # Count what will be deleted
    old_memories = Memory.objects.filter(created_at__lt=cutoff_date)
    old_notifications = MemoryNotification.objects.filter(sent_at__lt=cutoff_date)
    
    results = {
        'memories_deleted': old_memories.count(),
        'notifications_deleted': old_notifications.count(),
        'cutoff_date': str(cutoff_date.date())
    }
    
    # Delete old records
    old_memories.delete()
    old_notifications.delete()
    
    logger.info(f"Memory cleanup completed: {results}")
    return results


def _generate_video_placeholder(reel: FlashbackReel, photos: List) -> bytes:
    """
    Placeholder video generation function.
    
    In production, this would integrate with a video generation service
    like FFmpeg, AWS Elemental, or a third-party API.
    
    Args:
        reel: FlashbackReel object
        photos: List of Image objects
        
    Returns:
        bytes: Generated video content
    """
    # This is a placeholder that creates a simple "video" file
    # In production, you would:
    # 1. Download photo files
    # 2. Resize/crop photos to video dimensions
    # 3. Create transitions and effects
    # 4. Add music/audio if desired
    # 5. Render final video file
    
    video_metadata = {
        'title': reel.title,
        'duration': reel.duration,
        'theme': reel.theme,
        'photo_count': len(photos),
        'created_at': timezone.now().isoformat(),
        'photos': [
            {
                'filename': photo.original_filename,
                'taken_at': photo.taken_at.isoformat() if photo.taken_at else None,
                'location': photo.location_text
            }
            for photo in photos
        ]
    }
    
    # Create a simple placeholder video file (JSON metadata for now)
    import json
    placeholder_content = json.dumps(video_metadata, indent=2).encode('utf-8')
    
    logger.info(f"Generated placeholder video for reel {reel.id} with {len(photos)} photos")
    
    return placeholder_content


def _create_reel_share_link(reel: FlashbackReel):
    """
    Create a public share link for a completed reel.
    
    Args:
        reel: FlashbackReel object to create share link for
    """
    try:
        from apps.sharing.models import PublicShare
        from apps.sharing.services import SharingService
        
        # Check if share link already exists
        if reel.share_link:
            logger.info(f"Share link already exists for reel {reel.id}")
            return
        
        # Create a temporary album for the reel photos
        from apps.albums.models import Album
        
        share_album = Album.objects.create(
            name=f"Flashback Reel: {reel.title}",
            user=reel.user,
            description=f"Auto-generated album for flashback reel created on {reel.created_at.date()}"
        )
        
        # Add reel photos to the album
        share_album.images.set(reel.photos.all())
        
        # Create public share
        sharing_service = SharingService()
        share_link = sharing_service.create_public_share(
            album=share_album,
            created_by=reel.user,
            expires_at=timezone.now() + timedelta(days=365),  # 1 year expiry
            allow_download=True,
            password_protected=False
        )
        
        # Associate share link with reel
        reel.share_link = share_link
        reel.save(update_fields=['share_link'])
        
        logger.info(f"Created share link for reel {reel.id}: {share_link.share_token}")
        
    except Exception as e:
        logger.error(f"Failed to create share link for reel {reel.id}: {str(e)}")


# Periodic task scheduling (would be configured in Celery beat)
@shared_task
def daily_memory_processing():
    """
    Daily task that runs memory discovery and notifications.
    
    This task should be scheduled to run once per day, typically in the morning.
    """
    logger.info("Starting daily memory processing")
    
    # Discover memories for all users
    batch_result = batch_discover_memories.delay()
    
    # Send notifications for significant memories
    notification_result = send_memory_notifications.delay()
    
    return {
        'batch_discovery_task': batch_result.id,
        'notification_task': notification_result.id,
        'scheduled_at': timezone.now().isoformat()
    }


@shared_task
def weekly_memory_cleanup():
    """
    Weekly maintenance task for memory cleanup.
    
    This task should be scheduled to run once per week.
    """
    logger.info("Starting weekly memory cleanup")
    
    # Clean up old memories (keep 1 year)
    cleanup_result = cleanup_old_memories.delay(days_to_keep=365)
    
    return {
        'cleanup_task': cleanup_result.id,
        'scheduled_at': timezone.now().isoformat()
    }