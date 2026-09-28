"""Citizen endpoints for the SPA.

Access model (deliberately tighter than the templates):
* list / detail / edit are **staff only** (``IsOfficerOrAdmin``) and ward-scoped for
  officers, so a citizen can no longer enumerate the register.
* a citizen reaches their own data through ``/citizens/me/`` and ``/citizens/{id}/status/``
  (``IsOwnerCitizenOrStaff``).
"""
from django.contrib.auth import login as auth_login
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.filters import SearchFilter
from rest_framework.generics import (
    CreateAPIView,
    ListAPIView,
    RetrieveAPIView,
    RetrieveUpdateDestroyAPIView,
)
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.drf_permissions import (
    IsOfficerOrAdmin,
    IsOwnerCitizenOrStaff,
    WardScopedQuerysetMixin,
    enforce_ward_access,
)
from apps.accounts.pagination import DcrsPagination
from apps.accounts.serializers import UserSerializer

from .models import Citizen
from .serializers import (
    CitizenDetailSerializer,
    CitizenRegistrationSerializer,
    CitizenSerializer,
    CitizenStatusSerializer,
    CitizenWriteSerializer,
    RejectionSerializer,
)


class CitizenRegistrationView(CreateAPIView):
    """POST /api/v1/citizens/register/ — self-registration (public, multipart).

    Replaces ``CitizenRegistrationView``: creates the Citizen + the linked User, signs the
    new citizen in, and returns the same "submitted" message the template showed.
    """

    permission_classes = [AllowAny]
    serializer_class = CitizenRegistrationSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    # SessionAuthentication is intentionally kept: it means this public POST is still
    # CSRF-protected, exactly like the template form was.

    @extend_schema(request=CitizenRegistrationSerializer, responses={201: CitizenSerializer})
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        citizen = serializer.save()

        auth_login(request, serializer.created_user)
        return Response(
            {
                "detail": (
                    "Registration submitted — you're logged in, and can track your "
                    "approval status here."
                ),
                "profile": CitizenSerializer(citizen, context={"request": request}).data,
                "user": UserSerializer(serializer.created_user, context={"request": request}).data,
                "redirect": "/portal/",
            },
            status=status.HTTP_201_CREATED,
        )


class CitizenListView(WardScopedQuerysetMixin, ListAPIView):
    """GET /api/v1/citizens/ — staff only; ward-scoped for officers.

    Query params: ``?status=``, ``?ward=``, ``?search=``, ``?page=``.
    """

    permission_classes = [IsOfficerOrAdmin]
    serializer_class = CitizenSerializer
    pagination_class = DcrsPagination
    filter_backends = [SearchFilter]
    search_fields = ("full_name", "phone_number", "citizen_id", "national_id")
    queryset = Citizen.objects.all()
    ward_lookup = "ward"

    def get_queryset(self):
        qs = super().get_queryset().select_related("region", "district", "ward", "mtaa")
        params = self.request.query_params
        status_value = params.get("status")
        if status_value:
            qs = qs.filter(status=status_value)
        ward = params.get("ward")
        if ward and str(ward).isdigit():
            qs = qs.filter(ward_id=int(ward))
        return qs


class CitizenDetailView(WardScopedQuerysetMixin, RetrieveUpdateDestroyAPIView):
    """GET / PATCH / DELETE /api/v1/citizens/{id}/ — staff only, ward-scoped.

    DELETE also replaces the broken delete flow in the templates: CitizenDeleteView
    references ``citizen_confirm_delete.html``, which does not exist in this repo.
    """

    permission_classes = [IsOfficerOrAdmin]
    queryset = Citizen.objects.all()
    ward_lookup = "ward"

    def get_queryset(self):
        return super().get_queryset().select_related("region", "district", "ward", "mtaa")

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return CitizenWriteSerializer
        return CitizenDetailSerializer

    def destroy(self, request, *args, **kwargs):
        citizen = self.get_object()
        detail = f"Citizen record for {citizen.full_name} has been deleted."
        response = super().destroy(request, *args, **kwargs)
        response.data = {"detail": detail}
        return response


class CitizenStatusView(RetrieveAPIView):
    """GET /api/v1/citizens/{id}/status/ — the citizen's status card (owner or staff)."""

    permission_classes = [IsOwnerCitizenOrStaff]
    serializer_class = CitizenStatusSerializer
    queryset = Citizen.objects.select_related("region", "district", "ward", "mtaa")


class CitizenActionMixin:
    """Shared fetch + ward guard for the approve/reject actions."""

    permission_classes = [IsOfficerOrAdmin]

    def get_citizen(self, pk):
        citizen = get_object_or_404(Citizen, pk=pk)
        enforce_ward_access(self.request, citizen)
        return citizen


class CitizenApproveView(CitizenActionMixin, APIView):
    """POST /api/v1/citizens/{id}/approve/ — sets APPROVED, clears any rejection reason."""

    @extend_schema(request=None, responses={200: CitizenSerializer})
    def post(self, request, pk):
        citizen = self.get_citizen(pk)
        citizen.status = Citizen.Status.APPROVED
        citizen.rejection_reason = ""
        # .save() (not .update()) so the signals fire the approval SMS, the citizen's web
        # notification, and the audit entry — exactly like CitizenApproveView did.
        citizen.save()
        return Response(
            {
                "detail": f"{citizen.full_name} has been approved.",
                "citizen": CitizenSerializer(citizen, context={"request": request}).data,
            }
        )


class CitizenRejectView(CitizenActionMixin, APIView):
    """POST /api/v1/citizens/{id}/reject/ — requires ``{"reason": "..."}``."""

    serializer_class = RejectionSerializer

    @extend_schema(request=RejectionSerializer, responses={200: CitizenSerializer})
    def post(self, request, pk):
        serializer = RejectionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        citizen = self.get_citizen(pk)
        citizen.status = Citizen.Status.REJECTED
        citizen.rejection_reason = serializer.validated_data["reason"]
        citizen.save()
        return Response(
            {
                "detail": f"{citizen.full_name}'s registration has been rejected.",
                "citizen": CitizenSerializer(citizen, context={"request": request}).data,
            }
        )


class CitizenMeView(APIView):
    """GET /api/v1/citizens/me/ — the citizen portal payload (``CitizenPortalView``)."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: OpenApiResponse(description="profile + my_issues + open_count")}
    )
    def get(self, request):
        from apps.issues.serializers import IssueListSerializer  # local: avoids a cycle

        profile = getattr(request.user, "citizen_profile", None)
        if profile is None:
            return Response({"profile": None, "my_issues": [], "open_count": 0})

        my_issues = profile.issues.order_by("-created_at")
        open_count = my_issues.exclude(status__in=["RESOLVED", "CLOSED"]).count()
        return Response(
            {
                "profile": CitizenSerializer(profile, context={"request": request}).data,
                "my_issues": IssueListSerializer(
                    my_issues[:10], many=True, context={"request": request}
                ).data,
                "open_count": open_count,
            }
        )