
import sys
import os
import json
import numpy as np
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from core.trinity.core.quantum_engine import QuantumEngine
from core.trinity.core.resonance_engine import ResonanceEngine
from core.trinity.core.entanglement_engine import EntanglementEngine

def simulate_phase_23_intervention():
    # Case 05-Q-CALIB-FOLLOW-002 (Fake Fire Follow)
    bazi = ["丙午", "甲午", "丁巳", "壬子"]
    dm = "丁"
    month = "午"
    t_crisis = 12.5 # Known crisis node
    
    engine = QuantumEngine()
    
    # 1. Base Scan (No Intervention)
    res_base = engine.analyze_bazi(bazi, dm, month, t=t_crisis)
    state_base = res_base.get('resonance_state')
    report_base = state_base.resonance_report
    env_base = ResonanceEngine.interference_envelope(t_crisis, report_base.envelop_frequency)
    
    print(f"--- 🧪 Phase 23: Quantum Intervention Simulation ---")
    print(f"Target Case: 05-Q-CALIB-FOLLOW-002 (Fake Fire Follow)")
    print(f"Crisis Node: t = {t_crisis}")
    print(f"Original Envelope: {env_base:.4f} (Safety: 🔥 CRISIS)")
    
    # 2. Quantum Intervention (Injecting Black/Water Particle)
    print("\n[Action] Injecting 'Black/Water' interference particles...")
    res_fix = engine.analyze_bazi(bazi, dm, month, t=t_crisis, injections=["Black/Blue"])
    state_fix = res_fix.get('resonance_state')
    report_fix = state_fix.resonance_report
    env_fix = ResonanceEngine.interference_envelope(t_crisis, report_fix.envelop_frequency)
    
    repair_rate = EntanglementEngine.calculate_repair_rate(env_base, env_fix)
    
    print(f"Intervention Envelope: {env_fix:.4f}")
    print(f"Locking Ratio Shift: {report_base.locking_ratio:.2f} -> {report_fix.locking_ratio:.2f}")
    print(f"Phase Repair Rate: {repair_rate*100:.2f}%")
    
    status = "🍀 SAFE" if env_fix > 0.6 else ("⚠️ WARNING" if env_fix > 0.2 else "🔥 CRISIS")
    print(f"New Status: {status}")
    
    if repair_rate > 0.3:
        print("\n🚀 SUCCESS: Quantum entanglement successfully stabilized the phase oscillation.")
    else:
        print("\n⚠️ PARTIAL: Signal coupling insufficient for full remediation.")

if __name__ == "__main__":
    simulate_phase_23_intervention()
