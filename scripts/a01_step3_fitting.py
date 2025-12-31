import json
import numpy as np
import os
from sklearn.covariance import MinCovDet

INPUT_FILE = "core/subjects/holographic_pattern/mining_cache/a01_tier_a_seeds.json"
OUTPUT_FILE = "core/subjects/holographic_pattern/registry_fragment_a01.json"
PROTOTYPE_FILE = "scripts/a01_step1_prototype.json"

print("📉 [A-01 FITTING] Calculating Crystalline Manifold...")

# 1. Load Prototype & Seeds
with open(PROTOTYPE_FILE, 'r') as f:
    prototype = json.load(f)

with open(INPUT_FILE, 'r') as f:
    mining_data = json.load(f)
    seeds = mining_data['seeds'] # Top 500

# 2. Extract Vectors
vectors = np.array([[s['tensor'][axis] for axis in 'EOMSR'] for s in seeds])
mean_vector = np.mean(vectors, axis=0)
print(f"   Mean Vector: {mean_vector}")

# 3. Robust Covariance (MCD)
# Crystalline structures are very sensitive to noise, using robust estimation
mcd = MinCovDet(random_state=42).fit(vectors)
cov_matrix = mcd.covariance_
print(f"   Covariance Matrix:\n{cov_matrix}")

# 4. Define Transfer Matrix V2.5 (The Physics Laws)
# This defines how Ten Gods map to 5D Tensors for A-01
transfer_matrix = {
    # Energy: Day Master (Self) + Resource (Support)
    "E_row": {
        "Day_Master": 1.2,
        "Resource": 1.5,         # 印星强力护身
        "Indirect_Resource": 0.8
    },
    # Order: Direct Officer (The King)
    "O_row": {
        "Direct_Officer": 2.0,   # [CORE] 极其强烈的秩序转化
        "Seven_Killings": -1.5,  # [PURITY] 七杀是杂质，作为负Order
        "Friend": 0.5            # 比肩助威
    },
    # Matter: Wealth supports Officer
    "M_row": {
        "Direct_Wealth": 1.2,    # 财生官
        "Indirect_Wealth": 0.8
    },
    # Entropy: Hurting Officer (The Enemy)
    "S_row": {
        "Hurting_Officer": 2.5,  # [DANGER] 伤官极大幅度增加熵 (破坏晶体)
        "Seven_Killings": 1.0,   # 七杀也增加熵
        "Clash": 1.5
    },
    # Relation: Networking
    "R_row": {
        "Direct_Wealth": 0.5,
        "Combination": 1.0       # 有情之合
    }
}

# 5. Build Registry Fragment
registry_entry = {
    "id": "A-01",
    "name": "Direct Officer Pattern (正官格)",
    "version": "2.5",
    "active": True,
    "meta_info": {
        "pattern_id": "A-01",
        "name": "Direct Officer (The Judge)",
        "display_name": "Direct Officer",
        "chinese_name": "正官格",
        "category": "POWER",
        "physics_prototype": "Crystalline Lattice / Low Entropy",
        "description": "高度秩序化的晶体结构，以正官为核心，财印相辅。排斥伤官杂质。",
        "compliance": "FDS-V1.5.1 (Genesis Protocol)",
        "calibration_date": "2025-12-31",
        "mining_stats": mining_data['mining_stats'],
        "data_source": "holographic_universe_518k.jsonl (Static/Persistent)"
    },
    "physics_kernel": {
        "version": "2.5",
        "transfer_matrix": transfer_matrix,
        "tensor_dynamics": {
            "activation_function": "sigmoid_variant",
            "parameters": { "k_factor": 2.0 }  # Stiff response (Crystal-like)
        },
        "integrity_threshold": 0.65  # High threshold for integrity
    },
    "feature_anchors": {
        "description": "Standard Crystalline Manifold",
        "standard_manifold": {
            "mean_vector": dict(zip('EOMSR', mean_vector.tolist())),
            "covariance_matrix": cov_matrix.tolist(),
            "thresholds": {
                "max_mahalanobis_dist": 2.5  # Strict boundary
            }
        }
    }
}

# 6. Save
with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    json.dump(registry_entry, f, indent=2, ensure_ascii=False)

print(f"✅ Registry Fragment Generated: {OUTPUT_FILE}")
