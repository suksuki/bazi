from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from v20.learning.orchestrator_memory_training import build_orchestrator_memory_training_report
from v20.learning.orchestrator_policy_observability_training import build_policy_observability_training_report
from v20.learning.question_source_training import build_question_source_training_report
from v20.storage.local_jsonl import LocalJsonlStore, local_jsonl_store_from_env


ProgressCallback = Callable[[str], None]

QUALITY_SCORING_POLICY = {
    "version": "v20.orchestrator_policy_candidate_quality_policy.v1",
    "status": "active",
    "base_score": 0.2,
    "candidate_type_weights": {
        "mainline_arbitration_weight_policy": 0.16,
        "question_focus_policy": 0.13,
        "brain_memory_policy": 0.1,
        "question_source_graph_quality_policy": 0.08,
    },
    "memory_support_ratio_weight": 0.24,
    "sample_volume_unit_weight": 0.035,
    "sample_volume_max_weight": 0.16,
    "recommendation_type_weights": {
        "promotion_signal": 0.18,
        "coverage_signal": 0.14,
        "rollback_watch": 0.11,
        "steady_state": 0.08,
        "default": 0.06,
    },
    "observability_condition_weights": {
        "fallback_pressure": 0.1,
        "candidate_consumed_strength": 0.1,
    },
    "thresholds": {
        "high_quality_min": 0.72,
        "medium_quality_min": 0.45,
        "fallback_pressure_min": 0.5,
        "candidate_consumed_strength_min": 0.66,
    },
    "runtime_mutation": False,
    "guardrails": [
        "QUALITY_POLICY_IS_VERSIONED",
        "QUALITY_POLICY_RANKS_ONLY",
        "NO_RUNTIME_POLICY_WRITE_FROM_QUALITY_POLICY",
    ],
}


def build_orchestrator_policy_candidate_report(
    *,
    memory_training_report: dict[str, object] | None = None,
    policy_observability_report: dict[str, object] | None = None,
    question_source_training_report: dict[str, object] | None = None,
    store: LocalJsonlStore | None = None,
    progress: ProgressCallback | None = None,
) -> dict[str, object]:
    report = memory_training_report or build_orchestrator_memory_training_report(store=store, progress=progress)
    observability = policy_observability_report or build_policy_observability_training_report(store=store, progress=progress)
    source_training = question_source_training_report or build_question_source_training_report(store=store, progress=progress)
    quality_policy = _quality_scoring_policy()
    proposals = _ranked_candidates(
        _candidate_proposals(
            memory_report=report,
            observability=observability,
            question_source_training_report=source_training,
        ),
        observability,
        quality_policy,
    )
    review_artifact = _review_artifact(proposals, report)
    candidate_quality_summary = _candidate_quality_summary(proposals, quality_policy)
    _emit(progress, f"orchestrator policy candidates: {len(proposals)}")
    return {
        "version": "v20.orchestrator_policy_candidate_report.v1",
        "status": "ready_for_fast_iteration" if proposals else "not_enough_data",
        "source_report_version": report.get("version", ""),
        "source_policy_observability_version": observability.get("version", ""),
        "source_question_source_training_report_version": source_training.get("version", ""),
        "source_memory_signal_count": report.get("memory_signal_count", 0),
        "source_policy_observation_count": observability.get("observation_count", 0),
        "policy_observability_input_summary": _policy_observability_input_summary(observability),
        "quality_scoring_policy": quality_policy,
        "candidate_count": len(proposals),
        "candidate_quality_summary": candidate_quality_summary,
        "candidates": proposals,
        "review_artifact": review_artifact,
        "runtime_mutation": False,
        "guardrails": [
            "ORCHESTRATOR_POLICY_CANDIDATES_FAST_TRACK",
            "AUTO_ITERATION_POLICY_CANDIDATE",
            "RUNTIME_ROLLOUT_REQUIRES_VERSION_POINTER",
            "CORE_FACTS_REMAIN_DETERMINISTIC",
            "POLICY_OBSERVABILITY_RECOMMENDATIONS_CAN_FEED_NEXT_CANDIDATE",
            "CANDIDATE_QUALITY_SCORE_IS_RANKING_ONLY",
        ],
    }


