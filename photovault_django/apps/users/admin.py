"""
Admin configuration for users app.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, PersonCluster, EmailVerificationToken, PasswordResetToken


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Admin configuration for User model.
    """
    list_display = ('email', 'name', 'is_admin', 'email_verified', 'is_active', 'date_joined')
    list_filter = ('is_admin', 'email_verified', 'is_active', 'date_joined')
    search_fields = ('email', 'name')
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('name', 'google_id')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'is_admin', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
        ('Security', {'fields': ('email_verified', 'failed_login_attempts', 'locked_until')}),
        ('Encryption', {'fields': ('dek_encrypted_b64',)}),
        ('Face Recognition', {'fields': ('face_embedding_json',)}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'name', 'password1', 'password2'),
        }),
    )
    
    readonly_fields = ('date_joined', 'last_login')


@admin.register(PersonCluster)
class PersonClusterAdmin(admin.ModelAdmin):
    """
    Admin configuration for PersonCluster model.
    """
    list_display = ('name', 'user', 'confidence_score', 'created_at')
    list_filter = ('created_at', 'confidence_score')
    search_fields = ('name', 'user__email')
    ordering = ('-created_at',)
    
    fieldsets = (
        (None, {'fields': ('user', 'name')}),
        ('Face Data', {'fields': ('face_embedding_json', 'representative_face_id', 'confidence_score')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )
    
    readonly_fields = ('created_at', 'updated_at')


@admin.register(EmailVerificationToken)
class EmailVerificationTokenAdmin(admin.ModelAdmin):
    """
    Admin configuration for EmailVerificationToken model.
    """
    list_display = ('user', 'token', 'used', 'expires_at', 'created_at')
    list_filter = ('used', 'expires_at', 'created_at')
    search_fields = ('user__email', 'token')
    ordering = ('-created_at',)
    
    readonly_fields = ('created_at',)


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    """
    Admin configuration for PasswordResetToken model.
    """
    list_display = ('user', 'token', 'used', 'expires_at', 'created_at')
    list_filter = ('used', 'expires_at', 'created_at')
    search_fields = ('user__email', 'token')
    ordering = ('-created_at',)
    
    readonly_fields = ('created_at',)