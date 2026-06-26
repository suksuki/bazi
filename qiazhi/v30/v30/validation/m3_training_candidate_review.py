from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from v30.validation.m3_core_spine_snapshot import run_m3_core_spine_snapshot
from v30.validation.synthetic_case import run_synthetic_tier


M3_TRAINING_CANDIDATE_REVIEW_VERSION = "v30.m3_training_candidate_review.v1"

FORBIDDEN_TRAINING_SCOPE = {
    "chart_facts",
    "four_pillars",
    "luck_cycle_facts",
    "flow_year_facts",
    "flow_month_facts",
    "fixed_structure_verdict",
    "fixed_useful_god_verdict",
    "deterministic_chart_facts",
}


def run_m3_training_candidate_review(
    *,
    sample_limit: int = 8,
    artifact_dir: str | Path | None = None,
) -> dict[str, Any]:
    snapshot = run_m3_core_spine_snapshot(
        include_518k_sample=True,
        sample_limit=sample_limit,
        write_db=False,
    )
    training_pipeline = run_synthetic_tier("training_pipeline")
    return build_m3_training_candidate_review(
        m3_snapshot=snapshot,
        training_pipeline=training_pipeline.model_dump(mode="json"),
        artifact_dir=artifact_dir,
    )


def build_m3_training_candidate_review(
    *,
    m3_snapshot: Mapping[str, Any],
    training_pipeline: Mapping[str, Any],
    artifact_dir: str | Path | None = None,
) -> dict[str, Any]:
    reviewed_at = datetime.now(timezone.utc)
    review_id = f"v30.m3.g3.{reviewed_at.strftime('%Y%m%d%H%M%S%f')}"
    calibration = _mapping(m3_snapshot.get("source_governed_calibration"))
    tag_groups = _mapping(calibration.get("tag_groups"))
    candidates = _candidate_rows(
        review_id=review_id,
        tag_groups=tag_groups,
        training_pipeline=training_pipeline,
        validation_518k=_mapping(m3_snapshot.get("validation_518k")),
    )
    checks = _checks(
        candidates=candidates,
        calibration=calibration,
        training_pipeline=training_pipeline,
        validation_518k=_mapping(m3_snapshot.get("validation_518k")),
    )
    decision = _decision(candidates=candidates, checks=checks)
    payload: dict[str, Any] = {
        "version": M3_TRAINING_CANDIDATE_REVIEW_VERSION,
        "review_id": review_id,
        "reviewed_at": reviewed_at.isoformat(),
        "status": "completed" if decision["ready_for_training_review"] else "blocked",
        "decision": decision,
        "candidate_summary": {
            "candidate_count": len(candidates),
            "candidate_types": sorted({str(row.get("candidate_type")) for row in candidates}),
            "target_domains": sorted({
                domain
                for row in candidates
                for domain in _string_list(row.get("target_domains"))
            }),
            "forbidden_scope_hits": _forbidden_scope_hits(candidates),
        },
        "source_summary": {
            "m3_snapshot_id": str(m3_snapshot.get("snapshot_id") or ""),
            "m3_calibration_version": str(calibration.get("version") or ""),
            "training_pipeline_suite_id": str(training_pipeline.get("suite_id") or ""),
            "training_pipeline_passed": bool(training_pipeline.get("passed")),
            "validation_518k": _validation_518k_summary(_mapping(m3_snapshot.get("validation_518k"))),
        },
        "candidates": candidates,
        "checks": checks,
        "policy_boundary": {
            "review_only": True,
            "auto_apply_training_allowed": False,
            "policy_pointer_promotion_allowed": False,
            "chart_fact_mutation_allowed": False,
            "fixed_bazi_verdict_allowed": False,
            "full_pytest_required": False,
            "full_518k_required": False,
            "boundary": "m3_g3_training_candidates_are_review_evidence_not_policy_or_chart_fact_mutation",
        },
        "next_mainline_selection": _next_selection(decision),
        "boundary": "m3_g3_converts_m3_tags_and_distribution_observations_into_bounded_training_candidate_review_evidence",
    }
    if artifact_dir is not None:
        payload["artifact_uri"] = str(_write_artifact(payload, Path(artifact_dir)))
    return payload


