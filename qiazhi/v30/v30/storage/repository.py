from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any, Protocol

from v30.config import V30Settings
from v30.contracts import CoreRuntimeResult
from v30.storage.postgres import select_reading_sql, select_trace_sql, upsert_reading_sql, upsert_trace_sql


class RuntimeRepository(Protocol):
    def save_runtime(self, runtime: CoreRuntimeResult) -> None: ...

    def get_runtime_payload(self, reading_id: str) -> dict[str, object] | None: ...

    def list_runtime_payloads(
        self,
        *,
        actor_id: str = "",
        session_id: str = "",
        limit: int = 20,
    ) -> list[dict[str, object]]: ...

    def save_trace(self, runtime: CoreRuntimeResult) -> None: ...

    def get_trace_payload(self, trace_id: str) -> dict[str, object] | None: ...


class MemoryRuntimeRepository:
    def __init__(self) -> None:
        self._rows: dict[str, CoreRuntimeResult] = {}
        self._traces: dict[str, CoreRuntimeResult] = {}

    def save_runtime(self, runtime: CoreRuntimeResult) -> None:
        self._rows[runtime.reading_id] = runtime

    def get_runtime_payload(self, reading_id: str) -> dict[str, object] | None:
        runtime = self._rows.get(reading_id)
        return runtime.model_dump(mode="json") if runtime is not None else None

    def list_runtime_payloads(
        self,
        *,
        actor_id: str = "",
        session_id: str = "",
        limit: int = 20,
    ) -> list[dict[str, object]]:
        rows = [runtime.model_dump(mode="json") for runtime in self._rows.values()]
        return _filter_history_payloads(rows, actor_id=actor_id, session_id=session_id, limit=limit)

    def save_trace(self, runtime: CoreRuntimeResult) -> None:
        self._traces[runtime.trace_id] = runtime

    def get_trace_payload(self, trace_id: str) -> dict[str, object] | None:
        runtime = self._traces.get(trace_id)
        return runtime.model_dump(mode="json") if runtime is not None else None


class LocalJsonRuntimeRepository:
    def __init__(self, settings: V30Settings):
        self._reading_root = settings.runtime_dir / "readings"
        self._trace_root = settings.runtime_dir / "traces"

    def save_runtime(self, runtime: CoreRuntimeResult) -> None:
        path = self._reading_path(runtime.reading_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(runtime.model_dump(mode="json"), ensure_ascii=False, indent=2), encoding="utf-8")

    def get_runtime_payload(self, reading_id: str) -> dict[str, object] | None:
        path = self._reading_path(reading_id)
        if not path.exists():
            return None
        payload = json.loads(path.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else None

    def list_runtime_payloads(
        self,
        *,
        actor_id: str = "",
        session_id: str = "",
        limit: int = 20,
    ) -> list[dict[str, object]]:
        if not self._reading_root.exists():
            return []
        rows: list[dict[str, object]] = []
        for path in sorted(self._reading_root.glob("*.json")):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict):
                rows.append(payload)
        return _filter_history_payloads(rows, actor_id=actor_id, session_id=session_id, limit=limit)

    def save_trace(self, runtime: CoreRuntimeResult) -> None:
        path = self._trace_path(runtime.trace_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(runtime.model_dump(mode="json"), ensure_ascii=False, indent=2), encoding="utf-8")

    def get_trace_payload(self, trace_id: str) -> dict[str, object] | None:
        path = self._trace_path(trace_id)
        if not path.exists():
            return None
        payload = json.loads(path.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else None

    def _reading_path(self, reading_id: str) -> Path:
        return self._reading_root / f"{_safe_file_id(reading_id)}.json"

    def _trace_path(self, trace_id: str) -> Path:
        return self._trace_root / f"{_safe_file_id(trace_id)}.json"


def _safe_file_id(value: str) -> str:
    return value.replace("/", "_")


class PostgresRuntimeRepository:
    def __init__(self, settings: V30Settings, connect: Callable[[str], Any] | None = None):
        if not settings.database_url:
            raise ValueError("V30_DATABASE_URL is required when V30_REPOSITORY=postgres")
        self._database_url = settings.database_url
        self._connect = connect or _default_postgres_connect

    def save_runtime(self, runtime: CoreRuntimeResult) -> None:
        payload = json.dumps(runtime.model_dump(mode="json"), ensure_ascii=False)
        with self._connect(self._database_url) as connection:
            with connection.cursor() as cursor:
                cursor.execute(upsert_reading_sql(), (runtime.reading_id, payload))
            connection.commit()

    def get_runtime_payload(self, reading_id: str) -> dict[str, object] | None:
        return self._fetch_payload(select_reading_sql(), (reading_id,))

    def list_runtime_payloads(
        self,
        *,
        actor_id: str = "",
        session_id: str = "",
        limit: int = 20,
    ) -> list[dict[str, object]]:
        with self._connect(self._database_url) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT payload FROM v30_readings;", ())
                rows = cursor.fetchall()
        payloads = [
            payload for row in rows
            if row and (payload := _payload_to_dict(row[0])) is not None
        ]
        return _filter_history_payloads(payloads, actor_id=actor_id, session_id=session_id, limit=limit)

    def save_trace(self, runtime: CoreRuntimeResult) -> None:
        payload = json.dumps(runtime.model_dump(mode="json"), ensure_ascii=False)
        with self._connect(self._database_url) as connection:
            with connection.cursor() as cursor:
                cursor.execute(upsert_trace_sql(), (runtime.trace_id, runtime.reading_id, payload))
            connection.commit()

    def get_trace_payload(self, trace_id: str) -> dict[str, object] | None:
        return self._fetch_payload(select_trace_sql(), (trace_id,))

    def _fetch_payload(self, sql: str, params: tuple[str, ...]) -> dict[str, object] | None:
        with self._connect(self._database_url) as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql, params)
                row = cursor.fetchone()
        if row is None:
            return None
        return _payload_to_dict(row[0])


