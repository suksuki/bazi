import json
import os
import time

# ==========================================
# A-03 Step 2: The Fusion Mining (Static Universe)
# ==========================================

UNIVERSE_FILE = "core/data/holographic_universe_518k.jsonl"
OUTPUT_SEEDS_FILE = "core/subjects/holographic_pattern/mining_cache/a03_tier_a_seeds.json"

print(f"☢️  [A-03 MINING] Scanning 518k Universe for Tokamak Reactors...")

if not os.path.exists(UNIVERSE_FILE):
    raise FileNotFoundError("Genesis Universe not found! Cannot mine.")

candidates = []
accident_count = 0 # 记录“核事故”样本 (E高 S高 但 y低)
scanned = 0

start_time = time.time()

with open(UNIVERSE_FILE, 'r', encoding='utf-8') as f:
    for line in f:
        try:
            row = json.loads(line)
        except:
            continue
        
        # Skip header
        if "tensor" not in row: continue
        scanned += 1
        
        t = row['tensor']
        y = row.get('y_true', 0)
        
        # 1. 临界质量 (High Energy) - 羊刃特征
        if t['E'] < 0.65: continue
        
        # 2. 强磁约束 (High Stress) - 七杀特征
        if t['S'] < 0.55: continue
        
        # 3. 杂质控制 (Low Leakage) - 无食伤泄气
        if t['O'] > 0.35: continue
        
        # --- 进入高能区 ---
        
        # 4. 聚变验证 (Fusion Verify)
        # E 和 S 必须匹配 (Difference not too big)
        # 如果 E >> S，磁场关不住等离子体 -> 爆炸
        # 如果 S >> E，磁场压垮核心 -> 熄火
        balance_ratio = abs(t['E'] - t['S'])
        
        if balance_ratio > 0.25:
            # 能量不匹配，视为废料
            continue
            
        # 5. 结果验证 (Outcome)
        if y > 0.80:
            # 聚变成功: 大贵
            candidates.append(row)
        elif y < 0.40:
            # 聚变失败: 凶灾 (核事故)
            accident_count += 1

end_time = time.time()
duration = end_time - start_time

print(f"🛑 Mining Finished in {duration:.2f}s")
print(f"📊 Reactor Stats:")
print(f"   - Scanned: {scanned}")
print(f"   - High Energy/Stress Zone Found: {len(candidates) + accident_count}")
print(f"   - Meltdowns (Accidents): {accident_count} (High E+S but Low Outcome)")
print(f"   - Functional Reactors (Seeds): {len(candidates)} (Pure A-03)")

# 物理写入 (保留前 500 个作为种子)
# A-03 非常稀有，可能不足 500 个，如果不足就全取
final_seeds = candidates[:500]

output_data = {
    "pattern_id": "A-03",
    "step": "Step 2 - Fusion Mining",
    "data_source": "holographic_universe_518k.jsonl",
    "mining_stats": {
        "scanned": scanned,
        "meltdown_count": accident_count,
        "reactor_count": len(candidates)
    },
    "seeds": final_seeds
}

os.makedirs(os.path.dirname(OUTPUT_SEEDS_FILE), exist_ok=True)
with open(OUTPUT_SEEDS_FILE, 'w', encoding='utf-8') as f:
    json.dump(output_data, f, indent=2)

print(f"💾 Reactor Seeds Saved: {OUTPUT_SEEDS_FILE}")
