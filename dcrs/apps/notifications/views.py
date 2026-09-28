import json

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import FormView, ListView

from apps.citizens.models import Citizen

from .forms import BroadcastSMSForm, ComposeSMSForm, LogIncomingSMSForm
from .models import Notification, SMSLog
from .services import broadcast_sms, send_sms


class ComposeSMSView(LoginRequiredMixin, FormView):
    template_name = "notifications/sms_compose.html"
    form_class = ComposeSMSForm

    def get_initial(self):
        initial = super().get_initial()
        if self.request.GET.get("recipient"):
            initial["recipient"] = self.request.GET["recipient"]
        if self.request.GET.get("issue"):
            initial["issue"] = self.request.GET["issue"]
        return initial

    def form_valid(self, form):
        log = send_sms(form.cleaned_data["recipient"], form.cleaned_data["message_body"])
        issue_id = form.cleaned_data.get("issue")
        if issue_id:
            SMSLog.objects.filter(pk=log.pk).update(issue_id=issue_id)
            self._issue_id = issue_id
        return super().form_valid(form)

    def get_success_url(self):
        issue_id = getattr(self, "_issue_id", None)
        if issue_id:
            return reverse_lazy("issues:detail", kwargs={"pk": issue_id})
        return reverse_lazy("notifications:log")


class BroadcastSMSView(LoginRequiredMixin, FormView):
    template_name = "notifications/sms_broadcast.html"
    form_class = BroadcastSMSForm
    success_url = reverse_lazy("notifications:log")

    def _target_ward(self, user, cleaned_ward):
        """Officers may only broadcast to their own ward; admins may pick any."""
        if user.role == user.Role.OFFICER and not user.is_superuser:
            return user.ward
        return cleaned_ward

    def get_initial(self):
        initial = super().get_initial()
        user = self.request.user
        if user.role == user.Role.OFFICER and not user.is_superuser and user.ward_id:
            initial["ward"] = user.ward_id
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        officer_ward = (
            user.ward
            if user.role == user.Role.OFFICER and not user.is_superuser
            else None
        )
        context["officer_ward"] = officer_ward
        return context

    def form_valid(self, form):
        user = self.request.user
        ward = self._target_ward(user, form.cleaned_data.get("ward"))
        citizens = Citizen.objects.filter(status=Citizen.Status.APPROVED)
        if ward:
            citizens = citizens.filter(ward=ward)
        recipients = citizens.values_list("phone_number", flat=True)
        broadcast_sms(recipients, form.cleaned_data["message_body"])
        messages.success(
            self.request,
            f"Broadcast sent to {len(recipients)} approved citizen(s).",
        )
        return super().form_valid(form)


class LogIncomingSMSView(LoginRequiredMixin, View):
    """Staff-relayed inbound SMS (slide 22) — citizen calls/texts the published number directly;
    staff logs what was said here so it threads next to the outbound SMS log on the issue."""

    def post(self, request):
        form = LogIncomingSMSForm(request.POST)
        issue_id = request.POST.get("issue") or None
        redirect_target = reverse_lazy("issues:detail", kwargs={"pk": issue_id}) if issue_id else reverse_lazy("notifications:log")

        if not form.is_valid():
            messages.error(request, "Please fill in the sender's phone number and message.")
            return redirect(redirect_target)

        SMSLog.objects.create(
            recipient=form.cleaned_data["sender_phone"],
            message_body=form.cleaned_data["message_body"],
            status=SMSLog.Status.SENT,
            provider="Staff-logged (phone)",
            direction=SMSLog.Direction.INBOUND,
            issue_id=issue_id,
            logged_by=request.user,
        )
        if form.cleaned_data.get("send_reply") and form.cleaned_data.get("reply_body"):
            log = send_sms(form.cleaned_data["sender_phone"], form.cleaned_data["reply_body"])
            if issue_id:
                SMSLog.objects.filter(pk=log.pk).update(issue_id=issue_id)

        messages.success(request, "Incoming SMS logged.")
        return redirect(redirect_target)


@method_decorator(csrf_exempt, name="dispatch")
class SMSCallbackView(View):
    """Receives delivery status pushes from SendAfrica (SMS -> Settings -> Callback URLs)."""

    STATUS_MAP = {
        "delivered": SMSLog.Status.DELIVERED,
        "failed": SMSLog.Status.FAILED,
        "sent": SMSLog.Status.SENT,
    }

    def post(self, request, *args, **kwargs):
        try:
            payload = json.loads(request.body or "{}")
        except json.JSONDecodeError:
            return JsonResponse({"success": False, "error": "invalid_json"}, status=400)

        message_id = payload.get("message_id") or payload.get("id")
        raw_status = str(payload.get("status", "")).lower()
        new_status = self.STATUS_MAP.get(raw_status)

        if not message_id or not new_status:
            return JsonResponse({"success": False, "error": "unrecognised_payload"}, status=400)

        updated = SMSLog.objects.filter(reference_id=message_id).update(status=new_status)

        return JsonResponse({"success": True, "updated": bool(updated)})


class SMSLogListView(LoginRequiredMixin, ListView):
    model = SMSLog
    template_name = "notifications/sms_log.html"
    paginate_by = 12
    context_object_name = "sms_logs"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["delivered_count"] = SMSLog.objects.filter(status=SMSLog.Status.DELIVERED).count()
        context["sent_count"] = SMSLog.objects.filter(status=SMSLog.Status.SENT).count()
        context["failed_count"] = SMSLog.objects.filter(status=SMSLog.Status.FAILED).count()
        return context


class NotificationListView(LoginRequiredMixin, ListView):
    model = Notification
    template_name = "notifications/inbox.html"
    paginate_by = 20
    context_object_name = "notifications"

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user).select_related("related_issue")


class NotificationMarkReadView(LoginRequiredMixin, View):
    def post(self, request, pk=None):
        qs = Notification.objects.filter(recipient=request.user)
        if pk is None:
            qs.update(is_read=True)
        else:
            qs.filter(pk=pk).update(is_read=True)
        return redirect(request.POST.get("next") or "notifications:inbox")
