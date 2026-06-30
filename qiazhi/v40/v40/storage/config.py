from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class V40DatabaseConfig:
    dsn: str
    source: str


def resolve_v40_database_config() -> V40DatabaseConfig | None:
    dsn = os.getenv("V40_DATABASE_URL", "").strip()
    if dsn:
        return V40DatabaseConfig(dsn=dsn, source="env:V40_DATABASE_URL")

    local_dsn = _read_local_env_value("V40_DATABASE_URL")
    if local_dsn:
        return V40DatabaseConfig(dsn=local_dsn, source=".env.v40.local")

    return None


def v40_repository_configured() -> bool:
    return resolve_v40_database_config() is not None


def _read_local_env_value(key: str) -> str:
    env_path = Path(__file__).resolve().parents[2] / ".env.v40.local"
    if not env_path.exists():
        return ""

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        if name.strip() == key:
            return value.strip().strip('"').strip("'")
    return ""
