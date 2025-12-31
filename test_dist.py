
import sys
from pathlib import Path
import json
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

def get_energies(chart, day_master):
    month_branch = chart[1][1]
    month_element = BaziParticleNexus.get_branch_main_element(month_branch)
    blade = 0.0
    kill = 0.0
    for idx, pillar_str in enumerate(chart):
        stem_char = pillar_str[0]
        branch_char = pillar_str[1]
        pillar_w = PILLAR_WEIGHTS.get(['year', 'month', 'day', 'hour'][idx], 1.0)
        
        # Stem
        ts = BaziParticleNexus.get_shi_shen(stem_char, day_master)
        s_elem = BaziParticleNexus.get_element(stem_char)
        phase = 'wang' if s_elem == month_element else 'si'
        s_energy = 1.5 * SEASON_WEIGHTS.get(phase, 0.45) * pillar_w
        if ts in ["比肩", "劫财", "正印", "偏印"]: blade += s_energy
        elif ts in ["七杀", "正官"]: kill += s_energy
        
        # Hidden
        raw_hidden = BaziParticleNexus.get_branch_weights(branch_char)
        for h_idx, (hs, _) in enumerate(raw_hidden):
            ths = BaziParticleNexus.get_shi_shen(hs, day_master)
            h_elem = BaziParticleNexus.get_element(hs)
            phase = 'wang' if h_elem == month_element else 'si'
            ratio = 0.6 if h_idx == 0 else (0.3 if h_idx == 1 else 0.1)
            h_energy = ratio * SEASON_WEIGHTS.get(phase, 0.45) * pillar_w
            if ths in ["比肩", "劫财", "正印", "偏印"]: blade += h_energy
            elif ths in ["七杀", "正官"]: kill += h_energy
    return blade, kill

engine = SyntheticBaziEngine()
bazi_gen = engine.generate_all_bazi()
counts = {}

for i, chart in enumerate(bazi_gen):
    if i > 5000: break
    b, k = get_energies(chart, chart[2][0])
    for tb in [1.5, 2.0, 2.5, 3.0]:
        for tk in [1.2, 1.5, 2.0]:
            if b > tb and k > tk:
                tag = f"B{tb}_K{tk}"
                counts[tag] = counts.get(tag, 0) + 1

print(json.dumps(counts, indent=2))
