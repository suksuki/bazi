from __future__ import annotations

from v17_rebirth.backend.services.authority_layer_protocol import (
    build_authority_layer_protocol,
    clamp_soft_bias_map,
    preserve_hard_top,
)


def test_build_authority_layer_protocol_exports_levels_and_sources() -> None:
    protocol = build_authority_layer_protocol(
        hard_constraint_source=["classical.ziping.god_ring_resolver.v1", "stage_bias_protocol"],
        structure_enhancement_source=["classical.pattern.officer.v1", "climate_modifier_layer"],
        soft_bias_source=["blind_theme"],
        max_bias_ratio=0.35,
        override_forbidden=True,
    )

    assert protocol["contract"] == "v17.authority.layer_protocol.v1"
    assert protocol["authority_level"] == 1
    assert protocol["override_forbidden"] is True
    assert protocol["max_bias_ratio"] == 0.35
    assert protocol["summary"]["hard_constraint_count"] == 2
    assert protocol["summary"]["structure_enhancement_count"] == 2
    assert protocol["summary"]["soft_bias_count"] == 1


def test_clamp_soft_bias_map_respects_max_bias_ratio() -> None:
    clamped = clamp_soft_bias_map(
        hard_scores={"正官": 0.8, "食神": 0.2},
        bias_map={"正官": 0.6, "食神": 0.2},
        max_bias_ratio=0.25,
        soft_bias_floor=0.03,
    )

    assert clamped["正官"] == 0.2
    assert clamped["食神"] == 0.05


def test_preserve_hard_top_prevents_soft_bias_overturn() -> None:
    ranked = preserve_hard_top(
        hard_scores={"正官": 0.92, "食神": 0.54},
        ranked_gods=["食神", "正官"],
        override_forbidden=True,
    )

    assert ranked[0] == "正官"
