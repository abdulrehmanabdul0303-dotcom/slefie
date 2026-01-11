"""
Tests for Feature Flag system.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APITestCase
from rest_framework import status

from .models import FeatureFlag, FeatureFlagUsage, FeatureFlagOverride
from .services import FeatureFlagService

User = get_user_model()


class FeatureFlagModelTests(TestCase):
    """Test Feature Flag models."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            dek_encrypted_b64='test_dek'
        )
    
    def test_boolean_flag(self):
        """Test boolean feature flag."""
        flag = FeatureFlag.objects.create(
            key='test_boolean',
            name='Test Boolean Flag',
            description='Test flag',
            flag_type='BOOLEAN',
            is_active=True,
            environments=['PRODUCTION']
        )
        
        # Should be enabled for any user
        self.assertTrue(flag.is_enabled_for_user(self.user, 'PRODUCTION'))
        self.assertTrue(flag.is_enabled_for_user(None, 'PRODUCTION'))
        
        # Should be disabled in wrong environment
        self.assertFalse(flag.is_enabled_for_user(self.user, 'STAGING'))
    
    def test_percentage_rollout(self):
        """Test percentage rollout flag."""
        flag = FeatureFlag.objects.create(
            key='test_percentage',
            name='Test Percentage Flag',
            description='Test flag',
            flag_type='PERCENTAGE',
            is_active=True,
            rollout_percentage=50,
            environments=['PRODUCTION']
        )
        
        # Test with multiple users to check distribution
        enabled_count = 0
        for i in range(100):
            test_user = User.objects.create_user(
                username=f'user{i}',
                email=f'user{i}@example.com',
                password='testpass123',
                dek_encrypted_b64='test_dek'
            )
            if flag.is_enabled_for_user(test_user, 'PRODUCTION'):
                enabled_count += 1
        
        # Should be roughly 50% (allow some variance)
        self.assertGreater(enabled_count, 30)
        self.assertLess(enabled_count, 70)
    
    def test_user_whitelist(self):
        """Test user whitelist flag."""
        flag = FeatureFlag.objects.create(
            key='test_whitelist',
            name='Test Whitelist Flag',
            description='Test flag',
            flag_type='USER_LIST',
            is_active=True,
            environments=['PRODUCTION']
        )
        
        # Should be disabled for non-whitelisted user
        self.assertFalse(flag.is_enabled_for_user(self.user, 'PRODUCTION'))
        
        # Add user to whitelist
        flag.user_whitelist.add(self.user)
        
        # Should be enabled for whitelisted user
        self.assertTrue(flag.is_enabled_for_user(self.user, 'PRODUCTION'))
    
    def test_experiment_flag(self):
        """Test experiment flag with variants."""
        flag = FeatureFlag.objects.create(
            key='test_experiment',
            name='Test Experiment Flag',
            description='Test flag',
            flag_type='EXPERIMENT',
            is_active=True,
            environments=['PRODUCTION'],
            experiment_config={
                'variants': [
                    {'name': 'control', 'percentage': 50, 'enabled': True},
                    {'name': 'variant_a', 'percentage': 30, 'enabled': True},
                    {'name': 'variant_b', 'percentage': 20, 'enabled': False},
                ]
            }
        )
        
        # Test variant assignment
        variant = flag.get_variant_for_user(self.user)
        self.assertIn(variant, ['control', 'variant_a', 'variant_b'])
        
        # Variant should be consistent for same user
        variant2 = flag.get_variant_for_user(self.user)
        self.assertEqual(variant, variant2)
    
    def test_flag_expiry(self):
        """Test flag expiration."""
        flag = FeatureFlag.objects.create(
            key='test_expiry',
            name='Test Expiry Flag',
            description='Test flag',
            flag_type='BOOLEAN',
            is_active=True,
            environments=['PRODUCTION'],
            expires_at=timezone.now() - timedelta(hours=1)  # Expired
        )
        
        # Should be disabled due to expiry
        self.assertFalse(flag.is_enabled_for_user(self.user, 'PRODUCTION'))


