from django.db import DatabaseError, connection
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
