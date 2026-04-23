from __future__ import annotations

from v17_rebirth.backend.logic.L2_structure_patterns.xiangfa_theme import (
    XiangfaEvidencePlugin,
    XiangfaEventFramingPlugin,
    XiangfaNarrativeHintPlugin,
    XiangfaSemanticMappingPlugin,
)
from v17_rebirth.backend.logic.L2_structure_patterns.xiangfa_theme_core import (
    build_xiangfa_theme_contract,
    normalize_xiangfa_theme_meta,
    resolve_xiangfa_theme,
)


def _tensor() -> dict:
    return {
        "meta": {
            "god_ring_authority": {
                "use_gods": ["食神", "正财"],
                "taboo_gods": ["正印"],
            },
            "blind_theme": {
                "contract": "v17.blind.theme.v1",
                "primary_route": "食伤制杀",
                "house_roles": {"食伤": "outside", "七杀": "inside"},
            },
            "climate_theme": {
                "contract": "v17.climate.theme.v1",
                "state": "偏暖",
                "favored_gods": ["食神", "正财"],
                "strained_gods": ["正印"],
                "prompt_digest": "偏暖，食神/正财顺势，正印承压",
            },
        },
        "energy_meta": {
            "relation_formation_summary": [
                {
                    "formation_label": "巳酉丑三合金局",
                    "formation_percent": 66.0,
                    "status": "受扰成局",
                }
            ],
            "relation_dynamics_summary": [
                {
                    "label": "子午六冲",
                    "energy_axis": "激发",
                }
            ],
        },
    }


def test_xiangfa_theme_contract_stays_semantic_only() -> None:
    contract = build_xiangfa_theme_contract()
    assert contract["contract"] == "v17.xiangfa.theme.v1"
    assert contract["is_optional_topic"] is True
    assert contract["authority_bridge_mode"] == "disabled"


def test_resolve_xiangfa_theme_builds_semantic_outputs() -> None:
    analysis = resolve_xiangfa_theme(_tensor())
    theme = analysis["xiangfa_theme"]
    assert theme["contract"] == "v17.xiangfa.theme.v1"
    assert theme["authority_bridge_mode"] == "disabled"
    assert theme["semantic_mapping"]
    assert theme["evidence"]
    assert theme["event_framing"]
    assert theme["prompt_digest"]


def test_normalize_xiangfa_theme_meta_accepts_plain_dict() -> None:
    theme = normalize_xiangfa_theme_meta(
        {
            "semantic_mapping": ["体用主轴偏向食伤 / 正财"],
            "evidence": ["体用裁决来源：食神 / 正印"],
            "narrative_hint": ["当前叙事不宜只讲吉凶"],
            "event_framing": ["机会伴随成本"],
            "prompt_digest": "体用主轴偏向食伤 / 正财；机会伴随成本",
            "source_topics": ["authority", "blind"],
        }
    )
    assert theme["contract"] == "v17.xiangfa.theme.v1"
    assert theme["authority_bridge_mode"] == "disabled"
    assert theme["semantic_mapping"] == ["体用主轴偏向食伤 / 正财"]


def test_xiangfa_theme_plugins_emit_topic_facts() -> None:
    tensor = _tensor()
    plugins = [
        XiangfaSemanticMappingPlugin(),
        XiangfaEvidencePlugin(),
        XiangfaNarrativeHintPlugin(),
        XiangfaEventFramingPlugin(),
    ]
    for plugin in plugins:
        facts = plugin.collect_v17_facts(tensor)
        assert facts, plugin.plugin_id
        meta = facts[0].meta
        assert meta["source_event"] == "xiangfa_theme"
        assert meta["claim_type"] == "pattern_observation"
        assert meta["xiangfa_theme"]["contract"] == "v17.xiangfa.theme.v1"
