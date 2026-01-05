from typing import TypedDict


class ClientFingerprint(TypedDict, total=False):
    """Client-side fingerprinting signals"""

    # Stable fields (used in fingerprint)
    platform: str
    hardwareConcurrency: str
    deviceMemory: str
    webgl: str

    # Volatile fields (display only)
    screenResolution: str
    screenColorDepth: str
    browserTimezone: str
    language: str


class UserAgentInfo(TypedDict):
    user_agent_string: str
    browser_family: str
    os_family: str
    device_type: str
    ip_address: str
