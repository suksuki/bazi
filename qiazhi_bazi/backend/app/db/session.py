"""数据库会话：仅允许连接白名单内 PostgreSQL（默认本地）。"""
from __future__ import annotations

import os
from contextlib import contextmanager
from urllib.parse import urlparse

from sqlmodel import Session, SQLModel, create_engine

DB_URL = os.getenv("DATABASE_URL", "").strip()
if not DB_URL:
    raise RuntimeError("DATABASE_URL 未配置。当前架构禁止 SQLite 回退。")

parsed = urlparse(DB_URL)
if parsed.scheme not in {"postgresql", "postgresql+psycopg2", "postgresql+psycopg"}:
    raise RuntimeError(f"数据库协议不合法: {parsed.scheme}。仅允许 PostgreSQL。")
allowed_hosts = {"127.0.0.1", "localhost"}
extra_hosts = os.getenv("QIAZHI_ALLOWED_DB_HOSTS", "").strip()
if extra_hosts:
    allowed_hosts.update({h.strip().lower() for h in extra_hosts.split(",") if h.strip()})

host = (parsed.hostname or "").lower()
if host not in allowed_hosts or (parsed.port not in (None, 5432)):
    raise RuntimeError(
        f"数据库地址不合法。仅允许 {', '.join(sorted(allowed_hosts))}:5432（或省略端口）。"
    )

_engine = create_engine(
    DB_URL,
    echo=False,
    pool_pre_ping=True,
)


def init_db() -> None:
    # 延迟导入模型以注册 metadata
    from app.db import models  # noqa: F401
    from app.skills.physics_engine import seed_physics_defaults

    SQLModel.metadata.create_all(_engine)
    seed_physics_defaults()
    try:
        from app.core.physics.settings_manager import DynamicSettingsProvider

        DynamicSettingsProvider.sync_defaults_on_startup()
    except Exception as e:  # noqa: BLE001
        print(f"[startup] DynamicSettingsProvider.sync_defaults_on_startup failed: {e}")
    try:
        from app.core.bazi.l0_manager import sync_l0_from_defaults

        sync_l0_from_defaults()
    except Exception as e:  # noqa: BLE001
        print(f"[startup] sync_l0_from_defaults failed: {e}")


@contextmanager
def session_scope():
    session = Session(_engine)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
