from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping
import json

from v30.validation.latent_policy_observability import run_latent_policy_observability_readiness
from v30.validation.synthetic_case import run_synthetic_tier
from v30.validation.training_signals import extract_training_signals


LATENT_ATTRIBUTE_ADMIN_TRAINING_REVIEW_VERSION = "v30.latent_attribute_admin_training_review.v1"

ALLOWED_LATENT_TRAINING_SCOPE = {
    "latent_attribute_inference",
    "question_strategy",
    "individualized_projection",
}

FORBIDDEN_LATENT_TRAINING_SCOPE = {
    "chart_facts",
    "calendar_conversion",
    "luck_cycle",
    "flow_timing",
    "four_pillars",
    "fixed_structure_verdict",
    "fixed_useful_god_verdict",
}


def run_latent_attribute_admin_training_review(
    *,
    review_id: str = "",
    artifact_dir: str | Path | None = None,
) -> dict[str, Any]:
    observability = run_latent_policy_observability_readiness(
        reading_id=review_id or "hf-r26-latent-admin-training-review"
    )
    suite = run_synthetic_tier("latent_bazi_divergence")
    signals = [signal.model_dump(mode="json") for signal in extract_training_signals(suite)]
    return build_latent_attribute_admin_training_review(
        observability=observability,
        latent_divergence_suite=suite.model_dump(mode="json"),
        training_signals=signals,
        review_id=review_id,
        artifact_dir=artifact_dir,
    )


def build_latent_attribute_admin_training_review(
    *,
    observability: Mapping[str, Any],
    latent_divergence_suite: Mapping[str, Any],
    training_signals: list[Mapping[str, Any]],
    review_id: str = "",
    artifact_dir: str | Path | None = None,
) -> dict[str, Any]:
    reviewed_at = datetime.now(timezone.utc)
    resolved_review_id = review_id or f"v30.hf.r26.{reviewed_at.strftime('%Y%m%d%H%M%S%f')}"
    latent_signal = _latent_signal(training_signals)
    candidates = _candidate_rows(
        review_id=resolved_review_id,
        observability=_mapping(observability.get("observability")),
        latent_signal=latent_signal,
        suite=latent_divergence_suite,
    )
    checks = _checks(
        observability=observability,
        latent_signal=latent_signal,
        suite=latent_divergence_suite,
        candidates=candidates,
    )
    decision = _decision(checks, candidates)
    payload: dict[str, Any] = {
        "version": LATENT_ATTRIBUTE_ADMIN_TRAINING_REVIEW_VERSION,
        "review_id": resolved_review_id,
        "reviewed_at": reviewed_at.isoformat(),
        "status": "completed" if decision["review_ready"] else "blocked",
        "decision": decision,
        "source_summary": {
            "observability_version": str(observability.get("version") or ""),
            "observability_ready": _mapping(observability.get("decision")).get("readiness_ready") is True,
            "latent_divergence_suite_id": str(latent_divergence_suite.get("suite_id") or ""),
            "latent_divergence_passed": latent_divergence_suite.get("passed") is True,
            "training_signal_count": len(training_signals),
            "latent_signal_present": bool(latent_signal),
        },
        "candidate_summary": {
            "candidate_count": len(candidates),
            "candidate_types": sorted(str(row.get("candidate_type") or "") for row in candidates),
            "allowed_training_scope": sorted(ALLOWED_LATENT_TRAINING_SCOPE),
            "forbidden_training_scope": sorted(FORBIDDEN_LATENT_TRAINING_SCOPE),
            "auto_apply_allowed_count": sum(1 for row in candidates if row.get("auto_apply_allowed") is True),
            "pointer_promotion_allowed_count": sum(1 for row in candidates if row.get("policy_pointer_promotion_allowed") is True),
            "chart_fact_mutation_allowed_count": sum(1 for row in candidates if row.get("chart_fact_mutation_allowed") is True),
        },
        "candidates": candidates,
        "checks": checks,
        "policy_boundary": {
            "review_only": True,
            "auto_apply_training_allowed": False,
            "policy_pointer_promotion_allowed": False,
            "chart_fact_mutation_allowed": False,
            "full_pytest_required": False,
            "synthetic_all_required": False,
            "full_518k_required": False,
            "live_llm_required": False,
            "boundary": "hf_r26_reviews_latent_training_candidates_without_promoting_policy_or_mutating_chart_facts",
        },
        "next_mainline_selection": _next_selection(decision),
        "boundary": "latent_attribute_admin_training_review_connects_observability_to_admin_training_review_only",
    }
    if artifact_dir is not None:
        payload["artifact_uri"] = str(_write_artifact(payload, Path(artifact_dir)))
    return payload


