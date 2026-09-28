"""Issue serializers — service requests, technician scheduling, comments and feedback.

Field sets mirror the Django forms (``apps/issues/forms.py``) so the SPA can never post
server-managed fields such as ``reference_no``, ``status`` (on create) or ``rating``.
"""
from rest_framework import serializers

from apps.citizens.models import Citizen
from apps.localities.models import Ward
from apps.notifications.serializers import SmsLogSerializer

from .models import Issue, IssueComment


def is_staff_user(user):
    """True for ADMIN/OFFICER (or Django staff) — mirrors ``User.is_officer``."""
    if not (user and user.is_authenticated):
        return False
    return bool(user.is_superuser or user.is_staff or user.role in {"ADMIN", "OFFICER"})


class IssueCommentSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()
    author_role = serializers.SerializerMethodField()

    class Meta:
        model = IssueComment
        fields = (
            "id",
            "issue",
            "author",
            "author_name",
            "author_role",
            "body",
            "is_internal",
            "created_at",
        )
        read_only_fields = ("issue", "author", "created_at")

    def get_author_name(self, obj):
        if not obj.author_id:
            return "System"
        return obj.author.get_full_name() or obj.author.username

    def get_author_role(self, obj):
        return obj.author.role if obj.author_id else None

    def validate_is_internal(self, value):
        # A citizen must not be able to flag a comment as ward-internal.
        request = self.context.get("request")
        if value and not is_staff_user(getattr(request, "user", None)):
            raise serializers.ValidationError(
                "Only ward staff can mark a comment as internal."
            )
        return value


class IssueListSerializer(serializers.ModelSerializer):
    """Row representation used by the issue tables and dashboard panels."""

    category_display = serializers.CharField(source="get_category_display", read_only=True)
    priority_display = serializers.CharField(source="get_priority_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    ward_name = serializers.CharField(source="ward.name", read_only=True)
    citizen_name = serializers.CharField(source="citizen.full_name", read_only=True)
    citizen_ref = serializers.CharField(source="citizen.citizen_id", read_only=True)
    assigned_officer_name = serializers.SerializerMethodField()

    class Meta:
        model = Issue
        fields = (
            "id",
            "reference_no",
            "title",
            "category",
            "category_display",
            "priority",
            "priority_display",
            "status",
            "status_display",
            "ward",
            "ward_name",
            "citizen",
            "citizen_name",
            "citizen_ref",
            "assigned_officer",
            "assigned_officer_name",
            "assigned_technician_name",
            "appointment_at",
            "escalated_to_district",
            "rating",
            "created_at",
            "updated_at",
        )

    def get_assigned_officer_name(self, obj):
        if not obj.assigned_officer_id:
            return None
        officer = obj.assigned_officer
        return officer.get_full_name() or officer.username


class IssueDetailSerializer(IssueListSerializer):
    """Full detail payload: description, threaded comments, the SMS thread and feedback.

    ``internal_notes`` and internal comments are staff-only; ``can_rate`` tells the citizen
    portal whether the 1–5 star feedback form should be shown.
    """

    comments = serializers.SerializerMethodField()
    sms_thread = serializers.SerializerMethodField()
    internal_notes = serializers.SerializerMethodField()
    can_rate = serializers.SerializerMethodField()

    class Meta(IssueListSerializer.Meta):
        fields = IssueListSerializer.Meta.fields + (
            "description",
            "internal_notes",
            "feedback_comment",
            "closed_at",
            "comments",
            "sms_thread",
            "can_rate",
        )

    def _is_staff(self):
        request = self.context.get("request")
        return is_staff_user(getattr(request, "user", None))

    def get_comments(self, obj):
        qs = obj.comments.select_related("author")
        if not self._is_staff():
            qs = qs.filter(is_internal=False)
        return IssueCommentSerializer(qs, many=True, context=self.context).data

    def get_sms_thread(self, obj):
        qs = obj.sms_logs.select_related("logged_by").order_by("created_at")
        return SmsLogSerializer(qs, many=True, context=self.context).data

    def get_internal_notes(self, obj):
        # Ward notes must never leak to the reporting citizen.
        return obj.internal_notes if self._is_staff() else ""

    def get_can_rate(self, obj):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if not (user and user.is_authenticated):
            return False
        return bool(
            obj.status == Issue.Status.RESOLVED
            and obj.rating is None
            and obj.citizen.user_id == user.id
        )


class IssueCreateSerializer(serializers.ModelSerializer):
    """POST /api/v1/issues/ — mirrors IssueForm (status/reference_no/officer excluded)."""

    # Optional on purpose: for a citizen the server fills these from their own profile,
    # so a client can never file a request against somebody else's citizen/ward.
    citizen = serializers.PrimaryKeyRelatedField(
        queryset=Citizen.objects.all(), required=False
    )
    ward = serializers.PrimaryKeyRelatedField(queryset=Ward.objects.all(), required=False)

    class Meta:
        model = Issue
        fields = ("id", "title", "description", "category", "priority", "citizen", "ward")

    def validate(self, attrs):
        request = self.context.get("request")
        user = getattr(request, "user", None)

        if user is not None and user.is_authenticated and user.role == "CITIZEN":
            profile = getattr(user, "citizen_profile", None)
            if profile is None or profile.status != Citizen.Status.APPROVED:
                # Same guard as IssueCreateView.dispatch.
                raise serializers.ValidationError(
                    "Only approved citizens can file a service request."
                )
            attrs["citizen"] = profile
            attrs["ward"] = profile.ward
            return attrs

        if attrs.get("citizen") is None or attrs.get("ward") is None:
            raise serializers.ValidationError(
                {"citizen": "A citizen and ward are required for staff-filed requests."}
            )
        return attrs


class IssueUpdateSerializer(serializers.ModelSerializer):
    """PATCH /api/v1/issues/{id}/ — mirrors IssueStatusForm's fields.

    Technician name + appointment date/time is what triggers the appointment SMS to the
    citizen (apps/issues/signals.py), so updates must go through the model, not .update().
    """

    class Meta:
        model = Issue
        fields = (
            "status",
            "assigned_officer",
            "assigned_technician_name",
            "appointment_at",
            "internal_notes",
            "escalated_to_district",
        )


class IssueFeedbackSerializer(serializers.ModelSerializer):
    """Citizen rating for a RESOLVED issue. The 1–5 range comes from the model validators."""

    class Meta:
        model = Issue
        fields = ("rating", "feedback_comment")
        extra_kwargs = {"rating": {"required": True}}