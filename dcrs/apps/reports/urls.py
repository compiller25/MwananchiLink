from django.urls import path

from .views import AuditLogView, DashboardView, RegistrationReportView

app_name = "reports"

urlpatterns = [
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("registration/", RegistrationReportView.as_view(), name="registration_report"),
    path("audit/", AuditLogView.as_view(), name="audit_log"),
]