def _candidate_rows(
    *,
    review_id: str,
    observability: Mapping[str, Any],
    latent_signal: Mapping[str, Any],
    suite: Mapping[str, Any],
) -> list[dict[str, Any]]:
    observed = _mapping(latent_signal.get("payload"))
    influenced = observability.get("influenced_questions", [])
    influenced = influenced if isinstance(influenced, list) else []
    signal_strength = float(latent_signal.get("strength", 0.0) or 0.0)
    return [
        _candidate(
            review_id=review_id,
            candidate_type="latent_reverse_inference_review",
            target_domain="latent_attribute_inference",
            evidence_summary=(
                f"Review reverse inference from {int(observed.get('case_count', 0) or 0)} latent divergence cases; "
                f"signal_strength={round(signal_strength, 3)}."
            ),
            source_signal_id=str(latent_signal.get("signal_id") or ""),
            source_observation_ids=_str_list(observed.get("case_ids")),
        ),
        _candidate(
            review_id=review_id,
            candidate_type="latent_question_strategy_review",
            target_domain="question_strategy",
            evidence_summary=(
                f"Review latent question need from Admin-observed influenced questions: {len(influenced)}."
            ),
            source_signal_id=str(latent_signal.get("signal_id") or ""),
            source_observation_ids=[
                str(row.get("question_id") or "")
                for row in influenced
                if isinstance(row, Mapping) and row.get("question_id")
            ],
        ),
        _candidate(
            review_id=review_id,
            candidate_type="latent_individualized_projection_review",
            target_domain="individualized_projection",
            evidence_summary=(
                f"Review individualized projection only after latent divergence suite passed={suite.get('passed') is True}."
            ),
            source_signal_id=str(latent_signal.get("signal_id") or ""),
            source_observation_ids=_str_list(observed.get("projection_case_ids") or observed.get("case_ids")),
        ),
    ]


def _candidate(
    *,
    review_id: str,
    candidate_type: str,
    target_domain: str,
    evidence_summary: str,
    source_signal_id: str,
    source_observation_ids: list[str],
) -> dict[str, Any]:
    return {
        "candidate_id": f"{review_id}.{candidate_type}",
        "candidate_type": candidate_type,
        "target_domain": target_domain,
        "target_domains": [target_domain],
        "source_signal_id": source_signal_id,
        "source_observation_ids": sorted({row for row in source_observation_ids if row}),
        "source_observation_count": len({row for row in source_observation_ids if row}),
        "evidence_summary": evidence_summary,
        "recommended_review_action": "admin_review_before_any_policy_candidate",
        "allowed_training_scope": sorted(ALLOWED_LATENT_TRAINING_SCOPE),
        "forbidden_training_scope": sorted(FORBIDDEN_LATENT_TRAINING_SCOPE),
        "requires_operator_review": True,
        "auto_apply_allowed": False,
        "policy_pointer_promotion_allowed": False,
        "chart_fact_mutation_allowed": False,
        "fixed_bazi_verdict_allowed": False,
        "status": "review_candidate",
        "boundary": "latent_attribute_training_candidate_is_review_only_not_policy_write",
    }


