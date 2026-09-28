"""API v1 URL configuration — the JSON surface for the React + TypeScript frontend.

Each include maps to one Django app, mirroring the template URL layout so the SPA can
replace the server-rendered pages one screen at a time.
"""
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from apps.reports.api_views import PublicStatsView

urlpatterns = [
    path("auth/", include("apps.accounts.api_urls")),
    path("localities/", include("apps.localities.api_urls")),
    path("citizens/", include("apps.citizens.api_urls")),
    path("issues/", include("apps.issues.api_urls")),
    path("notifications/", include("apps.notifications.api_urls")),
    path("sms/", include("apps.notifications.sms_api_urls")),
    path("reports/", include("apps.reports.api_urls")),
    # Public (unauthenticated) — counters for the landing page.
    path("public/stats/", PublicStatsView.as_view(), name="public_stats"),
    # OpenAPI schema + browsable docs (drf-spectacular).
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="docs"),
]