"""Capture request metadata (IP, user-agent) so signal handlers can read it.

Pairs with django-crum (already installed) which exposes current request/user
via thread locals. This middleware just ensures CRUM is active and adds a
helper for extracting client IP behind proxies.
"""

from __future__ import annotations

from typing import Callable

from django.http import HttpRequest, HttpResponse


def client_ip(request: HttpRequest | None) -> str | None:
    if request is None:
        return None
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


class RequestContextMiddleware:
    """Lightweight pass-through. CRUM does the heavy lifting; this just
    documents the contract that audit signals expect CRUM to be installed
    above us in the middleware chain.
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        return self.get_response(request)
