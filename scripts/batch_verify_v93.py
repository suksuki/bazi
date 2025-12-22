
import sys
import os
import json
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from core.trinity.core.quantum_engine import QuantumEngine

def run_batch():
    mantra_path = Path("tests/data/quantum_mantra_v93.json")
    if not mantra_path.exists():
        print(f"Error: {mantra_path} not found.")
        return

    with open(mantra_path, "r", encoding="utf-8") as f:
        cases = json.load(f)

    engine = QuantumEngine()
    results = []
    
    print(f"{'ID':<15} | {'Expected':<10} | {'Actual':<10} | {'Sync':<6} | {'Status'}")
    print("-" * 65)
    
    passed = 0
    for case in cases:
        bazi = case['bazi']
        dm = case['day_master']
        month = case['month_branch']
        expected = case['expected_mode']
        
        analysis = engine.analyze_bazi(bazi, dm, month)
        resonance = analysis.get('resonance_state')
        report = resonance.resonance_report
        
        actual = report.vibration_mode
        sync = report.sync_state
        
        status = "✅" if actual == expected else "❌"
        if status == "✅": passed += 1
        
        print(f"{case['id']:<15} | {expected:<10} | {actual:<10} | {sync:.3f} | {status}")
        results.append({
            "id": case['id'],
            "expected": expected,
            "actual": actual,
            "status": status
        })

    print("-" * 65)
    print(f"Total: {len(cases)}, Passed: {passed}, Accuracy: {(passed/len(cases))*100:.1f}%")

if __name__ == "__main__":
    run_batch()
