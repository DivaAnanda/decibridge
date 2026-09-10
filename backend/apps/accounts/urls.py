from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .admin_views import (
    LoginHistoryView,
    UserAdminDetailView,
    UserAdminListView,
    UserForcePasswordResetView,
)
from .views import ChangePasswordView, LoginView, LogoutView, MeView

app_name = "accounts"

urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
    path("refresh/", TokenRefreshView.as_view(), name="refresh"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("me/", MeView.as_view(), name="me"),
    path("password/change/", ChangePasswordView.as_view(), name="password_change"),
    # Admin IT user administration (Round 3)
    path("admin/users/", UserAdminListView.as_view(), name="admin_user_list"),
    path("admin/users/<int:user_id>/", UserAdminDetailView.as_view(), name="admin_user_detail"),
    path(
        "admin/users/<int:user_id>/force-password-reset/",
        UserForcePasswordResetView.as_view(),
        name="admin_user_force_password_reset",
    ),
    path("admin/login-history/", LoginHistoryView.as_view(), name="admin_login_history"),
]
