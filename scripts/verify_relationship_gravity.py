#!/usr/bin/env python3
"""
Phase 36 Verification: Relationship Gravity Dynamics
Tests the RelationshipGravityEngine on test cases.
"""
import sys
import os
import json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.trinity.core.oracle import TrinityOracle

def run_verification():
    print("=" * 60)
    print("🌌 Phase 36: Relationship Gravity Dynamics Verification")
    print("=" * 60)
    
    # Load Test Data
    data_path = os.path.join(os.path.dirname(__file__), '../tests/data/phase36_relationship_gravity.json')
    with open(data_path, 'r') as f:
        cases = json.load(f)
        
    oracle = TrinityOracle()
    
    for case in cases:
        print(f"\n[SIMULATION] Target: {case['id']} - {case['name']}")
        print(f"  > Description: {case['description']}")
        print(f"  > Bazi: {' | '.join(case['bazi'])}")
        print(f"  > Day Master: {case['day_master']} ({case['gender']})")
        
        # Run Analysis
        res = oracle.analyze(case['bazi'], case['day_master'])
        r_data = res.get('relationship_gravity', {})
        
        # Extract Metrics
        E = r_data.get('Binding_Energy', 0)
        sigma = r_data.get('Orbital_Stability', 0)
        eta = r_data.get('Phase_Coherence', 0)
        peach = r_data.get('Peach_Blossom_Amplitude', 0)
        state = r_data.get('State', 'UNKNOWN')
        metrics = r_data.get('Metrics', {})
        
        print(f"\n  📊 Relationship Gravity Metrics:")
        print(f"     绑定能 (Binding Energy E): {E}")
        print(f"     轨道稳定性 (Orbital σ):    {sigma}")
        print(f"     相位相干性 (Coherence η):  {eta}")
        print(f"     桃花振幅 (Peach Blossom):  {peach}")
        print(f"     关系状态 (State):          {state}")
        
        print(f"\n  🔬 Detailed Metrics:")
        print(f"     配偶星 (Spouse Star):      {metrics.get('Spouse_Star', 'N/A')}")
        print(f"     配偶宫 (Spouse Palace):    {metrics.get('Spouse_Palace', 'N/A')} ({metrics.get('Spouse_Palace_Element', 'N/A')})")
        print(f"     摄动能 (Perturbation):     {metrics.get('Perturbation_Energy', 0)}")
        print(f"     轨道距离 (Orbital r):      {metrics.get('Orbital_Distance', 0)}")
        
        # Verification
        expected = case.get('expected_result', {})
        print(f"\n  ✅ Verification:")
        if 'State' in expected:
            status = "PASS" if state == expected['State'] else "FAIL"
            print(f"     State [{expected['State']}]: [{status}]")

if __name__ == "__main__":
    run_verification()
