from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Any, Iterator


_POOL: Any | None = None
_POOL_DSN = ""


@contextmanager
def pooled_postgres_connection(database_url: str | None = None) -> Iterator[Any]:
    dsn = str(database_url or os.getenv("V20_DATABASE_URL", "")).strip()
    if not dsn:
        raise RuntimeError("missing_V20_DATABASE_URL")
    pool = _pool_for_dsn(dsn)
    conn = pool.getconn()
    try:
        yield conn
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        raise
    finally:
        pool.putconn(conn)


def postgres_pool_status() -> dict[str, object]:
    return {
        "version": "v20.postgres_pool_status.v1",
        "enabled": bool(_POOL),
        "minconn": _pool_minconn(),
        "maxconn": _pool_maxconn(),
        "database_url_present": bool(os.getenv("V20_DATABASE_URL", "")),
        "runtime_mutation": False,
        "guardrails": ["NO_SECRET_VALUES_RENDERED", "POSTGRES_POOL_IS_PROCESS_LOCAL"],
    }


def close_postgres_pool() -> None:
    global _POOL, _POOL_DSN
    if _POOL is not None:
        _POOL.closeall()
    _POOL = None
    _POOL_DSN = ""


def _pool_for_dsn(dsn: str) -> Any:
    global _POOL, _POOL_DSN
    if _POOL is not None and _POOL_DSN == dsn:
        return _POOL
    if _POOL is not None:
        _POOL.closeall()
    try:
        from psycopg2.pool import SimpleConnectionPool
    except Exception as exc:
        raise RuntimeError(f"missing_psycopg2_pool:{type(exc).__name__}") from exc
    _POOL = SimpleConnectionPool(_pool_minconn(), _pool_maxconn(), dsn)
    _POOL_DSN = dsn
    return _POOL


def _pool_minconn() -> int:
    return _int_env("V20_POSTGRES_POOL_MINCONN", 1, lower=1, upper=10)


def _pool_maxconn() -> int:
    minimum = _pool_minconn()
    return max(minimum, _int_env("V20_POSTGRES_POOL_MAXCONN", 8, lower=minimum, upper=40))


def _int_env(name: str, default: int, *, lower: int, upper: int) -> int:
    try:
        value = int(os.getenv(name, str(default)))
    except ValueError:
        return default
    return max(lower, min(value, upper))
