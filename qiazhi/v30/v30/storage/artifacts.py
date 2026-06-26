from __future__ import annotations

import json
import os
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import Field

from v30.config import V30Settings, load_settings
from v30.contracts import V30Model
from v30.storage.repository import _default_postgres_connect, _payload_to_dict


ARTIFACT_FAMILY_518K = "518k_validation"
ARTIFACT_FAMILY_QUESTION_POLICY_COMPARISON = "question_policy_comparison"
ARTIFACT_INDEX_ID_518K = "v30.518k.validation_index.v1"


class ArtifactIndexWriteResult(V30Model):
    artifact_record_id: str
    artifact_search_backend: str
    artifact_searchable: bool
    error: str | None = None


class Validation518KArtifactRecord(V30Model):
    artifact_record_id: str
    run_id: str
    mode: str
    case_count: int
    promotion_signal: str
    artifact_uri: str | None = None
    index_entry_uri: str | None = None
    coverage_metrics: dict[str, object] = Field(default_factory=dict)
    drift_metrics: dict[str, object] = Field(default_factory=dict)
    failure_cluster_count: int = 0
    created_at: str | None = None


class Validation518KArtifactSearchResult(V30Model):
    backend: str
    searchable: bool
    count: int
    artifacts: list[Validation518KArtifactRecord] = Field(default_factory=list)
    fallback_used: bool = False
    error: str | None = None


class UnifiedValidationArtifactRecord(V30Model):
    artifact_record_id: str
    family: str
    runtime_path: str
    payload: dict[str, object] = Field(default_factory=dict)
    created_at: str | None = None


class UnifiedValidationArtifactSearchResult(V30Model):
    backend: str
    searchable: bool
    count: int
    artifacts: list[UnifiedValidationArtifactRecord] = Field(default_factory=list)
    fallback_used: bool = False
    error: str | None = None


def artifact_record_id_for_518k(run_id: str) -> str:
    return f"v30.518k.artifact.{run_id}"


def artifact_record_id_for_question_policy_comparison(candidate_id: str) -> str:
    return f"v30.question_policy_comparison.artifact.{candidate_id}"


def upsert_artifact_sql() -> str:
    return """
INSERT INTO v30_artifacts (artifact_id, family, runtime_path, payload)
VALUES (%s, %s, %s, %s::jsonb)
ON CONFLICT (artifact_id)
DO UPDATE SET family = EXCLUDED.family, runtime_path = EXCLUDED.runtime_path, payload = EXCLUDED.payload;
""".strip()


def select_518k_artifacts_sql() -> str:
    return """
SELECT artifact_id, runtime_path, payload, created_at
FROM v30_artifacts
WHERE family = %s
  AND (%s = '' OR payload->>'mode' = %s)
  AND (%s = '' OR payload->>'promotion_signal' = %s)
  AND (%s = '' OR payload->>'run_id' = %s)
ORDER BY created_at DESC
LIMIT %s;
""".strip()


def select_validation_artifacts_sql() -> str:
    return """
SELECT artifact_id, family, runtime_path, payload, created_at
FROM v30_artifacts
WHERE (%s = '' OR family = %s)
  AND (%s = '' OR payload->>'candidate_id' = %s)
  AND (%s = '' OR payload->>'run_id' = %s)
ORDER BY created_at DESC
LIMIT %s;
""".strip()


def index_518k_validation_artifact(
    result: Any,
    *,
    settings: V30Settings | None = None,
    connect: Callable[[str], Any] | None = None,
) -> ArtifactIndexWriteResult:
    settings = settings or load_settings()
    record_id = str(getattr(result, "artifact_record_id", None) or artifact_record_id_for_518k(result.run_id))
    if not settings.database_url:
        return ArtifactIndexWriteResult(
            artifact_record_id=record_id,
            artifact_search_backend="json_fallback",
            artifact_searchable=False,
        )
    payload = _payload_from_validation_result(result, record_id)
    try:
        with (connect or _default_postgres_connect)(settings.database_url) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    upsert_artifact_sql(),
                    (
                        record_id,
                        ARTIFACT_FAMILY_518K,
                        str(getattr(result, "artifact_uri", "") or ""),
                        json.dumps(payload, ensure_ascii=False),
                    ),
                )
            connection.commit()
    except Exception as exc:  # pragma: no cover - defensive path depends on external DB state.
        return ArtifactIndexWriteResult(
            artifact_record_id=record_id,
            artifact_search_backend="postgres_unavailable",
            artifact_searchable=False,
            error=str(exc),
        )
    return ArtifactIndexWriteResult(
        artifact_record_id=record_id,
        artifact_search_backend="postgres",
        artifact_searchable=True,
    )


