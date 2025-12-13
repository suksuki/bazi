
import json
import os
import sys

# Add repository root to path
sys.path.append("/home/jin/bazi_predict")
from core.quantum_engine import QuantumEngine

TARGET_FILE = "/home/jin/bazi_predict/data/calibration_cases.json"

NEW_CASES_DATA = [
  {
    "id": 21,
    "desc": "The Corporate Manager (Classic Officer-Resource)",
    "bazi": ["庚午", "甲申", "甲子", "乙亥"],
    "day_master": "甲",
    "gender": "男",
    "wang_shuai": "偏弱 (有印化杀)",
    "v_real": { "career": 5.0, "wealth": 3.0, "relationship": 2.0 },
    "physics_sources": {
        "self": { "stem_support": -2.0, "day_root": 4.0 }, 
        "officer": { "base": 9.0 }, 
        "wealth": { "base": 3.0 },
        "resource": { "base": 6.0 },
        "output": { "base": 0.0 }
    }
  },
  {
    "id": 22,
    "desc": "The Tech Entrepreneur (Output Generates Wealth)",
    "bazi": ["丙午", "甲午", "丙辰", "己丑"],
    "day_master": "丙",
    "gender": "男",
    "wang_shuai": "身旺 (食神生财)",
    "v_real": { "career": 4.0, "wealth": 6.0, "relationship": -2.0 },
    "physics_sources": {
        "self": { "stem_support": 8.0, "day_root": 6.0 }, 
        "output": { "base": 9.0 }, 
        "wealth": { "base": 7.0 },
        "officer": { "base": 2.0 }, # from relationship/spouse_star in user json? or minimal
        "resource": { "base": 0.0 }
    }
  },
  {
    "id": 23,
    "desc": "The Supported Spouse (Officer Heavy)",
    "bazi": ["乙卯", "己卯", "己未", "甲子"],
    "day_master": "己",
    "gender": "女",
    "wang_shuai": "身弱 (官杀混杂)",
    "v_real": { "career": -1.0, "wealth": 4.0, "relationship": 5.0 },
    "physics_sources": {
        "self": { "stem_support": -3.0, "day_root": 3.0 }, 
        "officer": { "base": 13.0 }, 
        "wealth": { "base": 5.0 },
        "output": { "base": 0.0 },
        "resource": { "base": 0.0 }
    }
  },
  {
    "id": 24,
    "desc": "The Freelance Artist (Leaking Structure)",
    "bazi": ["壬寅", "壬寅", "壬申", "甲辰"],
    "day_master": "壬",
    "gender": "男",
    "wang_shuai": "身弱 (食伤极旺)",
    "v_real": { "career": -3.0, "wealth": 2.0, "relationship": -4.0 },
    "physics_sources": {
        "self": { "stem_support": 2.0, "day_root": 2.0 }, 
        "output": { "base": 14.0 }, 
        "officer": { "base": 0.0 },
        "wealth": { "base": 0.0 },
        "resource": { "base": 0.0 }
    }
  },
  {
    "id": 25,
    "desc": "The Sudden Wealth (Earth Heavy)",
    "bazi": ["戊辰", "戊午", "戊戌", "癸丑"],
    "day_master": "戊",
    "gender": "男",
    "wang_shuai": "身极旺 (财星库)",
    "v_real": { "career": 1.0, "wealth": 7.0, "relationship": -5.0 },
    "physics_sources": {
        "self": { "stem_support": 9.0, "day_root": 8.0 }, 
        "wealth": { "base": 7.0 }, 
        "officer": { "base": 0.0 },
        "output": { "base": 0.0 },
        "resource": { "base": 0.0 }
    }
  }
]

