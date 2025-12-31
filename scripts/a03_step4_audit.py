import json
import os
import math

# ==========================================
# A-03 Step 4: The Alliance Audit (Superconductivity)
# ==========================================

UNIVERSE_FILE = "core/data/holographic_universe_518k.jsonl"
MATRIX_FILE = "core/subjects/holographic_pattern/mining_cache/a03_step3_matrix.json"
OUTPUT_AUDIT_FILE = "core/subjects/holographic_pattern/mining_cache/a03_step4_singularities.json"

print(f"☢️  [Step 4 START] Scanning for Superconductors (Yang Ren Combined with Killing)...")

# 1. 加载透镜 (Standard Tokamak)
if not os.path.exists(MATRIX_FILE):
    raise FileNotFoundError("Step 3 Matrix missing!")

with open(MATRIX_FILE, 'r', encoding='utf-8') as f:
    matrix_data = json.load(f)
    std_mean = matrix_data['standard_manifold']['mean_vector']
    # 简化方差读取
    std_cov = matrix_data['standard_manifold']['covariance_matrix']
    variances = {
        'E': std_cov[0][0], 'O': std_cov[1][1],
        'M': std_cov[2][2], 'S': std_cov[3][3],
        'R': std_cov[4][4]
    }

print(f"🔭 Lens Loaded. Standard R-Mean={std_mean['R']:.4f} (Likely Low)")
print(f"   Targeting: High E + High S + HIGH R (The Alliance)")

# 2. 扫描宇宙
candidates = []
scanned_count = 0

with open(UNIVERSE_FILE, 'r', encoding='utf-8') as f:
    for line in f:
        try:
            row = json.loads(line)
        except:
            continue
        
        if "tensor" not in row: continue
        scanned_count += 1
        t = row['tensor']
        y = row.get('y_true', 0)
        
        # -------------------------------------------------
        # 过滤器: 寻找 "The Alliance"
        # 基础条件: 必须是 A-03 的胚子 (High E, High S)
        # 奇点特征: High R (合相)
        # -------------------------------------------------
        
        if t['E'] > 0.60 and t['S'] > 0.55:
            # 这里的 R > 0.55 是关键。
            # 标准 A-03 的 R 通常很低（因为杀旺通常克比劫），
            # 只有出现了“合”，R 才会升高。
            if t['R'] > 0.55 and y > 0.85:
                
                # 计算到标准 Tokamak 的距离
                dist_sq = 0
                for axis in ['E', 'O', 'M', 'S', 'R']:
                    diff = t[axis] - std_mean[axis]
                    dist_sq += (diff ** 2) / (variances[axis] if variances[axis] > 0 else 1)
                
                dist = math.sqrt(dist_sq)
                
                candidates.append({
                    "uid": row['uid'],
                    "tensor": t,
                    "distance": dist,
                    "y_true": y
                })

# 3. 聚类分析
print(f"⚡ Scan Complete. Found {len(candidates)} Superconductors.")

if len(candidates) < 20:
    print("⚠️  Warning: Cluster too small. Rare phenomenon.")
else:
    # 计算簇均值
    cluster_mean = {k: 0.0 for k in ['E', 'O', 'M', 'S', 'R']}
    avg_dist = 0
    for c in candidates:
        avg_dist += c['distance']
        for k in cluster_mean:
            cluster_mean[k] += c['tensor'][k]
            
    for k in cluster_mean:
        cluster_mean[k] /= len(candidates)
    avg_dist /= len(candidates)
    
    print(f"🧩 Cluster Analysis (SP_A03_ALLIANCE):")
    print(f"   - Count: {len(candidates)}")
    print(f"   - Avg Distance from Standard: {avg_dist:.2f}")
    print(f"   - Cluster Mean R: {cluster_mean['R']:.4f} (Bonding Strength)")
    print(f"   - Cluster Mean S: {cluster_mean['S']:.4f}")

    # 4. 物理写入
    output_data = {
        "pattern_id": "A-03",
        "step": "Step 4 - Singularity Audit",
        "clusters": {
            "SP_A03_ALLIANCE": {
                "name": "The Alliance (羊刃合杀/超导态)",
                "count": len(candidates),
                "physical_signature": {
                    "R": "Very High (>0.55)",
                    "Condition": "Conflict (S) converted to Bond (R)"
                },
                "manifold_data": {
                    "mean_vector": cluster_mean
                }
            }
        }
    }
    
    os.makedirs(os.path.dirname(OUTPUT_AUDIT_FILE), exist_ok=True)
    with open(OUTPUT_AUDIT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"💾 Singularity Registered: {OUTPUT_AUDIT_FILE}")
