from app.plugins.base.interactions.clash import run_clash
from app.plugins.base.interactions.combine import run_combine
from app.plugins.base.interactions.grave import run_grave
from app.plugins.base.interactions.pierce import run_pierce
from app.plugins.base.interactions.punish import run_punish
from app.core.rules.junction import EnergyVaultStatus


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


def test_base_punish_friction_loss():
    out = run_punish(source_abs=10, target_abs=8, friction_coeff=0.25, mode="sanxing")
    assert out["effect"] == "punish"
    assert out["vector"] == "torsional_friction"
    assert out["abs_loss"] == 2.0
    assert out["impact_torque"] == 2.0


def test_base_grave_locked_vs_unlocked():
    locked = run_grave(base_abs=100.0, unlocked=False, burst_multiplier=1.3)
    assert locked["phi_work"] == 0.0
    assert locked["abs_burst"] == 0.0
    assert locked["energy_vault_status"] == EnergyVaultStatus.LOCKED.value
    active = run_grave(base_abs=100.0, unlocked=True, burst_multiplier=1.3)
    assert active["phi_work"] == 1.0
    assert active["abs_burst"] == 130.0
    assert active["energy_vault_status"] == EnergyVaultStatus.ACTIVE.value

