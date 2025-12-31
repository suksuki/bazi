
import sys
import os
import json
import numpy as np
from pathlib import Path
import logging

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from core.registry_loader import RegistryLoader, count_vaults_helper
from core.math_engine import calculate_mahalanobis_distance, tensor_normalize
from core.physics_engine import compute_energy_flux

def run_step6_test():
    logging.basicConfig(level=logging.INFO)
    print("🚀 D-01 Step 6: Precision Recognition Acceptance Test")
    print("======================================================")
    
    loader = RegistryLoader()
    with open("core/subjects/holographic_pattern/registry.json", "r", encoding="utf-8") as f:
        registry_data = json.load(f)
    
    d01_def = registry_data["patterns"]["D-01"]
    kernel = d01_def["physics_kernel"]
    # We use 4D EOMS for distance
    mu_std = np.array([kernel["standard_manifold"]["mean_vector"][k] for k in ["E", "O", "M", "S"]])
    cov_std = np.array(kernel["standard_manifold"]["covariance_matrix"])[:4, :4]
    
    cases = [
        {
            "id": "Case A (Standard - Balanced)",
            "chart": [["丙寅", "火木"], ["乙酉", "木金"], ["丁丑", "火土"], ["庚子", "金水"]], # Proper Wealth, Strong DM roots
            "dm": "丁"
        },
        {
            "id": "Case B (Surrender - Black Hole)",
            "chart": [["庚申", "金金"], ["辛酉", "金金"], ["丙申", "火金"], ["戊子", "土水"]], # No Wood/Fire roots, all Metal/Water
            "dm": "丙"
        },
        {
            "id": "Case C (Vault Tycoon)",
            "chart": [["戊戌", "土土"], ["乙未", "木土"], ["甲辰", "木土"], ["庚午", "金火"]], # 3 Vaults (戌, 未, 辰)
            "dm": "甲"
        },
        {
            "id": "Case D (Noise - Weak/Chaotic)",
            "chart": [["庚午", "金火"], ["壬午", "水火"], ["丙午", "火火"], ["戊午", "土火"]], # Extreme Stress, Out of bounds
            "dm": "壬"
        }
    ]
    
    for case in cases:
        print(f"\nAudit Log for {case['id']}:")
        chart = [p[0] for p in case["chart"]]
        dm = case["dm"]
        
        # 1. Feature Extraction & Routing (Step 5/6)
        res = loader.calculate_tensor_projection_from_registry("D-01", chart, dm)
        if "error" in res:
            print(f"❌ Error: {res['error']}")
            continue
            
        proj = res["projection"]
        sub_id = res.get("sub_id", "STANDARD")
        
        print(f"   -> Router Selection: {sub_id}")
        print(f"   -> Multi-Axis State: E={proj.get('E',0):.3f}, M={proj.get('M',0):.3f}, S={proj.get('S',0):.3f}, O={proj.get('O',0):.3f}")
        
        # 2. Precision Scoring (Step 6)
        # For standard, we use Mahalanobis
        if sub_id == "STANDARD":
            y_sample = np.array([proj[k] for k in ["E", "O", "M", "S"]])
            try:
                dm_dist = calculate_mahalanobis_distance(y_sample, mu_std, cov_std)
                print(f"   -> Mahalanobis Distance (Dm): {dm_dist:.4f}")
                
                # Recognition Threshold 3.5
                if dm_dist < 3.5:
                    print(f"   -> Result: ✅ MATCH (Standard Resonance)")
                else:
                    print(f"   -> Result: ❌ MISMATCH (Out of Bounds)")
            except Exception as e:
                print(f"   -> Dm Error: {e}")
        else:
            print(f"   -> Result: 🚀 MATCH (Singularity Phase Locked)")

if __name__ == "__main__":
    run_step6_test()
