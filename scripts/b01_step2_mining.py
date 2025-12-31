import json
import os
import time

# ==========================================
# B-01 Step 2: Mining Protocol (Physical Mode)
# ==========================================

UNIVERSE_FILE = "core/data/holographic_universe_518k.jsonl"
OUTPUT_DIR = "core/subjects/holographic_pattern/mining_cache"
SEEDS_FILE = os.path.join(OUTPUT_DIR, "b01_tier_a_seeds.json")
ANOMALY_FILE = os.path.join(OUTPUT_DIR, "b01_tier_x_candidates.json")

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

print(f"📡 [Step 2 START] Initializing B-01 Mining (Physical Mode)...")
print(f"📂 Source Universe: {UNIVERSE_FILE}")
print(f"🌊 Prototype: Laminar Flow (High O, Low S)")

def mine_from_universe():
    seeds_tier_a = []
    candidates_tier_x = []
    
    total_scanned = 0
    
    with open(UNIVERSE_FILE, 'r', encoding='utf-8') as f:
        # Skip header
        next(f)
        
        for line in f:
            try:
                record = json.loads(line)
                total_scanned += 1
                t = record['tensor']
                uid = record['uid']
                y_true = record['y_true']
                
                # -------------------------------------------------
                # Filter A: Standard B-01 (Laminar Eating God)
                # Logic: High Order (O), Strong Self (E), Zero Stress (S)
                # -------------------------------------------------
                if (t['O'] > 0.60 and       # 食神旺
                    t['E'] > 0.45 and       # 身旺
                    t['S'] < 0.20 and       # 极其平稳 (Laminar)
                    t['M'] > 0.30 and       # 有财
                    y_true > 0.70):         # 成功/福气
                    
                    record['structure'] = "Eating_God_Pure"
                    # Add simulated structural tags for consistency with previous steps
                    record['tags'] = ["Artist", "Scholar", "Laminar_Flow"]
                    seeds_tier_a.append(record)
                
                # -------------------------------------------------
                # Filter B: Singularity (Owl/Reversal)
                # Logic: High Resource (E), Visible Output (O), High Stress (S)
                # -------------------------------------------------
                elif (t['E'] > 0.75 and      # 极强印 (可能是偏印)
                      t['O'] > 0.30 and      # 食神被压制但仍在
                      t['S'] > 0.40 and      # 有显著压力 (枭神夺食的体现)
                      y_true > 0.75):        # 依然极度成功 (奇点特征)
                    
                    record['structure'] = "Owl_Dominant_Variant"
                    record['tags'] = ["Reversal", "Owl_Structure"]
                    candidates_tier_x.append(record)

            except json.JSONDecodeError:
                continue

            # Limit memory usage - we only need enough seeds
            if len(seeds_tier_a) >= 2000 and len(candidates_tier_x) >= 200:
                break
    
    return seeds_tier_a, candidates_tier_x, total_scanned

# Execute Mining
print(f"⛏️  Scanning Universe File...")
start_time = time.time()
seeds, anomalies, scanned_count = mine_from_universe()
duration = time.time() - start_time

# Limit to requested counts for the output file
final_seeds = seeds[:500]
final_anomalies = anomalies[:60]

# Stats
if final_seeds:
    avg_o = sum(s['tensor']['O'] for s in final_seeds) / len(final_seeds)
    avg_s = sum(s['tensor']['S'] for s in final_seeds) / len(final_seeds)
else:
    avg_o = 0
    avg_s = 0

print(f"✅ Scanning Complete in {duration:.2f}s.")
print(f"   - Total Scanned: {scanned_count}")
print(f"   - Tier A Matched: {len(seeds)} (Keeping top 500)")
print(f"   - Tier X Matched: {len(anomalies)} (Keeping top 60)")
print(f"📊 Tier A Physics Preview:")
print(f"   - Avg O (Flow): {avg_o:.4f}")
print(f"   - Avg S (Turbulence): {avg_s:.4f} (Target < 0.2)")

# Write Files
with open(SEEDS_FILE, 'w', encoding='utf-8') as f:
    json.dump({
        "pattern_id": "B-01",
        "step": "Step 2 - Stratification (Physical)",
        "source": "holographic_universe_518k.jsonl",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "seed_count": len(final_seeds),
        "seeds": final_seeds
    }, f, indent=2)

with open(ANOMALY_FILE, 'w', encoding='utf-8') as f:
    json.dump({
        "pattern_id": "B-01",
        "step": "Step 2 - Singularity Extraction (Physical)",
        "candidate_count": len(final_anomalies),
        "description": "High E + High S + High Success (The Reversal)",
        "candidates": final_anomalies
    }, f, indent=2)

print(f"💾 PHYSICAL FILES WRITTEN to {OUTPUT_DIR}")
