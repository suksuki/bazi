"""V6.x 全知推荐：插件/补丁/L1 结构、缓存与理由合成。"""
from __future__ import annotations

from typing import Any, Dict

from app.logic.reasoning_synthesizer import synthesize_recommendation_reason
from app.services.recommendation_service import (
    _recommendation_cache_key,
    get_top_recommendations,
    synthesize_manifest_trace_reason,
)


def test_get_top_recommendations_prefers_follower_patch_on_pingchang():
    """常规格（比劫偏重、财弱）：内置从财倾向补丁应高于「仅开关插件」的纯 dry-run 分差。"""
    deity = {
        "比肩": 0.34,
        "劫财": 0.32,
        "食神": 0.05,
        "伤官": 0.05,
        "偏财": 0.05,
        "正财": 0.05,
        "七杀": 0.04,
        "正官": 0.04,
        "偏印": 0.03,
        "正印": 0.03,
    }
    pt: Dict[str, Any] = {
        "deity_scores": dict(deity),
        "meta": {"global_entropy": 0.58},
        "audit_log": {},
    }
    md: Dict[str, Any] = {"conflict_matrix": {"points": []}}
    out = get_top_recommendations(
        physics_tensor=pt,
        metadata=md,
        blind_school_features={},
        enabled_plugins=["classical.blind_school.v1"],
        inbox_cards=[],
        top_n=5,
    )
    assert out["candidates_evaluated"] >= 1
    ranked = [x["candidate_id"] for x in out["top"]]
    assert ranked[0] == "patch:follower_wealth_bias"
    first = out["top"][0]
    assert float(first["total_score"]) >= 0.0
    assert "裁决者" in str(first.get("filled_reason") or "")


def test_get_top_recommendations_sanhe_style_energy_patch_scores_and_matches():
    """意志能量补丁（energy-patch）：大抬食伤、压比劫 → 高分并绑定星火卡片 id。"""
    deity = {
        "比肩": 0.3,
        "劫财": 0.28,
        "食神": 0.06,
        "伤官": 0.06,
        "偏财": 0.08,
        "正财": 0.08,
        "七杀": 0.05,
        "正官": 0.05,
        "偏印": 0.02,
        "正印": 0.02,
    }
    pt: Dict[str, Any] = {
        "deity_scores": dict(deity),
        "meta": {"global_entropy": 0.55},
        "audit_log": {},
    }
    md: Dict[str, Any] = {"conflict_matrix": {"points": []}}
    card_id = "inbox-sanhe-test-丑巳酉"
    inbox_cards = [
        {
            "id": card_id,
            "title": "地支三合局锁定",
            "cardType": "energy-patch",
            "proposal": {
                "adjustment_type": "ENERGY_PATCH",
                "energy_deltas": {"食神": 0.14, "伤官": 0.14, "比肩": -0.1, "劫财": -0.1},
            },
        }
    ]
    out = get_top_recommendations(
        physics_tensor=pt,
        metadata=md,
        blind_school_features={},
        enabled_plugins=["classical.blind_school.v1"],
        inbox_cards=inbox_cards,
        top_n=5,
    )
    top_ids = [x["candidate_id"] for x in out["top"]]
    assert f"card:{card_id}" in top_ids
    card_row = next(x for x in out["top"] if x["candidate_id"] == f"card:{card_id}")
    assert float(card_row["total_score"]) > 0.015
    assert card_id in (card_row.get("matched_card_ids") or [])


def test_get_top_recommendations_l1_structure_sanhe_card_matches():
    """真实 L1 三合结构卡：结构覆盖 + 评分 + matched_card_ids（星火勋章绑定）。"""
    deity = {
        "比肩": 0.32,
        "劫财": 0.3,
        "食神": 0.06,
        "伤官": 0.06,
        "偏财": 0.08,
        "正财": 0.08,
        "七杀": 0.05,
        "正官": 0.05,
        "偏印": 0.03,
        "正印": 0.03,
    }
    card_id = "inbox-sanhe-丑巳酉"
    pt: Dict[str, Any] = {
        "deity_scores": dict(deity),
        "meta": {"global_entropy": 0.56, "pattern_profile": {"pattern_name_zh": "常规格"}},
        "plugin_outputs": {
            "sys.core.physics": {
                "payload": {
                    "sanhe_clusters": [
                        {"branches": ["巳", "酉", "丑"], "energy_vault_status": "AGGREGATED"},
                    ]
                }
            }
        },
    }
    md: Dict[str, Any] = {"conflict_matrix": {"points": []}}
    inbox_cards = [
        {
            "id": card_id,
            "title": "地支三合局锁定",
            "cardType": "L1_STRUCTURE",
            "displayText": "巳酉丑金局 · AGGREGATED",
        }
    ]
    out = get_top_recommendations(
        physics_tensor=pt,
        metadata=md,
        blind_school_features={},
        enabled_plugins=["classical.blind_school.v1"],
        inbox_cards=inbox_cards,
        top_n=8,
    )
    cand_ids = [x["candidate_id"] for x in out["top"]]
    assert f"l1struct:{card_id}" in cand_ids
    row = next(x for x in out["top"] if x["candidate_id"] == f"l1struct:{card_id}")
    assert float(row["total_score"]) > 0.005
    assert card_id in (row.get("matched_card_ids") or [])
    fr = str(row.get("filled_reason") or "")
    assert "裁决者" in fr
    assert "地支三合" in fr or "合局" in fr or "结构" in fr


