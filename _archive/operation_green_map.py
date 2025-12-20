
import json
import math
import sys
import os

# Ensure we can import from core
sys.path.append(os.getcwd())

from core.engine_v88 import EngineV88 as QuantumEngine  # V8.8 Modular

def load_cases():
    with open('data/calibration_cases.json', 'r') as f:
        return json.load(f)

def calculate_rmse(cases, input_params):
    engine = QuantumEngine(input_params)
    total_sq_error = 0
    count = 0
    
    errors = {}

    for case in cases:
        pred = engine.calculate_energy(case)
        v_real = case.get('v_real', {})
        
        case_sq_error = 0
        case_count = 0
        
        for dim in ['career', 'wealth', 'relationship']:
            if dim in v_real:
                vr = v_real[dim]
                ep = pred.get(dim, 0)
                diff = vr - ep
                sq_err = diff ** 2
                
                total_sq_error += sq_err
                count += 1
                case_sq_error += sq_err
                case_count += 1
                
        if case_count > 0:
             errors[case['id']] = math.sqrt(case_sq_error / case_count)
        else:
             errors[case['id']] = 0

    global_rmse = math.sqrt(total_sq_error / count) if count > 0 else 0
    return global_rmse, errors, engine

def step_1_baseline(cases):
    print("\n--- STEP 1: BASELINE SCAN ---")
    # Default params based on code defaults
    params = {
        "K_Clash_Robbery": 1.2,
        "enable_mediation_exemption": True,
        "enable_structural_clash": False, # User asks to turn it on in Step 3
        "K_Broken_Collapse": 1.5,
        "T_Follow_Grid": -6.0,
        "T_Weak_Self": -2.0,
         # Add other defaults to be safe
        "w_e_weight": 1.0,
        "K_Mutiny_Betrayal": 1.8,
        "K_Leak_Drain": 0.87,
        "K_Burden_Wealth": 1.0,
        "K_Pressure_Attack": 1.0,
        "W_Career_Officer": 0.8,
        "W_Wealth_Cai": 0.6,
        "W_Rel_Spouse": 0.35,
        "W_Rel_Self": 0.20
    }
    
    rmse, errors, engine = calculate_rmse(cases, params)
    print(f"Global RMSE: {rmse:.4f}")
    
    # Find worst cases
    sorted_errors = sorted(errors.items(), key=lambda x: x[1], reverse=True)
    print("Top 3 Worst Cases:")
    for cid, err in sorted_errors[:3]:
        print(f"Case {cid}: RMSE={err:.2f}")

    # Specific check for user hypotheses
    pred_c1 = engine.calculate_energy(cases[0]) # Case 1
    pred_c18 = engine.calculate_energy(cases[17]) # Case 18 is index 17 (ID 18)
    
    print(f"Case 1 (Wealth): Real={cases[0]['v_real']['wealth']}, Pred={pred_c1['wealth']}")
    print(f"Case 18 (Rel): Real={cases[17]['v_real']['relationship']}, Pred={pred_c18['relationship']}")
    
    return params

def step_2_clash_balance(cases, base_params):
    print("\n--- STEP 2: CLASH BALANCE ---")
    best_k = 1.2
    best_exempt = True
    best_score = float('inf')
    
    # Grid search
    k_values = [0.8, 1.0, 1.2, 1.4, 1.5]
    exempt_options = [False, True]
    
    print(f"{'K_Clash':<8} | {'Exempt':<6} | {'C1(W) Err':<10} | {'C14(W) Err':<10} | {'Score (Min)'}")
    print("-" * 60)
    
    for k in k_values:
        for ex in exempt_options:
            p = base_params.copy()
            p['K_Clash_Robbery'] = k
            p['enable_mediation_exemption'] = ex
            
            # Run specific checks
            engine = QuantumEngine(p)
            
            # Case 1 (Wealth) - Should be GREEN (Low Error)
            c1 = next(c for c in cases if c['id'] == 1)
            p1 = engine.calculate_energy(c1)
            err1 = abs(c1['v_real']['wealth'] - p1['wealth'])
            
            # Case 14 (Wealth) - Should be GREEN (Low Error, meaning Prediction is LOW/Negative matching Real)
            # Case 14 Real is -7. Prediction should also be negative (penalty applied).
            c14 = next(c for c in cases if c['id'] == 14)
            p14 = engine.calculate_energy(c14)
            err14 = abs(c14['v_real']['wealth'] - p14['wealth'])
            
            score = err1 + err14 # Minimize combined error
            
            print(f"{k:<8} | {str(ex):<6} | {err1:<10.2f} | {err14:<10.2f} | {score:.2f}")
            
            if score < best_score:
                best_score = score
                best_k = k
                best_exempt = ex

    print(f"Winner: K={best_k}, Exempt={best_exempt}")
    base_params['K_Clash_Robbery'] = best_k
    base_params['enable_mediation_exemption'] = best_exempt
    return base_params

def step_3_structure(cases, base_params):
    print("\n--- STEP 3: STRUCTURE & COLLAPSE ---")
    
    # 3a. Enable Structural Clash
    base_params['enable_structural_clash'] = True
    
    engine = QuantumEngine(base_params)
    c18 = next(c for c in cases if c['id'] == 18)
    p18 = engine.calculate_energy(c18)
    err18 = abs(c18['v_real']['relationship'] - p18['relationship'])
    print(f"Case 18 (Relationship) with Structural Clash: Real={c18['v_real']['relationship']}, Pred={p18['relationship']}, Err={err18:.2f}")

    # 3b. Tune K_Broken
    print("\nTuning K_Broken for Case 8...")
    best_kb = 1.5
    best_err8 = float('inf')
    
    k_broken_vals = [1.5, 1.8, 2.0, 2.2, 2.5]
    c8 = next(c for c in cases if c['id'] == 8)
    
    for kb in k_broken_vals:
        p = base_params.copy()
        p['K_Broken_Collapse'] = kb
        engine = QuantumEngine(p)
        p8 = engine.calculate_energy(c8)
        
        # Average error across 3 dims for Case 8
        err = 0
        for d in ['career', 'wealth', 'relationship']:
            err += abs(c8['v_real'][d] - p8[d])
        avg_err = err / 3.0
        
        print(f"K_Broken={kb}: Case 8 Avg Err={avg_err:.2f} (Preds: {p8['career']}, {p8['wealth']}, {p8['relationship']})")
        
        if avg_err < best_err8:
             best_err8 = avg_err
             best_kb = kb
             
    base_params['K_Broken_Collapse'] = best_kb
    print(f"Winner: K_Broken={best_kb}")
    
    return base_params

def main():
    cases = load_cases()
    
    # Step 1
    params = step_1_baseline(cases)
    
    # Step 2
    params = step_2_clash_balance(cases, params)
    
    # Step 3
    params = step_3_structure(cases, params)
    
    # Final Validation
    print("\n--- FINAL SCORING ---")
    final_rmse, errors, _ = calculate_rmse(cases, params)
    print(f"Final Global RMSE: {final_rmse:.4f}")
    
    # Save
    with open('data/golden_parameters.json', 'w') as f:
        json.dump(params, f, indent=2)
    print("Saved to data/golden_parameters.json")

    # Check for remaining red flags
    print("\nRemaining Top Errors:")
    sorted_errors = sorted(errors.items(), key=lambda x: x[1], reverse=True)
    for cid, err in sorted_errors[:3]:
        print(f"Case {cid}: RMSE={err:.2f}")


if __name__ == "__main__":
    main()
