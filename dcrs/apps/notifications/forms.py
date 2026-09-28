from django import forms

from apps.localities.models import Ward


class ComposeSMSForm(forms.Form):
    recipient = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={"class": "form-control form-control-lg", "placeholder": "+255..."}),
    )
    message_body = forms.CharField(widget=forms.Textarea(attrs={"class": "form-control", "rows": 5}))
    issue = forms.IntegerField(required=False, widget=forms.HiddenInput())


class BroadcastSMSForm(forms.Form):
    ward = forms.ModelChoiceField(
        queryset=Ward.objects.all(),
        required=False,
        label="Ward",
        widget=forms.Select(
            attrs={"class": "form-select form-select-lg"},
        ),
    )
    message_body = forms.CharField(widget=forms.Textarea(attrs={"class": "form-control", "rows": 5}))


class LogIncomingSMSForm(forms.Form):
    """Staff-relayed inbound SMS — citizen calls/texts the published number, staff logs it here."""

    sender_phone = forms.CharField(max_length=30, widget=forms.TextInput(attrs={"class": "form-control"}))
    message_body = forms.CharField(widget=forms.Textarea(attrs={"class": "form-control", "rows": 3}))
    issue = forms.IntegerField(required=False, widget=forms.HiddenInput())
    send_reply = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={"class": "form-check-input"}))
    reply_body = forms.CharField(
        required=False, widget=forms.Textarea(attrs={"class": "form-control", "rows": 2})
    )
