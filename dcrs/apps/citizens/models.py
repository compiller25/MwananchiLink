from uuid import uuid4

from django.conf import settings
from django.db import models


class Citizen(models.Model):
    class Gender(models.TextChoices):
        FEMALE = "FEMALE", "Female"
        MALE = "MALE", "Male"
        OTHER = "OTHER", "Other"

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"
        SUSPENDED = "SUSPENDED", "Suspended"

    citizen_id = models.CharField(max_length=24, unique=True, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="citizen_profile",
    )
    full_name = models.CharField(max_length=160)
    national_id = models.CharField(max_length=32, unique=True)
    phone_number = models.CharField(max_length=20, unique=True)
    gender = models.CharField(max_length=16, choices=Gender.choices)
    date_of_birth = models.DateField(blank=True, null=True)
    region = models.ForeignKey("localities.Region", on_delete=models.PROTECT, related_name="citizens")
    district = models.ForeignKey("localities.District", on_delete=models.PROTECT, related_name="citizens")
    ward = models.ForeignKey("localities.Ward", on_delete=models.PROTECT, related_name="citizens")
    mtaa = models.ForeignKey(
        "localities.Mtaa", on_delete=models.PROTECT, related_name="citizens", blank=True, null=True
    )
    profile_photo = models.ImageField(upload_to="citizens/photos/", blank=True, null=True)
    registration_notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    rejection_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.citizen_id:
            self.citizen_id = f"CIT-{uuid4().hex[:10].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.full_name} ({self.citizen_id})"

