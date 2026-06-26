from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

from v30.validation.synthetic_case import SyntheticValidationSuiteResult, run_synthetic_tier


REAL_BUSINESS_BAZI_READING_ACCEPTANCE_VERSION = "v30.real_business_bazi_reading_acceptance.v1"

FORBIDDEN_CUSTOMER_TOKENS = (
    "policy_effect",
    "raw_score",
    "structure_paths",
    "feature_evidence_count",
    "training_signal",
    "policy_payloads",
    "macro_portrait_projections",
)


def run_real_business_bazi_reading_acceptance(*, case_limit: int = 12) -> dict[str, Any]:
    synthetic = run_synthetic_tier("real_case_calibration_pack")
    return build_real_business_bazi_reading_acceptance(
        synthetic_result=synthetic,
        case_limit=case_limit,
    )


def build_real_business_bazi_reading_acceptance(
    *,
    synthetic_result: SyntheticValidationSuiteResult | Mapping[str, Any],
    case_limit: int = 12,
) -> dict[str, Any]:
    payload = (
        synthetic_result.model_dump(mode="json")
        if hasattr(synthetic_result, "model_dump")
        else dict(synthetic_result)
    )
    case_limit = max(1, min(int(case_limit or 12), 30))
    rows = _business_reading_rows(_result_rows(payload), case_limit)
    acceptance_rows = [_acceptance_row(row) for row in rows]
    summary = _summary(payload, acceptance_rows)
    decision = _decision(summary, acceptance_rows)
    return {
        "version": REAL_BUSINESS_BAZI_READING_ACCEPTANCE_VERSION,
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "status": "completed" if decision["business_bazi_reading_ready"] else "blocked",
        "decision": decision,
        "acceptance_summary": summary,
        "acceptance_rows": acceptance_rows,
        "business_scope": {
            "task_id": "B1",
            "title": "Real Business Bazi Reading Acceptance",
            "acceptance_target": "BirthInput to customer-visible Bazi reading loop",
            "required_modules": [
                "M1_birth_input_chart_facts",
                "M2_base_fact_explanation",
                "M3_evidence_rule_knowledge_structure_spine",
                "M4_ten_god_energy_model",
                "M5_ranked_decisions",
                "M6_practical_reading_output",
                "M7_real_case_calibration",
                "M8_customer_projection",
            ],
            "boundary": "b1_accepts_real_business_reading_path_not_ui_polish_or_monitoring_loop",
        },
        "policy_boundary": {
            "full_pytest_run_by_default": False,
            "full_518k_run_by_default": False,
            "policy_pointer_promotion_allowed": False,
            "chart_fact_mutation_allowed": False,
            "training_signal_may_change_chart_facts": False,
            "boundary": "b1_is_read_only_business_acceptance_and_does_not_mutate_chart_facts",
        },
        "next_mainline_selection": _next_selection(decision),
        "boundary": "b1_validates_customer_bazi_calculation_before_question_or_ui_expansion",
    }


