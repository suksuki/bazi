from __future__ import annotations

import json
from collections import Counter
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from v30.runtime import create_smoke_runtime
from v30.validation.m3_source_backlog_closeout import run_m3_source_backlog_closeout
from v30.validation.synthetic_case import run_synthetic_tier


M5_EVIDENCE_CONSUMPTION_HARDENING_VERSION = "v30.m5_evidence_consumption_hardening.v1"

M5_DECISION_DOMAINS = ("strength", "structure_pattern", "useful_god")


def run_m5_evidence_consumption_hardening(
    *,
    sample_limit: int = 8,
    artifact_dir: str | Path | None = None,
) -> dict[str, Any]:
    m3_closeout = run_m3_source_backlog_closeout(
        sample_limit=sample_limit,
        artifact_dir=artifact_dir,
    )
    runtime = create_smoke_runtime("m5-evidence-consumption-hardening")
    policy_effect = runtime.question_plan.policy_effect
    m5_contract = run_synthetic_tier("m5_ranked_decision_contract").model_dump(mode="json")
    strength_tier = run_synthetic_tier("strength_structure_useful_god").model_dump(mode="json")
    return build_m5_evidence_consumption_hardening(
        m3_closeout=m3_closeout,
        ranked_decisions=_mapping(policy_effect.get("ranked_decisions")),
        m3_completion_summary=_mapping(policy_effect.get("m3_completion_summary")),
        krp_library_summary=_mapping(policy_effect.get("krp_library_summary")),
        structure_path_scores=runtime.structure_state.path_scores,
        feature_evidence=[
            row.model_dump(mode="json")
            for row in runtime.feature_evidence
        ],
        m5_contract_synthetic=m5_contract,
        strength_structure_synthetic=strength_tier,
        artifact_dir=artifact_dir,
    )


def build_m5_evidence_consumption_hardening(
    *,
    m3_closeout: Mapping[str, Any],
    ranked_decisions: Mapping[str, Any],
    m3_completion_summary: Mapping[str, Any],
    krp_library_summary: Mapping[str, Any],
    structure_path_scores: Mapping[str, Any],
    feature_evidence: list[Mapping[str, Any]],
    m5_contract_synthetic: Mapping[str, Any],
    strength_structure_synthetic: Mapping[str, Any],
    artifact_dir: str | Path | None = None,
) -> dict[str, Any]:
    reviewed_at = datetime.now(timezone.utc)
    review_id = f"v30.m5.h1.{reviewed_at.strftime('%Y%m%d%H%M%S%f')}"
    ranked_summary = _ranked_summary(ranked_decisions)
    evidence_summary = _evidence_summary(
        m3_completion_summary=m3_completion_summary,
        krp_library_summary=krp_library_summary,
        structure_path_scores=structure_path_scores,
        feature_evidence=feature_evidence,
    )
    synthetic_summary = _synthetic_summary(m5_contract_synthetic, strength_structure_synthetic)
    closeout_summary = _m3_closeout_summary(m3_closeout)
    checks = _checks(
        closeout_summary=closeout_summary,
        ranked_summary=ranked_summary,
        evidence_summary=evidence_summary,
        synthetic_summary=synthetic_summary,
    )
    decision = _decision(checks=checks, ranked_summary=ranked_summary)
    payload: dict[str, Any] = {
        "version": M5_EVIDENCE_CONSUMPTION_HARDENING_VERSION,
        "review_id": review_id,
        "reviewed_at": reviewed_at.isoformat(),
        "status": "completed" if decision["m5_evidence_consumption_ready"] else "blocked",
        "decision": decision,
        "m3_closeout_summary": closeout_summary,
        "ranked_decision_summary": ranked_summary,
        "m3_evidence_summary": evidence_summary,
        "synthetic_summary": synthetic_summary,
        "hardening_checks": checks,
        "policy_boundary": {
            "review_only": True,
            "ranked_candidates_only": True,
            "runtime_decision_write_allowed": False,
            "auto_apply_training_allowed": False,
            "policy_pointer_promotion_allowed": False,
            "chart_fact_mutation_allowed": False,
            "fixed_strength_verdict_allowed": False,
            "fixed_structure_verdict_allowed": False,
            "fixed_useful_god_verdict_allowed": False,
            "raw_model_score_visible": False,
            "full_pytest_required": False,
            "full_518k_required": False,
            "boundary": "m5_h1_reviews_evidence_consumption_without_mutating_ranked_decisions_or_chart_facts",
        },
        "next_mainline_selection": _next_selection(decision),
        "boundary": "m5_evidence_consumption_hardening_consumes_sealed_m3_evidence_as_candidate_scoring_review",
    }
    if artifact_dir is not None:
        payload["artifact_uri"] = str(_write_artifact(payload, Path(artifact_dir)))
    return payload


