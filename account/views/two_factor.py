from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render

from account.models import Device, IPAddress


def two_factor_notice(request):
    return render(request, "two_factor_notice.html")


@login_required
def device_list(request):
    """Partial View - Returns list of the user's recognized devices."""
    devices = Device.objects.filter(
        user=request.user,
        deleted_at__isnull=True,
    )

    trusted_devices = devices.filter(trusted=True, blocked=False)
    untrusted_devices = devices.filter(trusted=False, blocked=False)
    blocked_devices = devices.filter(blocked=True)

    return render(
        request,
        "partials/device_list.html",
        context={
            "trusted_devices": trusted_devices,
            "untrusted_devices": untrusted_devices,
            "blocked_devices": blocked_devices,
        },
    )


@login_required
def device_detail(request, device_id):
    """Partial view - returns expanded device with IP list"""
    device = get_object_or_404(
        Device,
        id=device_id,
        user=request.user,
        deleted_at__isnull=True,
    )
    ip_addresses = device.ip_addresses.filter(deleted_at__isnull=True)
    browsers = device.browsers.filter(deleted_at__isnull=True)

    return render(
        request,
        "partials/device_detail.html",
        {
            "device": device,
            "ip_addresses": ip_addresses,
            "browsers": browsers,
        },
    )


@login_required
def device_trust(request, device_id):
    """Action view - toggle trust, return updated device list"""
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    device = get_object_or_404(
        Device,
        id=device_id,
        user=request.user,
        deleted_at__isnull=True,
    )
    device.trusted = not device.trusted
    device.save()

    # Return the updated device list to refresh section headers
    return device_list(request)


@login_required
def device_block(request, device_id):
    """Confirmation page and action for blocking a device"""
    device = get_object_or_404(
        Device,
        id=device_id,
        user=request.user,
        deleted_at__isnull=True,
    )

    if request.method == "POST":
        device.blocked = True
        device.trusted = False
        device.save()
        messages.success(request, f"Device blocked: {device.display_name}")
        return redirect("profile")

    # GET: Show confirmation page
    return render(
        request,
        "device_block_confirm.html",
        {"device": device},
    )


@login_required
def device_delete(request, device_id):
    """Confirmation page and action for deleting a device"""
    device = get_object_or_404(
        Device,
        id=device_id,
        user=request.user,
        deleted_at__isnull=True,
    )

    if request.method == "POST":
        device_name = device.display_name
        device.delete(hard=True)
        messages.success(request, f"Device removed: {device_name}")
        return redirect("profile")

    # GET: Show confirmation page
    return render(
        request,
        "device_delete_confirm.html",
        {"device": device},
    )


@login_required
def ip_toggle_block(request, ip_id):
    """Toggle IP address block status and return updated device detail"""
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    ip_address = get_object_or_404(
        IPAddress,
        id=ip_id,
        device__user=request.user,
        deleted_at__isnull=True,
    )

    ip_address.blocked = not ip_address.blocked
    ip_address.save()

    # Return updated device detail to refresh the IP table
    return device_detail(request, ip_address.device_id)
