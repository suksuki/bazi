
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from core.trinity.core.quantum_engine import QuantumEngine

def debug_axe():
    config = {
        'physics': {
            'coherence_boost': 4.0,
            'recoil_factor': 1.5,
            'shielding_factor': 15.0,
            'entropy_guard': 1.0
        }
    }
    engine = QuantumEngine(config=config)
    case = {
        "bazi": ["庚申", "庚申", "甲寅", "庚申"], 
        "day_master": "甲",
        "month_branch": "申"
    }
    
    print("--- 1. Initialization Test (Wood vs Golden Axe) ---")
    waves = engine._initialize_waves(case['bazi'], "甲", "申")
    for e, w in waves.items():
        print(f"{e}: Amp={w.amplitude:.2f} Ph={w.phase:.2f}")

    print("\n--- 2. Logic Matrix Test ---")
    interactions = engine.logic.match_logic(case['bazi'], "甲", waves)
    for r in interactions:
        print(r)
    
    print("\n--- 3. Flux Test (3 Steps) ---")
    # Inject trace
    final = engine.flux.simulate_wave_flow(waves, interactions, "申", steps=3)
    for e, w in final.items():
        print(f"{e}: Amp={w.amplitude:.2f}")

if __name__ == "__main__":
    debug_axe()
