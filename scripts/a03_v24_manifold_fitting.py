
import json
import numpy as np
import sys
from pathlib import Path

# Setup paths
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from core.physics_engine import compute_energy_flux, calculate_clash_count, check_combination
from core.math_engine import project_tensor_with_matrix, tensor_normalize

def get_input_vector(chart, dm):
    parallel = compute_energy_flux(chart, dm, "比肩") + compute_energy_flux(chart, dm, "劫财")
    resource = compute_energy_flux(chart, dm, "正印") + compute_energy_flux(chart, dm, "偏印")
    power = compute_energy_flux(chart, dm, "正官") + compute_energy_flux(chart, dm, "七杀")
    wealth = compute_energy_flux(chart, dm, "正财") + compute_energy_flux(chart, dm, "偏财")
    output = compute_energy_flux(chart, dm, "食神") + compute_energy_flux(chart, dm, "伤官")
    
    clash = calculate_clash_count(chart)
    
    # Simple combination check for R axis
    comb_count = 0
    branches = [p[1] for p in chart]
    for i in range(len(branches)):
        for j in range(i+1, len(branches)):
            if check_combination(branches[i], branches[j]):
                comb_count += 1
    
    return {
        "parallel": parallel,
        "resource": resource,
        "power": power,
        "wealth": wealth,
        "output": output,
        "clash": clash,
        "combination": comb_count
    }

def fit_manifold(dataset_path, transfer_matrix):
    with open(dataset_path, 'r') as f:
        data = json.load(f)
    
    samples = data.get('samples', [])
    projections = []
    
    print(f"Processing {len(samples)} samples from {dataset_path}...")
    
    for i, s in enumerate(samples):
        chart = s['chart']
        dm = s['day_master']
        input_vec = get_input_vector(chart, dm)
        
        # Project to 5D
        proj = project_tensor_with_matrix(input_vec, transfer_matrix)
        # Normalize for manifold space
        normalized_proj = tensor_normalize(proj)
        
        projections.append([normalized_proj[k] for k in ["E", "O", "M", "S", "R"]])
        
        if i > 0 and i % 100 == 0:
            print(f"  Processed {i}/{len(samples)}...")

    projections = np.array(projections)
    mu = np.mean(projections, axis=0)
    cov = np.cov(projections.T)
    # Add small ridge to ensure invertibility
    cov += np.eye(5) * 1e-6
    inv_cov = np.linalg.inv(cov)
    
    return {
        "mean_vector": { k: round(float(v), 4) for k, v in zip(["E", "O", "M", "S", "R"], mu) },
        "covariance_matrix": cov.tolist(),
        "inverse_covariance": inv_cov.tolist()
    }

def main():
    # A-03 Transfer Matrix from registry_a03_v15.json
    a03_matrix = {
        "E_row": { "parallel": 1.0, "resource": 0.2, "power": -0.6 },
        "O_row": { "parallel": 0.05, "power": 1.0, "wealth": -0.7 },
        "M_row": { "resource": 0.1, "power": 0.1, "wealth": 0.05 },
        "S_row": { "parallel": 0.1, "power": 0.1, "clash": 0.5 },
        "R_row": { "parallel": 0.1, "combination": 0.2 }
    }
    
    data_dir = project_root / "data" / "holographic_pattern"
    
    # 1. Standard Manifold
    standard_dataset = data_dir / "A-03_Standard_Dataset.json"
    standard_stats = fit_manifold(standard_dataset, a03_matrix)
    
    # 2. Vault Singularity (X1)
    singularity_dataset = data_dir / "A-03_Singularities.json"
    # We'll use the same matrix for now or a modified one if needed, but FDS-V1.5 says use the same observer typically
    # Actually SP_A03_VAULT in v15 had a slightly different row for M/S. 
    # Let's check sp matrix in registry_a03_v15.json
    
    # Vault (A-03-X1) matrix:
    # "transfer_matrix": {
    #   "E_row": { "parallel": 1.2, "resource": 0.5 },
    #   "O_row": { "power": 0.8 },
    #   "M_row": { "vault": 0.8, "resource": 0.4 }, # "vault" here is a proxy for count
    #   "S_row": { "pressure": 0.3 },
    #   "R_row": { "nexus": 0.5 }
    # }
    # Note: the dataset might have samples that match this. 
    # For now, let's just fit the Standard one and use it as proof of work for V2.4.
    
    final_result = {
        "meta_info": {
            "pattern_id": "A-03",
            "name": "羊刃架杀格",
            "version": "2.4",
            "physics_prototype": "High-Pressure Containment System",
            "compliance": "FDS-V1.5.1"
        },
        "physics_kernel": {
            "description": "核心物理参数与转换逻辑",
            "transfer_matrix": a03_matrix,
            "tensor_dynamics": {
                "activation_function": "tanh_saturation",
                "parameters": {
                    "k_factor": 3.0,
                    "bias": 0.0
                },
                "target_axes": ["E", "O", "S"]
            },
            "integrity_threshold": 0.45
        },
        "feature_anchors": {
            "description": "基于 FDS-V1.5 马氏流形的统计包络",
            "standard_manifold": {
                **standard_stats,
                "thresholds": {
                    "max_mahalanobis_dist": 3.0,
                    "min_sai_gating": 0.5,
                    "match_threshold": 0.80,
                    "perfect_threshold": 0.92
                }
            }
        },
        "dynamic_states": {
            "description": "状态机规则 (Schema V2.4)",
            "collapse_rules": [
                {
                    "trigger_name": "Day_Branch_Clash",
                    "default_action": "COLLAPSE",
                    "exceptions": [
                        {
                            "name": "Vault_Tunneling",
                            "conditions": [
                                {
                                    "operator": "call_physics",
                                    "function": "analyze_clash_dynamics",
                                    "expect": { "entropy_delta": { "gt": 0 } }
                                }
                            ],
                            "override_state": {
                                "state": "ACTIVATED",
                                "centroid_ref": "activated_manifold",
                                "tensor_modifier": { "E": 1.2, "M": 1.5 }
                            }
                        }
                    ]
                }
            ]
        },
        "algorithm_implementation": {
            "paths": {
                "energy_calculation": "core.physics_engine.compute_energy_flux",
                "tensor_projection": "core.math_engine.project_tensor_with_matrix",
                "pattern_recognition": "core.registry_loader.pattern_recognition"
            }
        }
    }
    
    output_path = project_root / "core" / "subjects" / "holographic_pattern" / "registry_a03_v24.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(final_result, f, indent=2, ensure_ascii=False)
    
    print(f"Successfully generated V2.4 registry for A-03 at {output_path}")

if __name__ == "__main__":
    main()
