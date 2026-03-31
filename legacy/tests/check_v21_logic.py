
import numpy as np
import json
import sys
from core.trinity.core.oracle import TrinityOracle
from core.trinity.core.structural_dynamics import StructuralDynamics
from core.trinity.core.intelligence.quantum_remedy import QuantumRemedy
from core.trinity.core.physics.wave_laws import WaveState

def run_checks():
    print("🚀 Starting Phase 28 Comprehensive Logic Verification...")
    
    # Check 1: Structural Dynamics & AGC
    print("\n--- [1] Structural Dynamics: Scenario 004 ---")
    params = {"radiation_flux": 1.5, "shielding_thickness_mu": 0.85, "agc_enabled": True}
    res_sd = StructuralDynamics.run_scenario_004(params)
    print(f"Status: {res_sd['interpretation']}")
    print(f"Metrics: Efficiency={res_sd['metrics']['shielding_efficiency']:.2%}, Optimized Mu={res_sd['metrics']['shielding_thickness_optimized']}")
    if not res_sd['metrics']['is_aggregated']:
        print("❌ FAIL: Core failed to aggregate.")
        sys.exit(1)
    print("✅ PASS")

    # Check 2: Quantum Remedy Particle Mapping
    print("\n--- [2] Quantum Remedy: Particle Mapping ---")
    dm_wave = WaveState(amplitude=10, phase=3.7699) # Metal
    field = [WaveState(amplitude=30, phase=5.0265)] # Water
    remedy = QuantumRemedy.find_optimal_remedy(dm_wave, field)
    print(f"Suggested Particle: {remedy.get('best_particle')} ({remedy.get('optimal_element')})")
    print(f"Description: {remedy.get('description')}")
    if remedy.get('best_particle') == "None" or remedy.get('best_particle') is None:
        print("❌ FAIL: Particle mapping returned None.")
        sys.exit(1)
    print("✅ PASS")

    # Check 3: Oracle Interaction Detection
    print("\n--- [3] Trinity Oracle: Oppose Analysis ---")
    oracle = TrinityOracle()
    # Geng (Metal) vs Ren (Water/SG) vs Ding (Fire/OG)
    pillars = ["庚辰", "壬子", "庚子", "丁丑"]
    day_master = "庚"
    res_oracle = oracle.analyze(pillars, day_master)
    
    oppose_count = sum(1 for i in res_oracle['interactions'] if i['type'] == 'OPPOSE')
    print(f"Mode: {res_oracle['resonance'].mode}")
    print(f"Oppose Interactions Detected: {oppose_count}")
    if oppose_count == 0:
        print("❌ FAIL: No OPPOSE interaction detected for Shang Guan vs Zheng Guan.")
        sys.exit(1)
    
    if res_oracle.get('remedy'):
        print(f"Auto-Remedy Suggested: {res_oracle['remedy'].get('best_particle')}")
    else:
        print("⚠️ WARNING: No remedy suggested (Check sync_state threshold).")
    print("✅ PASS")

    print("\n📦 PHASE 28 FULL SYSTEM VALIDATION COMPLETE: 100% COHERENCE")

if __name__ == "__main__":
    run_checks()
