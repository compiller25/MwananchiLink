from django import forms

from .models import Issue, IssueComment


class IssueForm(forms.ModelForm):
    class Meta:
        model = Issue
        exclude = (
            "reference_no", "status", "assigned_officer", "internal_notes", "escalated_to_district",
            "closed_at", "assigned_technician_name", "appointment_at", "rating", "feedback_comment",
            "created_at", "updated_at",
        )
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control form-control-lg", "placeholder": "Issue title"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 5}),
            "category": forms.Select(attrs={"class": "form-select form-select-lg"}),
            "priority": forms.Select(attrs={"class": "form-select form-select-lg"}),
            "citizen": forms.Select(attrs={"class": "form-select form-select-lg"}),
            "ward": forms.Select(attrs={"class": "form-select form-select-lg"}),
        }


class IssueStatusForm(forms.ModelForm):
    class Meta:
        model = Issue
        fields = (
            "status", "assigned_officer", "assigned_technician_name", "appointment_at",
            "internal_notes", "escalated_to_district",
        )
        widgets = {
            "status": forms.Select(attrs={"class": "form-select form-select-lg"}),
            "assigned_officer": forms.Select(attrs={"class": "form-select form-select-lg"}),
            "assigned_technician_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Technician name"}),
            "appointment_at": forms.DateTimeInput(attrs={"class": "form-control", "type": "datetime-local"}),
            "internal_notes": forms.Textarea(attrs={"class": "form-control", "rows": 5}),
        }


class IssueFeedbackForm(forms.ModelForm):
    class Meta:
        model = Issue
        fields = ("rating", "feedback_comment")
        widgets = {
            "rating": forms.RadioSelect(choices=[(n, n) for n in range(1, 6)]),
            "feedback_comment": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Tell us about your experience (optional)"}),
        }


class IssueCommentForm(forms.ModelForm):
    class Meta:
        model = IssueComment
        fields = ("body", "is_internal")
        widgets = {
            "body": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
        }
