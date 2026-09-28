from django.urls import path

from .api_views import (
    DistrictsByRegionView,
    MitaaByWardView,
    RegionListView,
    WardListView,
    WardsByDistrictView,
)

app_name = "localities_api"

urlpatterns = [
    path("regions/", RegionListView.as_view(), name="regions"),
    path("regions/<int:region_id>/districts/", DistrictsByRegionView.as_view(), name="districts"),
    path("districts/<int:district_id>/wards/", WardsByDistrictView.as_view(), name="wards"),
    path("wards/", WardListView.as_view(), name="ward_list"),
    path("wards/<int:ward_id>/mitaa/", MitaaByWardView.as_view(), name="mitaa"),
]