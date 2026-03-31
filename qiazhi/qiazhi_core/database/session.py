"""数据库会话管理（MVP：SQLite 默认，可切换 PostgreSQL）。"""
from __future__ import annotations

import os
from contextlib import contextmanager

from sqlmodel import Session, SQLModel, create_engine

DB_URL = os.getenv("QIAZHI_DB_URL", "sqlite:///./qiazhi.db")
_engine = create_engine(DB_URL, echo=False)


def init_db() -> None:
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


def get_session():
    with Session(_engine) as session:
        yield session
