from __future__ import annotations

import os
import re
from datetime import datetime, timezone
from threading import Lock
from typing import Protocol

from product.database_schema import check_product_database_schema


class LegacyUsageStore(Protocol):
    persistent: bool
    storage_name: str

    def record(self, *, route_key: str, method: str) -> None: ...
    def snapshot(self) -> list[dict[str, object]]: ...


class MemoryLegacyUsageStore:
    persistent = False
    storage_name = "memory_only"

    def __init__(self) -> None:
        self._rows: dict[tuple[str, str], dict[str, object]] = {}
        self._lock = Lock()

    def record(self, *, route_key: str, method: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        key = (route_key, method.upper())
        with self._lock:
            row = self._rows.setdefault(key, {
                "route_key": route_key,
                "method": method.upper(),
                "request_count": 0,
                "first_seen_at": now,
                "last_seen_at": now,
            })
            row["request_count"] = int(row["request_count"]) + 1
            row["last_seen_at"] = now

    def snapshot(self) -> list[dict[str, object]]:
        with self._lock:
            return sorted(
                (dict(row) for row in self._rows.values()),
                key=lambda row: (-int(row["request_count"]), str(row["route_key"])),
            )


class PostgresLegacyUsageStore:
    persistent = True
    storage_name = "v50_postgresql"

    def __init__(self, database_url: str) -> None:
        self.database_url = database_url
        check_product_database_schema(database_url)

    def _connect(self):
        import psycopg

        return psycopg.connect(self.database_url)

    def record(self, *, route_key: str, method: str) -> None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO v50_legacy_runtime_usage (route_key, method, request_count)
                    VALUES (%s, %s, 1)
                    ON CONFLICT (route_key, method) DO UPDATE SET
                        request_count = v50_legacy_runtime_usage.request_count + 1,
                        last_seen_at = now()
                    """,
                    (route_key, method.upper()),
                )

    def snapshot(self) -> list[dict[str, object]]:
        from psycopg.rows import dict_row

        with self._connect() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    """
                    SELECT route_key, method, request_count, first_seen_at, last_seen_at
                    FROM v50_legacy_runtime_usage
                    ORDER BY request_count DESC, route_key ASC
                    """
                )
                rows = cur.fetchall()
        return [
            {
                **dict(row),
                "first_seen_at": row["first_seen_at"].isoformat(),
                "last_seen_at": row["last_seen_at"].isoformat(),
            }
            for row in rows
        ]


def build_legacy_usage_store() -> LegacyUsageStore:
    database_url = os.getenv("V50_DATABASE_URL", "").strip()
    return PostgresLegacyUsageStore(database_url) if database_url else MemoryLegacyUsageStore()


_EXACT_LEGACY_ROUTES = {
    "/app": "legacy-shell:index",
    "/visual-alpha": "legacy-shell:retired-alias",
    "/app.js": "legacy-shell:javascript",
    "/styles.css": "legacy-shell:stylesheet",
}


def legacy_route_key(path: str) -> str | None:
    if path in _EXACT_LEGACY_ROUTES:
        return _EXACT_LEGACY_ROUTES[path]
    if path.startswith("/api/v50/agent"):
        normalized = re.sub(
            r"/cases/[^/]+",
            "/cases/{case_id}",
            path,
        )
        normalized = re.sub(
            r"/jobs/[^/]+",
            "/jobs/{job_id}",
            normalized,
        )
        return f"legacy-agent-api:{normalized}"
    return None
