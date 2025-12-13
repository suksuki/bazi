
import sys
import os
import json
import numpy as np
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from core.quantum_engine import QuantumEngine

def load_cases():
    path = os.path.join(os.path.dirname(__file__), "../data/calibration_cases.json")
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return []

def load_golden_params():
    path = os.path.join(os.path.dirname(__file__), "../data/golden_parameters.json")
    if os.path.exists(path):
        with open(path, "r") as f:
            data = json.load(f)
            # Flatten or map to expected format if necessary
            # The QuantumEngine expects a flat dict of key-values as seen in UI.
            # We need to reconstruct the flat dict from the JSON structure
            flat = {}
            flat.update(data.get("global_physics", {}))
            
            # Key mapping based on UI logic
            # ui: w_e_val -> w_e_weight
            # json: w_e_weight
            
            # ui: st.sidebar.slider("We: ...", value=...) -> key "w_e_weight" in current_params
            
            # Map JSON keys to Engine keys
            # The JSON structure groups them.
            
            # global_physics
            flat['w_e_weight'] = data['global_physics']['w_e_weight']
            flat['f_yy_correction'] = data['global_physics']['f_yy_correction']
            
            # macro_weights_w (Career/Wealth)
            mw = data['macro_weights_w']
            flat['w_career_officer'] = mw['W_Career_Officer']
            flat['w_career_resource'] = mw['W_Career_Resource']
            flat['w_career_output'] = mw['W_Career_Output']
            flat['w_wealth_cai'] = mw['W_Wealth_Cai']
            flat['w_wealth_output'] = mw['W_Wealth_Output']
            
            # relationship_weights
            rw = data['relationship_weights']
            flat['w_rel_spouse'] = rw['W_Rel_Spouse']
            flat['w_rel_self'] = rw['W_Rel_Self']
            flat['w_rel_output'] = rw['W_Rel_Output']
            
            # conflict_and_conversion_k_factors
            k = data['conflict_and_conversion_k_factors']
            flat['k_control'] = k['K_Control_Conversion']
            flat['k_buffer'] = k['K_Buffer_Defense']
            flat['k_mutiny'] = k['K_Mutiny_Betrayal']
            flat['k_capture'] = k['K_Capture_Wealth']
            flat['k_leak'] = k['K_Leak_Drain']
            flat['k_clash'] = k['K_Clash_Robbery']
            flat['k_pressure'] = k['K_Pressure_Attack'] # Note: UI uses k_press/k_pressure logic
            # UI dict uses 'k_pressure' in key (line 73)
            
            return flat
    return {}

def calculate():
    cases = load_cases()
    params = load_golden_params()
    
    print(f"Loaded {len(cases)} cases.")
    print(f"Loaded Params: {params}")
    
    engine = QuantumEngine(params)
    
    total_sq_error = 0
    count = 0
    
    for c in cases:
        d_ctx = {"year": "2024", "luck": "default"}
        presets = c.get("dynamic_checks", [])
        target_v = c.get("v_real", {})
        
        if presets:
            p = presets[0]
            d_ctx = {"year": p['year'], "luck": p['luck']}
            if 'v_real_dynamic' in p:
                target_v = p['v_real_dynamic']
                
        calc = engine.calculate_energy(c, d_ctx)
        
        err_c = calc['career'] - target_v.get('career', 0)
        err_w = calc['wealth'] - target_v.get('wealth', 0)
        err_r = calc['relationship'] - target_v.get('relationship', 0)
        
        sq_err = (err_c**2 + err_w**2 + err_r**2) / 3
        rmse_c = np.sqrt(sq_err)
        
        total_sq_error += sq_err
        count += 1
        
        print(f"Case {c['id']} RMSE: {rmse_c:.4f} (Desc: {calc['desc']})")
        
    global_rmse = np.sqrt(total_sq_error / count) if count > 0 else 0
    print(f"\nGlobal RMSE: {global_rmse:.4f}")

if __name__ == "__main__":
    calculate()
