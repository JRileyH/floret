from datetime import timedelta

from django.utils import timezone


def in_24_hours():
    return timezone.now() + timedelta(days=1)
