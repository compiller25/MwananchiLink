from django.urls import path

from .views import (
    CitizenApproveView,
    CitizenDeleteView,
    CitizenDetailView,
    CitizenHomeView,
    CitizenListView,
    CitizenPortalView,
    CitizenRegistrationView,
    CitizenRejectView,
    CitizenStatusView,
    CitizenUpdateView,
)

app_name = "citizens"

urlpatterns = [
    path("", CitizenHomeView.as_view(), name="home"),
    path("portal/", CitizenPortalView.as_view(), name="portal"),
    path("register/", CitizenRegistrationView.as_view(), name="register"),
    path("list/", CitizenListView.as_view(), name="list"),
    path("<int:pk>/", CitizenDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", CitizenUpdateView.as_view(), name="edit"),
    path("<int:pk>/delete/", CitizenDeleteView.as_view(), name="delete"),
    path("<int:pk>/status/", CitizenStatusView.as_view(), name="status"),
    path("<int:pk>/approve/", CitizenApproveView.as_view(), name="approve"),
    path("<int:pk>/reject/", CitizenRejectView.as_view(), name="reject"),
]
