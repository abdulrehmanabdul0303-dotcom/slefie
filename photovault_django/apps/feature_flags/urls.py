"""
URLs for Feature Flag API.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    FeatureFlagViewSet, FeatureFlagUsageViewSet, FeatureFlagOverrideViewSet,
    FeatureFlagEvaluationView, FeatureFlagAnalyticsView, PhotoVault2090FeaturesView
)

# Create router for viewsets
router = DefaultRouter()
router.register(r'flags', FeatureFlagViewSet, basename='featureflag')
router.register(r'usage', FeatureFlagUsageViewSet, basename='featureflagusage')
router.register(r'overrides', FeatureFlagOverrideViewSet, basename='featureflagoverride')

app_name = 'feature_flags'

urlpatterns = [
    # ViewSet routes
    path('', include(router.urls)),
    
    # High-performance evaluation endpoint
    path('evaluate/', FeatureFlagEvaluationView.as_view(), name='evaluate'),
    
    # Analytics endpoint
    path('analytics/', FeatureFlagAnalyticsView.as_view(), name='analytics'),
    
    # PhotoVault 2090 features
    path('2090/', PhotoVault2090FeaturesView.as_view(), name='2090-features'),
]