def _payload_to_dict(payload: object) -> dict[str, object] | None:
    if isinstance(payload, dict):
        return payload
    if isinstance(payload, str):
        parsed = json.loads(payload)
        return parsed if isinstance(parsed, dict) else None
    return None


def _filter_history_payloads(
    rows: list[dict[str, object]],
    *,
    actor_id: str,
    session_id: str,
    limit: int,
) -> list[dict[str, object]]:
    limit = max(1, min(limit, 100))
    filtered: list[dict[str, object]] = []
    for payload in rows:
        actor_context = _actor_context(payload)
        if actor_id and actor_context.get("actor_id") != actor_id:
            continue
        if session_id and actor_context.get("session_id") != session_id:
            continue
        filtered.append(payload)
    return sorted(filtered, key=_payload_created_at, reverse=True)[:limit]


def _actor_context(payload: dict[str, object]) -> dict[str, object]:
    question_plan = payload.get("question_plan", {})
    if not isinstance(question_plan, dict):
        return {}
    policy_effect = question_plan.get("policy_effect", {})
    if not isinstance(policy_effect, dict):
        return {}
    actor_context = policy_effect.get("actor_context", {})
    return actor_context if isinstance(actor_context, dict) else {}


def _payload_created_at(payload: dict[str, object]) -> str:
    chart_context = payload.get("chart_context", {})
    if not isinstance(chart_context, dict):
        return ""
    return str(chart_context.get("created_at") or "")


def _default_postgres_connect(database_url: str) -> Any:
    try:
        import psycopg  # type: ignore[import-not-found]
    except ImportError as exc:
        raise RuntimeError("V30_REPOSITORY=postgres requires installing psycopg") from exc
    return psycopg.connect(database_url, connect_timeout=5)


def build_runtime_repository(settings: V30Settings) -> RuntimeRepository:
    if settings.repository == "memory":
        return MemoryRuntimeRepository()
    if settings.repository == "local_json":
        return LocalJsonRuntimeRepository(settings)
    if settings.repository == "postgres":
        return PostgresRuntimeRepository(settings)
    raise ValueError(f"Unsupported V30_REPOSITORY: {settings.repository}")
