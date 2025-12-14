
import json
import math
import os
import sys

# Add repository root to path so we can import core
sys.path.append("/home/jin/bazi_predict")

from core.engine_v88 import EngineV88 as QuantumEngine  # V8.8 Modular

def load_cases():
    path = "/home/jin/bazi_predict/data/calibration_cases.json"
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return []

def calculate_initial_rmse():
    cases = load_cases()
    
    # Default parameters as seen in ui/pages/quantum_lab.py
    # Lines 27-52 define defaults
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
        "k_pressure": 0.0 # Note: In code it was k_press variable initialized to 0.0. Key in dict is k_pressure?
        # Let's check line 73 of quantum_lab.py: "k_pressure": k_press
    }
    
    engine = QuantumEngine(current_params)
    
    total_sq_error = 0
    count = 0
    
    print(f"Calculating RMSE for {len(cases)} cases...")
    
    for case in cases:
        # Use default context if no dynamic checks override (or use Case's first dynamic check if available? 
        # The prompt implies '20 cases', usually we calibrate against static V_real unless dynamic is specified for that case verification.
        # However, some cases like Case 1 have a dynamic check that defines V_real_dynamic.
        # But usually calibration is done on a consistent basis. 
        # In quantum_lab.py (lines 241-245), if the user selects a year matching a preset, it switches to dynamic V_real.
        # For global calibration, we should probably stick to the primary V_real (static) for consistency, 
        # UNLESS the case is specifically a "dynamic verification case".
        # Case 1 desc is "月令 We 校验", V_real is set. 
        # Text says "Use existing cases", most have V_real.
        # I will use the top-level V_real for all cases for the "Global Calibration" unless otherwise specified.
        # Actually, if I look at Case 1, V_real is {6, 5, 4}. Dynamic is {-2, 8, 3}.
        # Standard calibration usually targets the base chart (Static).
        
        # Calculate Energy (Static Context)
        # Context needs 'year' and 'luck'. For static, these might matterless if using base chart, 
        # but QuantumEngine might require them.
        # I'll provide dummy or current year.
        ctx = {"year": "甲辰", "luck": "癸卯"} 
        
        res = engine.calculate_energy(case, ctx)
        
        v_real = case["v_real"]
        
        # Calculate errors
        diff_career = res['career'] - v_real['career']
        diff_wealth = res['wealth'] - v_real['wealth']
        diff_rel = res['relationship'] - v_real['relationship']
        
        total_sq_error += diff_career**2 + diff_wealth**2 + diff_rel**2
        count += 3 # 3 dimensions
        
    rmse = math.sqrt(total_sq_error / count)
    print(f"Initial RMSE: {rmse:.4f}")

if __name__ == "__main__":
    calculate_initial_rmse()
