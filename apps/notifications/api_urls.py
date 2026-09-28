from django.urls import path

from .api_views import (
    NotificationListView,
    NotificationMarkAllReadView,
    NotificationMarkReadView,
    UnreadNotificationsView,
)

app_name = "notifications_api"

urlpatterns = [
    # The signed-in user's own inbox (never anyone else's).
    path("", NotificationListView.as_view(), name="list"),
    path("unread/", UnreadNotificationsView.as_view(), name="unread"),
    path("read-all/", NotificationMarkAllReadView.as_view(), name="read_all"),
    path("<int:pk>/read/", NotificationMarkReadView.as_view(), name="read"),
]