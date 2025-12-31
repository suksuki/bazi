import json
import numpy as np
import os
from sklearn.covariance import MinCovDet

INPUT_FILE = "core/subjects/holographic_pattern/mining_cache/b02_tier_a_seeds_v151.json"
OUTPUT_FILE = "core/subjects/holographic_pattern/matrix_cache/b02_matrix_v151.json"

print("📉 [B-02 FITTING V1.5.1] Calculating Dissipative Lens & Manifold (Reactor Design)...")

# 1. Load Data
with open(INPUT_FILE, 'r') as f:
    mining_data = json.load(f)
    seeds = mining_data['seeds'] # Top ~10k

# 2. Extract Vectors
vectors = np.array([[s['tensor'][axis] for axis in 'EOMSR'] for s in seeds])
mean_vector = np.mean(vectors, axis=0)
print(f"   Mean Vector (E, O, M, S, R): {mean_vector}")

# 3. Robust Covariance (MCD)
mcd = MinCovDet(random_state=42).fit(vectors)
cov_matrix = mcd.covariance_
print(f"   Covariance Matrix:\n{cov_matrix}")

# 4. Define Transfer Matrix V2.5 (Dissipative Physics Constraints)
# The Engine + The Reactor + The Coolant
transfer_matrix = {
    # Energy: Day Master (Self) + Resource (Battery)
    "E_row": {
        "Day_Master": 1.2,
        "Resource": 1.2,          # Sourced from Prototype
        "Indirect_Resource": 0.8
    },
    # Order/Output: Hurting Officer (The Output Engine)
    "O_row": {
        "Hurting_Officer": 2.5,   # [CORE] Massive Output
        "Eating_God": 1.0,        # Smooth Output
        "Direct_Officer": -1.5,   # Rejection of Static Order
        "Seven_Killings": 0.5     # Aggressive Output
    },
    # Matter: Wealth transforms Chaos (The Condenser)
    "M_row": {
        "Direct_Wealth": 1.5,     # [KEY] Transforms S to M (Cooling)
        "Indirect_Wealth": 1.2
    },
    # Stress: The Reactor Core (Chaos & Pressure)
    "S_row": {
        "Hurting_Officer": 2.0,   # Intrinsic Stress/Instability
        "Direct_Officer": 3.0,    # [IGNITION] HO + DO = EXPLOSIVE STRESS
        "Seven_Killings": 1.5,
        "Resource": -2.0,         # [COOLANT 1] Resource suppresses HO (Stress Reduction)
        "Direct_Wealth": -1.0     # [COOLANT 2] Wealth drains HO (Stress Diversion)
    },
    # Relation: Networking
    "R_row": {
        "Friend": 0.5,            # Friends fuel HO
        "Rob_Wealth": 0.5
    }
}

# 5. Build Matrix Object
matrix_data = {
    "pattern_id": "B-02",
    "step": "Step 3 - Matrix Fitting (V1.5.1)",
    "meta_info": {
        "category": "TALENT",       # [Compliance] Enum
        "display_name": "Hurting Officer", # [Compliance]
        "chinese_name": "伤官格",
        "version": "1.5.1",
        "compliance": "FDS-V1.5.1",
        "physics_type": "Dissipative Structure"
    },
    "physics_kernel": {
        "description": "Dissipative Lens. High Output, High Reactivity (S). Requires Cooling (M/Resource).",
        "transfer_matrix": transfer_matrix,
        "tensor_dynamics": {
            "activation_function": "tanh_variant", # More dynamic response than sigmoid
            "parameters": { "k_factor": 1.5 } 
        },
        "integrity_threshold": 0.60 # Lower threshold for dynamic structures
    },
    "feature_anchors": {
        "description": "Standard Dissipative Manifold",
        "standard_manifold": {
            "mean_vector": dict(zip('EOMSR', mean_vector.tolist())),
            "covariance_matrix": cov_matrix.tolist(),
            "thresholds": {
                "max_mahalanobis_dist": 3.0 # Wider tolerance for chaos
            }
        }
    }
}

# 6. Save
os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    json.dump(matrix_data, f, indent=2, ensure_ascii=False)

print(f"✅ Reactor Matrix Generated: {OUTPUT_FILE}")
print(f"   - O-Axis Engine: Hurting Officer (+2.5)")
print(f"   - S-Axis Ignition: Direct Officer (+3.0)")
print(f"   - S-Axis Coolant: Resource (-2.0), Wealth (-1.0)")
