
import sys, json, time, random
from pathlib import Path
project_root = Path("/home/jin/bazi_predict")
sys.path.insert(0, str(project_root))
from core.trinity.core.engines.synthetic_bazi_engine import SyntheticBaziEngine
from core.trinity.core.nexus.definitions import PhysicsConstants, BaziParticleNexus
from core.config_schema import DEFAULT_FULL_ALGO_PARAMS

PHYSICS_CFG = DEFAULT_FULL_ALGO_PARAMS['physics']
SEASON_WEIGHTS = PHYSICS_CFG.get('seasonWeights', {})
HIDDEN_RATIOS = PHYSICS_CFG.get('hiddenStemRatios', {})
PILLAR_WEIGHTS = PHYSICS_CFG.get('pillarWeights', {})
STRUCTURE_PARAMS = DEFAULT_FULL_ALGO_PARAMS.get('structure', {})

def step1_mining():
    print("=" * 70)
    print("🚀 Operation A-03 Cold Restart: Step 1 - The Mining")
    print("=" * 70)
    engine = SyntheticBaziEngine()
    bazi_gen = engine.generate_all_bazi()
    candidates = []
    total = 518400
    count = 0
    start_time = time.time()
    NORM_FACTOR = 3.6 # Adjusted for ~12k samples
    threshold_blade = 0.65
    threshold_killings = 0.60
    
    for chart in bazi_gen:
        count += 1
        day_master = chart[2][0]
        month_branch = chart[1][1]
        month_element = BaziParticleNexus.get_branch_main_element(month_branch)
        b = 0.0
        k = 0.0
        for idx, pillar in enumerate(chart):
            s_char, b_char = pillar
            pw = PILLAR_WEIGHTS.get(['year', 'month', 'day', 'hour'][idx], 1.0)
            ts = BaziParticleNexus.get_shi_shen(s_char, day_master)
            s_elem = BaziParticleNexus.get_element(s_char)
            phase = 'wang' if s_elem == month_element else 'si'
            s_e = 1.5 * SEASON_WEIGHTS.get(phase, 0.45) * pw
            if ts in ["比肩", "劫财", "正印", "偏印"]: b += s_e
            elif ts in ["七杀", "正官"]: k += s_e
            hidden = BaziParticleNexus.get_branch_weights(b_char)
            for h_idx, (hs, _) in enumerate(hidden):
                ths = BaziParticleNexus.get_shi_shen(hs, day_master)
                h_elem = BaziParticleNexus.get_element(hs)
                h_phase = 'wang' if h_elem == month_element else 'si'
                ratio = 0.6 if h_idx == 0 else (0.3 if h_idx == 1 else 0.1)
                h_e = ratio * SEASON_WEIGHTS.get(h_phase, 0.45) * pw
                if ths in ["比肩", "劫财", "正印", "偏印"]: b += h_e
                elif ths in ["七杀", "正官"]: k += h_e
        bn, kn = b/NORM_FACTOR, k/NORM_FACTOR
        if bn > threshold_blade and kn > threshold_killings:
            success_index = (bn + kn) / 2.0 * (1.0 - abs(bn - kn)) + random.uniform(-0.1, 0.1)
            candidates.append({"chart": chart, "dm": day_master, "blade_energy": round(bn, 4), "killings_energy": round(kn, 4), "success_index": round(success_index, 4)})
        if count % 100000 == 0:
            print(f"Scanned {count}/{total} | Captured: {len(candidates)}")
    
    print(f"\n✅ Captured {len(candidates)} raw candidates.")
    with open("/home/jin/bazi_predict/data/a03_step1_candidates.json", "w") as f:
        json.dump(candidates, f, indent=2)
    return len(candidates)

if __name__ == "__main__":
    step1_mining()
