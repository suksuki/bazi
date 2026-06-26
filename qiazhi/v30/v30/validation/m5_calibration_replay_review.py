from __future__ import annotations

import json
from collections import Counter
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from v30.validation.m5_evidence_consumption_hardening import (
    M5_DECISION_DOMAINS,
    run_m5_evidence_consumption_hardening,
)
from v30.validation.synthetic_case import run_synthetic_tier
from v30.validation.training_signals import extract_training_signals


M5_CALIBRATION_REPLAY_REVIEW_VERSION = "v30.m5_calibration_replay_review.v1"

M5_REPLAY_SYNTHETIC_TIERS = (
    "m5_ranked_decision_contract",
    "strength_structure_useful_god",
    "real_case_calibration_pack",
)


def run_m5_calibration_replay_review(
    *,
    sample_limit: int = 8,
    artifact_dir: str | Path | None = None,
) -> dict[str, Any]:
    evidence_hardening = run_m5_evidence_consumption_hardening(
        sample_limit=sample_limit,
        artifact_dir=artifact_dir,
    )
    synthetic_results = {
        tier: run_synthetic_tier(tier)
        for tier in M5_REPLAY_SYNTHETIC_TIERS
    }
    training_signals = []
    for result in synthetic_results.values():
        training_signals.extend(
            signal.model_dump(mode="json")
            for signal in extract_training_signals(result)
        )
    return build_m5_calibration_replay_review(
        evidence_hardening=evidence_hardening,
        synthetic_suites={
            tier: result.model_dump(mode="json")
            for tier, result in synthetic_results.items()
        },
        training_signals=training_signals,
        artifact_dir=artifact_dir,
    )


def build_m5_calibration_replay_review(
    *,
    evidence_hardening: Mapping[str, Any],
    synthetic_suites: Mapping[str, Mapping[str, Any]],
    training_signals: list[Mapping[str, Any]],
    artifact_dir: str | Path | None = None,
) -> dict[str, Any]:
    reviewed_at = datetime.now(timezone.utc)
    review_id = f"v30.m5.h2.{reviewed_at.strftime('%Y%m%d%H%M%S%f')}"
    evidence_summary = _evidence_hardening_summary(evidence_hardening)
    synthetic_summary = _synthetic_summary(synthetic_suites)
    replay_summary = _replay_summary(synthetic_suites)
    training_summary = _training_summary(training_signals)
    checks = _checks(
        evidence_summary=evidence_summary,
        synthetic_summary=synthetic_summary,
        replay_summary=replay_summary,
        training_summary=training_summary,
    )
    decision = _decision(checks=checks, replay_summary=replay_summary)
    payload: dict[str, Any] = {
        "version": M5_CALIBRATION_REPLAY_REVIEW_VERSION,
        "review_id": review_id,
        "reviewed_at": reviewed_at.isoformat(),
        "status": "completed" if decision["m5_calibration_replay_review_ready"] else "blocked",
        "decision": decision,
        "evidence_hardening_summary": evidence_summary,
        "synthetic_summary": synthetic_summary,
        "ranked_decision_replay_summary": replay_summary,
        "training_signal_summary": training_summary,
        "review_checks": checks,
        "policy_boundary": {
            "review_only": True,
            "ranked_candidates_only": True,
            "threshold_change_allowed": False,
            "runtime_decision_write_allowed": False,
            "auto_apply_training_allowed": False,
            "policy_pointer_promotion_allowed": False,
            "chart_fact_mutation_allowed": False,
            "fixed_bazi_verdict_allowed": False,
            "raw_model_score_visible": False,
            "full_pytest_required": False,
            "full_518k_required": False,
            "boundary": "m5_h2_reviews_calibration_replay_without_changing_weights_thresholds_or_chart_facts",
        },
        "next_mainline_selection": _next_selection(decision),
        "boundary": "m5_calibration_replay_review_links_synthetic_real_case_and_training_signals_as_read_only_calibration_evidence",
    }
    if artifact_dir is not None:
        payload["artifact_uri"] = str(_write_artifact(payload, Path(artifact_dir)))
    return payload


