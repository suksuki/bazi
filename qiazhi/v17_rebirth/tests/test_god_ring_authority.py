from __future__ import annotations

from v17_rebirth.backend.services.god_ring_authority import resolve_god_ring_authority


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
