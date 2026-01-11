"""
URL configuration for image management.
"""
from django.urls import path
from . import views

urlpatterns = [
    # Image CRUD
    path('', views.ImageListView.as_view(), name='image_list'),
    path('<int:pk>/', views.ImageDetailView.as_view(), name='image_detail'),
    path('<int:pk>/file/', views.ImageFileView.as_view(), name='image_file'),
    
    # Image upload
    path('upload/', views.ImageUploadView.as_view(), name='image_upload'),
    path('bulk-upload/', views.BulkImageUploadView.as_view(), name='bulk_image_upload'),
    
    # Image search
    path('search/', views.ImageSearchView.as_view(), name='image_search'),
    
    # Image tags
    path('<int:pk>/tags/', views.add_image_tags, name='add_image_tags'),
    path('<int:pk>/tags/<int:tag_id>/', views.remove_image_tag, name='remove_image_tag'),
    
    # Bulk operations
    path('bulk-delete/', views.bulk_delete_images, name='bulk_delete_images'),
    
    # Statistics
    path('stats/', views.image_stats, name='image_stats'),
    
    # Folders
    path('folders/', views.FolderListCreateView.as_view(), name='folder_list_create'),
    path('folders/<int:pk>/', views.FolderDetailView.as_view(), name='folder_detail'),
]