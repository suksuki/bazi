from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

from pydantic import Field

from v30.config import V30Settings, load_settings
from v30.contracts import V30Model
from v30.storage.repository import _default_postgres_connect


M3_SNAPSHOT_FAMILY = "m3_core_spine"


class M3SnapshotWriteResult(V30Model):
    snapshot_id: str
    backend: str
    searchable: bool
    rows: dict[str, int] = Field(default_factory=dict)
    error: str | None = None


def upsert_m3_knowledge_unit_sql() -> str:
    return """
INSERT INTO v30_m3_knowledge_units (unit_id, unit_type, domain, family, pack_id, pack_version, payload)
VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb)
ON CONFLICT (unit_id)
DO UPDATE SET
  unit_type = EXCLUDED.unit_type,
  domain = EXCLUDED.domain,
  family = EXCLUDED.family,
  pack_id = EXCLUDED.pack_id,
  pack_version = EXCLUDED.pack_version,
  payload = EXCLUDED.payload,
  updated_at = NOW();
""".strip()


def upsert_m3_rule_spec_sql() -> str:
    return """
INSERT INTO v30_m3_rule_specs (rule_id, domain, decision_state, payload)
VALUES (%s, %s, %s, %s::jsonb)
ON CONFLICT (rule_id)
DO UPDATE SET
  domain = EXCLUDED.domain,
  decision_state = EXCLUDED.decision_state,
  payload = EXCLUDED.payload,
  updated_at = NOW();
""".strip()


def upsert_m3_portrait_asset_sql() -> str:
    return """
INSERT INTO v30_m3_portrait_assets (asset_id, asset_type, domain, payload)
VALUES (%s, %s, %s, %s::jsonb)
ON CONFLICT (asset_id)
DO UPDATE SET
  asset_type = EXCLUDED.asset_type,
  domain = EXCLUDED.domain,
  payload = EXCLUDED.payload,
  updated_at = NOW();
""".strip()


def insert_m3_validation_snapshot_sql() -> str:
    return """
INSERT INTO v30_m3_validation_snapshots (snapshot_id, family, payload)
VALUES (%s, %s, %s::jsonb)
ON CONFLICT (snapshot_id)
DO UPDATE SET
  family = EXCLUDED.family,
  payload = EXCLUDED.payload;
""".strip()


def upsert_m3_source_backlog_sql() -> str:
    return """
INSERT INTO v30_m3_source_backlog (
  backlog_id, source_family_id, queue_state, priority, review_status, target_domains, payload
)
VALUES (%s, %s, %s, %s, %s, %s::jsonb, %s::jsonb)
ON CONFLICT (backlog_id)
DO UPDATE SET
  source_family_id = EXCLUDED.source_family_id,
  queue_state = EXCLUDED.queue_state,
  priority = EXCLUDED.priority,
  review_status = EXCLUDED.review_status,
  target_domains = EXCLUDED.target_domains,
  payload = EXCLUDED.payload,
  updated_at = NOW();
""".strip()


def select_m3_source_backlog_sql() -> str:
    return """
SELECT backlog_id, source_family_id, queue_state, priority, review_status, target_domains, payload
FROM v30_m3_source_backlog
WHERE (%s = '' OR source_family_id = %s)
  AND (%s = '' OR priority = %s)
  AND (%s = '' OR queue_state = %s)
  AND (%s = '' OR review_status = %s)
  AND (%s = '' OR target_domains ? %s)
ORDER BY priority ASC, source_family_id ASC
LIMIT %s;
""".strip()


def query_m3_source_backlog_from_postgres(
    *,
    source_family_id: str = "",
    priority: str = "",
    queue_state: str = "",
    review_status: str = "",
    target_domain: str = "",
    limit: int = 50,
    settings: V30Settings | None = None,
    connect: Callable[[str], Any] | None = None,
) -> dict[str, object]:
    settings = settings or load_settings()
    if not settings.database_url:
        return {
            "backend": "json_fallback",
            "searchable": False,
            "rows": [],
            "row_count": 0,
            "error": None,
        }
    try:
        with (connect or _default_postgres_connect)(settings.database_url) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SET LOCAL statement_timeout = '30s';", ())
                cursor.execute(
                    select_m3_source_backlog_sql(),
                    (
                        source_family_id,
                        source_family_id,
                        priority,
                        priority,
                        queue_state,
                        queue_state,
                        review_status,
                        review_status,
                        target_domain,
                        target_domain,
                        max(1, min(int(limit), 200)),
                    ),
                )
                rows = [_source_backlog_row(row) for row in cursor.fetchall()]
        return {
            "backend": "postgres",
            "searchable": True,
            "rows": rows,
            "row_count": len(rows),
            "error": None,
        }
    except Exception as exc:  # pragma: no cover - depends on external DB state.
        return {
            "backend": "postgres_unavailable",
            "searchable": False,
            "rows": [],
            "row_count": 0,
            "error": str(exc),
        }


