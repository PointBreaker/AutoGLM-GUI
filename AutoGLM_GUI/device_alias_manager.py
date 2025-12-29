"""设备别名管理器 - 管理设备的自定义显示名称."""

import json
from pathlib import Path
from typing import Optional

from AutoGLM_GUI.logger import logger


class DeviceAliasManager:
    """管理设备别名的单例类."""

    _instance: Optional["DeviceAliasManager"] = None

    def __new__(cls) -> "DeviceAliasManager":
        """单例模式."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        """初始化别名管理器."""
        if self._initialized:
            return

        self._config_dir = Path.home() / ".config" / "autoglm"
        self._alias_file = self._config_dir / "device_aliases.json"
        self._aliases: dict[str, str] = {}
        self._load_aliases()
        self._initialized = True

    def _load_aliases(self) -> None:
        """从文件加载别名."""
        if not self._alias_file.exists():
            self._aliases = {}
            return

        try:
            with open(self._alias_file, "r", encoding="utf-8") as f:
                self._aliases = json.load(f)
            logger.debug(f"Loaded {len(self._aliases)} device aliases")
        except (json.JSONDecodeError, Exception) as e:
            logger.warning(f"Failed to load device aliases: {e}")
            self._aliases = {}

    def _save_aliases(self) -> bool:
        """保存别名到文件."""
        try:
            self._config_dir.mkdir(parents=True, exist_ok=True)
            temp_file = self._alias_file.with_suffix(".tmp")
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(self._aliases, f, indent=2, ensure_ascii=False)
            temp_file.replace(self._alias_file)
            return True
        except Exception as e:
            logger.error(f"Failed to save device aliases: {e}")
            return False

    def get_alias(self, serial: str) -> Optional[str]:
        """获取设备别名.

        Args:
            serial: 设备序列号

        Returns:
            设备别名，如果没有设置则返回 None
        """
        return self._aliases.get(serial)

    def set_alias(self, serial: str, alias: str) -> bool:
        """设置设备别名.

        Args:
            serial: 设备序列号
            alias: 别名（空字符串表示删除别名）

        Returns:
            是否成功
        """
        if alias.strip():
            self._aliases[serial] = alias.strip()
        else:
            self._aliases.pop(serial, None)

        return self._save_aliases()

    def delete_alias(self, serial: str) -> bool:
        """删除设备别名.

        Args:
            serial: 设备序列号

        Returns:
            是否成功
        """
        if serial in self._aliases:
            del self._aliases[serial]
            return self._save_aliases()
        return True

    def get_all_aliases(self) -> dict[str, str]:
        """获取所有设备别名.

        Returns:
            设备序列号到别名的映射
        """
        return self._aliases.copy()


device_alias_manager = DeviceAliasManager()
