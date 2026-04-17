from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus

from v17_rebirth.paths import RUNTIME_DIR

_DB_BRIDGE_FALLBACK = Path("/home/hlsystem/bazi/qiazhi/v17_rebirth/.runtime/db_bridge.json")


def _postgres_url_from_admin_blob(blob: dict[str, Any]) -> str | None:
    url = str(blob.get("url") or "").strip()
    if url:
        return url
    host = str(blob.get("host") or "").strip()
    database = str(blob.get("database") or "").strip()
    if not host or not database:
        return None
    port = int(blob.get("port") or 5432)
    user = str(blob.get("username") or "postgres")
    pw = str(blob.get("password") or "")
    ssl = str(blob.get("sslmode") or "prefer")
    auth = quote_plus(user)
    if pw:
        auth += ":" + quote_plus(pw)
    return f"postgresql://{auth}@{host}:{port}/{quote_plus(database)}?sslmode={quote_plus(ssl)}"


def _admin_db_url_from_disk() -> str | None:
    path = RUNTIME_DIR / "db_bridge.json"
    if not path.exists() and _DB_BRIDGE_FALLBACK.exists():
        path = _DB_BRIDGE_FALLBACK
    if not path.exists():
        return None
    try:
        blob = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    if not isinstance(blob, dict) or not blob.get("enabled"):
        return None
    return _postgres_url_from_admin_blob(blob)


@dataclass
class V17DbBridge:
    """连接能力；优先使用 Admin 页持久化的 db_bridge.json（enabled 时）。"""

    database_url: str | None = None

    def resolve_url(self) -> str:
        if self.database_url:
            return str(self.database_url)
        admin_url = _admin_db_url_from_disk()
        if admin_url:
            return admin_url
        return os.getenv("QIAZHI_DATABASE_URL", "sqlite:///qiazhi_v17.db")

    def tagged_record(self, payload: dict[str, Any]) -> dict[str, Any]:
        row = dict(payload or {})
        row["origin"] = "v17_origin"
        return row
