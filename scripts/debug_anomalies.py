
import sys
import os
import json
import numpy as np
import random
from pathlib import Path
from scipy.spatial.distance import mahalanobis

project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from core.trinity.core.middleware.holographic_fitter import HolographicMatrixFitter
from core.physics_engine import compute_energy_flux, calculate_clash_count
from core.math_engine import tensor_normalize, project_tensor_with_matrix, apply_saturation_layer
from core.trinity.core.engines.synthetic_bazi_engine import SyntheticBaziEngine
from core.trinity.core.nexus.definitions import BaziParticleNexus

def debug_anomalies():
    with open("scripts/d01_standard_matrix.json", "r", encoding="utf-8") as f:
        lens_data = json.load(f)
    tm_dict = lens_data["transfer_matrix"]
    cov_matrix = np.array(lens_data["covariance_matrix"])
    inv_cov = np.linalg.pinv(cov_matrix)
    target_tensor_dict = {'E': 0.85, 'O': 0.80, 'M': 0.95, 'S': 0.20, 'R': 0.50}
    mu = np.array(list(tensor_normalize(target_tensor_dict).values()))
    
    engine = SyntheticBaziEngine()
    output_keys = ["E", "O", "M", "S", "R"]
    dm_to_months = {}
    for dm in "甲乙丙丁戊己庚辛壬癸":
        valid_months = []
        for branch, data in BaziParticleNexus.BRANCHES.items():
            if data[2][0][0] and BaziParticleNexus.get_shi_shen(data[2][0][0], dm) == "正财":
                valid_months.append(branch)
        dm_to_months[dm] = valid_months

    anomalies = []
    checked = 0
    random.seed(42)
    
    while len(anomalies) < 10 and checked < 100000:
        checked += 1
        year_pillar = random.choice(engine.JIA_ZI)
        m_idx = random.randint(1, 12)
        month_pillar = engine.get_month_pillar(year_pillar[0], m_idx)
        day_pillar = random.choice(engine.JIA_ZI)
        hour_pillar = engine.get_hour_pillar(day_pillar[0], random.randint(0, 11))
        chart = [year_pillar, month_pillar, day_pillar, hour_pillar]
        dm = day_pillar[0]
        if month_pillar[1] not in dm_to_months[dm]: continue
        
        bj = compute_energy_flux(chart, dm, "比肩")
        jc = compute_energy_flux(chart, dm, "劫财")
        ss = compute_energy_flux(chart, dm, "食神")
        sg = compute_energy_flux(chart, dm, "伤官")
        pc = compute_energy_flux(chart, dm, "偏财")
        zc = compute_energy_flux(chart, dm, "正财")
        qs = compute_energy_flux(chart, dm, "七杀")
        zg = compute_energy_flux(chart, dm, "正官")
        py = compute_energy_flux(chart, dm, "偏印")
        zy = compute_energy_flux(chart, dm, "正印")
        clash = calculate_clash_count(chart)
        input_vec = {
            "bi_jian": bj, "jie_cai": jc, "shi_shen": ss, "shang_guan": sg, 
            "pian_cai": pc, "zheng_cai": zc, "qi_sha": qs, "zheng_guan": zg, 
            "pian_yin": py, "zheng_yin": zy,
            "parallel": bj+jc, "resource": py+zy, "power": qs+zg, "wealth": pc+zc, "output": ss+sg,
            "clash": clash, "combination": 0.0
        }
        sat_input = {k: apply_saturation_layer(v, 3.0) for k, v in input_vec.items()}
        y_proj_dict = project_tensor_with_matrix(sat_input, tm_dict)
        y_vec = np.array([y_proj_dict[k] for k in output_keys])
        dm_dist = mahalanobis(y_vec, mu, inv_cov)
        
        if dm_dist > 5.0:
            vaults = sum(1 for p in chart if p[1] in ['辰', '戌', '丑', '未'])
            anomalies.append({"tensor": y_proj_dict, "dm": dm_dist, "vaults": vaults, "chart": chart})

    print(json.dumps(anomalies, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    debug_anomalies()
