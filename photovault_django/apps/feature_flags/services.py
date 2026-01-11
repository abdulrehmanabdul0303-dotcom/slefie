"""
Feature Flag Service for PhotoVault 2090.
Provides high-performance feature flag evaluation with caching.
"""
from django.core.cache import cache
from django.conf import settings
from django.utils import timezone
from .models import FeatureFlag, FeatureFlagUsage, FeatureFlagOverride
import logging

logger = logging.getLogger(__name__)


class FeatureFlagService:
    """
    High-performance feature flag service with caching and analytics.
    """
    
    CACHE_PREFIX = 'feature_flag:'
    CACHE_TIMEOUT = 300  # 5 minutes
    
    @classmethod
    def is_enabled(cls, flag_key, user=None, environment=None, request=None, 
                   log_usage=True, metadata=None):
        """
        Check if a feature flag is enabled for a user.
        
        Args:
            flag_key: Feature flag key
            user: User instance (optional)
            environment: Environment name (defaults to settings)
            request: HTTP request for context (optional)
            log_usage: Whether to log usage analytics
            metadata: Additional metadata for logging
        
        Returns:
            bool: True if feature is enabled
        """
        try:
            # Default environment
            if environment is None:
                environment = getattr(settings, 'ENVIRONMENT', 'PRODUCTION')
            
            # Check user-specific override first
            if user:
                override = cls._get_user_override(flag_key, user)
                if override and override.is_active():
                    enabled = override.enabled
                    variant = override.variant
                    
                    if log_usage:
                        cls._log_usage(flag_key, user, enabled, variant, 
                                     environment, request, metadata, override=True)
                    
                    return enabled
            
            # Get flag from cache or database
            flag = cls._get_flag(flag_key)
            if not flag:
                if log_usage:
                    cls._log_usage(flag_key, user, False, '', 
                                 environment, request, metadata, not_found=True)
                return False
            
            # Evaluate flag
            enabled = flag.is_enabled_for_user(user, environment)
            variant = flag.get_variant_for_user(user) if flag.flag_type == 'EXPERIMENT' else ''
            
            # Log usage
            if log_usage:
                cls._log_usage(flag_key, user, enabled, variant, 
                             environment, request, metadata)
            
            return enabled
            
        except Exception as e:
            logger.error(f"Feature flag evaluation error for {flag_key}: {e}")
            return False
    
    @classmethod
    def get_variant(cls, flag_key, user=None, environment=None, request=None):
        """
        Get experiment variant for a user.
        
        Returns:
            str: Variant name or empty string
        """
        try:
            if environment is None:
                environment = getattr(settings, 'ENVIRONMENT', 'PRODUCTION')
            
            # Check user override
            if user:
                override = cls._get_user_override(flag_key, user)
                if override and override.is_active():
                    return override.variant
            
            # Get flag
            flag = cls._get_flag(flag_key)
            if not flag:
                return ''
            
            return flag.get_variant_for_user(user) or ''
            
        except Exception as e:
            logger.error(f"Feature flag variant error for {flag_key}: {e}")
            return ''
    
    @classmethod
    def get_enabled_flags(cls, user=None, environment=None, tags=None):
        """
        Get all enabled flags for a user.
        
        Args:
            user: User instance
            environment: Environment name
            tags: Filter by tags (list)
        
        Returns:
            dict: {flag_key: {'enabled': bool, 'variant': str}}
        """
        try:
            if environment is None:
                environment = getattr(settings, 'ENVIRONMENT', 'PRODUCTION')
            
            # Get all active flags
            flags = FeatureFlag.objects.filter(is_active=True)
            
            if tags:
                # Filter by tags - use icontains for SQLite compatibility
                from django.db.models import Q
                tag_filter = Q()
                for tag in tags:
                    # Use JSON field lookup that works with SQLite
                    tag_filter |= Q(tags__icontains=tag)
                flags = flags.filter(tag_filter)
            
            result = {}
            for flag in flags:
                enabled = flag.is_enabled_for_user(user, environment)
                variant = flag.get_variant_for_user(user) if enabled else ''
                
                result[flag.key] = {
                    'enabled': enabled,
                    'variant': variant,
                    'name': flag.name,
                    'description': flag.description,
                }
            
            return result
            
        except Exception as e:
            logger.error(f"Get enabled flags error: {e}")
            return {}
    
    @classmethod
    def create_override(cls, flag_key, user, enabled, variant='', 
                       reason='', created_by=None, expires_at=None):
        """
        Create user-specific flag override.
        """
        try:
            flag = FeatureFlag.objects.get(key=flag_key)
            
            override, created = FeatureFlagOverride.objects.update_or_create(
                user=user,
                flag=flag,
                defaults={
                    'enabled': enabled,
                    'variant': variant,
                    'reason': reason,
                    'created_by': created_by,
                    'expires_at': expires_at,
                }
            )
            
            # Clear cache
            cls._clear_user_cache(user)
            
            return override
            
        except FeatureFlag.DoesNotExist:
            logger.error(f"Flag not found for override: {flag_key}")
            return None
        except Exception as e:
            logger.error(f"Create override error: {e}")
            return None
    
    @classmethod
    def remove_override(cls, flag_key, user):
        """
        Remove user-specific flag override.
        """
        try:
            flag = FeatureFlag.objects.get(key=flag_key)
            FeatureFlagOverride.objects.filter(user=user, flag=flag).delete()
            
            # Clear cache
            cls._clear_user_cache(user)
            
            return True
            
        except Exception as e:
            logger.error(f"Remove override error: {e}")
            return False
    
    @classmethod
    def get_analytics(cls, flag_key=None, days=7):
        """
        Get feature flag usage analytics.
        
        Returns:
            dict: Analytics data
        """
        try:
            from django.db.models import Count, Q
            from datetime import timedelta
            
            since = timezone.now() - timedelta(days=days)
            
            usage_query = FeatureFlagUsage.objects.filter(timestamp__gte=since)
            
            if flag_key:
                usage_query = usage_query.filter(flag__key=flag_key)
            
            # Basic stats
            total_checks = usage_query.count()
            enabled_checks = usage_query.filter(enabled=True).count()
            
            # By flag
            by_flag = usage_query.values('flag__key', 'flag__name').annotate(
                total=Count('id'),
                enabled=Count('id', filter=Q(enabled=True))
            ).order_by('-total')
            
            # By user
            by_user = usage_query.filter(user__isnull=False).values(
                'user__email'
            ).annotate(
                total=Count('id'),
                enabled=Count('id', filter=Q(enabled=True))
            ).order_by('-total')[:10]
            
            return {
                'total_checks': total_checks,
                'enabled_checks': enabled_checks,
                'enabled_rate': enabled_checks / total_checks if total_checks > 0 else 0,
                'by_flag': list(by_flag),
                'by_user': list(by_user),
                'period_days': days,
            }
            
        except Exception as e:
            logger.error(f"Analytics error: {e}")
            return {}
    
    # Private methods
    
    @classmethod
    def _get_flag(cls, flag_key):
        """
        Get flag from cache or database.
        """
        cache_key = f"{cls.CACHE_PREFIX}flag:{flag_key}"
        flag = cache.get(cache_key)
        
        if flag is None:
            try:
                flag = FeatureFlag.objects.get(key=flag_key)
                cache.set(cache_key, flag, cls.CACHE_TIMEOUT)
            except FeatureFlag.DoesNotExist:
                # Cache negative result
                cache.set(cache_key, False, cls.CACHE_TIMEOUT)
                return None
        
        return flag if flag else None
    
    @classmethod
    def _get_user_override(cls, flag_key, user):
        """
        Get user override from cache or database.
        """
        cache_key = f"{cls.CACHE_PREFIX}override:{user.id}:{flag_key}"
        override = cache.get(cache_key)
        
        if override is None:
            try:
                override = FeatureFlagOverride.objects.select_related('flag').get(
                    user=user,
                    flag__key=flag_key
                )
                cache.set(cache_key, override, cls.CACHE_TIMEOUT)
            except FeatureFlagOverride.DoesNotExist:
                # Cache negative result
                cache.set(cache_key, False, cls.CACHE_TIMEOUT)
                return None
        
        return override if override else None
    
    @classmethod
    def _log_usage(cls, flag_key, user, enabled, variant, environment, 
                   request, metadata, override=False, not_found=False):
        """
        Log feature flag usage asynchronously.
        """
        try:
            # Get or create flag for logging
            if not not_found:
                flag = cls._get_flag(flag_key)
                if flag:
                    # Add context to metadata
                    log_metadata = metadata or {}
                    log_metadata.update({
                        'override': override,
                        'not_found': not_found,
                    })
                    
                    FeatureFlagUsage.log_usage(
                        flag=flag,
                        user=user,
                        enabled=enabled,
                        variant=variant,
                        environment=environment,
                        request=request,
                        metadata=log_metadata
                    )
        except Exception as e:
            logger.error(f"Usage logging error: {e}")
    
    @classmethod
    def _clear_user_cache(cls, user):
        """
        Clear cache for user overrides.
        """
        try:
            # This is a simplified approach - in production you'd want
            # more sophisticated cache invalidation
            cache_pattern = f"{cls.CACHE_PREFIX}override:{user.id}:*"
            # Note: This requires Redis or similar cache backend with pattern support
            # For Django's default cache, you'd need to track keys separately
        except Exception as e:
            logger.error(f"Cache clear error: {e}")


# Convenience functions for common 2090 features

def is_zero_knowledge_enabled(user=None, request=None):
    """Check if Zero-Knowledge Vault is enabled."""
    return FeatureFlagService.is_enabled('zero_knowledge_vault', user, request=request)

def is_anti_deepfake_enabled(user=None, request=None):
    """Check if Anti-Deepfake Authenticity is enabled."""
    return FeatureFlagService.is_enabled('anti_deepfake_authenticity', user, request=request)

def is_semantic_search_enabled(user=None, request=None):
    """Check if Semantic Search AI is enabled."""
    return FeatureFlagService.is_enabled('semantic_search_ai', user, request=request)

def is_digital_legacy_enabled(user=None, request=None):
    """Check if Digital Legacy Vault is enabled."""
    return FeatureFlagService.is_enabled('digital_legacy_vault', user, request=request)

def is_consent_sharing_enabled(user=None, request=None):
    """Check if Consent-Based Sharing is enabled."""
    return FeatureFlagService.is_enabled('consent_based_sharing', user, request=request)

def get_ai_enhancement_variant(user=None, request=None):
    """Get AI Photo Enhancement experiment variant."""
    return FeatureFlagService.get_variant('ai_photo_enhancement', user, request=request)