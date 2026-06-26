from __future__ import annotations

import os

import pytest

from v30.config import load_settings
from v30.runtime import create_smoke_runtime
from v30.storage.postgres_schema import CREATE_TABLE_STATEMENTS
from v30.storage.redis_cache import build_runtime_cache
from v30.storage.repository import build_runtime_repository


pytestmark = [
    pytest.mark.integration,
    pytest.mark.requires_postgres,
    pytest.mark.requires_redis,
]


def test_real_postgres_redis_runtime_loop() -> None:
    if os.getenv("V30_RUN_REAL_ENV_TESTS") != "1":
        pytest.skip("set V30_RUN_REAL_ENV_TESTS=1 to run live V30 environment tests")

    settings = load_settings()
    assert settings.repository == "postgres"
    assert settings.database_url
    assert settings.redis_url

    import psycopg

    with psycopg.connect(settings.database_url) as connection:
        with connection.cursor() as cursor:
            for sql in CREATE_TABLE_STATEMENTS.values():
                cursor.execute(sql)
        connection.commit()

    repository = build_runtime_repository(settings)
    cache = build_runtime_cache(settings)
    assert cache is not None

    runtime = create_smoke_runtime("pytest-real-env")
    repository.save_runtime(runtime)
    repository.save_trace(runtime)
    cache.set_reading(runtime)
    cache.set_trace(runtime)

    reading_payload = repository.get_runtime_payload("pytest-real-env")
    trace_payload = repository.get_trace_payload(runtime.trace_id)
    redis_payload = cache.get_reading_payload("pytest-real-env")
    redis_trace_payload = cache.get_trace_payload(runtime.trace_id)

    assert reading_payload is not None
    assert reading_payload["reading_id"] == "pytest-real-env"
    assert trace_payload is not None
    assert trace_payload["trace_id"] == runtime.trace_id
    assert redis_payload is not None
    assert redis_payload["reading_id"] == "pytest-real-env"
    assert redis_trace_payload is not None
    assert redis_trace_payload["trace_id"] == runtime.trace_id
