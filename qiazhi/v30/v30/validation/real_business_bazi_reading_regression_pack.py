from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

from v30.validation.real_business_bazi_reading_acceptance import (
    FORBIDDEN_CUSTOMER_TOKENS,
    _business_reading_rows,
    _result_rows,
)
from v30.validation.synthetic_case import SyntheticValidationSuiteResult, run_synthetic_tier


REAL_BUSINESS_BAZI_READING_REGRESSION_PACK_VERSION = "v30.real_business_bazi_reading_regression_pack.v1"
REQUIRED_DOMAIN_KEYS = {"career", "wealth", "relationship", "health", "timing"}


def run_real_business_bazi_reading_regression_pack(*, case_limit: int = 24) -> dict[str, Any]:
    synthetic = run_synthetic_tier("real_case_calibration_pack")
    return build_real_business_bazi_reading_regression_pack(
        synthetic_result=synthetic,
        case_limit=case_limit,
    )


def build_real_business_bazi_reading_regression_pack(
    *,
    synthetic_result: SyntheticValidationSuiteResult | Mapping[str, Any],
    case_limit: int = 24,
) -> dict[str, Any]:
    payload = (
        synthetic_result.model_dump(mode="json")
        if hasattr(synthetic_result, "model_dump")
        else dict(synthetic_result)
    )
    case_limit = max(1, min(int(case_limit or 24), 30))
    rows = _business_reading_rows(_result_rows(payload), case_limit)
    regression_rows = [_regression_row(row) for row in rows]
    coverage = _coverage(regression_rows)
    decision = _decision(payload, regression_rows, coverage)
    return {
        "version": REAL_BUSINESS_BAZI_READING_REGRESSION_PACK_VERSION,
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "status": "completed" if decision["business_reading_regression_ready"] else "blocked",
        "decision": decision,
        "regression_summary": {
            "source_suite_id": str(payload.get("suite_id") or ""),
            "source_suite_passed": bool(payload.get("passed")),
            "source_case_count": int(payload.get("case_count", 0) or 0),
            "regression_case_count": len(regression_rows),
            "passed_case_count": sum(1 for row in regression_rows if row["regression_ready"]),
            "failed_case_count": sum(1 for row in regression_rows if not row["regression_ready"]),
            "coverage": coverage,
        },
        "regression_rows": regression_rows,
        "business_scope": {
            "task_id": "B2",
            "title": "Business Reading Case Expansion And Regression Pack",
            "acceptance_target": "expanded ready-case customer Bazi reading regression",
            "required_surface_checks": [
                "base_fact_explanation",
                "ranked_decision_projection",
                "practical_domain_cards",
                "practical_domain_contracts",
                "customer_summary",
                "privacy_and_no_mutation",
            ],
            "boundary": "b2_regression_pack_tests_business_reading_quality_not_ui_polish",
        },
        "policy_boundary": {
            "full_pytest_run_by_default": False,
            "full_518k_run_by_default": False,
            "policy_pointer_promotion_allowed": False,
            "chart_fact_mutation_allowed": False,
            "training_signal_may_change_chart_facts": False,
            "boundary": "b2_is_read_only_regression_and_does_not_mutate_chart_facts",
        },
        "next_mainline_selection": _next_selection(decision),
        "boundary": "b2_expands_business_reading_regression_without_reopening_core_modules",
    }


