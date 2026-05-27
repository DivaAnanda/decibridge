from __future__ import annotations

from django.contrib.auth import password_validation
from django.contrib.auth.signals import user_logged_in
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import Role, User


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ["slug", "display_name_id", "display_name_en", "description"]


class UserSerializer(serializers.ModelSerializer):
    roles = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "full_name",
            "nip",
            "institution",
            "is_active",
            "is_staff",
            "is_superuser",
            "date_joined",
            "last_login",
            "roles",
        ]
        read_only_fields = ["id", "date_joined", "last_login", "is_superuser"]

    def get_roles(self, obj: User) -> list[dict]:
        roles = Role.objects.filter(group__user=obj)
        return RoleSerializer(roles, many=True).data


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)

    def validate_current_password(self, value: str) -> str:
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value

    def validate_new_password(self, value: str) -> str:
        password_validation.validate_password(value, self.context["request"].user)
        return value

    def save(self, **kwargs) -> User:
        user: User = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save(update_fields=["password"])
        return user


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class DeciBridgeTokenObtainPairSerializer(TokenObtainPairSerializer):
    """JWT login response includes a serialized user payload alongside the tokens.

    Also fires Django's `user_logged_in` signal so the audit hook records the
    login. SimpleJWT does not fire this signal by default because it bypasses
    Django's `login()` helper.
    """

    def validate(self, attrs: dict) -> dict:
        data = super().validate(attrs)
        request = self.context.get("request")
        user_logged_in.send(sender=self.user.__class__, request=request, user=self.user)
        data["user"] = UserSerializer(self.user).data
        return data
