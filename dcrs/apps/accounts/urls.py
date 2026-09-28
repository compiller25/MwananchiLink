from django.urls import path

from .views import OfficerLoginPageView, OfficerLogoutView, OfficerPasswordResetView, OTPVerifyView

app_name = "accounts"

urlpatterns = [
    path("login/", OfficerLoginPageView.as_view(), name="login"),
    path("logout/", OfficerLogoutView.as_view(), name="logout"),
    path("otp-verify/", OTPVerifyView.as_view(), name="otp_verify"),
    path("password-reset/", OfficerPasswordResetView.as_view(), name="password_reset"),
]
