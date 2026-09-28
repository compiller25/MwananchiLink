"""Serializers for the auth API.

``UserSerializer`` is the SPA's ``me`` payload — it replaces the
``apps.notifications.context_processors.notifications`` context processor, which only
ever fed the server-rendered navbar/sidebar.
"""
from django.contrib.auth import authenticate, get_user_model
from rest_framework import serializers

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    role_display = serializers.CharField(source="get_role_display", read_only=True)
    full_name = serializers.CharField(source="get_full_name", read_only=True)
    ward_name = serializers.SerializerMethodField()
    citizen_profile = serializers.SerializerMethodField()
    is_officer = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "first_name",
            "last_name",
            "full_name",
            "email",
            "role",
            "role_display",
            "is_officer",
            "phone_number",
            "national_id",
            "ward",
            "ward_name",
            "is_phone_verified",
            "citizen_profile",
        )

    def get_ward_name(self, obj):
        return obj.ward.name if obj.ward_id else None

    def get_citizen_profile(self, obj):
        """Compact summary so the SPA knows the citizen's status without a second call."""
        profile = getattr(obj, "citizen_profile", None)
        if profile is None:
            return None
        return {
            "id": profile.pk,
            "citizen_id": profile.citizen_id,
            "full_name": profile.full_name,
            "status": profile.status,
            "ward": profile.ward_id,
        }


class LoginSerializer(serializers.Serializer):
    """Sign in with username OR phone number (``UsernameOrPhoneBackend``)."""

    username = serializers.CharField(help_text="Username or phone number")
    password = serializers.CharField(write_only=True, style={"input_type": "password"})

    def validate(self, attrs):
        request = self.context.get("request")
        user = authenticate(
            request=request,
            username=attrs["username"].strip(),
            password=attrs["password"],
        )
        if user is None:
            # Deliberately vague — do not reveal whether the account exists.
            raise serializers.ValidationError(
                {"detail": "Invalid username/phone number or password."}
            )
        if not user.is_active:
            raise serializers.ValidationError({"detail": "This account is inactive."})
        attrs["user"] = user
        return attrs


class PasswordResetSerializer(serializers.Serializer):
    """Thin wrapper over Django's ``PasswordResetForm`` (console backend in dev)."""

    email = serializers.EmailField()

    def save(self, **kwargs):
        from django.contrib.auth.forms import PasswordResetForm

        request = self.context.get("request")
        form = PasswordResetForm({"email": self.validated_data["email"]})
        if form.is_valid():
            form.save(
                request=request,
                use_https=bool(request and request.is_secure()),
                email_template_name="accounts/password_reset_email.txt",
            )
        return self.validated_data["email"]


class OtpVerifySerializer(serializers.Serializer):
    otp = serializers.CharField(max_length=6, min_length=4)