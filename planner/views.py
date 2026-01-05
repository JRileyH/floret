import json

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET, require_POST

from planner.models import (
    BloomOptions,
    Color,
    Garden,
    GardenPlant,
    Niche,
    Plant,
    PlantFeature,
    PlantPosition,
    SunOptions,
)


def index(request):
    context = {
        "niches": Niche.objects.all(),
        "colors": Color.objects.all(),
        "features": PlantFeature.objects.all(),
    }
    return render(request, "index.html", context=context)


def garden_summary(request):
    """Garden Summary View - Displays analytics for selected plants."""
    return render(request, "garden_summary.html")


def _validate_filters(raw_filters):
    """
    Validate and sanitize filter values to prevent injection attacks.

    Args:
        raw_filters: Dictionary of raw filter values from JSON

    Returns:
        Dictionary of validated and sanitized filter values
    """
    if not isinstance(raw_filters, dict):
        return {}

    validated = {}

    # String fields - limit length and sanitize
    if "search" in raw_filters and isinstance(raw_filters["search"], str):
        validated["search"] = raw_filters["search"][:100].strip()

    # UUID fields - validate format
    if "niche" in raw_filters and raw_filters["niche"]:
        try:
            # Convert to string and validate it's a valid UUID format
            niche_str = str(raw_filters["niche"])
            if len(niche_str) == 36:  # UUID length
                validated["niche"] = niche_str
        except (ValueError, AttributeError):
            pass

    # Choice fields - validate against allowed values
    sun_values = dict(SunOptions.choices).keys()
    if "sun" in raw_filters and raw_filters["sun"] in sun_values:
        validated["sun"] = raw_filters["sun"]

    bloom_values = dict(BloomOptions.choices).keys()
    if "bloom" in raw_filters and raw_filters["bloom"] in bloom_values:
        validated["bloom"] = raw_filters["bloom"]

    # Boolean fields
    if "native" in raw_filters:
        validated["native"] = bool(raw_filters.get("native"))

    if "buyable" in raw_filters:
        validated["buyable"] = bool(raw_filters.get("buyable"))

    # Numeric fields with range validation
    for field in ["heightMin", "heightMax", "spreadMin", "spreadMax"]:
        if field in raw_filters:
            try:
                value = float(raw_filters[field])
                if 0 <= value <= 100:  # Reasonable range for plants
                    validated[field] = value
            except (ValueError, TypeError):
                pass

    # Array fields with validation and size limits
    if "colors" in raw_filters and isinstance(raw_filters["colors"], list):
        validated["colors"] = [
            str(c)
            for c in raw_filters["colors"][:20]  # Limit array size
            if c  # Filter out empty values
        ]

    if "features" in raw_filters and isinstance(raw_filters["features"], list):
        validated["features"] = [
            str(f)
            for f in raw_filters["features"][:20]  # Limit array size
            if f  # Filter out empty values
        ]

    return validated


def plant_list(request):
    """Partial View - Returns filtered and paginated list of plants."""
    # Start with base queryset
    plants = (
        Plant.objects.filter(deleted_at__isnull=True)
        .select_related("niche")
        .prefetch_related("colors", "features")
    )

    # Decode and validate filters from JSON parameter
    filters_json = request.GET.get("filters", "{}")
    try:
        raw_filters = json.loads(filters_json)
        filters = _validate_filters(raw_filters)
    except (json.JSONDecodeError, ValueError):
        filters = {}

    # Apply filters
    if filters.get("search"):
        search = filters["search"]
        plants = plants.filter(
            Q(common_name__icontains=search) | Q(scientific_name__icontains=search)
        )

    if filters.get("niche"):
        plants = plants.filter(niche_id=filters["niche"])

    if filters.get("sun"):
        plants = plants.filter(sun__contains=[filters["sun"]])

    if filters.get("bloom"):
        plants = plants.filter(bloom__contains=[filters["bloom"]])

    if filters.get("native"):
        plants = plants.filter(native=True)

    if filters.get("buyable"):
        plants = plants.exclude(link="")

    if filters.get("heightMin") is not None:
        plants = plants.filter(height__gte=filters["heightMin"])

    if filters.get("heightMax") is not None:
        plants = plants.filter(height__lte=filters["heightMax"])

    if filters.get("spreadMin") is not None:
        plants = plants.filter(spread__gte=filters["spreadMin"])

    if filters.get("spreadMax") is not None:
        plants = plants.filter(spread__lte=filters["spreadMax"])

    if filters.get("colors"):
        plants = plants.filter(colors__id__in=filters["colors"]).distinct()

    if filters.get("features"):
        # AND logic: plant must have ALL selected features
        # Use annotation to count matching features and filter efficiently
        from django.db.models import Count

        feature_ids = filters["features"]
        plants = (
            plants.filter(features__id__in=feature_ids)
            .annotate(matching_features=Count("features", distinct=True))
            .filter(matching_features=len(feature_ids))
        )

    # Pagination
    page_number = request.GET.get("page", 1)
    paginator = Paginator(plants, 24)  # 24 plants per page
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "partials/plant_list.html",
        context={
            "plants": page_obj,
            "page_obj": page_obj,
            "total_count": paginator.count,
        },
    )


