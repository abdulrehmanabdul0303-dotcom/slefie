"""
Views for sharing system.
"""
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator
from datetime import timedelta
import secrets

from .models import PublicShare, ShareAccess, FaceClaimSession, FaceClaimAudit
from .serializers import (
    ShareCreateSerializer,
    PublicShareSerializer,
    ShareAccessSerializer,
    SharedAlbumViewSerializer,
    FaceClaimUploadSerializer,
    FaceClaimVerifySerializer,
)
from .services import FaceVerificationService
from apps.albums.models import Album


class CreateShareLinkView(APIView):
    """
    Create a public share link for an album.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @method_decorator(ratelimit(key='user', rate='10/h', method='POST'))
    def post(self, request):
        serializer = ShareCreateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            album = serializer.validated_data['album_id']
            expires_in_hours = serializer.validated_data['expires_in_hours']
            
            # Check if share already exists for this album
            existing_share = PublicShare.objects.filter(
                album=album,
                created_by=request.user,
                revoked=False
            ).first()
            
            if existing_share and existing_share.is_valid:
                # Return existing valid share
                return Response(
                    PublicShareSerializer(existing_share, context={'frontend_url': request.build_absolute_uri('/')}).data,
                    status=status.HTTP_200_OK
                )
            
            # Create new share
            share = PublicShare.objects.create(
                created_by=request.user,
                album=album,
                scope=serializer.validated_data['scope'],
                share_type=serializer.validated_data['share_type'],
                expires_at=timezone.now() + timedelta(hours=expires_in_hours),
                max_views=serializer.validated_data.get('max_views'),
                require_face=serializer.validated_data['require_face'],
            )
            
            # Generate token
            token = share.generate_token()
            share.save()
            
            return Response(
                PublicShareSerializer(share, context={'frontend_url': request.build_absolute_uri('/')}).data,
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ListShareLinksView(APIView):
    """
    List user's share links.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        shares = PublicShare.objects.filter(
            created_by=request.user
        ).order_by('-created_at')
        
        serializer = PublicShareSerializer(shares, many=True, context={'frontend_url': request.build_absolute_uri('/')})
        return Response(serializer.data)


class ShareQRCodeView(APIView):
    """
    Generate QR code for share link.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, pk):
        share = get_object_or_404(PublicShare, pk=pk, created_by=request.user)
        
        if not share.is_valid:
            return Response({
                'error': 'Share link is expired or revoked'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Generate QR code
        from .services import ShareLinkService
        from django.http import HttpResponse
        
        share_url = share.get_share_url(request.build_absolute_uri('/'))
        qr_code_data = ShareLinkService.generate_qr_code(share_url)
        
        if qr_code_data:
            response = HttpResponse(qr_code_data, content_type='image/png')
            response['Content-Disposition'] = f'inline; filename="share_qr_{share.id}.png"'
            return response
        else:
            return Response({
                'error': 'Failed to generate QR code'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RevokeShareLinkView(APIView):
    """
    Revoke a share link.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def delete(self, request, pk):
        share = get_object_or_404(PublicShare, pk=pk, created_by=request.user)
        share.revoke()
        
        return Response({'message': 'Share link revoked successfully'}, status=status.HTTP_200_OK)


