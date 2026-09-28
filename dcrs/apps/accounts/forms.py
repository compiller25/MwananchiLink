from django import forms
from django.contrib.auth.forms import AuthenticationForm


class OfficerLoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(
            attrs={"class": "form-control form-control-lg", "placeholder": "Username or phone number"}
        )
    )
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={"class": "form-control form-control-lg", "placeholder": "Password"}
        )
    )


class OTPVerificationForm(forms.Form):
    otp = forms.CharField(
        max_length=6,
        widget=forms.TextInput(
            attrs={"class": "form-control form-control-lg text-center", "placeholder": "Enter OTP"}
        ),
    )
