import json
import os
import time

# ==========================================
# A-01 Step 2: Genesis Mining (V1.5.1 Strict)
# ==========================================
# Compliance: FDS-V1.5.1
# Funnel:
#   L1: High Order (O > 0.55)
#   L2: E-Gating (E > 0.45) - Self Strength
#   L3: Purity (S < 0.30) - Anti-Entropy
#   L4: Reality Check (y_true > 0.75) - Social Validation

UNIVERSE_FILE = "core/data/holographic_universe_518k.jsonl"
OUTPUT_FILE = "core/subjects/holographic_pattern/mining_cache/a01_tier_a_seeds_v151.json"

print(f"🏛️  [A-01 MINING V1.5.1] Searching for Crystalline Order (The Judge)...")

if not os.path.exists(UNIVERSE_FILE):
    raise FileNotFoundError("Genesis Universe not found!")

stats = {
    "scanned": 0,
    "L1_low_order_rejected": 0,
    "L2_weak_self_rejected": 0, # E-Gating
    "L3_impurity_rejected": 0,  # Purity
    "L4_mediocrity_rejected": 0, # Reality Check
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
        
        # --- L1: 物理流形 (O 轴) ---
        if t['O'] < 0.55:
            stats["L1_low_order_rejected"] += 1
            continue 
        
        # --- L2: 能量门控 (E-Gating) ---
        # 身弱不胜官。The Judge must have a strong Self.
        if t['E'] < 0.45:
            stats["L2_weak_self_rejected"] += 1
            continue
            
        # --- L3: 纯度控制 (Purity) ---
        # A-01 极其厌恶 S (动荡/伤害)
        if t['S'] > 0.30:
            stats["L3_impurity_rejected"] += 1
            continue
            
        # --- L4: 现实验证 (Reality Check) ---
        # 只有贵气 (High Y) 才能定义正官格
        # 平庸的正官格往往只是老好人，非 Tier A 种子
        if y < 0.75:
             stats["L4_mediocrity_rejected"] += 1
             continue

        # Qualified
        candidates.append(row)
        stats["candidates_found"] += 1

end_time = time.time()

# 提纯前 500 (按社会阶层排序)
final_seeds = sorted(candidates, key=lambda x: x['y_true'], reverse=True)[:500]

output_data = {
    "pattern_id": "A-01",
    "step": "Step 2 - Genesis Mining (V1.5.1)",
    "meta_info": { 
        "category": "POWER", # Strict Enum
        "display_name": "Direct Officer", # Strict English
        "chinese_name": "正官格"
    },
    "mining_stats": stats,
    "seeds": final_seeds
}

os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    json.dump(output_data, f, indent=2, ensure_ascii=False)

print(f"🛑 Mining Finished in {end_time - start_time:.2f}s")
print(f"📊 A-01 Mining Funnel (V1.5.1 Strict):")
print(f"   1. Total Scanned:         {stats['scanned']}")
print(f"   2. L1 Rejected (Low O):   {stats['L1_low_order_rejected']}")
print(f"   3. L2 Rejected (Weak E):  {stats['L2_weak_self_rejected']} (The Puppets)")
print(f"   4. L3 Rejected (High S):  {stats['L3_impurity_rejected']} (The Contaminated)")
print(f"   5. L4 Rejected (Low Y):   {stats['L4_mediocrity_rejected']} (The Mediocre)")
print(f"   6. Tier A Candidates:     {stats['candidates_found']}")
print(f"   7. Global Pass Rate:      {stats['candidates_found']/stats['scanned']*100:.3f}%")
print(f"💾 Seeds Saved: {OUTPUT_FILE}")
