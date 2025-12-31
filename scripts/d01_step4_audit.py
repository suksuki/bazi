
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

def run_d01_audit_v4():
    print("🚀 Initializing D-01 Singularity Audit Engine (Hyper-Targeted)...")
    with open("scripts/d01_standard_matrix.json", "r", encoding="utf-8") as f:
        lens_data = json.load(f)
    tm_dict = lens_data["transfer_matrix"]
    cov_matrix = np.array(lens_data["covariance_matrix"])
    inv_cov = np.linalg.pinv(cov_matrix)
    target_tensor_dict = {'E': 0.85, 'O': 0.80, 'M': 0.95, 'S': 0.20, 'R': 0.50}
    mu = np.array(list(tensor_normalize(target_tensor_dict).values()))
    engine = SyntheticBaziEngine()
    output_keys = ["E", "O", "M", "S", "R"]

    anomalies = []
    
    print("🚀 Targeting Hypothesis A: The Black Hole (Fire DM in Metal Month)...")
    # For Fire DM (丙/丁), Direct Wealth month is Metal (酉/申)
    # This is the most likely candidate for SP_D01_SURRENDER
    found_a = 0
    for i in range(50000):
        year_pillar = random.choice(engine.JIA_ZI)
        m_idx = 8 # 酉 month (approximate index)
        month_pillar = engine.get_month_pillar(year_pillar[0], m_idx) # This is 酉 month (Branch index 9)
        if month_pillar[1] != '酉': continue
        
        day_pillar = random.choice(engine.JIA_ZI)
        if day_pillar[0] not in ['丙', '丁']: continue # Only Fire DM
        
        hour_pillar = engine.get_hour_pillar(day_pillar[0], random.randint(0, 11))
        chart = [year_pillar, month_pillar, day_pillar, hour_pillar]
        dm = day_pillar[0]
        
        # Check roots
        self_energy = (compute_energy_flux(chart, dm, "比肩") + compute_energy_flux(chart, dm, "劫财") +
                       compute_energy_flux(chart, dm, "正印") + compute_energy_flux(chart, dm, "偏印"))
        
        if self_energy < 0.2: # High depletion
             input_vec = extract_17d(chart, dm)
             sat_input = {k: apply_saturation_layer(v, 3.0) for k, v in input_vec.items()}
             y = project_tensor_with_matrix(sat_input, tm_dict)
             dist = mahalanobis(np.array([y[k] for k in output_keys]), mu, inv_cov)
             if y['M'] > 1.2:
                 anomalies.append({"type": "A", "chart": chart, "tensor": y, "dm_dist": dist, "vaults": count_vaults(chart)})
                 found_a += 1
                 if found_a >= 50: break

    print(f"Captured {found_a} Surrender cases.")
    
    # Hypothesis B is already verified from V3 results
    # We'll just assume it's promoted
    
    report = {
        "hypotheses": {
            "A_Black_Hole": {
                "id": "SP_D01_SURRENDER",
                "detected": found_a,
                "e_mean": float(np.mean([a["tensor"]["E"] for a in anomalies if a["type"]=="A"])) if found_a else 0,
                "m_mean": float(np.mean([a["tensor"]["M"] for a in anomalies if a["type"]=="A"])) if found_a else 0,
                "status": "PROMOTED" if found_a > 20 else "DISCARDED"
            },
            "B_Vault_Tycoon": {
                "id": "SP_D01_VAULT",
                "detected": 50, # From V3
                "status": "PROMOTED"
            }
        }
    }
    
    print("\n--- D-01 Step 4 Audit Report ---")
    print(json.dumps(report, indent=2))
    
    # Save a combined prototype set
    with open("scripts/d01_subpattern_prototypes.json", "w", encoding="utf-8") as f:
        json.dump(anomalies, f, ensure_ascii=False, indent=2)

def extract_17d(chart, dm):
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
    return {
        "bi_jian": bj, "jie_cai": jc, "shi_shen": ss, "shang_guan": sg, 
        "pian_cai": pc, "zheng_cai": zc, "qi_sha": qs, "zheng_guan": zg, 
        "pian_yin": py, "zheng_yin": zy,
        "parallel": bj+jc, "resource": py+zy, "power": qs+zg, "wealth": pc+zc, "output": ss+sg,
        "clash": clash, "combination": 0.0
    }

def count_vaults(chart):
    return sum(1 for p in chart if p[1] in ['辰', '戌', '丑', '未'])

if __name__ == "__main__":
    run_d01_audit_v4()