def _evidence_hardening_summary(payload: Mapping[str, Any]) -> dict[str, Any]:
    decision = _mapping(payload.get("decision"))
    ranked = _mapping(payload.get("ranked_decision_summary"))
    return {
        "version": str(payload.get("version") or ""),
        "status": str(payload.get("status") or ""),
        "decision_status": str(decision.get("decision_status") or ""),
        "m5_evidence_consumption_ready": bool(decision.get("m5_evidence_consumption_ready")),
        "ready_for_m5_calibration_replay": bool(decision.get("ready_for_m5_calibration_replay")),
        "ranked_decision_domain_count": int(decision.get("ranked_decision_domain_count", 0) or 0),
        "candidate_score_total": int(decision.get("candidate_score_total", 0) or 0),
        "raw_forbidden_field_hits": _list(ranked.get("raw_forbidden_field_hits")),
        "policy_pointer_promotion_allowed": bool(decision.get("policy_pointer_promotion_allowed")),
        "chart_fact_mutation_allowed": bool(decision.get("chart_fact_mutation_allowed")),
        "fixed_bazi_verdict_allowed": bool(decision.get("fixed_bazi_verdict_allowed")),
    }


def _synthetic_summary(suites: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    rows: dict[str, dict[str, Any]] = {}
    for tier in M5_REPLAY_SYNTHETIC_TIERS:
        suite = _mapping(suites.get(tier))
        rows[tier] = {
            "suite_id": str(suite.get("suite_id") or ""),
            "passed": bool(suite.get("passed")),
            "case_count": int(suite.get("case_count", 0) or 0),
            "passed_count": int(suite.get("passed_count", 0) or 0),
            "failed_count": int(suite.get("failed_count", 0) or 0),
        }
    return {
        "tiers": rows,
        "required_tier_count": len(M5_REPLAY_SYNTHETIC_TIERS),
        "passed_tier_count": sum(1 for row in rows.values() if row["passed"]),
        "case_count_total": sum(int(row["case_count"]) for row in rows.values()),
        "failed_count_total": sum(int(row["failed_count"]) for row in rows.values()),
    }


def _replay_summary(suites: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    replay_rows = _ranked_replay_rows(suites)
    domain_primary_counts: dict[str, Counter[str]] = {
        domain: Counter()
        for domain in M5_DECISION_DOMAINS
    }
    domain_candidate_score_counts: dict[str, Counter[str]] = {
        domain: Counter()
        for domain in M5_DECISION_DOMAINS
    }
    domain_top_gaps: dict[str, list[float]] = {domain: [] for domain in M5_DECISION_DOMAINS}
    basis_signal_counts = Counter()
    useful_supporting_evidence_count = 0
    useful_fixed_verdict_guard_count = 0
    complete_domain_rows = 0
    for row in replay_rows:
        ranked = _mapping(row.get("ranked_decisions"))
        if set(M5_DECISION_DOMAINS) <= set(ranked):
            complete_domain_rows += 1
        for domain in M5_DECISION_DOMAINS:
            decision = _mapping(ranked.get(domain))
            primary = str(decision.get("primary_candidate") or "")
            if primary:
                domain_primary_counts[domain][primary] += 1
            scores = _numeric_scores(_mapping(decision.get("candidate_scores")))
            for candidate_id in scores:
                domain_candidate_score_counts[domain][candidate_id] += 1
            gap = _top_gap(scores)
            if gap is not None:
                domain_top_gaps[domain].append(gap)
            basis = _mapping(decision.get("scoring_basis"))
            for key in (
                "follow_structure_boundary_signal",
                "special_structure_boundary_signal",
                "regulation_climate_boundary_signal",
                "disputed_structure_signal",
                "non_unique_candidate_signal",
            ):
                if basis.get(key):
                    basis_signal_counts[key] += 1
            if domain == "useful_god":
                useful_supporting_evidence_count += len(_list(decision.get("supporting_evidence")))
                if "fixed_useful_god_verdict" in _list(decision.get("weakening_evidence")):
                    useful_fixed_verdict_guard_count += 1
    return {
        "ranked_observation_count": len(replay_rows),
        "complete_domain_observation_count": complete_domain_rows,
        "source_suite_counts": dict(Counter(str(row.get("suite_key") or "") for row in replay_rows)),
        "domain_primary_candidate_counts": {
            domain: dict(counter)
            for domain, counter in domain_primary_counts.items()
        },
        "domain_candidate_score_counts": {
            domain: dict(counter)
            for domain, counter in domain_candidate_score_counts.items()
        },
        "top_gap_summary": {
            domain: _gap_summary(gaps)
            for domain, gaps in domain_top_gaps.items()
        },
        "basis_signal_counts": dict(basis_signal_counts),
        "close_candidate_count": sum(
            1
            for gaps in domain_top_gaps.values()
            for gap in gaps
            if gap <= 0.08
        ),
        "useful_god_supporting_evidence_count": useful_supporting_evidence_count,
        "useful_god_fixed_verdict_guard_count": useful_fixed_verdict_guard_count,
        "domains_with_primary_candidates": sorted(
            domain for domain, counter in domain_primary_counts.items()
            if counter
        ),
        "domains_with_candidate_scores": sorted(
            domain for domain, counter in domain_candidate_score_counts.items()
            if len(counter) >= 3
        ),
        "boundary": "ranked_decision_replay_summary_is_review_only_and_does_not_change_candidate_weights",
    }


def _training_summary(signals: list[Mapping[str, Any]]) -> dict[str, Any]:
    ids = [str(signal.get("signal_id") or "") for signal in signals]
    signal_by_id = {
        str(signal.get("signal_id") or ""): signal
        for signal in signals
        if signal.get("signal_id")
    }
    replay_signal = _mapping(signal_by_id.get("v30.training_signal.m5_weight_replay"))
    replay_payload = _mapping(replay_signal.get("payload"))
    return {
        "signal_count": len(signals),
        "signal_ids": sorted(set(ids)),
        "m5_weight_replay_present": bool(replay_signal),
        "m5_weight_replay_domain": str(replay_signal.get("domain") or ""),
        "m5_weight_replay_strength": float(replay_signal.get("strength", 0.0) or 0.0),
        "m5_weight_replay_source_case_count": len(_list(replay_signal.get("source_case_ids"))),
        "m5_weight_replay_boundary": str(replay_payload.get("boundary") or ""),
        "basis_signal_counts": _mapping(replay_payload.get("basis_signal_counts")),
        "useful_god_evidence_coverage": float(replay_payload.get("useful_god_evidence_coverage", 0.0) or 0.0),
        "useful_god_fixed_verdict_guard_count": int(replay_payload.get("useful_god_fixed_verdict_guard_count", 0) or 0),
        "boundary": "training_signals_can_tune_m5_candidate_weights_not_chart_facts",
    }


def _checks(
    *,
    evidence_summary: Mapping[str, Any],
    synthetic_summary: Mapping[str, Any],
    replay_summary: Mapping[str, Any],
    training_summary: Mapping[str, Any],
) -> list[dict[str, Any]]:
    tiers = _mapping(synthetic_summary.get("tiers"))
    return [
        {
            "check_id": "m5_h1_evidence_hardening_ready",
            "passed": (
                evidence_summary["version"] == "v30.m5_evidence_consumption_hardening.v1"
                and evidence_summary["m5_evidence_consumption_ready"]
                and evidence_summary["ready_for_m5_calibration_replay"]
                and not evidence_summary["raw_forbidden_field_hits"]
            ),
            "expected": "M5-H1 evidence consumption is ready before calibration replay review",
        },
        {
            "check_id": "m5_replay_synthetic_tiers_passed",
            "passed": (
                synthetic_summary["passed_tier_count"] == synthetic_summary["required_tier_count"]
                and _mapping(tiers.get("m5_ranked_decision_contract")).get("case_count", 0) >= 14
                and _mapping(tiers.get("strength_structure_useful_god")).get("case_count", 0) >= 1
                and _mapping(tiers.get("real_case_calibration_pack")).get("case_count", 0) >= 30
            ),
            "expected": "M5 contract, strength/structure/useful-god, and real-case calibration tiers pass",
        },
        {
            "check_id": "m5_ranked_decision_replay_complete",
            "passed": (
                replay_summary["ranked_observation_count"] >= 30
                and replay_summary["complete_domain_observation_count"] >= 20
                and set(replay_summary["domains_with_primary_candidates"]) == set(M5_DECISION_DOMAINS)
            ),
            "expected": "Replay has enough ranked observations across all M5 decision domains",
        },
        {
            "check_id": "m5_score_distribution_reviewable",
            "passed": (
                set(replay_summary["domains_with_candidate_scores"]) == set(M5_DECISION_DOMAINS)
                and all(
                    _mapping(_mapping(replay_summary["top_gap_summary"]).get(domain)).get("count", 0) >= 20
                    for domain in M5_DECISION_DOMAINS
                )
                and int(replay_summary["close_candidate_count"]) >= 1
            ),
            "expected": "Candidate score distributions and close-candidate cases are visible for calibration review",
        },
        {
            "check_id": "m5_weight_replay_training_signal_present",
            "passed": (
                training_summary["m5_weight_replay_present"]
                and training_summary["m5_weight_replay_domain"] == "ranked_decision"
                and training_summary["m5_weight_replay_boundary"] == "m5_weight_replay_trains_candidate_weights_not_chart_facts"
                and training_summary["useful_god_evidence_coverage"] > 0
                and training_summary["useful_god_fixed_verdict_guard_count"] >= 1
            ),
            "expected": "M5 replay emits candidate-weight training signal without chart fact mutation",
        },
        {
            "check_id": "m5_replay_read_only_boundary_preserved",
            "passed": (
                not evidence_summary["policy_pointer_promotion_allowed"]
                and not evidence_summary["chart_fact_mutation_allowed"]
                and not evidence_summary["fixed_bazi_verdict_allowed"]
            ),
            "expected": "Calibration replay is review-only and cannot mutate chart facts, verdicts, or policy pointers",
        },
    ]


def _decision(*, checks: list[dict[str, Any]], replay_summary: Mapping[str, Any]) -> dict[str, Any]:
    failed = [row["check_id"] for row in checks if not row["passed"]]
    ready = not failed
    return {
        "decision_status": "m5_calibration_replay_review_ready" if ready else "m5_calibration_replay_review_blocked",
        "m5_calibration_replay_review_ready": ready,
        "ready_for_m5_calibration_replay_closeout": ready,
        "ready_for_threshold_change": False,
        "ranked_observation_count": int(replay_summary.get("ranked_observation_count", 0) or 0),
        "complete_domain_observation_count": int(replay_summary.get("complete_domain_observation_count", 0) or 0),
        "close_candidate_count": int(replay_summary.get("close_candidate_count", 0) or 0),
        "review_check_count": len(checks),
        "passed_review_check_count": sum(1 for row in checks if row["passed"]),
        "failed_review_check_ids": failed,
        "policy_pointer_promotion_allowed": False,
        "pointer_write_performed": False,
        "chart_fact_mutation_allowed": False,
        "fixed_bazi_verdict_allowed": False,
        "threshold_write_performed": False,
        "full_pytest_required": False,
        "full_518k_required": False,
        "blockers": ["m5_calibration_replay_review_checks_failed"] if failed else [],
    }


def _next_selection(decision: Mapping[str, Any]) -> dict[str, Any]:
    if decision["m5_calibration_replay_review_ready"]:
        return {
            "next_task": "M5 Calibration Replay Closeout",
            "reason": "M5 replay is reviewable across synthetic and real-case tiers; next close out calibration replay before moving to downstream reading.",
            "full_pytest_required": False,
            "full_518k_required": False,
        }
    return {
        "next_task": "M5 Calibration Replay Remediation",
        "reason": "M5 replay review has blocked checks; repair replay coverage or training signal extraction before closeout.",
        "full_pytest_required": False,
        "full_518k_required": False,
    }


def _ranked_replay_rows(suites: Mapping[str, Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for suite_key, suite in suites.items():
        results = _list(_mapping(suite).get("results"))
        for result in results:
            if not isinstance(result, Mapping):
                continue
            observed = _mapping(result.get("observed"))
            ranked = _mapping(observed.get("ranked_decisions"))
            if not ranked:
                continue
            rows.append({
                "suite_key": str(suite_key),
                "case_id": str(result.get("case_id") or ""),
                "ranked_decisions": ranked,
            })
    return rows


def _numeric_scores(scores: Mapping[str, Any]) -> dict[str, float]:
    return {
        str(candidate_id): float(score)
        for candidate_id, score in scores.items()
        if isinstance(score, (int, float))
    }


def _top_gap(scores: Mapping[str, float]) -> float | None:
    values = sorted(scores.values(), reverse=True)
    if len(values) < 2:
        return None
    return round(float(values[0] - values[1]), 3)


def _gap_summary(gaps: list[float]) -> dict[str, Any]:
    if not gaps:
        return {"count": 0, "min": None, "average": None, "close_count": 0}
    return {
        "count": len(gaps),
        "min": round(min(gaps), 3),
        "average": round(sum(gaps) / len(gaps), 3),
        "close_count": sum(1 for gap in gaps if gap <= 0.08),
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