def _result_rows(payload: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    rows = payload.get("results", [])
    if not isinstance(rows, list):
        return []
    return [row for row in rows if isinstance(row, Mapping)]


def _business_reading_rows(rows: Sequence[Mapping[str, Any]], case_limit: int) -> list[Mapping[str, Any]]:
    ready_rows = [row for row in rows if _chart_status(row) == "ready"]
    non_ready_rows = [row for row in rows if _chart_status(row) != "ready"]
    selected = ready_rows[:case_limit]
    if len(selected) < case_limit:
        selected.extend(non_ready_rows[: case_limit - len(selected)])
    return selected


def _chart_status(row: Mapping[str, Any]) -> str:
    observed = row.get("observed", {})
    observed = observed if isinstance(observed, Mapping) else {}
    metadata = observed.get("production_replay_metadata", {})
    metadata = metadata if isinstance(metadata, Mapping) else {}
    fixture = observed.get("real_case_fixture", {})
    fixture = fixture if isinstance(fixture, Mapping) else {}
    return str(metadata.get("chart_status") or fixture.get("chart_status") or "")


def _acceptance_row(row: Mapping[str, Any]) -> dict[str, Any]:
    observed = row.get("observed", {})
    observed = observed if isinstance(observed, Mapping) else {}
    fixture = observed.get("real_case_fixture", {})
    fixture = fixture if isinstance(fixture, Mapping) else {}
    metadata = observed.get("production_replay_metadata", {})
    metadata = metadata if isinstance(metadata, Mapping) else {}
    surface = observed.get("customer_reading_surface", {})
    surface = surface if isinstance(surface, Mapping) else {}
    core = observed.get("core_bazi_reading", {})
    core = core if isinstance(core, Mapping) else {}
    projection = observed.get("api_projection_contract", {})
    projection = projection if isinstance(projection, Mapping) else {}
    practical = observed.get("practical_reading_context", {})
    practical = practical if isinstance(practical, Mapping) else {}
    ranked = observed.get("ranked_decisions", {})
    ranked = ranked if isinstance(ranked, Mapping) else {}
    model_signal = observed.get("model_signal_summary", {})
    model_signal = model_signal if isinstance(model_signal, Mapping) else {}

    chart_ready = str(metadata.get("chart_status") or fixture.get("chart_status") or "") == "ready"
    pending_or_blocked = str(metadata.get("chart_status") or fixture.get("chart_status") or "") in {"pending", "blocked"}
    core_ready = (
        core.get("surface_type") == "core_bazi_calculation"
        and len(core.get("four_pillars", []) if isinstance(core.get("four_pillars"), list) else []) >= 4
        and isinstance(core.get("base_fact_summary"), Mapping)
    )
    ranked_ready = {"strength", "structure_pattern", "useful_god"}.issubset(set(ranked))
    practical_domains = practical.get("domain_readings", {})
    practical_ready = (
        str(practical.get("status") or "") in {"ready", "natal_only"}
        and isinstance(practical_domains, Mapping)
        and len(practical_domains) >= 5
    )
    projection_ready = (
        surface.get("surface_type") == "customer_reading_loop"
        and projection.get("version") == "v30.api_projection_contract.v1"
        and projection.get("leak_scan", {}).get("passed") is True
        and projection.get("customer_surface_order", [])[:2] == ["core_bazi_reading", "domain_cards"]
    )
    no_customer_leak = not any(token in str({"surface": surface, "core": core}) for token in FORBIDDEN_CUSTOMER_TOKENS)
    model_ready = isinstance(model_signal, Mapping) and str(model_signal.get("version") or "").startswith("v30.")

    checks = {
        "synthetic_case_passed": bool(row.get("passed")),
        "chart_ready_or_explainable_non_ready": chart_ready or pending_or_blocked,
        "core_bazi_reading_ready": core_ready if chart_ready else True,
        "m4_model_signal_ready": model_ready if chart_ready else True,
        "m5_ranked_decisions_ready": ranked_ready if chart_ready else True,
        "m6_practical_reading_ready": practical_ready if chart_ready else True,
        "m8_customer_projection_ready": projection_ready,
        "customer_projection_no_internal_leak": no_customer_leak,
    }
    failed = [check_id for check_id, passed in checks.items() if not passed]
    return {
        "case_id": str(row.get("case_id") or ""),
        "calendar_type": str(fixture.get("calendar_type") or metadata.get("calendar_type") or ""),
        "chart_status": str(metadata.get("chart_status") or fixture.get("chart_status") or ""),
        "gender_status": str(fixture.get("gender_status") or ""),
        "ready_for_business_reading": not failed,
        "checks": checks,
        "failed_check_ids": failed,
        "customer_surface_type": str(surface.get("surface_type") or ""),
        "core_surface_type": str(core.get("surface_type") or ""),
        "practical_reading_status": str(practical.get("status") or ""),
        "boundary": "case_acceptance_checks_business_reading_shape_not_final_fortune_claim",
    }


def _summary(payload: Mapping[str, Any], rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    ready_rows = [row for row in rows if row.get("ready_for_business_reading")]
    chart_statuses = {str(row.get("chart_status") or "") for row in rows}
    calendar_types = {str(row.get("calendar_type") or "") for row in rows}
    return {
        "source_suite_id": str(payload.get("suite_id") or ""),
        "source_suite_passed": bool(payload.get("passed")),
        "source_case_count": int(payload.get("case_count", 0) or 0),
        "accepted_case_count": len(rows),
        "ready_case_count": len(ready_rows),
        "failed_case_count": len(rows) - len(ready_rows),
        "calendar_types": sorted(row for row in calendar_types if row),
        "chart_statuses": sorted(row for row in chart_statuses if row),
        "ready_ratio": round(len(ready_rows) / max(1, len(rows)), 3),
        "customer_projection_leak_free_count": sum(
            1 for row in rows if row.get("checks", {}).get("customer_projection_no_internal_leak") is True
        ),
        "core_bazi_ready_count": sum(
            1 for row in rows if row.get("checks", {}).get("core_bazi_reading_ready") is True
        ),
        "m6_practical_ready_count": sum(
            1 for row in rows if row.get("checks", {}).get("m6_practical_reading_ready") is True
        ),
    }


def _decision(summary: Mapping[str, Any], rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    blockers: list[str] = []
    failed_rows = [row for row in rows if not row.get("ready_for_business_reading")]
    if summary.get("source_suite_id") != "v30.synthetic.real_case_calibration_pack":
        blockers.append("source_real_case_calibration_pack_missing")
    if not summary.get("source_suite_passed"):
        blockers.append("source_real_case_calibration_pack_not_passing")
    if int(summary.get("accepted_case_count", 0) or 0) < 10:
        blockers.append("accepted_case_count_below_business_minimum")
    if not {"solar", "lunar"}.issubset(set(summary.get("calendar_types", []))):
        blockers.append("calendar_type_business_coverage_incomplete")
    if "ready" not in set(summary.get("chart_statuses", [])):
        blockers.append("ready_chart_business_coverage_missing")
    if failed_rows:
        blockers.append("business_reading_acceptance_rows_failed")
    ready = not blockers
    return {
        "business_bazi_reading_ready": ready,
        "decision_status": "b1_real_business_bazi_reading_accepted" if ready else "b1_real_business_bazi_reading_blocked",
        "blockers": blockers,
        "failed_case_ids": [str(row.get("case_id") or "") for row in failed_rows],
        "full_pytest_required": False,
        "full_518k_required": False,
        "policy_pointer_promotion_allowed": False,
        "chart_fact_mutation_allowed": False,
        "rationale": (
            "B1 accepted: canonical real-case rows support a customer-visible Bazi calculation loop."
            if ready
            else "B1 blocked: fix the listed business reading acceptance gaps before UI or question expansion."
        ),
    }


def _next_selection(decision: Mapping[str, Any]) -> dict[str, Any]:
    if decision.get("business_bazi_reading_ready"):
        return {
            "task_id": "B2",
            "title": "Business Reading Case Expansion And Regression Pack",
            "selected_track": "business_bazi_acceptance",
            "scope": [
                "expand accepted business cases beyond the canonical synthetic pack",
                "keep validation metadata-only where private user content is involved",
                "preserve the concise UI while strengthening module-backed reading quality",
            ],
        }
    return {
        "task_id": "B1-FR",
        "title": "Real Business Bazi Reading Acceptance Failure Review",
        "selected_track": "business_bazi_acceptance",
        "scope": [
            "repair failed B1 case rows",
            "do not move to UI or question expansion until BirthInput-to-reading acceptance passes",
            "keep chart facts deterministic and training signals non-mutating",
        ],
    }
