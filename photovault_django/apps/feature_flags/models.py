"""
Feature Flag System for PhotoVault 2090 Features.
Enables controlled rollout of advanced features.
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.cache import cache
import json

User = get_user_model()


class FeatureFlag(models.Model):
    """
    Feature flag configuration for controlling feature availability.
    """
    
    FLAG_TYPES = [
        ('BOOLEAN', 'Boolean'),
        ('PERCENTAGE', 'Percentage Rollout'),
        ('USER_LIST', 'User Whitelist'),
        ('EXPERIMENT', 'A/B Test Experiment'),
    ]
    
    ENVIRONMENTS = [
        ('DEVELOPMENT', 'Development'),
        ('STAGING', 'Staging'),
        ('PRODUCTION', 'Production'),
    ]
    
    # Core fields
    key = models.CharField(max_length=100, unique=True, db_index=True)
    name = models.CharField(max_length=200)
    description = models.TextField()
    
    # Flag configuration
    flag_type = models.CharField(max_length=20, choices=FLAG_TYPES, default='BOOLEAN')
    is_active = models.BooleanField(default=False)
    
    # Rollout configuration
    rollout_percentage = models.IntegerField(default=0, help_text="0-100 for percentage rollout")
    user_whitelist = models.ManyToManyField(User, blank=True, related_name='whitelisted_features')
    
    # Environment targeting
    environments = models.JSONField(default=list, help_text="List of environments where flag is active")
    
    # Experiment configuration
    experiment_config = models.JSONField(default=dict, blank=True)
    
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_flags')
    tags = models.JSONField(default=list, help_text="Tags for organizing flags")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'feature_flags'
        ordering = ['name']
        indexes = [
            models.Index(fields=['key']),
            models.Index(fields=['is_active']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.key})"
    
    def is_enabled_for_user(self, user=None, environment='PRODUCTION'):
        """
        Check if feature is enabled for a specific user.
        """
        # Check if flag is active
        if not self.is_active:
            return False
        
        # Check expiration
        if self.expires_at and timezone.now() > self.expires_at:
            return False
        
        # Check environment
        if environment not in self.environments:
            return False
        
        # Boolean flag
        if self.flag_type == 'BOOLEAN':
            return True
        
        # User whitelist
        if self.flag_type == 'USER_LIST':
            return user and self.user_whitelist.filter(id=user.id).exists()
        
        # Percentage rollout
        if self.flag_type == 'PERCENTAGE':
            if user:
                # Use user ID for consistent rollout
                user_hash = hash(f"{self.key}:{user.id}") % 100
                return user_hash < self.rollout_percentage
            return False
        
        # Experiment
        if self.flag_type == 'EXPERIMENT':
            return self._evaluate_experiment(user)
        
        return False
    
    def _evaluate_experiment(self, user):
        """
        Evaluate A/B test experiment.
        """
        if not user or not self.experiment_config:
            return False
        
        variants = self.experiment_config.get('variants', [])
        if not variants:
            return False
        
        # Consistent assignment based on user ID
        user_hash = hash(f"{self.key}:{user.id}") % 100
        
        cumulative_percentage = 0
        for variant in variants:
            percentage = variant.get('percentage', 0)
            if user_hash < cumulative_percentage + percentage:
                return variant.get('enabled', False)
            cumulative_percentage += percentage
        
        return False
    
    def get_variant_for_user(self, user):
        """
        Get experiment variant for user.
        """
        if self.flag_type != 'EXPERIMENT' or not user:
            return None
        
        variants = self.experiment_config.get('variants', [])
        if not variants:
            return None
        
        user_hash = hash(f"{self.key}:{user.id}") % 100
        
        cumulative_percentage = 0
        for variant in variants:
            percentage = variant.get('percentage', 0)
            if user_hash < cumulative_percentage + percentage:
                return variant.get('name')
            cumulative_percentage += percentage
        
        return None


class FeatureFlagUsage(models.Model):
    """
    Track feature flag usage and analytics.
    """
    
    flag = models.ForeignKey(FeatureFlag, on_delete=models.CASCADE, related_name='usage_logs')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Usage context
    enabled = models.BooleanField()
    variant = models.CharField(max_length=100, blank=True)
    environment = models.CharField(max_length=20, default='PRODUCTION')
    
    # Request context
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'feature_flag_usage'
        indexes = [
            models.Index(fields=['flag', '-timestamp']),
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['-timestamp']),
        ]
    
    @classmethod
    def log_usage(cls, flag, user=None, enabled=False, variant='', 
                  environment='PRODUCTION', request=None, metadata=None):
        """
        Log feature flag usage.
        """
        # Extract request context
        ip_address = None
        user_agent = ''
        
        if request:
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip_address = x_forwarded_for.split(',')[0].strip()
            else:
                ip_address = request.META.get('REMOTE_ADDR')
            
            user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        return cls.objects.create(
            flag=flag,
            user=user,
            enabled=enabled,
            variant=variant,
            environment=environment,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=metadata or {}
        )


class FeatureFlagOverride(models.Model):
    """
    User-specific feature flag overrides.
    """
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='flag_overrides')
    flag = models.ForeignKey(FeatureFlag, on_delete=models.CASCADE, related_name='user_overrides')
    
    # Override configuration
    enabled = models.BooleanField()
    variant = models.CharField(max_length=100, blank=True)
    
    # Metadata
    reason = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_overrides')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'feature_flag_overrides'
        unique_together = ['user', 'flag']
        indexes = [
            models.Index(fields=['user', 'flag']),
            models.Index(fields=['expires_at']),
        ]
    
    def is_active(self):
        """
        Check if override is still active.
        """
        if self.expires_at:
            return timezone.now() <= self.expires_at
        return True


# 2090 Feature Flags - Predefined for PhotoVault
PHOTOVAULT_2090_FEATURES = {
    'zero_knowledge_vault': {
        'name': 'Zero-Knowledge Vault',
        'description': 'Client-side encryption with zero-knowledge architecture',
        'flag_type': 'PERCENTAGE',
        'tags': ['security', 'encryption', '2090'],
    },
    'anti_deepfake_authenticity': {
        'name': 'Anti-Deepfake Authenticity',
        'description': 'Blockchain-based photo authenticity verification',
        'flag_type': 'USER_LIST',
        'tags': ['security', 'blockchain', 'ai', '2090'],
    },
    'semantic_search_ai': {
        'name': 'Semantic Search AI',
        'description': 'Natural language photo search with AI understanding',
        'flag_type': 'PERCENTAGE',
        'tags': ['ai', 'search', 'nlp', '2090'],
    },
    'digital_legacy_vault': {
        'name': 'Digital Legacy Vault',
        'description': 'Automated inheritance and memorial features',
        'flag_type': 'BOOLEAN',
        'tags': ['legacy', 'inheritance', '2090'],
    },
    'consent_based_sharing': {
        'name': 'Consent-Based Sharing',
        'description': 'Advanced privacy controls with consent management',
        'flag_type': 'PERCENTAGE',
        'tags': ['privacy', 'sharing', 'consent', '2090'],
    },
    'quantum_resistant_encryption': {
        'name': 'Quantum-Resistant Encryption',
        'description': 'Post-quantum cryptography for future-proof security',
        'flag_type': 'USER_LIST',
        'tags': ['security', 'quantum', 'encryption', '2090'],
    },
    'ai_photo_enhancement': {
        'name': 'AI Photo Enhancement',
        'description': 'Automatic photo enhancement using advanced AI',
        'flag_type': 'EXPERIMENT',
        'tags': ['ai', 'enhancement', 'processing', '2090'],
    },
    'biometric_access_control': {
        'name': 'Biometric Access Control',
        'description': 'Face/fingerprint authentication for albums',
        'flag_type': 'PERCENTAGE',
        'tags': ['biometric', 'security', 'access', '2090'],
    },
    'temporal_photo_analysis': {
        'name': 'Temporal Photo Analysis',
        'description': 'AI-powered timeline and life event detection',
        'flag_type': 'BOOLEAN',
        'tags': ['ai', 'timeline', 'analysis', '2090'],
    },
    'decentralized_backup': {
        'name': 'Decentralized Backup',
        'description': 'IPFS-based distributed photo storage',
        'flag_type': 'USER_LIST',
        'tags': ['decentralized', 'backup', 'ipfs', '2090'],
    },
}