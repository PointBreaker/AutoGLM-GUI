"""Get device serial number using ADB."""

import re
from typing import Optional

from AutoGLM_GUI.platform_utils import run_cmd_silently_sync


def extract_serial_from_mdns(device_id: str) -> Optional[str]:
    """
    Extract hardware serial number from mDNS device ID.

    mDNS service names follow the pattern: adb-{serial}[-{suffix}].{service_type}

    Examples:
        - "adb-243a09b7-cbCO6P._adb-tls-connect._tcp" → "243a09b7"
        - "adb-243a09b7._adb._tcp" → "243a09b7"
        - "adb-ABC123DEF.local" → "ABC123DEF"

    Args:
        device_id: The device ID (can be mDNS service name or regular device ID)

    Returns:
        Extracted serial number, or None if not a valid mDNS format
    """
    # Check if this is an mDNS device ID
    mdns_indicators = [
        "._adb-tls-connect._tcp",
        "._adb-tls-pairing._tcp",
        "._adb._tcp",
        ".local",
    ]

    if not any(indicator in device_id for indicator in mdns_indicators):
        return None

    # Pattern: adb-{serial}[-{suffix}].{service_type}
    # The serial is everything after "adb-" until the next hyphen or dot
    # Match alphanumeric characters (not just hex)
    pattern = r"adb-([0-9a-zA-Z]+)"
    match = re.search(pattern, device_id)

    if match:
        serial = match.group(1)
        # Validate serial format (alphanumeric, typically 6-16 chars)
        if len(serial) >= 6 and serial.isalnum():
            return serial

    return None


def get_device_serial(device_id: str, adb_path: str = "adb") -> str | None:
    """
    Get the real hardware serial number of a device.

    For mDNS devices, attempts to extract serial from service name first.
    Falls back to getprop for USB/WiFi devices or if extraction fails.

    This works for both USB and WiFi connected devices,
    returning the actual hardware serial number (ro.serialno).

    Args:
        device_id: The device ID (can be USB serial or IP:port for WiFi)
        adb_path: Path to adb executable (default: "adb")

    Returns:
        The device hardware serial number, or None if failed
    """
    from AutoGLM_GUI.logger import logger

    # Fast path: Try mDNS extraction first
    mdns_serial = extract_serial_from_mdns(device_id)
    if mdns_serial:
        logger.debug(f"Extracted serial from mDNS name: {device_id} → {mdns_serial}")
        return mdns_serial

    # Fallback: Use getprop (original behavior)
    try:
        # Use getprop to get the actual hardware serial number
        # This works for both USB and WiFi connections
        result = run_cmd_silently_sync(
            [adb_path, "-s", device_id, "shell", "getprop", "ro.serialno"],
            timeout=3,
        )
        if result.returncode == 0:
            serial = result.stdout.strip()
            # Filter out error messages and empty values
            if serial and not serial.startswith("error:") and serial != "unknown":
                logger.debug(f"Got serial via getprop: {device_id} → {serial}")
                return serial
    except Exception as e:
        logger.debug(f"Failed to get serial via getprop for {device_id}: {e}")

    return None
