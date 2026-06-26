from __future__ import annotations

from typing import Any


PRODUCTION_REPLAY_METADATA_VERSION = "v30.production_replay_metadata.v1"
PRODUCTION_REPLAY_METADATA_SUMMARY_VERSION = "v30.production_replay_metadata_summary.v1"
PRODUCTION_REPLAY_METADATA_BOUNDARY = (
    "production_replay_metadata_tags_do_not_import_private_content_or_mutate_chart_facts"
)

_FORBIDDEN_METADATA_KEYS = {
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


def build_production_replay_metadata(
    real_case_fixture: dict[str, Any],
    *,
    api_projection_contract: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build metadata-only tags for future production replay rows."""

    if not isinstance(real_case_fixture, dict) or not real_case_fixture:
        return {}
    api_projection_contract = api_projection_contract if isinstance(api_projection_contract, dict) else {}
    leak_scan = api_projection_contract.get("leak_scan", {})
    leak_scan = leak_scan if isinstance(leak_scan, dict) else {}
    status = _status(real_case_fixture.get("status"))
    practical_contracts = real_case_fixture.get("practical_domain_contracts", {})
    practical_contracts = practical_contracts if isinstance(practical_contracts, dict) else {}
    m4_ready = bool(real_case_fixture.get("model_signal_ready")) and status == "ready"
    m5_ready = int(real_case_fixture.get("ranked_decision_count", 0) or 0) >= 3 and status == "ready"
    m6_ready = _m6_contract_ready(practical_contracts) and status == "ready"
    projection_ready = (
        bool(real_case_fixture.get("projection_matrix_ready"))
        or api_projection_contract.get("version") == "v30.api_projection_contract.v1"
    )
    leak_passed = leak_scan.get("passed") is True if leak_scan else True
    metadata = {
        "version": PRODUCTION_REPLAY_METADATA_VERSION,
        "case_id": str(real_case_fixture.get("case_id") or ""),
        "source": "synthetic_real_case_calibration_pack",
        "calendar_type": _calendar_type(real_case_fixture.get("calendar_type")),
        "lunar_is_leap_month": bool(real_case_fixture.get("lunar_is_leap_month")),
        "use_true_solar_time": bool(real_case_fixture.get("use_true_solar_time")),
        "unknown_hour": bool(real_case_fixture.get("unknown_hour")),
        "unknown_gender": real_case_fixture.get("gender_status") == "unknown",
        "chart_status": status,
        "has_pillars": bool(real_case_fixture.get("has_pillars")),
        "m4_model_signal_ready": m4_ready,
        "m5_ranked_decision_ready": m5_ready,
        "m6_practical_contract_ready": m6_ready,
        "m6_practical_domain_contract_count": len(practical_contracts),
        "api_projection_contract_ready": projection_ready,
        "projection_leak_scan_passed": bool(leak_passed),
        "readiness_tags": _readiness_tags(status),
        "boundary_tags": _boundary_tags(real_case_fixture),
        "module_contract_tags": _module_contract_tags(
            m4_ready=m4_ready,
            m5_ready=m5_ready,
            m6_ready=m6_ready,
            projection_ready=bool(projection_ready),
            leak_passed=bool(leak_passed),
        ),
        "privacy_guard": {
            "metadata_only": True,
            "no_private_user_content": True,
            "no_chart_fact_mutation": True,
            "forbidden_key_scan_passed": True,
        },
        "boundary": PRODUCTION_REPLAY_METADATA_BOUNDARY,
    }
    metadata["privacy_guard"]["forbidden_key_scan_passed"] = not _contains_forbidden_keys(metadata)
    return metadata


def summarize_production_replay_metadata(rows: list[dict[str, Any]]) -> dict[str, Any]:
    clean_rows = [
        row for row in rows
        if isinstance(row, dict) and row.get("version") == PRODUCTION_REPLAY_METADATA_VERSION
    ]
    privacy_pass_count = sum(
        1 for row in clean_rows
        if isinstance(row.get("privacy_guard"), dict)
        and row["privacy_guard"].get("metadata_only") is True
        and row["privacy_guard"].get("no_private_user_content") is True
        and row["privacy_guard"].get("no_chart_fact_mutation") is True
        and row["privacy_guard"].get("forbidden_key_scan_passed") is True
    )
    return {
        "version": PRODUCTION_REPLAY_METADATA_SUMMARY_VERSION,
        "row_count": len(clean_rows),
        "ready_count": sum(1 for row in clean_rows if row.get("chart_status") == "ready"),
        "pending_count": sum(1 for row in clean_rows if row.get("chart_status") == "pending"),
        "blocked_count": sum(1 for row in clean_rows if row.get("chart_status") == "blocked"),
        "calendar_types": sorted({str(row.get("calendar_type")) for row in clean_rows if row.get("calendar_type")}),
        "leap_month_count": sum(1 for row in clean_rows if row.get("lunar_is_leap_month") is True),
        "true_solar_count": sum(1 for row in clean_rows if row.get("use_true_solar_time") is True),
        "unknown_hour_count": sum(1 for row in clean_rows if row.get("unknown_hour") is True),
        "unknown_gender_count": sum(1 for row in clean_rows if row.get("unknown_gender") is True),
        "m4_ready_count": sum(1 for row in clean_rows if row.get("m4_model_signal_ready") is True),
        "m5_ready_count": sum(1 for row in clean_rows if row.get("m5_ranked_decision_ready") is True),
        "m6_ready_count": sum(1 for row in clean_rows if row.get("m6_practical_contract_ready") is True),
        "projection_contract_ready_count": sum(1 for row in clean_rows if row.get("api_projection_contract_ready") is True),
        "projection_leak_scan_pass_count": sum(1 for row in clean_rows if row.get("projection_leak_scan_passed") is True),
        "privacy_guard_pass_count": privacy_pass_count,
        "metadata_only_boundary_count": sum(
            1 for row in clean_rows if row.get("boundary") == PRODUCTION_REPLAY_METADATA_BOUNDARY
        ),
        "boundary": "production_replay_metadata_summary_trains_replay_selection_policy_not_chart_facts",
    }


def _status(value: object) -> str:
    status = str(value or "")
    if status in {"ready", "pending", "blocked"}:
        return status
    if status == "unsupported":
        return "blocked"
    return "pending"


def _calendar_type(value: object) -> str:
    calendar_type = str(value or "")
    return calendar_type if calendar_type in {"solar", "lunar"} else "unknown"


def _m6_contract_ready(practical_contracts: dict[str, Any]) -> bool:
    if len(practical_contracts) < 5:
        return False
    for contract in practical_contracts.values():
        if not isinstance(contract, dict):
            return False
        if contract.get("version") != "v30.practical_domain_reading.v2":
            return False
        if contract.get("calculation_basis_version") != "v30.practical_domain_calculation_basis.v1":
            return False
        if contract.get("model_signal_context_version") != "v30.practical_model_signal_context.v1":
            return False
        if int(contract.get("ranked_decision_link_count", 0) or 0) < 3:
            return False
        if bool(contract.get("raw_score_leak")):
            return False
    return True


def _readiness_tags(status: str) -> list[str]:
    return [f"chart_{status}"]


def _boundary_tags(real_case_fixture: dict[str, Any]) -> list[str]:
    tags = []
    if real_case_fixture.get("calendar_type"):
        tags.append(f"calendar_{_calendar_type(real_case_fixture.get('calendar_type'))}")
    if real_case_fixture.get("lunar_is_leap_month"):
        tags.append("lunar_leap_month")
    if real_case_fixture.get("use_true_solar_time"):
        tags.append("true_solar_time")
    if real_case_fixture.get("unknown_hour"):
        tags.append("unknown_hour")
    if real_case_fixture.get("gender_status") == "unknown":
        tags.append("unknown_gender")
    return sorted(set(tags))


def _module_contract_tags(
    *,
    m4_ready: bool,
    m5_ready: bool,
    m6_ready: bool,
    projection_ready: bool,
    leak_passed: bool,
) -> list[str]:
    tags = []
    tags.append("m4_model_signal_ready" if m4_ready else "m4_model_signal_pending")
    tags.append("m5_ranked_decision_ready" if m5_ready else "m5_ranked_decision_pending")
    tags.append("m6_practical_contract_ready" if m6_ready else "m6_practical_contract_pending")
    tags.append("api_projection_ready" if projection_ready else "api_projection_pending")
    tags.append("projection_leak_scan_passed" if leak_passed else "projection_leak_scan_pending")
    return tags


def _contains_forbidden_keys(value: object) -> bool:
    if isinstance(value, dict):
        for key, nested in value.items():
            if str(key) in _FORBIDDEN_METADATA_KEYS:
                return True
            if _contains_forbidden_keys(nested):
                return True
    if isinstance(value, list):
        return any(_contains_forbidden_keys(row) for row in value)
    return False
