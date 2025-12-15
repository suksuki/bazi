"""
utils/configuration_manager.py
-------------------------------
Global Configuration Manager (Singleton) for runtime settings.

Features:
- Singleton: ensure a single source of truth
- Dynamic reload: allow runtime re-read of config/env
- Unified access: get_setting(key, default)
"""

import json
import os
import threading
from typing import Any, Optional


class ConfigurationManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(ConfigurationManager, cls).__new__(cls)
                    cls._instance._config = {}
                    cls._instance._load_config()
        return cls._instance

    def _load_config(self) -> None:
        """Load configuration: env vars override file values."""
        # 1) Load from config file if exists
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "config.json")
        file_cfg = {}
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    file_cfg = json.load(f)
            except Exception:
                file_cfg = {}

        # 2) Base config (can be extended)
        base_cfg = {
            "LLM_SERVICE_ENABLED": True,
            "LLM_API_KEY": "",
            "CACHE_TTL_SECONDS": 3600,
        }

        # 3) Merge: file -> base (base overrides missing) then env overrides
        cfg = base_cfg.copy()
        cfg.update(file_cfg or {})

        # Env overrides
        cfg["LLM_SERVICE_ENABLED"] = os.environ.get("LLM_ENABLED", str(cfg.get("LLM_SERVICE_ENABLED", True))).lower() == "true"
        cfg["LLM_API_KEY"] = os.environ.get("LLM_API_KEY", cfg.get("LLM_API_KEY", ""))
        cfg["CACHE_TTL_SECONDS"] = int(os.environ.get("CACHE_TTL", cfg.get("CACHE_TTL_SECONDS", 3600)))

        self._config = cfg

    def get_setting(self, key: str, default: Optional[Any] = None) -> Any:
        """Unified getter for config values."""
        return self._config.get(key, default)

    def reload_config(self) -> None:
        """Reload configuration at runtime."""
        self._load_config()


def get_config_manager() -> ConfigurationManager:
    return ConfigurationManager()

