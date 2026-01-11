"""
Middleware for audit logging and security monitoring.
"""
import logging
import json
import time
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth import get_user_model

User = get_user_model()

# Create audit logger
audit_logger = logging.getLogger('audit')


class AuditLoggingMiddleware(MiddlewareMixin):
    """
    Middleware to log security-relevant events and API access.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
    
    def process_request(self, request):
        """Process incoming request."""
        request._audit_start_time = time.time()
        return None
    
    def process_response(self, request, response):
        """Process outgoing response and log audit events."""
        
        # Skip static files and health checks
        if (request.path.startswith('/static/') or 
            request.path.startswith('/media/') or
            request.path == '/health/'):
            return response
        
        # Calculate response time
        start_time = getattr(request, '_audit_start_time', time.time())
        response_time = (time.time() - start_time) * 1000  # milliseconds
        
        # Get user info
        user_id = None
        username = 'anonymous'
        if hasattr(request, 'user') and request.user.is_authenticated:
            user_id = request.user.id
            username = request.user.email or request.user.username
        
        # Get client info
        client_ip = self.get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')[:200]
        
        # Determine log level based on response status
        if response.status_code >= 500:
            log_level = logging.ERROR
        elif response.status_code >= 400:
            log_level = logging.WARNING
        else:
            log_level = logging.INFO
        
        # Create audit log entry
        audit_data = {
            'timestamp': time.time(),
            'method': request.method,
            'path': request.path,
            'status_code': response.status_code,
            'response_time_ms': round(response_time, 2),
            'user_id': user_id,
            'username': username,
            'client_ip': client_ip,
            'user_agent': user_agent,
            'content_length': len(response.content) if hasattr(response, 'content') else 0
        }
        
        # Add query parameters for GET requests
        if request.method == 'GET' and request.GET:
            audit_data['query_params'] = dict(request.GET)
        
        # Log security-sensitive events with more detail
        if self.is_security_sensitive_path(request.path):
            audit_data['security_event'] = True
            
            # Note: Skip request body logging to avoid RawPostDataException
            # The body has already been consumed by the view
        
        # Log the audit event
        audit_logger.log(
            log_level,
            f"{request.method} {request.path} - {response.status_code} - {username}@{client_ip}",
            extra={'audit_data': audit_data}
        )
        
        # Log specific security events
        self.log_security_events(request, response, audit_data)
        
        return response
    
    def get_client_ip(self, request):
        """Get client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', 'unknown')
        return ip
    
    def is_security_sensitive_path(self, path):
        """Check if path is security sensitive."""
        sensitive_paths = [
            '/api/auth/',
            '/api/sharing/',
            '/admin/',
        ]
        return any(path.startswith(sensitive_path) for sensitive_path in sensitive_paths)
    
    def log_security_events(self, request, response, audit_data):
        """Log specific security events."""
        
        # Failed login attempts
        if (request.path == '/api/auth/login/' and 
            request.method == 'POST' and 
            response.status_code == 400):
            
            audit_logger.warning(
                f"Failed login attempt from {audit_data['client_ip']} for user in request",
                extra={
                    'event_type': 'failed_login',
                    'audit_data': audit_data
                }
            )
        
        # Successful logins
        if (request.path == '/api/auth/login/' and 
            request.method == 'POST' and 
            response.status_code == 200):
            
            audit_logger.info(
                f"Successful login from {audit_data['client_ip']} for user {audit_data['username']}",
                extra={
                    'event_type': 'successful_login',
                    'audit_data': audit_data
                }
            )
        
        # Account registrations
        if (request.path == '/api/auth/register/' and 
            request.method == 'POST' and 
            response.status_code == 201):
            
            audit_logger.info(
                f"New account registration from {audit_data['client_ip']}",
                extra={
                    'event_type': 'account_registration',
                    'audit_data': audit_data
                }
            )
        
        # Password changes
        if (request.path == '/api/auth/change-password/' and 
            request.method == 'POST' and 
            response.status_code == 200):
            
            audit_logger.info(
                f"Password changed for user {audit_data['username']} from {audit_data['client_ip']}",
                extra={
                    'event_type': 'password_change',
                    'audit_data': audit_data
                }
            )
        
        # Share link access
        if ('/api/sharing/view/' in request.path and 
            request.method == 'GET'):
            
            if response.status_code == 200:
                audit_logger.info(
                    f"Share link accessed from {audit_data['client_ip']}",
                    extra={
                        'event_type': 'share_access',
                        'audit_data': audit_data
                    }
                )
            else:
                audit_logger.warning(
                    f"Failed share link access from {audit_data['client_ip']}",
                    extra={
                        'event_type': 'failed_share_access',
                        'audit_data': audit_data
                    }
                )
        
        # Rate limiting violations (429 status)
        if response.status_code == 429:
            audit_logger.warning(
                f"Rate limit exceeded from {audit_data['client_ip']} for {request.path}",
                extra={
                    'event_type': 'rate_limit_exceeded',
                    'audit_data': audit_data
                }
            )
        
        # Suspicious activity (multiple 403s, 404s)
        if response.status_code in [403, 404] and audit_data.get('user_id'):
            audit_logger.warning(
                f"Access denied for user {audit_data['username']} from {audit_data['client_ip']} to {request.path}",
                extra={
                    'event_type': 'access_denied',
                    'audit_data': audit_data
                }
            )


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Middleware to add security headers to responses.
    """
    
    def process_response(self, request, response):
        """Add security headers."""
        
        # Content Security Policy
        response['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: blob:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )
        
        # Additional security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        
        return response