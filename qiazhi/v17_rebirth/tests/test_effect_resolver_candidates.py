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
    assert result["use_candidates"][0]["authority_profile"] in {"高能稳态", "低能稳态"}
    assert str(result["use_candidates"][0]["authority_reason"]).strip()
    assert result["taboo_candidates"][0]["god"] == "正官"
    assert result["taboo_candidates"][0]["authority_profile"] in {"高能躁动", "低能低稳"}
    assert any(row["god"] == "正官" for row in result["dual_role_candidates"])
    assert "authority_profile" in effect_scores["食神"]
    assert "authority_use_score" in effect_scores["食神"]


def test_pick_god_candidates_prefers_stable_gain_over_unstable_high_energy() -> None:
    effect_scores = {
        "七杀": {
            "benefit_score": 0.92,
            "harm_score": 0.22,
            "net_utility": 0.86,
            "resolved_utility": 0.92,
            "resolved_utility_flux": 1.14,
            "stability_score": 0.08,
            "activation_score": 0.84,
            "contest_weight": 0.42,
            "release_weight": 0.02,
            "flux_harm": 0.24,
            "flux_out_support": 0.12,
            "flux_out_resist": 0.16,
            "flux_tension_load": 0.62,
            "flux_reinforce_load": 0.04,
        },
        "正印": {
            "benefit_score": 0.66,
            "harm_score": 0.08,
            "net_utility": 0.68,
            "resolved_utility": 0.72,
            "resolved_utility_flux": 0.88,
            "stability_score": 0.46,
            "activation_score": 0.32,
            "contest_weight": 0.06,
            "release_weight": 0.18,
            "flux_harm": 0.02,
            "flux_out_support": 0.28,
            "flux_out_resist": 0.01,
            "flux_tension_load": 0.08,
            "flux_reinforce_load": 0.22,
        },
    }

    result = pick_god_candidates(effect_scores)
    assert result["use_candidates"][0]["god"] == "正印"
    assert effect_scores["七杀"]["authority_profile"] == "高能躁动"
    assert effect_scores["正印"]["authority_profile"] in {"高能稳态", "低能稳态"}
    assert effect_scores["正印"]["authority_use_score"] > effect_scores["七杀"]["authority_use_score"]


def test_pick_god_candidates_consumes_climate_axis_deltas() -> None:
    effect_scores = {
        "食神": {
            "benefit_score": 0.66,
            "harm_score": 0.10,
            "net_utility": 0.62,
            "resolved_utility": 0.66,
            "resolved_utility_flux": 0.74,
            "stability_score": 0.22,
            "activation_score": 0.28,
            "contest_weight": 0.06,
            "release_weight": 0.14,
            "flux_harm": 0.02,
            "flux_out_support": 0.22,
            "flux_out_resist": 0.01,
            "flux_tension_load": 0.06,
            "flux_reinforce_load": 0.16,
            "climate_efficiency_delta": 0.22,
            "climate_stability_delta": 0.18,
            "climate_priority_delta": 0.24,
        },
        "正官": {
            "benefit_score": 0.72,
            "harm_score": 0.18,
            "net_utility": 0.68,
            "resolved_utility": 0.72,
            "resolved_utility_flux": 0.80,
            "stability_score": 0.18,
            "activation_score": 0.32,
            "contest_weight": 0.08,
            "release_weight": 0.08,
            "flux_harm": 0.03,
            "flux_out_support": 0.18,
            "flux_out_resist": 0.04,
            "flux_tension_load": 0.14,
            "flux_reinforce_load": 0.12,
            "climate_efficiency_delta": -0.18,
            "climate_stability_delta": -0.12,
            "climate_priority_delta": -0.22,
        },
    }

    result = pick_god_candidates(effect_scores)
    assert result["use_candidates"][0]["god"] == "食神"
    assert effect_scores["食神"]["authority_climate_fit"] > effect_scores["正官"]["authority_climate_fit"]
    assert effect_scores["食神"]["authority_use_score"] > effect_scores["正官"]["authority_use_score"]
    assert effect_scores["正官"]["authority_taboo_score"] > effect_scores["食神"]["authority_taboo_score"]
