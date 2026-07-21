from __future__ import annotations

import os
import threading
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Protocol

from product.database_schema import ensure_product_database_schema


class AgentJobStore(Protocol):
    persistent: bool
    storage_name: str

    def create(self, *, job_id: str, case_id: str, user_id: str | None, payload: dict[str, Any]) -> None: ...
    def append_event(self, *, job_id: str, event: dict[str, Any], status: str | None = None) -> dict[str, Any]: ...
    def get(self, *, job_id: str, user_id: str | None = None) -> dict[str, Any] | None: ...
    def recover_interrupted(self) -> int: ...


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _interrupted_event() -> dict[str, Any]:
    return {
        "event_type": "reading_failed",
        "epistemic_status": "failed",
        "payload": {
            "failure_code": "cognitive_job_interrupted",
            "failure_stage": "runtime_recovery",
            "message": "上一次看盘因服务中断没有完成。命理档案仍在，可以重新开始。",
        },
    }


class MemoryAgentJobStore:
    persistent = False
    storage_name = "memory_job_store"

    def __init__(self) -> None:
        self._jobs: dict[str, dict[str, Any]] = {}
        self._lock = threading.Lock()

    def create(self, *, job_id: str, case_id: str, user_id: str | None, payload: dict[str, Any]) -> None:
        with self._lock:
            self._jobs[job_id] = {
                **deepcopy(payload),
                "job_id": job_id,
                "case_id": case_id,
                "user_id": user_id,
                "status": "queued",
                "events": [],
                "created_at": _now(),
                "updated_at": _now(),
            }

    def append_event(self, *, job_id: str, event: dict[str, Any], status: str | None = None) -> dict[str, Any]:
        with self._lock:
            job = self._jobs[job_id]
            stored = {**deepcopy(event), "sequence": len(job["events"]) + 1, "created_at": _now()}
            job["events"].append(stored)
            job["updated_at"] = _now()
            if status:
                job["status"] = status
            return deepcopy(stored)

    def get(self, *, job_id: str, user_id: str | None = None) -> dict[str, Any] | None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None or (user_id is not None and job.get("user_id") not in {None, user_id}):
                return None
            return deepcopy(job)

    def recover_interrupted(self) -> int:
        recovered = 0
        with self._lock:
            for job in self._jobs.values():
                if job.get("status") not in {"queued", "running"}:
                    continue
                events = list(job.get("events") or [])
                events.append({**_interrupted_event(), "sequence": len(events) + 1, "created_at": _now()})
                job["events"] = events
                job["status"] = "failed"
                job["updated_at"] = _now()
                recovered += 1
        return recovered


class PostgresAgentJobStore:
    persistent = True
    storage_name = "v50_postgresql_jobs"

    def __init__(self, database_url: str) -> None:
        self.database_url = database_url
        ensure_product_database_schema(database_url)

    def _connect(self):
        import psycopg

        return psycopg.connect(self.database_url)

    def create(self, *, job_id: str, case_id: str, user_id: str | None, payload: dict[str, Any]) -> None:
        from psycopg.types.json import Jsonb

        job = {
            **payload,
            "job_id": job_id,
            "case_id": case_id,
            "user_id": user_id,
            "status": "queued",
            "events": [],
            "created_at": _now(),
            "updated_at": _now(),
        }
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO v50_mingli_cognitive_jobs (job_id, case_id, user_id, job_json) VALUES (%s, %s, %s, %s)",
                    (job_id, case_id, user_id, Jsonb(job)),
                )

    def append_event(self, *, job_id: str, event: dict[str, Any], status: str | None = None) -> dict[str, Any]:
        from psycopg.rows import dict_row
        from psycopg.types.json import Jsonb

        with self._connect() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    "SELECT job_json FROM v50_mingli_cognitive_jobs WHERE job_id = %s FOR UPDATE",
                    (job_id,),
                )
                row = cur.fetchone()
                if row is None:
                    raise KeyError(job_id)
                job = dict(row["job_json"])
                events = list(job.get("events") or [])
                stored = {**event, "sequence": len(events) + 1, "created_at": _now()}
                events.append(stored)
                job["events"] = events
                job["updated_at"] = _now()
                if status:
                    job["status"] = status
                cur.execute(
                    "UPDATE v50_mingli_cognitive_jobs SET job_json = %s, updated_at = now() WHERE job_id = %s",
                    (Jsonb(job), job_id),
                )
                return stored

    def get(self, *, job_id: str, user_id: str | None = None) -> dict[str, Any] | None:
        from psycopg.rows import dict_row

        with self._connect() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                if user_id is None:
                    cur.execute("SELECT job_json FROM v50_mingli_cognitive_jobs WHERE job_id = %s", (job_id,))
                else:
                    cur.execute(
                        "SELECT job_json FROM v50_mingli_cognitive_jobs WHERE job_id = %s AND (user_id = %s OR user_id IS NULL)",
                        (job_id, user_id),
                    )
                row = cur.fetchone()
        return dict(row["job_json"]) if row else None

    def recover_interrupted(self) -> int:
        from psycopg.rows import dict_row
        from psycopg.types.json import Jsonb

        recovered = 0
        with self._connect() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    """
                    SELECT job_id, job_json
                    FROM v50_mingli_cognitive_jobs
                    WHERE job_json->>'status' IN ('queued', 'running')
                    FOR UPDATE
                    """
                )
                for row in cur.fetchall():
                    job = dict(row["job_json"])
                    events = list(job.get("events") or [])
                    events.append({**_interrupted_event(), "sequence": len(events) + 1, "created_at": _now()})
                    job["events"] = events
                    job["status"] = "failed"
                    job["updated_at"] = _now()
                    cur.execute(
                        "UPDATE v50_mingli_cognitive_jobs SET job_json = %s, updated_at = now() WHERE job_id = %s",
                        (Jsonb(job), row["job_id"]),
                    )
                    recovered += 1
        return recovered


def build_agent_job_store() -> AgentJobStore:
    database_url = os.getenv("V50_DATABASE_URL", "").strip()
    return PostgresAgentJobStore(database_url) if database_url else MemoryAgentJobStore()
