"""
Core views for health checks and system status.
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.db import connection
from django.conf import settings
import redis
import time


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Comprehensive health check endpoint for production monitoring.
    """
    start_time = time.time()
    health_status = {
        'status': 'healthy',
        'service': 'PhotoVault Django API',
        'version': '1.0.0',
        'timestamp': int(time.time()),
        'checks': {}
    }
    
    overall_healthy = True
    
    # Database connectivity check
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        health_status['checks']['database'] = 'ok'
    except Exception as e:
        health_status['checks']['database'] = f'error: {str(e)}'
        overall_healthy = False
    
    # pgvector extension check
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT extname FROM pg_extension WHERE extname = 'vector'")
            result = cursor.fetchone()
            if result:
                health_status['checks']['pgvector'] = 'ok'
            else:
                health_status['checks']['pgvector'] = 'extension not installed'
                overall_healthy = False
    except Exception as e:
        health_status['checks']['pgvector'] = f'error: {str(e)}'
        overall_healthy = False
    
    # Redis connectivity check
    try:
        if hasattr(settings, 'CACHES') and 'default' in settings.CACHES:
            r = redis.Redis.from_url(settings.CACHES['default']['LOCATION'])
            r.ping()
            health_status['checks']['redis'] = 'ok'
        else:
            health_status['checks']['redis'] = 'not configured'
    except Exception as e:
        health_status['checks']['redis'] = f'error: {str(e)}'
        # Redis is not critical, so don't mark as unhealthy
    
    # Storage check
    try:
        import os
        storage_path = getattr(settings, 'MEDIA_ROOT', '/tmp')
        if os.path.exists(storage_path) and os.access(storage_path, os.W_OK):
            health_status['checks']['storage'] = 'ok'
        else:
            health_status['checks']['storage'] = 'path not writable'
            overall_healthy = False
    except Exception as e:
        health_status['checks']['storage'] = f'error: {str(e)}'
        overall_healthy = False
    
    # Set overall status
    if not overall_healthy:
        health_status['status'] = 'unhealthy'
    
    # Response time
    health_status['response_time_ms'] = round((time.time() - start_time) * 1000, 2)
    
    # Return appropriate HTTP status
    status_code = 200 if overall_healthy else 503
    return Response(health_status, status=status_code)


@api_view(['GET'])
@permission_classes([AllowAny])
def ready_check(request):
    """
    Readiness check - are we ready to serve traffic?
    """
    checks = {}
    ready = True
    
    # Check if migrations are applied
    try:
        from django.db.migrations.executor import MigrationExecutor
        executor = MigrationExecutor(connection)
        plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
        
        if plan:
            checks['migrations'] = f'error: {len(plan)} pending migrations'
            ready = False
        else:
            checks['migrations'] = 'ok'
    except Exception as e:
        checks['migrations'] = f'error: {str(e)}'
        ready = False
    
    # Check database connectivity
    try:
        connection.ensure_connection()
        checks['database'] = 'ok'
    except Exception as e:
        checks['database'] = f'error: {str(e)}'
        ready = False
    
    response_data = {
        'ready': ready,
        'checks': checks,
        'timestamp': int(time.time())
    }
    
    status_code = 200 if ready else 503
    return Response(response_data, status=status_code)


@api_view(['GET'])
@permission_classes([AllowAny])
def system_status(request):
    """
    Detailed system status with metrics.
    """
    from django.contrib.auth import get_user_model
    from apps.images.models import Image
    from apps.albums.models import Album
    
    User = get_user_model()
    
    status = {
        'service': 'PhotoVault Django API',
        'version': '1.0.0',
        'timestamp': int(time.time()),
        'database': {},
        'application': {},
        'system': {}
    }
    
    try:
        # Database metrics
        with connection.cursor() as cursor:
            cursor.execute("SELECT version()")
            db_version = cursor.fetchone()[0]
            status['database']['version'] = db_version
            
            # Check pgvector
            cursor.execute("SELECT extversion FROM pg_extension WHERE extname = 'vector'")
            vector_result = cursor.fetchone()
            status['database']['pgvector_version'] = vector_result[0] if vector_result else 'not installed'
        
        # Application metrics
        status['application']['total_users'] = User.objects.count()
        status['application']['total_images'] = Image.objects.count()
        status['application']['total_albums'] = Album.objects.count()
        
        # System info
        import platform
        status['system']['python_version'] = platform.python_version()
        status['system']['platform'] = platform.platform()
        
    except Exception as e:
        status['error'] = str(e)
    
    return Response(status)