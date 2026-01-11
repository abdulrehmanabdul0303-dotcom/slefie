"""
Client Delivery API Views - Professional photo delivery endpoints.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from .client_delivery import ClientDeliveryService
from .models import PublicShare
from apps.albums.models import Album
from apps.images.models import Image
import hashlib


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@ratelimit(key='user', rate='10/h', method='POST')
def create_client_link(request):
    """
    Create a professional client delivery link.
    
    POST /api/shares/client/create/
    {
        "album_id": 123,
        "expiry_hours": 168,
        "max_views": 0,
        "download_enabled": true,
        "watermark_enabled": false,
        "watermark_text": "© John Doe Photography",
        "passcode": "optional"
    }
    """
    try:
        album_id = request.data.get('album_id')
        if not album_id:
            return Response({
                'error': {
                    'code': 'MISSING_ALBUM',
                    'message': 'Album ID is required'
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get album (ensure user owns it)
        try:
            album = Album.objects.get(id=album_id, user=request.user)
        except Album.DoesNotExist:
            return Response({
                'error': {
                    'code': 'ALBUM_NOT_FOUND',
                    'message': 'Album not found or access denied'
                }
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Validate album has images
        if album.images.count() == 0:
            return Response({
                'error': {
                    'code': 'EMPTY_ALBUM',
                    'message': 'Cannot share empty album'
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create client link
        config = {
            'expiry_hours': request.data.get('expiry_hours', 168),  # 7 days default
            'max_views': request.data.get('max_views', 0),  # Unlimited default
            'download_enabled': request.data.get('download_enabled', True),
            'watermark_enabled': request.data.get('watermark_enabled', False),
            'watermark_text': request.data.get('watermark_text', ''),
            'passcode': request.data.get('passcode', ''),
        }
        
        result = ClientDeliveryService.create_client_link(album, request.user, config)
        
        return Response({
            'success': True,
            'client_link': result,
            'message': 'Client delivery link created successfully'
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({
            'error': {
                'code': 'CREATION_FAILED',
                'message': 'Failed to create client link',
                'details': str(e)
            }
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
@ratelimit(key='ip', rate='100/h', method='GET')
def get_client_link_meta(request, token):
    """
    Get safe metadata for client link preview.
    
    GET /api/shares/client/{token}/meta/
    """
    try:
        meta = ClientDeliveryService.get_client_link_meta(token)
        
        if not meta['valid']:
            error_messages = {
                'expired': 'This link has expired',
                'limit_reached': 'View limit has been reached',
                'revoked': 'This link has been revoked',
                'not_found': 'Link not found'
            }
            
            return Response({
                'error': {
                    'code': meta['error'].upper(),
                    'message': error_messages.get(meta['error'], 'Link is not valid')
                }
            }, status=status.HTTP_404_NOT_FOUND if meta['error'] == 'not_found' else status.HTTP_403_FORBIDDEN)
        
        return Response({
            'success': True,
            'meta': meta
        })
        
    except Exception as e:
        return Response({
            'error': {
                'code': 'META_FETCH_FAILED',
                'message': 'Failed to fetch link metadata',
                'details': str(e)
            }
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
@ratelimit(key='ip', rate='50/h', method='POST')
def access_client_content(request, token):
    """
    Access client content with validation.
    
    POST /api/shares/client/{token}/access/
    {
        "passcode": "optional"
    }
    """
    try:
        passcode = request.data.get('passcode', '')
        
        result = ClientDeliveryService.access_client_content(token, request, passcode)
        
        if not result['success']:
            error_messages = {
                'expired': 'This link has expired',
                'limit_reached': 'View limit has been reached',
                'revoked': 'This link has been revoked',
                'not_found': 'Link not found',
                'access_failed': 'Access denied'
            }
            
            return Response({
                'error': {
                    'code': result['error'].upper(),
                    'message': error_messages.get(result['error'], 'Access denied')
                }
            }, status=status.HTTP_403_FORBIDDEN)
        
        return Response({
            'success': True,
            'content': result
        })
        
    except Exception as e:
        return Response({
            'error': {
                'code': 'ACCESS_FAILED',
                'message': 'Failed to access content',
                'details': str(e)
            }
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def revoke_client_link(request, share_id):
    """
    Revoke a client delivery link.
    
    DELETE /api/shares/client/{share_id}/revoke/
    """
    try:
        result = ClientDeliveryService.revoke_client_link(share_id, request.user)
        
        if not result['success']:
            return Response({
                'error': {
                    'code': 'NOT_FOUND',
                    'message': 'Share link not found or access denied'
                }
            }, status=status.HTTP_404_NOT_FOUND)
        
        return Response({
            'success': True,
            'message': 'Client link revoked successfully'
        })
        
    except Exception as e:
        return Response({
            'error': {
                'code': 'REVOKE_FAILED',
                'message': 'Failed to revoke link',
                'details': str(e)
            }
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_creator_analytics(request):
    """
    Get analytics for creator's shared links.
    
    GET /api/shares/analytics/?days=30
    """
    try:
        days = int(request.GET.get('days', 30))
        days = min(days, 365)  # Max 1 year
        
        analytics = ClientDeliveryService.get_creator_analytics(request.user, days)
        
        return Response({
            'success': True,
            'analytics': analytics,
            'period_days': days
        })
        
    except Exception as e:
        return Response({
            'error': {
                'code': 'ANALYTICS_FAILED',
                'message': 'Failed to fetch analytics',
                'details': str(e)
            }
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_client_links(request):
    """
    List all client links created by user.
    
    GET /api/shares/client/list/
    """
    try:
        shares = PublicShare.objects.filter(
            created_by=request.user
        ).select_related('album').order_by('-created_at')
        
        links_data = []
        for share in shares:
            links_data.append({
                'id': share.id,
                'album_name': share.album.name,
                'album_id': share.album.id,
                'created_at': share.created_at,
                'expires_at': share.expires_at,
                'is_expired': share.is_expired,
                'is_valid': share.is_valid,
                'view_count': share.view_count,
                'max_views': share.max_views,
                'views_remaining': share.views_remaining,
                'time_remaining': share.time_remaining,
                'download_enabled': share.scope == 'download',
                'watermark_enabled': share.watermark_enabled,
                'last_accessed': share.last_accessed,
                'client_url': f"{request.build_absolute_uri('/').rstrip('/')}/client/{share.raw_token}" if share.raw_token else None,
            })
        
        return Response({
            'success': True,
            'links': links_data,
            'total_count': len(links_data)
        })
        
    except Exception as e:
        return Response({
            'error': {
                'code': 'LIST_FAILED',
                'message': 'Failed to fetch client links',
                'details': str(e)
            }
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Image serving endpoints for client links

@api_view(['GET'])
@permission_classes([AllowAny])
@ratelimit(key='ip', rate='200/h', method='GET')
def serve_client_image(request, token, image_id, size_type):
    """
    Serve images through client share token.
    
    GET /api/shares/client/{token}/images/{image_id}/{size_type}/
    size_type: thumbnail, preview, download
    """
    try:
        # Validate share token
        share = get_object_or_404(
            PublicShare, 
            token_hash=hashlib.sha256(token.encode()).hexdigest()
        )
        
        if not share.is_valid:
            raise Http404("Share link is not valid")
        
        # Get image
        image = get_object_or_404(Image, id=image_id, albums=share.album)
        
        # Check download permission
        if size_type == 'download' and share.scope != 'download':
            return Response({
                'error': {
                    'code': 'DOWNLOAD_DISABLED',
                    'message': 'Downloads are not allowed for this link'
                }
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Log access (for analytics)
        ip_address = ClientDeliveryService._get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Get image data based on size type
        if size_type == 'thumbnail':
            image_data = image.get_thumbnail_data()
            content_type = 'image/jpeg'
        elif size_type == 'preview':
            image_data = image.get_preview_data()
            content_type = 'image/jpeg'
        elif size_type == 'download':
            image_data = image.get_original_data()
            content_type = image.content_type or 'image/jpeg'
        else:
            raise Http404("Invalid size type")
        
        # Apply watermark if enabled
        if share.watermark_enabled and size_type in ['preview', 'download']:
            watermark_text = share.watermark_text or f"© {share.created_by.name or share.created_by.email}"
            image_data = ClientDeliveryService.apply_watermark(
                image_data, 
                watermark_text, 
                share.watermark_opacity
            )
        
        # Create response
        response = HttpResponse(image_data, content_type=content_type)
        
        # Set headers
        if size_type == 'download':
            response['Content-Disposition'] = f'attachment; filename="{image.filename}"'
        else:
            response['Content-Disposition'] = 'inline'
        
        # Cache headers
        response['Cache-Control'] = 'private, max-age=3600'  # 1 hour cache
        
        return response
        
    except Exception as e:
        raise Http404("Image not found or access denied")