def write_orchestrator_policy_candidate_artifact(
    *,
    store: LocalJsonlStore | None = None,
    policy_observability_report: dict[str, object] | None = None,
    question_source_training_report: dict[str, object] | None = None,
    output_dir: Path | None = None,
    progress: ProgressCallback | None = None,
) -> dict[str, object]:
    storage = store or local_jsonl_store_from_env()
    report = build_orchestrator_policy_candidate_report(
        store=storage,
        policy_observability_report=policy_observability_report,
        question_source_training_report=question_source_training_report,
        progress=progress,
    )
    directory = output_dir or storage.runtime_dir / "training" / "orchestrator_policy_candidates"
    directory.mkdir(parents=True, exist_ok=True)
    latest_path = directory / "latest.json"
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_path = directory / f"orchestrator_policy_candidates_{stamp}.json"
    payload = report | {
        "written_at": datetime.now(timezone.utc).isoformat(),
        "runtime_mutation": True,
    }
    latest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    run_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return {
        "version": "v20.orchestrator_policy_candidate_artifact_write.v1",
        "status": "written",
        "latest_path": str(latest_path),
        "run_path": str(run_path),
        "report_status": report["status"],
        "candidate_count": report["candidate_count"],
        "runtime_mutation": True,
        "guardrails": [
            "LOCAL_RUNTIME_ARTIFACT_ONLY",
            "NO_POSTGRES_WRITE",
            "NO_RUNTIME_POLICY_PROMOTION",
        ],
    }


def read_orchestrator_policy_candidate_artifact(*, output_dir: Path | None = None) -> dict[str, object]:
    runtime_dir = local_jsonl_store_from_env().runtime_dir
    latest_path = (output_dir or runtime_dir / "training" / "orchestrator_policy_candidates") / "latest.json"
    if not latest_path.exists():
        return {
            "version": "v20.orchestrator_policy_candidate_artifact_status.v1",
            "status": "not_built",
            "latest_path": str(latest_path),
            "runtime_mutation": False,
        }
    return json.loads(latest_path.read_text(encoding="utf-8")) | {"runtime_mutation": False}