def inject_and_verify():
    # 1. Load existing
    if os.path.exists(TARGET_FILE):
        with open(TARGET_FILE, "r") as f:
            cases = json.load(f)
    else:
        cases = []

    # Get existing IDs
    existing_ids = {c["id"] for c in cases}
    
    # 2. Append new cases if not present
    added_count = 0
    for new_case in NEW_CASES_DATA:
        if new_case["id"] not in existing_ids:
            cases.append(new_case)
            added_count += 1
        else:
            # Update existing?
            # Find and replace
            for i, c in enumerate(cases):
                if c["id"] == new_case["id"]:
                    cases[i] = new_case
                    break
    
    # 3. Save
    with open(TARGET_FILE, "w") as f:
        json.dump(cases, f, indent=2, ensure_ascii=False)
    
    print(f"Injected/Updated {len(NEW_CASES_DATA)} cases. Total cases: {len(cases)}")

    # 4. Verify (Run Quantum Engine)
    # Default Params as used in ui/pages/quantum_lab.py and scripts/calc_initial_rmse.py
    current_params = {
        "w_e_weight": 1.0,
        "f_yy_correction": 1.1,
        
        "w_career_officer": 0.8,
        "w_career_resource": 0.1,
        "w_career_output": 0.0,
        "k_control": 0.55,
        "k_buffer": 0.40,
        "k_mutiny": 1.8,
        
        "w_wealth_cai": 0.6,
        "w_wealth_output": 0.4,
        "k_capture": 0.0,
        "k_leak": 0.87,

        "w_rel_spouse": 0.35,
        "w_rel_self": 0.20,
        "w_rel_output": 0.15,
        "k_clash": 0.0,
        "k_pressure": 0.0, # Initial default might be 0.0 or 1.0? 
                           # Prompt says "不要修改任何当前的 V2.7 参数（K=1.2, P=1.0 等）".
                           # Wait, the prompt implies these ARE the current parameters.
                           # If I use 0.0 here, I might differ from what the user thinks is "current V2.7".
                           # Let's check golden_parameters.json if it exists, or infer from prompt.
                           # Prompt: "$K_{Clash}=1.2, K_{Pressure}=1.0$"
    }

    # Let's try to load golden_parameters.json
    golden_path = "/home/jin/bazi_predict/data/golden_parameters.json"
    if os.path.exists(golden_path):
         with open(golden_path, 'r') as f:
             current_params = json.load(f)
         print("Loaded golden_parameters.json")
    else:
        # Override with Prompt Defaults if golden not found
        current_params["K_Clash_Robbery"] = 1.2
        current_params["K_Pressure_Attack"] = 1.0 
        current_params["enable_mediation_exemption"] = True
        current_params["enable_structural_clash"] = True
        print("Using Prompt Defaults")

    engine = QuantumEngine(current_params)

    print("\n--- Blind Test Results (Cases 21-25) ---")
    
    # Define verification logic
    total_sq_error = 0
    count = 0
    
    for case in cases:
        if case["id"] not in [21, 22, 23, 24, 25]:
            continue
            
        ctx = {"year": "甲辰", "luck": "癸卯"} 
        res = engine.calculate_energy(case, ctx)
        v_real = case["v_real"]
        
        print(f"\nCase {case['id']}: {case['desc']}")
        print(f"  Real: {v_real}")
        print(f"  Pred: Career={res['career']}, Wealth={res['wealth']}, Rel={res['relationship']}")
        print(f"  Desc: {res['desc']}")
        
        # Check acceptance criteria
        # Case 21: Career
        if case['id'] == 21:
            if res['career'] <= -5.0:
                print("  [FAIL] Career too low (-5.0 or less). K_Pressure too heavy?")
            else:
                print("  [PASS] Career acceptable.")
                
        # Case 23: Relationship
        if case['id'] == 23:
             if res['relationship'] <= -8.0:
                 print("  [FAIL] Relationship too low (-8.0 or less).")
             else:
                 print("  [PASS] Relationship acceptable.")

        mse = (res['career'] - v_real['career'])**2 + \
              (res['wealth'] - v_real['wealth'])**2 + \
              (res['relationship'] - v_real['relationship'])**2
        rmse = (mse/3)**0.5
        print(f"  RMSE: {rmse:.2f}")
        
        total_sq_error += mse
        count += 3

    if count > 0:
        total_rmse = (total_sq_error / count)**0.5
        print(f"\nTotal RMSE for New Cases: {total_rmse:.4f}")

if __name__ == "__main__":
    inject_and_verify()