def _candidate_rows(
    *,
    review_id: str,
    tag_groups: Mapping[str, Any],
    training_pipeline: Mapping[str, Any],
    validation_518k: Mapping[str, Any],
) -> list[dict[str, Any]]:
    domain_depth = _list_of_mappings(tag_groups.get("domain_rule_depth_expansion"))
    source_queue = _list_of_mappings(tag_groups.get("source_extraction_queue"))
    real_case_tags = _list_of_mappings(tag_groups.get("real_case_calibration_tags"))
    training_distribution = _list_of_mappings(tag_groups.get("training_synthetic_distribution"))
    distribution_518k = _mapping(tag_groups.get("distribution_518k_summary"))

    source_tag_ids = [str(row.get("tag_id")) for row in source_queue if row.get("tag_id")]
    calibrated_domains = [
        str(row.get("domain"))
        for row in domain_depth
        if row.get("depth_state") == "calibrated_depth" and row.get("domain")
    ]
    growth_domains = [
        str(row.get("domain"))
        for row in domain_depth
        if row.get("depth_state") == "growth_candidate" and row.get("domain")
    ]
    dynamic_case_tags = [
        str(row.get("tag_id"))
        for row in real_case_tags
        if int(row.get("dynamic_path_count", 0) or 0) > 0 and row.get("tag_id")
    ]
    training_tag_ids = [str(row.get("tag_id")) for row in training_distribution if row.get("tag_id")]
    rows = [
        _candidate(
            review_id,
            "source_coverage_weight_candidate",
            "source_coverage",
            calibrated_domains[:8],
            source_tag_ids,
            "Review source-family coverage weights after G1/G2 source queue tags.",
            ["source_coverage_weights", "portrait_density_review"],
            "operator_review_after_source_extraction",
        ),
        _candidate(
            review_id,
            "rule_path_priority_candidate",
            "rule_path_priority",
            calibrated_domains[:8],
            [str(row.get("tag_id")) for row in domain_depth if row.get("tag_id")],
            "Review rule path priority across calibrated M3 domain-rule depth tags.",
            ["rule_path_priority", "domain_rule_depth_priority"],
            "operator_review_before_policy_candidate",
        ),
        _candidate(
            review_id,
            "domain_rule_depth_candidate",
            "domain_rule_depth",
            growth_domains or calibrated_domains[:8],
            [str(row.get("tag_id")) for row in domain_depth if row.get("tag_id")],
            "Track whether G2 domain depth remains steady or needs future source expansion.",
            ["domain_rule_depth_review", "source_family_coverage"],
            "steady_state_monitoring" if not growth_domains else "expand_growth_domains",
        ),
        _candidate(
            review_id,
            "counterevidence_trace_candidate",
            "rule_counterevidence",
            ["rule_counterevidence", "structure_pattern", "useful_god"],
            [str(row.get("tag_id")) for row in domain_depth if str(row.get("domain")) in {"rule_counterevidence", "structure_pattern", "useful_god"}],
            "Review counter-evidence trace density before tuning rule weights.",
            ["rule_counterevidence_trace", "rule_path_priority"],
            "operator_review_required",
        ),
        _candidate(
            review_id,
            "dynamic_path_priority_candidate",
            "dynamic_structure_path",
            ["structure_dynamic", "structure_pattern", "useful_god"],
            dynamic_case_tags,
            "Review dynamic path distribution from real-case synthetic tags before changing path weights.",
            ["dynamic_structure_path_review", "path_priority_review"],
            "operator_review_required",
        ),
        _candidate(
            review_id,
            "question_strategy_candidate",
            "question_strategy",
            ["question_strategy", "hidden_factor", "time_context"],
            training_tag_ids + ([str(distribution_518k.get("tag_id"))] if distribution_518k.get("tag_id") else []),
            "Use training-pipeline and 518K sample observations only for question strategy review.",
            ["question_strategy", "interaction_followup_policy"],
            "operator_review_after_question_replay",
        ),
        _candidate(
            review_id,
            "training_distribution_candidate",
            "training_synthetic_distribution",
            ["training_pipeline", "m3_core_spine"],
            training_tag_ids,
            (
                f"Training pipeline passed {int(training_pipeline.get('passed_count', 0) or 0)}/"
                f"{int(training_pipeline.get('case_count', 0) or 0)} and remains candidate-only."
            ),
            ["synthetic_distribution_review", "coverage_monitoring"],
            "ready_for_review" if bool(training_pipeline.get("passed")) else "blocked_until_training_pipeline_passes",
        ),
        _candidate(
            review_id,
            "distribution_518k_candidate",
            "distribution_518k",
            ["distribution_validation", "m3_coverage"],
            [str(distribution_518k.get("tag_id"))] if distribution_518k.get("tag_id") else [],
            (
                f"518K sample included={bool(validation_518k.get('included'))} "
                f"cases={int(validation_518k.get('case_count', 0) or 0)} for distribution review only."
            ),
            ["distribution_monitoring", "coverage_monitoring"],
            "ready_for_review" if bool(validation_518k.get("included")) else "blocked_until_518k_sample_present",
        ),
    ]
    return rows


def _candidate(
    review_id: str,
    candidate_type: str,
    target_domain: str,
    target_domains: list[str],
    source_tag_ids: list[str],
    evidence_summary: str,
    allowed_training_scope: list[str],
    recommended_review_action: str,
) -> dict[str, Any]:
    clean_source_ids = sorted({row for row in source_tag_ids if row})
    clean_domains = sorted({row for row in target_domains if row})
    return {
        "candidate_id": f"{review_id}.{candidate_type}",
        "candidate_type": candidate_type,
        "target_domain": target_domain,
        "target_domains": clean_domains,
        "source_tag_ids": clean_source_ids,
        "source_tag_count": len(clean_source_ids),
        "evidence_summary": evidence_summary,
        "recommended_review_action": recommended_review_action,
        "allowed_training_scope": allowed_training_scope,
        "forbidden_training_scope": sorted(FORBIDDEN_TRAINING_SCOPE),
        "requires_operator_review": True,
        "auto_apply_allowed": False,
        "policy_pointer_promotion_allowed": False,
        "chart_fact_mutation_allowed": False,
        "fixed_bazi_verdict_allowed": False,
        "status": "review_candidate",
        "boundary": "m3_training_candidate_is_review_only_and_cannot_mutate_chart_facts_or_promote_pointers",
    }


