import sys
import os
import json

# Add project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.trinity.core.engines.structural_vibration import StructuralVibrationEngine
from core.trinity.core.engines.temporal_shunting import TemporalShuntingEngine

def verify_precision_patches():
    print("🧪 Verifying Phase 4.0: Precision Calibration Patches...")
    
    # 1. Verify Hidden-State Pulse (MOD_15)
    print("\n1. Testing Hidden-State Pulse Activation (MOD_15)...")
    # Case: MOD15_PATCH_HIDDEN (辛己癸辛 | 酉丑巳酉)
    # 丑 contains [己(Main), 辛(Secondary), 癸(Tertiary)]
    # Annual Stem 癸 triggers the 3rd hidden stem.
    
    stems = ["辛", "己", "癸", "辛"]
    branches = ["酉", "丑", "巳", "酉"]
    engine_v = StructuralVibrationEngine("癸") # DM is癸
    
    # Run WITHOUT pulse trigger
    res_no_pulse = engine_v.calculate_vibration_metrics(stems, branches, context={"annual_pillar": "甲子"}) # 甲 does not trigger
    water_no_pulse = res_no_pulse['energy_state'].get('Water', 0)
    
    # Run WITH pulse trigger (癸 triggers癸)
    res_pulse = engine_v.calculate_vibration_metrics(stems, branches, context={"annual_pillar": "癸卯"}) 
    water_pulse = res_pulse['energy_state'].get('Water', 0)
    
    print(f"   - Water Energy (No Pulse): {water_no_pulse:.4f}")
    print(f"   - Water Energy (With Pulse): {water_pulse:.4f}")
    
    if water_pulse > water_no_pulse:
        print("   ✅ PASS: Hidden stem pulse activation detected.")
    else:
        print("   ❌ FAIL: Hidden stem pulse activation failed.")

    # 2. Verify Social Damping (MOD_16)
    print("\n2. Testing Social Damping (MOD_16)...")
    t_engine = TemporalShuntingEngine("壬")
    raw_peak = 2.5 # Simulated peak stress
    
    # Simulation: Stable Official (2.0) vs Freelancer (0.5)
    damped_gov = t_engine.simulate_intervention(raw_peak, "NONE", 1.0, social_damping=2.0)
    damped_free = t_engine.simulate_intervention(raw_peak, "NONE", 1.0, social_damping=0.5)
    
    print(f"   - Gov Official (D=2.0) Final SAI: {damped_gov['final_sai']}")
    print(f"   - Freelancer (D=0.5) Final SAI: {damped_free['final_sai']}")
    
    if damped_gov['final_sai'] < damped_free['final_sai']:
        print("   ✅ PASS: Social damping correctly buffers SAI stress.")
    else:
        print("   ❌ FAIL: Social damping logic ineffective.")

    # 3. Verify Refined Phase Reversal (80% Threshold)
    print("\n3. Testing Refined Phase Reversal (80% Threshold)...")
    # All Fire Bazi
    stems_f = ["丙", "丙", "丙", "丙"]
    branches_f = ["午", "午", "午", "午"]
    engine_f = StructuralVibrationEngine("丙")
    
    res_f = engine_f.calculate_vibration_metrics(stems_f, branches_f, context={})
    is_phase = res_f['is_phase_transition']
    purity = max(res_f['energy_state'].values()) / sum(res_f['energy_state'].values())
    
    print(f"   - System Purity: {purity*100:.1f}%")
    print(f"   - Phase Transition Triggered: {is_phase}")
    print(f"   - Optimal Deity Mix: {res_f['optimal_deity_mix']}")
    
    if is_phase and purity >= 0.80:
        if 'Fire' in res_f['optimal_deity_mix'] and 'Earth' in res_f['optimal_deity_mix']:
             print("   ✅ PASS: Logic Inverted (Dominant Fire and Output Earth supported).")
        else:
             print("   ❌ FAIL: Logic Inversion incomplete.")
    else:
        print(f"   ❌ FAIL: Phase transition did not trigger at {purity*100:.1f}% purity.")

    print("\n🏁 Phase 4.0 Verification Complete.")

if __name__ == "__main__":
    verify_precision_patches()
