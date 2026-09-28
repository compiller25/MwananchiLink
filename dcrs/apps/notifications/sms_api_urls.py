"""SMS endpoints for the SPA (compose, broadcast, log, staff-relayed inbound).

The SendAfrica delivery webhook is NOT duplicated here: it stays at
``/portal/sms/callback/`` (``SMSCallbackView``) because that exact URL is registered in the
SendAfrica dashboard — moving it would break delivery confirmations in production.
"""
from django.urls import path

from .api_views import (
    BroadcastSmsView,
    ComposeSmsView,
    LogIncomingSmsView,
    SmsLogListView,
)

app_name = "sms_api"

urlpatterns = [
    path("compose/", ComposeSmsView.as_view(), name="compose"),
    path("broadcast/", BroadcastSmsView.as_view(), name="broadcast"),
    path("log/", SmsLogListView.as_view(), name="log"),
    path("log-incoming/", LogIncomingSmsView.as_view(), name="log_incoming"),
]