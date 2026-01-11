"""
Custom exception handling for PhotoVault API.
"""
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError
from django.http import Http404
import logging

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Custom exception handler that returns consistent error format.
    
    Expected format:
    {
        "error": {
            "code": "ERROR_CODE",
            "message": "Human readable message",
            "details": {...},  # Optional
            "fields": {...}    # For validation errors
        }
    }
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    if response is not None:
        error_code = get_error_code(exc)
        error_message = get_error_message(exc, response.data)
        
        custom_response_data = {
            'error': {
                'code': error_code,
                'message': error_message,
            }
        }
        
        # Add field-specific errors for validation
        if hasattr(exc, 'detail') and isinstance(exc.detail, dict):
            fields = {}
            for field, errors in exc.detail.items():
                if isinstance(errors, list):
                    fields[field] = [str(error) for error in errors]
                else:
                    fields[field] = [str(errors)]
            
            if fields:
                custom_response_data['error']['fields'] = fields
        
        # Add details for specific error types
        if error_code in ['RATE_LIMITED', 'THROTTLED']:
            custom_response_data['error']['details'] = {
                'retry_after': getattr(exc, 'wait', None)
            }
        
        response.data = custom_response_data
        
        # Log error for monitoring
        log_error(exc, context, response.status_code)
    
    return response


def get_error_code(exc):
    """
    Map exception types to error codes.
    """
    error_mapping = {
        'ValidationError': 'VALIDATION_ERROR',
        'AuthenticationFailed': 'AUTHENTICATION_FAILED',
        'NotAuthenticated': 'NOT_AUTHENTICATED',
        'PermissionDenied': 'PERMISSION_DENIED',
        'NotFound': 'NOT_FOUND',
        'MethodNotAllowed': 'METHOD_NOT_ALLOWED',
        'Throttled': 'RATE_LIMITED',
        'ParseError': 'PARSE_ERROR',
        'UnsupportedMediaType': 'UNSUPPORTED_MEDIA_TYPE',
    }
    
    exc_name = exc.__class__.__name__
    return error_mapping.get(exc_name, 'INTERNAL_ERROR')


def get_error_message(exc, response_data):
    """
    Extract human-readable error message.
    """
    # Custom messages for common errors
    if exc.__class__.__name__ == 'NotAuthenticated':
        return 'Authentication credentials were not provided or are invalid.'
    
    if exc.__class__.__name__ == 'PermissionDenied':
        return 'You do not have permission to perform this action.'
    
    if exc.__class__.__name__ == 'NotFound':
        return 'The requested resource was not found.'
    
    if exc.__class__.__name__ == 'Throttled':
        return 'Request rate limit exceeded. Please try again later.'
    
    # Try to extract message from exception
    if hasattr(exc, 'detail'):
        if isinstance(exc.detail, str):
            return exc.detail
        elif isinstance(exc.detail, dict):
            # For validation errors, return a general message
            return 'The provided data is invalid. Please check the fields and try again.'
        elif isinstance(exc.detail, list) and exc.detail:
            return str(exc.detail[0])
    
    # Fallback to response data
    if isinstance(response_data, dict):
        if 'detail' in response_data:
            return response_data['detail']
        elif 'message' in response_data:
            return response_data['message']
    
    return 'An error occurred while processing your request.'


def log_error(exc, context, status_code):
    """
    Log error for monitoring and debugging.
    """
    request = context.get('request')
    view = context.get('view')
    
    log_data = {
        'exception': exc.__class__.__name__,
        'status_code': status_code,
        'path': request.path if request else None,
        'method': request.method if request else None,
        'user': str(request.user) if request and hasattr(request, 'user') else None,
        'view': view.__class__.__name__ if view else None,
    }
    
    if status_code >= 500:
        logger.error(f"Server error: {exc}", extra=log_data, exc_info=True)
    elif status_code >= 400:
        logger.warning(f"Client error: {exc}", extra=log_data)


class PhotoVaultException(Exception):
    """
    Base exception for PhotoVault-specific errors.
    """
    default_message = "An error occurred"
    default_code = "PHOTOVAULT_ERROR"
    
    def __init__(self, message=None, code=None, details=None):
        self.message = message or self.default_message
        self.code = code or self.default_code
        self.details = details or {}
        super().__init__(self.message)


class EncryptionError(PhotoVaultException):
    """
    Raised when encryption/decryption operations fail.
    """
    default_message = "Encryption operation failed"
    default_code = "ENCRYPTION_ERROR"


class FileProcessingError(PhotoVaultException):
    """
    Raised when file processing operations fail.
    """
    default_message = "File processing failed"
    default_code = "FILE_PROCESSING_ERROR"


class ShareTokenError(PhotoVaultException):
    """
    Raised when share token operations fail.
    """
    default_message = "Share token operation failed"
    default_code = "SHARE_TOKEN_ERROR"


class FeatureFlagError(PhotoVaultException):
    """
    Raised when feature flag operations fail.
    """
    default_message = "Feature flag operation failed"
    default_code = "FEATURE_FLAG_ERROR"