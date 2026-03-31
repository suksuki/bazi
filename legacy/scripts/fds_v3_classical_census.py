import json
import os
import logging
from typing import Dict, List, Tuple
from tqdm import tqdm

# Constants from SyntheticBaziEngine & PhysicsProcessor
STEMS = "甲乙丙丁戊己庚辛壬癸"
BRANCHES = "子丑寅卯辰巳午未申酉戌亥"
JIA_ZI = [STEMS[i % 10] + BRANCHES[i % 12] for i in range(60)]

GENESIS_HIDDEN_MAP = {
    '子': [('癸', 10)],
    '丑': [('己', 10), ('癸', 7), ('辛', 3)],
    '寅': [('甲', 10), ('丙', 7), ('戊', 3)],
    '卯': [('乙', 10)],
    '辰': [('戊', 10), ('乙', 7), ('癸', 3)],
    '巳': [('丙', 10), ('戊', 7), ('庚', 3)],
    '午': [('丁', 10), ('己', 7)],
    '未': [('己', 10), ('丁', 7), ('乙', 3)],
    '申': [('庚', 10), ('壬', 7), ('戊', 3)],
    '酉': [('辛', 10)],
    '戌': [('戊', 10), ('辛', 7), ('丁', 3)],
    '亥': [('壬', 10), ('甲', 7)]
}

PILLAR_WEIGHTS = {'year': 1.0, 'month': 1.8, 'day': 1.5, 'hour': 1.2}
BASE_SCORE = 10.0

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - FDS_CENSUS - %(levelname)s - %(message)s')
logger = logging.getLogger("FDS_CENSUS")

BASELINE_FILE = "/home/jin/bazi_predict/core/data/classical_abundance_baseline.json"
TOTAL_SAMPLES = 518400

# Ten God Mapping Logic
TEN_GOD_MAP = {
    # (DM_Stem, Target_Stem) -> TenGod Key
}

