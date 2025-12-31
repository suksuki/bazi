import json
import os
import math

# ==========================================
# D-01 Step 3: Matrix Re-Fitting (Genesis Data)
# ==========================================

INPUT_SEEDS_FILE = "core/subjects/holographic_pattern/mining_cache/d01_tier_a_seeds.json"
OUTPUT_MATRIX_FILE = "core/subjects/holographic_pattern/mining_cache/d01_step3_matrix.json"

print(f"🧱 [D-01 FITTING] Grinding Lens from Genesis Seeds...")

# 1. 加载 Genesis 种子
if not os.path.exists(INPUT_SEEDS_FILE):
    raise FileNotFoundError("D-01 Genesis seeds not found! Please run Step 2 first.")

with open(INPUT_SEEDS_FILE, 'r', encoding='utf-8') as f:
    data = json.load(f)
    seeds = data.get("seeds", [])

if len(seeds) < 50:
    raise ValueError("Not enough seeds to fit matrix!")

print(f"   - Input: {len(seeds)} verified seeds from Static Universe.")

# 2. 物理定义转换矩阵 (The Diligence Kernel)
# D-01 的物理法则：勤劳、积累、排他
transfer_matrix = {
    "E_row": {
        "Day_Master": 1.2,      # 必须身旺，作为载体
        "Resource": 0.8         # 印星护身
    },
    "M_row": {
        "Direct_Wealth": 1.5,   # 正财核心
        "Rob_Wealth": -1.0      # [关键] 劫财是负资产
    },
    "O_row": {
        "Direct_Officer": 1.0,  # 官星护财
        "Eating_God": 0.8       # 食神生财
    },
    "S_row": {
        "Seven_Killings": -0.5, # 七杀耗财
        "Clash": 1.0            # 冲是破坏积累
    },
    "R_row": {
        "Friend": 0.5,
        "Rob_Wealth": 1.2       # 比劫增加 R 值 (会被流形判定为远离中心)
    }
}

# 3. 计算标准流形 (Standard Manifold)
# 基于静态数据的真实分布计算均值和协方差
axes = ['E', 'O', 'M', 'S', 'R']
mean_vector = {k: 0.0 for k in axes}

# A. 计算均值
for s in seeds:
    t = s['tensor']
    for k in axes:
        mean_vector[k] += t[k]
for k in axes:
    mean_vector[k] /= len(seeds)

# B. 计算协方差 (简化对角线方差)
# 这决定了流形的"胖瘦"。方差越小，要求越严。
covariance = []
for i, ax_i in enumerate(axes):
    row = []
    for j, ax_j in enumerate(axes):
        if i == j:
            # Variance
            var = sum((s['tensor'][ax_i] - mean_vector[ax_i])**2 for s in seeds) / len(seeds)
            row.append(round(var, 6))
        else:
            row.append(0.0)
    covariance.append(row)

print(f"📊 D-01 Manifold Stats (Genesis):")
print(f"   - Mean E (Self):   {mean_vector['E']:.4f}")
print(f"   - Mean M (Wealth): {mean_vector['M']:.4f}")
print(f"   - Mean R (Rivals): {mean_vector['R']:.4f} (Should be LOW)")

# 4. 物理封卷
step3_output = {
    "pattern_id": "D-01",
    "step": "Step 3 - Matrix Fitting",
    "data_source": "holographic_universe_518k.jsonl",
    "physics_kernel": {
        "version": "1.5.1",
        "description": "Direct Wealth Accumulation Dynamics",
        "transfer_matrix": transfer_matrix
    },
    "standard_manifold": {
        "mean_vector": mean_vector,
        "covariance_matrix": covariance,
        "thresholds": {
            "max_mahalanobis_dist": 3.0,
            "min_sai_gating": 0.4
        }
    }
}

os.makedirs(os.path.dirname(OUTPUT_MATRIX_FILE), exist_ok=True)
with open(OUTPUT_MATRIX_FILE, 'w', encoding='utf-8') as f:
    json.dump(step3_output, f, indent=2)

print(f"💾 D-01 Lens Ground: {OUTPUT_MATRIX_FILE}")
