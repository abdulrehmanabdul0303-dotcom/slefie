"""
URL configuration for sharing system with client delivery.
"""
from django.urls import path
from . import views
from .client_views import (
    create_client_link,
    get_client_link_meta,
    access_client_content,
    revoke_client_link,
    get_creator_analytics,
    list_client_links,
    serve_client_image,
)

urlpatterns = [
    # Legacy share link management
    path('create/', views.CreateShareLinkView.as_view(), name='create_share_link'),
    path('list/', views.ListShareLinksView.as_view(), name='list_share_links'),
    path('<int:pk>/revoke/', views.RevokeShareLinkView.as_view(), name='revoke_share_link'),
    path('<int:pk>/analytics/', views.share_analytics, name='share_analytics'),
    path('<int:pk>/qr/', views.ShareQRCodeView.as_view(), name='share_qr_code'),
    
    # Public access (no auth required)
    path('view/<str:token>/', views.ViewSharedAlbumView.as_view(), name='view_shared_album'),
    
    # Face claim verification
    path('face-claim/upload/', views.FaceClaimUploadView.as_view(), name='face_claim_upload'),
    path('face-claim/verify/', views.FaceClaimVerifyView.as_view(), name='face_claim_verify'),
    
    # Client Delivery API - Money Feature #1
    path('client/create/', create_client_link, name='create-client-link'),
    path('client/list/', list_client_links, name='list-client-links'),
    path('client/<str:token>/meta/', get_client_link_meta, name='client-link-meta'),
    path('client/<str:token>/access/', access_client_content, name='client-link-access'),
    path('client/<int:share_id>/revoke/', revoke_client_link, name='revoke-client-link'),
    
    # Analytics - Engagement Engine
    path('analytics/', get_creator_analytics, name='creator-analytics'),
    
    # Image serving through client links
    path('client/<str:token>/images/<int:image_id>/<str:size_type>/', 
         serve_client_image, name='serve-client-image'),
]