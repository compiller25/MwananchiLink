from django.conf import settings
from django.db import models


class Notification(models.Model):
    """Web notification inbox — bell icon, read/unread (slide 22)."""

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications"
    )
    message = models.CharField(max_length=255)
    related_issue = models.ForeignKey(
        "issues.Issue", on_delete=models.SET_NULL, null=True, blank=True, related_name="notifications"
    )
    related_citizen = models.ForeignKey(
        "citizens.Citizen", on_delete=models.SET_NULL, null=True, blank=True, related_name="notifications"
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.recipient} - {self.message[:40]}"


class SMSTemplate(models.Model):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(unique=True)
    body = models.TextField()
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class SMSLog(models.Model):
    class Status(models.TextChoices):
        QUEUED = "QUEUED", "Queued"
        SENT = "SENT", "Sent"
        DELIVERED = "DELIVERED", "Delivered"
        FAILED = "FAILED", "Failed"

    class Direction(models.TextChoices):
        OUTBOUND = "OUTBOUND", "Outbound"
        INBOUND = "INBOUND", "Inbound"

    recipient = models.CharField(max_length=30)
    message_body = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.QUEUED)
    provider = models.CharField(max_length=80, default="Internal Simulator")
    reference_id = models.CharField(max_length=80, blank=True)
    error_message = models.TextField(blank=True)
    sent_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # Staff-relayed two-way SMS (slide 22) — citizen calls/texts the published number directly;
    # staff logs what was said here so it threads next to the outbound SMS log on the issue.
    direction = models.CharField(max_length=10, choices=Direction.choices, default=Direction.OUTBOUND)
    issue = models.ForeignKey(
        "issues.Issue", on_delete=models.SET_NULL, null=True, blank=True, related_name="sms_logs"
    )
    logged_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.recipient} - {self.status}"
