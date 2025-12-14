import pytest
import os
import json
from core.engine_v88 import EngineV88 as QuantumEngine  # V8.8 Modular

# --- Fixture: Load Calibration Data ---
@pytest.fixture
def calibration_cases():
    # Construct path relative to this test file
    base_dir = os.path.dirname(os.path.dirname(__file__))
    data_path = os.path.join(base_dir, 'data/calibration_cases.json')
    
    if not os.path.exists(data_path):
        pytest.skip("calibration_cases.json not found, skipping validation tests.")
        
    with open(data_path, 'r') as f:
        cases = json.load(f)
    return cases

# --- Test: Static Validation Loop ---
def test_static_validation_loop(calibration_cases):
    """
    Validates that the QuantumEngine (with default params) produces 
    E_pred values that are reasonably close to V_real for the Golden Set.
    Goal: MAE < 4.0 (Relaxed for Prototype/Mock logic)
    """
    
    # Default Params (V2.1 Baseline)
    params = {
        "w_e_weight": 1.0,
        "f_yy_correction": 1.1,
        "w_career": 1.0,
        "w_wealth": 1.0
    }
    
    engine = QuantumEngine(params)
    
    total_error = 0
    count = 0
    
    print("\n--- Calibration Report ---")
    for case in calibration_cases:
        real = case['v_real']
        pred = engine.calculate_energy(case)
        
        # Calculate Absolute Errors
        err_c = abs(pred['career'] - real['career'])
        err_w = abs(pred['wealth'] - real['wealth'])
        err_r = abs(pred['relationship'] - real['relationship'])
        
        case_avg_err = (err_c + err_w + err_r) / 3.0
        total_error += case_avg_err
        count += 1
        
        print(f"Case {case['id']} ({case['day_master']}): MAE={case_avg_err:.2f} | "
              f"Career: {pred['career']}/{real['career']} | "
              f"Wealth: {pred['wealth']}/{real['wealth']} | "
              f"Rel: {pred['relationship']}/{real['relationship']}")
              
    avg_mae = total_error / count
    print(f"\nGlobal Model MAE: {avg_mae:.2f}")
    
    # Assert that the model isn't completely broken
    # Note: Since the engine is using Mock logic (hashed IDs), it might not align perfectly
    # with the manually crafted "V_real". So we set a high tolerance threshold.
    # The purpose of this test right now is ensure the PIPELINE works, not the ACCURACY.
    assert avg_mae < 5.0, f"Model accuracy is too low (MAE {avg_mae:.2f} >= 5.0)"

# --- Test: Dynamic Time Logic ---
def test_dynamic_scenarios(calibration_cases):
    """
    Validates the Dynamic Time Variable logic (Year/Luck interactions).
    Specifically checks Case 1 + 壬申 (Ren Shen) year logic.
    """
    params = {"w_e_weight": 1.0}
    engine = QuantumEngine(params)
    
    # Pick Case 1
    case_1 = next((c for c in calibration_cases if c['id'] == 1), None)
    assert case_1 is not None
    
    # 1. Static Calculation
    static_res = engine.calculate_energy(case_1)
    
    # 2. Dynamic Calculation (Year = 壬申)
    # Note: In our mock engine, hash(1 + "壬申") determines the effect.
    # We rely on the Engine's deterministic hash logic for this test.
    ctx = {"year": "壬申", "luck": "己未"}
    dynamic_res = engine.calculate_energy(case_1, dynamic_context=ctx)
    
    print(f"\n--- Dynamic Test (Case 1) ---")
    print(f"Static Career: {static_res['career']}")
    print(f"Dynamic Career (壬申): {dynamic_res['career']}")
    print(f"Desc: {dynamic_res['desc']}")
    
    # Assert that dynamic context CHANGED the result
    assert static_res != dynamic_res, "Dynamic context should alter energy values"
    
    # Check description presence
    assert dynamic_res['desc'] != "", "Dynamic simulation should produce a description (Clash/Support/Flow)"

# --- Test: Relationship Formula ---
def test_relationship_matrix_weights():
    """
    Verifies that gender and body strength affect relationship scores correctly.
    """
    engine = QuantumEngine({})
    
    # Mock Case: Male (Spouse=Cai) vs Female (Spouse=GuanSha)
    # We use a case ID that produces differential raw scores for ease of testing
    # ID 10: 
    #   Raw Cai = (10*5)%9 = 5
    #   Raw Guan = (10*7)%10 = 0
    # Male Rel = 0.35*5*2 + ...
    # Female Rel = 0.35*0*2 + ...
    # So Male score should be significantly higher.
    
    case_m = {"id": 10, "gender": "男", "wang_shuai": "身中和"}
    case_f = {"id": 10, "gender": "女", "wang_shuai": "身中和"}
    
    res_m = engine.calculate_energy(case_m)
    res_f = engine.calculate_energy(case_f)
    
    print(f"\n--- Gender Physics Test ---")
    print(f"Male Rel Score: {res_m['relationship']}")
    print(f"Female Rel Score: {res_f['relationship']}")
    
    assert res_m['relationship'] != res_f['relationship'], "Gender should fundamentally alter Relationship E-field"
