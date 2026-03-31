"""数据库会话：仅允许连接 0.13 PostgreSQL。"""
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
if parsed.hostname != "192.168.0.13" or (parsed.port not in (None, 5432)):
    raise RuntimeError("数据库地址不合法。仅允许 192.168.0.13:5432。")

_engine = create_engine(
    DB_URL,
    echo=False,
    pool_pre_ping=True,
)


def init_db() -> None:
    # 延迟导入模型以注册 metadata
    from app.db import models  # noqa: F401

    SQLModel.metadata.create_all(_engine)


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
