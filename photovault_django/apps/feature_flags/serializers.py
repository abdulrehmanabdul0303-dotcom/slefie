"""
Serializers for Feature Flag API.
"""
from rest_framework import serializers
from .models import FeatureFlag, FeatureFlagUsage, FeatureFlagOverride


class FeatureFlagSerializer(serializers.ModelSerializer):
    """
    Serializer for Feature Flag model.
    """
    usage_count = serializers.SerializerMethodField()
    is_enabled_for_user = serializers.SerializerMethodField()
    variant_for_user = serializers.SerializerMethodField()
    
    class Meta:
        model = FeatureFlag
        fields = [
            'id', 'key', 'name', 'description', 'flag_type', 'is_active',
            'rollout_percentage', 'environments', 'experiment_config',
            'tags', 'created_at', 'updated_at', 'expires_at',
            'usage_count', 'is_enabled_for_user', 'variant_for_user'
        ]
        read_only_fields = ['created_at', 'updated_at', 'usage_count']
    
    def get_usage_count(self, obj):
        """Get usage count for the flag."""
        return obj.usage_logs.count()
    
    def get_is_enabled_for_user(self, obj):
        """Check if flag is enabled for current user."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.is_enabled_for_user(request.user)
        return False
    
    def get_variant_for_user(self, obj):
        """Get variant for current user."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.get_variant_for_user(request.user)
        return ''


class FeatureFlagCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating Feature Flags.
    """
    
    class Meta:
        model = FeatureFlag
        fields = [
            'key', 'name', 'description', 'flag_type', 'is_active',
            'rollout_percentage', 'environments', 'experiment_config',
            'tags', 'expires_at'
        ]
    
    def validate_key(self, value):
        """Validate flag key format."""
        import re
        if not re.match(r'^[a-z0-9_]+$', value):
            raise serializers.ValidationError(
                'Key must contain only lowercase letters, numbers, and underscores.'
            )
        return value
    
    def validate_rollout_percentage(self, value):
        """Validate rollout percentage."""
        if not 0 <= value <= 100:
            raise serializers.ValidationError(
                'Rollout percentage must be between 0 and 100.'
            )
        return value
    
    def validate_experiment_config(self, value):
        """Validate experiment configuration."""
        if self.initial_data.get('flag_type') == 'EXPERIMENT' and value:
            variants = value.get('variants', [])
            if not variants:
                raise serializers.ValidationError(
                    'Experiment flags must have at least one variant.'
                )
            
            total_percentage = sum(v.get('percentage', 0) for v in variants)
            if total_percentage > 100:
                raise serializers.ValidationError(
                    'Total variant percentages cannot exceed 100.'
                )
        
        return value


class FeatureFlagUsageSerializer(serializers.ModelSerializer):
    """
    Serializer for Feature Flag Usage analytics.
    """
    flag_name = serializers.CharField(source='flag.name', read_only=True)
    flag_key = serializers.CharField(source='flag.key', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = FeatureFlagUsage
        fields = [
            'id', 'flag_name', 'flag_key', 'user_email', 'enabled',
            'variant', 'environment', 'ip_address', 'timestamp', 'metadata'
        ]
        read_only_fields = ['timestamp']


class FeatureFlagOverrideSerializer(serializers.ModelSerializer):
    """
    Serializer for Feature Flag Overrides.
    """
    flag_name = serializers.CharField(source='flag.name', read_only=True)
    flag_key = serializers.CharField(source='flag.key', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    is_active = serializers.SerializerMethodField()
    
    class Meta:
        model = FeatureFlagOverride
        fields = [
            'id', 'flag_name', 'flag_key', 'user_email', 'enabled',
            'variant', 'reason', 'created_at', 'expires_at', 'is_active'
        ]
        read_only_fields = ['created_at']
    
    def get_is_active(self, obj):
        """Check if override is currently active."""
        return obj.is_active()


class FeatureFlagOverrideCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating Feature Flag Overrides.
    """
    
    class Meta:
        model = FeatureFlagOverride
        fields = ['flag', 'user', 'enabled', 'variant', 'reason', 'expires_at']


class FeatureFlagEvaluationSerializer(serializers.Serializer):
    """
    Serializer for feature flag evaluation requests.
    """
    flags = serializers.ListField(
        child=serializers.CharField(),
        help_text="List of feature flag keys to evaluate"
    )
    environment = serializers.CharField(
        required=False,
        default='PRODUCTION',
        help_text="Environment to evaluate flags for"
    )
    
    def validate_flags(self, value):
        """Validate flag keys exist."""
        if not value:
            raise serializers.ValidationError("At least one flag key is required.")
        
        # Check if flags exist
        existing_flags = FeatureFlag.objects.filter(key__in=value).values_list('key', flat=True)
        missing_flags = set(value) - set(existing_flags)
        
        if missing_flags:
            raise serializers.ValidationError(
                f"Unknown flags: {', '.join(missing_flags)}"
            )
        
        return value


class FeatureFlagEvaluationResponseSerializer(serializers.Serializer):
    """
    Serializer for feature flag evaluation responses.
    """
    flags = serializers.DictField(
        help_text="Dictionary of flag evaluations"
    )
    user_id = serializers.IntegerField(allow_null=True)
    environment = serializers.CharField()
    timestamp = serializers.DateTimeField()


class FeatureFlagAnalyticsSerializer(serializers.Serializer):
    """
    Serializer for feature flag analytics.
    """
    total_checks = serializers.IntegerField()
    enabled_checks = serializers.IntegerField()
    enabled_rate = serializers.FloatField()
    period_days = serializers.IntegerField()
    by_flag = serializers.ListField(
        child=serializers.DictField()
    )
    by_user = serializers.ListField(
        child=serializers.DictField()
    )


class Bulk2090FlagsSerializer(serializers.Serializer):
    """
    Serializer for bulk creating 2090 feature flags.
    """
    environment = serializers.ChoiceField(
        choices=['DEVELOPMENT', 'STAGING', 'PRODUCTION'],
        default='DEVELOPMENT',
        help_text="Environment to enable flags in"
    )
    enable_flags = serializers.BooleanField(
        default=False,
        help_text="Whether to enable flags after creation"
    )
    tags_filter = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text="Only create flags with these tags"
    )