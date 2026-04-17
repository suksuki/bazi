from app.services.helpers.tensor_adapters import ensure_abs_nodes_on_physics_tensor, mirror_abs_nodes_from_deity_axes


def test_mirror_abs_nodes_from_axes_simple():
    tensor = {
        "deity_energy_axes": {
            "比肩": {"absolute_energy": 1.5},
            "正财": {"absolute_energy": 2.0},
        },
    }
    out = mirror_abs_nodes_from_deity_axes(tensor)
    assert out["比肩"] == 1.5
    assert out["正财"] == 2.0


def test_ensure_abs_nodes_idempotent():
    tensor = {
        "abs_nodes": {"比肩": 9.0},
        "deity_energy_axes": {"比肩": {"absolute_energy": 1.0}},
    }
    ensure_abs_nodes_on_physics_tensor(tensor)
    assert tensor["abs_nodes"]["比肩"] == 9.0
