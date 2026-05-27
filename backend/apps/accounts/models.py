from __future__ import annotations

from django.contrib.auth.models import AbstractBaseUser, Group, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .managers import UserManager


class RoleSlug(models.TextChoices):
    """Canonical role slugs. Keep stable — referenced by permission classes and migrations."""

    ADMIN_IT = "admin_it", _("Admin IT")
    HTA_ANALYST = "hta_analyst", _("HTA Analyst / Farmakoekonomi")
    FARMASI_SEKRETARIS = "farmasi_sekretaris", _("Farmasi RS / Sekretaris KFT")
    KFT_MEMBER = "kft_member", _("Anggota KFT")
    KETUA_KFT = "ketua_kft", _("Ketua KFT / Approver")


class Role(models.Model):
    """Wrapper around Django Group adding display metadata.

    The underlying Group carries permissions; Role adds Indonesian display
    names and a stable slug for code references.
    """

    slug = models.CharField(max_length=64, unique=True, choices=RoleSlug.choices)
    display_name_id = models.CharField(_("Indonesian display name"), max_length=120)
    display_name_en = models.CharField(_("English display name"), max_length=120)
    description = models.TextField(blank=True, default="")
    group = models.OneToOneField(Group, on_delete=models.CASCADE, related_name="role")
    created_at = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        ordering = ["slug"]
        verbose_name = _("Role")
        verbose_name_plural = _("Roles")

    def __str__(self) -> str:
        return self.display_name_id


class User(AbstractBaseUser, PermissionsMixin):
    """Email-based custom user.

    Why custom: the brief separates Admin IT from clinical roles; a single
    email-as-identifier model is simpler than Django's default
    username+email pair, and starting custom lets future sprints add fields
    (NIP, institutional affiliation) without painful migrations.
    """

    email = models.EmailField(_("email address"), unique=True)
    full_name = models.CharField(_("full name"), max_length=180)
    nip = models.CharField(
        _("NIP / staff ID"),
        max_length=32,
        blank=True,
        default="",
        help_text=_("Indonesian government / hospital staff identifier"),
    )
    institution = models.CharField(_("institution"), max_length=180, blank=True, default="")
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False, help_text=_("Can access Django admin"))
    date_joined = models.DateTimeField(default=timezone.now)
    last_login_ip = models.GenericIPAddressField(blank=True, null=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name"]

    objects = UserManager()

    class Meta:
        ordering = ["email"]
        verbose_name = _("User")
        verbose_name_plural = _("Users")

    def __str__(self) -> str:
        return f"{self.full_name} <{self.email}>"

    def get_full_name(self) -> str:
        return self.full_name

    def get_short_name(self) -> str:
        return self.full_name.split(" ", 1)[0] if self.full_name else self.email

    @property
    def role_slugs(self) -> list[str]:
        return list(self.groups.filter(role__isnull=False).values_list("role__slug", flat=True))

    def has_role(self, slug: str) -> bool:
        return self.groups.filter(role__slug=slug).exists()
