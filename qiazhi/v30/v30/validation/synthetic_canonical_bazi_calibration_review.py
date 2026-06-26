from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping

from v30.validation.synthetic_case import (
    SYNTHETIC_CANONICAL_BAZI_CALIBRATION_CASES,
    SyntheticValidationSuiteResult,
    run_synthetic_tier,
)


SYNTHETIC_CANONICAL_BAZI_CALIBRATION_REVIEW_VERSION = "v30.synthetic_canonical_bazi_calibration_review.v1"


def run_synthetic_canonical_bazi_calibration_review() -> dict[str, Any]:
    suite = run_synthetic_tier("synthetic_canonical_bazi_calibration")
    return build_synthetic_canonical_bazi_calibration_review(synthetic_suite=suite)


def build_synthetic_canonical_bazi_calibration_review(
    *,
    synthetic_suite: SyntheticValidationSuiteResult | Mapping[str, Any],
) -> dict[str, Any]:
    payload = (
        synthetic_suite.model_dump(mode="json")
        if hasattr(synthetic_suite, "model_dump")
        else dict(synthetic_suite)
    )
    case_rows = _case_rows(payload)
    queue_items = _queue_items(case_rows)
    checks = _checks(payload, case_rows, queue_items)
    decision = _decision(checks, case_rows, queue_items)
    return {
        "version": SYNTHETIC_CANONICAL_BAZI_CALIBRATION_REVIEW_VERSION,
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "status": "completed" if decision["synthetic_canonical_calibration_ready"] else "blocked",
        "task": {
            "task_id": "SCAL-S1",
            "title": "Synthetic Canonical Bazi Case Pack And Calibration Review",
            "scope": "validate_typical_synthetic_bazi_structures_without_importing_unverifiable_real_person_truth",
        },
        "synthetic_suite_summary": _suite_summary(payload),
        "case_rows": case_rows,
        "calibration_queue_items": queue_items,
        "checks": checks,
        "decision": decision,
        "policy_boundary": {
            "uses_real_person_truth": False,
            "chart_fact_mutation_allowed": False,
            "auto_apply_training_allowed": False,
            "policy_pointer_promotion_allowed": False,
            "full_pytest_required": False,
            "synthetic_all_required": False,
            "full_518k_required": False,
            "boundary": "scal_s1_uses_synthetic_typical_structures_for_validation_not_unverifiable_biography",
        },
        "next_mainline_selection": _next_selection(decision),
        "boundary": "synthetic_canonical_cases_validate_structure_expectations_not_final_destiny_verdicts",
    }


