import json
import os
import time

# ==========================================
# A-03 Step 5: Final Assembly (Nuclear Station)
# ==========================================

CACHE_DIR = "core/subjects/holographic_pattern/mining_cache"
MATRIX_FILE = os.path.join(CACHE_DIR, "a03_step3_matrix.json")
AUDIT_FILE = os.path.join(CACHE_DIR, "a03_step4_singularities.json")
REGISTRY_FILE = "core/subjects/holographic_pattern/registry.json"

print(f"☢️  [Step 5 START] Assembling A-03 Reactor Core...")

# 1. 读取组件
with open(MATRIX_FILE, 'r', encoding='utf-8') as f:
    step3_data = json.load(f)
    std_mean = step3_data['standard_manifold']['mean_vector']
    std_cov = step3_data['standard_manifold']['covariance_matrix']
    base_transfer_matrix = step3_data['physics_kernel']['transfer_matrix']

with open(AUDIT_FILE, 'r', encoding='utf-8') as f:
    step4_data = json.load(f)
    all_cluster = step4_data['clusters']['SP_A03_ALLIANCE']
    all_mean = all_cluster['manifold_data']['mean_vector']
    all_count = all_cluster['count']

# 2. 构建 A-03 Schema V2.5
a03_registry_entry = {
    "id": "A-03",
    "name": "Blade & Killer (羊刃架杀格)",
    "version": "2.5",
    "active": True,
    "meta_info": {
        "pattern_id": "A-03",
        "name": "羊刃架杀格",
        "version": "2.5",
        "physics_prototype": "Tokamak / Stellarator (磁约束聚变)",
        "description": "High Energy Plasma (Yang Ren) confined by High Stress Field (Seven Killings).",
        "compliance": "FDS-V1.5.1 (Genesis Protocol)",
        "data_source": "holographic_universe_518k.jsonl (Static/Persistent)",
        "calibration_date": time.strftime("%Y-%m-%d"),
        "mining_stats": {
            "seed_count": 336,
            "singularity_count": all_count
        }
    },

    "physics_kernel": {
        "version": "2.5",
        "transfer_matrix": base_transfer_matrix, # 基础矩阵：对抗做功
        "tensor_dynamics": {
            "activation_function": "sigmoid_variant",
            "parameters": {"k_factor": 3.0} # 聚变反应堆需要更陡峭的激活函数
        },
        "integrity_threshold": 0.6 # 门槛极高
    },

    # 兼容锚点
    "feature_anchors": {
        "description": "Standard Tokamak Manifold",
        "standard_manifold": {
            "mean_vector": std_mean,
            "covariance_matrix": std_cov,
            "thresholds": {"max_mahalanobis_dist": 2.5}
        }
    },

    # V2.5 容器
    "sub_patterns_registry": [
        {
            "id": "SP_A03_ALLIANCE",
            "name": "The Alliance (羊刃合杀/仿星器)",
            "type": "SINGULARITY",
            "description": "Fusion achieved by bonding (High R). Self-stabilizing plasma.",
            
            # [物理重写] 
            # 在合杀局中，杀不攻身，反而化为权。
            "matrix_override": {
                "transfer_matrix": {
                    "S_row": {
                        "Seven_Killings": 1.0, # 压力降低 (被合住了)
                    },
                    "O_row": {
                        "Seven_Killings": 1.5, # 转化为权力的效率更高
                        "Combination": 1.2     # 合相直接产出权力 (化气)
                    }
                }
            },
            
            "manifold_data": {
                "mean_vector": all_mean # High R, High E, High S
            }
        },
        {
            "id": "SP_A03_STANDARD",
            "name": "The Tokamak (羊刃架杀/对抗态)",
            "type": "DEFAULT",
            "description": "Fusion achieved by pressure (High S). Dynamic equilibrium.",
            "manifold_data": {
                "mean_vector": std_mean,
                "covariance_matrix": std_cov
            }
        }
    ],

    # V2.5 核安全路由
    "matching_router": {
        "strategy_version": "2.5 (Genesis)",
        "description": "Nuclear Safety Protocols Enforced.",
        "strategies": [
            {
                "priority": 1,
                "target": "SP_A03_ALLIANCE",
                "description": "Check for Superconductivity (Bonding)",
                "logic": {
                    "condition": "AND",
                    "rules": [
                        {"axis": "E", "operator": "gt", "value": 0.60}, # [核门控] 燃料临界值
                        {"axis": "S", "operator": "gt", "value": 0.50}, # 磁场临界值
                        {"axis": "R", "operator": "gt", "value": 0.50}  # 键合临界值
                    ]
                }
            },
            {
                "priority": 2,
                "target": "SP_A03_STANDARD",
                "description": "Check for Tokamak Containment",
                "logic": {
                    "condition": "HYBRID", # 使用复合逻辑
                    "rules": [
                        {"axis": "E", "operator": "gt", "value": 0.60}, # [核门控] 燃料临界值
                        {"axis": "S", "operator": "gt", "value": 0.50}, # 磁场临界值
                        {"axis": "O", "operator": "lt", "value": 0.35}  # [杂质门控] 忌食伤泄气
                    ],
                    # 距离校验作为二级验证
                    "distance_check": {
                        "type": "MAHALANOBIS",
                        "threshold": 2.5
                    }
                }
            }
        ]
    }
}

# 3. 物理写入
print(f"💾 Writing to Main Registry: {REGISTRY_FILE}")
if os.path.exists(REGISTRY_FILE):
    with open(REGISTRY_FILE, 'r', encoding='utf-8') as f:
        current_data = json.load(f)
else:
    current_data = {"patterns": {}}

current_data["patterns"]["A-03"] = a03_registry_entry

with open(REGISTRY_FILE, 'w', encoding='utf-8') as f:
    json.dump(current_data, f, indent=2, ensure_ascii=False)

print(f"✅ SUCCESS: A-03 Reactor Core Registered.")
print(f"   Compliance: {a03_registry_entry['meta_info']['compliance']}")
print(f"   Safety Protocol: E > 0.60 HARD LOCK.")
