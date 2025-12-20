
import json
import os
import sys

# Ensure we can import from core
sys.path.append(os.getcwd())

from core.engine_v88 import EngineV88 as QuantumEngine  # V8.8 Modular

def main():
    # 1. Load Parameters
    try:
        with open('data/golden_parameters.json', 'r') as f:
            params = json.load(f)
    except FileNotFoundError:
        print("Error: golden_parameters.json not found.")
        return

    # 2. Load Cases
    try:
        with open('data/calibration_cases.json', 'r') as f:
            cases = json.load(f)
    except FileNotFoundError:
        print("Error: calibration_cases.json not found.")
        return

    # 3. Analyze
    engine = QuantumEngine(params)
    
    results = []

    for case in cases:
        # Run prediction
        pred = engine.calculate_energy(case)
        
        v_real = case.get('v_real', {})
        
        # Compare Dimensions
        max_delta = -1.0
        max_dim = ""
        v_r_val = 0
        e_p_val = 0
        
        for dim in ['career', 'wealth', 'relationship']:
            if dim in v_real:
                vr = v_real[dim]
                ep = pred.get(dim, 0)
                delta = abs(vr - ep)
                
                if delta > max_delta:
                    max_delta = delta
                    max_dim = dim
                    v_r_val = vr
                    e_p_val = ep
        
        # Store result
        results.append({
            "id": case['id'],
            "dim": max_dim,
            "v_real": v_r_val,
            "e_pred": e_p_val,
            "delta": max_delta,
            "desc": case.get('desc', 'N/A'),
            "bazi": case.get('bazi', []),
            "wang_shuai": case.get('wang_shuai', 'N/A')
        })

    # 4. Sort and Top 3
    results.sort(key=lambda x: x['delta'], reverse=True)
    top_3 = results[:3]

    # 5. Output Table
    print("| 案例 No. | 宏观相维度 | 专家标签 (V_real) | 模型预测 (E_pred) | 偏差 (|Δ|) | 核心物理冲突 |")
    print("|:---|:---|:---|:---|:---|:---|")
    
    dim_map = {
        "career": "事业",
        "wealth": "财富",
        "relationship": "感情"
    }

    for res in top_3:
        # Construct conflict description
        conflict = res['desc']
        # Try to add more context if possible
        # e.g., if weak DM and strong officer
        
        print(f"| Case {res['id']} | {dim_map.get(res['dim'], res['dim'])} | {res['v_real']} | {res['e_pred']} | {res['delta']:.1f} | {conflict} |")

if __name__ == "__main__":
    main()
