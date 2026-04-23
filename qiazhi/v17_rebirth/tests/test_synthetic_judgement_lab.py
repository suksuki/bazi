from __future__ import annotations

import pytest

from v17_rebirth.testing.synthetic_lab import (
    SYNTHETIC_AUTHORITY_CASES,
    SYNTHETIC_RISK_CASES,
    authority_case_ids,
    pattern_fact,
    risk_case_ids,
    run_authority_case,
    run_risk_case,
)


pytestmark = [pytest.mark.regression, pytest.mark.synthetic]


@pytest.mark.parametrize("case", SYNTHETIC_RISK_CASES, ids=risk_case_ids())
def test_synthetic_risk_cases_emit_expected_pattern_candidates(case) -> None:
    run = run_risk_case(case)

    assert run.facts
    pattern_names = {
        str((fact.meta or {}).get("pattern_candidate") or "")
        for fact in run.facts
        if isinstance(fact.meta, dict)
    }
    for pattern_name in case.expected_patterns:
        assert pattern_name in pattern_names


def test_synthetic_officer_judgement_case_preserves_dual_bias_directions() -> None:
    run = run_risk_case(SYNTHETIC_RISK_CASES[0])

    contest = pattern_fact(run, "伤官见官")
    exhaust = pattern_fact(run, "伤官伤尽")

    assert contest is not None
    assert exhaust is not None
    assert contest.meta["god_ring_bias"]["taboo_bias"]["伤官"] > 0.0
    assert contest.meta["god_ring_bias"]["use_bias"]["正官"] > 0.0
    assert exhaust.meta["god_ring_bias"]["use_bias"]["伤官"] > 0.0
    assert exhaust.meta["god_ring_bias"]["taboo_bias"]["正官"] > 0.0
    assert exhaust.meta["work_evidence"]["effect_type"] == "benefit"


def test_synthetic_owl_food_case_protects_food_and_marks_owl_as_taboo() -> None:
    run = run_risk_case(SYNTHETIC_RISK_CASES[1])

    owl_food = pattern_fact(run, "枭印夺食")

    assert owl_food is not None
    assert owl_food.meta["god_ring_bias"]["use_bias"]["食神"] > 0.0
    assert owl_food.meta["god_ring_bias"]["taboo_bias"]["偏印"] > 0.0
    assert owl_food.meta["work_evidence"]["effect_type"] == "benefit"


@pytest.mark.parametrize("case", SYNTHETIC_AUTHORITY_CASES, ids=authority_case_ids())
def test_synthetic_authority_cases_emit_authority_and_resolved_payload(case) -> None:
    run = run_authority_case(case)

    assert run.facts
    assert run.authority["source"] == "classical.ziping.god_ring_resolver.v1"
    assert run.resolved["display_mode"] == "authority"
    assert run.resolved["source"] == "classical.ziping.god_ring_resolver.v1"
    assert isinstance(run.resolved["effect_scores"], dict)


def test_synthetic_authority_bias_case_surfaces_judgement_entries_and_use_shift() -> None:
    run = run_authority_case(SYNTHETIC_AUTHORITY_CASES[0])

    assert run.authority["judgement_bias"]["use_bias"]["伤官"] == pytest.approx(0.32, abs=1e-6)
    assert run.authority["judgement_bias"]["taboo_bias"]["正官"] == pytest.approx(0.26, abs=1e-6)
    assert run.authority["judgement_bias_entries"][0]["reason"] == "伤官见官"
    assert "伤官" in run.authority["use_gods"]
    assert "伤官" in run.resolved["god_of_use"]


def test_synthetic_authority_bias_case_surfaces_stage_bias_protocol() -> None:
    run = run_authority_case(SYNTHETIC_AUTHORITY_CASES[0])

    stage_bias = run.authority["stage_bias"]
    stage_protocol = run.authority["stage_bias_protocol"]

    assert stage_protocol["contract"] == "v17.authority.stage_bias.v1"
    assert stage_protocol["summary"]["entry_count"] == 2
    assert stage_bias["正官"]["use_boost"] == pytest.approx(0.644, abs=1e-6)
    assert stage_bias["正官"]["stability_boost"] == pytest.approx(0.46, abs=1e-6)
    assert stage_bias["比肩"]["taboo_boost"] == pytest.approx(0.608, abs=1e-6)
    assert stage_bias["比肩"]["volatility_boost"] == pytest.approx(0.684, abs=1e-6)


def test_synthetic_authority_tongguan_case_surfaces_bridge_candidates() -> None:
    run = run_authority_case(SYNTHETIC_AUTHORITY_CASES[1])

    assert set(run.authority["tongguan_gods"]) >= {"正印", "偏印"}
    assert set(run.resolved["tongguan_gods"]) >= {"正印", "偏印"}
    assert "偏印" in run.authority["use_gods"] or "正印" in run.authority["use_gods"]
    assert run.resolved["core_path_count"] >= 1
    assert isinstance(run.resolved["core_paths_preview"], list)


def test_synthetic_authority_blind_theme_case_surfaces_parallel_blind_bias() -> None:
    run = run_authority_case(SYNTHETIC_AUTHORITY_CASES[2])

    blind_protocol = run.authority["blind_bias_protocol"]
    assert blind_protocol["contract"] == "v17.blind.bias.v1"
    assert blind_protocol["authority_bridge_mode"] == "bias_only"
    assert blind_protocol["primary_route"] == "食伤生财"
    assert run.authority["blind_bias"]["use_bias"]["食神"] > 0.0
    assert run.authority["blind_bias"]["use_bias"]["伤官"] > 0.0
    assert run.authority["blind_bias"]["taboo_bias"]["正官"] > 0.0
    assert run.authority["blind_theme"]["body_mode"] == "disturbed_body"