class FeatureFlagServiceTests(TestCase):
    """Test Feature Flag service."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            dek_encrypted_b64='test_dek'
        )
        
        self.flag = FeatureFlag.objects.create(
            key='test_service',
            name='Test Service Flag',
            description='Test flag',
            flag_type='BOOLEAN',
            is_active=True,
            environments=['PRODUCTION']
        )
    
    def test_is_enabled(self):
        """Test service is_enabled method."""
        # Should be enabled
        self.assertTrue(
            FeatureFlagService.is_enabled('test_service', self.user, 'PRODUCTION')
        )
        
        # Should be disabled for non-existent flag
        self.assertFalse(
            FeatureFlagService.is_enabled('non_existent', self.user, 'PRODUCTION')
        )
    
    def test_user_override(self):
        """Test user-specific overrides."""
        # Create override to disable flag for user
        FeatureFlagOverride.objects.create(
            user=self.user,
            flag=self.flag,
            enabled=False
        )
        
        # Should be disabled due to override
        self.assertFalse(
            FeatureFlagService.is_enabled('test_service', self.user, 'PRODUCTION')
        )
        
        # Should still be enabled for other users
        other_user = User.objects.create_user(
            username='other',
            email='other@example.com',
            password='testpass123',
            dek_encrypted_b64='test_dek'
        )
        self.assertTrue(
            FeatureFlagService.is_enabled('test_service', other_user, 'PRODUCTION')
        )
    
    def test_usage_logging(self):
        """Test usage logging."""
        initial_count = FeatureFlagUsage.objects.count()
        
        # Enable flag (should log usage)
        FeatureFlagService.is_enabled('test_service', self.user, 'PRODUCTION')
        
        # Should have logged usage
        self.assertEqual(FeatureFlagUsage.objects.count(), initial_count + 1)
        
        usage = FeatureFlagUsage.objects.latest('timestamp')
        self.assertEqual(usage.flag, self.flag)
        self.assertEqual(usage.user, self.user)
        self.assertTrue(usage.enabled)
    
    def test_get_enabled_flags(self):
        """Test getting all enabled flags."""
        # Create another flag
        FeatureFlag.objects.create(
            key='test_service_2',
            name='Test Service Flag 2',
            description='Test flag 2',
            flag_type='BOOLEAN',
            is_active=True,
            environments=['PRODUCTION'],
            tags=['test']
        )
        
        enabled_flags = FeatureFlagService.get_enabled_flags(
            user=self.user,
            environment='PRODUCTION'
        )
        
        self.assertIn('test_service', enabled_flags)
        self.assertIn('test_service_2', enabled_flags)
        self.assertTrue(enabled_flags['test_service']['enabled'])
        self.assertTrue(enabled_flags['test_service_2']['enabled'])
        
        # Test tag filtering
        tagged_flags = FeatureFlagService.get_enabled_flags(
            user=self.user,
            environment='PRODUCTION',
            tags=['test']
        )
        
        self.assertNotIn('test_service', tagged_flags)
        self.assertIn('test_service_2', tagged_flags)


class FeatureFlagAPITests(APITestCase):
    """Test Feature Flag API endpoints."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            dek_encrypted_b64='test_dek'
        )
        
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            is_staff=True,
            is_superuser=True,
            dek_encrypted_b64='test_dek'
        )
        
        self.flag = FeatureFlag.objects.create(
            key='test_api',
            name='Test API Flag',
            description='Test flag',
            flag_type='BOOLEAN',
            is_active=True,
            environments=['PRODUCTION']
        )
    
    def test_flag_list_authenticated(self):
        """Test flag list for authenticated user."""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.get('/api/feature-flags/flags/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should see active flags
        flag_keys = [flag['key'] for flag in response.data['results']]
        self.assertIn('test_api', flag_keys)
    
    def test_flag_evaluation(self):
        """Test flag evaluation endpoint."""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.post('/api/feature-flags/evaluate/', {
            'flags': ['test_api'],
            'environment': 'PRODUCTION'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('test_api', response.data['flags'])
        self.assertTrue(response.data['flags']['test_api'])
    
    def test_2090_features_endpoint(self):
        """Test PhotoVault 2090 features endpoint."""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.get('/api/feature-flags/2090/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should return 2090 features
        self.assertIn('features', response.data)
        features = response.data['features']
        
        # Check some expected features
        expected_features = [
            'zero_knowledge_vault',
            'anti_deepfake_authenticity',
            'semantic_search_ai'
        ]
        
        for feature in expected_features:
            self.assertIn(feature, features)
            self.assertIn('name', features[feature])
            self.assertIn('description', features[feature])
            self.assertIn('enabled', features[feature])
    
    def test_create_2090_flags_admin(self):
        """Test creating 2090 flags (admin only)."""
        self.client.force_authenticate(user=self.admin_user)
        
        response = self.client.post('/api/feature-flags/flags/create_2090_flags/', {
            'environment': 'DEVELOPMENT',
            'enable_flags': True
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('created', response.data)
        
        # Check that flags were created
        created_flags = FeatureFlag.objects.filter(
            key__in=['zero_knowledge_vault', 'semantic_search_ai']
        )
        self.assertTrue(created_flags.exists())
    
    def test_create_2090_flags_non_admin(self):
        """Test creating 2090 flags as non-admin (should fail)."""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.post('/api/feature-flags/flags/create_2090_flags/', {
            'environment': 'DEVELOPMENT',
            'enable_flags': True
        })
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class FeatureFlagDecoratorTests(TestCase):
    """Test feature flag decorators."""
    
    def setUp(self):
        from django.test import RequestFactory
        from django.contrib.auth.models import AnonymousUser
        
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            dek_encrypted_b64='test_dek'
        )
        
        self.flag = FeatureFlag.objects.create(
            key='test_decorator',
            name='Test Decorator Flag',
            description='Test flag',
            flag_type='BOOLEAN',
            is_active=True,
            environments=['PRODUCTION']
        )
    
    def test_feature_flag_required_decorator(self):
        """Test feature_flag_required decorator."""
        from .decorators import feature_flag_required
        
        @feature_flag_required('test_decorator')
        def test_view(request):
            return {'success': True}
        
        # Test with enabled flag
        request = self.factory.get('/')
        request.user = self.user
        
        result = test_view(request)
        self.assertEqual(result, {'success': True})
        
        # Test with disabled flag
        self.flag.is_active = False
        self.flag.save()
        
        result = test_view(request)
        self.assertEqual(result.status_code, 403)
    
    def test_feature_flag_context_decorator(self):
        """Test feature_flag_context decorator."""
        from .decorators import feature_flag_context
        
        @feature_flag_context(['test_decorator'])
        def test_view(request):
            return request.feature_flags
        
        request = self.factory.get('/')
        request.user = self.user
        
        result = test_view(request)
        self.assertIn('test_decorator', result)
        self.assertTrue(result['test_decorator']['enabled'])