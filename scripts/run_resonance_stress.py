
import sys
import os
import json
import numpy as np
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from core.trinity.core.quantum_engine import QuantumEngine
from core.trinity.core.resonance_engine import ResonanceEngine
from core.trinity.core.wave_mechanics import WaveState

from core.trinity.core.physics_engine import ParticleDefinitions

def run_stress_tests():
    data_path = Path(__file__).parent.parent / "tests/data/resonance_stress_tests.json"
    with open(data_path, 'r', encoding='utf-8') as f:
        cases = json.load(f)

    engine = QuantumEngine()
    
    print(f"🚀 Running {len(cases)} Resonance Stress Tests...\n")
    
    for case in cases:
        print(f"--- Case: {case['name']} ---")
        # Full analysis to get waves and resonance
        month_branch = case['bazi'][1][1]
        result_full = engine.analyze_bazi(case['bazi'], case['day_master'], month_branch)
        
        res = result_full['resonance_state'].resonance_report
        
        print(f"Mode: {res.vibration_mode}")
        print(f"Locking Ratio: {res.locking_ratio:.2f}")
        print(f"Sync State: {res.sync_state:.4f}")
        
        if res.vibration_mode == "BEATING":
            # Test envelope at different t
            for t in [0, 5, 10]:
                env = ResonanceEngine.interference_envelope(t, res.envelop_frequency)
                print(f"  t={t:.1f} -> Env={env:.4f} {'(Crisis!)' if env < 0.2 else ''}")
        
        print(f"Description: {res.description}\n")

if __name__ == "__main__":
    run_stress_tests()
