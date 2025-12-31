
import sys
import os
import time
import random
from pathlib import Path
import json

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from core.trinity.core.engines.synthetic_bazi_engine import SyntheticBaziEngine
from core.trinity.core.nexus.definitions import BaziParticleNexus
from core.physics_engine import compute_energy_flux

def run_d01_mining():
    print("🚀 Initializing D-01 Mining Engine (Optimized Random Scan)...")
    engine = SyntheticBaziEngine()
    
    l1_count = 0
    l3_candidates = []
    
    # Pre-calculate DayStem to Month Branch mappings
    dm_to_months = {}
    for dm in "甲乙丙丁戊己庚辛壬癸":
        valid_months = []
        for branch, data in BaziParticleNexus.BRANCHES.items():
            main_qi = data[2][0][0]
            if BaziParticleNexus.get_shi_shen(main_qi, dm) == "正财":
                valid_months.append(branch)
        dm_to_months[dm] = valid_months
    
    start_time = time.time()
    total_checks = 100000 # Enough to find 500 seeds
    
    for i in range(total_checks):
        # Random Bazi Generation
        year_pillar = random.choice(engine.JIA_ZI)
        m_idx = random.randint(1, 12)
        month_pillar = engine.get_month_pillar(year_pillar[0], m_idx)
        day_pillar = random.choice(engine.JIA_ZI)
        hour_pillar = engine.get_hour_pillar(day_pillar[0], random.randint(0, 11))
        
        chart = [year_pillar, month_pillar, day_pillar, hour_pillar]
        dm = day_pillar[0]
        month_branch = month_pillar[1]
        
        # L1.1 Classical Anchor
        if month_branch not in dm_to_months[dm]:
            continue
            
        # L1.2-L1.4 Heavy Physics
        w_energy = compute_energy_flux(chart, dm, "正财") + \
                   compute_energy_flux(chart, dm, "偏财") + \
                   compute_energy_flux(chart, dm, "食神") + \
                   compute_energy_flux(chart, dm, "伤官")
        
        if w_energy <= 0.40:
            continue
            
        self_energy = compute_energy_flux(chart, dm, "比肩") + \
                      compute_energy_flux(chart, dm, "劫财") + \
                      compute_energy_flux(chart, dm, "正印") + \
                      compute_energy_flux(chart, dm, "偏印")
        
        if self_energy <= 0.15:
            continue
            
        rob_energy = compute_energy_flux(chart, dm, "劫财")
        if rob_energy >= 0.35:
            continue
        
        l1_count += 1
        
        # L3 Selection Criteria
        e_m_ratio = self_energy / w_energy if w_energy > 0 else 0
        if 0.6 <= e_m_ratio <= 1.2:
            # Simple Clash Check
            all_branches = [p[1] for p in chart]
            clash_found = False
            for bi in range(len(all_branches)):
                for bj in range(bi + 1, len(all_branches)):
                    b1, b2 = all_branches[bi], all_branches[bj]
                    clash_pairs = [('子','午'), ('丑','未'), ('寅','申'), ('卯','酉'), ('辰','戌'), ('巳','亥')]
                    if (b1, b2) in clash_pairs or (b2, b1) in clash_pairs:
                        clash_found = True
                        break
                if clash_found: break
            
            if not clash_found:
                l3_candidates.append({
                    "chart": chart,
                    "e_m_ratio": round(e_m_ratio, 3),
                    "w_energy": round(w_energy, 3),
                    "e_energy": round(self_energy, 3)
                })
        
        if len(l3_candidates) >= 600:
            break

    elapsed = time.time() - start_time
    
    # Extrapolate L1 count to full population
    # 518,400 total. We checked total_checks.
    extrapolated_l1 = int(l1_count * (518400 / (i + 1)))
    
    seeds = l3_candidates[:500]
    avg_e = sum(s["e_energy"] for s in seeds) / len(seeds) if seeds else 0
    avg_m = sum(s["w_energy"] for s in seeds) / len(seeds) if seeds else 0
    
    print(f"--- D-01 Step 2 Report ---")
    print(f"L1 捕获预估 (Extrapolated): {extrapolated_l1}")
    print(f"L3 种子数量: {len(seeds)}")
    print(f"L3 种子特征预览 (Mean Vector): E={avg_e:.4f}, M={avg_m:.4f}")
    print(f"耗时: {elapsed:.2f}s")
    
    with open("scripts/d01_tier_a_seeds.json", "w", encoding="utf-8") as f:
        json.dump(seeds, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    run_d01_mining()
