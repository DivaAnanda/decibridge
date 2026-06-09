from pathlib import Path

from django.conf import settings
from django.db import DatabaseError, connection
from django.http import FileResponse, HttpResponse, HttpResponseNotFound
from django.views import View
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthView(APIView):
    """Liveness + readiness probe.

    Sprint 0 baseline: confirms Django boots and the DB connection answers.
    Later sprints will extend this with Redis/Celery checks.
    """

    permission_classes = (AllowAny,)
    authentication_classes: list = []

    def get(self, request: Request) -> Response:
        checks: dict[str, str] = {"django": "ok"}
        http_status = status.HTTP_200_OK

        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            checks["database"] = "ok"
        except DatabaseError as exc:
            checks["database"] = f"error: {exc}"
            http_status = status.HTTP_503_SERVICE_UNAVAILABLE

        return Response({"status": "ok" if http_status == 200 else "degraded", "checks": checks}, status=http_status)


class SPAFallbackView(View):
    """Serve the React build's index.html for any non-API route.

    In production the Dockerfile copies the Vite build output into
    `settings.FRONTEND_DIST`, which contains a single-page app. All client-side
    routes (`/`, `/login`, `/dashboard`, `/cases/HF_ARNI_ACEI_001`, etc.) need
    to receive the same `index.html` so React Router can take over.

    URL patterns in `decibridge/urls.py` mount this view AFTER /admin/ and
    /api/, so API + admin still resolve normally.

    In local dev, the React app runs on Vite's :5173 and this view typically
    only fires when someone hits the backend's bare host:port — useful for
    redirecting devs to the dev server.
    """

    def get(self, request, *args, **kwargs) -> HttpResponse:
        index_path: Path = settings.FRONTEND_DIST / "index.html"
        if not index_path.exists():
            return HttpResponseNotFound(
                "Frontend build not found. In production this means the "
                "Dockerfile didn't copy the React dist/ into FRONTEND_DIST. "
                "In dev, run `npm run dev` and open http://localhost:5173."
            )
        return FileResponse(open(index_path, "rb"), content_type="text/html")
