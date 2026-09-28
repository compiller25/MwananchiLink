from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

from .models import Citizen

_CTRL = {"class": "form-control"}
_SEL  = {"class": "form-select"}
_CTRL_LG = {"class": "form-control form-control-lg"}
_SEL_LG  = {"class": "form-select form-select-lg"}


class CitizenRegistrationForm(forms.ModelForm):
    """Creates the Citizen profile AND the linked login account in one step — the citizen can
    log in and use their portal immediately, even while their registration is still PENDING."""

    username = forms.CharField(
        label="Username",
        required=False,
        widget=forms.TextInput(attrs={**_CTRL_LG, "placeholder": "Choose a username (defaults to your phone number)"}),
    )
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={**_CTRL_LG, "placeholder": "Choose a password"}),
    )
    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={**_CTRL_LG, "placeholder": "Re-enter password"}),
    )

    def clean_username(self):
        username = self.cleaned_data.get("username", "").strip()
        if username and get_user_model().objects.filter(username=username).exists():
            raise forms.ValidationError("That username is already taken.")
        return username

    class Meta:
        model = Citizen
        exclude = ("citizen_id", "user", "status", "rejection_reason", "created_at", "updated_at")
        widgets = {
            "full_name":           forms.TextInput(attrs={**_CTRL_LG, "placeholder": "Full name"}),
            "national_id":         forms.TextInput(attrs={**_CTRL_LG, "placeholder": "National ID"}),
            "phone_number":        forms.TextInput(attrs={**_CTRL_LG, "placeholder": "+255..."}),
            "gender":              forms.Select(attrs=_SEL_LG),
            "date_of_birth":       forms.DateInput(attrs={**_CTRL_LG, "type": "date"}),
            "region":              forms.Select(attrs=_SEL_LG),
            "district":            forms.Select(attrs=_SEL_LG),
            "ward":                forms.Select(attrs=_SEL_LG),
            "mtaa":                forms.Select(attrs=_SEL_LG),
            "profile_photo":       forms.ClearableFileInput(attrs=_CTRL_LG),
            "registration_notes":  forms.Textarea(attrs={**_CTRL, "rows": 4}),
        }

    def clean_phone_number(self):
        phone_number = self.cleaned_data["phone_number"]
        if get_user_model().objects.filter(username=phone_number).exists():
            raise forms.ValidationError("An account already exists for this phone number.")
        return phone_number

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords do not match.")
        if password2:
            validate_password(password2)
        return password2


class CitizenEditForm(forms.ModelForm):
    class Meta:
        model = Citizen
        exclude = ("citizen_id", "user", "status", "rejection_reason", "created_at", "updated_at")
        widgets = {
            "full_name":           forms.TextInput(attrs=_CTRL),
            "national_id":         forms.TextInput(attrs=_CTRL),
            "phone_number":        forms.TextInput(attrs=_CTRL),
            "gender":              forms.Select(attrs=_SEL),
            "date_of_birth":       forms.DateInput(attrs={**_CTRL, "type": "date"}),
            "region":              forms.Select(attrs=_SEL),
            "district":            forms.Select(attrs=_SEL),
            "ward":                forms.Select(attrs=_SEL),
            "mtaa":                forms.Select(attrs=_SEL),
            "profile_photo":       forms.ClearableFileInput(attrs=_CTRL),
            "registration_notes":  forms.Textarea(attrs={**_CTRL, "rows": 3}),
        }

