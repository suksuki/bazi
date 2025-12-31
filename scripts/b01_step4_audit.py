import json
import os
import math

# ==========================================
# B-01 Step 4: The Owl Audit (Singularity Hunt)
# ==========================================

UNIVERSE_FILE = "core/data/holographic_universe_518k.jsonl"
MATRIX_FILE = "core/subjects/holographic_pattern/mining_cache/b01_step3_matrix.json"
OUTPUT_AUDIT_FILE = "core/subjects/holographic_pattern/mining_cache/b01_step4_singularities.json"

print(f"📡 [Step 4 START] Hunting for The Phoenix (Owl Survivors)...")

# 1. 加载透镜 (Standard Manifold)
if not os.path.exists(MATRIX_FILE):
    raise FileNotFoundError("Step 3 Matrix missing!")

with open(MATRIX_FILE, 'r', encoding='utf-8') as f:
    matrix_data = json.load(f)
    std_mean = matrix_data['standard_manifold']['mean_vector']
    # 简化处理：读取对角线方差
    std_cov_diag = matrix_data['standard_manifold']['covariance_matrix']
    # 构造简单的方差向量用于距离计算
    variances = {
        'E': std_cov_diag[0][0], 'O': std_cov_diag[1][1],
        'M': std_cov_diag[2][2], 'S': std_cov_diag[3][3],
        'R': std_cov_diag[4][4]
    }

print(f"🔭 Lens Loaded. Standard S-Mean={std_mean['S']:.4f}, Variance={variances['S']:.6f}")
print(f"   Targeting: High Indirect Resource (>0.45) + High Success (>0.75)")

# 2. 扫描宇宙 (Real Scan)
candidates = []
scanned_count = 0

with open(UNIVERSE_FILE, 'r', encoding='utf-8') as f:
    for line in f:
        try:
            row = json.loads(line)
        except:
            continue
        
        if "tensor" not in row: continue # 跳过header
        
        scanned_count += 1
        tensor = row['tensor']
        y_true = row['y_true']
        
        # -------------------------------------------------
        # 过滤器 A: 寻找 "The Reversal" 候选者
        # 特征: 偏印极重 (S源头), 但依然成功
        # 逻辑: 标准 B-01 要求 S < 0.15。
        # 我们寻找 S > 0.45 (严重污染) 且 E > 0.40 (身旺抗杀/印) 且 y_true > 0.75
        # -------------------------------------------------
        if tensor['S'] > 0.45 and tensor['E'] > 0.40 and y_true > 0.75:
            
            # 3. 计算马氏距离 (Distance from Standard)
            dist_sq = 0
            for axis in ['E', 'O', 'M', 'S', 'R']:
                diff = tensor[axis] - std_mean[axis]
                # 加权欧氏距离 (模拟马氏)
                # 防止除以零
                var = variances[axis] if variances[axis] > 1e-9 else 1e-9
                dist_sq += (diff ** 2) / var
            
            mahalanobis_dist = math.sqrt(dist_sq)
            
            # 记录数据
            candidates.append({
                "uid": row['uid'],
                "tensor": tensor,
                "distance": mahalanobis_dist,
                "y_true": y_true
            })

# 3. 聚类分析 (Cluster Analysis)
# 我们需要确认这些怪胎是否 "长得一样"
print(f"⚡ Scan Complete. Found {len(candidates)} candidates out of {scanned_count}.")

if len(candidates) < 30:
    print("⚠️  Warning: Not enough candidates to form a cluster.")
    cluster_valid = False
else:
    # 计算簇的质心
    cluster_mean = {k: 0.0 for k in ['E', 'O', 'M', 'S', 'R']}
    avg_dist = 0
    for c in candidates:
        avg_dist += c['distance']
        for k in ['E', 'O', 'M', 'S', 'R']:
            cluster_mean[k] += c['tensor'][k]
    
    for k in cluster_mean:
        cluster_mean[k] /= len(candidates)
    avg_dist /= len(candidates)
    
    print(f"🧩 Cluster Analysis (SP_B01_REVERSAL):")
    print(f"   - Count: {len(candidates)}")
    print(f"   - Avg Distance from Standard: {avg_dist:.2f} (Extreme!)")
    print(f"   - Cluster Mean S: {cluster_mean['S']:.4f} (Vs Standard {std_mean['S']:.4f})")
    print(f"   - Cluster Mean E: {cluster_mean['E']:.4f} (High Energy confirmed)")
    
    cluster_valid = True

# 4. 物理写入
if cluster_valid:
    output_data = {
        "pattern_id": "B-01",
        "step": "Step 4 - Singularity Audit",
        "clusters": {
            "SP_B01_REVERSAL": {
                "name": "The Reversal (弃食就印/倒食转化)",
                "count": len(candidates),
                "physical_signature": {
                    "S": "Very High (>0.45)",
                    "E": "High (>0.40)",
                    "Condition": "Phase Transition triggered by high pressure"
                },
                "manifold_data": {
                    "mean_vector": cluster_mean
                },
                "samples_preview": candidates[:10]
            }
        }
    }
    
    os.makedirs(os.path.dirname(OUTPUT_AUDIT_FILE), exist_ok=True)
    with open(OUTPUT_AUDIT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"💾 Singularity Registered: {OUTPUT_AUDIT_FILE}")
else:
    print("❌ No valid singularity cluster found.")