def _regression_row(row: Mapping[str, Any]) -> dict[str, Any]:
    observed = row.get("observed", {})
    observed = observed if isinstance(observed, Mapping) else {}
    fixture = _mapping(observed.get("real_case_fixture", {}))
    metadata = _mapping(observed.get("production_replay_metadata", {}))
    surface = _mapping(observed.get("customer_reading_surface", {}))
    core = _mapping(observed.get("core_bazi_reading", {}))
    practical = _mapping(observed.get("practical_reading_context", {}))
    projection = _mapping(observed.get("api_projection_contract", {}))

    domain_cards = surface.get("domain_cards", [])
    domain_cards = domain_cards if isinstance(domain_cards, list) else []
    practical_domains = practical.get("domain_readings", {})
    practical_domains = practical_domains if isinstance(practical_domains, Mapping) else {}
    core_practical_domains = core.get("practical_domains", [])
    core_practical_domains = core_practical_domains if isinstance(core_practical_domains, list) else []
    base_summary = _mapping(core.get("base_fact_summary", {}))
    explanations = _mapping(core.get("base_fact_explanations", {}))
    m1_m2_completion = _mapping(core.get("m1_m2_completion_summary", {}))
    ranked_projection = _mapping(core.get("ranked_decisions", {}))
    reading_summary = _mapping(surface.get("reading_summary", {}))
    privacy_guard = _mapping(metadata.get("privacy_guard", {}))

    checks = {
        "synthetic_case_passed": bool(row.get("passed")),
        "ready_chart": str(metadata.get("chart_status") or fixture.get("status") or "") == "ready",
        "base_fact_summary_complete": (
            base_summary.get("status") == "ready"
            and int(base_summary.get("pillar_count", 0) or 0) == 4
            and isinstance(base_summary.get("element_distribution"), Mapping)
        ),
        "base_fact_explanations_ready": (
            explanations.get("version") == "v30.base_bazi_fact_explanations.v1"
            and explanations.get("boundary") == "base_fact_explanations_are_deterministic_context_not_ranked_decisions"
        ),
        "m1_m2_completion_ready": (
            m1_m2_completion.get("version") == "v30.m1_m2_completion_summary.v1"
            and m1_m2_completion.get("status") == "ready"
        ),
        "ranked_decision_projection_ready": (
            {"strength", "structure_pattern", "useful_god"}.issubset(set(ranked_projection))
            and all(
                str(_mapping(ranked_projection.get(key, {})).get("primary_candidate") or "").strip()
                for key in ("strength", "structure_pattern", "useful_god")
            )
        ),
        "customer_summary_ready": bool(str(reading_summary.get("primary_message") or "").strip()),
        "domain_cards_complete": _domain_cards_complete(domain_cards),
        "core_practical_domains_complete": len(core_practical_domains) >= 5 and all(
            str(card.get("summary") or "").strip() and str(card.get("customer_takeaway") or "").strip()
            for card in core_practical_domains
            if isinstance(card, Mapping)
        ),
        "practical_domain_contracts_ready": _practical_domains_ready(practical_domains),
        "projection_contract_ready": (
            projection.get("version") == "v30.api_projection_contract.v1"
            and projection.get("leak_scan", {}).get("passed") is True
        ),
        "metadata_privacy_no_mutation": (
            privacy_guard.get("metadata_only") is True
            and privacy_guard.get("no_private_user_content") is True
            and privacy_guard.get("no_chart_fact_mutation") is True
        ),
        "customer_projection_no_internal_leak": not any(
            token in str({"surface": surface, "core": core}) for token in FORBIDDEN_CUSTOMER_TOKENS
        ),
    }
    failed = [check_id for check_id, passed in checks.items() if not passed]
    return {
        "case_id": str(row.get("case_id") or ""),
        "calendar_type": str(fixture.get("calendar_type") or metadata.get("calendar_type") or ""),
        "chart_status": str(metadata.get("chart_status") or fixture.get("status") or ""),
        "lunar_is_leap_month": bool(fixture.get("lunar_is_leap_month") or metadata.get("lunar_is_leap_month")),
        "use_true_solar_time": bool(fixture.get("use_true_solar_time") or metadata.get("use_true_solar_time")),
        "unknown_gender": bool(metadata.get("unknown_gender")) or str(fixture.get("gender_status") or "") == "unknown",
        "domain_card_count": len(domain_cards),
        "practical_domain_count": len(practical_domains),
        "regression_ready": not failed,
        "checks": checks,
        "failed_check_ids": failed,
        "boundary": "b2_case_regression_checks_customer_reading_quality_not_final_claim_truth",
    }


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _domain_cards_complete(cards: Sequence[object]) -> bool:
    rows = [card for card in cards if isinstance(card, Mapping)]
    domains = {str(card.get("domain") or "") for card in rows}
    if not REQUIRED_DOMAIN_KEYS.issubset(domains) or len(rows) < 5:
        return False
    return all(
        str(card.get("summary") or "").strip()
        and str(card.get("customer_takeaway") or "").strip()
        and str(card.get("action_prompt") or "").strip()
        for card in rows
    )


