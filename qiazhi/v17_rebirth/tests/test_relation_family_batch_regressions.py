from __future__ import annotations

from typing import Any, Dict, List

from v17_rebirth.backend.logic.plugin_discovery import collect_all_spec_facts


def _tensor_from_base(*, relation_payload: Dict[str, Any], base_scores: Dict[str, float], origin_type: str) -> Dict[str, Any]:
    iv2 = {
        "liu_chong": [],
        "liu_hai": [],
        "liu_po": [],
        "liu_he": [],
        "san_he": [],
        "ban_he": [],
        "sanxing": [],
    }
    iv2.update(relation_payload)

    return {
        "four_pillars": {"year": "甲子", "month": "乙卯", "day": "丙寅", "hour": "丁酉"},
        "luck_pillar": "戊辰",
        "flow_pillar": "己巳",
        "ten_gods_absolute": dict(base_scores),
        "ten_gods_base_l0": dict(base_scores),
        "ten_gods_runtime": dict(base_scores),
        "meta": {
            "interaction_v2": iv2,
            "stem_fusion_v1": {"cases": []},
        },
    }


def _top_fact_for_plugin(tensor: Dict[str, Any], plugin_id: str):
    facts = collect_all_spec_facts(tensor)
    candidate = [f for f in facts if str(f.plugin_id or "") == plugin_id]
    assert candidate, f"expected plugin fact: {plugin_id}"
    return max(
        candidate,
        key=lambda item: float(item.meta.get("match_ratio", 0.0) or 0.0),
    )


def _assert_static_layer_protocol(fact) -> None:
    assert isinstance(fact.meta, dict)
    assert "static_basis" in fact.meta
    assert isinstance(fact.meta["static_basis"], dict)
    assert fact.meta["static_basis"].get("relation_family") == fact.meta.get("relation_family") or fact.meta.get("relation_family") is None
    assert float(fact.meta.get("match_ratio", 0.0) or 0.0) > 0.0


def _relation_tensor(
    family: str,
    pair: List[str],
    *,
    origin_type: str,
    pillars: List[str],
) -> Dict[str, Any]:
    payload = {family: [{"pair": pair, "origin_type": origin_type, "pillars": pillars}]}
    if family in {"san_he"}:
        payload["san_he"][0]["group"] = pair
    return payload


def test_relation_layer_protocol_weights_follow_origin_priority() -> None:
    base_scores = {"正官": 22.0, "七杀": 14.0, "食神": 18.0, "偏财": 12.0}
    relation_matrix = {
        "liuhe": {
            "plugin": "l1.physics.op_branch_liuhe",
            "payload": {"liu_he": [{"pair": ["子", "丑"], "pillars": ["year", "month"], "origin_type": "natal"}]},
        },
        "liuhai": {
            "plugin": "l1.physics.op_branch_liuhai",
            "payload": {"liu_hai": [{"pair": ["子", "未"], "pillars": ["year", "month"], "origin_type": "natal"}]},
        },
        "liupo": {
            "plugin": "l1.physics.op_branch_liupo",
            "payload": {"liu_po": [{"pair": ["子", "酉"], "pillars": ["year", "month"], "origin_type": "natal"}]},
        },
    }

    for family, info in relation_matrix.items():
        base_payload = info["payload"]
        plugin_id = info["plugin"]
        natal = _tensor_from_base(
            relation_payload=base_payload,
            base_scores=base_scores,
            origin_type="natal",
        )

        if family == "liuhe":
            luck_payload = {"liu_he": [{"pair": ["子", "丑"], "pillars": ["year", "luck"], "origin_type": "luck_background"}]}
            flow_payload = {"liu_he": [{"pair": ["子", "丑"], "pillars": ["year", "flow"], "origin_type": "flow_trigger"}]}
        elif family == "liuhai":
            luck_payload = {"liu_hai": [{"pair": ["子", "未"], "pillars": ["year", "luck"], "origin_type": "luck_background"}]}
            flow_payload = {"liu_hai": [{"pair": ["子", "未"], "pillars": ["year", "flow"], "origin_type": "flow_trigger"}]}
        else:
            luck_payload = {"liu_po": [{"pair": ["子", "酉"], "pillars": ["year", "luck"], "origin_type": "luck_background"}]}
            flow_payload = {"liu_po": [{"pair": ["子", "酉"], "pillars": ["year", "flow"], "origin_type": "flow_trigger"}]}

        luck = _tensor_from_base(
            relation_payload=luck_payload,
            base_scores=base_scores,
            origin_type="luck_background",
        )
        flow = _tensor_from_base(
            relation_payload=flow_payload,
            base_scores=base_scores,
            origin_type="flow_trigger",
        )

        natal_fact = _top_fact_for_plugin(natal, plugin_id)
        luck_fact = _top_fact_for_plugin(luck, plugin_id)
        flow_fact = _top_fact_for_plugin(flow, plugin_id)

        assert float(natal_fact.meta.get("match_ratio", 0.0) or 0.0) > float(luck_fact.meta.get("match_ratio", 0.0) or 0.0)
        assert float(luck_fact.meta.get("match_ratio", 0.0) or 0.0) > float(flow_fact.meta.get("match_ratio", 0.0) or 0.0)
        assert natal_fact.meta.get("origin_type") == "natal"
        assert luck_fact.meta.get("origin_type") == "luck_background"
        assert flow_fact.meta.get("origin_type") == "flow_trigger"
        _assert_static_layer_protocol(natal_fact)


