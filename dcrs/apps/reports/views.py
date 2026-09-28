from django.apps import apps
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.views.generic import ListView, TemplateView

from .models import AuditLog


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "reports/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        Citizen = apps.get_model("citizens", "Citizen")
        Issue = apps.get_model("issues", "Issue")
        SMSLog = apps.get_model("notifications", "SMSLog")
        today = timezone.localdate()
        context.update(
            total_citizens=Citizen.objects.count(),
            pending_approvals=Citizen.objects.filter(status=Citizen.Status.PENDING).count(),
            open_issues=Issue.objects.exclude(status__in=[Issue.Status.RESOLVED, Issue.Status.CLOSED]).count(),
            sms_sent_today=SMSLog.objects.filter(created_at__date=today, status=SMSLog.Status.SENT).count(),
            recent_citizens=Citizen.objects.select_related("ward", "district").all()[:5],
            recent_issues=Issue.objects.select_related("citizen", "ward").all()[:5],
            recent_activity=AuditLog.objects.select_related("actor").all()[:8],
        )
        return context


class RegistrationReportView(LoginRequiredMixin, TemplateView):
    template_name = "reports/registration_report.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        Citizen = apps.get_model("citizens", "Citizen")
        citizens = Citizen.objects.select_related("ward", "district", "region").all()
        ward = self.request.GET.get("ward")
        status = self.request.GET.get("status")
        if ward:
            citizens = citizens.filter(ward__name__icontains=ward)
        if status:
            citizens = citizens.filter(status=status)
        context["citizens"] = citizens
        context["selected_ward"] = ward or ""
        context["selected_status"] = status or ""
        return context


class AuditLogView(LoginRequiredMixin, ListView):
    model = AuditLog
    template_name = "reports/audit_log.html"
    paginate_by = 15
    context_object_name = "logs"
