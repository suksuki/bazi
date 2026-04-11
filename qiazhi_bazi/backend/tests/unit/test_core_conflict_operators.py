from app.core.routing.causal_router import CausalRouter
from app.plugins.base_physics.core_operators.op_owl_food import apply_op_owl_food
from app.plugins.base_physics.core_operators.op_wealth_seal import apply_op_wealth_seal
from app.plugins.base_physics.skill_manifest_loader import reload_base_physics_skill_manifest_for_tests


def test_op_owl_food_dampens_shishen_when_pi_yin_present() -> None:
    tensor = {
        "deity_energy_axes": {
            "偏印": {"absolute_energy": 2.0, "relative_percentage": 20.0},
            "食神": {"absolute_energy": 4.0, "relative_percentage": 40.0},
        },
        "meta": {},
    }
    settings = {"L1_CORE_CONFLICT_OPS_ENABLE": 1.0, "L1_OWL_FOOD_DAMPING": 0.15}
    steps = apply_op_owl_food(physics_tensor=tensor, settings=settings)
    assert steps
    sh = tensor["deity_energy_axes"]["食神"]["absolute_energy"]
    assert abs(sh - 3.4) < 0.01


def test_op_wealth_seal_sets_routing_meta() -> None:
    tensor = {
        "deity_energy_axes": {
            "正财": {"absolute_energy": 3.0, "relative_percentage": 30.0},
            "正印": {"absolute_energy": 2.5, "relative_percentage": 25.0},
        },
        "meta": {},
    }
    metadata = {
        "pillars": {
            "year": {"stem": "甲", "branch": "子"},
            "month": {"stem": "丙", "branch": "寅"},
            "day": {"stem": "甲", "branch": "午"},
            "hour": {"stem": "壬", "branch": "申"},
        }
    }
    settings = {"L1_CORE_CONFLICT_OPS_ENABLE": 1.0, "L1_WEALTH_SEAL_COLLAPSE": 0.2}
    steps = apply_op_wealth_seal(physics_tensor=tensor, metadata=metadata, settings=settings)
    assert isinstance(tensor["meta"], dict)
    assert tensor["meta"].get("wealth_seal_routing")
    assert steps


def test_causal_router_appends_l1_polarity_seeds() -> None:
    reload_base_physics_skill_manifest_for_tests()
    pt = {
        "meta": {
            "l1_polarity_routing_seeds": [
                {
                    "pattern": "TEST",
                    "deity": "食神",
                    "plugin_a": "L1_OP_OWL_FOOD",
                    "plugin_b": "base.physics",
                    "delta_a": 0.2,
                    "delta_b": -0.2,
                }
            ]
        }
    }
    out = CausalRouter(
        routing_config={"conflict_strategy": "conservative", "school_sovereignty": False},
    ).negotiate_impact({}, physics_tensor=pt)
    ev = out["conflict_events"]
    assert any(e.get("deity") == "食神" and e.get("note") == "Polarity_Flip" for e in ev)
