from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from v30.ops.admin_runtime import apply_saved_v30_admin_env_overrides


V30_ENV_NAMES = (
    "V30_DATABASE_URL",
    "V30_REDIS_URL",
    "V30_REDIS_PREFIX",
    "V30_RUNTIME_DIR",
    "V30_HOST",
    "V30_PORT",
    "V30_REPOSITORY",
)


@dataclass(frozen=True)
class V30Settings:
    database_url: str | None
    redis_url: str | None
    redis_prefix: str
    runtime_dir: Path
    host: str
    port: int
    env: str
    repository: str


def load_settings() -> V30Settings:
    apply_saved_v30_admin_env_overrides()
    runtime_dir = Path(os.getenv("V30_RUNTIME_DIR", ".runtime")).resolve()
    redis_prefix = os.getenv("V30_REDIS_PREFIX", "v30")
    if redis_prefix != "v30":
        raise ValueError("V30_REDIS_PREFIX must be exactly 'v30'")
    database_url = os.getenv("V30_DATABASE_URL")
    _validate_database_url(database_url)
    return V30Settings(
        database_url=database_url,
        redis_url=os.getenv("V30_REDIS_URL"),
        redis_prefix=redis_prefix,
        runtime_dir=runtime_dir,
        host=os.getenv("V30_HOST", "127.0.0.1"),
        port=int(os.getenv("V30_PORT", "9030")),
        env=os.getenv("V30_ENV", "local"),
        repository=os.getenv("V30_REPOSITORY", "memory"),
    )


def _validate_database_url(database_url: str | None) -> None:
    if not database_url:
        return
    parsed = urlparse(database_url)
    db_name = parsed.path.rsplit("/", 1)[-1].lower()
    if "v20" in db_name:
        raise ValueError("V30_DATABASE_URL must not point to a V20 database.")