def _m3_closeout_summary(payload: Mapping[str, Any]) -> dict[str, Any]:
    decision = _mapping(payload.get("decision"))
    return {
        "version": str(payload.get("version") or ""),
        "status": str(payload.get("status") or ""),
        "decision_status": str(decision.get("decision_status") or ""),
        "m3_closeout_ready": bool(decision.get("m3_closeout_ready")),
        "m3_steady_state_ready": bool(decision.get("m3_steady_state_ready")),
        "return_to_ranked_decision_hardening_ready": bool(decision.get("return_to_ranked_decision_hardening_ready")),
        "policy_pointer_promotion_allowed": bool(decision.get("policy_pointer_promotion_allowed")),
        "chart_fact_mutation_allowed": bool(decision.get("chart_fact_mutation_allowed")),
        "fixed_bazi_verdict_allowed": bool(decision.get("fixed_bazi_verdict_allowed")),
    }


def _ranked_summary(ranked_decisions: Mapping[str, Any]) -> dict[str, Any]:
    rows: dict[str, dict[str, Any]] = {}
    for domain in M5_DECISION_DOMAINS:
        decision = _mapping(ranked_decisions.get(domain))
        basis = _mapping(decision.get("scoring_basis"))
        rows[domain] = {
            "status": str(decision.get("status") or ""),
            "primary_candidate": str(decision.get("primary_candidate") or ""),
            "candidate_score_count": len(_mapping(decision.get("candidate_scores"))),
            "primary_is_scored": str(decision.get("primary_candidate") or "") in _mapping(decision.get("candidate_scores")),
            "supporting_evidence_count": len(_list(decision.get("supporting_evidence"))),
            "weakening_evidence": _list(decision.get("weakening_evidence")),
            "boundary": str(decision.get("boundary") or ""),
            "basis_version": str(basis.get("version") or ""),
            "basis_boundary": str(basis.get("boundary") or ""),
            "dynamic_path_count": float(basis.get("dynamic_path_count", 0.0) or 0.0),
            "branch_conflict_path_count": float(basis.get("branch_conflict_path_count", 0.0) or 0.0),
            "tongguan_path_count": float(basis.get("tongguan_path_count", 0.0) or 0.0),
            "zhihua_path_count": float(basis.get("zhihua_path_count", 0.0) or 0.0),
            "model_signal_interface_version": str(basis.get("model_signal_interface_version") or ""),
            "model_signal_calibration_profile_version": str(basis.get("model_signal_calibration_profile_version") or ""),
            "root_fact_summary_version": str(basis.get("root_fact_summary_version") or ""),
            "root_vault_boundary": str(basis.get("root_vault_boundary") or ""),
            "raw_forbidden_fields": [
                field for field in ("raw_score", "raw_weight", "energy", "stability", "volatility")
                if field in basis
            ],
        }
    return {
        "decision_domains": sorted(rows),
        "decision_domain_count": len(rows),
        "decisions": rows,
        "candidate_score_total": sum(row["candidate_score_count"] for row in rows.values()),
        "supporting_evidence_total": sum(row["supporting_evidence_count"] for row in rows.values()),
        "all_primary_scored": all(row["primary_is_scored"] for row in rows.values()),
        "all_candidate_bound": all(
            row["status"] == "ranked_candidate"
            and ("not_fixed" in row["boundary"] or "not_final" in row["boundary"])
            for row in rows.values()
        ),
        "raw_forbidden_field_hits": sorted({field for row in rows.values() for field in row["raw_forbidden_fields"]}),
    }


