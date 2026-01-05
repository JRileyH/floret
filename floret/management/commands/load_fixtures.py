from __future__ import annotations

from pathlib import Path

import yaml
from django.apps import apps
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError, transaction
from django.utils.module_loading import import_string


class Command(BaseCommand):
    help = "Load development fixtures from fixtures/fixtures.yml in all apps"

    def handle(self, *args, **options):
        if settings.IS_PROD:
            raise CommandError("Cannot load fixtures in production")

        total_created = 0

        for app_config in apps.get_app_configs():
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
                    "\nNo fixtures found. Create app/fixtures/fixtures.yml to add fixtures."
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
