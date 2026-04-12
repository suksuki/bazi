"""数据库会话：PostgreSQL；默认同环回/私网任意端口；可 QIAZHI_TRUST_ANY_HOST 跳过主机校验。"""
from __future__ import annotations

import ipaddress
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

_TRUST_ANY = os.getenv("QIAZHI_TRUST_ANY_HOST", "").lower() in ("1", "true", "yes")
_STRICT_DB = os.getenv("QIAZHI_STRICT_DB_HOSTS", "").lower() in ("1", "true", "yes")

allowed_hosts = {"127.0.0.1", "localhost", "::1", "host.docker.internal"}
_extra = os.getenv("QIAZHI_ALLOWED_DB_HOSTS", "").strip()
if _extra:
    allowed_hosts.update({h.strip().lower() for h in _extra.split(",") if h.strip()})

_host = (parsed.hostname or "").lower()


def _startup_db_host_ok() -> bool:
    if _TRUST_ANY:
        return True
    if _host in allowed_hosts:
        return True
    if not _STRICT_DB:
        try:
            ip = ipaddress.ip_address(_host)
            # RFC1918 / 环回 / 链路本地等，与 ipaddress.is_private 语义一致（含 10/8, 172.16/12, 192.168/16）
            return bool(ip.is_private or ip.is_loopback or ip.is_link_local)
        except ValueError:
            return False
    return False


if not _startup_db_host_ok():
    raise RuntimeError(
        f"数据库地址不合法：主机 {_host!r} 未放行。"
        "默认可用 localhost/127.0.0.1/::1 及私网 IP、任意端口；"
        "任意主机名可设 QIAZHI_TRUST_ANY_HOST=true，或把主机名加入 QIAZHI_ALLOWED_DB_HOSTS。"
        + (" 已启用 QIAZHI_STRICT_DB_HOSTS。" if _STRICT_DB else "")
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
