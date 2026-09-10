"""Admin IT user administration routes.

Mounted at /api/v1/admin/ rather than under the accounts app's /auth/ prefix:
these endpoints administer accounts, they are not part of authentication.
"""

from django.urls import path

from .admin_views import (
    LoginHistoryView,
    UserAdminDetailView,
    UserAdminListView,
    UserForcePasswordResetView,
)

app_name = "user_admin"

urlpatterns = [
    path("users/", UserAdminListView.as_view(), name="user_list"),
    path("users/<int:user_id>/", UserAdminDetailView.as_view(), name="user_detail"),
    path(
        "users/<int:user_id>/force-password-reset/",
        UserForcePasswordResetView.as_view(),
        name="user_force_password_reset",
    ),
    path("login-history/", LoginHistoryView.as_view(), name="login_history"),
]
