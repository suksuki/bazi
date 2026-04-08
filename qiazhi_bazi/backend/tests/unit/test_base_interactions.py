from app.plugins.base.interactions.clash import run_clash
from app.plugins.base.interactions.combine import run_combine
from app.plugins.base.interactions.pierce import run_pierce


def test_base_clash_outputs_physical_delta_only():
    out = run_clash(source_abs=10, target_abs=8, intensity=1.0)
    assert out["effect"] == "clash"
    assert out["vector"] == "repulsion"
    assert out["abs_loss"] > 0


def test_base_combine_outputs_lock_delta_only():
    out = run_combine(source_abs=10, target_abs=8, lock_ratio=0.5)
    assert out["effect"] == "combine"
    assert out["vector"] == "binding"
    assert out["abs_locked"] == 4.0


def test_base_pierce_outputs_damage_delta_only():
    out = run_pierce(source_abs=10, target_abs=8, penetration_ratio=0.5)
    assert out["effect"] == "pierce"
    assert out["vector"] == "penetration"
    assert out["abs_loss"] == 4.0

