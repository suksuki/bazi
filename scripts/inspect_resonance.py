
import sys
import os
import json
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from core.trinity.core.quantum_engine import QuantumEngine

def inspect_resonance():
    mantra_path = Path("tests/data/quantum_mantra_v93.json")
    with open(mantra_path, "r", encoding="utf-8") as f:
        cases = json.load(f)

    engine = QuantumEngine()
    
    print(f"{'ID':<15} | {'Locking':<8} | {'Sync':<8} | {'Mode':<10}")
    print("-" * 50)
    
    for case in cases:
        bazi = case['bazi']
        dm = case['day_master']
        month = case['month_branch']
        
        analysis = engine.analyze_bazi(bazi, dm, month)
        res = analysis.get('resonance_state').resonance_report
        
        print(f"{case['id']:<15} | {res.locking_ratio:<8.3f} | {res.sync_state:<8.3f} | {res.vibration_mode:<10}")

if __name__ == "__main__":
    inspect_resonance()
