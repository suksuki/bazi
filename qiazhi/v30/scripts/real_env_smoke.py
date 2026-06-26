from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import psycopg

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from v30.config import load_settings
from v30.runtime import create_smoke_runtime
from v30.storage.postgres_schema import CREATE_TABLE_STATEMENTS
from v30.storage.redis_cache import build_runtime_cache
from v30.storage.repository import build_runtime_repository


def _load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("'\""))


def _apply_schema(database_url: str) -> None:
    with psycopg.connect(database_url) as connection:
        with connection.cursor() as cursor:
            for sql in CREATE_TABLE_STATEMENTS.values():
                cursor.execute(sql)
        connection.commit()


def main() -> int:
    parser = argparse.ArgumentParser(description="Run V30 real Postgres/Redis smoke.")
    parser.add_argument("--env-file", default=".env.v30.real")
    parser.add_argument("--reading-id", default="v30-real-smoke")
    args = parser.parse_args()

    _load_env_file(Path(args.env_file))
    os.environ.setdefault("V30_REPOSITORY", "postgres")
    os.environ.setdefault("V30_REDIS_PREFIX", "v30")

    settings = load_settings()
    if settings.repository != "postgres":
        raise RuntimeError("real env smoke requires V30_REPOSITORY=postgres")
    if not settings.database_url:
        raise RuntimeError("real env smoke requires V30_DATABASE_URL")
    if not settings.redis_url:
        raise RuntimeError("real env smoke requires V30_REDIS_URL")

    _apply_schema(settings.database_url)
    repository = build_runtime_repository(settings)
    cache = build_runtime_cache(settings)
    if cache is None:
        raise RuntimeError("real env smoke requires Redis cache")

    runtime = create_smoke_runtime(args.reading_id)
    repository.save_runtime(runtime)
    repository.save_trace(runtime)
    cache.set_reading(runtime)
    cache.set_trace(runtime)

    db_payload = repository.get_runtime_payload(args.reading_id)
    db_trace = repository.get_trace_payload(runtime.trace_id)
    redis_payload = cache.get_reading_payload(args.reading_id)
    redis_trace = cache.get_trace_payload(runtime.trace_id)

    assert db_payload is not None and db_payload["reading_id"] == args.reading_id
    assert db_trace is not None and db_trace["trace_id"] == runtime.trace_id
    assert redis_payload is not None and redis_payload["reading_id"] == args.reading_id
    assert redis_trace is not None and redis_trace["trace_id"] == runtime.trace_id

    print(
        "v30.real_env.smoke: passed "
        f"reading_id={args.reading_id} trace_id={runtime.trace_id} "
        "postgres=v30_readings,v30_runtime_traces redis=v30:*"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
