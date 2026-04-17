from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class V17AdminBridge:
    """Read existing admin settings without importing old business flows."""

    def read_admin_config(self) -> dict[str, str]:
        return {
            "admin_token": os.getenv("QIAZHI_ADMIN_TOKEN", ""),
            "allowed_hosts": os.getenv("QIAZHI_ALLOWED_HOSTS", ""),
            "origin": "v17_origin",
        }
