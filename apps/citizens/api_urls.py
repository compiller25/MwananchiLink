from django.urls import path

from .api_views import (
    CitizenApproveView,
    CitizenDetailView,
    CitizenListView,
    CitizenMeView,
    CitizenRegistrationView,
    CitizenRejectView,
    CitizenStatusView,
)

app_name = "citizens_api"

urlpatterns = [
    # Public self-registration (must come before the <int:pk> patterns).
    path("register/", CitizenRegistrationView.as_view(), name="register"),
    # The signed-in citizen's own portal payload.
    path("me/", CitizenMeView.as_view(), name="me"),
    # Staff-only register (ward-scoped for officers).
    path("", CitizenListView.as_view(), name="list"),
    path("<int:pk>/", CitizenDetailView.as_view(), name="detail"),
    path("<int:pk>/status/", CitizenStatusView.as_view(), name="status"),
    path("<int:pk>/approve/", CitizenApproveView.as_view(), name="approve"),
    path("<int:pk>/reject/", CitizenRejectView.as_view(), name="reject"),
]