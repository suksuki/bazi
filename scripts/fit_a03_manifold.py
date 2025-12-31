
import numpy as np
import json
import logging
from pathlib import Path
from core.trinity.core.middleware.holographic_fitter import HolographicMatrixFitter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("A03FinalRefit")

def generate_tiered_samples(n_a=500, n_x=50):
    """
    Step 2: Sample Stratification (Tier A & Tier X)
    """
    # [parallel, resource, power, wealth, output, clash, combination]
    
    # Tier A: Stable Fusion (Standard YRJS)
    samples_a = []
    labels_a = []
    for _ in range(n_a):
        parallel = np.random.normal(2.5, 0.4)
        power = np.random.normal(2.0, 0.3)
        resource = np.random.normal(0.6, 0.1)
        wealth = np.random.normal(0.2, 0.1)
        output = np.random.normal(0.2, 0.1)
        clash = np.random.normal(0.1, 0.1)
        combination = np.random.normal(0.4, 0.2)
        
        samples_a.append([parallel, resource, power, wealth, output, clash, combination])
        # Expected Standard Tensor
        labels_a.append([0.92, 0.88, 0.35, 0.50, 0.45]) # E, O, M, S, R

    # Tier X: Sudden Discharge / Tomb Opening (Activated YRJS)
    samples_x = []
    labels_x = []
    for _ in range(n_x):
        # Activated state often involves higher S and E spike
        parallel = np.random.normal(3.0, 0.5) 
        power = np.random.normal(2.5, 0.4)
        clash = np.random.normal(1.5, 0.3) # Heavy clash trigger
        combination = np.random.normal(0.2, 0.1) # Less stabilizer
        
        samples_x.append([parallel, 0.3, power, 0.1, 0.3, clash, combination])
        # Expected Activated Tensor (High E, High S spike, O slightly destabilized)
        labels_x.append([0.98, 0.75, 0.40, 0.85, 0.30])
        
    return np.array(samples_a), np.array(labels_a), np.array(samples_x), np.array(labels_x)

def main():
    # Phase 2: Mining
    x_train_a, y_train_a, x_train_x, y_train_x = generate_tiered_samples()
    
    # Phase 1: Initialize with Phase 1 Weights
    fitter = HolographicMatrixFitter(learning_rate=0.01, regularization=0.01)
    
    # Manual Override Initial Matrix (Phase 1 Instruction)
    # OUTPUT_KEYS = ["E", "O", "M", "S", "R"]
    # INPUT_KEYS = ["parallel", "resource", "power", "wealth", "output", "clash", "combination"]
    init_matrix = np.zeros((5, 7))
    init_matrix[0, 0] = 1.5   # E_row, parallel
    init_matrix[1, 2] = 1.2   # O_row, power
    init_matrix[2, 3] = -0.5  # M_row, wealth
    init_matrix[3, 5] = 0.8   # S_row, clash
    init_matrix[4, 6] = 0.3   # R_row, combination
    fitter.transfer_matrix = init_matrix

    # Phase 3: Matrix Fitting (Targeting Tier A consistency)
    matrix = fitter.fit("A-03", x_train_a, y_train_a, epochs=2000)
    
    # Phase 4: Manifold Construction
    def construct_manifold(samples, fitter, matrix, desc, thresholds):
        proj = fitter._apply_saturation(samples) @ matrix.T
        mu = np.mean(proj, axis=0)
        cov = np.cov(proj.T)
        inv_cov = np.linalg.pinv(cov)
        
        return {
            "description": desc,
            "mean_vector": { k: round(float(v), 4) for k, v in zip(["E", "O", "M", "S", "R"], mu) },
            "covariance_matrix": cov.tolist(),
            "inverse_covariance": inv_cov.tolist(),
            "thresholds": thresholds
        }

    standard_manifold = construct_manifold(
        x_train_a, fitter, matrix, 
        "标准态流形 (Standard Manifold) - Tokamak Stable",
        {"max_mahalanobis_dist": 3.0, "min_sai_gating": 0.5, "match_threshold": 0.75, "perfect_threshold": 0.92}
    )
    
    activated_manifold = construct_manifold(
        x_train_x, fitter, matrix,
        "激活态流形 (Activated Manifold) - Sudden Discharge",
        {"max_mahalanobis_dist": 4.5, "min_sai_gating": 0.8, "match_threshold": 0.65, "perfect_threshold": 0.9}
    )
    
    # Phase 6: Final Package
    kernel = fitter.export_to_json_format()
    kernel["status"] = "✅ Fitted (FDS-V1.5 Final Level)"
    
    registry_snippet = {
        "physics_kernel": kernel,
        "feature_anchors": {
            "description": "FDS-V1.5 Precision Manifold (Mahalanobis Envelopes)",
            "standard_manifold": standard_manifold,
            "activated_manifold": activated_manifold
        }
    }
    
    with open("a03_final_registry.json", "w") as f:
        json.dump(registry_snippet, f, indent=2, ensure_ascii=False)
        
    logger.info("✅ Operation A-03 Precision Refit COMPLETE.")

if __name__ == "__main__":
    main()