def _checks(
    *,
    candidates: list[dict[str, Any]],
    calibration: Mapping[str, Any],
    training_pipeline: Mapping[str, Any],
    validation_518k: Mapping[str, Any],
) -> list[dict[str, Any]]:
    required_types = {
        "source_coverage_weight_candidate",
        "rule_path_priority_candidate",
        "domain_rule_depth_candidate",
        "counterevidence_trace_candidate",
        "dynamic_path_priority_candidate",
        "question_strategy_candidate",
    }
    candidate_types = {str(row.get("candidate_type")) for row in candidates}
    return [
        {
            "check_id": "m3_source_governed_calibration_ready",
            "passed": calibration.get("version") == "v30.m3_source_governed_calibration.v1" and calibration.get("status") == "ready",
            "expected": "M3 G1/G2 calibration tags are present and ready",
        },
        {
            "check_id": "required_candidate_types_present",
            "passed": required_types.issubset(candidate_types),
            "expected": "source, rule, depth, counter-evidence, dynamic path, and question strategy candidates exist",
        },
        {
            "check_id": "candidate_count_sufficient",
            "passed": len(candidates) >= 8,
            "expected": "at least eight M3 training review candidates are produced",
        },
        {
            "check_id": "training_pipeline_passed",
            "passed": bool(training_pipeline.get("passed")) and int(training_pipeline.get("passed_count", 0) or 0) >= 91,
            "expected": "training_pipeline synthetic tier passes at current baseline",
        },
        {
            "check_id": "sample_518k_distribution_present",
            "passed": bool(validation_518k.get("included")) and int(validation_518k.get("case_count", 0) or 0) >= 8,
            "expected": "518K sample distribution is included for G3 review",
        },
        {
            "check_id": "no_forbidden_training_scope_allowed",
            "passed": not _forbidden_scope_hits(candidates),
            "expected": "allowed training scopes do not include deterministic chart facts or fixed verdicts",
        },
        {
            "check_id": "review_only_boundaries_enforced",
            "passed": all(
                not bool(row.get("auto_apply_allowed"))
                and not bool(row.get("policy_pointer_promotion_allowed"))
                and not bool(row.get("chart_fact_mutation_allowed"))
                and not bool(row.get("fixed_bazi_verdict_allowed"))
                and bool(row.get("requires_operator_review"))
                for row in candidates
            ),
            "expected": "all candidates are review-only and require operator review",
        },
    ]


def _decision(*, candidates: list[dict[str, Any]], checks: list[dict[str, Any]]) -> dict[str, Any]:
    passed = sum(1 for row in checks if row["passed"])
    ready = passed == len(checks)
    return {
        "decision_status": "m3_g3_training_candidate_review_ready" if ready else "m3_g3_training_candidate_review_blocked",
        "ready_for_training_review": ready,
        "ready_for_pointer_promotion": False,
        "policy_pointer_promotion_allowed": False,
        "chart_fact_mutation_allowed": False,
        "fixed_bazi_verdict_allowed": False,
        "candidate_count": len(candidates),
        "passed_checks": passed,
        "total_checks": len(checks),
    }


def _validation_518k_summary(validation_518k: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "included": bool(validation_518k.get("included")),
        "run_id": str(validation_518k.get("run_id") or ""),
        "mode": str(validation_518k.get("mode") or ""),
        "case_count": int(validation_518k.get("case_count", 0) or 0),
        "promotion_signal": str(validation_518k.get("promotion_signal") or ""),
        "artifact_record_id": str(validation_518k.get("artifact_record_id") or ""),
        "artifact_search_backend": str(validation_518k.get("artifact_search_backend") or ""),
    }


def _next_selection(decision: Mapping[str, Any]) -> dict[str, Any]:
    if decision.get("ready_for_training_review"):
        return {
            "next_task": "M3-G4 Source Extraction Queue Operationalization",
            "reason": "G3 candidate evidence is ready; next make source extraction queue operational while preserving review-only boundaries.",
            "full_pytest_required": False,
            "full_518k_required": False,
        }
    return {
        "next_task": "M3-G3 Remediation",
        "reason": "G3 checks are blocked; fix training candidate evidence before continuing M3.",
        "full_pytest_required": False,
        "full_518k_required": False,
    }


def _forbidden_scope_hits(candidates: list[dict[str, Any]]) -> dict[str, list[str]]:
    hits: dict[str, list[str]] = {}
    for row in candidates:
        allowed = set(_string_list(row.get("allowed_training_scope")))
        overlap = sorted(allowed & FORBIDDEN_TRAINING_SCOPE)
        if overlap:
            hits[str(row.get("candidate_id") or row.get("candidate_type"))] = overlap
    return hits


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


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
    path = artifact_dir / f"{payload['review_id']}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
