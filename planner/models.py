from django.contrib.postgres.fields import ArrayField
from django.db import models

from common.mixins import base as base_mixins


class SunOptions(models.TextChoices):
    FULL_SUN = "full", "Full Sun"
    PARTIAL_SUN = "partial", "Partial Sun"
    SHADE = "shade", "Shade"


class BloomOptions(models.TextChoices):
    JANUARY = "jan", "January"
    FEBRUARY = "feb", "February"
    MARCH = "mar", "March"
    APRIL = "apr", "April"
    MAY = "may", "May"
    JUNE = "jun", "June"
    JULY = "jul", "July"
    AUGUST = "aug", "August"
    SEPTEMBER = "sep", "September"
    OCTOBER = "oct", "October"
    NOVEMBER = "nov", "November"
    DECEMBER = "dec", "December"


class Niche(base_mixins.BaseModel):
    slug = models.SlugField(max_length=100, unique=True)
    icon = models.ImageField(upload_to="icons/", blank=True, null=True)
    title = models.CharField(max_length=100, unique=True)
    subtitle = models.CharField(max_length=150, blank=True)
    role = models.TextField(blank=True)

    def __str__(self):
        return self.title


class Plant(base_mixins.BaseModel):
    slug = models.SlugField(max_length=255, unique=True)
    common_name = models.CharField(max_length=255)
    scientific_name = models.CharField(max_length=255, unique=True)
    image = models.ImageField(upload_to="plants/", blank=True, null=True)
    sun = ArrayField(
        base_field=models.CharField(choices=SunOptions.choices, max_length=20),
        blank=True,
        default=list,
    )
    bloom = ArrayField(
        base_field=models.CharField(choices=BloomOptions.choices, max_length=20),
        blank=True,
        default=list,
    )
    native = models.BooleanField(default=True)
    features = models.ManyToManyField("PlantFeature", related_name="plants", blank=True)
    notes = models.TextField(blank=True)
    link = models.URLField(blank=True)
    height = models.FloatField(help_text="Height in feet", blank=True, null=True)
    spread = models.FloatField(help_text="Plant spacing in feet", blank=True, null=True)
    colors = models.ManyToManyField("Color", related_name="plants", blank=True)
    niche = models.ForeignKey(
        "Niche",
        on_delete=models.CASCADE,
        related_name="plants",
        blank=True,
        null=True,
    )

    def __str__(self):
        return self.common_name


class PlantFeature(base_mixins.BaseModel):
    icon = models.ImageField(upload_to="icons/", blank=True, null=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Color(base_mixins.BaseModel):
    name = models.CharField(max_length=100, unique=True)
    hex_code = models.CharField(max_length=7, unique=True)

    def __str__(self):
        return self.name


class Garden(base_mixins.BaseModel):
    """A garden design/plan created by a user."""

    name = models.CharField(max_length=200)
    width = models.FloatField(help_text="Garden width in feet")
    length = models.FloatField(help_text="Garden length in feet")
    description = models.TextField(blank=True)
    user = models.ForeignKey(
        "account.User",
        on_delete=models.CASCADE,
        related_name="gardens",
    )

    def __str__(self):
        return f"{self.name} ({self.user.email})"


class GardenPlant(base_mixins.BaseModel):
    """A plant selection within a garden with specific color."""

    garden = models.ForeignKey(Garden, on_delete=models.CASCADE, related_name="garden_plants")
    plant = models.ForeignKey(Plant, on_delete=models.CASCADE)
    color = models.ForeignKey(Color, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("garden", "plant", "color")

    @property
    def quantity(self):
        """Computed quantity based on number of positions."""
        return self.positions.count()

    def __str__(self):
        return f"{self.plant.common_name} ({self.color.name}) in {self.garden.name}"


class PlantPosition(base_mixins.BaseModel):
    """Individual plant instance with specific position in a garden."""

    garden_plant = models.ForeignKey(
        GardenPlant,
        on_delete=models.CASCADE,
        related_name="positions",
    )
    x = models.FloatField(help_text="X coordinate in feet from origin")
    y = models.FloatField(help_text="Y coordinate in feet from origin")

    class Meta:
        indexes = [
            models.Index(fields=["garden_plant", "x", "y"]),
        ]

    def __str__(self):
        return f"{self.garden_plant.plant.common_name} at ({self.x}, {self.y})"
