from __future__ import annotations

from v17_rebirth.backend.services.god_ring_authority import resolve_god_ring_authority
from v17_rebirth.backend.services.practitioner_choice_candidates import (
    build_practitioner_choice_candidates,
    normalize_practitioner_override_context,
    practitioner_override_prompt_lines,
    selected_override_gods,
)


def test_resolve_god_ring_authority_passes_judgement_bias_payload() -> None:
    raw = {
        "meta": {
            "god_ring_authority": {
                "use_gods": ["食神"],
                "taboo_gods": ["七杀"],
                "tongguan_gods": ["正财"],
                "source": "classical.ziping.god_ring_resolver.v1",
                "mode": "six_pillar_spacetime_core",
                "confidence": 0.83,
                "core_flux_meta": {
                    "enabled": True,
                    "chain_count": 8,
                },
                "judgement_bias": {
                    "use_bias": {"食神": 0.22},
                    "taboo_bias": {"七杀": 0.18},
                },
                "stage_bias": {
                    "食神": {
                        "lu": 1.2,
                        "blade": 0.0,
                        "general": 0.3,
                        "use_boost": 0.82,
                        "taboo_boost": 0.02,
                    }
                },
                "judgement_bias_entries": [
                    {
                        "plugin_id": "classical.pattern.shishen_zhisha.v1",
                        "source_label": "食神制杀",
                        "reason": "食神制杀",
                        "use_bias": {"食神": 0.22},
                        "taboo_bias": {"七杀": 0.18},
                    }
                ],
                "authority_layer_protocol": {
                    "contract": "v17.authority.layer_protocol.v1",
                    "authority_level": 1,
                    "override_forbidden": True,
                    "max_bias_ratio": 0.35,
                },
                "climate_modifier_layer": {
                    "contract": "v17.climate_modifier_layer.v1",
                    "ten_god_efficiency": {"食神": 0.12},
                },
            }
        }
    }

    info = resolve_god_ring_authority(raw_physics=raw, ranked_pairs=[("食神", 10.0), ("七杀", 6.0)])
    assert info["display_mode"] == "authority"
    assert info["judgement_bias"]["use_bias"]["食神"] == 0.22
    assert info["judgement_bias"]["taboo_bias"]["七杀"] == 0.18
    assert info["stage_bias"]["食神"]["lu"] == 1.2
    assert info["judgement_bias_entries"][0]["source_label"] == "食神制杀"
    assert info["core_flux_meta"]["enabled"] is True
    assert info["authority_layer_protocol"]["contract"] == "v17.authority.layer_protocol.v1"
    assert info["climate_modifier_layer"]["contract"] == "v17.climate_modifier_layer.v1"


def test_practitioner_choice_candidates_are_system_computed_with_confidence() -> None:
    authority = {
        "god_of_use": ["食神"],
        "god_of_taboo": ["七杀"],
        "confidence": 0.82,
        "core_use_candidates": [
            {"god": "食神", "score": 1.4, "authority_reason": "食神可制杀"},
            {"god": "正印", "score": 0.7, "authority_reason": "印可护身"},
        ],
        "core_taboo_candidates": [
            {"god": "七杀", "score": 1.2, "authority_reason": "杀重需制"},
            {"god": "偏财", "score": 0.4, "authority_reason": "财泄印"},
        ],
    }

    bundle = build_practitioner_choice_candidates(
        raw_physics={},
        god_ring_authority=authority,
        plugin_rows=[
            {
                "plugin_id": "classical.pattern.shishen_zhisha.v1",
                "pattern_candidate": "食神制杀",
                "pattern_confidence": 0.76,
                "target_god": "七杀",
                "claim_id": "claim-pattern",
            },
            {
                "plugin_id": "classical.pattern.yangren_jiasha.v1",
                "pattern_candidate": "阳刃驾杀",
                "pattern_confidence_percent": 68,
            },
        ],
    )

    assert bundle["contract"] == "v17.practitioner.choice_candidates.v1"
    assert bundle["selections"]["pattern"][0]["name"] == "食神制杀"
    assert bundle["selections"]["pattern"][0]["selected_by_system"] is True
    assert bundle["selections"]["pattern"][0]["confidence_percent"] == 76
    assert bundle["selections"]["use_god"][0]["name"] == "食神"
    assert bundle["selections"]["use_god"][0]["selected_by_system"] is True
    assert bundle["selections"]["taboo_god"][0]["name"] == "七杀"
    assert bundle["guardrails"][1] == "practitioner choices only override the current narrative reading"


def test_practitioner_override_context_builds_prompt_without_parameter_write() -> None:
    context = normalize_practitioner_override_context(
        {
            "selections": {
                "pattern": {"id": "pattern:食神制杀", "name": "食神制杀", "confidence": 0.76},
                "use_god": {"id": "use_god:食神", "name": "食神", "confidence": 0.82},
                "taboo_god": {"id": "taboo_god:七杀", "name": "七杀", "confidence": 0.82},
            }
        }
    )

    assert context["contract"] == "v17.practitioner.override_context.v1"
    assert context["has_override"] is True
    assert selected_override_gods(context) == (["食神"], ["七杀"])
    lines = practitioner_override_prompt_lines(context)
    assert "格局=食神制杀" in lines[0]
    assert "只影响本次断语" in lines[1]
