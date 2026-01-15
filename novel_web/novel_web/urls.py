"""URL configuration for novel_web project."""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from django.views.generic import RedirectView
from django.views.i18n import set_language
from novels.health_views import health_check, health_detailed, readiness_check, liveness_check

urlpatterns = [
    # Language switcher (outside i18n_patterns)
    path('i18n/setlang/', set_language, name='set_language'),

    # Health check endpoints (outside i18n_patterns)
    path('health/', health_check, name='health'),
    path('health/detailed/', health_detailed, name='health_detailed'),
    path('readiness/', readiness_check, name='readiness'),
    path('liveness/', liveness_check, name='liveness'),

    # API endpoints (outside i18n_patterns - APIs should be language-agnostic)
    path('api/', include('novels.api_urls')),
]

# Add i18n patterns for main application (web pages only)
urlpatterns += i18n_patterns(
    path('admin/', admin.site.urls),
    path('', include('novels.urls')),
)

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
