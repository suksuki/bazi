import json
import os
import time

# ==========================================
# B-02 Step 2: Genesis Mining (V1.5.1)
# ==========================================
# Target: The Successful Destroyer (Hurting Officer)
# Funnel:
#   L1: Shockwave (High O > 0.50, High S > 0.30)
#   L2: E-Gating (E > 0.45) - Must be Strong to sustain Chaos
#   L3: Reality Check (y_true > 0.75) - Only the successful ones

UNIVERSE_FILE = "core/data/holographic_universe_518k.jsonl"
OUTPUT_FILE = "core/subjects/holographic_pattern/mining_cache/b02_tier_a_seeds_v151.json"

print(f"🌪️  [B-02 MINING V1.5.1] Searching for 'The Successful Destroyer'...")

if not os.path.exists(UNIVERSE_FILE):
    raise FileNotFoundError("Genesis Universe not found!")

stats = {
    "scanned": 0,
    "L1_weak_signal_rejected": 0, # Low O or Low S
    "L2_weak_self_rejected": 0,   # E-Gating (Crucial for B-02)
    "L3_mediocrity_rejected": 0,  # Failed Reality Check
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
        
        # --- L1: 物理流形 (Shockwave) ---
        # High Output (O) AND High Stress/Change (S)
        if t['O'] < 0.50 or t['S'] < 0.30:
            stats["L1_weak_signal_rejected"] += 1
            continue
            
        # --- L2: 能量门控 (E-Gating) ---
        # 身弱伤官 = 泄气/内耗 (Neuroticism)
        # 身旺伤官 = 才华/变革 (Creativity)
        if t['E'] < 0.45:
            stats["L2_weak_self_rejected"] += 1
            continue
            
        # --- L3: 现实验证 (Reality Check) ---
        # 伤官格成才极难。"聪明不过伤官，伶俐不过七杀"，但大多数聪明人一事无成。
        if y < 0.75:
            stats["L3_mediocrity_rejected"] += 1
            continue
            
        candidates.append(row)
        stats["candidates_found"] += 1

end_time = time.time()

# Sort by Success (y_true)
final_seeds = sorted(candidates, key=lambda x: x['y_true'], reverse=True)[:500]

output_data = {
    "pattern_id": "B-02",
    "step": "Step 2 - Genesis Mining (V1.5.1)",
    "meta_info": { 
        "category": "TALENT", 
        "display_name": "Hurting Officer",
        "chinese_name": "伤官格"
    },
    "mining_stats": stats,
    "seeds": final_seeds
}

os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    json.dump(output_data, f, indent=2, ensure_ascii=False)

print(f"🛑 Mining Finished in {end_time - start_time:.2f}s")
print(f"📊 B-02 Mining Funnel (The Survivor's Game):")
print(f"   1. Total Scanned:         {stats['scanned']}")
print(f"   2. L1 Rejected (Quiet):   {stats['L1_weak_signal_rejected']} (Low O/S)")
print(f"   3. L2 Rejected (Weak):    {stats['L2_weak_self_rejected']} (Self < 0.45)")
print(f"   4. L3 Rejected (Failed):  {stats['L3_mediocrity_rejected']} (Talented but Poor)")
print(f"   5. Tier A Rebels:         {stats['candidates_found']}")
print(f"   6. Global Pass Rate:      {stats['candidates_found']/stats['scanned']*100:.3f}%")
print(f"💾 Seeds Saved: {OUTPUT_FILE}")
