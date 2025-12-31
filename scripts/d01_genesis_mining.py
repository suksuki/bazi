import json
import os
import time

# ==========================================
# D-01 Step 2: Genesis Mining (Direct Wealth)
# ==========================================
# 依据: FDS-V1.5.1 - 禁止随机生成，强制读取静态宇宙

UNIVERSE_FILE = "core/data/holographic_universe_518k.jsonl"
OUTPUT_FILE = "core/subjects/holographic_pattern/mining_cache/d01_tier_a_seeds.json"

print(f"💰 [D-01 GENESIS MINING] Opening Static Universe...")

if not os.path.exists(UNIVERSE_FILE):
    raise FileNotFoundError(f"CRITICAL: Genesis file {UNIVERSE_FILE} not found!")

# 计数器
stats = {
    "scanned": 0,
    "candidates": 0,
    "rejected_weak_self": 0, # 身弱财旺被剔除
    "rejected_rob_wealth": 0 # 比劫夺财被剔除
}

candidates = []
start_time = time.time()

# --- 1. 静态流式读取 ---
with open(UNIVERSE_FILE, 'r', encoding='utf-8') as f:
    for line in f:
        try:
            row = json.loads(line)
            if "meta" in row: continue # 跳过 header
        except:
            continue
            
        stats["scanned"] += 1
        t = row['tensor']
        y = row.get('y_true', 0)
        
        # --- 2. 物理过滤器 (L1 Filter) ---
        
        # A. 财气通门户 (Material Base)
        # 正财不需要极高，但必须稳健
        if t['M'] < 0.50: continue
        
        # B. 身旺任财 (Energy Base) - 核心物理铁律
        # 如果财旺身弱 (M > 0.6 but E < 0.4)，是灾难
        if t['E'] < 0.45:
            stats["rejected_weak_self"] += 1
            continue
            
        # C. 忌比劫夺财 (Low Entanglement)
        # 正财格是私有制的极致，讨厌分享
        if t['R'] > 0.40:
            stats["rejected_rob_wealth"] += 1
            continue
            
        # --- 3. 交叉验证 (L2 Validation) ---
        
        # D-01 的成功定义：勤劳致富，虽不一定暴富，但长久
        # y_true 代表社会阶层/幸福感
        if y > 0.70:
            candidates.append(row)

end_time = time.time()

# --- 4. 结果统计 ---
print(f"🛑 Mining Finished in {end_time - start_time:.2f}s")
print(f"📊 D-01 Genesis Stats:")
print(f"   - Scanned: {stats['scanned']}")
print(f"   - Weak Self Rejections (富屋贫人): {stats['rejected_weak_self']}")
print(f"   - Rob Wealth Rejections (群劫争财): {stats['rejected_rob_wealth']}")
print(f"   - Qualified Seeds (Tier A): {len(candidates)}")

# --- 5. 提纯与存储 ---
# 取前 500 个最标准的作为种子
final_seeds = sorted(candidates, key=lambda x: x['y_true'], reverse=True)[:500]

output_data = {
    "pattern_id": "D-01",
    "step": "Step 2 - Genesis Mining",
    "data_source": "holographic_universe_518k.jsonl",
    "mining_stats": {
        "total_scanned": stats["scanned"],
        "hit_rate": f"{(len(candidates)/stats['scanned'])*100:.2f}%"
    },
    "seeds": final_seeds
}

os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    json.dump(output_data, f, indent=2)

print(f"💾 D-01 Seeds Saved: {OUTPUT_FILE}")
