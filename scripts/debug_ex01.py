
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from core.trinity.core.quantum_engine import QuantumEngine

def debug_ex01():
    engine = QuantumEngine()
    case = {
        "bazi": ["壬子", "壬子", "壬子", "壬子"], 
        "day_master": "壬",
        "month_branch": "子"
    }
    
    print("--- 1. Initialization Test ---")
    waves = engine._initialize_waves(case['bazi'], "壬", "子")
    for e, w in waves.items():
        print(f"{e}: Amp={w.amplitude:.2f} Ph={w.phase:.2f}")

    print("\n--- 2. Logic Matrix Test ---")
    interactions = engine.logic.match_logic(case['bazi'], "壬", waves)
    for r in interactions:
        print(r)

    print("\n--- 3. Flux Test (3 Steps) ---")
    final = engine.flux.simulate_wave_flow(waves, interactions, "子", steps=3)
    for e, w in final.items():
        print(f"{e}: Amp={w.amplitude:.2f}")

if __name__ == "__main__":
    debug_ex01()
