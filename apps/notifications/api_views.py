"""Notification inbox and SMS endpoints for the SPA.

Sending goes through ``apps.notifications.services`` (``send_sms`` / ``broadcast_sms``), so
the SendAfrica real-API/simulator switch and the SMS log behave exactly as they did for the
templates. The delivery webhook is deliberately NOT re-implemented here — see
``sms_api_urls.py``.
"""
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.drf_permissions import IsOfficerOrAdmin
from apps.accounts.pagination import NotificationPagination, SmsLogPagination
from apps.citizens.models import Citizen

from .models import Notification, SMSLog
from .serializers import (
    BroadcastSmsSerializer,
    ComposeSmsSerializer,
    LogIncomingSmsSerializer,
    NotificationSerializer,
    SmsLogSerializer,
)
from .services import broadcast_sms, send_sms


class NotificationListView(ListAPIView):
    """GET /api/v1/notifications/ — the full inbox (own notifications only)."""

    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer
    pagination_class = NotificationPagination

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user).select_related(
            "related_issue", "related_citizen"
        )


class UnreadNotificationsView(APIView):
    """GET /api/v1/notifications/unread/ — bell badge: unread count + latest 6.

    Mirrors ``apps.notifications.context_processors.notifications``.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Notification.objects.filter(recipient=request.user, is_read=False).select_related(
            "related_issue", "related_citizen"
        )
        return Response(
            {
                "count": qs.count(),
                "results": NotificationSerializer(
                    qs[:6], many=True, context={"request": request}
                ).data,
            }
        )


class NotificationMarkReadView(APIView):
    """POST /api/v1/notifications/{pk}/read/"""

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        updated = Notification.objects.filter(recipient=request.user, pk=pk).update(
            is_read=True
        )
        if not updated:
            return Response(
                {"detail": "Notification not found."}, status=status.HTTP_404_NOT_FOUND
            )
        return Response({"detail": "Marked as read."})


class NotificationMarkAllReadView(APIView):
    """POST /api/v1/notifications/read-all/"""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        count = Notification.objects.filter(recipient=request.user, is_read=False).update(
            is_read=True
        )
        return Response(
            {"detail": f"{count} notification(s) marked as read.", "count": count}
        )


class SmsLogListView(ListAPIView):
    """GET /api/v1/sms/log/ — delivery history plus the status tallies the page showed."""

    permission_classes = [IsOfficerOrAdmin]
    serializer_class = SmsLogSerializer
    pagination_class = SmsLogPagination
    queryset = SMSLog.objects.select_related("issue", "logged_by")

    def get_queryset(self):
        qs = super().get_queryset()
        status_value = self.request.query_params.get("status")
        direction = self.request.query_params.get("direction")
        if status_value:
            qs = qs.filter(status=status_value)
        if direction:
            qs = qs.filter(direction=direction)
        return qs

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        response.data["counts"] = {
            "delivered": SMSLog.objects.filter(status=SMSLog.Status.DELIVERED).count(),
            "sent": SMSLog.objects.filter(status=SMSLog.Status.SENT).count(),
            "failed": SMSLog.objects.filter(status=SMSLog.Status.FAILED).count(),
            "queued": SMSLog.objects.filter(status=SMSLog.Status.QUEUED).count(),
            "total": SMSLog.objects.count(),
        }
        return response


class ComposeSmsView(APIView):
    """POST /api/v1/sms/compose/ — one-off SMS, optionally attached to an issue thread."""

    permission_classes = [IsOfficerOrAdmin]

    def post(self, request):
        serializer = ComposeSmsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        log = send_sms(data["recipient"], data["message_body"])
        issue = data.get("issue")
        if issue is not None:
            # .update() is safe: SMSLog emits no signals (unlike Citizen/Issue).
            SMSLog.objects.filter(pk=log.pk).update(issue=issue)
            log.issue = issue
        return Response(
            {
                "detail": f"SMS {log.get_status_display().lower()} to {log.recipient}.",
                "log": SmsLogSerializer(log, context={"request": request}).data,
            },
            status=status.HTTP_201_CREATED,
        )


class BroadcastSmsView(APIView):
    """POST /api/v1/sms/broadcast/ — an officer is always forced onto their own ward."""

    permission_classes = [IsOfficerOrAdmin]

    def post(self, request):
        serializer = BroadcastSmsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        ward = serializer.validated_data.get("ward")
        if user.role == "OFFICER" and not user.is_superuser:
            ward = user.ward  # parity with BroadcastSMSView._target_ward
        citizens = Citizen.objects.filter(status=Citizen.Status.APPROVED)
        if ward is not None:
            citizens = citizens.filter(ward=ward)
        recipients = list(citizens.values_list("phone_number", flat=True))
        broadcast_sms(recipients, serializer.validated_data["message_body"])
        return Response(
            {
                "detail": f"Broadcast sent to {len(recipients)} approved citizen(s).",
                "recipients": len(recipients),
            }
        )


class LogIncomingSmsView(APIView):
    """POST /api/v1/sms/log-incoming/ — staff-relayed inbound SMS, with an optional reply."""

    permission_classes = [IsOfficerOrAdmin]

    def post(self, request):
        serializer = LogIncomingSmsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        issue = data.get("issue")
        log = SMSLog.objects.create(
            recipient=data["sender_phone"],
            message_body=data["message_body"],
            status=SMSLog.Status.SENT,
            provider="Staff-logged (phone)",
            direction=SMSLog.Direction.INBOUND,
            issue=issue,
            logged_by=request.user,
        )
        reply_log = None
        if data.get("send_reply"):
            reply_log = send_sms(data["sender_phone"], data["reply_body"])
            if issue is not None:
                SMSLog.objects.filter(pk=reply_log.pk).update(issue=issue)
                reply_log.issue = issue
        return Response(
            {
                "detail": "Incoming SMS logged.",
                "log": SmsLogSerializer(log, context={"request": request}).data,
                "reply": (
                    SmsLogSerializer(reply_log, context={"request": request}).data
                    if reply_log
                    else None
                ),
            },
            status=status.HTTP_201_CREATED,
        )