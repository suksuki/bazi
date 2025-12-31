import json
import os

# ==========================================
# D-02 Step 3: Matrix Fitting (The Venture Lens)
# ==========================================

INPUT_SEEDS_FILE = "core/subjects/holographic_pattern/mining_cache/d02_tier_a_seeds.json"
OUTPUT_MATRIX_FILE = "core/subjects/holographic_pattern/mining_cache/d02_step3_matrix.json"

print(f"🌊 [D-02 FITTING] Grinding Lens for Hunters & Syndicates...")

# 1. 加载 Genesis 种子 (Mixed: Standard + Syndicate + Collider)
if not os.path.exists(INPUT_SEEDS_FILE):
    raise FileNotFoundError("D-02 Genesis seeds not found! Run Step 2.")

with open(INPUT_SEEDS_FILE, 'r', encoding='utf-8') as f:
    data = json.load(f)
    seeds = data.get("seeds", [])

print(f"   - Input: {len(seeds)} verified seeds (The Survivors).")

# 2. 物理定义转换矩阵 (The Venture Kernel)
# D-02 的物理法则：流动、杠杆、风险
transfer_matrix = {
    "E_row": {
        "Day_Master": 1.2,      # 身旺依旧是核心
        "Resource": 0.8
    },
    "M_row": {
        "Indirect_Wealth": 1.5, # 偏财主气
        "Direct_Wealth": 0.5,   # 正财为辅
        "Rob_Wealth": -0.2      # [关键物理修正]
                                # 在 D-01 是 -1.0 (抢劫)。
                                # 在 D-02 是 -0.2 (运营成本/分红)。
                                # 只要 M 足以覆盖这个成本，系统允许它的存在。
    },
    "O_row": {
        "Hurting_Officer": 1.2, # 伤官生偏财 (营销/手段)
        "Eating_God": 0.8
    },
    "S_row": {
        "Seven_Killings": 0.5,  # [风险接纳]
                                # 七杀不再是纯粹的负面，而是压力源。
                                # 系数设为正，代表"有压力"，但不是"毁灭"。
        "Clash": 0.5            # 冲代表流动
    },
    "R_row": {
        "Rob_Wealth": 1.0,      # [人脉杠杆]
        "Friend": 0.8           # 朋友越多，R越高。
                                # 在 D-02 中，High R 不会导致直接破格，
                                # 而是会将样本推向 Syndicate 子流形。
    }
}

# 3. 计算流形 (The Manifold)
axes = ['E', 'O', 'M', 'S', 'R']
mean_vector = {k: 0.0 for k in axes}

# 计算均值
for s in seeds:
    t = s['tensor']
    for k in axes:
        mean_vector[k] += t[k]
for k in axes:
    mean_vector[k] /= len(seeds)

# 计算协方差
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

print(f"📊 D-02 Manifold Stats (Genesis):")
print(f"   - Mean E (Self):   {mean_vector['E']:.4f} (Should be High)")
print(f"   - Mean M (Wealth): {mean_vector['M']:.4f} (Should be High)")
print(f"   - Mean R (Network):{mean_vector['R']:.4f} (Should be MODERATE/HIGH)")
print(f"     *Note: If Mean R > 0.4, it proves D-02 tolerates Rob Wealth.*")

# 4. 物理封卷
step3_output = {
    "pattern_id": "D-02",
    "step": "Step 3 - Matrix Fitting",
    "data_source": "holographic_universe_518k.jsonl",
    "physics_kernel": {
        "version": "1.5.1",
        "description": "Indirect Wealth / Venture Dynamics",
        "transfer_matrix": transfer_matrix
    },
    "standard_manifold": {
        "mean_vector": mean_vector,
        "covariance_matrix": covariance,
        # D-02 的判定阈值比 D-01 宽松，因为它涵盖了多种亚种
        "thresholds": {
            "max_mahalanobis_dist": 4.0, 
            "min_sai_gating": 0.5
        }
    }
}

os.makedirs(os.path.dirname(OUTPUT_MATRIX_FILE), exist_ok=True)
with open(OUTPUT_MATRIX_FILE, 'w', encoding='utf-8') as f:
    json.dump(step3_output, f, indent=2)

print(f"💾 D-02 Lens Ground: {OUTPUT_MATRIX_FILE}")
