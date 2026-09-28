from django.urls import path

from .api_views import (
    IssueCommentDeleteView,
    IssueCommentListCreateView,
    IssueDetailView,
    IssueFeedbackView,
    IssueListCreateView,
    ServiceCentreView,
)

app_name = "issues_api"

urlpatterns = [
    path("", IssueListCreateView.as_view(), name="list_create"),
    path("services/", ServiceCentreView.as_view(), name="services"),
    path("comments/<int:pk>/", IssueCommentDeleteView.as_view(), name="comment_delete"),
    path("<int:pk>/", IssueDetailView.as_view(), name="detail"),
    path("<int:pk>/feedback/", IssueFeedbackView.as_view(), name="feedback"),
    path("<int:pk>/comments/", IssueCommentListCreateView.as_view(), name="comments"),
]