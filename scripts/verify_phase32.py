
import sys
import os
import json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.trinity.core.oracle import TrinityOracle
from core.trinity.core.nexus.definitions import PhysicsConstants

def verify_phase32():
    print("--- Phase 32: Penalty & Harm Dynamics Verification ---")
    
    # Load Test Cases
    try:
        with open('tests/data/phase32_penalty_harm.json', 'r') as f:
            cases = json.load(f)
    except FileNotFoundError:
        print("Error: Test data not found.")
        return

    oracle = TrinityOracle()

    for case in cases:
        print(f"\n[CASE] {case['name']} ({case['id']})")
        bazi = case['bazi']
        dm = "庚" if "庚" in bazi[2] else bazi[2][0] # Simple extraction for test
        # Actually need proper day master extraction from string
        # Assuming format "StemBranch"
        dm = bazi[2][0] 
        
        # Pillars list
        pillars = [
            ("Year", bazi[0]), ("Month", bazi[1]), ("Day", bazi[2]), ("Hour", bazi[3])
        ]
        
        # Analyze
        # Mocking luck/annual for base test
        result = oracle.analyze(
            pillars=[(p[0], p[1][1]) for p in pillars], # Passing (Name, Branch) roughly? 
            # Wait, oracle expects pillars as [str, str, str, str]? No.
            # oracle.analyze signature: pillars: List[str]... wait let's check view_file.
            # oracle.py: analyze(pillars: List[str], day_master: str...) 
            # Actually pillars arg in analyze usually expects just strings or tuples?
            # Looking at previous usage: selected_case['bazi'][:4] is passed.
            # Definitions say pillars are strings like "甲子".
            # But the stress engine extraction used: `month_branch_s = all_pillars[1][1]`
            # This implies pillars are strings, so `p[1]` gets the 2nd char (Branch). Correct.
            
            day_master=dm,
            luck_pillar="甲子", # Dummy
            annual_pillar="乙丑" # Dummy
        )
        
        stress = result.get('structural_stress', {})
        print(f"  > SAI (Stress Index): {stress.get('SAI')} {'[CRITICAL]' if stress.get('SAI',0) > 0.75 else ''}")
        print(f"  > IC (Interference):  {stress.get('IC')} {'[HIGH JITTER]' if stress.get('IC',0) > 0.3 else ''}")
        print("  > Defects Topology:")
        for d in stress.get('defects', []):
            print(f"    - {d['type']} | Nodes: {d['nodes']} | Score: {d.get('score')}")

if __name__ == "__main__":
    verify_phase32()