# Garden Management API Endpoints


@login_required
@require_POST
def save_garden(request):
    """
    Save a garden from localStorage to the database.

    Expects JSON body:
    {
        "name": "Garden Name",
        "width": 10.5,
        "length": 8.0,
        "description": "Optional description",
        "plants": [
            {
                "plant_id": "uuid",
                "color_id": "uuid",
                "positions": [[2.5, 1.0], [3.5, 1.0], [4.5, 2.0]]
            }
        ]
    }

    Returns: {"success": true, "garden_id": "uuid"}
    """
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)

    # Validate required fields
    required = ["name", "width", "length", "plants"]
    if not all(field in data for field in required):
        return JsonResponse({"success": False, "error": "Missing required fields"}, status=400)

    try:
        with transaction.atomic():
            # Create the garden
            garden = Garden.objects.create(
                user=request.user,
                name=data["name"],
                width=float(data["width"]),
                length=float(data["length"]),
                description=data.get("description", ""),
            )

            # Create garden plants with positions
            for plant_data in data["plants"]:
                # Create the GardenPlant (plant/color combination)
                garden_plant = GardenPlant.objects.create(
                    garden=garden,
                    plant_id=plant_data["plant_id"],
                    color_id=plant_data["color_id"],
                )

                # Create individual PlantPosition records for each coordinate
                positions = plant_data.get("positions", [])
                for pos in positions:
                    if isinstance(pos, (list, tuple)) and len(pos) == 2:
                        PlantPosition.objects.create(
                            garden_plant=garden_plant,
                            x=float(pos[0]),
                            y=float(pos[1]),
                        )

            return JsonResponse({"success": True, "garden_id": str(garden.id)}, status=201)
    except (ValueError, KeyError, Plant.DoesNotExist, Color.DoesNotExist) as e:
        return JsonResponse({"success": False, "error": f"Invalid data: {str(e)}"}, status=400)


@login_required
@require_GET
def load_garden(request, garden_id):
    """
    Load a garden from the database and return as JSON.

    Returns:
    {
        "name": "Garden Name",
        "width": 10.5,
        "length": 8.0,
        "description": "Description",
        "plants": [
            {
                "plant_id": "uuid",
                "color_id": "uuid",
                "positions": [[2.5, 1.0], [3.5, 1.0]]
            }
        ]
    }
    """
    garden = get_object_or_404(Garden, id=garden_id, user=request.user)

    plants_data = [
        {
            "plant_id": str(gp.plant.id),
            "color_id": str(gp.color.id),
            "positions": [[pos.x, pos.y] for pos in gp.positions.all()],
        }
        for gp in garden.garden_plants.select_related("plant", "color").prefetch_related(
            "positions"
        )
    ]

    return JsonResponse(
        {
            "name": garden.name,
            "width": garden.width,
            "length": garden.length,
            "description": garden.description,
            "plants": plants_data,
        }
    )


@login_required
@require_GET
def list_gardens(request):
    """
    List all gardens for the authenticated user.

    Returns:
    {
        "gardens": [
            {
                "id": "uuid",
                "name": "Garden Name",
                "created_at": "2026-01-05T12:00:00Z",
                "plant_count": 5
            }
        ]
    }
    """
    gardens = (
        Garden.objects.filter(user=request.user)
        .annotate(plant_count=Count("garden_plants"))
        .order_by("-created_at")
    )

    gardens_data = [
        {
            "id": str(garden.id),
            "name": garden.name,
            "created_at": garden.created_at.isoformat(),
            "plant_count": garden.plant_count,
        }
        for garden in gardens
    ]

    return JsonResponse({"gardens": gardens_data})


@require_POST
def get_garden_plants(request):
    """
    Fetch plant details for garden summary.

    Expects JSON body:
    {
        "plants": [
            {"plant_id": "uuid", "color_id": "uuid"},
            ...
        ]
    }

    Returns plant details with color, height, bloom, features, niche, native status.
    """
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)

    plant_selections = data.get("plants", [])
    results = []

    for selection in plant_selections:
        plant_id = selection.get("plant_id")
        color_id = selection.get("color_id")

        try:
            plant = (
                Plant.objects.select_related("niche")
                .prefetch_related("features", "colors")
                .get(id=plant_id)
            )
            color = Color.objects.get(id=color_id)

            results.append(
                {
                    "plant_id": str(plant.id),
                    "color_id": str(color.id),
                    "common_name": plant.common_name,
                    "scientific_name": plant.scientific_name,
                    "height": plant.height,
                    "bloom": plant.bloom,
                    "native": plant.native,
                    "niche_id": str(plant.niche.id) if plant.niche else None,
                    "niche_name": plant.niche.title if plant.niche else None,
                    "color_hex": color.hex_code,
                    "color_name": color.name,
                    "features": [
                        {"id": str(f.id), "name": f.name, "icon": f.icon.url if f.icon else None}
                        for f in plant.features.all()
                    ],
                }
            )
        except (Plant.DoesNotExist, Color.DoesNotExist):
            continue

    return JsonResponse({"success": True, "plants": results})
