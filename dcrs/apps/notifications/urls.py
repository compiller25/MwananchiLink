from django.urls import path

from .views import (
    BroadcastSMSView,
    ComposeSMSView,
    LogIncomingSMSView,
    NotificationListView,
    NotificationMarkReadView,
    SMSCallbackView,
    SMSLogListView,
)

app_name = "notifications"

urlpatterns = [
    path("compose/", ComposeSMSView.as_view(), name="compose"),
    path("broadcast/", BroadcastSMSView.as_view(), name="broadcast"),
    path("log/", SMSLogListView.as_view(), name="log"),
    path("log-incoming/", LogIncomingSMSView.as_view(), name="log_incoming"),
    path("callback/", SMSCallbackView.as_view(), name="callback"),
    path("inbox/", NotificationListView.as_view(), name="inbox"),
    path("inbox/read-all/", NotificationMarkReadView.as_view(), name="mark_all_read"),
    path("inbox/<int:pk>/read/", NotificationMarkReadView.as_view(), name="mark_read"),
]
