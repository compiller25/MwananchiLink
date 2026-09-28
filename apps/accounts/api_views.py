"""Auth endpoints for the SPA.

Session-cookie auth: ``POST /api/v1/auth/login/`` starts the same Django session the
templates use, so ``UsernameOrPhoneBackend`` (username *or* phone), roles, ward scoping
and the 30-minute idle timeout all behave exactly as before. Because DRF's
``SessionAuthentication`` enforces CSRF on unsafe methods, the SPA first calls
``GET /api/v1/auth/csrf/`` to receive the ``csrftoken`` cookie and then echoes it in the
``X-CSRFToken`` header.
"""
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import (
    LoginSerializer,
    OtpVerifySerializer,
    PasswordResetSerializer,
    UserSerializer,
)


def post_login_redirect(user):
    """Mirrors OfficerLoginPageView.get_success_url: citizens → portal, staff → dashboard."""
    if user.role == user.Role.CITIZEN:
        return "/portal/"
    return "/app/dashboard"


@method_decorator(ensure_csrf_cookie, name="get")
class CsrfBootstrapView(APIView):
    """GET /api/v1/auth/csrf/ — sets the csrftoken cookie for the SPA."""

    permission_classes = [AllowAny]
    authentication_classes = []

    @extend_schema(responses={200: OpenApiResponse(description="CSRF cookie set")})
    def get(self, request):
        return Response({"detail": "CSRF cookie set."})


class LoginView(APIView):
    """POST /api/v1/auth/login/ — username or phone number + password."""

    permission_classes = [AllowAny]
    serializer_class = LoginSerializer

    @extend_schema(
        request=LoginSerializer,
        responses={200: UserSerializer},
        description="Sign in. Returns the user profile and the post-login redirect target.",
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        auth_login(request, user)
        return Response(
            {
                "user": UserSerializer(user, context={"request": request}).data,
                "redirect": post_login_redirect(user),
                "detail": "Signed in.",
            }
        )


class LogoutView(APIView):
    """POST /api/v1/auth/logout/ — ends the session."""

    permission_classes = [AllowAny]

    @extend_schema(request=None, responses={204: OpenApiResponse(description="Signed out")})
    def post(self, request):
        auth_logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    """GET /api/v1/auth/me/ — the current user (replaces the notifications context processor)."""

    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: UserSerializer})
    def get(self, request):
        return Response(UserSerializer(request.user, context={"request": request}).data)


class PasswordResetView(APIView):
    """POST /api/v1/auth/password-reset/ — emails a reset link (console backend in dev)."""

    permission_classes = [AllowAny]
    serializer_class = PasswordResetSerializer

    @extend_schema(request=PasswordResetSerializer, responses={200: OpenApiResponse(description="Email sent")})
    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        # Always the same response, so the endpoint cannot be used to probe for accounts.
        return Response(
            {"detail": "If that email is registered, a reset link has been sent."}
        )


class OtpVerifyView(APIView):
    """POST /api/v1/auth/otp-verify/ — NOT IMPLEMENTED.

    ``OfficerLoginPageView``/``OTPVerifyView`` in the templates is a stub too: there is no
    OTP field on ``User``, no code generation, and no verification backend. This endpoint is
    deliberately a 501 so the SPA does not fake a security check.
    """

    permission_classes = [AllowAny]
    serializer_class = OtpVerifySerializer

    @extend_schema(
        request=OtpVerifySerializer,
        responses={501: OpenApiResponse(description="OTP verification is not implemented")},
    )
    def post(self, request):
        serializer = OtpVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(
            {
                "detail": (
                    "OTP verification is not implemented in DCRS yet — accounts are secured "
                    "by the standard password sign-in."
                )
            },
            status=status.HTTP_501_NOT_IMPLEMENTED,
        )