def _evidence_summary(
    *,
    m3_completion_summary: Mapping[str, Any],
    krp_library_summary: Mapping[str, Any],
    structure_path_scores: Mapping[str, Any],
    feature_evidence: list[Mapping[str, Any]],
) -> dict[str, Any]:
    evidence_domains = Counter(str(row.get("domain") or "") for row in feature_evidence)
    krp_by_domain = _mapping(krp_library_summary.get("by_domain"))
    required_support = _mapping(m3_completion_summary.get("required_support"))
    return {
        "m3_completion_version": str(m3_completion_summary.get("version") or ""),
        "m3_completion_status": str(m3_completion_summary.get("status") or ""),
        "m3_completion_boundary": str(m3_completion_summary.get("boundary") or ""),
        "m3_acts_as_conclusion_engine": bool(m3_completion_summary.get("acts_as_conclusion_engine")),
        "source_family_count": int(m3_completion_summary.get("source_family_count", 0) or 0),
        "krp_domain_count": int(m3_completion_summary.get("krp_domain_count", 0) or len(krp_by_domain)),
        "rule_evidence_count": int(m3_completion_summary.get("rule_evidence_count", 0) or evidence_domains.get("rule", 0)),
        "dynamic_path_count": int(m3_completion_summary.get("dynamic_path_count", 0) or float(structure_path_scores.get("dynamic_path_count", 0.0) or 0.0)),
        "m5_ranked_decision_support_count": int(m3_completion_summary.get("m5_ranked_decision_support_count", 0) or 0),
        "required_support": dict(required_support),
        "feature_evidence_domain_counts": dict(evidence_domains),
        "krp_domains": sorted(str(domain) for domain in krp_by_domain if str(domain)),
        "structure_path_scores": {str(key): value for key, value in structure_path_scores.items()},
    }


def _synthetic_summary(m5_contract: Mapping[str, Any], strength_structure: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "m5_contract": {
            "suite_id": str(m5_contract.get("suite_id") or ""),
            "passed": bool(m5_contract.get("passed")),
            "case_count": int(m5_contract.get("case_count", 0) or 0),
            "passed_count": int(m5_contract.get("passed_count", 0) or 0),
        },
        "strength_structure_useful_god": {
            "suite_id": str(strength_structure.get("suite_id") or ""),
            "passed": bool(strength_structure.get("passed")),
            "case_count": int(strength_structure.get("case_count", 0) or 0),
            "passed_count": int(strength_structure.get("passed_count", 0) or 0),
        },
    }


