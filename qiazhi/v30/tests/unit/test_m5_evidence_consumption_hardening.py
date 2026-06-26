from __future__ import annotations

from pathlib import Path

from v30.validation import (
    build_m5_evidence_consumption_hardening,
    run_m5_evidence_consumption_hardening,
)


def _m3_closeout(*, blocked: bool = False) -> dict[str, object]:
    return {
        "version": "v30.m3_source_backlog_closeout.v1",
        "status": "blocked" if blocked else "completed",
        "decision": {
            "decision_status": "m3_g6_source_backlog_closeout_blocked" if blocked else "m3_g6_source_backlog_closeout_ready",
            "m3_closeout_ready": not blocked,
            "m3_steady_state_ready": not blocked,
            "return_to_ranked_decision_hardening_ready": not blocked,
            "policy_pointer_promotion_allowed": False,
            "chart_fact_mutation_allowed": False,
            "fixed_bazi_verdict_allowed": False,
        },
    }


def _ranked_decisions(*, raw_hit: bool = False) -> dict[str, object]:
    basis = {
        "version": "v30.ranked_decision_scoring_basis.v1",
        "boundary": "ranked_decision_scoring_basis_uses_chart_facts_and_model_signals_not_fixed_verdict",
        "dynamic_path_count": 3.0,
        "branch_conflict_path_count": 2.0,
        "tongguan_path_count": 1.0,
        "zhihua_path_count": 1.0,
        "model_signal_interface_version": "v30.model_signal_interface_contract.v1",
        "model_signal_calibration_profile_version": "v30.model_signal_calibration_profile.v1",
        "root_fact_summary_version": "v30.root_vault_fact_summary.v1",
        "root_vault_boundary": "root_vault_summary_records_presence_without_strength_or_useful_god_verdict",
    }
    if raw_hit:
        basis["raw_score"] = 0.9
    return {
        "strength": {
            "status": "ranked_candidate",
            "primary_candidate": "balanced",
            "candidate_scores": {"balanced": 0.8, "strong": 0.4, "weak": 0.3, "slightly_strong": 0.5, "slightly_weak": 0.4},
            "scoring_basis": basis,
            "supporting_evidence": ["evidence:strength"],
            "weakening_evidence": ["fixed_strength_verdict"],
            "boundary": "strength_decision_ranked_candidate_not_final_verdict",
        },
        "structure_pattern": {
            "status": "ranked_candidate",
            "primary_candidate": "ordinary_structure_review",
            "candidate_scores": {"ordinary_structure_review": 0.8, "dynamic_structure_review": 0.5, "disputed_structure_review": 0.4, "mediation_path_review": 0.3, "regulation_climate_boundary_review": 0.3},
            "scoring_basis": basis,
            "supporting_evidence": ["evidence:structure"],
            "weakening_evidence": ["fixed_geju_verdict"],
            "boundary": "structure_pattern_ranked_candidate_not_fixed_geju",
        },
        "useful_god": {
            "status": "ranked_candidate",
            "primary_candidate": "balance_review",
            "candidate_scores": {"balance_review": 0.8, "resource_or_self_support_review": 0.5, "output_or_wealth_release_review": 0.4, "authority_regulation_review": 0.3, "climate_regulation_review": 0.3},
            "scoring_basis": basis,
            "supporting_evidence": ["evidence:useful"],
            "weakening_evidence": ["fixed_useful_god_verdict"],
            "boundary": "useful_god_ranked_candidate_not_fixed_favorable_verdict",
        },
    }


def _m3_completion() -> dict[str, object]:
    return {
        "version": "v30.m3_completion_summary.v1",
        "status": "ready",
        "source_family_count": 6,
        "krp_domain_count": 12,
        "rule_evidence_count": 3,
        "dynamic_path_count": 4,
        "m5_ranked_decision_support_count": 3,
        "required_support": {"m5_ranked_decision_support": True},
        "acts_as_conclusion_engine": False,
        "boundary": "m3_completion_summary_validates_evidence_spine_supports_m4_m5_m6_not_final_verdicts",
    }


def _synthetic(suite_id: str, case_count: int) -> dict[str, object]:
    return {
        "suite_id": suite_id,
        "passed": True,
        "case_count": case_count,
        "passed_count": case_count,
        "failed_count": 0,
    }


def _build(**overrides):
    payload = {
        "m3_closeout": _m3_closeout(),
        "ranked_decisions": _ranked_decisions(),
        "m3_completion_summary": _m3_completion(),
        "krp_library_summary": {"by_domain": {"useful_god": 3, "structure_pattern": 3}},
        "structure_path_scores": {"dynamic_path_count": 4.0},
        "feature_evidence": [{"domain": "rule"}, {"domain": "useful_god"}],
        "m5_contract_synthetic": _synthetic("v30.synthetic.m5_ranked_decision_contract", 14),
        "strength_structure_synthetic": _synthetic("v30.synthetic.strength_structure_useful_god", 1),
    }
    payload.update(overrides)
    return build_m5_evidence_consumption_hardening(**payload)


def test_m5_evidence_consumption_hardening_ready(tmp_path: Path) -> None:
    result = _build(artifact_dir=tmp_path)
    decision = result["decision"]

    assert result["version"] == "v30.m5_evidence_consumption_hardening.v1"
    assert result["status"] == "completed"
    assert decision["decision_status"] == "m5_evidence_consumption_hardening_ready"
    assert decision["m5_evidence_consumption_ready"] is True
    assert decision["ready_for_m5_calibration_replay"] is True
    assert decision["policy_pointer_promotion_allowed"] is False
    assert decision["chart_fact_mutation_allowed"] is False
    assert result["next_mainline_selection"]["next_task"] == "M5 Calibration Replay Review"
    assert Path(str(result["artifact_uri"])).exists()


def test_m5_evidence_consumption_blocks_missing_m3_closeout() -> None:
    result = _build(m3_closeout=_m3_closeout(blocked=True))

    assert result["status"] == "blocked"
    assert result["decision"]["m5_evidence_consumption_ready"] is False
    assert "m3_g6_closeout_ready" in result["decision"]["failed_hardening_check_ids"]


def test_m5_evidence_consumption_blocks_raw_score_leak() -> None:
    result = _build(ranked_decisions=_ranked_decisions(raw_hit=True))

    assert result["status"] == "blocked"
    assert result["decision"]["m5_evidence_consumption_ready"] is False
    assert "m5_candidate_boundary_and_raw_score_guard" in result["decision"]["failed_hardening_check_ids"]
    assert result["ranked_decision_summary"]["raw_forbidden_field_hits"] == ["raw_score"]


def test_m5_evidence_consumption_runner_passes_targeted_gates(tmp_path: Path) -> None:
    result = run_m5_evidence_consumption_hardening(sample_limit=8, artifact_dir=tmp_path)

    assert result["decision"]["decision_status"] == "m5_evidence_consumption_hardening_ready"
    assert result["decision"]["ranked_decision_domain_count"] == 3
    assert result["decision"]["candidate_score_total"] >= 15
