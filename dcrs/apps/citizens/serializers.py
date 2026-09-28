"""Citizen serializers.

Validation mirrors the Django forms so the SPA renders the same messages the templates
did (see ``apps/citizens/forms.py``): unique username / phone / national ID, matching
passwords, and Django's password validators.
"""
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.db.models import Q
from rest_framework import serializers

from .models import Citizen

User = get_user_model()


class CitizenSerializer(serializers.ModelSerializer):
    """Read-only representation used by lists, detail and the portal."""

    region_name = serializers.CharField(source="region.name", read_only=True)
    district_name = serializers.CharField(source="district.name", read_only=True)
    ward_name = serializers.CharField(source="ward.name", read_only=True)
    mtaa_name = serializers.SerializerMethodField()
    gender_display = serializers.CharField(source="get_gender_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    has_login = serializers.SerializerMethodField()

    class Meta:
        model = Citizen
        fields = (
            "id",
            "citizen_id",
            "full_name",
            "national_id",
            "phone_number",
            "gender",
            "gender_display",
            "date_of_birth",
            "region",
            "region_name",
            "district",
            "district_name",
            "ward",
            "ward_name",
            "mtaa",
            "mtaa_name",
            "profile_photo",
            "registration_notes",
            "status",
            "status_display",
            "rejection_reason",
            "has_login",
            "created_at",
            "updated_at",
        )

    def get_mtaa_name(self, obj):
        return obj.mtaa.name if obj.mtaa_id else None

    def get_has_login(self, obj):
        return obj.user_id is not None


class CitizenIssueSummaryMixin:
    """Adds the ``recent_issues`` / ``open_issue_count`` fields the detail pages show.

    ``apps.issues.serializers`` is imported lazily inside the methods: the issues
    serializers describe citizens, so a module-level import here would be circular.
    """

    recent_issues_limit = 10

    def get_recent_issues(self, obj):
        from apps.issues.serializers import IssueListSerializer

        qs = obj.issues.select_related("ward", "citizen").order_by("-created_at")
        return IssueListSerializer(
            qs[: self.recent_issues_limit], many=True, context=self.context
        ).data

    def get_open_issue_count(self, obj):
        return obj.issues.exclude(status__in=["RESOLVED", "CLOSED"]).count()


class CitizenDetailSerializer(CitizenIssueSummaryMixin, CitizenSerializer):
    """Detail payload — mirrors CitizenDetailView's ``citizen_issues`` context (last 10)."""

    recent_issues = serializers.SerializerMethodField()
    open_issue_count = serializers.SerializerMethodField()

    class Meta(CitizenSerializer.Meta):
        fields = CitizenSerializer.Meta.fields + ("recent_issues", "open_issue_count")


class CitizenStatusSerializer(CitizenIssueSummaryMixin, CitizenSerializer):
    """Status card payload — mirrors CitizenStatusView (5 most recent issues)."""

    recent_issues_limit = 5
    recent_issues = serializers.SerializerMethodField()
    open_issue_count = serializers.SerializerMethodField()

    class Meta(CitizenSerializer.Meta):
        fields = CitizenSerializer.Meta.fields + ("recent_issues", "open_issue_count")


class CitizenWriteSerializer(serializers.ModelSerializer):
    """PATCH payload — exactly the fields CitizenEditForm exposes."""

    class Meta:
        model = Citizen
        fields = (
            "full_name",
            "national_id",
            "phone_number",
            "gender",
            "date_of_birth",
            "region",
            "district",
            "ward",
            "mtaa",
            "profile_photo",
            "registration_notes",
        )


class CitizenRegistrationSerializer(serializers.ModelSerializer):
    """Self-registration: creates the Citizen *and* the linked login account in one step.

    Mirrors ``CitizenRegistrationForm`` — the citizen can sign in and use the portal
    immediately, even while the registration is still PENDING.
    """

    username = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=150,
        help_text="Optional — defaults to the phone number when left blank.",
    )
    password1 = serializers.CharField(write_only=True, style={"input_type": "password"})
    password2 = serializers.CharField(write_only=True, style={"input_type": "password"})

    class Meta:
        model = Citizen
        fields = (
            "full_name",
            "national_id",
            "phone_number",
            "gender",
            "date_of_birth",
            "region",
            "district",
            "ward",
            "mtaa",
            "profile_photo",
            "registration_notes",
            "username",
            "password1",
            "password2",
        )

    def validate_username(self, value):
        value = (value or "").strip()
        if value and User.objects.filter(username=value).exists():
            raise serializers.ValidationError("That username is already taken.")
        return value

    def validate_phone_number(self, value):
        # Parity with the form, tightened: the form only checked username, but
        # User.phone_number is unique too, so check both to avoid an IntegrityError.
        if User.objects.filter(Q(username=value) | Q(phone_number=value)).exists():
            raise serializers.ValidationError(
                "An account already exists for this phone number."
            )
        return value

    def validate(self, attrs):
        password1 = attrs.get("password1")
        password2 = attrs.get("password2")
        if password1 and password2 and password1 != password2:
            raise serializers.ValidationError({"password2": "Passwords do not match."})
        if password2:
            try:
                validate_password(password2)
            except DjangoValidationError as exc:
                raise serializers.ValidationError({"password2": list(exc.messages)})
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        username = (validated_data.pop("username", "") or "").strip()
        password = validated_data.pop("password2")
        validated_data.pop("password1", None)

        # Saving here (not queryset.update()) is essential: the post_save signals send the
        # "awaiting approval" SMS, notify the ward officers/admins, and write the audit log.
        citizen = Citizen.objects.create(**validated_data)

        first_name, _, last_name = citizen.full_name.partition(" ")
        user = User(
            username=username or citizen.phone_number,
            role=User.Role.CITIZEN,
            phone_number=citizen.phone_number,
            national_id=citizen.national_id,
            first_name=first_name,
            last_name=last_name,
        )
        user.set_password(password)
        user.save()

        citizen.user = user
        citizen.save(update_fields=["user"])

        self.created_user = user
        return citizen


class RejectionSerializer(serializers.Serializer):
    """Officers must give a reason — it is saved on the record and sent to the citizen by SMS."""

    reason = serializers.CharField(allow_blank=False, trim_whitespace=True)


class PublicCitizenSerializer(serializers.ModelSerializer):
    """Public landing-page card — exactly what templates/citizens/home.html renders.

    Deliberately minimal: anonymous visitors must not receive national_id, phone number,
    date of birth, notes, or the profile photo.
    """

    ward_name = serializers.CharField(source="ward.name", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Citizen
        fields = ("id", "citizen_id", "full_name", "ward_name", "status", "status_display")