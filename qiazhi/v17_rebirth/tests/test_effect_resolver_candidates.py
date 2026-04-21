from __future__ import annotations

from v17_rebirth.backend.logic.core_engine.effect_resolver import pick_god_candidates


def test_pick_god_candidates_consumes_flux_tension_and_reinforce_loads() -> None:
    effect_scores = {
        "食神": {
            "benefit_score": 0.72,
            "harm_score": 0.18,
            "net_utility": 0.64,
            "resolved_utility": 0.66,
            "resolved_utility_flux": 0.92,
            "stability_score": 0.34,
            "contest_weight": 0.08,
            "flux_harm": 0.06,
            "flux_out_support": 0.42,
            "flux_out_resist": 0.02,
            "flux_tension_load": 0.04,
            "flux_reinforce_load": 0.28,
        },
        "正官": {
            "benefit_score": 0.61,
            "harm_score": 0.68,
            "net_utility": 0.71,
            "resolved_utility": 0.74,
            "resolved_utility_flux": 0.78,
            "stability_score": 0.16,
            "contest_weight": 0.36,
            "flux_harm": 0.42,
            "flux_out_support": 0.04,
            "flux_out_resist": 0.22,
            "flux_tension_load": 0.46,
            "flux_reinforce_load": 0.02,
        },
    }

    result = pick_god_candidates(effect_scores)
    assert result["use_candidates"][0]["god"] == "食神"
    assert result["taboo_candidates"][0]["god"] == "正官"
    assert any(row["god"] == "正官" for row in result["dual_role_candidates"])