def index_question_policy_comparison_artifact(
    comparison: Any,
    *,
    settings: V30Settings | None = None,
    connect: Callable[[str], Any] | None = None,
) -> ArtifactIndexWriteResult:
    settings = settings or load_settings()
    record_id = str(
        getattr(comparison, "artifact_record_id", None)
        or artifact_record_id_for_question_policy_comparison(comparison.candidate_id)
    )
    if not settings.database_url:
        return ArtifactIndexWriteResult(
            artifact_record_id=record_id,
            artifact_search_backend="json_fallback",
            artifact_searchable=False,
        )
    payload = _payload_from_question_policy_comparison(comparison, record_id)
    payload["artifact_search_backend"] = "postgres"
    payload["artifact_searchable"] = True
    try:
        with (connect or _default_postgres_connect)(settings.database_url) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    upsert_artifact_sql(),
                    (
                        record_id,
                        ARTIFACT_FAMILY_QUESTION_POLICY_COMPARISON,
                        str(getattr(comparison, "artifact_uri", "") or ""),
                        json.dumps(payload, ensure_ascii=False),
                    ),
                )
            connection.commit()
    except Exception as exc:  # pragma: no cover - defensive path depends on external DB state.
        return ArtifactIndexWriteResult(
            artifact_record_id=record_id,
            artifact_search_backend="postgres_unavailable",
            artifact_searchable=False,
            error=str(exc),
        )
    return ArtifactIndexWriteResult(
        artifact_record_id=record_id,
        artifact_search_backend="postgres",
        artifact_searchable=True,
    )


def search_validation_artifacts(
    *,
    settings: V30Settings | None = None,
    family: str = "",
    candidate_id: str = "",
    run_id: str = "",
    limit: int = 20,
    connect: Callable[[str], Any] | None = None,
) -> UnifiedValidationArtifactSearchResult:
    settings = settings or load_settings()
    clean_limit = min(max(int(limit), 1), 100)
    if settings.database_url:
        try:
            rows = _search_validation_artifacts_postgres(
                settings=settings,
                family=family,
                candidate_id=candidate_id,
                run_id=run_id,
                limit=clean_limit,
                connect=connect,
            )
            return UnifiedValidationArtifactSearchResult(
                backend="postgres",
                searchable=True,
                count=len(rows),
                artifacts=rows,
            )
        except Exception as exc:  # pragma: no cover - defensive path depends on external DB state.
            fallback = _search_validation_artifacts_json(
                settings=settings,
                family=family,
                candidate_id=candidate_id,
                run_id=run_id,
                limit=clean_limit,
            )
            return fallback.model_copy(update={"fallback_used": True, "error": str(exc)})
    return _search_validation_artifacts_json(
        settings=settings,
        family=family,
        candidate_id=candidate_id,
        run_id=run_id,
        limit=clean_limit,
    )


def search_518k_validation_artifacts(
    *,
    settings: V30Settings | None = None,
    mode: str = "",
    promotion_signal: str = "",
    run_id: str = "",
    limit: int = 20,
    artifact_dir: str | Path | None = None,
    connect: Callable[[str], Any] | None = None,
) -> Validation518KArtifactSearchResult:
    settings = settings or load_settings()
    clean_limit = min(max(int(limit), 1), 100)
    if settings.database_url:
        try:
            rows = _search_518k_artifacts_postgres(
                settings=settings,
                mode=mode,
                promotion_signal=promotion_signal,
                run_id=run_id,
                limit=clean_limit,
                connect=connect,
            )
            return Validation518KArtifactSearchResult(
                backend="postgres",
                searchable=True,
                count=len(rows),
                artifacts=rows,
            )
        except Exception as exc:  # pragma: no cover - defensive path depends on external DB state.
            fallback = _search_518k_artifacts_json(
                settings=settings,
                mode=mode,
                promotion_signal=promotion_signal,
                run_id=run_id,
                limit=clean_limit,
                artifact_dir=artifact_dir,
            )
            return fallback.model_copy(
                update={
                    "backend": "json_fallback",
                    "searchable": False,
                    "fallback_used": True,
                    "error": str(exc),
                }
            )
    return _search_518k_artifacts_json(
        settings=settings,
        mode=mode,
        promotion_signal=promotion_signal,
        run_id=run_id,
        limit=clean_limit,
        artifact_dir=artifact_dir,
    )


