from __future__ import annotations

from pathlib import Path

from v30.validation import (
    build_m5_calibration_replay_review,
    run_m5_calibration_replay_review,
)


def _h1(*, blocked: bool = False) -> dict[str, object]:
    return {
        "version": "v30.m5_evidence_consumption_hardening.v1",
        "status": "blocked" if blocked else "completed",
        "decision": {
            "decision_status": "m5_evidence_consumption_hardening_blocked" if blocked else "m5_evidence_consumption_hardening_ready",
            "m5_evidence_consumption_ready": not blocked,
            "ready_for_m5_calibration_replay": not blocked,
            "ranked_decision_domain_count": 3,
            "candidate_score_total": 17,
            "policy_pointer_promotion_allowed": False,
            "chart_fact_mutation_allowed": False,
            "fixed_bazi_verdict_allowed": False,
        },
        "ranked_decision_summary": {"raw_forbidden_field_hits": []},
    }


def _ranked_decisions(index: int = 0) -> dict[str, object]:
    strength_primary = ["weak", "slightly_weak", "balanced", "strong"][index % 4]
    useful_primary = {
        "weak": "resource_or_self_support_review",
        "slightly_weak": "resource_or_self_support_review",
        "balanced": "balance_review",
        "strong": "output_or_wealth_release_review",
    }[strength_primary]
    structure_basis = {
        "version": "v30.ranked_decision_scoring_basis.v1",
        "follow_structure_boundary_signal": index % 2 == 0,
        "special_structure_boundary_signal": index % 3 == 0,
        "regulation_climate_boundary_signal": index % 5 == 0,
        "disputed_structure_signal": index % 4 == 0,
        "non_unique_candidate_signal": True,
    }
    return {
        "strength": {
            "primary_candidate": strength_primary,
            "candidate_scores": {
                "weak": 0.65 if strength_primary == "weak" else 0.58,
                "slightly_weak": 0.63 if strength_primary == "slightly_weak" else 0.57,
                "balanced": 0.66 if strength_primary == "balanced" else 0.59,
                "strong": 0.64 if strength_primary == "strong" else 0.56,
            },
            "scoring_basis": {"version": "v30.ranked_decision_scoring_basis.v1"},
            "supporting_evidence": ["strength:evidence"],
            "weakening_evidence": ["fixed_strength_verdict"],
        },
        "structure_pattern": {
            "primary_candidate": "ordinary_structure_review",
            "candidate_scores": {
                "ordinary_structure_review": 0.66,
                "dynamic_structure_review": 0.62,
                "follow_structure_boundary_review": 0.60,
                "disputed_structure_review": 0.58,
            },
            "scoring_basis": structure_basis,
            "supporting_evidence": ["structure:evidence"],
            "weakening_evidence": ["fixed_geju_verdict"],
        },
        "useful_god": {
            "primary_candidate": useful_primary,
            "candidate_scores": {
                "balance_review": 0.64 if useful_primary == "balance_review" else 0.59,
                "resource_or_self_support_review": 0.65 if useful_primary == "resource_or_self_support_review" else 0.58,
                "output_or_wealth_release_review": 0.64 if useful_primary == "output_or_wealth_release_review" else 0.57,
                "climate_regulation_review": 0.56,
            },
            "scoring_basis": {"version": "v30.ranked_decision_scoring_basis.v1"},
            "supporting_evidence": ["useful:evidence"],
            "weakening_evidence": ["fixed_useful_god_verdict"],
        },
    }


def _suite(tier: str, count: int, *, passed: bool = True) -> dict[str, object]:
    return {
        "suite_id": f"v30.synthetic.{tier}",
        "passed": passed,
        "case_count": count,
        "passed_count": count if passed else count - 1,
        "failed_count": 0 if passed else 1,
        "results": [
            {
                "case_id": f"{tier}.{index}",
                "passed": passed,
                "failures": [] if passed else ["synthetic_failed"],
                "observed": {"ranked_decisions": _ranked_decisions(index)},
            }
            for index in range(count)
        ],
    }


def _training_signal(*, missing: bool = False) -> list[dict[str, object]]:
    if missing:
        return []
    return [
        {
            "signal_id": "v30.training_signal.m5_weight_replay",
            "domain": "ranked_decision",
            "signal_type": "candidate_weight_replay_and_useful_god_evidence_calibration",
            "strength": 0.91,
            "source_case_ids": ["real.1", "real.2"],
            "payload": {
                "basis_signal_counts": {
                    "follow_structure_boundary": 4,
                    "disputed_structure": 2,
                    "non_unique_candidate": 20,
                },
                "useful_god_evidence_coverage": 0.8,
                "useful_god_fixed_verdict_guard_count": 20,
                "boundary": "m5_weight_replay_trains_candidate_weights_not_chart_facts",
            },
        }
    ]


def _build(**overrides):
    payload = {
        "evidence_hardening": _h1(),
        "synthetic_suites": {
            "m5_ranked_decision_contract": _suite("m5_ranked_decision_contract", 30),
            "strength_structure_useful_god": _suite("strength_structure_useful_god", 1),
            "real_case_calibration_pack": _suite("real_case_calibration_pack", 30),
        },
        "training_signals": _training_signal(),
    }
    payload.update(overrides)
    return build_m5_calibration_replay_review(**payload)


def test_m5_calibration_replay_review_ready(tmp_path: Path) -> None:
    result = _build(artifact_dir=tmp_path)
    decision = result["decision"]

    assert result["version"] == "v30.m5_calibration_replay_review.v1"
    assert result["status"] == "completed"
    assert decision["decision_status"] == "m5_calibration_replay_review_ready"
    assert decision["m5_calibration_replay_review_ready"] is True
    assert decision["ready_for_threshold_change"] is False
    assert decision["policy_pointer_promotion_allowed"] is False
    assert decision["chart_fact_mutation_allowed"] is False
    assert result["next_mainline_selection"]["next_task"] == "M5 Calibration Replay Closeout"
    assert Path(str(result["artifact_uri"])).exists()


def test_m5_calibration_replay_blocks_missing_h1() -> None:
    result = _build(evidence_hardening=_h1(blocked=True))

    assert result["status"] == "blocked"
    assert result["decision"]["m5_calibration_replay_review_ready"] is False
    assert "m5_h1_evidence_hardening_ready" in result["decision"]["failed_review_check_ids"]


def test_m5_calibration_replay_blocks_missing_training_signal() -> None:
    result = _build(training_signals=_training_signal(missing=True))

    assert result["status"] == "blocked"
    assert result["decision"]["m5_calibration_replay_review_ready"] is False
    assert "m5_weight_replay_training_signal_present" in result["decision"]["failed_review_check_ids"]


def test_m5_calibration_replay_blocks_failed_real_case_tier() -> None:
    suites = {
        "m5_ranked_decision_contract": _suite("m5_ranked_decision_contract", 30),
        "strength_structure_useful_god": _suite("strength_structure_useful_god", 1),
        "real_case_calibration_pack": _suite("real_case_calibration_pack", 30, passed=False),
    }
    result = _build(synthetic_suites=suites)

    assert result["status"] == "blocked"
    assert "m5_replay_synthetic_tiers_passed" in result["decision"]["failed_review_check_ids"]


def test_m5_calibration_replay_runner_passes_targeted_gates(tmp_path: Path) -> None:
    result = run_m5_calibration_replay_review(sample_limit=8, artifact_dir=tmp_path)

    assert result["decision"]["decision_status"] == "m5_calibration_replay_review_ready"
    assert result["decision"]["ranked_observation_count"] >= 30
    assert result["training_signal_summary"]["m5_weight_replay_present"] is True
