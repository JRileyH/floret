from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from account.models import Browser, Device, IPAddress, Secret, User
from common.mixins.base import BaseModelAdmin, BaseTabularInline


class SecretInline(BaseTabularInline):
    model = Secret
    fk_name = "user"
    fields = (
        "magic_link",
        "secret_type",
        "expires_at",
        "used_at",
        "created_at",
        "updated_at",
        "deleted_at",
        "code",
    )
    readonly_fields = (
        "magic_link",
        "secret_type",
        "expires_at",
        "used_at",
        "created_at",
        "updated_at",
        "deleted_at",
        "code",
    )
    extra = 0

    def has_add_permission(self, request, obj):
        return False


class DeviceInline(BaseTabularInline):
    model = Device
    fk_name = "user"
    fields = (
        "display_name",
        "device_token",
        "os_family",
        "device_type",
        "platform",
        "trusted",
        "blocked",
        "last_seen_at",
        "access_count",
    )
    readonly_fields = (
        "display_name",
        "device_token",
        "device_fingerprint",
        "os_family",
        "device_type",
        "platform",
        "hardware_concurrency",
        "device_memory",
        "gpu_vendor",
        "screen_resolution",
        "browser_timezone",
        "language",
        "last_seen_at",
        "access_count",
        "created_at",
        "updated_at",
        "deleted_at",
    )
    extra = 0

    def has_add_permission(self, request, obj):
        return False


class IpAddressInline(BaseTabularInline):
    model = IPAddress
    fk_name = "device"
    fields = (
        "ip_address",
        "first_seen_at",
        "last_seen_at",
        "created_at",
        "updated_at",
        "deleted_at",
    )
    readonly_fields = (
        "ip_address",
        "first_seen_at",
        "last_seen_at",
        "created_at",
        "updated_at",
        "deleted_at",
    )
    extra = 0

    def has_add_permission(self, request, obj):
        return False


class BrowserInline(BaseTabularInline):
    model = Browser
    fk_name = "device"
    fields = (
        "browser_family",
        "user_agent",
        "access_count",
        "first_seen_at",
        "last_seen_at",
    )
    readonly_fields = (
        "browser_family",
        "user_agent",
        "access_count",
        "first_seen_at",
        "last_seen_at",
        "created_at",
        "updated_at",
        "deleted_at",
    )
    extra = 0

    def has_add_permission(self, request, obj):
        return False


@admin.register(User)
class UserAdmin(DjangoUserAdmin, BaseModelAdmin):
    search_fields = (
        "id",
        "email",
        "first_name",
        "last_name",
    )
    list_filter = (
        "is_staff",
        "is_superuser",
    )
    list_display = (
        "email",
        "first_name",
        "last_name",
        "is_staff",
        "is_superuser",
        "is_verified",
    )
    autocomplete_fields = ()
    filter_horizontal = ()
    exclude = ("username",)
    fieldsets = (
        ("Personal info", {"fields": ("email", "password", "first_name", "last_name")}),
        (
            "Important dates",
            {
                "fields": (
                    "last_login",
                    "date_joined",
                    "email_verified_at",
                )
            },
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "mfa_enabled",
                )
            },
        ),
    )
    add_fieldsets = (
        (
            None,
            {"fields": ("email", "password1", "password2", "first_name", "last_name")},
        ),
    )
    inlines = (SecretInline, DeviceInline)
    ordering = ("email",)

    @admin.display(boolean=True, description="Verified")
    def is_verified(self, obj):
        return obj.email_verified_at is not None


@admin.register(Device)
class DeviceAdmin(BaseModelAdmin):
    search_fields = (
        "id",
        "device_token",
        "device_fingerprint",
        "device_name",
        "user__email",
        "platform",
        "gpu_vendor",
    )
    list_filter = (
        "trusted",
        "blocked",
        "os_family",
        "device_type",
        "platform",
    )
    list_display = (
        "display_name",
        "user",
        "os_family",
        "device_type",
        "platform",
        "hardware_specs",
        "trusted",
        "blocked",
        "last_seen_at",
        "access_count",
    )
    readonly_fields = (
        "device_token",
        "device_fingerprint",
        "first_seen_at",
        "last_seen_at",
        "access_count",
        "created_at",
        "updated_at",
        "deleted_at",
    )
    fieldsets = (
        (
            "Device Identity",
            {
                "fields": (
                    "user",
                    "device_name",
                    "device_token",
                    "device_fingerprint",
                )
            },
        ),
        (
            "Hardware Characteristics (Stable)",
            {
                "fields": (
                    "os_family",
                    "device_type",
                    "platform",
                    "hardware_concurrency",
                    "device_memory",
                    "gpu_vendor",
                )
            },
        ),
        (
            "Display Info",
            {
                "fields": (
                    "screen_resolution",
                    "browser_timezone",
                    "language",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Security",
            {"fields": ("trusted", "blocked")},
        ),
        (
            "Tracking",
            {
                "fields": (
                    "first_seen_at",
                    "last_seen_at",
                    "access_count",
                    "created_at",
                    "updated_at",
                    "deleted_at",
                )
            },
        ),
    )
    inlines = (IpAddressInline, BrowserInline)
    autocomplete_fields = ("user",)
    ordering = ("-last_seen_at",)

    @admin.display(description="Hardware")
    def hardware_specs(self, obj):
        specs = []
        if obj.gpu_vendor:
            specs.append(obj.gpu_vendor)
        if obj.hardware_concurrency:
            specs.append(f"{obj.hardware_concurrency} cores")
        if obj.device_memory:
            specs.append(f"{obj.device_memory}GB RAM")
        return " • ".join(specs) if specs else "-"
