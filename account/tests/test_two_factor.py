"""
Unit tests for 2FA device tracking and management.

Focus: High-impact tests for critical logic paths and edge cases.
"""

from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.test import RequestFactory

from account.models import Device

User = get_user_model()


@pytest.fixture
def user(db):
    """Create a test user."""
    return User.objects.create_user(email="test@example.com", password="testpass123")  # type: ignore[attr-defined]


@pytest.fixture
def request_factory():
    """Django request factory."""
    return RequestFactory()


@pytest.fixture
def mock_request(request_factory, user):
    """Create a mock request with common headers."""
    request = request_factory.get("/")
    request.user = user
    request.COOKIES = {}
    request.META = {
        "HTTP_USER_AGENT": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "REMOTE_ADDR": "192.168.1.100",
    }
    return request


class TestDeviceFingerprinting:
    """Test critical device fingerprinting logic."""

    @pytest.mark.django_db
    @patch("account.managers.get_user_agent_info")
    @patch("account.managers.get_client_fingerprint")
    def test_anonymous_device_no_client_signals(
        self, mock_fingerprint, mock_ua_info, user, mock_request
    ):
        # Simulate no client-side JavaScript signals
        mock_fingerprint.return_value = {"platform": "", "webgl": ""}
        mock_ua_info.return_value = {
            "ip_address": "192.168.1.100",
            "browser_family": "Chrome",
            "os_family": "Mac OS X",
            "device_type": "Desktop",
            "user_agent_string": "Mozilla/5.0...",
        }

        device, created = Device.objects.get_or_create_from_request(mock_request, user)

        # Should return None for anonymous devices
        assert device is None
        assert created is False
        assert Device.objects.filter(user=user).count() == 0

    @pytest.mark.django_db
    @patch("account.managers.get_user_agent_info")
    @patch("account.managers.get_client_fingerprint")
    def test_device_fingerprint_collision_different_ips(
        self, mock_fingerprint, mock_ua_info, user, mock_request
    ):
        # First device from home network
        mock_fingerprint.return_value = {"platform": "MacIntel", "webgl": "Apple M1"}
        mock_ua_info.return_value = {
            "ip_address": "192.168.1.100",
            "browser_family": "Chrome",
            "os_family": "Mac OS X",
            "device_type": "Desktop",
            "user_agent_string": "Mozilla/5.0...",
        }

        device1, created1 = Device.objects.get_or_create_from_request(mock_request, user)
        assert created1 is True
        assert device1 is not None

        # Same device from work network (different IP)
        mock_ua_info.return_value["ip_address"] = "10.0.0.50"
        device2, created2 = Device.objects.get_or_create_from_request(mock_request, user)

        # Should create a new device due to unknown IP
        assert created2 is True
        assert device2.id != device1.id
        assert Device.objects.filter(user=user).count() == 2

    @pytest.mark.django_db
    @patch("account.managers.get_user_agent_info")
    @patch("account.managers.get_client_fingerprint")
    def test_device_fingerprint_same_ip_network_reuses_device(
        self, mock_fingerprint, mock_ua_info, user, mock_request
    ):
        mock_fingerprint.return_value = {"platform": "MacIntel", "webgl": "Apple M1"}
        mock_ua_info.return_value = {
            "ip_address": "192.168.1.100",
            "browser_family": "Chrome",
            "os_family": "Mac OS X",
            "device_type": "Desktop",
            "user_agent_string": "Mozilla/5.0...",
        }

        # Create initial device
        device1, created1 = Device.objects.get_or_create_from_request(mock_request, user)
        assert created1 is True
        initial_access_count = device1.access_count

        # Access from same IP
        device2, created2 = Device.objects.get_or_create_from_request(mock_request, user)

        assert created2 is False
        assert device2.id == device1.id
        assert Device.objects.filter(user=user).count() == 1

        # Should increment access count
        device2.refresh_from_db()
        assert device2.access_count == initial_access_count + 1

    @pytest.mark.django_db
    @patch("account.managers.get_user_agent_info")
    @patch("account.managers.get_client_fingerprint")
    def test_device_token_cookie_takes_precedence(
        self, mock_fingerprint, mock_ua_info, user, mock_request
    ):
        mock_fingerprint.return_value = {"platform": "MacIntel", "webgl": "Apple M1"}
        mock_ua_info.return_value = {
            "ip_address": "192.168.1.100",
            "browser_family": "Chrome",
            "os_family": "Mac OS X",
            "device_type": "Desktop",
            "user_agent_string": "Mozilla/5.0...",
        }

        # Create initial device
        device1, _ = Device.objects.get_or_create_from_request(mock_request, user)
        device_token = device1.device_token

        # Simulate cookie being set
        mock_request.COOKIES["device_token"] = device_token

        # Change fingerprint signals (e.g., GPU driver update)
        mock_fingerprint.return_value = {"platform": "MacIntel", "webgl": "Apple M2"}

        device2, created2 = Device.objects.get_or_create_from_request(mock_request, user)

        # Should reuse same device via cookie
        assert created2 is False
        assert device2.id == device1.id
        assert Device.objects.filter(user=user).count() == 1


class TestDeviceTrustAndBlocking:
    """Test device trust and blocking state changes."""

    @pytest.mark.django_db
    def test_blocking_device_untrusts_it(self, user):
        device = Device.objects.create(
            user=user,
            device_token="test_token",
            device_fingerprint="test_fp",
            os_family="Mac OS X",
            device_type="Desktop",
            trusted=True,
            blocked=False,
        )

        # Simulate blocking (from view logic)
        device.blocked = True
        device.trusted = False
        device.save()

        assert device.blocked is True
        assert device.trusted is False

    @pytest.mark.django_db
    def test_device_filtering_by_trust_state(self, user):
        """
        CRITICAL: Device list filtering must correctly separate trusted/untrusted/blocked.
        Bug impact: Could show devices in wrong sections of UI.
        """
        # Create devices in different states
        trusted = Device.objects.create(
            user=user,
            device_token="trusted_token",
            device_fingerprint="trusted_fp",
            os_family="Mac OS X",
            device_type="Desktop",
            trusted=True,
            blocked=False,
        )

        untrusted = Device.objects.create(
            user=user,
            device_token="untrusted_token",
            device_fingerprint="untrusted_fp",
            os_family="Windows",
            device_type="Desktop",
            trusted=False,
            blocked=False,
        )

        blocked = Device.objects.create(
            user=user,
            device_token="blocked_token",
            device_fingerprint="blocked_fp",
            os_family="Linux",
            device_type="Desktop",
            trusted=False,
            blocked=True,
        )

        # Simulate view filtering logic
        devices = Device.objects.filter(user=user, deleted_at__isnull=True)
        trusted_devices = devices.filter(trusted=True, blocked=False)
        untrusted_devices = devices.filter(trusted=False, blocked=False)
        blocked_devices = devices.filter(blocked=True)

        assert list(trusted_devices) == [trusted]
        assert list(untrusted_devices) == [untrusted]
        assert list(blocked_devices) == [blocked]
