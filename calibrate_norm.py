
import sys, json
from pathlib import Path
project_root = Path("/home/jin/bazi_predict")
sys.path.insert(0, str(project_root))
from core.trinity.core.engines.synthetic_bazi_engine import SyntheticBaziEngine
from core.trinity.core.nexus.definitions import BaziParticleNexus
from core.config_schema import DEFAULT_FULL_ALGO_PARAMS

PHYSICS_CFG = DEFAULT_FULL_ALGO_PARAMS['physics']
SEASON_WEIGHTS = PHYSICS_CFG.get('seasonWeights', {})
HIDDEN_RATIOS = PHYSICS_CFG.get('hiddenStemRatios', {})
PILLAR_WEIGHTS = PHYSICS_CFG.get('pillarWeights', {})

def get_energies(chart, day_master):
    month_branch = chart[1][1]
    month_element = BaziParticleNexus.get_branch_main_element(month_branch)
    blade = 0.0
    kill = 0.0
    for idx, pillar_str in enumerate(chart):
        stem_char, branch_char = pillar_str
        pillar_w = PILLAR_WEIGHTS.get(['year', 'month', 'day', 'hour'][idx], 1.0)
        ts = BaziParticleNexus.get_shi_shen(stem_char, day_master)
        s_elem = BaziParticleNexus.get_element(stem_char)
        phase = 'wang' if s_elem == month_element else 'si'
        s_energy = 1.5 * SEASON_WEIGHTS.get(phase, 0.45) * pillar_w
        if ts in ["比肩", "劫财", "正印", "偏印"]: blade += s_energy
        elif ts in ["七杀", "正官"]: kill += s_energy
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
res = []
for i, chart in enumerate(engine.generate_all_bazi()):
    if i > 10000: break
    res.append(get_energies(chart, chart[2][0]))

for norm in [3.0, 3.5, 4.0]:
    count = sum(1 for b, k in res if b/norm > 0.65 and k/norm > 0.60)
    print(f"Norm {norm}: {count} samples ({(count/10000)*518400:.0f} total)")
