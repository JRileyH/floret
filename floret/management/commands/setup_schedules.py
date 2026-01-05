import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django_q.models import Schedule


class Command(BaseCommand):
    help = "Set up Django-Q2 scheduled tasks from JSON configuration"

    def handle(self, *args, **options):
        """Load schedules from JSON and sync to database."""
        all_schedules = []
        for app in settings.INTERNAL_APPS:
            # Look for tasks.json in app directory
            try:
                app_path = Path(settings.BASE_DIR) / app.replace(".", "/")
                tasks_json = app_path / "tasks.json"

                if tasks_json.exists():
                    with open(tasks_json) as f:
                        config = json.load(f)
                        schedules = config.get("schedules", [])
                        all_schedules.extend(schedules)
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"📖 Loaded {len(schedules)} schedule(s) from {app}/tasks.json"
                            )
                        )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"❌ Error loading tasks.json from {app}: {e}")
                )

        if not all_schedules:
            self.stdout.write(self.style.WARNING("⚠️  No task schedules found"))
            return

        created_count = 0
        updated_count = 0

        schedule_type_map = {
            "once": Schedule.ONCE,
            "hourly": Schedule.HOURLY,
            "daily": Schedule.DAILY,
            "weekly": Schedule.WEEKLY,
            "monthly": Schedule.MONTHLY,
            "quarterly": Schedule.QUARTERLY,
            "yearly": Schedule.YEARLY,
            "cron": Schedule.CRON,
        }

        for schedule_data in all_schedules:
            schedule_type_str = schedule_data.get("schedule_type", "daily").lower()
            schedule_type = schedule_type_map.get(schedule_type_str, Schedule.DAILY)

            defaults = {
                "name": schedule_data["name"],
                "schedule_type": schedule_type,
                "repeats": schedule_data.get("repeats", -1),
            }

            # Add optional fields if present
            if "minutes" in schedule_data:
                defaults["minutes"] = schedule_data["minutes"]
            if "cron" in schedule_data:
                defaults["cron"] = schedule_data["cron"]

            schedule, created = Schedule.objects.update_or_create(
                func=schedule_data["func"], defaults=defaults
            )

            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"✓ Created schedule: {schedule.name}"))
            else:
                updated_count += 1
                self.stdout.write(self.style.WARNING(f"○ Updated schedule: {schedule.name}"))

        self.stdout.write(
            self.style.SUCCESS(
                f"\n✨ Setup complete: {created_count} created, {updated_count} updated"
            )
        )