def _payload_from_validation_result(result: Any, record_id: str) -> dict[str, object]:
    return {
        "artifact_record_id": record_id,
        "run_id": result.run_id,
        "mode": result.mode,
        "corpus_version": result.corpus_version,
        "target_case_count": result.target_case_count,
        "shard_count": result.shard_count,
        "shard_ids": result.shard_ids,
        "case_count": result.case_count,
        "promotion_signal": result.promotion_signal,
        "failure_cluster_count": len(result.failure_clusters),
        "artifact_uri": result.artifact_uri,
        "index_uri": result.index_uri,
        "index_entry_uri": result.index_entry_uri,
        "coverage_metrics": result.coverage_metrics,
        "drift_metrics": result.drift_metrics,
        "started_at": result.started_at.isoformat(),
        "finished_at": result.finished_at.isoformat(),
    }


def _payload_from_question_policy_comparison(comparison: Any, record_id: str) -> dict[str, object]:
    payload = comparison.model_dump(mode="json") if hasattr(comparison, "model_dump") else {}
    payload["artifact_record_id"] = record_id
    payload["family"] = ARTIFACT_FAMILY_QUESTION_POLICY_COMPARISON
    return payload


def _search_validation_artifacts_postgres(
    *,
    settings: V30Settings,
    family: str,
    candidate_id: str,
    run_id: str,
    limit: int,
    connect: Callable[[str], Any] | None,
) -> list[UnifiedValidationArtifactRecord]:
    rows: list[UnifiedValidationArtifactRecord] = []
    with (connect or _default_postgres_connect)(settings.database_url or "") as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                select_validation_artifacts_sql(),
                (family, family, candidate_id, candidate_id, run_id, run_id, limit),
            )
            fetched = cursor.fetchall()
    for artifact_id, family_value, runtime_path, payload, created_at in fetched:
        rows.append(
            UnifiedValidationArtifactRecord(
                artifact_record_id=str(artifact_id),
                family=str(family_value),
                runtime_path=str(runtime_path or ""),
                payload=_payload_to_dict(payload) or {},
                created_at=_iso_datetime(created_at),
            )
        )
    return rows


def _search_518k_artifacts_postgres(
    *,
    settings: V30Settings,
    mode: str,
    promotion_signal: str,
    run_id: str,
    limit: int,
    connect: Callable[[str], Any] | None,
) -> list[Validation518KArtifactRecord]:
    rows: list[Validation518KArtifactRecord] = []
    with (connect or _default_postgres_connect)(settings.database_url or "") as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                select_518k_artifacts_sql(),
                (
                    ARTIFACT_FAMILY_518K,
                    mode,
                    mode,
                    promotion_signal,
                    promotion_signal,
                    run_id,
                    run_id,
                    limit,
                ),
            )
            fetched = cursor.fetchall()
    for artifact_id, runtime_path, payload, created_at in fetched:
        record_payload = _payload_to_dict(payload) or {}
        if runtime_path and not record_payload.get("artifact_uri"):
            record_payload["artifact_uri"] = runtime_path
        rows.append(_artifact_record_from_payload(record_payload, str(artifact_id), _iso_datetime(created_at)))
    return rows


def _search_validation_artifacts_json(
    *,
    settings: V30Settings,
    family: str,
    candidate_id: str,
    run_id: str,
    limit: int,
) -> UnifiedValidationArtifactSearchResult:
    records: list[UnifiedValidationArtifactRecord] = []
    if family in {"", ARTIFACT_FAMILY_518K}:
        records.extend(_unified_518k_json_records(settings=settings, run_id=run_id))
    if family in {"", ARTIFACT_FAMILY_QUESTION_POLICY_COMPARISON}:
        records.extend(_unified_question_policy_comparison_records(settings=settings, candidate_id=candidate_id))
    if candidate_id:
        records = [
            row for row in records
            if str(row.payload.get("candidate_id") or "") == candidate_id
        ]
    if run_id:
        records = [
            row for row in records
            if str(row.payload.get("run_id") or "") == run_id
        ]
    records = sorted(records, key=lambda row: row.created_at or "", reverse=True)[:limit]
    return UnifiedValidationArtifactSearchResult(
        backend="json_fallback",
        searchable=False,
        count=len(records),
        artifacts=records,
    )