def test_get_top_recommendations_cache_hit_same_state():
    pt: Dict[str, Any] = {
        "deity_scores": {"比肩": 0.2, "劫财": 0.2, "食神": 0.1, "伤官": 0.1, "偏财": 0.1, "正财": 0.1, "七杀": 0.05, "正官": 0.05, "偏印": 0.05, "正印": 0.05},
        "meta": {"global_entropy": 0.4},
    }
    md: Dict[str, Any] = {"conflict_matrix": {"points": []}}
    kwargs = dict(
        physics_tensor=pt,
        metadata=md,
        blind_school_features={},
        enabled_plugins=[],
        inbox_cards=[],
        top_n=3,
    )
    a = get_top_recommendations(**kwargs)
    b = get_top_recommendations(**kwargs)
    assert a.get("cache_key") == b.get("cache_key")
    assert [x["candidate_id"] for x in a["top"]] == [x["candidate_id"] for x in b["top"]]


def test_synthesize_recommendation_reason_includes_arbiter_phrase():
    sb: Dict[str, Any] = {
        "deity_scores": {"比肩": 0.25, "劫财": 0.25, "食神": 0.1, "伤官": 0.1, "偏财": 0.1, "正财": 0.1, "七杀": 0.05, "正官": 0.05, "偏印": 0.05, "正印": 0.05},
        "meta": {},
    }
    sa = dict(sb)
    sa["deity_scores"] = dict(sb["deity_scores"])
    sa["deity_scores"]["食神"] = 0.2
    sa["deity_scores"]["伤官"] = 0.18
    score_detail = {
        "raw": {"follower_name_before": "常规格", "follower_name_after": "从儿格"},
        "components": {"pattern_boost": 0.5, "stability_gain": 0.4},
        "weights": {"pattern": 0.4, "stability": 0.3},
    }
    line = synthesize_recommendation_reason(
        action_phrase="通过「测试」修补食伤断裂点",
        score_detail=score_detail,
        tensor_before=sb,
        tensor_after=sa,
    )
    assert "裁决者" in line
    assert "常规格" in line or "从儿" in line


def test_synthesize_manifest_trace_reason_when_exclusion_cleared() -> None:
    """manifest 行：由 exclusion_hit → false 时应合成压制忌神、避开坍塌的旁白。"""
    before = {
        "meta": {
            "pattern_thresholds": [
                {
                    "pattern_id": "FOLLOW_CHILD",
                    "name": "从儿格",
                    "exclusion_hit": True,
                    "stability": 0.35,
                    "trace_display_zh": ["[拦截] 印星 权重 0.08 > 阈值 0.03"],
                }
            ]
        }
    }
    after = {
        "meta": {
            "pattern_thresholds": [
                {
                    "pattern_id": "FOLLOW_CHILD",
                    "name": "从儿格",
                    "exclusion_hit": False,
                    "stability": 0.62,
                    "trace_logic": ["base:primary=0.6000_min=0.5200_affinity=0.9200"],
                }
            ]
        }
    }
    voice = synthesize_manifest_trace_reason(before, after)
    assert "裁决者" in voice
    assert "从儿格" in voice
    assert "逻辑坍塌" in voice


def test_recommendation_cache_key_includes_manifest_fingerprint(tmp_path, monkeypatch) -> None:
    """法典文件 mtime/size 变化后缓存键应变，避免 Decision Inbox 命中旧 manifest 语义。"""
    mf = tmp_path / "pattern_manifest.json"
    mf.write_text('{"ENGINE":{}}', encoding="utf-8")
    monkeypatch.setenv("QIAZHI_PATTERN_MANIFEST_PATH", str(mf))
    pt: Dict[str, Any] = {"deity_scores": {}, "meta": {}}
    k1 = _recommendation_cache_key(
        physics_tensor=pt,
        metadata={},
        blind_school_features={},
        enabled_plugins=[],
        inbox_cards=[],
        top_n=3,
    )
    mf.write_text('{"ENGINE":{"x":1}}', encoding="utf-8")
    k2 = _recommendation_cache_key(
        physics_tensor=pt,
        metadata={},
        blind_school_features={},
        enabled_plugins=[],
        inbox_cards=[],
        top_n=3,
    )
    assert k1 != k2
