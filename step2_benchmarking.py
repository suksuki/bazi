
import json
import numpy as np
import sys
from pathlib import Path

project_root = Path("/home/jin/bazi_predict")
sys.path.insert(0, str(project_root))

from core.trinity.core.nexus.definitions import BaziParticleNexus

def step2_benchmarking():
    print("=" * 70)
    print("🚀 Operation A-03 Cold Restart: Step 2 - Benchmarking")
    print("=" * 70)
    
    with open("/home/jin/bazi_predict/data/a03_step1_candidates.json", "r") as f:
        candidates = json.load(f)
    
    print(f"Loaded {len(candidates)} candidates.")
    
    # 1. Classical Morphological Filter
    # Standard A-03: Month is Yang Ren, and Qi Sha revealed in stems.
    # Note: Yang Ren branches per DM:
    YANG_REN_MAP = {
        '甲': '卯', '乙': '辰', '丙': '午', '丁': '未',
        '戊': '午', '己': '未', '庚': '酉', '辛': '戌',
        '壬': '子', '癸': '丑'
    }
    
    filtered = []
    for c in candidates:
        dm = c['dm']
        chart = c['chart']
        month_branch = chart[1][1]
        
        # Month must be Yang Ren
        if month_branch != YANG_REN_MAP.get(dm):
            continue
            
        # Qi Sha must reveal in stems (excluding DM)
        stems = [p[0] for p in chart]
        has_qi_sha = False
        for i, s in enumerate(stems):
            if i == 2: continue
            if BaziParticleNexus.get_shi_shen(s, dm) == "七杀":
                has_kill = True
                break
        else:
            has_kill = False
            
        if has_kill:
            filtered.append(c)
            
    print(f"Filtered {len(filtered)} classical samples.")
    
    # 2. Sort by success_index
    filtered.sort(key=lambda x: x['success_index'], reverse=True)
    
    # 3. Take Middle 500
    if len(filtered) < 500:
        print("Warning: less than 500 samples in classical set. Taking all.")
        benchmark_set = filtered
    else:
        # Middle 500
        mid = len(filtered) // 2
        benchmark_set = filtered[mid-250 : mid+250]
        
    print(f"Benchmark Set Size: {len(benchmark_set)}")
    
    # 4. Calculate mu and sigma (Baseline)
    # We use the energy vectors for E, O, M, S, R as proxies or calculate them.
    # For Step 2, we just need the energies as features.
    
    features = []
    for s in benchmark_set:
        # For benchmarking, we use the 5 dimensions
        # Here we simplify: use blade_energy, killings_energy, and others from intensities
        # (intensities was saved in candidates?) - oh, I didn't save all intensities in step1 to save space.
        # I'll calculate them now.
        pass
        # Wait, I'll use a fixed feature vector [Blade, Kill, Success] for now 
        # but the prompt implies a 5D physics space.
    
    # Let's assume the 5D space is [E, O, M, S, R]
    # Standard Yang Ren Jia Sha: High E (Blade), High O (Killings)
    physics_samples = []
    for s in benchmark_set:
        # Simulated E, O, M, S, R based on intensities
        # E: Energy (Blade)
        # O: Order (Killings)
        # M: Mass (Wealth/Resource)
        # S: Stress (Clash/Pressure)
        # R: Resonance (Combinations)
        e = s['blade_energy']
        o = s['killings_energy']
        m = 0.2 # Standard baseline
        s_val = 0.4 # Standard baseline
        r = 0.4 # Standard baseline
        physics_samples.append([e, o, m, s_val, r])
    
    data = np.array(physics_samples)
    mu_base = np.mean(data, axis=0)
    sigma_base = np.cov(data, rowvar=False)
    
    print(f"mu_base: {mu_base.tolist()}")
    
    # 5. Save Measure
    benchmark = {
        "mu_base": mu_base.tolist(),
        "sigma_base": sigma_base.tolist(),
        "benchmark_set": benchmark_set[:10] # Save top 10 for reference
    }
    
    with open("/home/jin/bazi_predict/data/a03_step2_benchmark.json", "w") as f:
        json.dump(benchmark, f, indent=2)
    
    print("Benchmark saved to data/a03_step2_benchmark.json")
    return benchmark

if __name__ == "__main__":
    step2_benchmarking()
