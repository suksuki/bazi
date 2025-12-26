
import pytest
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.trinity.core.unified_arbitrator_master import QuantumUniversalFramework
from core.trinity.core.middleware.influence_bus import InfluenceBus, ExpectationVector
from core.trinity.core.operators.standard_factors import LuckCycleFactor, AnnualPulseFactor, GeoBiasFactor
from core.trinity.core.engines.pattern_scout import PatternScout
from core.bazi_profile import BaziProfile

@pytest.fixture
def framework():
    return QuantumUniversalFramework()

@pytest.fixture
def scout():
    return PatternScout()

def test_framework_initialization(framework):
    """Verify that the QuantumUniversalFramework initializes correctly."""
    assert framework.registry is not None
    assert framework.dispersion_engine is not None
    assert framework.gravity_engine is not None
    assert framework.inertia_engine is not None

def test_pattern_scout_v4_1_registration(scout):
    """Verify that all V4.1/V5.0 topics are correctly registered and accessible."""
    topics = [
        "SHANG_GUAN_JIAN_GUAN", "SHANG_GUAN_SHANG_JIN", "YANG_REN_JIA_SHA", 
        "XIAO_SHEN_DUO_SHI", "CAI_GUAN_XIANG_SHENG_V4", "SHANG_GUAN_PEI_YIN", 
        "SHI_SHEN_ZHI_SHA", "PGB_ULTRA_FLUID", "PGB_BRITTLE_TITAN"
    ]
    
    chart = ["癸卯", "甲寅", "癸亥", "壬子", ("甲", "子"), ("丙", "午")]
    for tid in topics:
        res = scout._deep_audit(chart, tid)
        assert res is None or isinstance(res, dict)

def test_geo_phase_shift_v4_1_6(framework):
    """Verify the V4.1.6 Geo Phase Cancellation logic in the brittle zone."""
    context = {"sai_estimate": 5.0} # Brittle Zone
    
    geo_factor = GeoBiasFactor(geo_factor=1.2, geo_element="Fire")
    e_vector = ExpectationVector(elements={"fire": 10.0})
    
    # 1. Normal Zone
    result_std = geo_factor.apply_nonlinear_correction(e_vector, {"sai_estimate": 1.0})
    assert abs(result_std.elements["fire"] - 12.0) < 0.01 
    
    # 2. Brittle Zone Cancellation
    result_cancel = geo_factor.apply_nonlinear_correction(e_vector, context)
    # Expected: 10.0 * (1.0 - 0.33) = 6.7
    assert result_cancel.elements["fire"] < 10.0
    assert any("Geo Phase Cancellation [V4.1.6]" in log for log in geo_factor._logs)

def test_archive_pulse_smoke(framework):
    """Verify that a real archive can be processed through the full pipeline."""
    case_data = ["戊午", "丁巳", "壬子", "庚子"] 
    birth_info = {"gender": "female", "year": 1978, "month": 5, "day": 7, "hour": 0}
    
    state = framework.arbitrate_bazi(case_data, birth_info)
    assert state is not None
    assert "physics" in state
    assert "intelligence" in state
    
    report = framework.generate_holographic_report(state)
    assert len(report) > 500
    assert "八字物理全息" in report

def test_pgb_v4_1_fluid_logic(scout):
    """Verify the PGB V4.1 Superfluid logic with a triggering chart."""
    # DM: 甲 (Natal stems: 庚, 甲, 甲, 丙 -> [7S, BJ, Self, SS])
    chart = [("庚", "午"), ("甲", "申"), ("甲", "寅"), ("丙", "寅"), ("甲", "子"), ("丙", "午")]
    
    res_fluid = scout._deep_audit(chart, "PGB_ULTRA_FLUID")
    assert res_fluid is not None
    assert "sai" in res_fluid
    assert res_fluid["audit_mode"] == "PGB_V4.1_ULTRA_FLUID"

if __name__ == "__main__":
    pytest.main([__file__])
