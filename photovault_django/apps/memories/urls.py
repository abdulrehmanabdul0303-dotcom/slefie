from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'', views.MemoryViewSet, basename='memory')
router.register(r'reels', views.FlashbackReelViewSet, basename='flashback-reel')

app_name = 'memories'

urlpatterns = [
    path('daily/', views.DailyMemoriesView.as_view(), name='daily-memories'),
    path('<int:memory_id>/detail/', views.MemoryDetailView.as_view(), name='memory-detail'),
    path('<int:memory_id>/engage/', views.MemoryEngagementView.as_view(), name='memory-engagement'),
    path('analytics/', views.MemoryAnalyticsView.as_view(), name='memory-analytics'),
    path('preferences/', views.MemoryPreferencesView.as_view(), name='memory-preferences'),
    path('', include(router.urls)),
]