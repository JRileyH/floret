"""
Account app background tasks.

All tasks are configured in account/tasks.json.
"""

import logging
from datetime import timedelta

from django.utils import timezone

from account.constants import STALE_DEVICE_THRESHOLD_DAYS
from account.models import Device

logger = logging.getLogger(__name__)


def remove_stale_devices() -> str:
    if STALE_DEVICE_THRESHOLD_DAYS < 0:
        logger.info("Stale device removal is disabled.")
        return "Stale device removal is disabled."
    now = timezone.now()
    stale_devices = Device.objects.filter(
        trusted=False,
        blocked=False,
        last_seen_at__lt=now - timedelta(days=STALE_DEVICE_THRESHOLD_DAYS),
    )
    stale_devices_count = stale_devices.count()
    if stale_devices_count > 0:
        logger.info(f"Removing {stale_devices_count} stale devices.")
        stale_devices.delete()
    return f"Removed {stale_devices_count} stale devices."
