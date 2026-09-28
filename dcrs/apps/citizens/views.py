from django.apps import apps
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth import login as auth_login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView, TemplateView, UpdateView

from apps.accounts.mixins import WardScopedQuerysetMixin

from .forms import CitizenEditForm, CitizenRegistrationForm
from .models import Citizen


def _guard_ward_access(request, citizen):
    """404 a non-admin officer trying to act on a citizen outside their ward.

    Mirrors WardScopedQuerysetMixin for the single-object action views (Approve/Reject) that
    fetch by pk directly rather than through get_queryset().
    """
    user = request.user
    if user.role != user.Role.OFFICER or user.is_superuser:
        return
    if not user.ward_id or user.ward_id != citizen.ward_id:
        raise Http404


class CitizenPortalView(LoginRequiredMixin, TemplateView):
    template_name = "citizens/portal.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        Issue = apps.get_model("issues", "Issue")
        try:
            profile = self.request.user.citizen_profile
        except Citizen.DoesNotExist:
            profile = None
        context["profile"] = profile
        if profile:
            my_issues = Issue.objects.filter(citizen=profile).order_by("-created_at")
            context["my_issues"] = my_issues[:10]
            context["open_count"] = my_issues.exclude(
                status__in=["RESOLVED", "CLOSED"]
            ).count()
        else:
            context["my_issues"] = []
            context["open_count"] = 0
        return context


class CitizenHomeView(TemplateView):
    template_name = "citizens/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        Issue = apps.get_model("issues", "Issue")
        SMSLog = apps.get_model("notifications", "SMSLog")
        context.update(
            total_citizens=Citizen.objects.count(),
            pending_citizens=Citizen.objects.filter(status=Citizen.Status.PENDING).count(),
            open_issues=Issue.objects.filter(status__in=["OPEN", "IN_PROGRESS", "ESCALATED"]).count(),
            sms_logs=SMSLog.objects.count(),
            recent_citizens=Citizen.objects.select_related("ward", "district").all()[:4],
        )
        return context


class CitizenRegistrationView(CreateView):
    model = Citizen
    form_class = CitizenRegistrationForm
    template_name = "citizens/register.html"
    success_url = reverse_lazy("citizens:portal")

    def form_valid(self, form):
        response = super().form_valid(form)
        citizen = self.object

        User = get_user_model()
        first_name, _, last_name = citizen.full_name.partition(" ")
        user = User(
            username=form.cleaned_data.get("username") or citizen.phone_number,
            role=User.Role.CITIZEN,
            phone_number=citizen.phone_number,
            national_id=citizen.national_id,
            first_name=first_name,
            last_name=last_name,
        )
        user.set_password(form.cleaned_data["password2"])
        user.save()

        citizen.user = user
        citizen.save(update_fields=["user"])

        auth_login(self.request, user)
        messages.success(self.request, "Registration submitted — you're logged in, and can track your approval status here.")
        return response


class CitizenListView(WardScopedQuerysetMixin, LoginRequiredMixin, ListView):
    model = Citizen
    template_name = "citizens/citizen_list.html"
    paginate_by = 10
    context_object_name = "citizens"
    ward_lookup = "ward"

    def get_queryset(self):
        return super().get_queryset().select_related("region", "district", "ward", "mtaa").all()


class CitizenDetailView(WardScopedQuerysetMixin, LoginRequiredMixin, DetailView):
    model = Citizen
    template_name = "citizens/citizen_detail.html"
    context_object_name = "citizen"
    ward_lookup = "ward"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        Issue = apps.get_model("issues", "Issue")
        context["citizen_issues"] = Issue.objects.filter(
            citizen=self.object
        ).select_related("ward", "assigned_officer").order_by("-created_at")[:10]
        return context


class CitizenUpdateView(WardScopedQuerysetMixin, LoginRequiredMixin, UpdateView):
    model = Citizen
    form_class = CitizenEditForm
    template_name = "citizens/citizen_edit.html"
    context_object_name = "citizen"
    ward_lookup = "ward"

    def get_success_url(self):
        messages.success(self.request, f"{self.object.full_name}'s profile has been updated.")
        return reverse_lazy("citizens:detail", kwargs={"pk": self.object.pk})


class CitizenApproveView(LoginRequiredMixin, View):
    def post(self, request, pk):
        citizen = get_object_or_404(Citizen, pk=pk)
        _guard_ward_access(request, citizen)
        citizen.status = Citizen.Status.APPROVED
        citizen.rejection_reason = ""
        citizen.save()
        messages.success(request, f"{citizen.full_name} has been approved.")
        return redirect("citizens:detail", pk=citizen.pk)


class CitizenRejectView(LoginRequiredMixin, View):
    def post(self, request, pk):
        citizen = get_object_or_404(Citizen, pk=pk)
        _guard_ward_access(request, citizen)
        reason = request.POST.get("reason", "").strip()
        if not reason:
            messages.error(request, "A rejection reason is required.")
            return redirect("citizens:detail", pk=citizen.pk)
        citizen.status = Citizen.Status.REJECTED
        citizen.rejection_reason = reason
        citizen.save()
        messages.success(request, f"{citizen.full_name}'s registration has been rejected.")
        return redirect("citizens:detail", pk=citizen.pk)


class CitizenDeleteView(LoginRequiredMixin, DeleteView):
    model = Citizen
    template_name = "citizens/citizen_confirm_delete.html"
    context_object_name = "citizen"
    success_url = reverse_lazy("citizens:list")

    def form_valid(self, form):
        messages.success(self.request, f"Citizen record for {self.object.full_name} has been deleted.")
        return super().form_valid(form)


class CitizenStatusView(LoginRequiredMixin, DetailView):
    model = Citizen
    template_name = "citizens/citizen_status.html"
    context_object_name = "citizen"
