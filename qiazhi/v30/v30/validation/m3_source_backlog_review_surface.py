from __future__ import annotations

import json
from collections import Counter
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from v30.config import V30Settings
from v30.storage.m3 import query_m3_source_backlog_from_postgres
from v30.validation.m3_source_extraction_backlog import run_m3_source_extraction_backlog


M3_SOURCE_BACKLOG_REVIEW_SURFACE_VERSION = "v30.m3_source_backlog_review_surface.v1"


def run_m3_source_backlog_review_surface(
    *,
    source_family_id: str = "",
    priority: str = "",
    queue_state: str = "",
    review_status: str = "",
    target_domain: str = "",
    limit: int = 50,
    write_db: bool = False,
    artifact_dir: str | Path | None = None,
    settings: V30Settings | None = None,
) -> dict[str, Any]:
    query = query_m3_source_backlog_from_postgres(
        source_family_id=source_family_id,
        priority=priority,
        queue_state=queue_state,
        review_status=review_status,
        target_domain=target_domain,
        limit=limit,
        settings=settings,
    )
    fallback_payload: dict[str, Any] | None = None
    rows = _list_of_mappings(query.get("rows"))
    backend = str(query.get("backend") or "")
    if not rows:
        fallback_payload = run_m3_source_extraction_backlog(
            artifact_dir=artifact_dir,
            write_db=write_db,
        )
        rows = _filter_rows(
            _list_of_mappings(fallback_payload.get("backlog_rows")),
            source_family_id=source_family_id,
            priority=priority,
            queue_state=queue_state,
            review_status=review_status,
            target_domain=target_domain,
            limit=limit,
        )
        backend = f"{backend}_generated_backlog" if backend else "generated_backlog"
    return build_m3_source_backlog_review_surface(
        rows=rows,
        query_backend=backend,
        query_error=str(query.get("error") or ""),
        filters={
            "source_family_id": source_family_id,
            "priority": priority,
            "queue_state": queue_state,
            "review_status": review_status,
            "target_domain": target_domain,
            "limit": limit,
        },
        generated_backlog=fallback_payload,
        artifact_dir=artifact_dir,
    )


def build_m3_source_backlog_review_surface(
    *,
    rows: list[Mapping[str, Any]],
    query_backend: str,
    query_error: str = "",
    filters: Mapping[str, Any] | None = None,
    generated_backlog: Mapping[str, Any] | None = None,
    artifact_dir: str | Path | None = None,
) -> dict[str, Any]:
    reviewed_at = datetime.now(timezone.utc)
    surface_id = f"v30.m3.g5.{reviewed_at.strftime('%Y%m%d%H%M%S%f')}"
    filters = dict(filters or {})
    checks = _checks(rows=rows, query_backend=query_backend)
    decision = _decision(rows=rows, checks=checks)
    payload: dict[str, Any] = {
        "version": M3_SOURCE_BACKLOG_REVIEW_SURFACE_VERSION,
        "surface_id": surface_id,
        "reviewed_at": reviewed_at.isoformat(),
        "status": "completed" if decision["ready_for_admin_review_surface"] else "blocked",
        "decision": decision,
        "filters": filters,
        "query_summary": {
            "backend": query_backend,
            "error": query_error,
            "row_count": len(rows),
            "priority_counts": dict(Counter(str(row.get("priority")) for row in rows)),
            "queue_state_counts": dict(Counter(str(row.get("queue_state")) for row in rows)),
            "review_status_counts": dict(Counter(str(row.get("review_status")) for row in rows)),
            "target_domains": sorted({
                domain
                for row in rows
                for domain in _string_list(row.get("target_domains"))
            }),
            "generated_backlog_id": str((generated_backlog or {}).get("backlog_id") or ""),
        },
        "rows": [dict(row) for row in rows],
        "checks": checks,
        "policy_boundary": {
            "admin_surface_read_only": True,
            "runtime_decision_write_allowed": False,
            "auto_apply_training_allowed": False,
            "policy_pointer_promotion_allowed": False,
            "chart_fact_mutation_allowed": False,
            "fixed_bazi_verdict_allowed": False,
            "runtime_v20_import_allowed": False,
            "boundary": "m3_g5_backlog_surface_is_query_and_review_only_not_runtime_policy",
        },
        "next_mainline_selection": _next_selection(decision),
        "boundary": "m3_g5_exposes_source_backlog_for_admin_training_review_without_mutating_bazi_runtime",
    }
    if artifact_dir is not None:
        payload["artifact_uri"] = str(_write_artifact(payload, Path(artifact_dir)))
    return payload


