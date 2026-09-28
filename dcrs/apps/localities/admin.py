from django.contrib import admin

from .models import District, Mtaa, Region, Ward


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    search_fields = ("name",)
    list_display = ("name",)


@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    search_fields = ("name", "region__name")
    list_display = ("name", "region")
    list_filter = ("region",)


@admin.register(Ward)
class WardAdmin(admin.ModelAdmin):
    search_fields = ("name", "district__name")
    list_display = ("name", "district")
    list_filter = ("district__region",)


@admin.register(Mtaa)
class MtaaAdmin(admin.ModelAdmin):
    search_fields = ("name", "ward__name")
    list_display = ("name", "ward")
    list_filter = ("ward__district",)