def _candidate_proposals(
    memory_report: dict[str, object],
    observability: dict[str, object],
    question_source_training_report: dict[str, object],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for proposal in memory_report.get("training_proposals", ()):
        if not isinstance(proposal, dict):
            continue
        target = str(proposal.get("target", ""))
        if target == "mainline_arbitration_weight_policy":
            rows.append(_mainline_candidate(proposal))
        elif target == "question_focus_policy":
            rows.append(_question_focus_candidate(proposal))
    for proposal in question_source_training_report.get("training_proposals", ()):
        if not isinstance(proposal, dict):
            continue
        if str(proposal.get("target", "")) == "question_source_graph_quality_policy":
            rows.append(_question_source_candidate(proposal))
    rows.extend(_time_layer_candidates(memory_report))
    rows.extend(_policy_observability_candidates(observability))
    return [row for row in rows if row]


def _mainline_candidate(proposal: dict[str, object]) -> dict[str, object]:
    direction = str(proposal.get("suggested_direction", ""))
    action = {
        "accept_primary": "increase_primary_stability_weight",
        "switch_to_supporting": "increase_supporting_review_weight",
        "evidence_insufficient": "increase_evidence_gap_penalty",
        "defer_mainline": "increase_review_boundary_weight",
    }.get(direction, "collect_more_mainline_memory")
    return {
        "candidate_id": _candidate_id("mainline", str(proposal.get("primary_mainline_key", "")), direction),
        "candidate_type": "mainline_arbitration_weight_policy",
        "primary_mainline_key": proposal.get("primary_mainline_key", ""),
        "suggested_action": action,
        "supporting_direction": direction,
        "sample_count": proposal.get("sample_count", 0),
        "support_ratio": proposal.get("support_ratio", 0),
        "status": "auto_fast_track",
        "next_gate": "shadow_replay_then_version_pointer",
        "runtime_allowed": True,
    }


def _question_focus_candidate(proposal: dict[str, object]) -> dict[str, object]:
    return {
        "candidate_id": _candidate_id("question_focus", str(proposal.get("domain", "")), str(proposal.get("average_strength", ""))),
        "candidate_type": "question_focus_policy",
        "domain": proposal.get("domain", ""),
        "suggested_action": "review_domain_question_focus_boost",
        "signal_count": proposal.get("signal_count", 0),
        "average_strength": proposal.get("average_strength", 0),
        "status": "auto_fast_track",
        "next_gate": "question_ranking_shadow_replay",
        "runtime_allowed": True,
    }


def _question_source_candidate(proposal: dict[str, object]) -> dict[str, object]:
    return {
        "candidate_id": _candidate_id("question_source_graph_quality", str(proposal.get("source_key", "")), str(proposal.get("status", ""))),
        "candidate_type": "question_source_graph_quality_policy",
        "source_key": proposal.get("source_key", ""),
        "suggested_action": str(proposal.get("suggested_action", "increase_source_quality_prior")),
        "sample_count": proposal.get("sample_count", 0),
        "average_graph_score": proposal.get("average_graph_score", 0),
        "average_question_score": proposal.get("average_question_score", 0),
        "status": "auto_fast_track",
        "next_gate": "question_source_graph_quality_shadow_replay",
        "runtime_allowed": True,
    }


def _time_layer_candidates(report: dict[str, object]) -> list[dict[str, object]]:
    rows = []
    for summary in report.get("mainline_summaries", ()):
        if not isinstance(summary, dict):
            continue
        coordination = summary.get("coordination_status_counts", {})
        if not isinstance(coordination, dict):
            continue
        review_count = int(coordination.get("需复核", 0) or coordination.get("reviewing", 0) or 0)
        if review_count < 3:
            continue
        rows.append(
            {
                "candidate_id": _candidate_id("time_layer", str(summary.get("primary_mainline_key", "")), str(review_count)),
                "candidate_type": "brain_memory_policy",
                "primary_mainline_key": summary.get("primary_mainline_key", ""),
                "suggested_action": "keep_time_layer_missing_as_review_boundary",
                "review_sample_count": review_count,
                "status": "auto_fast_track",
                "next_gate": "time_layer_shadow_replay",
                "runtime_allowed": True,
            }
        )
    return rows


def _policy_observability_candidates(observability: dict[str, object]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for recommendation in observability.get("strategy_recommendations", ()):
        if not isinstance(recommendation, dict):
            continue
        key = str(recommendation.get("recommendation_key", ""))
        recommendation_type = str(recommendation.get("recommendation_type", ""))
        suggested_action = str(recommendation.get("suggested_action", ""))
        if not key:
            continue
        if recommendation_type == "data_collection":
            continue
        if recommendation_type == "coverage_signal" and "mainline_arbitration" in key:
            candidate_type = "mainline_arbitration_weight_policy"
            next_gate = "policy_observability_coverage_replay"
        elif recommendation_type == "coverage_signal" and "question_mainline_focus" in key:
            candidate_type = "question_focus_policy"
            next_gate = "policy_observability_question_focus_replay"
        else:
            candidate_type = "brain_memory_policy"
            next_gate = "policy_observability_fast_track_replay"
        rows.append({
            "candidate_id": _candidate_id("policy_observability", key, recommendation_type),
            "candidate_type": candidate_type,
            "source_recommendation_key": key,
            "source_recommendation_type": recommendation_type,
            "suggested_action": _candidate_action_from_observability(recommendation_type, key, suggested_action),
            "supporting_direction": recommendation_type,
            "status": "auto_fast_track",
            "next_gate": next_gate,
            "runtime_allowed": True,
        })
    return rows


def _candidate_action_from_observability(recommendation_type: str, key: str, suggested_action: str) -> str:
    if recommendation_type == "promotion_signal":
        return "keep_latest_candidate_active_from_observability"
    if recommendation_type == "rollback_watch":
        return "increase_candidate_coverage_before_next_version"
    if recommendation_type == "coverage_signal":
        return f"expand_policy_match_coverage:{key[:80]}"
    if recommendation_type == "data_collection":
        return "collect_more_policy_observability"
    return suggested_action[:120] or "continue_fast_track_observation"


def _policy_observability_input_summary(observability: dict[str, object]) -> dict[str, object]:
    trend = observability.get("trend_summary", {})
    if not isinstance(trend, dict):
        trend = {}
    recommendations = [row for row in observability.get("strategy_recommendations", ()) if isinstance(row, dict)]
    return {
        "version": "v20.orchestrator_policy_candidate_observability_input.v1",
        "status": str(trend.get("status", "")) or str(observability.get("status", "")) or "not_enough_data",
        "observation_count": int(observability.get("observation_count", 0) or 0),
        "candidate_consumed_ratio": float(observability.get("candidate_consumed_ratio", 0) or 0),
        "fallback_ratio": float(observability.get("fallback_ratio", 0) or 0),
        "recommendation_count": len(recommendations),
        "recommendation_keys": [
            str(row.get("recommendation_key", ""))
            for row in recommendations
            if row.get("recommendation_key")
        ][:8],
        "runtime_mutation": False,
        "guardrails": [
            "OBSERVABILITY_INPUT_SUMMARY_ONLY",
            "NO_POLICY_WRITE_FROM_CANDIDATE_INPUT",
            "FAST_TRACK_CANDIDATE_REMAINS_VERSIONED",
        ],
    }


def _ranked_candidates(candidates: list[dict[str, object]], observability: dict[str, object], quality_policy: dict[str, object]) -> list[dict[str, object]]:
    scored = []
    for index, candidate in enumerate(candidates):
        quality = _candidate_quality(candidate, observability, quality_policy)
        scored.append(dict(candidate) | {
            "quality_score": quality["quality_score"],
            "quality_band": quality["quality_band"],
            "quality_reasons": quality["quality_reasons"],
            "quality_rank": index + 1,
            "quality_policy_version": quality_policy.get("version", ""),
            "quality_runtime_mutation": False,
        })
    scored.sort(key=lambda row: (-float(row.get("quality_score", 0) or 0), str(row.get("candidate_id", ""))))
    for index, row in enumerate(scored, start=1):
        row["quality_rank"] = index
    return scored


def _candidate_quality(candidate: dict[str, object], observability: dict[str, object], quality_policy: dict[str, object]) -> dict[str, object]:
    score = _float(quality_policy.get("base_score", 0.2))
    reasons = ["baseline_fast_track_candidate"]
    candidate_type = str(candidate.get("candidate_type", ""))
    type_weights = quality_policy.get("candidate_type_weights", {})
    if isinstance(type_weights, dict) and candidate_type in type_weights:
        score += _float(type_weights.get(candidate_type, 0))
        reasons.append(f"{candidate_type}_candidate")
    support_ratio = _float(candidate.get("support_ratio", 0))
    if support_ratio:
        memory_weight = _float(quality_policy.get("memory_support_ratio_weight", 0.24))
        score += min(memory_weight, support_ratio * memory_weight)
        reasons.append("memory_support_ratio")
    sample_count = int(candidate.get("sample_count", 0) or candidate.get("signal_count", 0) or candidate.get("review_sample_count", 0) or 0)
    if sample_count:
        score += min(
            _float(quality_policy.get("sample_volume_max_weight", 0.16)),
            sample_count * _float(quality_policy.get("sample_volume_unit_weight", 0.035)),
        )
        reasons.append("sample_volume")
    recommendation_type = str(candidate.get("source_recommendation_type", ""))
    if recommendation_type:
        recommendation_weights = quality_policy.get("recommendation_type_weights", {})
        weight = 0.06
        if isinstance(recommendation_weights, dict):
            weight = _float(recommendation_weights.get(recommendation_type, recommendation_weights.get("default", 0.06)))
        score += weight
        reasons.append(f"observability_{recommendation_type}")
    fallback_ratio = _float(observability.get("fallback_ratio", 0))
    candidate_consumed_ratio = _float(observability.get("candidate_consumed_ratio", 0))
    thresholds = quality_policy.get("thresholds", {})
    thresholds = thresholds if isinstance(thresholds, dict) else {}
    condition_weights = quality_policy.get("observability_condition_weights", {})
    condition_weights = condition_weights if isinstance(condition_weights, dict) else {}
    if recommendation_type == "rollback_watch" and fallback_ratio >= _float(thresholds.get("fallback_pressure_min", 0.5)):
        score += _float(condition_weights.get("fallback_pressure", 0.1))
        reasons.append("fallback_pressure")
    if recommendation_type == "promotion_signal" and candidate_consumed_ratio >= _float(thresholds.get("candidate_consumed_strength_min", 0.66)):
        score += _float(condition_weights.get("candidate_consumed_strength", 0.1))
        reasons.append("candidate_consumed_strength")
    score = round(min(1.0, max(0.0, score)), 4)
    return {
        "quality_score": score,
        "quality_band": _quality_band(score, thresholds),
        "quality_reasons": reasons[:6],
    }


def _candidate_quality_summary(candidates: list[dict[str, object]], quality_policy: dict[str, object]) -> dict[str, object]:
    bands = {"high": 0, "medium": 0, "low": 0}
    for candidate in candidates:
        band = str(candidate.get("quality_band", "low"))
        bands[band if band in bands else "low"] += 1
    top = candidates[0] if candidates else {}
    return {
        "version": "v20.orchestrator_policy_candidate_quality_summary.v1",
        "quality_policy_version": quality_policy.get("version", ""),
        "candidate_count": len(candidates),
        "band_counts": bands,
        "top_candidate_id": str(top.get("candidate_id", "")),
        "top_quality_score": float(top.get("quality_score", 0) or 0),
        "runtime_mutation": False,
        "guardrails": [
            "QUALITY_SCORE_RANKS_CANDIDATES_ONLY",
            "NO_RUNTIME_POLICY_WRITE_FROM_QUALITY_SCORE",
            "FAST_TRACK_REMAINS_VERSION_POINTER_CONTROLLED",
        ],
    }


def _quality_scoring_policy() -> dict[str, object]:
    return json.loads(json.dumps(QUALITY_SCORING_POLICY, ensure_ascii=False))


def _quality_band(score: float, thresholds: dict[str, object]) -> str:
    if score >= _float(thresholds.get("high_quality_min", 0.72)):
        return "high"
    if score >= _float(thresholds.get("medium_quality_min", 0.45)):
        return "medium"
    return "low"


def _review_artifact(candidates: list[dict[str, object]], report: dict[str, object]) -> dict[str, object]:
    artifact_id = _candidate_id("artifact", str(report.get("version", "")), str(len(candidates)))
    return {
        "artifact_id": f"v20.orchestrator.policy.review.{artifact_id}",
        "artifact_type": "orchestrator_policy_candidate_review",
        "candidate_count": len(candidates),
        "source_report_version": report.get("version", ""),
        "source_memory_signal_count": report.get("memory_signal_count", 0),
        "review_status": "auto_recorded" if candidates else "no_candidates",
        "runtime_allowed": bool(candidates),
    }


def _candidate_id(*values: str) -> str:
    raw = "|".join(values)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def _float(value: object) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _emit(progress: ProgressCallback | None, message: str) -> None:
    if progress is not None:
        progress(message)
