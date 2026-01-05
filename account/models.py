from __future__ import annotations

from secrets import token_urlsafe
from typing import ClassVar
from urllib.parse import urlencode
from uuid import UUID

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

from account.enums import SecretType
from account.managers import (
    BrowserManager,
    DeviceManager,
    IPAddressManager,
    SecretManager,
    UserManager,
)
from common.mixins import base as base_mixins
from common.utils.time import in_24_hours


class User(AbstractUser, base_mixins.BaseModel):
    EMAIL_FIELD = "email"
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    email = models.EmailField(null=False, unique=True)
    email_verified_at = models.DateTimeField(blank=True, null=True)

    mfa_enabled = models.BooleanField(default=False)

    username = None  # type: ignore[assignment]

    objects: ClassVar[UserManager] = UserManager()

    class Meta:
        db_table = "user"

    def __str__(self):
        return self.email


class Secret(base_mixins.BaseModel):
    expires_at = models.DateTimeField(default=in_24_hours)
    used_at = models.DateTimeField(blank=True, null=True)
    code = models.CharField(default=token_urlsafe, max_length=255, unique=True)
    user = models.ForeignKey["User"](
        "account.User",
        on_delete=models.CASCADE,
        related_name="+",
    )
    secret_type = models.CharField(
        max_length=32, choices=SecretType.choices, default=SecretType.PASSWORD_RESET
    )

    user_id: UUID

    objects: ClassVar[SecretManager] = SecretManager()

    @property
    def magic_link(self) -> str:
        params = urlencode({"secret": self.code})
        return f"{settings.BASE_URL}/account/magic_link/?{params}"

    class Meta:
        db_table = "secret"

    def __str__(self):
        return f"Secret: {self.user_id} {self.id}"


class Device(base_mixins.BaseModel):
    user = models.ForeignKey(
        "User",
        on_delete=models.CASCADE,
        related_name="devices",
    )

    # Device identification
    device_token = models.CharField(max_length=255, unique=True, db_index=True)
    device_fingerprint = models.CharField(max_length=512, db_index=True)
    device_name = models.CharField(max_length=255, blank=True)  # User can customize

    # Device characteristics (used in fingerprint)
    os_family = models.CharField(max_length=128)
    device_type = models.CharField(max_length=128)
    platform = models.CharField(max_length=64, blank=True)  # MacIntel, Win32, etc.
    gpu_vendor = models.CharField(
        max_length=255, blank=True
    )  # Normalized vendor (Apple, NVIDIA, etc.)

    # Display-only fields (not used in fingerprint)
    hardware_concurrency = models.IntegerField(null=True, blank=True)  # CPU cores
    device_memory = models.FloatField(null=True, blank=True)  # RAM in GB
    screen_resolution = models.CharField(max_length=32, blank=True)
    browser_timezone = models.CharField(max_length=64, blank=True)
    language = models.CharField(max_length=16, blank=True)

    first_seen_at = models.DateTimeField(default=timezone.now, editable=False, blank=True)
    last_seen_at = models.DateTimeField(default=timezone.now, editable=True, blank=True)
    access_count = models.PositiveIntegerField(default=1)

    trusted = models.BooleanField(default=False)
    blocked = models.BooleanField(default=False)

    user_id: UUID
    ip_addresses: models.Manager[IPAddress]
    browsers: models.Manager[Browser]

    objects: ClassVar[DeviceManager] = DeviceManager()

    @property
    def ip_address(self) -> str:
        ip_address = self.ip_addresses.order_by("-last_seen_at").first()
        if ip_address:
            return ip_address.ip_address
        return "Unknown"

    @property
    def display_name(self) -> str:
        """Human-readable device name"""
        if self.device_name:
            return self.device_name
        return f"{self.os_family} {self.device_type}"

    class Meta:
        db_table = "device"
        ordering = ["-last_seen_at"]

    def __str__(self):
        return f"{self.user.email}: {self.display_name}"


class Browser(base_mixins.BaseModel):
    """Track which browsers have been used on this device"""

    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name="browsers")
    browser_family = models.CharField(max_length=128)
    user_agent = models.CharField(max_length=512)
    access_count = models.PositiveIntegerField(default=1)
    first_seen_at = models.DateTimeField(default=timezone.now, editable=False, blank=True)
    last_seen_at = models.DateTimeField(default=timezone.now, editable=True, blank=True)

    device_id: UUID

    objects: ClassVar[BrowserManager] = BrowserManager()

    class Meta:
        db_table = "browser"
        unique_together = [["device", "browser_family"]]
        ordering = ["-last_seen_at"]

    def __str__(self):
        return self.browser_family


class IPAddress(base_mixins.BaseModel):
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name="ip_addresses")
    ip_address = models.GenericIPAddressField(db_index=True)
    access_count = models.PositiveIntegerField(default=1)
    first_seen_at = models.DateTimeField(default=timezone.now, editable=False, blank=True)
    last_seen_at = models.DateTimeField(default=timezone.now, editable=True, blank=True)
    blocked = models.BooleanField(default=False)

    device_id: UUID

    objects: ClassVar[IPAddressManager] = IPAddressManager()

    class Meta:
        db_table = "ip_address"
        unique_together = [["device", "ip_address"]]
        ordering = ["-last_seen_at"]

    def __str__(self):
        return self.ip_address
