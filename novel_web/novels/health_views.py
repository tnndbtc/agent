"""
Health check views for monitoring and load balancing
"""
from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache
import redis
from django.conf import settings


def health_check(request):
    """
    Basic health check endpoint
    Returns 200 if service is up
    """
    return JsonResponse({
        'status': 'healthy',
        'service': 'novel-agent-web'
    })


def health_detailed(request):
    """
    Detailed health check including database and redis connectivity
    """
    health_status = {
        'status': 'healthy',
        'checks': {}
    }

    # Check database connection
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        health_status['checks']['database'] = 'healthy'
    except Exception as e:
        health_status['checks']['database'] = f'unhealthy: {str(e)}'
        health_status['status'] = 'unhealthy'

    # Check Redis connection
    try:
        cache.set('health_check', 'ok', 10)
        result = cache.get('health_check')
        if result == 'ok':
            health_status['checks']['redis'] = 'healthy'
        else:
            health_status['checks']['redis'] = 'unhealthy: cache test failed'
            health_status['status'] = 'unhealthy'
    except Exception as e:
        health_status['checks']['redis'] = f'unhealthy: {str(e)}'
        health_status['status'] = 'unhealthy'

    # Check Celery (basic check - just verify Redis broker is accessible)
    try:
        from novel_web.celery import app as celery_app
        inspect = celery_app.control.inspect()
        stats = inspect.stats()
        if stats:
            health_status['checks']['celery'] = 'healthy'
        else:
            health_status['checks']['celery'] = 'unhealthy: no workers responding'
            health_status['status'] = 'degraded'
    except Exception as e:
        health_status['checks']['celery'] = f'unhealthy: {str(e)}'
        health_status['status'] = 'degraded'

    status_code = 200 if health_status['status'] in ['healthy', 'degraded'] else 503
    return JsonResponse(health_status, status=status_code)


def readiness_check(request):
    """
    Kubernetes readiness probe
    Returns 200 when ready to serve traffic
    """
    try:
        # Check if migrations are applied
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM django_migrations")
            count = cursor.fetchone()[0]
            if count > 0:
                return JsonResponse({'status': 'ready'})
            else:
                return JsonResponse({'status': 'not ready', 'reason': 'migrations pending'}, status=503)
    except Exception as e:
        return JsonResponse({'status': 'not ready', 'reason': str(e)}, status=503)


def liveness_check(request):
    """
    Kubernetes liveness probe
    Returns 200 if application is alive (even if not fully functional)
    """
    return JsonResponse({'status': 'alive'})
