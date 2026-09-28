from django.contrib import admin

from .models import Citizen


@admin.register(Citizen)
class CitizenAdmin(admin.ModelAdmin):
    list_display = ("citizen_id", "full_name", "phone_number", "status", "ward", "created_at")
    list_filter = ("status", "ward", "region")
    search_fields = ("citizen_id", "full_name", "national_id", "phone_number")
    ordering = ("-created_at",)