def _checks(
    *,
    closeout_summary: Mapping[str, Any],
    ranked_summary: Mapping[str, Any],
    evidence_summary: Mapping[str, Any],
    synthetic_summary: Mapping[str, Any],
) -> list[dict[str, Any]]:
    decisions = _mapping(ranked_summary.get("decisions"))
    m5_contract = _mapping(synthetic_summary.get("m5_contract"))
    strength_tier = _mapping(synthetic_summary.get("strength_structure_useful_god"))
    return [
        {
            "check_id": "m3_g6_closeout_ready",
            "passed": (
                closeout_summary["version"] == "v30.m3_source_backlog_closeout.v1"
                and closeout_summary["m3_closeout_ready"]
                and closeout_summary["return_to_ranked_decision_hardening_ready"]
            ),
            "expected": "M3-G6 closeout is ready before M5 hardening",
        },
        {
            "check_id": "m5_ranked_domains_complete",
            "passed": (
                set(ranked_summary["decision_domains"]) == set(M5_DECISION_DOMAINS)
                and ranked_summary["all_primary_scored"]
                and ranked_summary["candidate_score_total"] >= 15
            ),
            "expected": "strength, structure_pattern, and useful_god ranked candidates are complete",
        },
        {
            "check_id": "m5_scoring_basis_consumes_m1_m2_m4",
            "passed": all(
                _mapping(decisions.get(domain)).get("basis_version") == "v30.ranked_decision_scoring_basis.v1"
                and _mapping(decisions.get(domain)).get("model_signal_interface_version") == "v30.model_signal_interface_contract.v1"
                and _mapping(decisions.get(domain)).get("model_signal_calibration_profile_version") == "v30.model_signal_calibration_profile.v1"
                and _mapping(decisions.get(domain)).get("root_fact_summary_version") == "v30.root_vault_fact_summary.v1"
                for domain in M5_DECISION_DOMAINS
            ),
            "expected": "M5 basis consumes M1/M2 root/vault facts and M4 model signal interface",
        },
        {
            "check_id": "m5_consumes_m3_evidence_spine",
            "passed": (
                evidence_summary["m3_completion_version"] == "v30.m3_completion_summary.v1"
                and evidence_summary["m3_completion_status"] == "ready"
                and evidence_summary["source_family_count"] >= 6
                and evidence_summary["krp_domain_count"] >= 10
                and evidence_summary["rule_evidence_count"] >= 1
                and evidence_summary["dynamic_path_count"] > 0
                and evidence_summary["m5_ranked_decision_support_count"] >= 2
            ),
            "expected": "M3 source, K/R/P, rule, dynamic path, and M5 support signals are present",
        },
        {
            "check_id": "m5_decisions_have_evidence_and_counterevidence",
            "passed": all(
                _mapping(decisions.get(domain)).get("supporting_evidence_count", 0) >= 1
                and any(str(item).startswith("fixed_") for item in _mapping(decisions.get(domain)).get("weakening_evidence", []))
                for domain in M5_DECISION_DOMAINS
            ),
            "expected": "each M5 decision has supporting evidence and fixed-verdict counter-evidence guards",
        },
        {
            "check_id": "m5_candidate_boundary_and_raw_score_guard",
            "passed": (
                ranked_summary["all_candidate_bound"]
                and not ranked_summary["raw_forbidden_field_hits"]
                and not closeout_summary["policy_pointer_promotion_allowed"]
                and not closeout_summary["chart_fact_mutation_allowed"]
            ),
            "expected": "M5 remains candidate-bound, raw-score-free, and read-only",
        },
        {
            "check_id": "m5_synthetic_contracts_passed",
            "passed": (
                m5_contract["suite_id"] == "v30.synthetic.m5_ranked_decision_contract"
                and m5_contract["passed"]
                and int(m5_contract["case_count"]) >= 14
                and strength_tier["suite_id"] == "v30.synthetic.strength_structure_useful_god"
                and strength_tier["passed"]
            ),
            "expected": "M5 contract and strength/structure/useful-god synthetic tiers pass",
        },
    ]


def _decision(*, checks: list[dict[str, Any]], ranked_summary: Mapping[str, Any]) -> dict[str, Any]:
    failed = [row["check_id"] for row in checks if not row["passed"]]
    ready = not failed
    return {
        "decision_status": "m5_evidence_consumption_hardening_ready" if ready else "m5_evidence_consumption_hardening_blocked",
        "m5_evidence_consumption_ready": ready,
        "m5_candidate_boundary_preserved": ready,
        "ready_for_m5_calibration_replay": ready,
        "ranked_decision_domain_count": int(ranked_summary.get("decision_domain_count", 0) or 0),
        "candidate_score_total": int(ranked_summary.get("candidate_score_total", 0) or 0),
        "hardening_check_count": len(checks),
        "passed_hardening_check_count": sum(1 for row in checks if row["passed"]),
        "failed_hardening_check_ids": failed,
        "policy_pointer_promotion_allowed": False,
        "pointer_write_performed": False,
        "chart_fact_mutation_allowed": False,
        "fixed_bazi_verdict_allowed": False,
        "full_pytest_required": False,
        "full_518k_required": False,
        "blockers": ["m5_evidence_consumption_checks_failed"] if failed else [],
    }


def _next_selection(decision: Mapping[str, Any]) -> dict[str, Any]:
    if decision["m5_evidence_consumption_ready"]:
        return {
            "next_task": "M5 Calibration Replay Review",
            "reason": "M5 consumes sealed M3 evidence; next review calibration replay before any threshold or weight changes.",
            "full_pytest_required": False,
            "full_518k_required": False,
        }
    return {
        "next_task": "M5 Evidence Consumption Remediation",
        "reason": "M5 evidence consumption checks are blocked; repair ranked decision evidence links before calibration replay.",
        "full_pytest_required": False,
        "full_518k_required": False,
    }


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _write_artifact(payload: Mapping[str, Any], artifact_dir: Path) -> Path:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    path = artifact_dir / f"{payload['review_id']}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
