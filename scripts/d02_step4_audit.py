import json
import os
import math

# ==========================================
# D-02 Step 4: Singularity Audit (The Spectrum)
# ==========================================

UNIVERSE_FILE = "core/data/holographic_universe_518k.jsonl"
OUTPUT_AUDIT_FILE = "core/subjects/holographic_pattern/mining_cache/d02_step4_singularities.json"

print(f"🌊 [Step 4 START] Splitting the D-02 Spectrum...")

# 定义聚类容器
clusters = {
    "SP_D02_STANDARD": {"samples": [], "sum_tensor": {k:0.0 for k in "EOMSR"}},
    "SP_D02_SYNDICATE": {"samples": [], "sum_tensor": {k:0.0 for k in "EOMSR"}},
    "SP_D02_COLLIDER": {"samples": [], "sum_tensor": {k:0.0 for k in "EOMSR"}}
}

scanned_count = 0

with open(UNIVERSE_FILE, 'r', encoding='utf-8') as f:
    for line in f:
        try:
            row = json.loads(line)
            if "tensor" not in row: continue
        except:
            continue
            
        scanned_count += 1
        t = row['tensor']
        y = row.get('y_true', 0)
        
        # 1. 基础 D-02 门槛 (身旺财旺)
        if t['M'] < 0.55 or t['E'] < 0.45:
            continue
            
        # 2. 只有成功者才有资格定义格局
        if y < 0.75:
            continue
            
        # 3. 光谱分离 (Spectral Separation)
        
        # Priority A: Collider (High S) - 风险最高，特征最明显
        if t['S'] > 0.55:
            target = "SP_D02_COLLIDER"
            
        # Priority B: Syndicate (High R) - 众筹财团
        elif t['R'] > 0.55:
            target = "SP_D02_SYNDICATE"
            
        # Priority C: Standard (Balanced) - 传统大鳄
        else:
            target = "SP_D02_STANDARD"
            
        # 4. 归仓
        clusters[target]["samples"].append(t)
        for k in "EOMSR":
            clusters[target]["sum_tensor"][k] += t[k]

print(f"⚡ Spectrum Analysis Complete. Scanned {scanned_count} entities.")

# 计算各簇的均值向量 (Manifold Centers)
output_clusters = {}

for pid, data in clusters.items():
    count = len(data["samples"])
    if count < 30:
        print(f"⚠️  Cluster {pid} too small ({count}), discarding.")
        continue
        
    mean_vector = {k: v / count for k, v in data["sum_tensor"].items()}
    
    print(f"🧩 {pid}:")
    print(f"   - Count: {count}")
    print(f"   - Mean R: {mean_vector['R']:.4f}")
    print(f"   - Mean S: {mean_vector['S']:.4f}")
    print(f"   - Mean M: {mean_vector['M']:.4f}")

    output_clusters[pid] = {
        "name": pid,
        "count": count,
        "manifold_data": {
            "mean_vector": mean_vector
            # 简化：这里我们假设协方差矩阵使用 Step 3 的全局矩阵
            # 在 Step 5 封装时，我们会复用全局协方差，但在路由时使用这些特定的 Mean 向量
        }
    }

# 物理写入
output_data = {
    "pattern_id": "D-02",
    "step": "Step 4 - Singularity Audit",
    "clusters": output_clusters
}

os.makedirs(os.path.dirname(OUTPUT_AUDIT_FILE), exist_ok=True)
with open(OUTPUT_AUDIT_FILE, 'w', encoding='utf-8') as f:
    json.dump(output_data, f, indent=2)

print(f"💾 Spectrum Registered: {OUTPUT_AUDIT_FILE}")