def test_stem_fusion_transformed_is_stronger_than_stuck() -> None:
    base_scores = {"正官": 24.0, "七杀": 16.0, "比肩": 18.0, "食神": 10.0}
    stuck_pt = {
        "four_pillars": {"year": "辛酉", "month": "乙酉", "day": "乙丑", "hour": "庚申"},
        "luck_pillar": "庚辰",
        "flow_pillar": "辛巳",
        "ten_gods_absolute": dict(base_scores),
        "ten_gods_base_l0": dict(base_scores),
        "ten_gods_runtime": dict(base_scores),
        "meta": {
            "interaction_v2": {
                "liu_chong": [],
                "liu_hai": [],
                "liu_po": [],
                "liu_he": [],
                "san_he": [],
                "ban_he": [],
                "sanxing": [],
            },
            "stem_fusion_v1": {
                "cases": [
                    {
                        "pillars": ["month", "luck"],
                        "stems": ["乙", "庚"],
                        "mode": "stuck",
                        "hua_element": "metal",
                        "month_stem_supports": False,
                        "branch_hua_ratio": 0.16,
                    }
                ],
            },
        },
    }
    formed_pt = {
        **stuck_pt,
        "meta": {
            **stuck_pt["meta"],
            "stem_fusion_v1": {
                "cases": [
                    {
                        "pillars": ["month", "luck"],
                        "stems": ["乙", "庚"],
                        "mode": "transformed",
                        "hua_element": "metal",
                        "month_stem_supports": True,
                        "branch_hua_ratio": 0.70,
                    }
                ],
            },
        },
    }

    stuck_fact = _top_fact_for_plugin(stuck_pt, "l1.physics.op_stem_fusion")
    formed_fact = _top_fact_for_plugin(formed_pt, "l1.physics.op_stem_fusion")

    assert float(formed_fact.meta.get("match_ratio", 0.0) or 0.0) > float(stuck_fact.meta.get("match_ratio", 0.0) or 0.0)
    assert formed_fact.meta.get("condition_state") == "formed"
    assert formed_fact.meta.get("condition_trigger") == "month_support"
    assert stuck_fact.meta.get("condition_state") == "stuck"
    assert "static_basis" in formed_fact.meta


def test_sanhe_support_and_blocked_modes_have_expected_protocol_fields() -> None:
    base_scores = {"比肩": 30.0, "正官": 18.0, "七杀": 11.0, "食神": 14.0}
    base_tensor = {
        "four_pillars": {"year": "丁巳", "month": "乙巳", "day": "乙丑", "hour": "乙酉"},
        "luck_pillar": "庚子",
        "flow_pillar": "丙午",
        "ten_gods_absolute": dict(base_scores),
        "ten_gods_base_l0": dict(base_scores),
        "ten_gods_runtime": dict(base_scores),
        "meta": {
            "interaction_v2": {
                "liu_chong": [],
                "liu_hai": [],
                "liu_po": [],
                "liu_he": [],
                "san_he": [
                    {
                        "group": ["巳", "酉", "丑"],
                        "matched_branches": ["巳", "酉", "丑"],
                        "stress": 1.0,
                        "pillars": ["year", "month", "hour"],
                        "origin_type": "natal",
                        "pivot_factor": 1.0,
                    }
                ],
                "ban_he": [],
                "sanxing": [],
            },
            "stem_fusion_v1": {"cases": []},
        },
    }
    contest_tensor = {
        **base_tensor,
        "meta": {
            **base_tensor["meta"],
            "interaction_v2": {
                **base_tensor["meta"]["interaction_v2"],
                "liu_chong": [{"pair": ["酉", "丑"], "pillars": ["month", "luck"], "origin_type": "luck_background"}],
            },
        },
    }

    supported_fact = _top_fact_for_plugin(base_tensor, "l1.physics.op_branch_sanhe")
    contested_fact = _top_fact_for_plugin(contest_tensor, "l1.physics.op_branch_sanhe")

    assert supported_fact.meta.get("condition_state") == "supported"
    assert contested_fact.meta.get("condition_state") in {"contested", "supported"}
    assert supported_fact.meta.get("manifestation_state") in {"manifested", "supported"}
    assert contested_fact.meta.get("manifestation_state") in {"manifested", "supported"}
    assert supported_fact.meta.get("interaction_layer") == "branch"
    assert contested_fact.meta.get("interaction_layer") == "branch"
    assert float(supported_fact.meta.get("match_ratio", 0.0) or 0.0) >= float(contested_fact.meta.get("match_ratio", 0.0) or 0.0)
    assert "projection_share" in supported_fact.meta
    assert 0.0 < float(supported_fact.meta.get("projection_share") or 0.0) <= 1.0
    assert isinstance(supported_fact.meta.get("cluster_projection"), dict)
    assert len(supported_fact.meta.get("cluster_projection") or {}) >= 1
    assert supported_fact.meta.get("static_basis", {}).get("relation_family") == "sanhe"
    assert contested_fact.meta.get("static_basis", {}).get("relation_family") == "sanhe"
    _assert_static_layer_protocol(supported_fact)
