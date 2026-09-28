from django.urls import path

from .views import (
    IssueCommentDeleteView,
    IssueCreateView,
    IssueDeleteView,
    IssueDetailView,
    IssueFeedbackView,
    IssueListView,
    IssueUpdateView,
    ServiceCentreView,
)

app_name = "issues"

urlpatterns = [
    path("", IssueListView.as_view(), name="list"),
    path("services/", ServiceCentreView.as_view(), name="service_centre"),
    path("submit/", IssueCreateView.as_view(), name="submit"),
    path("<int:pk>/", IssueDetailView.as_view(), name="detail"),
    path("<int:pk>/update/", IssueUpdateView.as_view(), name="update"),
    path("<int:pk>/delete/", IssueDeleteView.as_view(), name="delete"),
    path("<int:pk>/feedback/", IssueFeedbackView.as_view(), name="feedback"),
    path("comment/<int:pk>/delete/", IssueCommentDeleteView.as_view(), name="comment_delete"),
]
