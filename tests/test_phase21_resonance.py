
import sys
import os
import numpy as np

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.trinity.core.wave_mechanics import WaveState
from core.trinity.core.structural_dynamics import StructuralDynamics

def test_resonance_scenarios():
    print("\n=== PHASE 21: RESONANT WAVE UNIFIED TEST ===")
    
    # 1. Day Master Wave (Base)
    dm_wave = WaveState(amplitude=2.0, phase=0.0)
    
    # --- Scenario A: TRUE FOLLOW (Coherent Sync) ---
    print("\n🔬 SCENARIO A: TRUE FOLLOW (Superconductive Resonance)")
    # Field is huge and in-phase
    field_waves = [
        WaveState(amplitude=8.0, phase=0.1), # Very close to DM phase
        WaveState(amplitude=6.0, phase=-0.05)
    ]
    
    result = StructuralDynamics.evaluate_system_resonance(dm_wave, field_waves)
    print(f"Result: {result.resonance_report.vibration_mode}")
    print(f"Sync State: {result.total_coherence:.4f}")
    print(f"Locking Ratio: {result.resonance_report.locking_ratio:.2f}")
    print(f"Narrative: {result.description}")

    # --- Scenario B: FAKE FOLLOW (Beating) ---
    print("\n🔬 SCENARIO B: FAKE FOLLOW (Phase Beating)")
    # Field is huge but phase mismatch is significant (e.g. 60 degrees)
    field_waves_b = [
        WaveState(amplitude=7.0, phase=np.radians(60)), 
        WaveState(amplitude=5.0, phase=np.radians(70))
    ]
    
    result_b = StructuralDynamics.evaluate_system_resonance(dm_wave, field_waves_b)
    print(f"Result: {result_b.resonance_report.vibration_mode}")
    print(f"Sync State: {result_b.total_coherence:.4f}")
    print(f"Envelope Freq: {result_b.resonance_report.envelop_frequency:.4f}")
    print(f"Narrative: {result_b.description}")

    # --- Scenario C: ORDINARY (Damped Interference) ---
    print("\n🔬 SCENARIO C: ORDINARY SYSTEM (Independent Damping)")
    # Field is weak or phase is opposite
    field_waves_c = [
        WaveState(amplitude=1.5, phase=np.pi), # Out of phase
        WaveState(amplitude=1.0, phase=np.pi/2)
    ]
    
    result_c = StructuralDynamics.evaluate_system_resonance(dm_wave, field_waves_c)
    print(f"Result: {result_c.resonance_report.vibration_mode}")
    print(f"Sync State: {result_c.total_coherence:.4f}")
    print(f"Impedance Shift: {result_c.resonance_report.impedance_shift:.2f}")
    print(f"Narrative: {result_c.description}")

if __name__ == "__main__":
    test_resonance_scenarios()
