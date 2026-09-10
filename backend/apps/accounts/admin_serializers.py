"""Serializers for the Admin IT user-administration module.

The brief scopes Admin IT to "hanya mengelola sistem" and explicitly bars the
role from clinical judgement, so this module touches accounts and nothing else.

Passwords are never set here. An administrator can force a change at next
sign-in, but never chooses, sees, or transmits a password on another user's
behalf.
"""

from __future__ import annotations

from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.core.privacy import MaskedIPField

from .models import Role, RoleSlug

User = get_user_model()


class AdminUserSerializer(serializers.ModelSerializer):
    roles = serializers.SerializerMethodField()
    last_login_ip = MaskedIPField()

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "full_name",
            "nip",
            "institution",
            "roles",
            "is_active",
            "must_change_password",
            "date_joined",
            "last_login",
            "last_login_ip",
        ]
        read_only_fields = fields

    def get_roles(self, obj: User) -> list[str]:
        return sorted(obj.role_slugs)


class AdminUserUpdateSerializer(serializers.Serializer):
    """Partial update of the two things an administrator may change."""

    is_active = serializers.BooleanField(required=False)
    roles = serializers.ListField(
        child=serializers.ChoiceField(choices=RoleSlug.choices),
        required=False,
        allow_empty=True,
    )

    def validate_roles(self, value: list[str]) -> list[str]:
        unique = sorted(set(value))
        known = set(Role.objects.filter(slug__in=unique).values_list("slug", flat=True))
        missing = [s for s in unique if s not in known]
        if missing:
            raise serializers.ValidationError(
                f"Role belum terdaftar di sistem: {', '.join(missing)}."
            )
        return unique

    def validate(self, attrs: dict) -> dict:
        if not attrs:
            raise serializers.ValidationError(
                "Tidak ada perubahan. Sertakan 'is_active' dan/atau 'roles'."
            )

        target = self.context["target"]
        actor = self.context["actor"]

        # Locking the last administrator out of the system is unrecoverable
        # without database access, so an administrator cannot demote or disable
        # their own account.
        if target.pk == actor.pk:
            if attrs.get("is_active") is False:
                raise serializers.ValidationError(
                    {"is_active": "Anda tidak dapat menonaktifkan akun Anda sendiri."}
                )
            if "roles" in attrs and RoleSlug.ADMIN_IT not in attrs["roles"]:
                raise serializers.ValidationError(
                    {"roles": "Anda tidak dapat melepas peran Admin IT dari akun Anda sendiri."}
                )
        return attrs