def _checks(
    *,
    observability: Mapping[str, Any],
    latent_signal: Mapping[str, Any],
    suite: Mapping[str, Any],
    candidates: list[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    obs_decision = _mapping(observability.get("decision"))
    return [
        {
            "check_id": "hf_r25_observability_ready",
            "passed": observability.get("version") == "v30.latent_policy_observability_readiness.v1"
            and obs_decision.get("readiness_ready") is True,
            "observed": {"version": observability.get("version"), "decision": obs_decision.get("decision_status")},
        },
        {
            "check_id": "latent_divergence_synthetic_passed",
            "passed": suite.get("passed") is True and int(suite.get("passed_count", 0) or 0) >= 2,
            "observed": {
                "suite_id": suite.get("suite_id"),
                "passed": suite.get("passed"),
                "passed_count": suite.get("passed_count"),
                "case_count": suite.get("case_count"),
            },
        },
        {
            "check_id": "latent_training_signal_available",
            "passed": latent_signal.get("signal_id") == "v30.training_signal.latent_bazi_attribute_alignment",
            "observed": {"signal_id": latent_signal.get("signal_id"), "strength": latent_signal.get("strength")},
        },
        {
            "check_id": "candidate_rows_cover_allowed_training_scope",
            "passed": {str(row.get("target_domain") or "") for row in candidates} == ALLOWED_LATENT_TRAINING_SCOPE,
            "observed": {"target_domains": sorted(str(row.get("target_domain") or "") for row in candidates)},
        },
        {
            "check_id": "candidate_boundaries_block_chart_fact_and_pointer_writes",
            "passed": all(
                row.get("auto_apply_allowed") is False
                and row.get("policy_pointer_promotion_allowed") is False
                and row.get("chart_fact_mutation_allowed") is False
                and FORBIDDEN_LATENT_TRAINING_SCOPE <= set(_str_list(row.get("forbidden_training_scope")))
                for row in candidates
            ),
            "observed": {
                "candidate_count": len(candidates),
                "forbidden_scope": sorted(FORBIDDEN_LATENT_TRAINING_SCOPE),
            },
        },
    ]


def _decision(checks: list[Mapping[str, Any]], candidates: list[Mapping[str, Any]]) -> dict[str, Any]:
    failed = [str(row.get("check_id") or "") for row in checks if row.get("passed") is not True]
    ready = not failed and len(candidates) == 3
    return {
        "review_ready": ready,
        "decision_status": "hf_r26_latent_attribute_admin_training_review_ready" if ready else "hf_r26_latent_attribute_admin_training_review_blocked",
        "check_count": len(checks),
        "passed_check_count": len(checks) - len(failed),
        "failed_check_ids": failed,
        "candidate_count": len(candidates),
        "rationale": (
            "Latent attribute training candidates are available for Admin review only and cannot mutate chart facts or promote pointers."
            if ready
            else "Repair observability, latent divergence signal, or candidate boundaries before continuing."
        ),
    }


def _next_selection(decision: Mapping[str, Any]) -> dict[str, Any]:
    if decision.get("review_ready") is True:
        return {
            "task_id": "HF-R2.7",
            "title": "Latent Attribute Training UI Review Panel",
            "scope": [
                "render latent training candidates in the Admin training page",
                "preserve manual review and no-pointer-promotion boundary",
            ],
        }
    return {
        "task_id": "HF-R2.6-FIX",
        "title": "Repair Latent Attribute Admin Training Review",
        "scope": ["repair missing signal, observability, or candidate boundary checks"],
    }


def _latent_signal(signals: list[Mapping[str, Any]]) -> Mapping[str, Any]:
    for signal in signals:
        if signal.get("signal_id") == "v30.training_signal.latent_bazi_attribute_alignment":
            return signal
    return {}


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _str_list(value: object) -> list[str]:
    return [str(row) for row in value] if isinstance(value, list) else []


def _write_artifact(payload: Mapping[str, Any], artifact_dir: Path) -> Path:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    path = artifact_dir / f"{payload['review_id']}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
