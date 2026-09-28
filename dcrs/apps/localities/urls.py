from django.urls import path

from .views import districts_by_region, mitaa_by_ward, wards_by_district

app_name = "localities"

urlpatterns = [
    path("regions/<int:region_id>/districts/", districts_by_region, name="districts_by_region"),
    path("districts/<int:district_id>/wards/", wards_by_district, name="wards_by_district"),
    path("wards/<int:ward_id>/mitaa/", mitaa_by_ward, name="mitaa_by_ward"),
]
