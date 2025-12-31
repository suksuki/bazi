
import sys
import os
import json
import numpy as np
from pathlib import Path
import logging

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from core.trinity.core.middleware.holographic_fitter import HolographicMatrixFitter
from core.physics_engine import compute_energy_flux, calculate_clash_count
from core.math_engine import tensor_normalize

def run_d01_fitting():
    logging.basicConfig(level=logging.INFO)
    print("🚀 Loading D-01 Seeds...")
    
    with open("scripts/d01_tier_a_seeds.json", "r", encoding="utf-8") as f:
        seeds = json.load(f)
    
    fitter = HolographicMatrixFitter(learning_rate=0.01, regularization=0.005)
    
    x_train = []
    y_train = []
    
    # D-01 Target Tensor (Standard Stable Wealth)
    # E: 0.85, O: 0.80, M: 0.95, S: 0.20, R: 0.50
    # Normalize it just in case
    target_tensor_dict = {'E': 0.85, 'O': 0.80, 'M': 0.95, 'S': 0.20, 'R': 0.50}
    target_tensor_norm = tensor_normalize(target_tensor_dict)
    y_target = np.array([target_tensor_norm[k] for k in fitter.OUTPUT_KEYS])
    
    print(f"DEBUG: Target Tensor: {target_tensor_norm}")
    print("🚀 Extracting 17D Features from seeds...")
    
    for s in seeds:
        chart = s["chart"]
        dm = chart[2][0]
        
        # 10 Ten Gods
        bj = compute_energy_flux(chart, dm, "比肩")
        jc = compute_energy_flux(chart, dm, "劫财")
        ss = compute_energy_flux(chart, dm, "食神")
        sg = compute_energy_flux(chart, dm, "伤官")
        pc = compute_energy_flux(chart, dm, "偏财")
        zc = compute_energy_flux(chart, dm, "正财")
        qs = compute_energy_flux(chart, dm, "七杀")
        zg = compute_energy_flux(chart, dm, "正官")
        py = compute_energy_flux(chart, dm, "偏印")
        zy = compute_energy_flux(chart, dm, "正印")
        
        # Interactions
        clash = calculate_clash_count(chart)
        comb = 0.0 # Placeholder
        
        # Legacy/Aggregates
        parallel = bj + jc
        resource = py + zy
        power = qs + zg
        wealth = pc + zc
        output = ss + sg
        
        vec = [
            bj, jc, ss, sg, pc, zc, qs, zg, py, zy,
            parallel, resource, power, wealth, output,
            clash, comb
        ]
        x_train.append(vec)
        y_train.append(y_target)
        
    x_train = np.array(x_train)
    y_train = np.array(y_train)
    
    print(f"🚀 Fitting D-01 Transfer Matrix (PGD with Axiom Locking)...")
    matrix = fitter.fit("D-01", x_train, y_train, epochs=3000)
    
    # Calculate Covariance for V1.5
    # Since our targets are all the same, covariance would be zero or noise-based if we had different targets.
    # For now, let's just use the fitted matrix outputs to see variability.
    y_pred = fitter._apply_saturation(x_train) @ matrix.T
    cov = fitter.calculate_covariance(y_pred)
    
    json_matrix = fitter.export_to_json_format(covariance=cov)
    
    print("\n--- FITTED D-01 TRANSFER MATRIX ---")
    print(json.dumps(json_matrix, indent=2, ensure_ascii=False))
    
    # Save to disk for Step 4
    with open("scripts/d01_standard_matrix.json", "w", encoding="utf-8") as f:
        json.dump(json_matrix, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    run_d01_fitting()
