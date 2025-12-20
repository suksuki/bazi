
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from core.trinity.core.quantum_engine import QuantumEngine

def debug_blade():
    config = {
        'physics': {
            'coherence_boost': 2.0,
            'recoil_factor': 1.5,
            'shielding_factor': 15.0
        }
    }
    engine = QuantumEngine(config=config)
    case = {
        "bazi": ["庚申", "辛酉", "庚申", "辛酉"], 
        "day_master": "庚",
        "month_branch": "酉"
    }
    
    print("--- 1. Initialization Test (Metal Blade) ---")
    waves = engine._initialize_waves(case['bazi'], "庚", "酉")
    for e, w in waves.items():
        print(f"{e}: Amp={w.amplitude:.2f}")

    print("\n--- 2. Logic Matrix Test ---")
    interactions = engine.logic.match_logic(case['bazi'], "庚", waves)
    
    print("\n--- 3. Flux Test (3 Steps) ---")
    final = engine.flux.simulate_wave_flow(waves, interactions, "酉", steps=3)
    for e, w in final.items():
        print(f"{e}: Amp={w.amplitude:.2f}")
        
    res = engine.analyze_bazi(case['bazi'], "庚", "酉")
    print(f"\nVerdict: {res['verdict']['label']}")

if __name__ == "__main__":
    debug_blade()
