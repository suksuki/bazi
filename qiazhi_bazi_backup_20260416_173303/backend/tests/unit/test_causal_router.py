from app.core.routing.causal_router import CausalRouter


def test_negotiate_weighted_sum_detects_polarity_flip() -> None:
    plugin_outputs = {
        "classical.blind_school.v1": {
            "payload": {
                "work_vectors": [
                    {"source_deity": "比肩", "expected_work": 2.0},
                    {"source_deity": "劫财", "expected_work": -0.5},
                ]
            }
        },
        "classical.wangshuai.v1": {
            "payload": {
                "self_abs": 12.0,
                "verdict": "能量过载，优先泄耗降压。",
                "wangshuai_axes": {},
            },
        },
    }
    cfg = {
        "conflict_strategy": "conservative",
        "school_sovereignty": False,
        "priority_base_physics": 100,
        "priority_blind_school": 80,
        "layer_L1": 100,
        "layer_L2": 80,
    }
    out = CausalRouter(routing_config=cfg).negotiate_impact(plugin_outputs, physics_tensor={})
    assert out["strategy_applied"] == "weighted_sum"
    assert isinstance(out["conflict_events"], list)
    assert out["routing_decision"]
    assert any(x.get("skill_id") == "mp_pierce_01" for x in out["skill_sovereignty_rank"])


def test_school_priority_prefers_blind_vector() -> None:
    plugin_outputs = {
        "classical.blind_school.v1": {
            "payload": {"work_vectors": [{"source_deity": "比肩", "expected_work": 1.0}]}
        },
        "classical.wangshuai.v1": {
            "payload": {"self_abs": 10.0, "verdict": "身弱偏虚，优先扶助。", "wangshuai_axes": {}}
        },
    }
    cfg = {"conflict_strategy": "school_priority", "school_sovereignty": False}
    out = CausalRouter(routing_config=cfg).negotiate_impact(plugin_outputs, physics_tensor={})
    assert out["strategy_applied"] == "school_priority"
    assert out["merged_impact"].get("比肩") == 1.0
