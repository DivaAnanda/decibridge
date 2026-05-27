"""ASGI entrypoint for async-capable servers (uvicorn, daphne)."""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "decibridge.settings")

application = get_asgi_application()
