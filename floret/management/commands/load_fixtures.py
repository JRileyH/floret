from __future__ import annotations

import shutil
from pathlib import Path

import yaml
from django.apps import apps
from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError, transaction
from django.utils.module_loading import import_string


class Command(BaseCommand):
    help = "Load development fixtures from fixtures/fixtures.yml or fixtures.json in all apps"

    def handle(self, *args, **options):
        if settings.IS_PROD:
            raise CommandError("Cannot load fixtures in production")

        total_created = 0

        for app_config in apps.get_app_configs():
            # Check for JSON fixture first
            json_path = Path(app_config.path) / "fixtures" / "fixtures.json"
            if json_path.exists():
                self.stdout.write(f"\n{app_config.name}:")

                # Copy fixture images to MEDIA_ROOT if they exist
                plant_fixture_images = Path(app_config.path) / "fixtures" / "images" / "plants"
                icon_fixture_images = Path(app_config.path) / "fixtures" / "images" / "icons"
                if plant_fixture_images.exists() and plant_fixture_images.is_dir():
                    media_plants = Path(settings.MEDIA_ROOT) / "plants"
                    media_plants.mkdir(parents=True, exist_ok=True)

                    image_count = 0
                    for image_file in plant_fixture_images.glob("*"):
                        if image_file.is_file():
                            dest = media_plants / image_file.name
                            shutil.copy2(image_file, dest)
                            image_count += 1
                if icon_fixture_images.exists() and icon_fixture_images.is_dir():
                    media_icons = Path(settings.MEDIA_ROOT) / "icons"
                    media_icons.mkdir(parents=True, exist_ok=True)

                    icon_count = 0
                    for icon_file in icon_fixture_images.glob("*"):
                        if icon_file.is_file():
                            dest = media_icons / icon_file.name
                            shutil.copy2(icon_file, dest)
                            icon_count += 1
                    if image_count > 0:
                        self.stdout.write(f"  Copied {image_count} image(s) to {media_plants}")
                    if icon_count > 0:
                        self.stdout.write(f"  Copied {icon_count} icon(s) to {media_icons}")

                self.stdout.write(f"  Loading from {json_path.name}...")
                try:
                    call_command("loaddata", str(json_path), verbosity=0)
                    self.stdout.write(
                        self.style.SUCCESS(f"  ✓ Loaded fixtures from {json_path.name}")
                    )
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"  Failed to load {json_path.name}: {e}"))
                    raise
                continue

            # Fall back to YAML fixtures
            fixtures_path = Path(app_config.path) / "fixtures" / "fixtures.yml"
            if not fixtures_path.exists():
                continue

            self.stdout.write(f"\n{app_config.name}:")

            try:
                with open(fixtures_path) as f:
                    config = yaml.safe_load(f)

                with transaction.atomic():
                    created, model_counts = self._load_app_fixtures(config)
                    total_created += created

                for model_name, count in model_counts.items():
                    if count > 0:
                        self.stdout.write(f"  ✓ {model_name}: {count}")

                self.stdout.write(self.style.SUCCESS(f"  Total: {created} fixture(s)"))

            except IntegrityError as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"  Failed! Model may have changed.\n"
                        f"  Error: {e}\n"
                        f"  Update {fixtures_path} or the factory."
                    )
                )
                raise

        if total_created == 0:
            self.stdout.write(
                self.style.WARNING(
                    "\nNo fixtures found. Create app/fixtures/fixtures.yml or fixtures.json to add fixtures."
                )
            )
        else:
            self.stdout.write(self.style.SUCCESS(f"\nTotal: {total_created} fixture(s) created"))

    def _load_app_fixtures(self, config: dict) -> tuple[int, dict[str, int]]:
        created = 0
        model_counts = {}

        for fixture in config.get("fixtures", []):
            model_path = fixture["model"]
            factory_path = fixture["factory"]
            count = fixture.get("count", 1)
            overrides = fixture.get("overrides", {})

            Model = apps.get_model(model_path)
            Factory = import_string(factory_path)

            model_name = Model.__name__
            if model_name not in model_counts:
                model_counts[model_name] = 0

            for i in range(count):
                instance_overrides = {}
                for key, value in overrides.items():
                    if isinstance(value, str) and "{n}" in value:
                        instance_overrides[key] = value.format(n=i + 1)
                    else:
                        instance_overrides[key] = value

                if hasattr(Model, "email"):
                    if "email" in instance_overrides:
                        if Model.objects.filter(email=instance_overrides["email"]).exists():
                            continue
                    else:
                        default_email = f"user{i}@example.com"
                        if Model.objects.filter(email=default_email).exists():
                            continue

                Factory(**instance_overrides)
                created += 1
                model_counts[model_name] += 1

        return created, model_counts
