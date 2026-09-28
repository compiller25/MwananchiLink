from django.contrib import admin

from .models import Issue, IssueComment


class IssueCommentInline(admin.TabularInline):
    model = IssueComment
    extra = 0


@admin.register(Issue)
class IssueAdmin(admin.ModelAdmin):
    list_display = ("reference_no", "title", "citizen", "category", "status", "priority", "ward", "created_at")
    list_filter = ("status", "priority", "category", "ward")
    search_fields = ("reference_no", "title", "citizen__full_name", "citizen__phone_number")
    inlines = [IssueCommentInline]


@admin.register(IssueComment)
class IssueCommentAdmin(admin.ModelAdmin):
    list_display = ("issue", "author", "is_internal", "created_at")
    list_filter = ("is_internal",)
    search_fields = ("issue__reference_no", "body", "author__username")
