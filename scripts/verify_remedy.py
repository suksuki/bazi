
import sys
import os
import json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.trinity.core.oracle import TrinityOracle

def verify_remedy():
    print("--- Phase 33: Remedy Injection Verification (Hai Water) ---")
    
    # CASE: Tiger-Snake-Monkey (Ungrateful Penalty)
    # 1998-5-26 16:00 (approx for Wu-Yin, Ding-Si, Geng-Shen structure)
    # Using mock pillars for precise control
    
    # Base Case: Yin(Month)-Si(Day)-Shen(Hour)
    base_pillars = ["戊寅", "丁巳", "庚申", "甲申"] 
    dm = "庚"
    
    oracle = TrinityOracle()
    
    print("\n[TEST 1] Baseline Stress (No Injection)")
    res1 = oracle.analyze(base_pillars, dm)
    sai1 = res1.get('structural_stress', {}).get('SAI', 0.0)
    print(f"  > SAI Baseline: {sai1} {'[CRITICAL]' if sai1 > 0.75 else ''}")
    
    print("\n[TEST 2] Quantum Injection (Hai Water 亥)")
    # Injecting '亥'
    res2 = oracle.analyze(base_pillars, dm, injections=['亥'])
    sai2 = res2.get('structural_stress', {}).get('SAI', 0.0)
    print(f"  > SAI After Injection: {sai2}")
    
    # Calculate Drop
    if sai1 > 0:
        drop = (sai1 - sai2) / sai1 * 100
        print(f"  > Stress Reduction: {drop:.1f}%")
        if drop >= 40:
             print("  [SUCCESS] Shear Stress Damped Significantly.")
        else:
             print("  [FAIL] Damping Insufficient.")
    
    # Check defects for Remedy Note
    defects = res2.get('structural_stress', {}).get('defects', [])
    remedy_active = any(d.get('type') == 'REMEDY_ACTIVE' for d in defects)
    print(f"  > Remedy Logic Active: {remedy_active}")

if __name__ == "__main__":
    verify_remedy()
