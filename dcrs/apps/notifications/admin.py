from django.contrib import admin

from .models import SMSTemplate, SMSLog


@admin.register(SMSTemplate)
class SMSTemplateAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("name", "slug", "body")


@admin.register(SMSLog)
class SMSLogAdmin(admin.ModelAdmin):
    list_display = ("recipient", "status", "provider", "sent_at", "created_at")
    list_filter = ("status", "provider")
    search_fields = ("recipient", "message_body", "reference_id")
