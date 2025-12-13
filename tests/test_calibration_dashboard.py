
import pytest
import os
import json
import numpy as np
from core.quantum_engine import QuantumEngine

# --- Fixtures ---
@pytest.fixture
def calibration_data():
    base_dir = os.path.dirname(os.path.dirname(__file__))
    case_path = os.path.join(base_dir, 'data/calibration_cases.json')
    param_path = os.path.join(base_dir, 'data/golden_parameters.json')
    
    with open(case_path, 'r') as f:
        cases = json.load(f)
        
    with open(param_path, 'r') as f:
        # Flatten logic similar to script
        data = json.load(f)
        params = {}
        params.update(data.get("global_physics", {}))
        
        mw = data['macro_weights_w']
        params['w_career_officer'] = mw['W_Career_Officer']
        params['w_career_resource'] = mw['W_Career_Resource']
        params['w_career_output'] = mw['W_Career_Output']
        params['w_wealth_cai'] = mw['W_Wealth_Cai']
        params['w_wealth_output'] = mw['W_Wealth_Output']
        
        rw = data['relationship_weights']
        params['w_rel_spouse'] = rw['W_Rel_Spouse']
        params['w_rel_self'] = rw['W_Rel_Self']
        params['w_rel_output'] = rw['W_Rel_Output']
        
        k = data['conflict_and_conversion_k_factors']
        params['k_control'] = k['K_Control_Conversion']
        params['k_buffer'] = k['K_Buffer_Defense']
        params['k_mutiny'] = k['K_Mutiny_Betrayal']
        params['k_capture'] = k['K_Capture_Wealth']
        params['k_leak'] = k['K_Leak_Drain']
        params['k_clash'] = k['K_Clash_Robbery']
        params['k_pressure'] = k['K_Pressure_Attack']
        
    return {"cases": cases, "params": params}

# --- Tests ---

def test_global_rmse_calculation(calibration_data):
    """
    Test 1: Verify that we can calculate a Global RMSE for all cases without error.
    """
    cases = calibration_data['cases']
    params = calibration_data['params']
    
    engine = QuantumEngine(params)
    
    total_sq_error = 0
    count = 0
    
    for c in cases:
        # Context logic
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
        total_sq_error += sq_err
        count += 1
        
    global_rmse = np.sqrt(total_sq_error / count) if count > 0 else 0
    
    print(f"\nCalculated Global RMSE: {global_rmse}")
    
    # Assertions
    assert count == 20, "Should have processed all 20 cases"
    assert global_rmse > 0, "RMSE should be positive"
    assert global_rmse < 20, "RMSE should be within a reasonable range (not exploded)"

def test_parameter_sensitivity(calibration_data):
    """
    Test 2: Verify that changing parameters (slider logic) actually changes the RMSE.
    """
    cases = calibration_data['cases']
    base_params = calibration_data['params']
    
    # Run Baseline
    engine_base = QuantumEngine(base_params)
    rmse_base = 0
    # ... (Simplified loop for speed)
    total_sq_base = 0
    for c in cases:
        calc = engine_base.calculate_energy(c) # Simple static for sensitivity check
        target_v = c.get("v_real", {})
        err = calc['wealth'] - target_v.get('wealth', 0)
        total_sq_base += err**2
    rmse_base = np.sqrt(total_sq_base / len(cases))
    
    # Run Modified: Increase Wealth Weight significantly
    mod_params = base_params.copy()
    mod_params['w_wealth_cai'] = 1.0 # Max out
    mod_params['k_capture'] = 0.5    # Max out capture
    
    engine_mod = QuantumEngine(mod_params)
    total_sq_mod = 0
    for c in cases:
        calc = engine_mod.calculate_energy(c)
        target_v = c.get("v_real", {})
        err = calc['wealth'] - target_v.get('wealth', 0)
        total_sq_mod += err**2
    rmse_mod = np.sqrt(total_sq_mod / len(cases))
    
    print(f"\nBase RMSE (Wealth Only): {rmse_base}")
    print(f"Mod RMSE (Wealth Only): {rmse_mod}")
    
    assert rmse_base != rmse_mod, "Changing parameters should change the Error Metric"

def test_verdict_generation(calibration_data):
    """
    Test 3: Ensure narrative verdicts are generated for special cases.
    """
    cases = calibration_data['cases']
    params = calibration_data['params']
    engine = QuantumEngine(params)
    
    # Case 1 usually triggers K_Control
    case_1 = next(c for c in cases if c['id'] == 1)
    
    d_ctx = {"year": "壬申", "luck": "Simulated"}
    res = engine.calculate_energy(case_1, d_ctx)
    
    assert res['desc'] != "", "Should have a generated description"
    assert "K_Control" in res['desc'] or "能量转化" in res['desc'], "Case 1 should trigger Control Logic"