def _case_rows(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows = payload.get("results", [])
    if not isinstance(rows, list):
        return []
    case_by_id = {case.case_id: case for case in SYNTHETIC_CANONICAL_BAZI_CALIBRATION_CASES}
    output: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        case_id = str(row.get("case_id") or "")
        case = case_by_id.get(case_id)
        observed = _mapping(row.get("observed"))
        quality = _mapping(observed.get("real_bazi_diagnosis_quality"))
        expected_domains = sorted(case.expected_rbd_domains) if case else []
        observed_domains = [str(item) for item in quality.get("domain_claims", [])] if isinstance(quality.get("domain_claims"), list) else []
        missing_domains = sorted(set(expected_domains) - set(observed_domains))
        failures = [str(item) for item in row.get("failures", [])] if isinstance(row.get("failures"), list) else []
        output.append(
            {
                "case_id": case_id,
                "case_type": str(case.case_type if case else ""),
                "chart_input": dict(case.chart_input) if case else {},
                "passed": bool(row.get("passed")),
                "failures": failures,
                "expected_domains": expected_domains,
                "observed_domains": observed_domains,
                "missing_domains": missing_domains,
                "rule_match_count": int(quality.get("rule_match_count", 0) or 0),
                "path_count": int(quality.get("path_count", 0) or 0),
                "portrait_count": int(quality.get("portrait_count", 0) or 0),
                "claim_count": int(quality.get("claim_count", 0) or 0),
                "generic_language_rate": float(quality.get("generic_language_rate", 0.0) or 0.0),
                "untraceable_claim_count": int(quality.get("untraceable_claim_count", 0) or 0),
                "llm_generated_claim_count": int(quality.get("llm_generated_claim_count", 0) or 0),
                "chart_fact_mutation_claim_count": int(quality.get("chart_fact_mutation_claim_count", 0) or 0),
                "fixed_event_prediction_claim_count": int(quality.get("fixed_event_prediction_claim_count", 0) or 0),
                "customer_internal_leak_count": int(quality.get("customer_internal_leak_count", 0) or 0),
                "notes": case.notes if case else "",
                "boundary": "canonical_case_row_checks_structure_expectations_not_real_life_truth",
            }
        )
    return output


def _queue_items(case_rows: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    for row in case_rows:
        if row.get("passed") is True:
            continue
        failed_domains = row.get("missing_domains", [])
        if not isinstance(failed_domains, list) or not failed_domains:
            failed_domains = ["general"]
        for domain in failed_domains:
            domain_key = str(domain or "general")
            item = grouped.setdefault(
                domain_key,
                {
                    "queue_item_id": f"scal.calibration.synthetic_canonical.{domain_key}",
                    "target_module": "RBD",
                    "target_domain": domain_key,
                    "issue_type": "synthetic_canonical_structure_expectation_gap",
                    "source": "synthetic_canonical_bazi_calibration",
                    "evidence_case_ids": [],
                    "observed_failure_count": 0,
                    "recommended_action": "review_rules_paths_portraits_or_question_strategy_for_canonical_structure",
                    "status": "queued_for_review",
                    "runtime_mutation_allowed": False,
                    "chart_fact_mutation_allowed": False,
                    "policy_pointer_promotion_allowed": False,
                    "boundary": "scal_queue_item_is_synthetic_evidence_candidate_not_auto_apply",
                },
            )
            item["observed_failure_count"] += 1
            case_id = str(row.get("case_id") or "")
            if case_id and case_id not in item["evidence_case_ids"]:
                item["evidence_case_ids"].append(case_id)
    return sorted(grouped.values(), key=lambda item: str(item["queue_item_id"]))


def _checks(
    payload: Mapping[str, Any],
    case_rows: list[Mapping[str, Any]],
    queue_items: list[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    passed_case_count = sum(1 for row in case_rows if row.get("passed") is True)
    no_forbidden_writes = all(
        int(row.get("chart_fact_mutation_claim_count", 0) or 0) == 0
        and int(row.get("fixed_event_prediction_claim_count", 0) or 0) == 0
        and int(row.get("llm_generated_claim_count", 0) or 0) == 0
        for row in case_rows
    )
    queue_readonly = all(
        item.get("runtime_mutation_allowed") is False
        and item.get("chart_fact_mutation_allowed") is False
        and item.get("policy_pointer_promotion_allowed") is False
        for item in queue_items
    )
    return [
        {
            "check_id": "canonical_synthetic_tier_registered_and_complete",
            "passed": payload.get("suite_id") == "v30.synthetic.synthetic_canonical_bazi_calibration"
            and int(payload.get("case_count", 0) or 0) == len(SYNTHETIC_CANONICAL_BAZI_CALIBRATION_CASES)
            and len(case_rows) == len(SYNTHETIC_CANONICAL_BAZI_CALIBRATION_CASES),
            "observed": {"suite_id": payload.get("suite_id"), "case_count": payload.get("case_count")},
        },
        {
            "check_id": "canonical_cases_pass_current_rbd_expectations",
            "passed": bool(payload.get("passed")) and passed_case_count == len(case_rows),
            "observed": {"passed_case_count": passed_case_count, "case_count": len(case_rows)},
        },
        {
            "check_id": "canonical_cases_are_traceable_and_not_generic",
            "passed": all(
                int(row.get("untraceable_claim_count", 0) or 0) == 0
                and float(row.get("generic_language_rate", 0.0) or 0.0) <= 0.2
                and int(row.get("customer_internal_leak_count", 0) or 0) == 0
                for row in case_rows
            ),
            "observed": {
                "max_generic_language_rate": max((float(row.get("generic_language_rate", 0.0) or 0.0) for row in case_rows), default=0.0),
                "total_untraceable_claim_count": sum(int(row.get("untraceable_claim_count", 0) or 0) for row in case_rows),
            },
        },
        {
            "check_id": "canonical_cases_do_not_mutate_or_predict_fixed_events",
            "passed": no_forbidden_writes,
            "observed": {"no_forbidden_writes": no_forbidden_writes},
        },
        {
            "check_id": "calibration_queue_is_readonly",
            "passed": queue_readonly,
            "observed": {"queued_item_count": len(queue_items), "queue_readonly": queue_readonly},
        },
        {
            "check_id": "heavy_gates_remain_explicit",
            "passed": True,
            "observed": {"full_pytest_required": False, "synthetic_all_required": False, "full_518k_required": False},
        },
    ]


def _decision(
    checks: list[Mapping[str, Any]],
    case_rows: list[Mapping[str, Any]],
    queue_items: list[Mapping[str, Any]],
) -> dict[str, Any]:
    failed = [str(row.get("check_id") or "") for row in checks if row.get("passed") is not True]
    ready = not failed
    return {
        "synthetic_canonical_calibration_ready": ready,
        "decision_status": "scal_s1_synthetic_canonical_calibration_ready" if ready else "scal_s1_synthetic_canonical_calibration_blocked",
        "check_count": len(checks),
        "passed_check_count": len(checks) - len(failed),
        "failed_check_ids": failed,
        "case_count": len(case_rows),
        "passed_case_count": sum(1 for row in case_rows if row.get("passed") is True),
        "queued_item_count": len(queue_items),
        "chart_fact_mutation_allowed": False,
        "auto_apply_training_allowed": False,
        "policy_pointer_promotion_allowed": False,
        "full_pytest_required": False,
        "synthetic_all_required": False,
        "full_518k_required": False,
        "blockers": ["synthetic_canonical_calibration_checks_failed"] if failed else [],
    }


def _suite_summary(payload: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "suite_id": str(payload.get("suite_id") or ""),
        "passed": bool(payload.get("passed")),
        "case_count": int(payload.get("case_count", 0) or 0),
        "passed_count": int(payload.get("passed_count", 0) or 0),
        "failed_count": int(payload.get("failed_count", 0) or 0),
    }


def _next_selection(decision: Mapping[str, Any]) -> dict[str, Any]:
    if decision.get("synthetic_canonical_calibration_ready"):
        return {
            "task_id": "SCAL-S2",
            "title": "Synthetic Canonical Pack Expansion Or Cadence Decision",
            "selected_track": "synthetic_canonical_calibration",
            "scope": [
                "review whether to expand canonical synthetic structures",
                "keep failed items read-only until evidence review",
                "do not introduce unverifiable real-person truth",
            ],
        }
    return {
        "task_id": "SCAL-S1-FR",
        "title": "Synthetic Canonical Calibration Failure Review",
        "selected_track": "synthetic_canonical_calibration",
        "scope": [
            "inspect failed canonical case expectations",
            "queue bounded RBD/M3/M5/IQ review candidates",
            "keep chart facts and policy pointers immutable",
        ],
    }


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}
