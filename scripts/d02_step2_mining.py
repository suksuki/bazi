
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
from core.physics_engine import compute_energy_flux, calculate_clash_count, check_combination

def run_d02_mining():
    print("🚀 Initializing D-02 Mining Engine (High Kinetic Flux Scan)...")
    engine = SyntheticBaziEngine()
    
    l1_count = 0
    l3_candidates = []
    
    # Pre-calculate DayStem to Month Branch mappings for Indirect Wealth
    dm_to_months = {}
    for dm in "甲乙丙丁戊己庚辛壬癸":
        valid_months = []
        for branch, data in BaziParticleNexus.BRANCHES.items():
            main_qi = data[2][0][0]
            if BaziParticleNexus.get_shi_shen(main_qi, dm) == "偏财":
                valid_months.append(branch)
        dm_to_months[dm] = valid_months
    
    start_time = time.time()
    total_checks = 100000 
    
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
        
        # --- D-02 Logic Start ---
        
        # 1. Classical Anchor (Month Branch Main Qi is Indirect Wealth)
        if month_branch not in dm_to_months[dm]:
            continue
            
        # 2. Physics: Indirect Wealth Dominance
        iw_energy = compute_energy_flux(chart, dm, "偏财")
        dw_energy = compute_energy_flux(chart, dm, "正财")
        
        if iw_energy <= 0.35: # Base threshold
            continue
        if dw_energy > iw_energy: # Purity check
            continue
            
        # 3. Physics: Root/Resilience Check
        # D-02 needs a captain for the turbulent ship
        self_energy = compute_energy_flux(chart, dm, "比肩") + \
                      compute_energy_flux(chart, dm, "劫财") + \
                      compute_energy_flux(chart, dm, "正印") + \
                      compute_energy_flux(chart, dm, "偏印")
        
        if self_energy <= 0.15: # Critical line
            continue
            
        # 4. Physics: Kinetic Flux (Clash OR Combination)
        clash_count = calculate_clash_count(chart)
        
        comb_count = 0
        branches = [p[1] for p in chart]
        for bi in range(len(branches)):
            for bj in range(bi+1, len(branches)):
                if check_combination(branches[bi], branches[bj]):
                    comb_count += 1
        
        # D-02 Physics: Needs movement (Clash) OR Connection (Comb) or huge mass
        has_kinetic_potential = (clash_count >= 1) or (comb_count >= 1)
        
        if not has_kinetic_potential and iw_energy < 0.6:
            # If static, needs massive wealth to compensate
            continue
            
        # 5. Physics: Controlled Competition
        rob_energy = compute_energy_flux(chart, dm, "劫财")
        if rob_energy > iw_energy * 0.9: # Tolerates more than D-01, but not total dominance
            continue

        l1_count += 1
        
        # L3 Selection (Refining candidates)
        l3_candidates.append({
            "chart": chart,
            "iw_energy": round(iw_energy, 3),
            "self_energy": round(self_energy, 3),
            "clash_count": clash_count,
            "comb_count": comb_count
        })
        
        if len(l3_candidates) >= 600:
            break

    elapsed = time.time() - start_time
    
    # Extrapolate
    extrapolated_l1 = int(l1_count * (518400 / (i + 1)))
    
    seeds = l3_candidates[:500]
    # Simple formatting for preview
    avg_iw = sum(s["iw_energy"] for s in seeds) / len(seeds) if seeds else 0
    avg_self = sum(s["self_energy"] for s in seeds) / len(seeds) if seeds else 0
    
    print(f"--- D-02 Step 2 Report (Indirect Wealth) ---")
    print(f"L1 捕获预估 (Extrapolated): {extrapolated_l1}")
    print(f"L3 种子数量: {len(seeds)}")
    print(f"L3 种子特征预览 (Mean Vector): IW={avg_iw:.4f}, Self={avg_self:.4f}")
    print(f"耗时: {elapsed:.2f}s")
    
    out_path = Path(__file__).parent / "d02_tier_a_seeds.json"
    print(f"📂 Saving seeds to: {out_path}")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(seeds, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    run_d02_mining()
