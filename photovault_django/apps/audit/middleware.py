"""
Middleware for automatic audit logging.
"""
from django.utils.deprecation import MiddlewareMixin
from .models import AuditEvent


class AuditLoggingMiddleware(MiddlewareMixin):
    """
    Middleware to automatically log certain events.
    """
    
    def process_request(self, request):
        """Store request start time for performance tracking."""
        import time
        request._audit_start_time = time.time()
        return None
    
    def process_response(self, request, response):
        """Log certain responses based on status code and path."""
        
        # Skip logging for certain paths
        skip_paths = [
            '/admin/',
            '/static/',
            '/media/',
            '/health/',
            '/api/schema/',
            '/docs/',
            '/redoc/',
        ]
        
        if any(request.path.startswith(path) for path in skip_paths):
            return response
        
        # Log failed authentication attempts
        if (request.path.startswith('/api/auth/login/') and 
            response.status_code == 400):
            
            # Extract email from request if possible
            email = None
            try:
                import json
                if hasattr(request, 'body'):
                    data = json.loads(request.body.decode('utf-8'))
                    email = data.get('email')
            except:
                pass
            
            AuditEvent.log_event(
                event_type='LOGIN_FAILED',
                user=None,  # Failed login is always anonymous
                request=request,
                details={
                    'email': email,
                    'status_code': response.status_code,
                    'path': request.path
                },
                success=False,
                error_message='Login attempt failed'
            )
        
        # Log successful logins
        elif (request.path.startswith('/api/auth/login/') and 
              response.status_code == 200):
            
            # Get user if authenticated, otherwise None
            user = getattr(request, 'user', None)
            if hasattr(user, 'is_anonymous') and user.is_anonymous:
                user = None
            
            AuditEvent.log_event(
                event_type='LOGIN_SUCCESS',
                user=user,
                request=request,
                details={
                    'path': request.path
                },
                success=True
            )
        
        # Log registration attempts
        elif (request.path.startswith('/api/auth/register/') and 
              response.status_code == 201):
            
            AuditEvent.log_event(
                event_type='REGISTER',
                user=None,  # Registration is always anonymous
                request=request,
                details={
                    'path': request.path
                },
                success=True
            )
        
        # Log suspicious activity (multiple 401/403 responses)
        elif response.status_code in [401, 403]:
            
            # Check if this IP has multiple recent failures
            ip_address = self._get_client_ip(request)
            if ip_address:
                from django.utils import timezone
                from datetime import timedelta
                
                recent_failures = AuditEvent.objects.filter(
                    ip_address=ip_address,
                    success=False,
                    timestamp__gte=timezone.now() - timedelta(minutes=5)
                ).count()
                
                if recent_failures >= 10:  # Threshold for suspicious activity
                    AuditEvent.log_event(
                        event_type='SUSPICIOUS_ACTIVITY',
                        user=None,  # Suspicious activity is typically anonymous
                        request=request,
                        details={
                            'recent_failures': recent_failures,
                            'status_code': response.status_code,
                            'path': request.path
                        },
                        success=False,
                        error_message=f'Multiple failures from IP: {ip_address}'
                    )
        
        return response
    
    def _get_client_ip(self, request):
        """Get the real client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip