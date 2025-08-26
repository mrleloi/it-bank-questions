"""
ASGI config for core project with proper FastAPI integration.
"""

import os
from django.core.asgi import get_asgi_application
from starlette.applications import Starlette
from starlette.routing import Mount

# Set Django settings FIRST
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.development')

# Initialize Django ASGI application early
django_asgi_app = get_asgi_application()

# Now import FastAPI after Django is properly initialized
from interfaces.api.main import app as fastapi_app

# Create the combined application
application = Starlette(routes=[
    Mount("/api/v1", fastapi_app),
    Mount("/", django_asgi_app),
])