"""IP address masking for audit surfaces (Round 3).

Acceptance testing found the full client IP of every actor visible to the
Sekretariat account in the audit history:

    "Riwayat audit menampilkan alamat IP lengkap kepada akun Sekretariat. Akses
     terhadap informasi ini sebaiknya dibatasi atau IP disamarkan."

The brief records IP only conditionally ("IP/perangkat bila diperlukan"), so it
is kept for forensics but shown in full only to Admin IT, whose role the brief
defines as "hanya mengelola sistem". Everyone else sees a masked value, which is
still enough to tell two sessions apart.
"""

from __future__ import annotations

from rest_framework import serializers

from apps.accounts.models import RoleSlug

PRIVILEGED_ROLES = frozenset({RoleSlug.ADMIN_IT})
MASK_V4 = "xxx"
MASK_V6 = "xxxx"


def mask_ip(value: str | None) -> str | None:
    """Blank the host portion, keeping enough to distinguish sessions."""
    if not value:
        return value
    if ":" in value:
        parts = value.split(":")
        keep = max(len(parts) - 3, 1)
        return ":".join(parts[:keep] + [MASK_V6] * (len(parts) - keep))
    parts = value.split(".")
    if len(parts) != 4:
        return value
    return ".".join(parts[:3] + [MASK_V4])


def may_see_full_ip(user) -> bool:
    if user is None or not getattr(user, "is_authenticated", False):
        return False
    if getattr(user, "is_superuser", False):
        return True
    return bool(set(getattr(user, "role_slugs", [])) & PRIVILEGED_ROLES)


class MaskedIPField(serializers.Field):
    """Full IP for Admin IT, masked for everyone else.

    Fails closed: without a request in the serializer context (snapshot builders,
    management commands) the value is masked.
    """

    def __init__(self, **kwargs):
        kwargs.setdefault("read_only", True)
        super().__init__(**kwargs)

    def to_representation(self, value):
        request = self.context.get("request")
        user = getattr(request, "user", None) if request is not None else None
        return value if may_see_full_ip(user) else mask_ip(value)

    def get_attribute(self, instance):
        return getattr(instance, self.source or self.field_name, None)
