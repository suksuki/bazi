from __future__ import annotations

from v17_rebirth.backend.logic.L2_structure_patterns.climate_theme import (
    ClimateAxisPlugin,
    ClimatePatternSurvivalPlugin,
    ClimateSummaryPlugin,
    ClimateTenGodFitPlugin,
)
from v17_rebirth.backend.logic.L2_structure_patterns.climate_theme_core import (
    build_climate_theme_contract,
    normalize_climate_theme_meta,
    resolve_climate_theme,
)


def _tensor() -> dict:
    return {
        "energy_meta": {
            "climate_field": {
                "state": "偏暖",
                "thermal_index": 0.42,
                "moisture_index": -0.18,
                "climate_tension": 0.31,
                "source_by_scope": {
                    "month": {"thermal": 0.62, "moisture": -0.22},
                    "luck": {"thermal": -0.18, "moisture": 0.16},
                    "flow": {"thermal": 0.11, "moisture": -0.07},
                },
            },
            "climate_modifier_layer": {
                "contract": "v17.climate_modifier_layer.v1",
                "ten_god_efficiency": {"食神": 0.14, "伤官": 0.11, "正印": -0.12},
                "ten_god_stability": {"食神": 0.08, "正财": 0.05, "正印": -0.09},
                "yongshen_priority_delta": {"食神": 0.16, "正财": 0.12, "正印": -0.18},
                "pattern_survival_delta": {"食伤财": 0.22, "印官": -0.14},
            },
        }
    }


def test_climate_theme_contract_declares_optional_topic() -> None:
    contract = build_climate_theme_contract()
    assert contract["contract"] == "v17.climate.theme.v1"
    assert contract["is_optional_topic"] is True
    assert contract["authority_bridge_mode"] == "narrative_only"


def test_resolve_climate_theme_builds_summary() -> None:
    analysis = resolve_climate_theme(_tensor())
    theme = analysis["climate_theme"]
    assert theme["contract"] == "v17.climate.theme.v1"
    assert theme["state"] == "偏暖"
    assert "食神" in theme["favored_gods"]
    assert "正印" in theme["strained_gods"]
    assert theme["pattern_survival"][0]["label"] in {"食伤财链", "印官共振"}
    assert theme["prompt_digest"]


def test_normalize_climate_theme_meta_accepts_plain_dict() -> None:
    theme = normalize_climate_theme_meta(
        {
            "state": "寒湿",
            "origin_type": "flow_trigger",
            "favored_gods": ["正印"],
            "strained_gods": ["伤官"],
            "prompt_digest": "寒湿，印星顺势，食伤承压",
        }
    )
    assert theme["contract"] == "v17.climate.theme.v1"
    assert theme["state"] == "寒湿"
    assert theme["origin_type"] == "flow_trigger"
    assert theme["favored_gods"] == ["正印"]


def test_climate_theme_plugins_emit_topic_facts() -> None:
    tensor = _tensor()
    plugins = [
        ClimateAxisPlugin(),
        ClimateTenGodFitPlugin(),
        ClimatePatternSurvivalPlugin(),
        ClimateSummaryPlugin(),
    ]
    for plugin in plugins:
        facts = plugin.collect_v17_facts(tensor)
        assert facts, plugin.plugin_id
        meta = facts[0].meta
        assert meta["source_event"] == "climate_theme"
        assert meta["claim_type"] == "pattern_observation"
        assert meta["climate_theme"]["contract"] == "v17.climate.theme.v1"
