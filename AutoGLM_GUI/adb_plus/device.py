"""Device availability checking utilities."""

import asyncio
from typing import Optional

from AutoGLM_GUI.exceptions import DeviceNotAvailableError
from AutoGLM_GUI.logger import logger
from AutoGLM_GUI.platform_utils import run_cmd_silently, run_cmd_silently_sync


async def check_device_available(device_id: str | None = None) -> None:
    """Check if the device is available.

    Args:
        device_id: ADB device serial (None for default device)

    Raises:
        DeviceNotAvailableError: If device is not reachable
    """
    cmd = ["adb"]
    if device_id:
        cmd.extend(["-s", device_id])
    cmd.append("get-state")

    try:
        result = await asyncio.wait_for(run_cmd_silently(cmd), timeout=5.0)

        state = result.stdout.strip() if result.stdout else ""
        error_output = result.stderr.strip() if result.stderr else ""

        # Check for common error patterns
        if "not found" in error_output.lower() or "offline" in error_output.lower():
            raise DeviceNotAvailableError(
                f"Device {device_id} is not available: {error_output}"
            )

        if state != "device":
            raise DeviceNotAvailableError(
                f"Device {device_id} is not available (state: {state or 'offline'})"
            )

        logger.debug(f"Device {device_id} is available (state: {state})")

    except asyncio.TimeoutError:
        raise DeviceNotAvailableError(f"Device {device_id} connection timed out")
    except FileNotFoundError:
        raise DeviceNotAvailableError("ADB executable not found")
    except DeviceNotAvailableError:
        raise
    except Exception as e:
        raise DeviceNotAvailableError(f"Failed to check device {device_id}: {e}")


def get_device_model(device_id: str, adb_path: str = "adb") -> Optional[str]:
    """Get device model via adb shell getprop.

    This is used as a fallback when model info is not available from
    'adb devices -l' output (common for WiFi-connected devices).

    Args:
        device_id: ADB device serial or IP:port
        adb_path: Path to adb executable

    Returns:
        Device model string (e.g., "Redmi K30 Pro") or None if not available
    """
    cmd = [adb_path, "-s", device_id, "shell", "getprop", "ro.product.model"]

    try:
        result = run_cmd_silently_sync(cmd, timeout=5.0)
        if result.returncode == 0 and result.stdout:
            model = result.stdout.strip()
            if model:
                return model.replace(" ", "_")
        return None
    except Exception as e:
        logger.debug(f"Failed to get model for device {device_id}: {e}")
        return None
