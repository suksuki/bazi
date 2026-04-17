from app.plugins.base_physics.core_operators.op_status import apply_l1_status_to_physics_tensor


def test_op_status_scales_axes_and_emits_step():
    metadata = {
        "pillars": {
            "year": {"stem": "丁", "branch": "巳"},
            "month": {"stem": "乙", "branch": "巳"},
            "day": {"stem": "乙", "branch": "酉"},
            "hour": {"stem": "辛", "branch": "丑"},
        }
    }
    axes = {
        "比肩": {"absolute_energy": 10.0, "relative_percentage": 25.0},
        "劫财": {"absolute_energy": 2.0, "relative_percentage": 5.0},
        "正印": {"absolute_energy": 2.0, "relative_percentage": 5.0},
        "偏印": {"absolute_energy": 2.0, "relative_percentage": 5.0},
        "食神": {"absolute_energy": 2.0, "relative_percentage": 5.0},
        "伤官": {"absolute_energy": 2.0, "relative_percentage": 5.0},
        "正财": {"absolute_energy": 2.0, "relative_percentage": 5.0},
        "偏财": {"absolute_energy": 2.0, "relative_percentage": 5.0},
        "正官": {"absolute_energy": 2.0, "relative_percentage": 5.0},
        "七杀": {"absolute_energy": 2.0, "relative_percentage": 5.0},
    }
    tensor = {"deity_energy_axes": axes}
    settings = {
        "L1_STATUS_OP_ENABLE": 1.0,
        "STATUS_BOOST_MULTIPLIER": 1.15,
        "STATUS_DRAIN_MULTIPLIER": 0.85,
    }
    steps = apply_l1_status_to_physics_tensor(physics_tensor=tensor, metadata=metadata, settings=settings)
    assert len(steps) == 1
    assert steps[0]["skill_ids"] == ["l1_status_01"]
    assert float(axes["比肩"]["absolute_energy"]) != 10.0
    assert (tensor.get("meta") or {}).get("l1_status_v1", {}).get("applied") is True
    pct = float(axes["比肩"]["relative_percentage"])
    assert 0.0 <= pct <= 100.0
