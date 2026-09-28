"""Locality cascade endpoints for the SPA's Region → District → Ward → Mtaa pickers.

These replace the hand-rolled ``JsonResponse`` views in ``apps/localities/views.py`` (which
are still mounted at ``/api/localities/`` for the Django templates' JS). The response shape
is kept identical — ``{"results": [{"id": ..., "name": ...}]}`` — because the cascade only
needs id/name pairs and this keeps both consumers interchangeable.

There was no ``regions`` list endpoint before; without it the SPA cannot populate the first
dropdown, so ``RegionListView`` is new.
"""
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import District, Mtaa, Region, Ward
from .serializers import MtaaSerializer, RegionSerializer, WardSerializer, DistrictSerializer


def _results(serializer):
    return Response({"results": serializer.data})


class RegionListView(APIView):
    """GET /api/v1/localities/regions/ — cascade root (public: used by the register form)."""

    permission_classes = [AllowAny]

    def get(self, request):
        regions = Region.objects.all().order_by("name")
        return _results(RegionSerializer(regions, many=True))


class DistrictsByRegionView(APIView):
    """GET /api/v1/localities/regions/{region_id}/districts/"""

    permission_classes = [AllowAny]

    def get(self, request, region_id):
        districts = District.objects.filter(region_id=region_id).order_by("name")
        return _results(DistrictSerializer(districts, many=True))


class WardsByDistrictView(APIView):
    """GET /api/v1/localities/districts/{district_id}/wards/"""

    permission_classes = [AllowAny]

    def get(self, request, district_id):
        wards = Ward.objects.filter(district_id=district_id).order_by("name")
        return _results(WardSerializer(wards, many=True))


class MitaaByWardView(APIView):
    """GET /api/v1/localities/wards/{ward_id}/mitaa/"""

    permission_classes = [AllowAny]

    def get(self, request, ward_id):
        mitaa = Mtaa.objects.filter(ward_id=ward_id).order_by("name")
        return _results(MtaaSerializer(mitaa, many=True))


class WardListView(APIView):
    """GET /api/v1/localities/wards/ — staff pickers (e.g. SMS broadcast, issue filters)."""

    def get(self, request):
        wards = Ward.objects.select_related("district").order_by("district__name", "name")
        return Response(
            {
                "results": [
                    {
                        "id": ward.pk,
                        "name": str(ward),
                        "ward": ward.name,
                        "district": ward.district_id,
                    }
                    for ward in wards
                ]
            }
        )