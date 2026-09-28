from django.urls import path

from .api_views import AuditLogView, DashboardView, RegistrationReportView

app_name = "reports_api"

urlpatterns = [
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("registration/", RegistrationReportView.as_view(), name="registration"),
    path("audit/", AuditLogView.as_view(), name="audit"),
]