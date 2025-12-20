import sys
import os
import json
from pathlib import Path
from typing import List, Dict, Any

# Add project root to sys.path
sys.path.append(str(Path(__file__).parent.parent))

from core.trinity.core.quantum_engine import QuantumEngine

def verify_v14_case(case: Dict[str, Any], engine: QuantumEngine):
    name = case.get('name', 'Unknown')
    bazi = case.get('bazi', [])
    dm = case.get('day_master', '')
    month_branch = bazi[1][1] if len(bazi) > 1 and len(bazi[1]) > 1 else ''
    
    print(f"\n>>> [V14] Pressure Test: {name}")
    print(f"    Bazi: {bazi}, DM: {dm}, Month: {month_branch}")
    
    # Run V14 Engine
    res = engine.analyze_bazi(bazi, dm, month_branch)
    verdict = res['verdict']['label']
    order_param = res['verdict']['order_parameter']
    score = res['verdict']['score']
    
    gt = case.get('ground_truth', {})
    expected = gt.get('strength', 'N/A')
    category = gt.get('category', 'Unknown')
    
    status = "✅ PASS" if verdict == expected else "❌ FAIL"
    
    print(f"    Category: {category}")
    print(f"    Verdict: {verdict} (Order Parameter: {order_param:.4f})")
    print(f"    Energy Balance (Allies %): {score:.2f}%")
    print(f"    Integration Status: {status}")
    if verdict != expected:
        print(f"    [DEBUG] Mismatch: Verdict='{verdict}' Expected='{expected}'")
    
    # Print Wave Details
    waves = res.get('waves', {})
    if waves:
        top_elements = sorted(waves.items(), key=lambda x: x[1].amplitude, reverse=True)[:3]
        wave_str = ", ".join([f"{e}: {w.amplitude:.2f}@∠{np.degrees(w.phase):.0f}°" for e, w in top_elements])
        print(f"    Phasor Envelope: {wave_str}")

    return verdict == expected

import numpy as np # Needed for print logic

def run_v14_suite():
    print("🚀 Quantum Trinity V14.0: Precision Revolution Test Suite")
    print("=======================================================")
    
    # Load Cases (Default or Matrix 30)
    data_path = Path(__file__).parent.parent / "data" / "v14_synthetic_cases.json"
    matrix_path = Path(__file__).parent.parent / "tests" / "v14_tuning_matrix.json"
    
    cases = []
    if matrix_path.exists():
        print(f"DEBUG: Loading Matrix 30 from {matrix_path}")
        with open(matrix_path, 'r', encoding='utf-8') as f:
            cases = json.load(f)
        print(f"Dataset: Matrix 30 (Subset) - Loaded {len(cases)} cases")
    else:
        print(f"DEBUG: Loading Default from {data_path}")
        with open(data_path, 'r', encoding='utf-8') as f:
            cases = json.load(f)
        print(f"Dataset: V14 Synthetic Default - Loaded {len(cases)} cases")
        
    engine = QuantumEngine()
    
    passed = 0
    total = len(cases)
    
    for case in cases:
        if verify_v14_case(case, engine):
            passed += 1
            
    print("\n" + "="*55)
    print(f"V14.0 Summary: {passed}/{total} Passed")
    print(f"Precision Rating: {(passed/total)*100:.1f}%")
    print("="*55)

if __name__ == "__main__":
    run_v14_suite()
