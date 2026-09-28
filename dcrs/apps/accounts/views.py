from django.contrib.auth import logout as auth_logout
from django.contrib.auth.views import LoginView, LogoutView, PasswordResetView
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import TemplateView

from .forms import OfficerLoginForm, OTPVerificationForm


class OfficerLoginPageView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = OfficerLoginForm
    redirect_authenticated_user = True

    def get_success_url(self):
        user = self.request.user
        if user.role == user.Role.CITIZEN:
            return reverse_lazy("citizens:portal")
        return reverse_lazy("reports:dashboard")


class OfficerLogoutView(LogoutView):
    next_page = reverse_lazy("citizens:home")
    http_method_names = ["get", "post", "options"]

    def get(self, request, *args, **kwargs):
        auth_logout(request)
        return redirect(self.next_page)


class OTPVerifyView(TemplateView):
    template_name = "accounts/otp_verify.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = OTPVerificationForm()
        return context


class OfficerPasswordResetView(PasswordResetView):
    template_name = "accounts/password_reset.html"
    email_template_name = "accounts/password_reset_email.txt"
    success_url = reverse_lazy("accounts:login")
