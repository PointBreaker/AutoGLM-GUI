"""Device discovery routes."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter

if TYPE_CHECKING:
    from AutoGLM_GUI.device_manager import ManagedDevice
    from AutoGLM_GUI.phone_agent_manager import PhoneAgentManager

from AutoGLM_GUI.adb_plus.qr_pair import qr_pairing_manager
from AutoGLM_GUI.logger import logger

from AutoGLM_GUI.schemas import (
    DeviceListResponse,
    WiFiConnectRequest,
    WiFiConnectResponse,
    WiFiDisconnectRequest,
    WiFiDisconnectResponse,
    WiFiManualConnectRequest,
    WiFiManualConnectResponse,
    WiFiPairRequest,
    WiFiPairResponse,
    MdnsDiscoverResponse,
    MdnsDeviceResponse,
    QRPairGenerateResponse,
    QRPairStatusResponse,
    QRPairCancelResponse,
)


def _build_device_response_with_agent(
    device: ManagedDevice, agent_manager: PhoneAgentManager
) -> dict:
    """组合设备信息和 Agent 状态（API 层职责）。

    Args:
        device: ManagedDevice 实例
        agent_manager: PhoneAgentManager 实例

    Returns:
        dict: 完整的设备响应，匹配 DeviceResponse schema
    """
    from AutoGLM_GUI.device_alias_manager import device_alias_manager

    # 获取纯设备信息
    response = device.to_dict()

    # 添加设备别名
    alias = device_alias_manager.get_alias(device.serial)
    response["alias"] = alias

    # 通过 serial 查找 Agent（支持连接切换）
    agent_device_id = agent_manager.find_agent_by_serial(device.serial)

    if agent_device_id:
        metadata = agent_manager.get_metadata(agent_device_id)

        if metadata:
            response["agent"] = {
                "state": metadata.state.value,
                "created_at": metadata.created_at,
                "last_used": metadata.last_used,
                "error_message": metadata.error_message,
                "model_name": metadata.model_config.model_name,
            }
        else:
            response["agent"] = None
    else:
        response["agent"] = None

    return response


router = APIRouter()


@router.get("/api/devices", response_model=DeviceListResponse)
def list_devices() -> DeviceListResponse:
    """列出所有 ADB 设备及 Agent 状态."""
    from AutoGLM_GUI.device_manager import DeviceManager
    from AutoGLM_GUI.phone_agent_manager import PhoneAgentManager

    device_manager = DeviceManager.get_instance()
    agent_manager = PhoneAgentManager.get_instance()

    # Fallback: 如果轮询未启动,执行同步获取
    if not device_manager._poll_thread or not device_manager._poll_thread.is_alive():
        logger.warning("Polling not started, performing synchronous device fetch")
        device_manager.force_refresh()

    managed_devices = device_manager.get_devices()

    # API 层负责聚合设备信息和 Agent 状态
    devices_with_agents = [
        _build_device_response_with_agent(d, agent_manager) for d in managed_devices
    ]

    return DeviceListResponse(devices=devices_with_agents)


@router.post("/api/devices/connect_wifi", response_model=WiFiConnectResponse)
def connect_wifi(request: WiFiConnectRequest) -> WiFiConnectResponse:
    """从 USB 启用 TCP/IP 并连接到 WiFi。"""
    from AutoGLM_GUI.device_manager import DeviceManager

    device_manager = DeviceManager.get_instance()
    success, message, wifi_id = device_manager.connect_wifi(
        device_id=request.device_id,
        port=request.port,
    )

    if success:
        # Immediately refresh device list to show new WiFi device
        device_manager.force_refresh()

        return WiFiConnectResponse(
            success=True,
            message=message,
            device_id=wifi_id,
            address=wifi_id,
        )
    else:
        # Determine error type from message
        error_type = "connect"
        if "not found" in message.lower():
            error_type = "device_not_found"
        elif "tcpip" in message.lower():
            error_type = "tcpip"
        elif "ip" in message.lower():
            error_type = "ip"

        return WiFiConnectResponse(
            success=False,
            message=message,
            error=error_type,
        )


@router.post("/api/devices/disconnect_wifi", response_model=WiFiDisconnectResponse)
def disconnect_wifi(request: WiFiDisconnectRequest) -> WiFiDisconnectResponse:
    """断开 WiFi 连接。"""
    from AutoGLM_GUI.device_manager import DeviceManager

    device_manager = DeviceManager.get_instance()
    success, message = device_manager.disconnect_wifi(request.device_id)

    if success:
        # Refresh device list to update status
        device_manager.force_refresh()

    return WiFiDisconnectResponse(
        success=success,
        message=message,
        error=None if success else "disconnect_failed",
    )


@router.post(
    "/api/devices/connect_wifi_manual", response_model=WiFiManualConnectResponse
)
def connect_wifi_manual(
    request: WiFiManualConnectRequest,
) -> WiFiManualConnectResponse:
    """手动连接到 WiFi 设备 (直接连接,无需 USB)."""
    from AutoGLM_GUI.device_manager import DeviceManager

    device_manager = DeviceManager.get_instance()
    success, message, device_id = device_manager.connect_wifi_manual(
        ip=request.ip,
        port=request.port,
    )

    if success:
        # Refresh device list to show new device
        device_manager.force_refresh()

        return WiFiManualConnectResponse(
            success=True,
            message=message,
            device_id=device_id,
        )
    else:
        # Determine error type from message
        error_type = "connect_failed"
        if "Invalid IP" in message:
            error_type = "invalid_ip"
        elif "Port must be" in message:
            error_type = "invalid_port"

        return WiFiManualConnectResponse(
            success=False,
            message=message,
            error=error_type,
        )


@router.post("/api/devices/pair_wifi", response_model=WiFiPairResponse)
def pair_wifi(request: WiFiPairRequest) -> WiFiPairResponse:
    """使用无线调试配对并连接到 WiFi 设备 (Android 11+)."""
    from AutoGLM_GUI.device_manager import DeviceManager

    device_manager = DeviceManager.get_instance()
    success, message, device_id = device_manager.pair_wifi(
        ip=request.ip,
        pairing_port=request.pairing_port,
        pairing_code=request.pairing_code,
        connection_port=request.connection_port,
    )

    if success:
        # Refresh device list to show newly paired device
        device_manager.force_refresh()

        return WiFiPairResponse(
            success=True,
            message=message,
            device_id=device_id,
        )
    else:
        # Determine error type from message
        error_type = "connect_failed"
        if "Invalid IP" in message:
            error_type = "invalid_ip"
        elif "port must be" in message.lower():
            error_type = "invalid_port"
        elif "Pairing code must be" in message:
            error_type = "invalid_pairing_code"
        elif "connection failed" not in message.lower():
            error_type = "pair_failed"

        return WiFiPairResponse(
            success=False,
            message=message,
            error=error_type,
        )


@router.get("/api/devices/discover_mdns", response_model=MdnsDiscoverResponse)
def discover_mdns() -> MdnsDiscoverResponse:
    """Discover wireless ADB devices via mDNS."""
    from phone_agent.adb import ADBConnection
    from AutoGLM_GUI.adb_plus import discover_mdns_devices

    try:
        conn = ADBConnection()
        devices = discover_mdns_devices(conn.adb_path)

        device_responses = [
            MdnsDeviceResponse(
                name=dev.name,
                ip=dev.ip,
                port=dev.port,
                has_pairing=dev.has_pairing,
                service_type=dev.service_type,
                pairing_port=dev.pairing_port,
            )
            for dev in devices
        ]

        return MdnsDiscoverResponse(
            success=True,
            devices=device_responses,
        )

    except Exception as e:
        return MdnsDiscoverResponse(
            success=False,
            devices=[],
            error=str(e),
        )


# QR Code Pairing Routes


@router.post("/api/devices/qr_pair/generate", response_model=QRPairGenerateResponse)
def generate_qr_pairing(timeout: int = 90) -> QRPairGenerateResponse:
    """Generate QR code for wireless pairing and start mDNS listener.

    Args:
        timeout: Session timeout in seconds (default 90)

    Returns:
        QR code payload and session information
    """
    try:
        from phone_agent.adb import ADBConnection

        conn = ADBConnection()
        session = qr_pairing_manager.create_session(
            timeout=timeout, adb_path=conn.adb_path
        )

        return QRPairGenerateResponse(
            success=True,
            qr_payload=session.qr_payload,
            session_id=session.session_id,
            expires_at=session.expires_at,
            message="QR code generated, listening for devices...",
        )
    except Exception as e:
        return QRPairGenerateResponse(
            success=False,
            message=f"Failed to generate QR pairing: {str(e)}",
            error="generation_failed",
        )


def _get_status_message(status: str) -> str:
    """Get user-friendly message for status code."""
    messages = {
        "listening": "等待手机扫描二维码...",
        "pairing": "正在配对设备...",
        "paired": "配对成功，正在连接...",
        "connecting": "正在建立连接...",
        "connected": "连接成功！",
        "timeout": "超时：未检测到设备扫码",
        "error": "配对失败",
    }
    return messages.get(status, "未知状态")


@router.get(
    "/api/devices/qr_pair/status/{session_id}", response_model=QRPairStatusResponse
)
def get_qr_pairing_status(session_id: str) -> QRPairStatusResponse:
    """Get current status of a QR pairing session.

    Args:
        session_id: Session UUID

    Returns:
        Current session status and device information if connected
    """
    session = qr_pairing_manager.get_session(session_id)

    if not session:
        return QRPairStatusResponse(
            session_id=session_id,
            status="error",
            message="Session not found or expired",
            error="session_not_found",
        )

    return QRPairStatusResponse(
        session_id=session.session_id,
        status=session.status,
        device_id=session.device_id,
        message=_get_status_message(session.status),
        error=session.error_message,
    )


@router.delete("/api/devices/qr_pair/{session_id}", response_model=QRPairCancelResponse)
def cancel_qr_pairing(session_id: str) -> QRPairCancelResponse:
    """Cancel an active QR pairing session.

    Args:
        session_id: Session UUID to cancel

    Returns:
        Success status
    """
    success = qr_pairing_manager.cancel_session(session_id)

    if success:
        return QRPairCancelResponse(
            success=True,
            message="Pairing session cancelled",
        )
    else:
        return QRPairCancelResponse(
            success=False,
            message="Session not found or already completed",
        )


# ==================== 设备别名管理 ====================


@router.get("/api/devices/{serial}/alias")
def get_device_alias(serial: str) -> dict:
    """获取设备别名.

    Args:
        serial: 设备序列号

    Returns:
        设备别名信息
    """
    from AutoGLM_GUI.device_alias_manager import device_alias_manager

    alias = device_alias_manager.get_alias(serial)
    return {
        "serial": serial,
        "alias": alias,
    }


@router.put("/api/devices/{serial}/alias")
def set_device_alias(serial: str, data: dict) -> dict:
    """设置设备别名.

    Args:
        serial: 设备序列号
        data: 包含 alias 字段的请求体

    Returns:
        操作结果
    """
    from AutoGLM_GUI.device_alias_manager import device_alias_manager

    alias = data.get("alias", "")
    success = device_alias_manager.set_alias(serial, alias)

    if success:
        return {
            "success": True,
            "serial": serial,
            "alias": alias if alias.strip() else None,
            "message": "Alias updated" if alias.strip() else "Alias removed",
        }
    else:
        return {
            "success": False,
            "message": "Failed to save alias",
        }


@router.delete("/api/devices/{serial}/alias")
def delete_device_alias(serial: str) -> dict:
    """删除设备别名.

    Args:
        serial: 设备序列号

    Returns:
        操作结果
    """
    from AutoGLM_GUI.device_alias_manager import device_alias_manager

    success = device_alias_manager.delete_alias(serial)
    return {
        "success": success,
        "serial": serial,
        "message": "Alias deleted" if success else "Failed to delete alias",
    }


# ==================== 设备删除（断开并清理） ====================


@router.delete("/api/devices/{serial}")
def delete_device(serial: str) -> dict:
    """删除设备（断开连接并清理资源）.

    Args:
        serial: 设备序列号

    Returns:
        操作结果
    """
    from AutoGLM_GUI.device_manager import DeviceManager
    from AutoGLM_GUI.phone_agent_manager import PhoneAgentManager
    from AutoGLM_GUI.device_alias_manager import device_alias_manager

    device_manager = DeviceManager.get_instance()
    agent_manager = PhoneAgentManager.get_instance()

    # 获取设备信息
    device = device_manager.get_device_by_serial(serial)
    if not device:
        return {
            "success": False,
            "message": f"Device with serial {serial} not found",
        }

    device_id = device.primary_device_id

    # 清理 Agent
    agent_device_id = agent_manager.find_agent_by_serial(serial)
    if agent_device_id:
        try:
            agent_manager.remove_agent(agent_device_id)
            logger.info(f"Removed agent for device {serial}")
        except Exception as e:
            logger.warning(f"Failed to remove agent: {e}")

    # 断开 WiFi 连接（如果是 WiFi 设备）
    conn_type = device.connection_type.value
    if conn_type == "wifi" or conn_type == "remote":
        try:
            device_manager.disconnect_wifi(device_id)
            logger.info(f"Disconnected WiFi for device {serial}")
        except Exception as e:
            logger.warning(f"Failed to disconnect WiFi: {e}")

    # 删除设备别名
    device_alias_manager.delete_alias(serial)

    # 刷新设备列表
    device_manager.force_refresh()

    return {
        "success": True,
        "serial": serial,
        "message": f"Device {serial} removed successfully",
    }


# ==================== 断开所有连接 ====================


@router.post("/api/devices/{serial}/disconnect_all")
def disconnect_all_connections(serial: str) -> dict:
    """断开设备的所有连接（USB和WiFi）.

    Args:
        serial: 设备序列号

    Returns:
        操作结果
    """
    from AutoGLM_GUI.device_manager import DeviceManager
    from AutoGLM_GUI.phone_agent_manager import PhoneAgentManager
    from AutoGLM_GUI.platform_utils import run_cmd_silently_sync
    from phone_agent.adb import ADBConnection

    device_manager = DeviceManager.get_instance()
    agent_manager = PhoneAgentManager.get_instance()

    # 获取设备信息
    device = device_manager.get_device_by_serial(serial)
    if not device:
        return {
            "success": False,
            "serial": serial,
            "message": f"Device with serial {serial} not found",
        }

    disconnected = []

    # 清理 Agent
    agent_device_id = agent_manager.find_agent_by_serial(serial)
    if agent_device_id:
        try:
            agent_manager.remove_agent(agent_device_id)
            logger.info(f"Removed agent for device {serial}")
            disconnected.append("agent")
        except Exception as e:
            logger.warning(f"Failed to remove agent: {e}")

    # 断开 WiFi 连接
    conn_type = device.connection_type.value
    if conn_type == "wifi" or conn_type == "remote":
        try:
            device_manager.disconnect_wifi(device.primary_device_id)
            logger.info(f"Disconnected WiFi for device {serial}")
            disconnected.append("wifi")
        except Exception as e:
            logger.warning(f"Failed to disconnect WiFi: {e}")

    # 尝试断开所有与该设备相关的连接（包括可能的 WiFi 连接）
    try:
        conn = ADBConnection()
        # 获取所有设备列表
        all_devices = device_manager.get_devices()
        for d in all_devices:
            if d.serial == serial:
                # 如果是远程连接，断开
                d_conn_type = d.connection_type.value
                if d_conn_type in ("wifi", "remote"):
                    run_cmd_silently_sync(
                        [conn.adb_path, "disconnect", d.primary_device_id],
                        timeout=5
                    )
                    logger.info(f"Disconnected connection {d.primary_device_id}")
                    if "wifi" not in disconnected:
                        disconnected.append("wifi")
    except Exception as e:
        logger.warning(f"Failed to disconnect additional connections: {e}")

    # 刷新设备列表
    device_manager.force_refresh()

    return {
        "success": True,
        "serial": serial,
        "message": f"Disconnected: {', '.join(disconnected) if disconnected else 'none'}",
    }

