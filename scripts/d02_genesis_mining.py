import json
import os
import time

# ==========================================
# D-02 Step 2: Genesis Mining (Indirect Wealth)
# ==========================================
# 依据: FDS-V1.5.1 - 静态宇宙读取
# 核心差异: 允许 High R (Syndicate) 和 High S (Collider)

UNIVERSE_FILE = "core/data/holographic_universe_518k.jsonl"
OUTPUT_FILE = "core/subjects/holographic_pattern/mining_cache/d02_tier_a_seeds.json"

print(f"🌊 [D-02 MINING] Casting nets for Hunters & Syndicates...")

if not os.path.exists(UNIVERSE_FILE):
    raise FileNotFoundError("CRITICAL: Genesis Universe not found!")

# 统计计数器
stats = {
    "total_scanned": 0,
    "weak_self_rejected": 0, # 身弱不担偏财 (必死定律)
    "candidates_found": 0,
    
    # 亚种统计
    "type_standard": 0,   # 传统的偏财大亨
    "type_syndicate": 0,  # 众筹/杠杆成功者
    "type_collider": 0,   # 风险/风投成功者
    
    # 失败组 (用于计算生存率)
    "failed_gamblers": 0, # High R + High M, but Low Y (赌输了)
    "failed_risk_takers": 0 # High S + High M, but Low Y (浪死了)
}

candidates = []
start_time = time.time()

with open(UNIVERSE_FILE, 'r', encoding='utf-8') as f:
    for line in f:
        try:
            row = json.loads(line)
            if "meta" in row: continue
        except:
            continue
            
        stats["total_scanned"] += 1
        t = row['tensor']
        y = row.get('y_true', 0)
        
        # --- L1: 基础物理门槛 ---
        
        # 1. 偏财必须有财 (High M)
        if t['M'] < 0.55: continue
        
        # 2. 身必须旺 (High E) - 这一点与 D-01 一致
        # 偏财是"众人之财"，流动性大，身弱者拿不住，会被财压死
        if t['E'] < 0.45:
            stats["weak_self_rejected"] += 1
            continue
            
        # --- L2: 形态分类 (Pattern Classification) ---
        
        category = None
        
        # A. Standard Tycoon (大亨)
        # 特征: 财旺，身旺，且 R 和 S 都不算太高 (类似 D-01，但更灵活)
        if t['R'] <= 0.50 and t['S'] <= 0.50:
            if y > 0.75:
                category = "SP_D02_STANDARD"
                stats["type_standard"] += 1
        
        # B. Syndicate (财团/众筹) - D-01 的弃子，D-02 的宝贝
        # 特征: 财旺，身旺，且比劫极重 (R > 0.5)
        elif t['R'] > 0.50:
            if y > 0.80: # 只有大成功才算 Syndicate
                category = "SP_D02_SYNDICATE"
                stats["type_syndicate"] += 1
            elif y < 0.40:
                stats["failed_gamblers"] += 1 # 只有R高没有成功 -> 赌徒/被骗
                
        # C. Collider (枭雄/风投)
        # 特征: 财旺，身旺，且动荡极重 (S > 0.5)
        elif t['S'] > 0.50:
            if y > 0.80:
                category = "SP_D02_COLLIDER"
                stats["type_collider"] += 1
            elif y < 0.40:
                stats["failed_risk_takers"] += 1 # 只有S高没有成功 -> 因财惹祸
        
        # --- L3: 种子录入 ---
        if category:
            row['d02_subtype'] = category # 打上标签，供 Step 5 路由使用
            candidates.append(row)

end_time = time.time()

# --- 统计汇报 ---
print(f"🛑 Mining Finished in {end_time - start_time:.2f}s")
print(f"📊 D-02 Genesis Stats:")
print(f"   - Scanned: {stats['total_scanned']}")
print(f"   - Weak Self Rejections: {stats['weak_self_rejected']} (Ghost of Wealth)")
print(f"   - Total Seeds Found: {len(candidates)}")
print(f"   ------------------------------------")
print(f"   [Sub-Pattern Breakdown]")
print(f"   - Standard Tycoons: {stats['type_standard']}")
print(f"   - Syndicates (High R): {stats['type_syndicate']}")
print(f"   - Colliders (High S): {stats['type_collider']}")
print(f"   ------------------------------------")
print(f"   [Survival Rates]")
if (stats['type_syndicate'] + stats['failed_gamblers']) > 0:
    syn_rate = stats['type_syndicate'] / (stats['type_syndicate'] + stats['failed_gamblers'])
    print(f"   - Syndicate Leverage Rate: {syn_rate*100:.2f}% (Vs Gamblers)")
else:
    print(f"   - Syndicate Leverage Rate: N/A")
    
if (stats['type_collider'] + stats['failed_risk_takers']) > 0:
    risk_rate = stats['type_collider'] / (stats['type_collider'] + stats['failed_risk_takers'])
    print(f"   - Collider Survival Rate:  {risk_rate*100:.2f}% (Vs Victims)")
else:
    print(f"   - Collider Survival Rate: N/A")

# 提纯前 500 (混合亚种，按成就排序)
final_seeds = sorted(candidates, key=lambda x: x['y_true'], reverse=True)[:500]

output_data = {
    "pattern_id": "D-02",
    "step": "Step 2 - Genesis Mining",
    "data_source": "holographic_universe_518k.jsonl",
    "mining_stats": stats,
    "seeds": final_seeds
}

os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    json.dump(output_data, f, indent=2)

print(f"💾 D-02 Seeds Saved: {OUTPUT_FILE}")
