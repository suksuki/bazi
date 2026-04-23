from __future__ import annotations

from v17_rebirth.backend.logic.L2_structure_patterns.blind_school_core import (
    BlindBodyCandidate,
    BlindThemeResult,
    build_blind_bias_protocol,
    build_blind_theme_contract,
    normalize_blind_theme_meta,
    resolve_blind_theme,
)


def test_blind_theme_contract_declares_optional_independent_topic() -> None:
    contract = build_blind_theme_contract()
    assert contract["contract"] == "v17.blind.theme.v1"
    assert contract["is_optional_topic"] is True
    assert "ziping" in contract["coexists_with"]
    assert "final_meta_keys" in contract
    assert "temporary_meta_keys" in contract


def test_blind_theme_result_exports_final_meta_only() -> None:
    result = BlindThemeResult(
        primary_route="食伤制杀",
        body_mode="disturbed_body",
        body_candidates=(
            BlindBodyCandidate(
                route_id="shishang_zhisha",
                label="食伤制杀",
                score=0.82,
                status="primary",
                relation_families=("san_he", "ke"),
                notes=("火制金",),
            ),
        ),
        use_candidates=("食伤", "七杀"),
        taboo_candidates=("强印",),
        house_roles={"食伤": "outside", "七杀": "inside", "偏财": "inside"},
        runtime_switches=("己亥运中食伤生财抢权",),
        narrative_focus=("先看做功，再看断事",),
    )
    meta = result.to_meta()
    assert meta["contract"] == "v17.blind.theme.v1"
    assert meta["primary_route"] == "食伤制杀"
    assert meta["body_mode"] == "disturbed_body"
    assert meta["use_candidates"] == ["食伤", "七杀"]
    assert meta["taboo_candidates"] == ["强印"]
    assert meta["house_roles"]["食伤"] == "outside"
    assert "prompt_digest" in meta


def test_normalize_blind_theme_meta_accepts_plain_dict() -> None:
    meta = normalize_blind_theme_meta(
        {
            "primary_route": "食伤生财",
            "body_mode": "shifted_body",
            "use_candidates": ["偏财"],
            "taboo_candidates": ["强印"],
            "house_roles": {"偏财": "inside", "食伤": "outside"},
            "runtime_switches": ["己亥运中生财抢权"],
        }
    )
    assert meta["contract"] == "v17.blind.theme.v1"
    assert meta["primary_route"] == "食伤生财"
    assert meta["body_mode"] == "shifted_body"
    assert meta["house_roles"]["偏财"] == "inside"


def test_build_blind_bias_protocol_expands_cluster_labels_and_keeps_bias_only() -> None:
    protocol = build_blind_bias_protocol(
        {
            "primary_route": "食伤生财",
            "body_mode": "disturbed_body",
            "confidence": 0.82,
            "use_candidates": ["食伤", "财"],
            "taboo_candidates": ["强印", "正官"],
            "house_roles": {"食伤": "outside", "正财": "inside", "偏财": "inside", "偏印": "bridge"},
            "runtime_switches": ["己亥运中食伤生财抢权"],
            "authority_bridge_mode": "bias_only",
        }
    )
    assert protocol["contract"] == "v17.blind.bias.v1"
    assert protocol["authority_bridge_mode"] == "bias_only"
    assert protocol["use_bias"]["食神"] > 0.0
    assert protocol["use_bias"]["伤官"] > 0.0
    assert protocol["use_bias"]["正财"] > 0.0
    assert protocol["taboo_bias"]["正印"] > 0.0
    assert protocol["taboo_bias"]["偏印"] > 0.0
    assert protocol["taboo_bias"]["正官"] > 0.0
    assert protocol["summary"]["switch_count"] == 1


def test_resolve_blind_theme_builds_shared_route_and_roles() -> None:
    analysis = resolve_blind_theme(
        {
            "four_pillars": {"year": "丁巳", "month": "乙巳", "day": "乙丑", "hour": "乙酉"},
            "ten_gods_runtime": {"伤官": 90.0, "食神": 70.0, "正官": 18.0, "七杀": 11.0, "偏财": 16.0},
            "ten_gods_base_l0": {"伤官": 90.0, "食神": 70.0, "正官": 18.0, "七杀": 11.0, "偏财": 16.0},
            "meta": {
                "interaction_v2": {
                    "san_he": [{"group": ["巳", "酉", "丑"], "origin_type": "natal"}],
                    "liu_chong": [],
                }
            },
        }
    )
    theme = analysis["blind_theme"]
    assert theme["contract"] == "v17.blind.theme.v1"
    assert theme["primary_route"] in {"食伤制杀", "食伤生财"}
    assert theme["use_candidates"]
    assert theme["house_roles"]
    assert analysis["target_god"] in theme["use_candidates"]
