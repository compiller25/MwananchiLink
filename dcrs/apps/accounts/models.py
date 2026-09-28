from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        OFFICER = "OFFICER", "Officer"
        CITIZEN = "CITIZEN", "Citizen"

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.OFFICER)
    phone_number = models.CharField(max_length=20, blank=True, unique=True, null=True)
    national_id = models.CharField(max_length=32, blank=True, unique=True)
    ward = models.ForeignKey(
        "localities.Ward",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="users",
    )
    is_phone_verified = models.BooleanField(default=False)
    failed_login_attempts = models.PositiveSmallIntegerField(default=0)
    locked_until = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["username"]

    @property
    def is_officer(self):
        return self.role in {self.Role.ADMIN, self.Role.OFFICER} or self.is_staff

    @property
    def is_citizen_profile(self):
        return self.role == self.Role.CITIZEN
