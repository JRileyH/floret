from hashlib import sha256
from secrets import token_urlsafe
from typing import TYPE_CHECKING

from django.contrib.auth.base_user import BaseUserManager
from django.utils import timezone

from account.enums import SecretType
from account.utils import get_client_fingerprint, get_user_agent_info
from common.mixins.base import BaseManager

if TYPE_CHECKING:
    from django.http import HttpRequest

    from account.models import Device, User


class UserManager(BaseUserManager, BaseManager):
    def _create_user(self, email, password, **kwargs) -> "User":
        if not email:
            raise ValueError("email required")
        user = self.model(email=email.lower().strip(), **kwargs)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **kwargs) -> "User":
        kwargs.setdefault("is_staff", False)
        kwargs.setdefault("is_superuser", False)
        return self._create_user(email, password, **kwargs)

    def create_superuser(self, email, password, **kwargs) -> "User":
        kwargs["is_staff"] = True
        kwargs["is_superuser"] = True
        return self._create_user(email, password, **kwargs)


class SecretManager(BaseManager):
    def create_for_password_reset(self, user: "User"):
        self.filter(
            user=user,
            secret_type=SecretType.PASSWORD_RESET,
            used_at__isnull=True,
        ).update(deleted_at=timezone.now())
        return self.create(user=user, secret_type=SecretType.PASSWORD_RESET)


class IPAddressManager(BaseManager):
    pass


class BrowserManager(BaseManager):
    pass


class DeviceManager(BaseManager):
    def get_or_create_from_request(
        self, request: "HttpRequest", user: "User"
    ) -> tuple["Device | None", bool]:
        """
        Get or create Device from request.

        Attempts to identify devices using cookie token, then hardware fingerprinting.
        Returns (None, False) for unidentifiable devices (e.g., JavaScript disabled).
        Returns (Device, True) for new devices, (Device, False) for existing.
        """
        from account.models import Browser, IPAddress

        now = timezone.now()

        # Extract client and server signals
        user_agent_info = get_user_agent_info(request)
        client_signals = get_client_fingerprint(request)

        ip_address = user_agent_info.get("ip_address")
        browser_family = user_agent_info.get("browser_family")
        os_family = user_agent_info.get("os_family")
        device_type = user_agent_info.get("device_type")
        user_agent_string = user_agent_info.get("user_agent_string")

        # Check if we have enough client signals to identify device
        # If all fingerprint fields are empty, treat as anonymous (e.g., JS disabled)
        has_client_signals = any(
            [
                client_signals.get("platform"),
                client_signals.get("webgl"),
            ]
        )

        # Check for existing device_token cookie
        device_token = request.COOKIES.get("device_token")
        if device_token:
            device = self.filter(
                user=user, device_token=device_token, deleted_at__isnull=True
            ).first()
            if device:
                self._update_device(
                    device, ip_address, browser_family, user_agent_string, now, client_signals
                )
                return device, False

        # If no client signals available, treat as anonymous device
        if not has_client_signals:
            return None, False

        # Create device fingerprint from stable hardware signals
        fingerprint_components = [
            str(user.id),
            os_family,
            device_type,
            client_signals.get("platform", ""),
            client_signals.get("webgl", ""),
        ]
        fingerprint_string = "|".join(filter(None, fingerprint_components))
        device_fingerprint = sha256(fingerprint_string.encode()).hexdigest()

        # Try to find matching device by fingerprint
        matching_devices = list(
            self.filter(
                user=user, device_fingerprint=device_fingerprint, deleted_at__isnull=True
            ).prefetch_related("ip_addresses", "browsers")
        )

        # If fingerprint matches, check if IP subnet has been used
        if matching_devices:
            for device in matching_devices:
                # Check if this IP subnet has been used before
                known_ips = set(device.ip_addresses.values_list("ip_address", flat=True))
                if ip_address in known_ips:
                    self._update_device(
                        device, ip_address, browser_family, user_agent_string, now, client_signals
                    )
                    return device, False

        # Create new device
        new_device_token = token_urlsafe(32)

        # Extract client signals
        platform = client_signals.get("platform", "")
        webgl = client_signals.get("webgl", "")

        # Extract display fields
        hardware_concurrency = client_signals.get("hardwareConcurrency")
        device_memory = client_signals.get("deviceMemory")
        screen_resolution = client_signals.get("screenResolution", "")
        browser_timezone = client_signals.get("browserTimezone", "")
        language = client_signals.get("language", "")

        device = self.create(
            user=user,
            device_token=new_device_token,
            device_fingerprint=device_fingerprint,
            os_family=os_family,
            device_type=device_type,
            platform=platform,
            gpu_vendor=webgl[:255] if webgl else "",
            hardware_concurrency=int(hardware_concurrency) if hardware_concurrency else None,
            device_memory=float(device_memory) if device_memory else None,
            screen_resolution=screen_resolution,
            browser_timezone=browser_timezone,
            language=language,
        )

        # Create initial IP and browser records
        if ip_address:
            IPAddress.objects.create(device=device, ip_address=ip_address)
        if browser_family:
            Browser.objects.create(
                device=device,
                browser_family=browser_family,
                user_agent=user_agent_string,
            )

        return device, True

    def _update_device(
        self, device, ip_address, browser_family, user_agent_string, now, client_signals=None
    ):
        """Update existing device with new access"""
        from account.models import Browser, IPAddress

        # Update device access tracking
        device.last_seen_at = now
        device.access_count = device.access_count + 1

        # Update volatile display fields if client signals provided
        update_fields = ["last_seen_at", "access_count"]
        if client_signals:
            device.screen_resolution = client_signals.get("screenResolution", "")
            device.browser_timezone = client_signals.get("browserTimezone", "")
            device.language = client_signals.get("language", "")
            update_fields.extend(["screen_resolution", "browser_timezone", "language"])

        device.save(update_fields=update_fields)

        # Track IP
        if ip_address:
            ip_record = device.ip_addresses.filter(ip_address=ip_address).first()
            if ip_record:
                ip_record.last_seen_at = now
                ip_record.access_count = ip_record.access_count + 1
                ip_record.save(update_fields=["last_seen_at", "access_count"])
            else:
                try:
                    IPAddress.objects.create(device=device, ip_address=ip_address)
                except Exception:
                    # Ignore duplicate/race condition errors
                    pass

        # Track browser
        if browser_family:
            browser_record = device.browsers.filter(browser_family=browser_family).first()
            if browser_record:
                browser_record.last_seen_at = now
                browser_record.access_count = browser_record.access_count + 1
                browser_record.user_agent = user_agent_string  # Update to latest UA
                browser_record.save(update_fields=["last_seen_at", "access_count", "user_agent"])
            else:
                try:
                    Browser.objects.create(
                        device=device,
                        browser_family=browser_family,
                        user_agent=user_agent_string,
                    )
                except Exception:
                    # Ignore duplicate/race condition errors
                    pass
