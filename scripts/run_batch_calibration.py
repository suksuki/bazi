import sys
import os
import json
import copy
sys.path.append(os.getcwd())
try:
    from core.engine_v88 import EngineV88 as QuantumEngine  # V8.8 Modular
    from core.config_schema import DEFAULT_FULL_ALGO_PARAMS
    from ui.pages.quantum_lab import create_profile_from_case # Try reuse logic if possible, or mock
except ImportError:
    # If UI import fails due to streamlit dependency in headless mode, mock create_profile
    from core.bazi_profile import VirtualBaziProfile
    from core.engine_v88 import EngineV88 as QuantumEngine  # V8.8 Modular
    from core.config_schema import DEFAULT_FULL_ALGO_PARAMS

def create_profile_mock(case, luck):
    bazi = case['bazi'] # ["Year", "Month", "Day", "Hour"]
    # We need a profile with pillars accessed by .pillars['year']
    # VirtualBaziProfile is perfect.
    class MockProfile:
        def __init__(self, dm, pillars, gender):
            self.day_master = dm
            self.pillars = {
                'year': pillars[0],
                'month': pillars[1],
                'day': pillars[2],
                'hour': pillars[3]
            }
            self.gender = 1 if gender == "男" else 0
            self.birth_date = None
        
        def get_luck_pillar_at(self, year):
            return luck

    return MockProfile(case['day_master'], bazi, case['gender'])

def run_batch():
    # 1. Load Cases
    path = "data/calibration_cases.json"
    if not os.path.exists(path):
        print("Error: data/calibration_cases.json not found.")
        return

    with open(path, "r") as f:
        cases = json.load(f)

    # 2. Init Engine (With Tuning)
    params = copy.deepcopy(DEFAULT_FULL_ALGO_PARAMS)
    
    # [Target Tuning: Damping Protocol Phase 2]
    # 1. Tighten Output Drain (Protect Self): MaxDrain 0.4
    params['flow']['outputViscosity'] = {'maxDrainRate': 0.4, 'drainFriction': 0.2}
    
    # 2. Increase Resource Impedance (Prevent bloating): Base 0.5
    params['flow']['resourceImpedance'] = {'base': 0.5, 'weaknessPenalty': 0.5}
    
    # [Target Tuning: Operation Month Storm]
    # 3. Boost Month Command to Emperor Status (2.0)
    params['physics']['pillarWeights']['month'] = 2.0
    
    # Legacy Bonus (Case 005) - Keep High
    params['interactions']['stemFiveCombination']['bonus'] = 6.0 
    
    engine = QuantumEngine()
    engine.update_full_config(params) # Deep Update
    
    print("=== 🧪 V7.3 Batch Calibration Report (Tuned Params) ===\n")
    print(f"{'Case ID':<25} | {'Target':<10} | {'Computed':<10} | {'Result':<5} | {'Score'}")
    print("-" * 75)

    passed = 0
    total = 0
    failed_list = []

    for c in cases:
        gt = c.get('ground_truth')
        if not gt: continue
        total += 1
        
        # Profile
        presets = c.get("dynamic_checks", [])
        luck_p = presets[0]['luck'] if presets else "癸卯"
        # We use the mock profile which mimics the structure used in UI
        profile = create_profile_mock(c, luck_p)
        
        # Engine Eval
        bazi_list = [profile.pillars['year'], profile.pillars['month'], profile.pillars['day'], profile.pillars['hour']]
        try:
            ws_tuple = engine._evaluate_wang_shuai(profile.day_master, bazi_list)
            comp_str = ws_tuple[0] # "Strong" / "Weak"
            comp_score = ws_tuple[1]
        except Exception as e:
            comp_str = "Error"
            comp_score = 0.0

        # Verify
        target_str = gt.get('strength', 'Unknown')
        is_match = False
        
        # Loose Match Logic (Same as UI)
        if target_str != "Unknown":
            if (target_str in comp_str) or (comp_str in target_str):
                is_match = True
            if "Follower" in target_str and "Follower" in comp_str:
                is_match = True

        if is_match:
            passed += 1
            res_icon = "✅"
        else:
            res_icon = "❌"
            failed_list.append((c['id'], target_str, comp_str, comp_score))

        print(f"{c.get('id', 'Unknown')[:25]:<25} | {target_str:<10} | {comp_str:<10} | {res_icon:<5} | {comp_score:.1f}")

    print("-" * 75)
    acc = (passed / total * 100) if total else 0
    print(f"\n📊 Global Accuracy: {acc:.1f}% ({passed}/{total})")
    
    if failed_list:
        print("\n🚩 RED LIST (Failures):")
        for fid, tgt, cmp, scr in failed_list:
            print(f" - {fid}: Target[{tgt}] vs Computed[{cmp}] (Score: {scr:.1f})")

if __name__ == "__main__":
    run_batch()