def write_m3_source_backlog_to_postgres(
    backlog_payload: dict[str, object],
    *,
    settings: V30Settings | None = None,
    connect: Callable[[str], Any] | None = None,
) -> M3SnapshotWriteResult:
    settings = settings or load_settings()
    backlog_id = str(backlog_payload.get("backlog_id") or "")
    if not backlog_id:
        raise ValueError("m3 source backlog requires backlog_id")
    if not settings.database_url:
        return M3SnapshotWriteResult(
            snapshot_id=backlog_id,
            backend="json_fallback",
            searchable=False,
            rows={"source_backlog": 0},
        )
    rows = {"source_backlog": 0, "validation_snapshots": 0}
    try:
        with (connect or _default_postgres_connect)(settings.database_url) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SET LOCAL lock_timeout = '10s';", ())
                cursor.execute("SET LOCAL statement_timeout = '120s';", ())
                for item in _dict_rows(backlog_payload.get("backlog_rows")):
                    cursor.execute(
                        upsert_m3_source_backlog_sql(),
                        (
                            str(item.get("backlog_item_id") or ""),
                            str(item.get("source_family_id") or ""),
                            str(item.get("queue_state") or ""),
                            str(item.get("priority") or ""),
                            str(item.get("review_status") or ""),
                            json.dumps(item.get("target_domains") or [], ensure_ascii=False),
                            json.dumps(item, ensure_ascii=False),
                        ),
                    )
                    rows["source_backlog"] += 1
                cursor.execute(
                    insert_m3_validation_snapshot_sql(),
                    (
                        backlog_id,
                        "m3_source_extraction_backlog",
                        json.dumps(backlog_payload, ensure_ascii=False),
                    ),
                )
                rows["validation_snapshots"] = 1
            connection.commit()
    except Exception as exc:  # pragma: no cover - depends on external DB state.
        return M3SnapshotWriteResult(
            snapshot_id=backlog_id,
            backend="postgres_unavailable",
            searchable=False,
            rows=rows,
            error=str(exc),
        )
    return M3SnapshotWriteResult(
        snapshot_id=backlog_id,
        backend="postgres",
        searchable=True,
        rows=rows,
    )


def write_m3_snapshot_to_postgres(
    snapshot: dict[str, object],
    *,
    settings: V30Settings | None = None,
    connect: Callable[[str], Any] | None = None,
) -> M3SnapshotWriteResult:
    settings = settings or load_settings()
    snapshot_id = str(snapshot.get("snapshot_id") or "")
    if not snapshot_id:
        raise ValueError("m3 snapshot requires snapshot_id")
    if not settings.database_url:
        return M3SnapshotWriteResult(
            snapshot_id=snapshot_id,
            backend="json_fallback",
            searchable=False,
        )
    rows = {
        "knowledge_units": 0,
        "rule_specs": 0,
        "portrait_assets": 0,
        "validation_snapshots": 0,
    }
    try:
        with (connect or _default_postgres_connect)(settings.database_url) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SET LOCAL lock_timeout = '10s';", ())
                cursor.execute("SET LOCAL statement_timeout = '120s';", ())
                for unit in _dict_rows(snapshot.get("knowledge_units")):
                    cursor.execute(
                        upsert_m3_knowledge_unit_sql(),
                        (
                            str(unit.get("unit_id") or ""),
                            str(unit.get("unit_type") or ""),
                            str(unit.get("domain") or ""),
                            str(unit.get("family") or ""),
                            str(unit.get("pack_id") or ""),
                            str(unit.get("pack_version") or ""),
                            json.dumps(unit, ensure_ascii=False),
                        ),
                    )
                    rows["knowledge_units"] += 1
                for rule in _dict_rows(snapshot.get("rule_specs")):
                    cursor.execute(
                        upsert_m3_rule_spec_sql(),
                        (
                            str(rule.get("rule_id") or ""),
                            str(rule.get("domain") or ""),
                            str(rule.get("decision_state") or ""),
                            json.dumps(rule, ensure_ascii=False),
                        ),
                    )
                    rows["rule_specs"] += 1
                for asset in _dict_rows(snapshot.get("portrait_assets")):
                    cursor.execute(
                        upsert_m3_portrait_asset_sql(),
                        (
                            str(asset.get("asset_id") or ""),
                            str(asset.get("asset_type") or ""),
                            str(asset.get("domain") or ""),
                            json.dumps(asset, ensure_ascii=False),
                        ),
                    )
                    rows["portrait_assets"] += 1
                cursor.execute(
                    insert_m3_validation_snapshot_sql(),
                    (
                        snapshot_id,
                        M3_SNAPSHOT_FAMILY,
                        json.dumps(snapshot, ensure_ascii=False),
                    ),
                )
                rows["validation_snapshots"] = 1
            connection.commit()
    except Exception as exc:  # pragma: no cover - depends on external DB state.
        return M3SnapshotWriteResult(
            snapshot_id=snapshot_id,
            backend="postgres_unavailable",
            searchable=False,
            rows=rows,
            error=str(exc),
        )
    return M3SnapshotWriteResult(
        snapshot_id=snapshot_id,
        backend="postgres",
        searchable=True,
        rows=rows,
    )


def _dict_rows(value: object) -> list[dict[str, object]]:
    if not isinstance(value, list):
        return []
    return [row for row in value if isinstance(row, dict)]


def _source_backlog_row(row: object) -> dict[str, object]:
    if isinstance(row, dict):
        payload = row.get("payload")
        return payload if isinstance(payload, dict) else dict(row)
    if isinstance(row, (tuple, list)) and len(row) >= 7:
        payload = row[6]
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except json.JSONDecodeError:
                payload = {}
        if isinstance(payload, dict):
            return payload
        return {
            "backlog_item_id": row[0],
            "source_family_id": row[1],
            "queue_state": row[2],
            "priority": row[3],
            "review_status": row[4],
            "target_domains": row[5],
        }
    return {}
