import json
import os
import time

# ==========================================
# D-02 Step 5 (Redux): Final Assembly with Built-in Safety
# ==========================================

CACHE_DIR = "core/subjects/holographic_pattern/mining_cache"
MATRIX_FILE = os.path.join(CACHE_DIR, "d02_step3_matrix.json")
AUDIT_FILE = os.path.join(CACHE_DIR, "d02_step4_singularities.json")
REGISTRY_FILE = "core/subjects/holographic_pattern/registry.json"

print(f"🌊 [D-02 REGISTRATION REDUX] Assembling V2.5 Container with Native Safety...")

# 1. 加载组件
with open(MATRIX_FILE, 'r', encoding='utf-8') as f:
    matrix_data = json.load(f)
    base_transfer_matrix = matrix_data['physics_kernel']['transfer_matrix']
    std_cov = matrix_data['standard_manifold']['covariance_matrix']

with open(AUDIT_FILE, 'r', encoding='utf-8') as f:
    audit_data = json.load(f)
    clusters = audit_data['clusters']

# 2. 构建 Schema V2.5 Entry
d02_entry = {
    "id": "D-02",
    "name": "Indirect Wealth Pattern (偏财格)",
    "version": "2.5.1 (Safety Redux)",
    "active": True,
    "meta_info": {
        "pattern_id": "D-02",
        "name": "偏财格",
        "version": "2.5.1",
        "physics_prototype": "Venture Lens / Dynamic Flow",
        "description": "Wealth through leverage (R) and risk (S).",
        "compliance": "FDS-V1.5.1 (Genesis Protocol - Shift Left)",
        "data_source": "holographic_universe_518k.jsonl",
        "calibration_date": time.strftime("%Y-%m-%d")
    },
    
    "physics_kernel": {
        "version": "2.5",
        "transfer_matrix": base_transfer_matrix,
        "integrity_threshold": 0.5
    },

    # V2.5 容器 (包含三个亚种)
    "sub_patterns_registry": [
        {
            "id": "SP_D02_COLLIDER",
            "name": "The Collider (风投/枭雄)",
            "type": "SINGULARITY",
            "description": "High Risk (S), High Wealth (M). Profit from volatility.",
            "matrix_override": {
                "transfer_matrix": {
                    "S_row": {
                        "Seven_Killings": 1.2, # 风险转化为动力
                        "Clash": 1.0
                    },
                    "M_row": {
                         "Direct_Wealth": 0.5,
                         "Indirect_Wealth": 1.8 # 偏财极旺抗杀
                    }
                }
            },
            "manifold_data": {
                "mean_vector": clusters["SP_D02_COLLIDER"]["manifold_data"]["mean_vector"]
            }
        },
        {
            "id": "SP_D02_SYNDICATE",
            "name": "The Syndicate (财团/大鳄)",
            "type": "SINGULARITY",
            "description": "High Leverage (R), High Wealth (M). Profit from network.",
            "matrix_override": {
                "transfer_matrix": {
                    "R_row": {
                        "Rob_Wealth": 1.5, # 劫财即合伙人
                        "Friend": 1.2
                    },
                    "M_row": {
                        "Rob_Wealth": 0.5  # 劫财不再耗财，反而生财
                    }
                }
            },
            "manifold_data": {
                "mean_vector": clusters["SP_D02_SYNDICATE"]["manifold_data"]["mean_vector"]
            }
        },
        {
            "id": "SP_D02_STANDARD",
            "name": "The Hunter (传统大亨)",
            "type": "DEFAULT",
            "description": "Balanced high wealth and energy. Standard venture model.",
            "manifold_data": {
                "mean_vector": clusters["SP_D02_STANDARD"]["manifold_data"]["mean_vector"],
                "covariance_matrix": std_cov
            }
        }
    ],

    # V2.5 路由 - Built-in Safety
    "matching_router": {
        "strategy_version": "2.5.1 (Shift Left)",
        "description": "Spectrum Priority w/ Native E-Gating",
        "strategies": [
            # Priority 1: Collider
            {
                "priority": 1,
                "target": "SP_D02_COLLIDER",
                "logic": {
                    "condition": "AND",
                    "rules": [
                        {"axis": "E", "operator": "gt", "value": 0.45}, # [NATIVE SAFETY]
                        {"axis": "M", "operator": "gt", "value": 0.60},
                        {"axis": "S", "operator": "gt", "value": 0.50} 
                    ],
                    "distance_check": {
                        "type": "MAHALANOBIS",
                        "threshold": 3.0
                    }
                }
            },
            # Priority 2: Syndicate
            {
                "priority": 2,
                "target": "SP_D02_SYNDICATE",
                "logic": {
                    "condition": "AND",
                    "rules": [
                        {"axis": "E", "operator": "gt", "value": 0.45}, # [NATIVE SAFETY]
                        {"axis": "M", "operator": "gt", "value": 0.60},
                        {"axis": "R", "operator": "gt", "value": 0.50} 
                    ],
                    "distance_check": {
                        "type": "MAHALANOBIS",
                        "threshold": 3.0
                    }
                }
            },
            # Priority 3: Standard
            {
                "priority": 3,
                "target": "SP_D02_STANDARD",
                "logic": {
                    "condition": "AND",
                    "rules": [
                        {"axis": "E", "operator": "gt", "value": 0.45}, 
                        {"axis": "M", "operator": "gt", "value": 0.55}
                    ]
                }
            }
        ]
    }
}

# 3. 物理写入
print(f"💾 Overwriting D-02 in Registry: {REGISTRY_FILE}")

if os.path.exists(REGISTRY_FILE):
    with open(REGISTRY_FILE, 'r', encoding='utf-8') as f:
        current_data = json.load(f)
else:
    current_data = {"patterns": {}}

current_data["patterns"]["D-02"] = d02_entry

with open(REGISTRY_FILE, 'w', encoding='utf-8') as f:
    json.dump(current_data, f, indent=2, ensure_ascii=False)

print(f"✅ SUCCESS: D-02 (Redux) Registered.")
print(f"   - E-Gating (E > 0.45) is now NATIVE to all strategies.")
print(f"   - No external patch required.")
