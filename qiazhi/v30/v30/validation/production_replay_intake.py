from __future__ import annotations

from typing import Any

from v30.validation.production_replay_metadata import PRODUCTION_REPLAY_METADATA_VERSION


PRODUCTION_REPLAY_INTAKE_VERSION = "v30.production_replay_intake.v1"
PRODUCTION_REPLAY_INTAKE_BATCH_VERSION = "v30.production_replay_intake_batch.v1"
PRODUCTION_REPLAY_INTAKE_SUMMARY_VERSION = "v30.production_replay_intake_summary.v1"

_FORBIDDEN_INTAKE_KEYS = {
    "answer",
    "birth_date",
    "birth_time",
    "date",
    "datetime",
    "email",
    "free_text",
    "message",
    "name",
    "phone",
    "raw_payload",
    "text",
    "user_answer",
    "user_text",
}


def build_production_replay_intake_row(
    metadata: dict[str, Any],
    *,
    source_artifact: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not isinstance(metadata, dict) or metadata.get("version") != PRODUCTION_REPLAY_METADATA_VERSION:
        return {}
    source_artifact = source_artifact if isinstance(source_artifact, dict) else {}
    privacy = metadata.get("privacy_guard", {})
    privacy = privacy if isinstance(privacy, dict) else {}
    chart_status = _chart_status(metadata.get("chart_status"))
    module_ready = {
        "m4": metadata.get("m4_model_signal_ready") is True,
        "m5": metadata.get("m5_ranked_decision_ready") is True,
        "m6": metadata.get("m6_practical_contract_ready") is True,
        "m8": metadata.get("api_projection_contract_ready") is True,
    }
    privacy_ready = (
        privacy.get("metadata_only") is True
        and privacy.get("no_private_user_content") is True
        and privacy.get("no_chart_fact_mutation") is True
        and privacy.get("forbidden_key_scan_passed") is True
        and not _contains_forbidden_keys(metadata)
    )
    leak_ready = metadata.get("projection_leak_scan_passed") is True
    selection_status = _selection_status(
        chart_status=chart_status,
        module_ready=module_ready,
        privacy_ready=privacy_ready,
        leak_ready=leak_ready,
    )
    row = {
        "version": PRODUCTION_REPLAY_INTAKE_VERSION,
        "intake_id": f"production_replay_intake:{metadata.get('case_id', '')}",
        "case_id": str(metadata.get("case_id") or ""),
        "source": str(metadata.get("source") or "production_replay_metadata"),
        "source_artifact": _source_artifact_summary(source_artifact),
        "chart_status": chart_status,
        "calendar_type": str(metadata.get("calendar_type") or "unknown"),
        "boundary_tags": [str(row) for row in metadata.get("boundary_tags", [])]
        if isinstance(metadata.get("boundary_tags"), list) else [],
        "readiness_tags": [str(row) for row in metadata.get("readiness_tags", [])]
        if isinstance(metadata.get("readiness_tags"), list) else [],
        "module_contract_tags": [str(row) for row in metadata.get("module_contract_tags", [])]
        if isinstance(metadata.get("module_contract_tags"), list) else [],
        "module_readiness": module_ready,
        "selection_status": selection_status,
        "calibration_candidate": selection_status == "calibration_ready",
        "hold_reasons": _hold_reasons(
            chart_status=chart_status,
            module_ready=module_ready,
            privacy_ready=privacy_ready,
            leak_ready=leak_ready,
        ),
        "privacy_guard": {
            "metadata_only": True,
            "no_private_user_content": privacy_ready,
            "no_deterministic_fact_import": True,
            "forbidden_key_scan_passed": True,
        },
        "fact_import_policy": {
            "chart_facts_imported": False,
            "private_content_imported": False,
            "allowed_fields": [
                "case_id",
                "calendar_type",
                "chart_status",
                "boundary_tags",
                "readiness_tags",
                "module_contract_tags",
                "module_readiness",
                "source_artifact",
            ],
            "forbidden_fields": sorted(_FORBIDDEN_INTAKE_KEYS),
        },
        "boundary": "production_replay_intake_selects_calibration_candidates_without_importing_private_content_or_chart_facts",
    }
    row["privacy_guard"]["forbidden_key_scan_passed"] = not _contains_forbidden_keys(row)
    return row


def build_production_replay_intake_batch(
    metadata_rows: list[dict[str, Any]],
    *,
    artifact_review: dict[str, Any] | None = None,
) -> dict[str, Any]:
    artifact_review = artifact_review if isinstance(artifact_review, dict) else {}
    source_artifact = _preferred_source_artifact(artifact_review)
    rows = [
        row
        for metadata in metadata_rows
        if (row := build_production_replay_intake_row(metadata, source_artifact=source_artifact))
    ]
    return {
        "version": PRODUCTION_REPLAY_INTAKE_BATCH_VERSION,
        "rows": rows,
        "summary": summarize_production_replay_intake(rows),
        "artifact_review_link": {
            "version": str(artifact_review.get("version") or ""),
            "status": str(artifact_review.get("status") or ""),
            "artifact_families": [
                str(row.get("family") or "")
                for row in artifact_review.get("artifact_index", [])
                if isinstance(row, dict) and row.get("family")
            ] if isinstance(artifact_review.get("artifact_index"), list) else [],
            "boundary": "artifact_review_link_is_diagnostic_not_fact_source",
        },
        "boundary": "production_replay_intake_batch_is_metadata_only_and_does_not_promote_policy",
    }


def summarize_production_replay_intake(rows: list[dict[str, Any]]) -> dict[str, Any]:
    clean_rows = [
        row for row in rows
        if isinstance(row, dict) and row.get("version") == PRODUCTION_REPLAY_INTAKE_VERSION
    ]
    statuses = _count_by(clean_rows, "selection_status")
    chart_statuses = _count_by(clean_rows, "chart_status")
    return {
        "version": PRODUCTION_REPLAY_INTAKE_SUMMARY_VERSION,
        "row_count": len(clean_rows),
        "calibration_ready_count": statuses.get("calibration_ready", 0),
        "hold_pending_count": statuses.get("hold_pending", 0),
        "blocked_count": statuses.get("blocked", 0),
        "privacy_guard_pass_count": sum(
            1 for row in clean_rows
            if isinstance(row.get("privacy_guard"), dict)
            and row["privacy_guard"].get("metadata_only") is True
            and row["privacy_guard"].get("no_private_user_content") is True
            and row["privacy_guard"].get("no_deterministic_fact_import") is True
            and row["privacy_guard"].get("forbidden_key_scan_passed") is True
        ),
        "chart_status_counts": chart_statuses,
        "selection_status_counts": statuses,
        "calendar_types": sorted({str(row.get("calendar_type")) for row in clean_rows if row.get("calendar_type")}),
        "boundary_tag_counts": _tag_counts(clean_rows, "boundary_tags"),
        "module_ready_counts": {
            "m4": sum(1 for row in clean_rows if row.get("module_readiness", {}).get("m4") is True),
            "m5": sum(1 for row in clean_rows if row.get("module_readiness", {}).get("m5") is True),
            "m6": sum(1 for row in clean_rows if row.get("module_readiness", {}).get("m6") is True),
            "m8": sum(1 for row in clean_rows if row.get("module_readiness", {}).get("m8") is True),
        },
        "boundary": "production_replay_intake_summary_guides_replay_selection_not_chart_fact_generation",
    }


def _chart_status(value: object) -> str:
    status = str(value or "")
    return status if status in {"ready", "pending", "blocked"} else "pending"


def _selection_status(
    *,
    chart_status: str,
    module_ready: dict[str, bool],
    privacy_ready: bool,
    leak_ready: bool,
) -> str:
    if not privacy_ready or not leak_ready or chart_status == "blocked":
        return "blocked"
    if chart_status != "ready":
        return "hold_pending"
    if all(module_ready.values()):
        return "calibration_ready"
    return "hold_pending"


def _hold_reasons(
    *,
    chart_status: str,
    module_ready: dict[str, bool],
    privacy_ready: bool,
    leak_ready: bool,
) -> list[str]:
    reasons = []
    if not privacy_ready:
        reasons.append("privacy_guard_failed")
    if not leak_ready:
        reasons.append("projection_leak_scan_failed")
    if chart_status == "blocked":
        reasons.append("chart_status_blocked")
    if chart_status == "pending":
        reasons.append("chart_status_pending")
    for module_id, ready in module_ready.items():
        if not ready:
            reasons.append(f"{module_id}_not_ready")
    return reasons


def _source_artifact_summary(source_artifact: dict[str, Any]) -> dict[str, Any]:
    return {
        "family": str(source_artifact.get("family") or ""),
        "run_id": str(source_artifact.get("run_id") or ""),
        "artifact_record_id": str(source_artifact.get("artifact_record_id") or ""),
        "artifact_uri": str(source_artifact.get("artifact_uri") or ""),
        "search_backend": str(source_artifact.get("search_backend") or ""),
    }


def _preferred_source_artifact(artifact_review: dict[str, Any]) -> dict[str, Any]:
    rows = artifact_review.get("artifact_index", [])
    if not isinstance(rows, list):
        return {}
    for family in ("518k_sample", "518k_shard", "llm_live_smoke"):
        for row in rows:
            if isinstance(row, dict) and row.get("family") == family:
                return row
    return rows[0] if rows and isinstance(rows[0], dict) else {}


def _count_by(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        value = str(row.get(key) or "")
        if value:
            counts[value] = counts.get(value, 0) + 1
    return counts


def _tag_counts(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        tags = row.get(key, [])
        if not isinstance(tags, list):
            continue
        for tag in tags:
            value = str(tag)
            counts[value] = counts.get(value, 0) + 1
    return counts


def _contains_forbidden_keys(value: object) -> bool:
    if isinstance(value, dict):
        for key, nested in value.items():
            if str(key) in _FORBIDDEN_INTAKE_KEYS:
                return True
            if _contains_forbidden_keys(nested):
                return True
    if isinstance(value, list):
        return any(_contains_forbidden_keys(row) for row in value)
    return False
