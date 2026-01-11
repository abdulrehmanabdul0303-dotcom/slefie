"""
Serializers for user authentication and management.
"""
from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import User, PersonCluster


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    """
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ('email', 'name', 'password', 'password_confirm')
    
    def validate_name(self, value):
        """
        Validate and sanitize the name field to prevent XSS.
        """
        import html
        import re
        
        # Remove HTML tags
        clean_name = re.sub(r'<[^>]*>', '', value)
        
        # HTML escape any remaining special characters
        clean_name = html.escape(clean_name)
        
        # Ensure name is not empty after cleaning
        if not clean_name.strip():
            raise serializers.ValidationError("Name cannot be empty or contain only HTML tags.")
        
        return clean_name.strip()
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match.")
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        
        # Generate and encrypt DEK (Data Encryption Key)
        from .services import EncryptionService
        dek = EncryptionService.generate_dek()
        encrypted_dek = EncryptionService.encrypt_dek(dek, password)
        validated_data['dek_encrypted_b64'] = encrypted_dek
        
        user = User.objects.create_user(
            username=validated_data['email'],  # Use email as username
            **validated_data
        )
        user.set_password(password)
        user.save()
        
        return user


class UserLoginSerializer(serializers.Serializer):
    """
    Serializer for user login.
    """
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            # Check if user exists
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                raise serializers.ValidationError('Invalid credentials.')
            
            # Check if account is locked
            if user.is_locked:
                raise serializers.ValidationError('Account is temporarily locked due to too many failed attempts.')
            
            # Authenticate user
            user = authenticate(username=email, password=password)
            if not user:
                # Increment failed attempts for existing user
                try:
                    existing_user = User.objects.get(email=email)
                    existing_user.increment_failed_attempts()
                except User.DoesNotExist:
                    pass
                raise serializers.ValidationError('Invalid credentials.')
            
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled.')
            
            # Reset failed attempts on successful login
            user.reset_failed_attempts()
            attrs['user'] = user
            
        else:
            raise serializers.ValidationError('Must include email and password.')
        
        return attrs


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for user profile information.
    """
    class Meta:
        model = User
        fields = ('id', 'email', 'name', 'is_admin', 'email_verified', 'date_joined', 'last_login')
        read_only_fields = ('id', 'email', 'is_admin', 'email_verified', 'date_joined', 'last_login')


class UserUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating user profile.
    """
    class Meta:
        model = User
        fields = ('name',)


class PasswordChangeSerializer(serializers.Serializer):
    """
    Serializer for changing password.
    """
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("New passwords don't match.")
        return attrs
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value


class PasswordResetRequestSerializer(serializers.Serializer):
    """
    Serializer for password reset request.
    """
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    Serializer for password reset confirmation.
    """
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("Passwords don't match.")
        return attrs


class EmailVerificationSerializer(serializers.Serializer):
    """
    Serializer for email verification.
    """
    token = serializers.CharField()


class PersonClusterSerializer(serializers.ModelSerializer):
    """
    Serializer for person clusters.
    """
    class Meta:
        model = PersonCluster
        fields = ('id', 'name', 'confidence_score', 'representative_face_id', 'created_at')
        read_only_fields = ('id', 'created_at')


class GoogleOAuthSerializer(serializers.Serializer):
    """
    Serializer for Google OAuth authentication.
    """
    access_token = serializers.CharField()
    
    def validate_access_token(self, value):
        # This would validate the Google access token
        # For now, we'll just return the value
        return value