import json
import os
import math

# ==========================================
# A-03 Step 3: Fusion Matrix Fitting
# ==========================================

INPUT_SEEDS_FILE = "core/subjects/holographic_pattern/mining_cache/a03_tier_a_seeds.json"
OUTPUT_MATRIX_FILE = "core/subjects/holographic_pattern/mining_cache/a03_step3_matrix.json"

print(f"☢️  [Step 3 START] Calculating Fusion Equations for 336 Reactors...")

# 1. 物理定义转换矩阵 (The Tokamak Kernel)
# 这是一个高度特异化的矩阵，完全违背常规"吉凶"定义
transfer_matrix = {
    "E_row": {
        "Yang_Ren": 1.5,        # [燃料] 羊刃是E轴的绝对核心
        "Day_Master": 1.0,      # 日主本身
        "Seven_Killings": -0.3  # [损耗] 七杀会消耗能量(克身)，但被羊刃抵消
    },
    "S_row": {
        "Seven_Killings": 1.8,  # [磁场] 七杀提供极高压强
        "Direct_Officer": 0.5,  # 正官太软，不算高压
        "Yang_Ren": 0.0         # 羊刃本身不产生外部压力，它是内部压力
    },
    "O_row": {
        # [聚变奇迹] 权力的来源
        # 只要成格，羊刃就是权力，七杀就是威望。
        # 这里的权重代表：越旺的羊刃/七杀，转化出的 O 越高。
        "Seven_Killings": 1.2,  # 杀即是权 (Authority)
        "Yang_Ren": 0.8,        # 刃即是威 (Prestige)
        "Eating_God": -0.8,     # [冷却剂] 食神泄气，降低反应堆温度 (负分)
        "Hurting_Officer": -0.8 # 伤官泄气
    },
    "M_row": {
        "Yang_Ren": -1.2,       # [副作用] 羊刃劫财。A-03通常不主富，主贵。
        "Direct_Wealth": 0.5,
        "Seven_Killings": 0.8   # 杀护财 (防止劫财抢劫)
    },
    "R_row": {
        "Friend": 1.0,
        "Rob_Wealth": 0.5
    }
}

# 2. 计算标准流形 (Standard Manifold)
# 读取那 336 个珍贵的成功样本
if not os.path.exists(INPUT_SEEDS_FILE):
    raise FileNotFoundError("Seeds file missing! Did Step 2 complete?")

with open(INPUT_SEEDS_FILE, 'r', encoding='utf-8') as f:
    data = json.load(f)
    seeds = data.get("seeds", [])

if len(seeds) == 0:
    raise ValueError("No seeds found to fit!")

print(f"🧪 Fitting Manifold using {len(seeds)} Fusion Reactors...")

# 计算均值
axes = ['E', 'O', 'M', 'S', 'R']
mean_vector = {k: 0.0 for k in axes}
count = len(seeds)

for s in seeds:
    t = s['tensor']
    for k in axes:
        mean_vector[k] += t[k]

for k in axes:
    mean_vector[k] /= count

# 计算协方差 (简易版)
covariance = []
for i, ax_i in enumerate(axes):
    row = []
    for j, ax_j in enumerate(axes):
        if i == j:
            # 计算方差
            var = sum((s['tensor'][ax_i] - mean_vector[ax_i])**2 for s in seeds) / count
            row.append(round(var, 6))
        else:
            row.append(0.0) 
    covariance.append(row)

print(f"📊 Fusion Manifold Stats:")
print(f"   Mean E (Fuel):   {mean_vector['E']:.4f} (Must be high)")
print(f"   Mean S (Field):  {mean_vector['S']:.4f} (Must be high)")
print(f"   Mean O (Power):  {mean_vector['O']:.4f} (Result of Fusion)")

# 3. 物理封卷
step3_output = {
    "pattern_id": "A-03",
    "step": "Step 3 - Matrix Fitting",
    "physics_kernel": {
        "version": "1.5.1",
        "description": "Controlled Fusion Dynamics",
        "transfer_matrix": transfer_matrix
    },
    "standard_manifold": {
        "mean_vector": mean_vector,
        "covariance_matrix": covariance,
        "thresholds": {
            "max_mahalanobis_dist": 2.5, # 核反应堆非常精密，容错率极低
            "min_sai_gating": 0.6
        }
    }
}

os.makedirs(os.path.dirname(OUTPUT_MATRIX_FILE), exist_ok=True)
with open(OUTPUT_MATRIX_FILE, 'w', encoding='utf-8') as f:
    json.dump(step3_output, f, indent=2)

print(f"💾 Fusion Lens Saved: {OUTPUT_MATRIX_FILE}")
