"""In-app notification and SMS serializers.

``SmsLogSerializer`` is imported by ``apps/issues/serializers.py`` to embed the issue's
SMS thread in the detail payload — this module only imports issue *models*, so there is
no circular import.
"""
from rest_framework import serializers

from apps.issues.models import Issue
from apps.localities.models import Ward

from .models import Notification, SMSLog


class NotificationSerializer(serializers.ModelSerializer):
    related_issue_ref = serializers.SerializerMethodField()
    related_citizen_ref = serializers.SerializerMethodField()
    target = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = (
            "id",
            "message",
            "is_read",
            "created_at",
            "related_issue",
            "related_issue_ref",
            "related_citizen",
            "related_citizen_ref",
            "target",
        )

    def get_related_issue_ref(self, obj):
        return obj.related_issue.reference_no if obj.related_issue_id else None

    def get_related_citizen_ref(self, obj):
        return obj.related_citizen.citizen_id if obj.related_citizen_id else None

    def get_target(self, obj):
        """Deep-link target, mirroring the bell dropdown in partials/navbar.html."""
        if obj.related_issue_id:
            return {"type": "issue", "id": obj.related_issue_id}
        if obj.related_citizen_id:
            return {"type": "citizen", "id": obj.related_citizen_id}
        return {"type": "inbox", "id": None}


class SmsLogSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    direction_display = serializers.CharField(source="get_direction_display", read_only=True)
    logged_by_name = serializers.SerializerMethodField()
    issue_ref = serializers.SerializerMethodField()

    class Meta:
        model = SMSLog
        fields = (
            "id",
            "recipient",
            "message_body",
            "status",
            "status_display",
            "provider",
            "reference_id",
            "error_message",
            "sent_at",
            "created_at",
            "direction",
            "direction_display",
            "issue",
            "issue_ref",
            "logged_by",
            "logged_by_name",
        )

    def get_logged_by_name(self, obj):
        if not obj.logged_by_id:
            return None
        return obj.logged_by.get_full_name() or obj.logged_by.username

    def get_issue_ref(self, obj):
        return obj.issue.reference_no if obj.issue_id else None


class ComposeSmsSerializer(serializers.Serializer):
    """One-off SMS (``ComposeSMSForm``)."""

    recipient = serializers.CharField(max_length=30)
    message_body = serializers.CharField()
    issue = serializers.PrimaryKeyRelatedField(
        queryset=Issue.objects.all(), required=False, allow_null=True
    )


class BroadcastSmsSerializer(serializers.Serializer):
    """Ward broadcast (``BroadcastSMSForm``); ward blank = all approved citizens."""

    ward = serializers.PrimaryKeyRelatedField(
        queryset=Ward.objects.all(), required=False, allow_null=True
    )
    message_body = serializers.CharField()


class LogIncomingSmsSerializer(serializers.Serializer):
    """Staff-relayed inbound SMS (``LogIncomingSMSForm``) — citizen phones/texts the office."""

    sender_phone = serializers.CharField(max_length=30)
    message_body = serializers.CharField()
    issue = serializers.PrimaryKeyRelatedField(
        queryset=Issue.objects.all(), required=False, allow_null=True
    )
    send_reply = serializers.BooleanField(required=False, default=False)
    reply_body = serializers.CharField(required=False, allow_blank=True, default="")

    def validate(self, attrs):
        if attrs.get("send_reply") and not (attrs.get("reply_body") or "").strip():
            raise serializers.ValidationError(
                {"reply_body": "A reply message is required when sending a reply."}
            )
        return attrs