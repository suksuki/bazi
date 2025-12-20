import sys
import os
import json
from pathlib import Path
from typing import List, Dict, Any

# Add project root to sys.path
sys.path.append(str(Path(__file__).parent))

from core.engine_v88 import EngineV88
from core.trinity.core.quantum_engine import QuantumEngine

def verify_case(case: Dict[str, Any], legacy_engine: EngineV88, trinity_engine: QuantumEngine):
    name = case.get('name', 'Unknown')
    bazi = case.get('bazi', [])
    dm = case.get('day_master', '')
    # Month branch is the second character of the second pillar
    month_branch = bazi[1][1] if len(bazi) > 1 and len(bazi[1]) > 1 else ''
    
    print(f"\n>>> Verifying: {name}")
    print(f"    Bazi: {bazi}, DM: {dm}, Month Branch: {month_branch}")
    
    # 1. Legacy EngineV88
    res_l = legacy_engine.analyze(bazi, dm)
    legacy_verdict = res_l.strength.verdict
    legacy_score = res_l.strength.adjusted_score
    
    # 2. Trinity QuantumEngine
    res_t = trinity_engine.analyze_bazi(bazi, dm, month_branch)
    trinity_verdict = res_t['verdict']['label']
    trinity_prob = res_t['verdict'].get('order_parameter', 0.0) # V14 Update
    trinity_score = res_t['verdict']['score']
    
    # Ground Truth Comparison
    gt = case.get('ground_truth', {})
    expected = gt.get('strength', 'N/A')
    
    # V15 Label Normalization
    normalized_verdict = trinity_verdict.replace("Extreme ", "")
    status = "✅ PASS" if normalized_verdict == expected else "❌ FAIL"
    
    if trinity_verdict == expected == legacy_verdict:
        status = "✨ PERFECT (Matches Legacy & GT)"
    elif normalized_verdict == expected:
        status = "✅ PASS (V15 Extreme Category)"
        
    print(f"    Expected: {expected}")
    print(f"    Legacy:  {legacy_verdict} (Score: {legacy_score:.2f})")
    print(f"    Trinity: {trinity_verdict} (Prob: {trinity_prob:.2f}, Score: {trinity_score:.2f}) -> {status}")
    
    # Print matched rules for Trinity
    rules = res_t.get('matched_rules', [])
    if rules:
        active_rules = [r['name'] for r in rules if r.get('active')]
        print(f"    Trinity Rules: {', '.join(active_rules[:5])}{'...' if len(active_rules) > 5 else ''}")

    return normalized_verdict == expected

def verify_bulk():
    print("=== Trinity V10.0 Celebrity Batch Verification ===")
    
    data_path = Path(__file__).parent / "data" / "real_celebrity_cases.json"
    if not data_path.exists():
        print(f"Error: Data file not found at {data_path}")
        return

    with open(data_path, 'r', encoding='utf-8') as f:
        cases = json.load(f)
        
    legacy = EngineV88()
    trinity = QuantumEngine()
    
    passed = 0
    total = len(cases)
    
    for case in cases:
        if verify_case(case, legacy, trinity):
            passed += 1
            
    print("\n" + "="*40)
    print(f"Final Result: {passed}/{total} Passed")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    print("="*40)

if __name__ == "__main__":
    verify_bulk()
