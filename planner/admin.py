from django.contrib import admin

from common.mixins.base import BaseModelAdmin, BaseTabularInline
from planner.models import Color, Garden, GardenPlant, Niche, Plant, PlantFeature, PlantPosition


class PlantPositionInline(BaseTabularInline):
    model = PlantPosition
    extra = 1
    fields = ("x", "y")


class GardenPlantInline(BaseTabularInline):
    model = GardenPlant
    extra = 1
    fields = ("plant", "color")
    autocomplete_fields = ("plant", "color")
    show_change_link = True


@admin.register(Garden)
class GardenAdmin(BaseModelAdmin):
    list_display = ("name", "user", "width", "length", "created_at")
    list_filter = ("user", "created_at")
    search_fields = ("name", "description", "user__email")
    readonly_fields = ("id", "created_at", "updated_at", "deleted_at")
    autocomplete_fields = ("user",)
    inlines = [GardenPlantInline]
    fieldsets = (
        ("Garden Info", {"fields": ("name", "user", "width", "length")}),
        ("Description", {"fields": ("description",)}),
        ("Metadata", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )


@admin.register(GardenPlant)
class GardenPlantAdmin(BaseModelAdmin):
    list_display = ("garden", "plant", "color", "get_quantity")
    list_filter = ("garden", "plant", "color")
    search_fields = ("garden__name", "plant__common_name", "color__name")
    autocomplete_fields = ("garden", "plant", "color")
    readonly_fields = ("id", "created_at", "updated_at", "deleted_at")
    inlines = [PlantPositionInline]

    def get_quantity(self, obj):
        return obj.quantity

    get_quantity.short_description = "Quantity"


@admin.register(Plant)
class PlantAdmin(BaseModelAdmin):
    list_display = (
        "common_name",
        "scientific_name",
        "niche",
        "native",
        "height",
        "spread",
    )
    list_filter = ("native", "niche", "sun", "bloom")
    search_fields = (
        "common_name",
        "scientific_name",
        "slug",
    )
    autocomplete_fields = ("niche",)
    filter_horizontal = ("features", "colors")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        ("Basic Info", {"fields": ("common_name", "scientific_name", "slug", "image")}),
        ("Characteristics", {"fields": ("sun", "bloom", "native", "niche", "height", "spread")}),
        ("Relationships", {"fields": ("features", "colors")}),
        ("Additional Info", {"fields": ("notes", "link")}),
        ("Metadata", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )


@admin.register(Niche)
class NicheAdmin(BaseModelAdmin):
    list_display = (
        "title",
        "slug",
    )
    search_fields = (
        "title",
        "slug",
    )


@admin.register(PlantFeature)
class PlantFeatureAdmin(BaseModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Color)
class ColorAdmin(BaseModelAdmin):
    list_display = (
        "name",
        "hex_code",
    )
    search_fields = (
        "name",
        "hex_code",
    )
    ordering = ("name",)


@admin.register(PlantPosition)
class PlantPositionAdmin(BaseModelAdmin):
    list_display = ("garden_plant", "x", "y", "created_at")
    list_filter = ("garden_plant__garden", "garden_plant__plant")
    search_fields = ("garden_plant__garden__name", "garden_plant__plant__common_name")
    autocomplete_fields = ("garden_plant",)
    readonly_fields = ("created_at", "updated_at")
