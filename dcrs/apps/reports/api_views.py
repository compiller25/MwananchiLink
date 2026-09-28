"""Report endpoints: dashboard, registration report, audit trail and the public counters.

Each mirrors the context its template view used to build, so the SPA dashboard shows the
same numbers as ``templates/reports/dashboard.html``.
"""
from django.utils import timezone
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.drf_permissions import IsOfficerOrAdmin
from apps.accounts.pagination import AuditLogPagination, DcrsPagination
from apps.citizens.models import Citizen
from apps.citizens.serializers import CitizenSerializer, PublicCitizenSerializer
from apps.issues.models import Issue
from apps.issues.serializers import IssueListSerializer
from apps.notifications.models import SMSLog

from .models import AuditLog
from .serializers import AuditLogSerializer


class DashboardView(APIView):
    """GET /api/v1/reports/dashboard/ — stat cards, recent lists and the activity feed."""

    permission_classes = [IsOfficerOrAdmin]

    def get(self, request):
        today = timezone.localdate()
        ctx = {"request": request}
        return Response(
            {
                "stats": {
                    "total_citizens": Citizen.objects.count(),
                    "pending_approvals": Citizen.objects.filter(
                        status=Citizen.Status.PENDING
                    ).count(),
                    "open_issues": Issue.objects.exclude(
                        status__in=[Issue.Status.RESOLVED, Issue.Status.CLOSED]
                    ).count(),
                    "sms_sent_today": SMSLog.objects.filter(
                        created_at__date=today, status=SMSLog.Status.SENT
                    ).count(),
                },
                "recent_citizens": CitizenSerializer(
                    Citizen.objects.select_related("ward", "district")[:5],
                    many=True,
                    context=ctx,
                ).data,
                "recent_issues": IssueListSerializer(
                    Issue.objects.select_related("citizen", "ward")[:5],
                    many=True,
                    context=ctx,
                ).data,
                "recent_activity": AuditLogSerializer(
                    AuditLog.objects.select_related("actor")[:8], many=True, context=ctx
                ).data,
            }
        )


class RegistrationReportView(ListAPIView):
    """GET /api/v1/reports/registration/?ward=&status= — registration report, paginated."""

    permission_classes = [IsOfficerOrAdmin]
    serializer_class = CitizenSerializer
    pagination_class = DcrsPagination

    def get_queryset(self):
        qs = Citizen.objects.select_related("ward", "district", "region")
        ward = self.request.query_params.get("ward")
        status_value = self.request.query_params.get("status")
        if ward:
            # Parity with RegistrationReportView: a case-insensitive name match, not an id.
            qs = qs.filter(ward__name__icontains=ward)
        if status_value:
            qs = qs.filter(status=status_value)
        return qs


class AuditLogView(ListAPIView):
    """GET /api/v1/reports/audit/ — every audited action, newest first."""

    permission_classes = [IsOfficerOrAdmin]
    serializer_class = AuditLogSerializer
    pagination_class = AuditLogPagination
    queryset = AuditLog.objects.select_related("actor")


class PublicStatsView(APIView):
    """GET /api/v1/public/stats/ — landing-page counters (no auth required).

    ``recent_citizens`` uses the slim PublicCitizenSerializer: the server-rendered landing
    page only ever printed the citizen id, name, ward and status, so the API must not hand
    out national IDs, phone numbers or photos to anonymous visitors.
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        return Response(
            {
                "total_citizens": Citizen.objects.count(),
                "pending_citizens": Citizen.objects.filter(
                    status=Citizen.Status.PENDING
                ).count(),
                "open_issues": Issue.objects.filter(
                    status__in=["OPEN", "IN_PROGRESS", "ESCALATED"]
                ).count(),
                "sms_logs": SMSLog.objects.count(),
                "recent_citizens": PublicCitizenSerializer(
                    Citizen.objects.select_related("ward", "district")[:4],
                    many=True,
                    context={"request": request},
                ).data,
            }
        )