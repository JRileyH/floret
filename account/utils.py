from ipaddress import ip_address, ip_network

import user_agents
from django.http import HttpRequest

from account.types import ClientFingerprint, UserAgentInfo


def get_client_fingerprint(request: HttpRequest) -> ClientFingerprint:
    """Extract client-side fingerprint from request POST data"""
    return ClientFingerprint(
        # Stable fields
        platform=request.POST.get("client_platform", ""),
        hardwareConcurrency=request.POST.get("client_hardwareConcurrency", ""),
        deviceMemory=request.POST.get("client_deviceMemory", ""),
        webgl=request.POST.get("client_webgl", ""),
        # Volatile fields
        screenResolution=request.POST.get("client_screenResolution", ""),
        screenColorDepth=request.POST.get("client_screenColorDepth", ""),
        browserTimezone=request.POST.get("client_browserTimezone", ""),
        language=request.POST.get("client_language", ""),
    )


def normalize_ip_to_subnet(ip_str: str) -> str:
    """Normalize IP to subnet for privacy: /24 for IPv4, /48 for IPv6"""
    try:
        ip_obj = ip_address(ip_str)
        if ip_obj.version == 4:
            # Store as /24 subnet (e.g., 192.168.1.0)
            subnet = ip_network(f"{ip_str}/24", strict=False)
            return str(subnet.network_address)
        else:
            # Store as /48 subnet for IPv6
            subnet = ip_network(f"{ip_str}/48", strict=False)
            return str(subnet.network_address)
    except Exception:
        # Fallback to original if parsing fails
        return ip_str


def get_user_agent_info(request: HttpRequest) -> UserAgentInfo:
    """Extract user agent details from request"""
    user_agent_string = request.META.get("HTTP_USER_AGENT", "")

    # Extract raw IP
    ip_address = request.META.get("HTTP_X_FORWARDED_FOR")
    if ip_address:
        ip_address = ip_address.split(",")[0].strip()
    else:
        ip_address = request.META.get("REMOTE_ADDR", None)

    # Normalize to subnet for privacy (/24 for IPv4, /48 for IPv6)
    if ip_address:
        ip_address = normalize_ip_to_subnet(ip_address)

    user_agent = user_agents.parse(user_agent_string)
    return UserAgentInfo(
        user_agent_string=user_agent_string,
        browser_family=user_agent.browser.family,
        os_family=user_agent.os.family,
        device_type=user_agent.device.family,
        ip_address=ip_address,
    )
