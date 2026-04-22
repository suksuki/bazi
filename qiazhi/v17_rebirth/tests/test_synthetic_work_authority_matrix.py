from __future__ import annotations

import pytest

from v17_rebirth.testing.synthetic_lab import (
    SYNTHETIC_CORE_CASES,
    core_case_ids,
    run_core_case,
)


pytestmark = [pytest.mark.regression, pytest.mark.synthetic]


@pytest.mark.parametrize("case", SYNTHETIC_CORE_CASES, ids=core_case_ids())
def test_synthetic_core_cases_emit_effect_scores_and_candidates(case) -> None:
    run = run_core_case(case)

    result = run.result
    assert isinstance(result.get("effect_scores"), dict)
    assert result.get("use_candidates")
    assert result.get("taboo_candidates")
    assert str(result.get("mode") or "").strip() == "six_pillar_spacetime_core"


def test_synthetic_core_officer_contest_routes_high_energy_low_stability_to_taboo() -> None:
    run = run_core_case(SYNTHETIC_CORE_CASES[0])
    result = run.result
    effect_scores = result["effect_scores"]

    assert result["use_candidates"][0]["god"] == "伤官"
    assert result["taboo_candidates"][0]["god"] == "正官"
    assert effect_scores["伤官"]["contest_pressure"] > 0.0
    assert effect_scores["正官"]["contest_pressure"] > 0.0
    assert effect_scores["伤官"]["authority_profile"] == "高能躁动"
    assert effect_scores["正官"]["authority_profile"] == "低能低稳"


def test_synthetic_core_positive_path_prefers_stable_fusion_lane() -> None:
    run = run_core_case(SYNTHETIC_CORE_CASES[1])
    result = run.result
    effect_scores = result["effect_scores"]

    assert result["use_candidates"][0]["god"] == "正官"
    assert result["taboo_candidates"][0]["god"] == "伤官"
    assert effect_scores["正官"]["authority_profile"] in {"高能稳态", "低能稳态"}
    assert effect_scores["伤官"]["authority_profile"] == "高能躁动"
    assert any(path["path_type"] == "stem_fusion" for path in result["paths"])


def test_synthetic_core_bridge_present_keeps_tongguan_lane_visible() -> None:
    run = run_core_case(SYNTHETIC_CORE_CASES[2])
    result = run.result

    tongguan_paths = [path for path in result["paths"] if path["path_type"] == "tongguan_present"]
    assert tongguan_paths
    assert any(candidate["god"] in {"正印", "偏印"} for candidate in result["use_candidates"])
    assert tongguan_paths[0]["evidence"]["mediator_element"] == "火"
