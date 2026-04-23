from __future__ import annotations

import pytest

from v17_rebirth.testing.synthetic_lab import (
    SYNTHETIC_PATTERN_CASES,
    pattern_case_fact,
    pattern_case_ids,
    run_pattern_case,
)


pytestmark = [pytest.mark.regression, pytest.mark.synthetic]


@pytest.mark.parametrize("case", SYNTHETIC_PATTERN_CASES, ids=pattern_case_ids())
def test_synthetic_pattern_cases_emit_expected_pattern_and_route_into_authority(case) -> None:
    run = run_pattern_case(case)
    fact = pattern_case_fact(run)

    assert fact is not None
    assert fact.meta["pattern_candidate"] == case.expected_pattern
    assert fact.meta["target_god"] == case.expected_target_god
    for god in case.expected_use_bias:
        assert fact.meta["god_ring_bias"]["use_bias"][god] > 0.0
    for god in case.expected_taboo_bias:
        assert fact.meta["god_ring_bias"]["taboo_bias"][god] > 0.0

    assert run.authority["source"] == "classical.ziping.god_ring_resolver.v1"
    assert run.resolved["display_mode"] == "authority"
    assert run.authority["judgement_bias_entries"]


def test_synthetic_shishen_zhisha_pattern_pushes_food_to_use_and_sha_to_taboo() -> None:
    run = run_pattern_case(SYNTHETIC_PATTERN_CASES[0])

    assert run.authority["judgement_bias"]["use_bias"]["食神"] > 0.0
    assert run.authority["judgement_bias"]["taboo_bias"]["七杀"] > 0.0
    assert run.authority["judgement_bias_entries"][0]["reason"] == "食神制杀"
    assert "食神" in run.authority["use_gods"] or "食神" in run.resolved["god_of_use"]


def test_synthetic_shangguan_peiyin_pattern_keeps_hurt_and_seal_on_support_side() -> None:
    run = run_pattern_case(SYNTHETIC_PATTERN_CASES[1])

    use_bias = run.authority["judgement_bias"]["use_bias"]
    assert use_bias["伤官"] > 0.0
    assert sum(use_bias.get(god, 0.0) for god in ("正印", "偏印")) > 0.0
    assert run.authority["judgement_bias"]["taboo_bias"] == {}


def test_synthetic_caipoyin_pattern_reroutes_seal_to_use_and_wealth_to_taboo() -> None:
    run = run_pattern_case(SYNTHETIC_PATTERN_CASES[2])

    use_bias = run.authority["judgement_bias"]["use_bias"]
    taboo_bias = run.authority["judgement_bias"]["taboo_bias"]
    assert sum(use_bias.get(god, 0.0) for god in ("正印", "偏印")) > 0.0
    assert sum(taboo_bias.get(god, 0.0) for god in ("正财", "偏财")) > 0.0
    assert run.authority["judgement_bias_entries"][0]["reason"] == "财破印"
