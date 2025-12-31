import json
import os
import time

# ==========================================
# B-01 Step 5: Final Assembly & Registration
# ==========================================

# 1. 定义物理路径
CACHE_DIR = "core/subjects/holographic_pattern/mining_cache"
MATRIX_FILE = os.path.join(CACHE_DIR, "b01_step3_matrix.json")
AUDIT_FILE = os.path.join(CACHE_DIR, "b01_step4_singularities.json")
REGISTRY_FILE = "core/subjects/holographic_pattern/registry.json"

print(f"📡 [Step 5 START] Assembling B-01 Engine (Container V2.5)...")

# 2. 读取分步成果
if not os.path.exists(MATRIX_FILE) or not os.path.exists(AUDIT_FILE):
    raise FileNotFoundError("Critical component missing in mining_cache!")

with open(MATRIX_FILE, 'r', encoding='utf-8') as f:
    step3_data = json.load(f)
    std_mean = step3_data['standard_manifold']['mean_vector']
    std_cov = step3_data['standard_manifold']['covariance_matrix']
    base_transfer_matrix = step3_data['physics_kernel']['transfer_matrix']

with open(AUDIT_FILE, 'r', encoding='utf-8') as f:
    step4_data = json.load(f)
    rev_cluster = step4_data['clusters']['SP_B01_REVERSAL']
    rev_mean = rev_cluster['manifold_data']['mean_vector']
    rev_count = rev_cluster['count']

print(f"🧩 Components Loaded:")
print(f"   - Standard Laminar (Count=1,522, Mean S={std_mean['S']:.4f})")
print(f"   - Reversal Phoenix (Count={rev_count}, Mean S={rev_mean['S']:.4f})")

# 3. 构建 B-01 Schema V2.5 对象
b01_registry_entry = {
    "id": "B-01",
    "name": "Eating God Pattern (食神格)",
    "version": "2.5",
    "active": True,
    "meta_info": {
        "pattern_id": "B-01",
        "name": "食神格",
        "version": "2.5",
        "physics_prototype": "Laminar Flow / Superfluidity (层流/超流体)",
        "description": "包含标准层流态与高压逆转态的复合容器。",
        "compliance": "FDS-V1.5.1",
        "calibration_date": time.strftime("%Y-%m-%d"),
        "mining_stats": {
            "seed_count": 1522,
            "singularity_count": rev_count
        }
    },
    
    # 全局物理内核 (默认法则：厌恶偏印)
    "physics_kernel": {
        "version": "2.5",
        "transfer_matrix": base_transfer_matrix, 
        "tensor_dynamics": {
            "activation_function": "sigmoid_variant",
            "parameters": {"k_factor": 2.0}
        },
        "integrity_threshold": 0.5
    },

    # 兼容性锚点 (指向 Standard)
    "feature_anchors": {
        "description": "Standard Laminar Manifold",
        "standard_manifold": {
            "mean_vector": std_mean,
            "covariance_matrix": std_cov,
            "thresholds": {"max_mahalanobis_dist": 3.0}
        }
    },

    # V2.5 子格局容器
    "sub_patterns_registry": [
        {
            "id": "SP_B01_STANDARD",
            "name": "The Artist (标准层流态)",
            "type": "DEFAULT",
            "description": "Low Entropy, High Output. The ideal Eating God flow.",
            # 标准态沿用全局矩阵，无需 Override
            "manifold_data": {
                "mean_vector": std_mean,
                "covariance_matrix": std_cov
            }
        },
        {
            "id": "SP_B01_REVERSAL",
            "name": "The Phoenix (弃食就印/倒食转化)",
            "type": "SINGULARITY",
            "description": "High Pressure (Owl) converted to Power by Strong Self.",
            
            # [关键] 物理法则重写
            "matrix_override": {
                "transfer_matrix": {
                    "S_row": {
                        "Indirect_Resource": -1.0, # 翻转：不再视为压力，而是资源
                        "Seven_Killings": 0.5      # 杀印相生
                    },
                    "E_row": {
                        "Indirect_Resource": 1.5   # 翻转：偏印成为极强的生身源头
                    }
                }
            },
            
            "manifold_data": {
                "mean_vector": rev_mean
                # 使用 Step 4 聚类出的均值 (High S, High E)
            }
        }
    ],

    # V2.5 路由协议
    "matching_router": {
        "strategy_version": "2.5",
        "description": "Distinguish between Fragile Art and Tough Survival.",
        "strategies": [
            {
                "priority": 1,
                "target": "SP_B01_REVERSAL",
                "description": "Check for Phoenix first (More common, High Energy Requirement)",
                "logic": {
                    "condition": "AND",
                    "rules": [
                        {"axis": "S", "operator": "gt", "value": 0.40}, # 必须有高压 (偏印/杀)
                        {"axis": "E", "operator": "gt", "value": 0.45}  # 必须身旺抗压
                    ]
                }
            },
            {
                "priority": 2,
                "target": "SP_B01_STANDARD",
                "description": "Check for Laminar Flow (Strict Purity)",
                "logic": {
                    "condition": "MAHALANOBIS",
                    "threshold": 3.0 # 严苛的距离判定
                }
            }
        ]
    }
}

# 4. 物理写入主注册表
print(f"💾 Writing to Main Registry: {REGISTRY_FILE}")

try:
    if os.path.exists(REGISTRY_FILE):
        with open(REGISTRY_FILE, 'r', encoding='utf-8') as f:
            current_data = json.load(f)
    else:
        current_data = {"patterns": {}}
    
    # 注入 B-01
    current_data["patterns"]["B-01"] = b01_registry_entry

    with open(REGISTRY_FILE, 'w', encoding='utf-8') as f:
        json.dump(current_data, f, indent=2, ensure_ascii=False)

    print(f"✅ SUCCESS: B-01 (Eating God) has been PHYSICALLY REGISTERED.")
    print(f"   Router Logic: Reversal (P1) -> Standard (P2)")

except Exception as e:
    print(f"❌ ERROR: Failed to write registry. {str(e)}")