def _filter_rows(
    rows: list[Mapping[str, Any]],
    *,
    source_family_id: str,
    priority: str,
    queue_state: str,
    review_status: str,
    target_domain: str,
    limit: int,
) -> list[Mapping[str, Any]]:
    result: list[Mapping[str, Any]] = []
    for row in rows:
        if source_family_id and row.get("source_family_id") != source_family_id:
            continue
        if priority and row.get("priority") != priority:
            continue
        if queue_state and row.get("queue_state") != queue_state:
            continue
        if review_status and row.get("review_status") != review_status:
            continue
        if target_domain and target_domain not in _string_list(row.get("target_domains")):
            continue
        result.append(row)
        if len(result) >= max(1, min(int(limit), 200)):
            break
    return result


def _checks(*, rows: list[Mapping[str, Any]], query_backend: str) -> list[dict[str, Any]]:
    return [
        {
            "check_id": "query_surface_has_backend",
            "passed": bool(query_backend),
            "expected": "review surface records postgres, fallback, or generated backlog backend",
        },
        {
            "check_id": "query_surface_returns_review_rows",
            "passed": len(rows) >= 1,
            "expected": "review surface returns at least one backlog row for current filters",
        },
        {
            "check_id": "rows_have_filterable_fields",
            "passed": all(
                row.get("source_family_id")
                and row.get("priority")
                and row.get("queue_state")
                and row.get("review_status")
                and _string_list(row.get("target_domains"))
                for row in rows
            ),
            "expected": "rows include source family, priority, queue state, review status, and target domains",
        },
        {
            "check_id": "rows_have_review_evidence_links",
            "passed": all(
                _string_list(row.get("linked_knowledge_unit_ids"))
                and isinstance(row.get("evidence_link_counts"), Mapping)
                for row in rows
            ),
            "expected": "rows include evidence links for admin/training review",
        },
        {
            "check_id": "surface_is_read_only",
            "passed": all(
                not bool(row.get("runtime_v20_import_allowed"))
                and not bool(row.get("chart_fact_mutation_allowed"))
                and not bool(row.get("policy_pointer_promotion_allowed"))
                and not bool(row.get("fixed_bazi_verdict_allowed"))
                for row in rows
            ),
            "expected": "rows cannot import V20 runtime, mutate facts, promote pointers, or create fixed verdicts",
        },
    ]


def _decision(*, rows: list[Mapping[str, Any]], checks: list[Mapping[str, Any]]) -> dict[str, Any]:
    passed = sum(1 for row in checks if row.get("passed"))
    ready = passed == len(checks)
    return {
        "decision_status": "m3_g5_backlog_review_surface_ready" if ready else "m3_g5_backlog_review_surface_blocked",
        "ready_for_admin_review_surface": ready,
        "ready_for_pointer_promotion": False,
        "policy_pointer_promotion_allowed": False,
        "chart_fact_mutation_allowed": False,
        "fixed_bazi_verdict_allowed": False,
        "runtime_v20_import_allowed": False,
        "row_count": len(rows),
        "passed_checks": passed,
        "total_checks": len(checks),
    }


def _next_selection(decision: Mapping[str, Any]) -> dict[str, Any]:
    if decision.get("ready_for_admin_review_surface"):
        return {
            "next_task": "M3-G6 Source Backlog Closeout And M3 Seal Review",
            "reason": "G5 backlog review surface is ready; next close M3 backlog flow before deciding whether to return to M5.",
            "full_pytest_required": False,
            "full_518k_required": False,
        }
    return {
        "next_task": "M3-G5 Remediation",
        "reason": "G5 review surface checks are blocked; fix storage/query/filter surface before continuing M3.",
        "full_pytest_required": False,
        "full_518k_required": False,
    }


def _list_of_mappings(value: Any) -> list[Mapping[str, Any]]:
    if not isinstance(value, list):
        return []
    return [row for row in value if isinstance(row, Mapping)]


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(row) for row in value if str(row)]


def _write_artifact(payload: Mapping[str, Any], artifact_dir: Path) -> Path:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    path = artifact_dir / f"{payload['surface_id']}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
