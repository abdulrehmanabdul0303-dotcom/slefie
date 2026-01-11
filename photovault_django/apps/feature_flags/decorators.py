"""
Decorators for feature flag integration.
"""
from functools import wraps
from django.http import JsonResponse
from rest_framework import status
from rest_framework.response import Response
from .services import FeatureFlagService


def feature_flag_required(flag_key, environment=None, return_json=True):
    """
    Decorator to require a feature flag to be enabled.
    
    Args:
        flag_key: Feature flag key to check
        environment: Environment to check (defaults to settings)
        return_json: Whether to return JSON response (True) or DRF Response (False)
    
    Usage:
        @feature_flag_required('zero_knowledge_vault')
        def my_view(request):
            # This view only runs if zero_knowledge_vault is enabled
            pass
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            user = getattr(request, 'user', None)
            
            if not FeatureFlagService.is_enabled(
                flag_key, 
                user=user, 
                environment=environment, 
                request=request
            ):
                error_response = {
                    'error': 'Feature not available',
                    'feature': flag_key,
                    'message': f'The {flag_key} feature is not enabled for your account.'
                }
                
                if return_json:
                    return JsonResponse(error_response, status=403)
                else:
                    return Response(error_response, status=status.HTTP_403_FORBIDDEN)
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def feature_flag_context(flag_keys, environment=None):
    """
    Decorator to add feature flag context to view.
    
    Args:
        flag_keys: List of feature flag keys to evaluate
        environment: Environment to check (defaults to settings)
    
    Usage:
        @feature_flag_context(['zero_knowledge_vault', 'semantic_search_ai'])
        def my_view(request):
            # request.feature_flags will contain flag evaluations
            pass
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            user = getattr(request, 'user', None)
            
            # Evaluate all flags
            feature_flags = {}
            for flag_key in flag_keys:
                enabled = FeatureFlagService.is_enabled(
                    flag_key,
                    user=user,
                    environment=environment,
                    request=request,
                    log_usage=False  # Don't log for context checks
                )
                
                variant = FeatureFlagService.get_variant(
                    flag_key,
                    user=user,
                    environment=environment,
                    request=request
                )
                
                feature_flags[flag_key] = {
                    'enabled': enabled,
                    'variant': variant
                }
            
            # Add to request
            request.feature_flags = feature_flags
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def experiment_variant(flag_key, variants, environment=None):
    """
    Decorator for A/B testing with different view implementations.
    
    Args:
        flag_key: Experiment feature flag key
        variants: Dict mapping variant names to view functions
        environment: Environment to check (defaults to settings)
    
    Usage:
        def variant_a(request):
            return Response({'version': 'A'})
        
        def variant_b(request):
            return Response({'version': 'B'})
        
        @experiment_variant('ai_photo_enhancement', {
            'control': variant_a,
            'enhanced': variant_b
        })
        def photo_enhancement_view(request):
            # Default implementation if no variant matches
            return Response({'version': 'default'})
    """
    def decorator(default_view):
        @wraps(default_view)
        def wrapper(request, *args, **kwargs):
            user = getattr(request, 'user', None)
            
            # Get variant for user
            variant = FeatureFlagService.get_variant(
                flag_key,
                user=user,
                environment=environment,
                request=request
            )
            
            # Use variant-specific view if available
            if variant and variant in variants:
                return variants[variant](request, *args, **kwargs)
            
            # Fall back to default view
            return default_view(request, *args, **kwargs)
        return wrapper
    return decorator


class FeatureFlagMixin:
    """
    Mixin for class-based views to add feature flag functionality.
    """
    
    required_feature_flags = []  # List of required flags
    feature_flag_context = []    # List of flags to add to context
    feature_flag_environment = None
    
    def dispatch(self, request, *args, **kwargs):
        """Check required feature flags before dispatching."""
        user = getattr(request, 'user', None)
        
        # Check required flags
        for flag_key in self.required_feature_flags:
            if not FeatureFlagService.is_enabled(
                flag_key,
                user=user,
                environment=self.feature_flag_environment,
                request=request
            ):
                return Response({
                    'error': 'Feature not available',
                    'feature': flag_key,
                    'message': f'The {flag_key} feature is not enabled for your account.'
                }, status=status.HTTP_403_FORBIDDEN)
        
        # Add context flags
        if self.feature_flag_context:
            feature_flags = {}
            for flag_key in self.feature_flag_context:
                enabled = FeatureFlagService.is_enabled(
                    flag_key,
                    user=user,
                    environment=self.feature_flag_environment,
                    request=request,
                    log_usage=False
                )
                
                variant = FeatureFlagService.get_variant(
                    flag_key,
                    user=user,
                    environment=self.feature_flag_environment,
                    request=request
                )
                
                feature_flags[flag_key] = {
                    'enabled': enabled,
                    'variant': variant
                }
            
            request.feature_flags = feature_flags
        
        return super().dispatch(request, *args, **kwargs)


# Convenience decorators for PhotoVault 2090 features

def zero_knowledge_required(view_func):
    """Require Zero-Knowledge Vault feature."""
    return feature_flag_required('zero_knowledge_vault')(view_func)

def anti_deepfake_required(view_func):
    """Require Anti-Deepfake Authenticity feature."""
    return feature_flag_required('anti_deepfake_authenticity')(view_func)

def semantic_search_required(view_func):
    """Require Semantic Search AI feature."""
    return feature_flag_required('semantic_search_ai')(view_func)

def digital_legacy_required(view_func):
    """Require Digital Legacy Vault feature."""
    return feature_flag_required('digital_legacy_vault')(view_func)

def consent_sharing_required(view_func):
    """Require Consent-Based Sharing feature."""
    return feature_flag_required('consent_based_sharing')(view_func)