"""
API Views for Feature Flag management.
"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from django.db.models import Q
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator

from .models import FeatureFlag, FeatureFlagUsage, FeatureFlagOverride, PHOTOVAULT_2090_FEATURES
from .serializers import (
    FeatureFlagSerializer, FeatureFlagCreateSerializer, FeatureFlagUsageSerializer,
    FeatureFlagOverrideSerializer, FeatureFlagOverrideCreateSerializer,
    FeatureFlagEvaluationSerializer, FeatureFlagEvaluationResponseSerializer,
    FeatureFlagAnalyticsSerializer, Bulk2090FlagsSerializer
)
from .services import FeatureFlagService


class FeatureFlagViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Feature Flags.
    """
    queryset = FeatureFlag.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'key'
    
    def get_serializer_class(self):
        if self.action == 'create':
            return FeatureFlagCreateSerializer
        return FeatureFlagSerializer
    
    def get_queryset(self):
        """Filter queryset based on user permissions."""
        queryset = super().get_queryset()
        
        # Non-admin users can only see flags they have access to
        if not self.request.user.is_staff:
            # Show flags that are either public or user has override
            user_override_flags = FeatureFlagOverride.objects.filter(
                user=self.request.user
            ).values_list('flag_id', flat=True)
            
            queryset = queryset.filter(
                Q(is_active=True) | Q(id__in=user_override_flags)
            )
        
        # Filter by tags
        tags = self.request.query_params.getlist('tags')
        if tags:
            for tag in tags:
                queryset = queryset.filter(tags__icontains=tag)
        
        # Filter by environment
        environment = self.request.query_params.get('environment')
        if environment:
            queryset = queryset.filter(environments__icontains=environment)
        
        return queryset.order_by('name')
    
    def perform_create(self, serializer):
        """Set created_by when creating flag."""
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def evaluate(self, request, key=None):
        """
        Evaluate a specific flag for the current user.
        """
        flag = self.get_object()
        
        environment = request.data.get('environment', 'PRODUCTION')
        metadata = request.data.get('metadata', {})
        
        enabled = FeatureFlagService.is_enabled(
            flag.key,
            user=request.user,
            environment=environment,
            request=request,
            metadata=metadata
        )
        
        variant = FeatureFlagService.get_variant(
            flag.key,
            user=request.user,
            environment=environment,
            request=request
        )
        
        return Response({
            'flag_key': flag.key,
            'enabled': enabled,
            'variant': variant,
            'environment': environment,
            'timestamp': timezone.now()
        })
    
    @action(detail=True, methods=['get'])
    def analytics(self, request, key=None):
        """
        Get analytics for a specific flag.
        """
        if not request.user.is_staff:
            return Response(
                {'error': 'Admin access required'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        flag = self.get_object()
        days = int(request.query_params.get('days', 7))
        
        analytics = FeatureFlagService.get_analytics(flag.key, days)
        
        serializer = FeatureFlagAnalyticsSerializer(analytics)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def bulk_evaluate(self, request):
        """
        Evaluate multiple flags for the current user.
        """
        serializer = FeatureFlagEvaluationSerializer(data=request.data)
        if serializer.is_valid():
            flags = serializer.validated_data['flags']
            environment = serializer.validated_data['environment']
            
            results = {}
            for flag_key in flags:
                enabled = FeatureFlagService.is_enabled(
                    flag_key,
                    user=request.user,
                    environment=environment,
                    request=request
                )
                
                variant = FeatureFlagService.get_variant(
                    flag_key,
                    user=request.user,
                    environment=environment,
                    request=request
                )
                
                results[flag_key] = {
                    'enabled': enabled,
                    'variant': variant
                }
            
            response_data = {
                'flags': results,
                'user_id': request.user.id,
                'environment': environment,
                'timestamp': timezone.now()
            }
            
            response_serializer = FeatureFlagEvaluationResponseSerializer(response_data)
            return Response(response_serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def enabled_for_user(self, request):
        """
        Get all enabled flags for the current user.
        """
        environment = request.query_params.get('environment', 'PRODUCTION')
        tags = request.query_params.getlist('tags')
        
        enabled_flags = FeatureFlagService.get_enabled_flags(
            user=request.user,
            environment=environment,
            tags=tags if tags else None
        )
        
        return Response({
            'flags': enabled_flags,
            'user_id': request.user.id,
            'environment': environment,
            'timestamp': timezone.now()
        })
    
    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def create_2090_flags(self, request):
        """
        Create all PhotoVault 2090 feature flags.
        """
        serializer = Bulk2090FlagsSerializer(data=request.data)
        if serializer.is_valid():
            environment = serializer.validated_data['environment']
            enable_flags = serializer.validated_data['enable_flags']
            tags_filter = serializer.validated_data.get('tags_filter')
            
            created_flags = []
            updated_flags = []
            
            for key, config in PHOTOVAULT_2090_FEATURES.items():
                # Filter by tags if specified
                if tags_filter and not any(tag in config['tags'] for tag in tags_filter):
                    continue
                
                flag, created = FeatureFlag.objects.get_or_create(
                    key=key,
                    defaults={
                        'name': config['name'],
                        'description': config['description'],
                        'flag_type': config['flag_type'],
                        'is_active': enable_flags,
                        'tags': config['tags'],
                        'environments': [environment],
                        'created_by': request.user,
                    }
                )
                
                if created:
                    created_flags.append(flag.key)
                else:
                    # Update existing flag
                    if environment not in flag.environments:
                        flag.environments.append(environment)
                    if enable_flags:
                        flag.is_active = True
                    flag.save()
                    updated_flags.append(flag.key)
            
            return Response({
                'message': f'PhotoVault 2090 flags processed',
                'created': created_flags,
                'updated': updated_flags,
                'total_created': len(created_flags),
                'total_updated': len(updated_flags)
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class FeatureFlagUsageViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Feature Flag Usage analytics (read-only).
    """
    queryset = FeatureFlagUsage.objects.all()
    serializer_class = FeatureFlagUsageSerializer
    permission_classes = [permissions.IsAdminUser]
    
    def get_queryset(self):
        """Filter usage logs."""
        queryset = super().get_queryset()
        
        # Filter by flag
        flag_key = self.request.query_params.get('flag')
        if flag_key:
            queryset = queryset.filter(flag__key=flag_key)
        
        # Filter by user
        user_email = self.request.query_params.get('user')
        if user_email:
            queryset = queryset.filter(user__email=user_email)
        
        # Filter by environment
        environment = self.request.query_params.get('environment')
        if environment:
            queryset = queryset.filter(environment=environment)
        
        # Filter by enabled status
        enabled = self.request.query_params.get('enabled')
        if enabled is not None:
            queryset = queryset.filter(enabled=enabled.lower() == 'true')
        
        return queryset.order_by('-timestamp')


class FeatureFlagOverrideViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Feature Flag Overrides.
    """
    queryset = FeatureFlagOverride.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return FeatureFlagOverrideCreateSerializer
        return FeatureFlagOverrideSerializer
    
    def get_queryset(self):
        """Filter overrides based on user permissions."""
        queryset = super().get_queryset()
        
        # Non-admin users can only see their own overrides
        if not self.request.user.is_staff:
            queryset = queryset.filter(user=self.request.user)
        
        # Filter by flag
        flag_key = self.request.query_params.get('flag')
        if flag_key:
            queryset = queryset.filter(flag__key=flag_key)
        
        # Filter by user (admin only)
        if self.request.user.is_staff:
            user_email = self.request.query_params.get('user')
            if user_email:
                queryset = queryset.filter(user__email=user_email)
        
        return queryset.order_by('-created_at')
    
    def perform_create(self, serializer):
        """Set created_by when creating override."""
        # Non-admin users can only create overrides for themselves
        if not self.request.user.is_staff:
            serializer.save(
                user=self.request.user,
                created_by=self.request.user
            )
        else:
            serializer.save(created_by=self.request.user)


@method_decorator(ratelimit(key='user', rate='100/h', method='POST'), name='post')
class FeatureFlagEvaluationView(APIView):
    """
    High-performance feature flag evaluation endpoint.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """
        Evaluate feature flags for the current user.
        Optimized for high-frequency calls.
        """
        serializer = FeatureFlagEvaluationSerializer(data=request.data)
        if serializer.is_valid():
            flags = serializer.validated_data['flags']
            environment = serializer.validated_data['environment']
            
            # Batch evaluation for performance
            results = {}
            for flag_key in flags:
                enabled = FeatureFlagService.is_enabled(
                    flag_key,
                    user=request.user,
                    environment=environment,
                    request=request,
                    log_usage=False  # Disable logging for high-frequency calls
                )
                
                results[flag_key] = enabled
            
            return Response({
                'flags': results,
                'timestamp': timezone.now().isoformat()
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class FeatureFlagAnalyticsView(APIView):
    """
    Feature flag analytics endpoint.
    """
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request):
        """
        Get comprehensive feature flag analytics.
        """
        flag_key = request.query_params.get('flag')
        days = int(request.query_params.get('days', 7))
        
        analytics = FeatureFlagService.get_analytics(flag_key, days)
        
        serializer = FeatureFlagAnalyticsSerializer(analytics)
        return Response(serializer.data)


class PhotoVault2090FeaturesView(APIView):
    """
    Get information about PhotoVault 2090 features.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """
        Get all PhotoVault 2090 features with their status.
        """
        environment = request.query_params.get('environment', 'PRODUCTION')
        
        features = {}
        for key, config in PHOTOVAULT_2090_FEATURES.items():
            enabled = FeatureFlagService.is_enabled(
                key,
                user=request.user,
                environment=environment,
                request=request,
                log_usage=False
            )
            
            variant = FeatureFlagService.get_variant(
                key,
                user=request.user,
                environment=environment,
                request=request
            )
            
            features[key] = {
                'name': config['name'],
                'description': config['description'],
                'tags': config['tags'],
                'enabled': enabled,
                'variant': variant,
            }
        
        return Response({
            'features': features,
            'user_id': request.user.id,
            'environment': environment,
            'timestamp': timezone.now()
        })