from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView, TemplateView, UpdateView

from apps.accounts.mixins import WardScopedQuerysetMixin
from apps.citizens.models import Citizen
from apps.notifications.services import send_issue_update_sms

from .constants import SERVICE_TILES
from .forms import IssueCommentForm, IssueFeedbackForm, IssueForm, IssueStatusForm
from .models import Issue, IssueComment


class ServiceCentreView(LoginRequiredMixin, TemplateView):
    """One-Stop Emergency & Services Centre — 5 service tiles (slide 20)."""

    template_name = "issues/service_centre.html"

    # Shared with the API (GET /api/v1/issues/services/) so both stay in sync.
    SERVICES = SERVICE_TILES

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["services"] = self.SERVICES
        return context


class IssueListView(WardScopedQuerysetMixin, LoginRequiredMixin, ListView):
    model = Issue
    template_name = "issues/issue_list.html"
    paginate_by = 10
    context_object_name = "issues"
    ward_lookup = "ward"

    def get_queryset(self):
        return super().get_queryset().select_related("citizen", "ward", "assigned_officer").all()


class IssueCreateView(LoginRequiredMixin, CreateView):
    model = Issue
    form_class = IssueForm
    template_name = "issues/issue_submit.html"
    success_url = reverse_lazy("issues:list")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user.role == request.user.Role.CITIZEN:
            try:
                profile = request.user.citizen_profile
            except Citizen.DoesNotExist:
                profile = None
            if not profile or profile.status != Citizen.Status.APPROVED:
                messages.error(request, "Only approved citizens can file a service request.")
                return redirect("citizens:portal")
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        initial = super().get_initial()
        category = self.request.GET.get("category")
        if category:
            initial["category"] = category
        if self.request.user.role == self.request.user.Role.CITIZEN:
            try:
                profile = self.request.user.citizen_profile
                initial["citizen"] = profile.pk
                initial["ward"] = profile.ward_id
            except Citizen.DoesNotExist:
                pass
        return initial


class IssueDetailView(WardScopedQuerysetMixin, LoginRequiredMixin, DetailView):
    model = Issue
    template_name = "issues/issue_detail.html"
    context_object_name = "issue"
    ward_lookup = "ward"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["comment_form"] = IssueCommentForm()
        context["comments"] = self.object.comments.select_related("author").all()
        context["sms_thread"] = self.object.sms_logs.order_by("created_at")
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = IssueCommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.issue = self.object
            comment.author = request.user
            comment.save()
            messages.success(request, "Comment added.")
            if request.user.role != request.user.Role.CITIZEN and not comment.is_internal:
                send_issue_update_sms(self.object, f"New update from the ward: {comment.body[:120]}")
        return redirect("issues:detail", pk=self.object.pk)


class IssueUpdateView(WardScopedQuerysetMixin, LoginRequiredMixin, UpdateView):
    model = Issue
    form_class = IssueStatusForm
    template_name = "issues/issue_update.html"
    ward_lookup = "ward"

    def get_success_url(self):
        messages.success(self.request, f"Issue {self.object.reference_no} updated.")
        return reverse_lazy("issues:detail", kwargs={"pk": self.object.pk})


class IssueFeedbackView(LoginRequiredMixin, View):
    """Lets the reporting citizen rate a RESOLVED issue once (slides 21, 23)."""

    def post(self, request, pk):
        issue = get_object_or_404(
            Issue, pk=pk, citizen__user=request.user, status=Issue.Status.RESOLVED, rating__isnull=True
        )
        form = IssueFeedbackForm(request.POST, instance=issue)
        if form.is_valid():
            form.save()
            messages.success(request, "Thanks for your feedback!")
            send_issue_update_sms(issue, "Thank you for your feedback. It helps us serve your community better.")
        else:
            messages.error(request, "Please choose a rating between 1 and 5.")
        return redirect("issues:detail", pk=issue.pk)


class IssueDeleteView(LoginRequiredMixin, DeleteView):
    model = Issue
    template_name = "issues/issue_confirm_delete.html"
    context_object_name = "issue"
    success_url = reverse_lazy("issues:list")

    def form_valid(self, form):
        messages.success(self.request, f"Issue {self.object.reference_no} has been deleted.")
        return super().form_valid(form)


class IssueCommentDeleteView(LoginRequiredMixin, DeleteView):
    model = IssueComment

    def get_success_url(self):
        return reverse_lazy("issues:detail", kwargs={"pk": self.object.issue.pk})

    def get(self, request, *args, **kwargs):
        return self.delete(request, *args, **kwargs)
