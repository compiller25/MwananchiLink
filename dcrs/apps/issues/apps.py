from django.apps import AppConfig


class IssuesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.issues"
    label = "issues"

    def ready(self):
        from . import signals  # noqa: F401

