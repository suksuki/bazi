import json
import numpy as np
import os
from sklearn.covariance import MinCovDet

INPUT_FILE = "core/subjects/holographic_pattern/mining_cache/a01_tier_a_seeds_v151.json"
OUTPUT_FILE = "core/subjects/holographic_pattern/matrix_cache/a01_matrix_v151.json"
PROTOTYPE_FILE = "scripts/a01_step1_prototype.json" # Reusing prototype for base logic

print("📉 [A-01 FITTING V1.5.1] Calculating Crystalline Lens & Manifold...")

# 1. Load Data
with open(INPUT_FILE, 'r') as f:
    mining_data = json.load(f)
    seeds = mining_data['seeds'] # Top 500 sorted by y_true

# 2. Extract Vectors (5D Tensor)
vectors = np.array([[s['tensor'][axis] for axis in 'EOMSR'] for s in seeds])
mean_vector = np.mean(vectors, axis=0)
print(f"   Mean Vector (E, O, M, S, R): {mean_vector}")

# 3. Robust Covariance (MCD)
# Using robust estimation to ignore outliers even within Tier A
mcd = MinCovDet(random_state=42).fit(vectors)
cov_matrix = mcd.covariance_
print(f"   Covariance Matrix:\n{cov_matrix}")

# 4. Define Transfer Matrix V2.5 (Physics Constraints Enforcement)
# This defines the "Crystal Lens" - how Ten Gods map to Space-Time 5D
transfer_matrix = {
    # Energy: Day Master (Self) + Resource (Support)
    "E_row": {
        "Day_Master": 1.2,
        "Resource": 1.5,         # 印星强力护身 (Strong Support)
        "Indirect_Resource": 0.8
    },
    # Order: Direct Officer (The King) - Purity Constraint
    "O_row": {
        "Direct_Officer": 2.0,   # [CORE] Max Order contribution
        "Seven_Killings": -1.5,  # [PURITY] Impurity reduces Order
        "Hurting_Officer": -2.5, # [AXIOM] Hurting Officer DESTROYS Order (Negative Weight)
        "Friend": 0.5            
    },
    # Matter: Wealth supports Officer
    "M_row": {
        "Direct_Wealth": 1.2,    # 财生官
        "Indirect_Wealth": 0.8
    },
    # Entropy: Hurting Officer (The Enemy) - Sensitivity Constraint
    "S_row": {
        "Hurting_Officer": 3.0,  # [DANGER] Extreme sensitivity to Hurting Officer on S-axis
        "Seven_Killings": 1.0,   # Seven Killings adds Chaos
        "Clash": 1.5             # Physical Clash adds Entropy
    },
    # Relation: Networking
    "R_row": {
        "Direct_Wealth": 0.5,
        "Combination": 1.0       # 有情之合
    }
}

# 5. Build Matrix Object (Pre-Registry)
matrix_data = {
    "pattern_id": "A-01",
    "step": "Step 3 - Matrix Fitting (V1.5.1)",
    "meta_info": {
        "category": "POWER",        # Enum Compliant
        "display_name": "Direct Officer", # Enum Compliant
        "chinese_name": "正官格",
        "version": "1.5.1",
        "compliance": "FDS-V1.5.1"
    },
    "physics_kernel": {
        "description": "Crystalline Lens (High Order, High Sensitivity to S)",
        "transfer_matrix": transfer_matrix,
        "tensor_dynamics": {
            "activation_function": "sigmoid_variant",
            "parameters": { "k_factor": 2.0 }  # Stiff response (Crystal-like)
        },
        "integrity_threshold": 0.65
    },
    "feature_anchors": {
        "description": "Standard Crystalline Manifold",
        "standard_manifold": {
            "mean_vector": dict(zip('EOMSR', mean_vector.tolist())),
            "covariance_matrix": cov_matrix.tolist(),
            "thresholds": {
                "max_mahalanobis_dist": 2.5
            }
        }
    }
}

# 6. Save
os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    json.dump(matrix_data, f, indent=2, ensure_ascii=False)

print(f"✅ Matrix Lens Generated: {OUTPUT_FILE}")
print(f"   - O-Axis Purity: High (DO=+2.0, HO=-2.5)")
print(f"   - S-Axis Sensitivity: Extreme (HO=+3.0)")