def _practical_domains_ready(domains: Mapping[str, Any]) -> bool:
    if not REQUIRED_DOMAIN_KEYS.issubset(set(domains)):
        return False
    for payload in domains.values():
        payload = _mapping(payload)
        quality = _mapping(payload.get("quality_contract", {}))
        basis = _mapping(payload.get("calculation_basis", {}))
        trace = _mapping(payload.get("module_trace", {}))
        if quality.get("version") != "v30.practical_reading_quality.v1":
            return False
        if basis.get("version") != "v30.practical_domain_calculation_basis.v1":
            return False
        if trace.get("version") != "v30.m6_practical_module_trace.v1":
            return False
        if trace.get("uses_m1_m2_facts") is not True or trace.get("uses_m5_ranked_decisions") is not True:
            return False
        if not str(payload.get("customer_takeaway") or "").strip():
            return False
        if not str(payload.get("action_prompt") or "").strip():
            return False
    return True


def _coverage(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    return {
        "calendar_types": sorted({str(row.get("calendar_type") or "") for row in rows if row.get("calendar_type")}),
        "ready_case_count": sum(1 for row in rows if row.get("chart_status") == "ready"),
        "solar_case_count": sum(1 for row in rows if row.get("calendar_type") == "solar"),
        "lunar_case_count": sum(1 for row in rows if row.get("calendar_type") == "lunar"),
        "leap_lunar_case_count": sum(1 for row in rows if row.get("lunar_is_leap_month")),
        "true_solar_case_count": sum(1 for row in rows if row.get("use_true_solar_time")),
        "unknown_gender_case_count": sum(1 for row in rows if row.get("unknown_gender")),
        "domain_card_min_count": min((int(row.get("domain_card_count", 0) or 0) for row in rows), default=0),
        "practical_domain_min_count": min((int(row.get("practical_domain_count", 0) or 0) for row in rows), default=0),
    }


def _decision(
    payload: Mapping[str, Any],
    rows: Sequence[Mapping[str, Any]],
    coverage: Mapping[str, Any],
) -> dict[str, Any]:
    failed_rows = [row for row in rows if not row.get("regression_ready")]
    blockers: list[str] = []
    if payload.get("suite_id") != "v30.synthetic.real_case_calibration_pack":
        blockers.append("source_real_case_calibration_pack_missing")
    if not payload.get("passed"):
        blockers.append("source_real_case_calibration_pack_not_passing")
    if len(rows) < 20:
        blockers.append("regression_case_count_below_b2_minimum")
    if failed_rows:
        blockers.append("business_reading_regression_rows_failed")
    if not {"solar", "lunar"}.issubset(set(coverage.get("calendar_types", []))):
        blockers.append("calendar_coverage_missing")
    if int(coverage.get("leap_lunar_case_count", 0) or 0) <= 0:
        blockers.append("leap_lunar_coverage_missing")
    if int(coverage.get("true_solar_case_count", 0) or 0) <= 0:
        blockers.append("true_solar_coverage_missing")
    if int(coverage.get("unknown_gender_case_count", 0) or 0) <= 0:
        blockers.append("unknown_gender_coverage_missing")
    if int(coverage.get("domain_card_min_count", 0) or 0) < 5:
        blockers.append("domain_card_minimum_not_met")
    if int(coverage.get("practical_domain_min_count", 0) or 0) < 5:
        blockers.append("practical_domain_minimum_not_met")
    ready = not blockers
    return {
        "business_reading_regression_ready": ready,
        "decision_status": "b2_business_reading_regression_pack_ready" if ready else "b2_business_reading_regression_pack_blocked",
        "blockers": blockers,
        "failed_case_ids": [str(row.get("case_id") or "") for row in failed_rows],
        "full_pytest_required": False,
        "full_518k_required": False,
        "policy_pointer_promotion_allowed": False,
        "chart_fact_mutation_allowed": False,
        "rationale": (
            "B2 ready: expanded business reading rows meet regression quality and coverage checks."
            if ready
            else "B2 blocked: repair the listed reading regression or coverage gaps before the next business task."
        ),
    }


def _next_selection(decision: Mapping[str, Any]) -> dict[str, Any]:
    if decision.get("business_reading_regression_ready"):
        return {
            "task_id": "B3",
            "title": "Business Reading Answer Refresh Regression",
            "selected_track": "business_bazi_acceptance",
            "scope": [
                "verify answer refresh preserves the accepted reading surface",
                "validate structured follow-up answers do not mutate chart facts",
                "keep UI minimal and use API-level regression first",
            ],
        }
    return {
        "task_id": "B2-FR",
        "title": "Business Reading Regression Failure Review",
        "selected_track": "business_bazi_acceptance",
        "scope": [
            "repair failed B2 regression rows",
            "preserve M1-M8 frozen scope",
            "do not run full pytest unless release/full-freeze is explicitly requested",
        ],
    }