class ViewSharedAlbumView(APIView):
    """
    View a shared album (public endpoint).
    """
    permission_classes = [permissions.AllowAny]
    
    @method_decorator(ratelimit(key='ip', rate='100/h', method='GET'))
    def get(self, request, token):
        try:
            # Find share by token
            shares = PublicShare.objects.filter(revoked=False)
            share = None
            
            for s in shares:
                if s.verify_token(token):
                    share = s
                    break
            
            if not share:
                return Response({'error': 'Invalid or expired share link'}, status=status.HTTP_404_NOT_FOUND)
            
            if not share.is_valid:
                return Response({'error': 'Share link has expired or reached view limit'}, status=status.HTTP_410_GONE)
            
            # Check if face verification is required
            if share.require_face and share.share_type == 'FACE_CLAIM':
                if not share.face_claim_verified:
                    return Response({
                        'error': 'Face verification required',
                        'requires_face_verification': True,
                        'share_id': share.id
                    }, status=status.HTTP_403_FORBIDDEN)
            
            # Log access
            ShareAccess.objects.create(
                share=share,
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:512]
            )
            
            # Increment view count
            share.increment_view_count()
            
            # Return album data
            serializer = SharedAlbumViewSerializer(share)
            return Response(serializer.data)
            
        except Exception as e:
            return Response({'error': 'Failed to load shared album'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def get_client_ip(self, request):
        """Get client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class FaceClaimUploadView(APIView):
    """
    Upload face image for claim verification.
    """
    permission_classes = [permissions.AllowAny]
    
    @method_decorator(ratelimit(key='ip', rate='10/h', method='POST'))
    def post(self, request):
        share_id = request.data.get('share_id')
        if not share_id:
            return Response({'error': 'share_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            share = PublicShare.objects.get(id=share_id, share_type='FACE_CLAIM', revoked=False)
        except PublicShare.DoesNotExist:
            return Response({'error': 'Invalid share'}, status=status.HTTP_404_NOT_FOUND)
        
        if share.is_face_claim_locked:
            return Response({'error': 'Face verification temporarily locked'}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        
        serializer = FaceClaimUploadSerializer(data=request.data)
        if serializer.is_valid():
            image = serializer.validated_data['image']
            
            try:
                # Extract face embedding (placeholder implementation)
                face_embedding = FaceVerificationService.extract_face_embedding(image)
                
                if not face_embedding:
                    # Log failed attempt
                    FaceClaimAudit.objects.create(
                        share=share,
                        attempt_type='FACE_UPLOAD',
                        success=False,
                        ip_address=self.get_client_ip(request),
                        user_agent=request.META.get('HTTP_USER_AGENT', '')[:512]
                    )
                    
                    return Response({'error': 'No face detected in image'}, status=status.HTTP_400_BAD_REQUEST)
                
                # Create face claim session
                session_token = secrets.token_urlsafe(32)
                session = FaceClaimSession.objects.create(
                    share=share,
                    session_token=session_token,
                    face_embedding_json=face_embedding,
                    ip_address=self.get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')[:512],
                    expires_at=timezone.now() + timedelta(minutes=10)
                )
                
                return Response({
                    'session_token': session_token,
                    'message': 'Face detected. Proceed with verification.'
                })
                
            except Exception as e:
                return Response({'error': 'Face processing failed'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def get_client_ip(self, request):
        """Get client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class FaceClaimVerifyView(APIView):
    """
    Verify face claim and grant access.
    """
    permission_classes = [permissions.AllowAny]
    
    @method_decorator(ratelimit(key='ip', rate='5/m', method='POST'))
    def post(self, request):
        serializer = FaceClaimVerifySerializer(data=request.data)
        if serializer.is_valid():
            session = serializer.validated_data['session_token']
            share = session.share
            
            try:
                # Verify face against album faces (placeholder implementation)
                verification_result = FaceVerificationService.verify_face_against_album(
                    session.face_embedding_json,
                    share.album
                )
                
                if verification_result['match']:
                    # Grant access
                    share.face_claim_verified = True
                    share.face_claim_embedding_json = session.face_embedding_json
                    share.save()
                    
                    # Log successful attempt
                    FaceClaimAudit.objects.create(
                        share=share,
                        attempt_type='VERIFY',
                        success=True,
                        confidence_score=verification_result['confidence'],
                        matched_face_id=verification_result.get('face_id'),
                        ip_address=self.get_client_ip(request),
                        user_agent=request.META.get('HTTP_USER_AGENT', '')[:512]
                    )
                    
                    # Delete session
                    session.delete()
                    
                    return Response({
                        'verified': True,
                        'message': 'Face verification successful. Access granted.',
                        'confidence': verification_result['confidence']
                    })
                else:
                    # Increment failed attempts
                    share.face_claim_attempts += 1
                    share.face_claim_last_attempt = timezone.now()
                    
                    # Lock if too many attempts
                    if share.face_claim_attempts >= 5:
                        share.face_claim_lock_until = timezone.now() + timedelta(hours=1)
                    
                    share.save()
                    
                    # Log failed attempt
                    FaceClaimAudit.objects.create(
                        share=share,
                        attempt_type='VERIFY',
                        success=False,
                        confidence_score=verification_result.get('confidence', 0.0),
                        ip_address=self.get_client_ip(request),
                        user_agent=request.META.get('HTTP_USER_AGENT', '')[:512]
                    )
                    
                    return Response({
                        'verified': False,
                        'message': 'Face verification failed. Access denied.',
                        'attempts_remaining': max(0, 5 - share.face_claim_attempts)
                    }, status=status.HTTP_403_FORBIDDEN)
                    
            except Exception as e:
                return Response({'error': 'Verification failed'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def get_client_ip(self, request):
        """Get client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def share_analytics(request, pk):
    """
    Get analytics for a share link.
    """
    share = get_object_or_404(PublicShare, pk=pk, created_by=request.user)
    
    access_logs = ShareAccess.objects.filter(share=share).order_by('-accessed_at')[:50]
    
    analytics = {
        'share_info': PublicShareSerializer(share).data,
        'total_views': share.view_count,
        'recent_access': ShareAccessSerializer(access_logs, many=True).data,
        'face_claim_attempts': share.face_claim_attempts if share.share_type == 'FACE_CLAIM' else 0,
    }
    
    return Response(analytics)