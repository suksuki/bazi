from app.core.rules.junction import build_l1_operator_audit_items_from_steps
from app.plugins.base.interactions.clash import run_clash
from app.plugins.base_physics.core_operators import op_connection, op_destruction, op_production


def test_op_destruction_scales_abs_loss():
    raw = run_clash(source_abs=10.0, target_abs=10.0, intensity=1.0)
    out = op_destruction.apply_eta(raw, 0.5)
    assert out["abs_loss"] == round(float(raw["abs_loss"]) * 0.5, 4)


def test_op_production_scales_abs_gain():
    raw = run_clash(source_abs=10.0, target_abs=10.0, intensity=1.0)
    out = op_production.apply_eta(raw, 2.0)
    assert out["abs_gain"] == round(float(raw["abs_gain"]) * 2.0, 4)


def test_op_connection_scales_abs_locked():
    from app.plugins.base.interactions.combine import run_combine

    raw = run_combine(source_abs=8.0, target_abs=6.0, lock_ratio=0.5)
    out = op_connection.apply_eta(raw, 0.25)
    assert out["abs_locked"] == round(float(raw["abs_locked"]) * 0.25, 4)


def test_build_l1_operator_audit_items_from_steps_emits_rows():
    steps = [
        {
            "plugin": "base.clash",
            "edge": ["year", "month"],
            "delta": {"abs_loss": 0.1, "abs_gain": 0.02},
            "l1_operator_ids": ["L1_OP_DEST", "L1_OP_PROD"],
        }
    ]
    rows = build_l1_operator_audit_items_from_steps(steps, timestamp="2026-04-11T00:00:00Z")
    assert len(rows) == 2
    assert rows[0]["payload"]["l1_operator_id"] == "L1_OP_DEST"
    assert rows[0]["payload"]["skill_id"] == "l1_dest_01"
    assert rows[1]["payload"]["l1_operator_id"] == "L1_OP_PROD"
    assert rows[1]["payload"]["skill_id"] == "l1_prod_01"
