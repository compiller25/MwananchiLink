from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("username", "email", "phone_number", "role", "is_staff", "is_active")
    list_filter = ("role", "is_staff", "is_active")
    search_fields = ("username", "email", "phone_number", "national_id")
    ordering = ("username",)

    fieldsets = BaseUserAdmin.fieldsets + (
        (
            "Lodrick Profile",
            {
                "fields": (
                    "role",
                    "phone_number",
                    "national_id",
                    "ward",
                    "is_phone_verified",
                    "failed_login_attempts",
                    "locked_until",
                )
            },
        ),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        (
            "Lodrick Profile",
            {
                "fields": (
                    "role",
                    "phone_number",
                    "national_id",
                    "ward",
                    "is_phone_verified",
                )
            },
        ),
    )
