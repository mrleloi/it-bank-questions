"""Core URL Configuration."""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Django REST Framework admin endpoints
    path('admin/api/', include('interfaces.rest.urls')),

    # Django admin
    path('admin/', admin.site.urls),

    # API v1 - FastAPI mounted via ASGI
    # FastAPI handles /api/v1/* routes

    # Health check
    # path('health/', include('health_check.urls')),
]

# Serve static files (bao gồm REST framework assets)
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    # Django Debug Toolbar (nếu có)
    try:
        import debug_toolbar
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns
    except ImportError:
        pass

# Production static files serving
if not settings.DEBUG:
    # Thêm whitenoise nếu cần
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)