def _unified_518k_json_records(*, settings: V30Settings, run_id: str) -> list[UnifiedValidationArtifactRecord]:
    index = _load_json_object(_artifact_root(settings, None) / "index.json")
    entries = index.get("entries", []) if isinstance(index, dict) else []
    records: list[UnifiedValidationArtifactRecord] = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        if run_id and entry.get("run_id") != run_id:
            continue
        record_id = str(entry.get("artifact_record_id") or artifact_record_id_for_518k(str(entry.get("run_id") or "")))
        records.append(
            UnifiedValidationArtifactRecord(
                artifact_record_id=record_id,
                family=ARTIFACT_FAMILY_518K,
                runtime_path=str(entry.get("artifact_uri") or ""),
                payload=entry,
                created_at=str(entry.get("started_at") or ""),
            )
        )
    return records


def _unified_question_policy_comparison_records(
    *,
    settings: V30Settings,
    candidate_id: str,
) -> list[UnifiedValidationArtifactRecord]:
    root = settings.runtime_dir / "validation" / "question_policy_comparisons"
    index = _load_json_object(root / "index.json")
    entries = index.get("entries", []) if isinstance(index, dict) else []
    records: list[UnifiedValidationArtifactRecord] = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        if candidate_id and entry.get("candidate_id") != candidate_id:
            continue
        path = Path(str(entry.get("artifact_uri") or ""))
        payload = _load_json_object(path)
        if not payload:
            payload = entry
        record_id = str(
            payload.get("artifact_record_id")
            or artifact_record_id_for_question_policy_comparison(str(entry.get("candidate_id") or ""))
        )
        records.append(
            UnifiedValidationArtifactRecord(
                artifact_record_id=record_id,
                family=ARTIFACT_FAMILY_QUESTION_POLICY_COMPARISON,
                runtime_path=str(entry.get("artifact_uri") or payload.get("artifact_uri") or ""),
                payload=payload,
                created_at=str(entry.get("created_at") or payload.get("created_at") or ""),
            )
        )
    return records


def _search_518k_artifacts_json(
    *,
    settings: V30Settings,
    mode: str,
    promotion_signal: str,
    run_id: str,
    limit: int,
    artifact_dir: str | Path | None,
) -> Validation518KArtifactSearchResult:
    index_path = _artifact_root(settings, artifact_dir) / "index.json"
    payload = _load_json_object(index_path)
    entries = payload.get("entries", []) if isinstance(payload, dict) else []
    records: list[Validation518KArtifactRecord] = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        if mode and entry.get("mode") != mode:
            continue
        if promotion_signal and entry.get("promotion_signal") != promotion_signal:
            continue
        if run_id and entry.get("run_id") != run_id:
            continue
        record_id = str(entry.get("artifact_record_id") or artifact_record_id_for_518k(str(entry.get("run_id") or "")))
        records.append(_artifact_record_from_payload(entry, record_id, str(entry.get("started_at") or "")))
    records = sorted(records, key=lambda row: row.created_at or "", reverse=True)[:limit]
    return Validation518KArtifactSearchResult(
        backend="json_fallback",
        searchable=False,
        count=len(records),
        artifacts=records,
    )


def _artifact_record_from_payload(
    payload: dict[str, object],
    artifact_record_id: str,
    created_at: str | None,
) -> Validation518KArtifactRecord:
    return Validation518KArtifactRecord(
        artifact_record_id=str(payload.get("artifact_record_id") or artifact_record_id),
        run_id=str(payload.get("run_id") or ""),
        mode=str(payload.get("mode") or ""),
        case_count=int(payload.get("case_count") or 0),
        promotion_signal=str(payload.get("promotion_signal") or ""),
        artifact_uri=str(payload.get("artifact_uri")) if payload.get("artifact_uri") is not None else None,
        index_entry_uri=str(payload.get("index_entry_uri")) if payload.get("index_entry_uri") is not None else None,
        coverage_metrics=payload.get("coverage_metrics") if isinstance(payload.get("coverage_metrics"), dict) else {},
        drift_metrics=payload.get("drift_metrics") if isinstance(payload.get("drift_metrics"), dict) else {},
        failure_cluster_count=int(payload.get("failure_cluster_count") or 0),
        created_at=created_at,
    )


def _artifact_root(settings: V30Settings, artifact_dir: str | Path | None) -> Path:
    if artifact_dir is not None:
        return Path(artifact_dir)
    env_dir = os.environ.get("V30_518K_ARTIFACT_DIR")
    if env_dir:
        return Path(env_dir)
    return settings.runtime_dir / "validation" / "518k"


def _load_json_object(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _iso_datetime(value: object) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.isoformat()
    return str(value)
