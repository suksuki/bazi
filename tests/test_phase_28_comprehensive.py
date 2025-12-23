
import pytest
import numpy as np
import json
from core.trinity.core.oracle import TrinityOracle
from core.trinity.core.structural_dynamics import StructuralDynamics
from core.trinity.core.intelligence.quantum_remedy import QuantumRemedy
from core.trinity.core.nexus.definitions import BaziParticleNexus

def test_structural_dynamics_shielding():
    """Test the shielding and AGC logic of Scenario 004."""
    params = {
        "radiation_flux": 1.5,
        "shielding_thickness_mu": 0.85,
        "agc_enabled": True
    }
    result = StructuralDynamics.run_scenario_004(params)
    
    assert result["metrics"]["is_aggregated"] is True
    assert result["metrics"]["shielding_efficiency"] > 0.8
    assert result["metrics"]["shielding_thickness_optimized"] >= 0.8
    assert result["agc_active"] is True

def test_quantum_remedy_particle_mapping():
    """Test if QuantumRemedy returns actual Bazi characters (Stems)."""
    from core.trinity.core.physics.wave_laws import WaveState
    
    # DM is Geng Metal (Metal), Field is pure Water (Output/Shang Guan) -> Needs Earth (Individually)
    dm_wave = WaveState(amplitude=10, phase=3.7699) # Metal
    field = [WaveState(amplitude=30, phase=5.0265)] # Water
    
    remedy = QuantumRemedy.find_optimal_remedy(dm_wave, field)
    
    # It should suggest Earth to dampen Water
    assert remedy["optimal_element"] == "Earth"
    assert remedy["best_particle"] == "戊"
    assert "best_particle" in remedy

def test_oracle_oppose_detection():
    """Test if the Oracle correctly identifies PH28_01 (Oppose)."""
    oracle = TrinityOracle()
    # Geng (Metal) vs Ren (Water/Shang Guan) vs Ding (Fire/Zheng Guan)
    pillars = ["庚辰", "壬子", "庚子", "丁丑"]
    day_master = "庚"
    
    res = oracle.analyze(pillars, day_master)
    
    # Find PH28_01 in interactions
    oppose_found = any(i["type"] == "OPPOSE" for i in res["interactions"])
    assert oppose_found is True
    
    # Check if remedy is suggested for low sync if sync < 0.9
    if res["resonance"].sync_state < 0.9:
        assert res["remedy"] is not None
        assert "best_particle" in res["remedy"]

def test_load_all_presets():
    """Ensure our calibration data loads correctly."""
    import os
    path = "tests/data/oppose_matrix_v21.json"
    assert os.path.exists(path)
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        assert len(data) >= 4
        assert data[3]["id"] == "OPPOSE_004_SHIELDING_INTERVENTION"
        assert data[3]["quality_tier"] == "A"

if __name__ == "__main__":
    pytest.main([__file__])
