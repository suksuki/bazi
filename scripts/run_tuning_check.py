import sys
import os
import copy
sys.path.append(os.getcwd())
from core.engine_v88 import EngineV88 as QuantumEngine  # V8.8 Modular
from core.config_schema import DEFAULT_FULL_ALGO_PARAMS
from ui.pages.quantum_lab import create_profile_from_case
import json

# Mock Profile for simplicity
class MockProfile:
    def __init__(self, dm, pillars, gender):
        self.day_master = dm
        self.pillars = { 'year': pillars[0], 'month': pillars[1], 'day': pillars[2], 'hour': pillars[3] }
        self.gender = 1 if gender == "男" else 0
        self.birth_date = None
    def get_luck_pillar_at(self, year): return "None"

def run_tuning_test():
    print("=== 🧪 Phase 2: Code Injection Verification & Tuning ===")
    
    path = "data/calibration_cases.json"
    with open(path, "r") as f: cases = json.load(f)

    # 1. Base Config
    params = copy.deepcopy(DEFAULT_FULL_ALGO_PARAMS)
    
    # 2. Apply Surgical Tuning (Simulating User Action)
    # Strategy: We want to weaken Case 002.
    # Case 002 is Strong because Fire -> Earth -> Metal (Guan Yin Xiang Sheng).
    # We need to DECREASE Resource Benefit or INCREASE Officer Damage.
    # Parameter: 'W_Rel_Spouse' (Spouse/Officer Weight)? No.
    # Parameter: 'exposedBoost'? 
    # Parameter: 'w_e_weight' (Global Energy Weight)?
    
    # Let's try adjusting Flow Decay to reduce "remote" support?
    # Or reduce Rooting Weight (to mimic reduced Hidden Stem support, although Engine is blind to hidden stems, it uses Main Element).
    # Case 002: Day Branch is Chou (Earth). Main Element Earth.
    # Xin Metal is produced by Earth.
    # If we reduce 'resource' support?
    
    # Let's just run with Default first to see if Case 005 is fixed.
    engine = QuantumEngine(params)
    
    print(f"\n[Run 1] Default Params + Code Injection (V7.4)")
    for c in cases:
        if c['id'] not in ['CASE_002_STAR_ACTRESS', 'CASE_005_WARLORD_YUAN']: continue
        
        # Profile
        # Fix: Direct access to bazi list
        raw_bazi = c['bazi'] # ["Year", "Month", "Day", "Hour"]
        
        # Parse into (Stem, Branch) tuples if engine needs that?
        # Engine _evaluate_wang_shuai takes list of tuples or list of strings?
        # Looking at core/quantum_engine.py _calculate_energy_v7:
        # It expects pillars to be iterable where p[0] is stem, p[1] is branch.
        # String "乙未" works as p[0]='乙', p[1]='未'. 
        # So passing ["乙未", ...] works!
        
        mp = MockProfile(c['day_master'], raw_bazi, c.get('gender', 'Male'))
        
        ws, score = engine._evaluate_wang_shuai(mp.day_master, raw_bazi)
        gt = c['ground_truth']['strength']
        
        icon = "✅" if (gt in ws) or (("Follower" in gt) and ("Follower" in ws)) else "❌"
        print(f"{c['id']}: Target[{gt}] Computed[{ws} {score:.1f}] {icon}")

if __name__ == "__main__":
    run_tuning_test()
