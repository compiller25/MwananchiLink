from django.http import JsonResponse
from django.views.decorators.http import require_GET

from .models import District, Mtaa, Ward


@require_GET
def districts_by_region(request, region_id):
    districts = District.objects.filter(region_id=region_id).order_by("name")
    return JsonResponse(
        {"results": [{"id": district.id, "name": district.name} for district in districts]}
    )


@require_GET
def wards_by_district(request, district_id):
    wards = Ward.objects.filter(district_id=district_id).order_by("name")
    return JsonResponse({"results": [{"id": ward.id, "name": ward.name} for ward in wards]})


@require_GET
def mitaa_by_ward(request, ward_id):
    mitaa = Mtaa.objects.filter(ward_id=ward_id).order_by("name")
    return JsonResponse({"results": [{"id": item.id, "name": item.name} for item in mitaa]})
