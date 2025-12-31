import json
import os
import time

# ==========================================
# A-01 Step 2: Genesis Mining (Direct Officer)
# ==========================================
# Compliance: FDS-V1.5.1

UNIVERSE_FILE = "core/data/holographic_universe_518k.jsonl"
OUTPUT_FILE = "core/subjects/holographic_pattern/mining_cache/a01_tier_a_seeds.json"

print(f"🏛️  [A-01 MINING] Searching for Crystalline Order (The Judge)...")

if not os.path.exists(UNIVERSE_FILE):
    raise FileNotFoundError("Genesis Universe not found!")

stats = {
    "scanned": 0,
    "weak_self_rejected": 0, # 身弱不胜官
    "impurity_rejected": 0,  # 官杀混杂/伤官见官
    "candidates_found": 0
}

candidates = []
start_time = time.time()

with open(UNIVERSE_FILE, 'r', encoding='utf-8') as f:
    for line in f:
        try:
            row = json.loads(line)
        except:
            continue
            
        if 'tensor' not in row:
            continue
            
        stats["scanned"] += 1
        t = row['tensor']
        y = row.get('y_true', 0)
        
        # --- L1: 物理门槛 ---
        
        # 1. 核心: 正官(Order)必须旺
        # 假设 t['O'] 由正官/七杀贡献. 
        # In the static universe, 'O' represents Order/Authority.
        if t['O'] < 0.55: continue 
        
        # 2. 安全门控 (E-Gating Pre-check)
        # 身弱遇官，是压力而非权力
        if t['E'] < 0.50:
            stats["weak_self_rejected"] += 1
            continue
            
        # 3. 纯度控制 (Purity)
        # A-01 极其厌恶 S (动荡/伤害)
        # 如果 S 轴太高 (代表有伤官或重杀混杂)
        if t['S'] > 0.30:
            stats["impurity_rejected"] += 1
            continue
            
        # --- L2: 交叉验证 ---
        
        # 只有贵气 (High Y) 才能定义正官格
        # 平庸的正官格往往只是老好人
        if y > 0.75:
            candidates.append(row)
            stats["candidates_found"] += 1

end_time = time.time()

# 提纯前 500
final_seeds = sorted(candidates, key=lambda x: x['y_true'], reverse=True)[:500]

output_data = {
    "pattern_id": "A-01",
    "step": "Step 2 - Genesis Mining",
    "meta_info": { # [Step 5 前置准备]
        "category": "POWER", # FDS-V1.5.1 Enum Compliance
        "display_name": "Direct Officer", # Pure English Code Index
        "chinese_name": "正官格" # UI Title
    },
    "mining_stats": stats,
    "seeds": final_seeds
}

os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    json.dump(output_data, f, indent=2, ensure_ascii=False)

print(f"🛑 Mining Finished in {end_time - start_time:.2f}s")
print(f"📊 A-01 Mining Funnel (FDS-V1.5.1 Audit):")
print(f"   1. Total Scanned: {stats['scanned']}")
print(f"   2. Failed High-Order (O < 0.55): [Implicit]") 
print(f"   3. Failed E-Gating (E < 0.50): {stats['weak_self_rejected']} (weak/puppet officers)")
print(f"   4. Failed Purity (S > 0.30):   {stats['impurity_rejected']} (contaminated/injured)")
print(f"   5. Qualified Judges (Tier A):  {len(candidates)}")
print(f"   6. Pass Rate: {len(candidates)/stats['scanned']*100:.2f}%")
print(f"💾 Seeds Saved: {OUTPUT_FILE}")
