from django.urls import path

from .api_views import (
    CsrfBootstrapView,
    LoginView,
    LogoutView,
    MeView,
    OtpVerifyView,
    PasswordResetView,
)

app_name = "accounts_api"

urlpatterns = [
    path("csrf/", CsrfBootstrapView.as_view(), name="csrf"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("me/", MeView.as_view(), name="me"),
    path("password-reset/", PasswordResetView.as_view(), name="password_reset"),
    path("otp-verify/", OtpVerifyView.as_view(), name="otp_verify"),
]