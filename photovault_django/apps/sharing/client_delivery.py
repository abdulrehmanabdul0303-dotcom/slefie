"""
Client Delivery Mode - Professional photo delivery for photographers.
"""
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
import secrets
import hashlib
from PIL import Image, ImageDraw, ImageFont
import io
import base64

from .models import PublicShare, ShareAccess
from apps.albums.models import Album
from apps.images.models import Image


class ClientDeliveryService:
    """
    Service for creating and managing professional client delivery links.
    """
    
    @classmethod
    def create_client_link(cls, album, creator, config):
        """
        Create a professional client delivery link.
        
        Args:
            album: Album instance
            creator: User who creates the link
            config: Dict with delivery settings
                - expiry_hours: Hours until expiry (default: 168 = 7 days)
                - max_views: Maximum views allowed (0 = unlimited)
                - download_enabled: Allow downloads (default: True)
                - watermark_enabled: Add watermark (default: False)
                - watermark_text: Custom watermark text
                - passcode: Optional passcode protection
        
        Returns:
            Dict with share token and metadata
        """
        # Calculate expiry
        expiry_hours = config.get('expiry_hours', 168)  # 7 days default
        expires_at = timezone.now() + timedelta(hours=expiry_hours)
        
        # Create share instance
        share = PublicShare.objects.create(
            created_by=creator,
            album=album,
            scope='download' if config.get('download_enabled', True) else 'view',
            expires_at=expires_at,
            max_views=config.get('max_views', 0),
            watermark_enabled=config.get('watermark_enabled', False),
            watermark_text=config.get('watermark_text', f"© {creator.name or creator.email}"),
            watermark_opacity=config.get('watermark_opacity', 0.7),
        )
        
        # Generate secure token
        token = share.generate_token()
        
        # Create client-friendly URL
        client_url = f"{settings.FRONTEND_URL}/client/{token}"
        
        return {
            'token': token,
            'client_url': client_url,
            'share_id': share.id,
            'expires_at': expires_at,
            'max_views': share.max_views,
            'views_remaining': share.views_remaining,
            'time_remaining': share.time_remaining,
            'settings': {
                'download_enabled': share.scope == 'download',
                'watermark_enabled': share.watermark_enabled,
                'passcode_protected': bool(config.get('passcode')),
            }
        }
    
    @classmethod
    def get_client_link_meta(cls, token):
        """
        Get safe metadata for client link (no sensitive data).
        Used for link preview and initial page load.
        """
        try:
            share = PublicShare.objects.get(token_hash=hashlib.sha256(token.encode()).hexdigest())
            
            if not share.is_valid:
                return {
                    'valid': False,
                    'error': 'expired' if share.is_expired else 'limit_reached' if share.is_view_limit_reached else 'revoked'
                }
            
            return {
                'valid': True,
                'album_name': share.album.name,
                'creator_name': share.created_by.name or share.created_by.email.split('@')[0],
                'photo_count': share.album.images.count(),
                'expires_at': share.expires_at,
                'time_remaining': share.time_remaining,
                'views_remaining': share.views_remaining,
                'download_enabled': share.scope == 'download',
                'watermark_enabled': share.watermark_enabled,
                'branding': {
                    'title': f"Photos from {share.created_by.name or 'Your Photographer'}",
                    'subtitle': f"{share.album.images.count()} photos • Expires {share.time_remaining}",
                    'protected_by': "Protected by PhotoVault"
                }
            }
            
        except PublicShare.DoesNotExist:
            return {
                'valid': False,
                'error': 'not_found'
            }
    
    @classmethod
    def access_client_content(cls, token, request, passcode=None):
        """
        Access client content with proper validation and logging.
        Returns album content if access is granted.
        """
        try:
            share = PublicShare.objects.get(token_hash=hashlib.sha256(token.encode()).hexdigest())
            
            # Validate access
            if not share.is_valid:
                return {
                    'success': False,
                    'error': 'expired' if share.is_expired else 'limit_reached' if share.is_view_limit_reached else 'revoked'
                }
            
            # TODO: Validate passcode if required
            
            # Log access
            ip_address = cls._get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            # Increment view count
            if not share.increment_view_count(ip_address, user_agent):
                return {
                    'success': False,
                    'error': 'access_failed'
                }
            
            # Get album images
            images = share.album.images.all().order_by('created_at')
            
            # Prepare image data
            image_data = []
            for image in images:
                image_info = {
                    'id': image.id,
                    'filename': image.filename,
                    'thumbnail_url': cls._get_secure_image_url(image, 'thumbnail', share),
                    'preview_url': cls._get_secure_image_url(image, 'preview', share),
                    'download_url': cls._get_secure_image_url(image, 'original', share) if share.scope == 'download' else None,
                    'metadata': {
                        'size': image.file_size,
                        'dimensions': f"{image.width}x{image.height}" if image.width and image.height else None,
                        'date_taken': image.date_taken,
                    }
                }
                image_data.append(image_info)
            
            return {
                'success': True,
                'album': {
                    'name': share.album.name,
                    'description': share.album.description,
                    'image_count': len(image_data),
                    'images': image_data,
                },
                'share_info': {
                    'expires_at': share.expires_at,
                    'time_remaining': share.time_remaining,
                    'views_remaining': share.views_remaining,
                    'download_enabled': share.scope == 'download',
                    'watermark_enabled': share.watermark_enabled,
                },
                'access_log': {
                    'view_count': share.view_count,
                    'last_accessed': share.last_accessed,
                }
            }
            
        except PublicShare.DoesNotExist:
            return {
                'success': False,
                'error': 'not_found'
            }
    
    @classmethod
    def revoke_client_link(cls, share_id, user):
        """
        Revoke a client delivery link.
        """
        try:
            share = PublicShare.objects.get(id=share_id, created_by=user)
            share.revoke()
            return {'success': True}
        except PublicShare.DoesNotExist:
            return {'success': False, 'error': 'not_found'}
    
    @classmethod
    def get_creator_analytics(cls, user, days=30):
        """
        Get analytics for creator's shared links.
        """
        from django.db.models import Count, Sum
        from datetime import timedelta
        
        since = timezone.now() - timedelta(days=days)
        
        # Get shares
        shares = PublicShare.objects.filter(
            created_by=user,
            created_at__gte=since
        ).select_related('album')
        
        # Get access logs
        access_logs = ShareAccess.objects.filter(
            share__created_by=user,
            accessed_at__gte=since
        ).select_related('share__album')
        
        # Calculate metrics
        total_shares = shares.count()
        total_views = access_logs.count()
        unique_viewers = access_logs.values('ip_address').distinct().count()
        
        # Top albums
        top_albums = access_logs.values('share__album__name').annotate(
            views=Count('id')
        ).order_by('-views')[:5]
        
        # Recent activity
        recent_activity = access_logs.order_by('-accessed_at')[:10]
        
        # Views timeline (last 7 days)
        timeline_data = []
        for i in range(7):
            date = timezone.now().date() - timedelta(days=i)
            views = access_logs.filter(accessed_at__date=date).count()
            timeline_data.append({
                'date': date,
                'views': views
            })
        
        return {
            'summary': {
                'total_shares': total_shares,
                'total_views': total_views,
                'unique_viewers': unique_viewers,
                'avg_views_per_share': total_views / total_shares if total_shares > 0 else 0,
            },
            'top_albums': list(top_albums),
            'recent_activity': [
                {
                    'album_name': activity.share.album.name,
                    'accessed_at': activity.accessed_at,
                    'ip_address': activity.ip_address[:8] + '...',  # Partial IP for privacy
                }
                for activity in recent_activity
            ],
            'timeline': list(reversed(timeline_data)),  # Oldest to newest
        }
    
    @classmethod
    def apply_watermark(cls, image_data, watermark_text, opacity=0.7):
        """
        Apply watermark to image data.
        """
        try:
            # Open image
            image = Image.open(io.BytesIO(image_data))
            
            # Create watermark
            watermark = Image.new('RGBA', image.size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(watermark)
            
            # Calculate font size based on image size
            font_size = max(20, min(image.width, image.height) // 30)
            
            try:
                # Try to use a nice font
                font = ImageFont.truetype("arial.ttf", font_size)
            except:
                # Fallback to default font
                font = ImageFont.load_default()
            
            # Get text size
            bbox = draw.textbbox((0, 0), watermark_text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            # Position watermark (bottom right)
            margin = 20
            x = image.width - text_width - margin
            y = image.height - text_height - margin
            
            # Draw watermark with semi-transparent background
            bg_padding = 10
            draw.rectangle([
                x - bg_padding, y - bg_padding,
                x + text_width + bg_padding, y + text_height + bg_padding
            ], fill=(0, 0, 0, int(128 * opacity)))
            
            # Draw text
            draw.text((x, y), watermark_text, font=font, fill=(255, 255, 255, int(255 * opacity)))
            
            # Composite watermark onto image
            if image.mode != 'RGBA':
                image = image.convert('RGBA')
            
            watermarked = Image.alpha_composite(image, watermark)
            
            # Convert back to RGB if needed
            if watermarked.mode == 'RGBA':
                watermarked = watermarked.convert('RGB')
            
            # Save to bytes
            output = io.BytesIO()
            watermarked.save(output, format='JPEG', quality=90)
            return output.getvalue()
            
        except Exception as e:
            # If watermarking fails, return original image
            return image_data
    
    @classmethod
    def _get_secure_image_url(cls, image, size_type, share):
        """
        Generate secure, time-limited image URLs.
        """
        # Use the raw token for URL generation
        token = share.raw_token or share.token_hash[:16]  # Fallback to hash prefix
        
        if size_type == 'thumbnail':
            return f"/api/shares/client/{token}/images/{image.id}/thumbnail/"
        elif size_type == 'preview':
            return f"/api/shares/client/{token}/images/{image.id}/preview/"
        elif size_type == 'download':
            return f"/api/shares/client/{token}/images/{image.id}/download/"
        
        return None
    
    @classmethod
    def _get_client_ip(cls, request):
        """Get client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip