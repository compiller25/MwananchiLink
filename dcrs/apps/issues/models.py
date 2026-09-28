from uuid import uuid4

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Issue(models.Model):
    class Category(models.TextChoices):
        # Labels match the One-Stop Services Centre tiles (Water/Electricity/Waste/Roads/Security).
        WATER = "WATER", "Water"
        ELECTRICITY = "ELECTRICITY", "Electricity"
        SANITATION = "SANITATION", "Waste"
        ROAD = "ROAD", "Roads"
        SECURITY = "SECURITY", "Security"
        LIGHTING = "LIGHTING", "Lighting"
        OTHER = "OTHER", "Other"

    class Priority(models.TextChoices):
        LOW = "LOW", "Low"
        MEDIUM = "MEDIUM", "Medium"
        HIGH = "HIGH", "High"
        CRITICAL = "CRITICAL", "Critical"

    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        IN_PROGRESS = "IN_PROGRESS", "In progress"
        ESCALATED = "ESCALATED", "Escalated"
        RESOLVED = "RESOLVED", "Resolved"
        CLOSED = "CLOSED", "Closed"

    reference_no = models.CharField(max_length=24, unique=True, editable=False)
    citizen = models.ForeignKey("citizens.Citizen", on_delete=models.CASCADE, related_name="issues")
    title = models.CharField(max_length=180)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=Category.choices)
    priority = models.CharField(max_length=20, choices=Priority.choices, default=Priority.MEDIUM)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    ward = models.ForeignKey("localities.Ward", on_delete=models.PROTECT, related_name="issues")
    assigned_officer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="assigned_issues",
    )
    internal_notes = models.TextField(blank=True)
    escalated_to_district = models.BooleanField(default=False)
    closed_at = models.DateTimeField(blank=True, null=True)

    # One-Stop Services Centre — appointment/technician assignment (slide 21)
    assigned_technician_name = models.CharField(max_length=120, blank=True)
    appointment_at = models.DateTimeField(blank=True, null=True)

    # Citizen feedback after resolution (slides 21, 23)
    rating = models.PositiveSmallIntegerField(
        blank=True, null=True, validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    feedback_comment = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.reference_no:
            self.reference_no = f"ISS-{uuid4().hex[:10].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.reference_no} - {self.title}"


class IssueComment(models.Model):
    issue = models.ForeignKey(Issue, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="issue_comments")
    body = models.TextField()
    is_internal = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Comment on {self.issue.reference_no}"
