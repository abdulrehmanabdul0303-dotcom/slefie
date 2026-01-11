"""
URL configuration for album management.
"""
from django.urls import path
from . import views

urlpatterns = [
    # Album CRUD
    path('', views.AlbumListCreateView.as_view(), name='album_list_create'),
    path('<int:pk>/', views.AlbumDetailView.as_view(), name='album_detail'),
    
    # Album images
    path('<int:pk>/images/', views.AlbumImagesView.as_view(), name='album_images'),
    path('<int:pk>/add-images/', views.add_images_to_album, name='add_images_to_album'),
    path('<int:pk>/remove-images/', views.remove_images_from_album, name='remove_images_from_album'),
    
    # Auto-generated albums
    path('by-date/', views.AlbumsByDateView.as_view(), name='albums_by_date'),
    path('by-location/', views.AlbumsByLocationView.as_view(), name='albums_by_location'),
    path('by-person/', views.AlbumsByPersonView.as_view(), name='albums_by_person'),
    
    # Album management
    path('<int:pk>/set-cover/', views.set_album_cover, name='set_album_cover'),
    path('<int:pk>/reorder/', views.reorder_album_images, name='reorder_album_images'),
]