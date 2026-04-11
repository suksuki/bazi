from app.plugins.base_physics.core_operators.op_geography import apply_op_geography


def test_op_geography_boosts_fire_for_south() -> None:
    tensor = {
        "vector": {"wood": 1.0, "fire": 2.0, "earth": 1.0, "metal": 1.0, "water": 1.0},
        "normalized": {"wood": 0.2, "fire": 0.2, "earth": 0.2, "metal": 0.2, "water": 0.2},
        "deity_energy_axes": {
            "食神": {"absolute_energy": 10.0, "relative_percentage": 10.0},
        },
        "deity_trace_details": {
            "食神": {
                "base_energy": {
                    "contribution_sources": [
                        {"source": "year.stem:丙", "contribution_energy": 10.0},
                    ]
                }
            }
        },
        "meta": {},
    }
    steps = apply_op_geography(
        physics_tensor=tensor,
        physics_config={"user_target_direction": "南"},
        settings={"L1_OP_GEOGRAPHY_ENABLE": 1.0, "GEOG_DIRECTION_ABS_BOOST": 0.15},
    )
    assert steps
    assert abs(float(tensor["vector"]["fire"]) - 2.3) < 1e-6
    assert tensor["meta"]["geography_field_patch_v1"]["element"] == "fire"


def test_op_geography_noop_when_direction_missing() -> None:
    tensor = {"vector": {"wood": 1.0, "fire": 2.0, "earth": 1.0, "metal": 1.0, "water": 1.0}, "meta": {}}
    steps = apply_op_geography(physics_tensor=tensor, physics_config={}, settings={"L1_OP_GEOGRAPHY_ENABLE": 1.0})
    assert steps == []


def test_op_geography_noop_for_east() -> None:
    tensor = {"vector": {"wood": 1.0, "fire": 2.0, "earth": 1.0, "metal": 1.0, "water": 1.0}, "meta": {}}
    steps = apply_op_geography(
        physics_tensor=tensor,
        physics_config={"user_target_direction": "东"},
        settings={"L1_OP_GEOGRAPHY_ENABLE": 1.0},
    )
    assert steps == []
    assert float(tensor["vector"]["wood"]) == 1.0