def get_ten_god(dm_stem: str, target_stem: str) -> str:
    """
    Returns the Ten God key for a target stem relative to a day master stem.
    """
    dm_idx = STEMS.index(dm_stem)
    target_idx = STEMS.index(target_stem)
    
    # Polarities: 0 for Yang, 1 for Yin
    dm_pol = dm_idx % 2
    target_pol = target_idx % 2
    same_pol = (dm_pol == target_pol)
    
    # 5-Element relations
    # 0: Self, 1: Output, 2: Wealth, 3: Officer, 4: Resource
    rel = ((target_idx // 2) - (dm_idx // 2)) % 5
    
    mapping = {
        (0, True): "bi_jian",
        (0, False): "jie_cai",
        (1, True): "shi_shen",
        (1, False): "shang_guan",
        (2, True): "pian_cai",
        (2, False): "zheng_cai",
        (3, True): "qi_sha",
        (3, False): "zheng_guan",
        (4, True): "pian_yin",
        (4, False): "zheng_yin",
    }
    return mapping.get((rel, same_pol), "unknown")

def calculate_shishen_energies(bazi: List[str]) -> Dict[str, float]:
    """
    Calculates 10 God energies using V3.0 Physics Layer 1 Logic.
    """
    dm_stem = bazi[2][0]
    energies = {
        "bi_jian": 0.0, "jie_cai": 0.0,
        "shi_shen": 0.0, "shang_guan": 0.0,
        "zheng_cai": 0.0, "pian_cai": 0.0,
        "zheng_guan": 0.0, "qi_sha": 0.0,
        "zheng_yin": 0.0, "pian_yin": 0.0
    }
    
    pillar_names = ['year', 'month', 'day', 'hour']
    
    for idx, pillar in enumerate(bazi):
        stem = pillar[0]
        branch = pillar[1]
        w_p = PILLAR_WEIGHTS[pillar_names[idx]]
        
        # Stem Contribution (Skip DM itself for counting)
        if idx != 2:
            god = get_ten_god(dm_stem, stem)
            energies[god] += BASE_SCORE * w_p
        
        # Branch Contribution (Hidden Stems)
        hiddens = GENESIS_HIDDEN_MAP.get(branch, [])
        for h_stem, h_weight in hiddens:
            god = get_ten_god(dm_stem, h_stem)
            energies[god] += h_weight * w_p
            
    return energies

def recover_bazi(uid: int) -> List[str]:
    """
    Reconstructs Bazi pillars from UID.
    """
    temp = uid
    h_idx = temp % 12
    temp //= 12
    day_idx = temp % 60
    temp //= 60
    month_idx = temp % 12
    temp //= 12
    year_idx = temp % 60
    
    year_pillar = JIA_ZI[year_idx]
    
    # Month calculation based on year stem
    y_stem = year_pillar[0]
    stem_map = {"甲": 2, "己": 2, "乙": 4, "庚": 4, "丙": 6, "辛": 6, "丁": 8, "壬": 8, "戊": 0, "癸": 0}
    start_stem_idx = stem_map.get(y_stem, 0)
    month_stem_idx = (start_stem_idx + month_idx) % 10
    month_branch_idx = (2 + month_idx) % 12
    month_pillar = STEMS[month_stem_idx] + BRANCHES[month_branch_idx]
    
    day_pillar = JIA_ZI[day_idx]
    
    # Hour calculation based on day stem
    d_stem = day_pillar[0]
    h_stem_map = {"甲": 0, "己": 0, "乙": 2, "庚": 2, "丙": 4, "辛": 4, "丁": 6, "壬": 6, "戊": 8, "癸": 8}
    h_start_stem_idx = h_stem_map.get(d_stem, 0)
    hour_stem_idx = (h_start_stem_idx + h_idx) % 10
    hour_branch_idx = h_idx % 12
    hour_pillar = STEMS[hour_stem_idx] + BRANCHES[hour_branch_idx]
    
    return [year_pillar, month_pillar, day_pillar, hour_pillar]

def filter_classical(pattern_id: str, x: Dict[str, float]) -> bool:
    """
    Pure Classical Logic Filters (V3.1 Census Edition).
    """
    if pattern_id == "A-01": # 正官格: 官星露头且无伤
        return x.get('zheng_guan', 0) > 25.0 and x.get('shang_guan', 0) < 10.0
    elif pattern_id == "A-03": # 羊刃架杀格: 劫财高能 + 七杀
        return x.get('jie_cai', 0) > 40.0 and x.get('qi_sha', 0) > 15.0
    elif pattern_id == "B-01": # 食神格: 食神泄秀
        return x.get('shi_shen', 0) > 30.0 and x.get('pian_yin', 0) < 12.0
    elif pattern_id == "B-02": # 伤官格: 伤官高能
        return x.get('shang_guan', 0) > 35.0
    elif pattern_id == "D-01": # 正财格: 正财得位
        return x.get('zheng_cai', 0) > 28.0 and x.get('jie_cai', 0) < 15.0
    elif pattern_id == "D-02": # 偏财格: 偏财横溢
        return x.get('pian_cai', 0) > 35.0
    return False

def run_cosmic_census():
    patterns = ["A-01", "A-03", "B-01", "B-02", "D-01", "D-02"]
    stats = {pid: {"hits": 0} for pid in patterns}
    
    logger.info(f"🚀 Starting Cosmic Census (V3.1) over {TOTAL_SAMPLES} charts...")
    
    for uid in tqdm(range(TOTAL_SAMPLES)):
        bazi = recover_bazi(uid)
        energies = calculate_shishen_energies(bazi)
        
        for pid in patterns:
            if filter_classical(pid, energies):
                stats[pid]["hits"] += 1

    # Calculate Abundance
    final_stats = {}
    for pid, data in stats.items():
        abundance = (data["hits"] / TOTAL_SAMPLES) * 100
        final_stats[pid] = {
            "n_hit": data["hits"],
            "abundance_pct": round(abundance, 4),
            "n_total": TOTAL_SAMPLES
        }
        logger.info(f"📊 Pattern {pid}: Hit {data['hits']} | Abundance {abundance:.4f}%")

    # Save Baseline
    output = {
        "version": "3.1",
        "date": "2026-01-01",
        "protocol": "Genesis Physics L1",
        "total_processed": TOTAL_SAMPLES,
        "patterns": final_stats
    }
    
    os.makedirs(os.path.dirname(BASELINE_FILE), exist_ok=True)
    with open(BASELINE_FILE, 'w') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    logger.info(f"✅ Cosmic Baseline Saved: {BASELINE_FILE}")

if __name__ == "__main__":
    run_cosmic_census()
