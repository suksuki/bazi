import json
import os
import time

# ==========================================
# D-01 Step 5: Final Registration (V2.5)
# ==========================================

CACHE_DIR = "core/subjects/holographic_pattern/mining_cache"
MATRIX_FILE = os.path.join(CACHE_DIR, "d01_step3_matrix.json")
REGISTRY_FILE = "core/subjects/holographic_pattern/registry.json"

print(f"🧱 [D-01 REGISTRATION] Assembling V2.5 Container...")

if not os.path.exists(MATRIX_FILE):
    raise FileNotFoundError("D-01 Matrix not found. Run Step 3 first.")

with open(MATRIX_FILE, 'r', encoding='utf-8') as f:
    step3_data = json.load(f)
    std_mean = step3_data['standard_manifold']['mean_vector']
    std_cov = step3_data['standard_manifold']['covariance_matrix']
    transfer_matrix = step3_data['physics_kernel']['transfer_matrix']

# 构建 D-01 Schema V2.5
# 这是一个极其纯粹的单态容器 (Single-State Container)
d01_entry = {
    "id": "D-01",
    "name": "Direct Wealth Pattern (正财格)",
    "version": "2.5",
    "active": True,
    "meta_info": {
        "pattern_id": "D-01",
        "name": "正财格",
        "version": "2.5",
        "physics_prototype": "Gravity Accumulation (引力吸积)",
        "description": "Standard wealth accumulation. Requires High E to hold High M.",
        "compliance": "FDS-V1.5.1 (Genesis Protocol)",
        "data_source": "holographic_universe_518k.jsonl",
        "calibration_date": time.strftime("%Y-%m-%d")
    },
    
    "physics_kernel": {
        "version": "2.5",
        "transfer_matrix": transfer_matrix,
        "integrity_threshold": 0.5
    },

    # V2.5 容器
    "sub_patterns_registry": [
        {
            "id": "SP_D01_STANDARD",
            "name": "The Keeper (守财奴/地主)",
            "type": "DEFAULT",
            "description": "High Energy, High Wealth, Low Relation (Private Ownership).",
            "manifold_data": {
                "mean_vector": std_mean,
                "covariance_matrix": std_cov
            }
        }
    ],

    # V2.5 路由 (简单逻辑)
    "matching_router": {
        "strategy_version": "2.5",
        "description": "Standard Manifold Validation",
        "strategies": [
            {
                "priority": 1,
                "target": "SP_D01_STANDARD",
                "logic": {
                    "condition": "AND",
                    "rules": [
                        # 核心门控: 身必须旺，财必须多，比劫必须少
                        {"axis": "E", "operator": "gt", "value": 0.45},
                        {"axis": "M", "operator": "gt", "value": 0.50},
                        {"axis": "R", "operator": "lt", "value": 0.40} 
                    ],
                    "distance_check": {
                        "type": "MAHALANOBIS",
                        "threshold": 3.0
                    }
                }
            }
        ]
    }
}

# 物理写入
print(f"💾 Writing D-01 to Registry: {REGISTRY_FILE}")

if os.path.exists(REGISTRY_FILE):
    with open(REGISTRY_FILE, 'r', encoding='utf-8') as f:
        current_data = json.load(f)
else:
    current_data = {"patterns": {}}

current_data["patterns"]["D-01"] = d01_entry

with open(REGISTRY_FILE, 'w', encoding='utf-8') as f:
    json.dump(current_data, f, indent=2, ensure_ascii=False)

print(f"✅ SUCCESS: D-01 (Direct Wealth) Registered under Genesis Protocol.")
