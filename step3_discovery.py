
import json
import numpy as np
import sys
from pathlib import Path
from sklearn.cluster import DBSCAN

project_root = Path("/home/jin/bazi_predict")
sys.path.insert(0, str(project_root))

def mahalanobis(x, mean, inv_cov):
    x_minus_mu = x - mean
    return np.sqrt(np.dot(np.dot(x_minus_mu, inv_cov), x_minus_mu.T))

def step3_discovery():
    print("=" * 70)
    print("🚀 Operation A-03 Cold Restart: Step 3 - Singularity Discovery")
    print("=" * 70)
    
    with open("/home/jin/bazi_predict/data/a03_step1_candidates.json", "r") as f:
        candidates = json.load(f)
    
    with open("/home/jin/bazi_predict/data/a03_step2_benchmark.json", "r") as f:
        benchmark = json.load(f)
        
    mu = np.array(benchmark["mu_base"])
    sigma = np.array(benchmark["sigma_base"])
    
    # Calculate inverse covariance for Mahalanobis
    # Add small epsilon to diagonal for stability
    inv_sigma = np.linalg.inv(sigma + np.eye(5) * 1e-6)
    
    print(f"Total candidates to scan: {len(candidates)}")
    
    extreme_success = []
    
    for c in candidates:
        # Construct physics vector (same as benchmark)
        e = c['blade_energy']
        o = c['killings_energy']
        m = 0.2
        s_val = 0.4
        r = 0.4
        x = np.array([e, o, m, s_val, r])
        
        dm_dist = mahalanobis(x, mu, inv_sigma)
        
        # Criteria: High distance (Singularity) and High Success
        if dm_dist > 5.0 and c['success_index'] > 1.2:
            c['mahalanobis_dist'] = dm_dist
            extreme_success.append(c)
            
    print(f"Captured {len(extreme_success)} singular successful samples.")
    
    if not extreme_success:
        print("No extreme success samples found. Adjusting thresholds...")
        # Fallback to top dist samples
        extreme_success = sorted(candidates, key=lambda x: x['success_index'], reverse=True)[:100]
        for c in extreme_success:
             x = np.array([c['blade_energy'], c['killings_energy'], 0.2, 0.4, 0.4])
             c['mahalanobis_dist'] = mahalanobis(x, mu, inv_sigma)
    
    # Clustering
    features = np.array([[c['blade_energy'], c['killings_energy'], c['mahalanobis_dist'], c['success_index']] for c in extreme_success])
    # Normalize features for clustering
    f_mean = np.mean(features, axis=0)
    f_std = np.std(features, axis=0) + 1e-6
    f_norm = (features - f_mean) / f_std
    
    db = DBSCAN(eps=0.5, min_samples=5).fit(f_norm)
    labels = db.labels_
    
    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    print(f"Found {n_clusters} clusters.")
    
    valid_clusters = []
    
    for i in range(n_clusters):
        cluster_indices = [idx for idx, label in enumerate(labels) if label == i]
        cluster_samples = [extreme_success[idx] for idx in cluster_indices]
        
        # Validation
        # X1: SP_A03_VAULT (Low variance in Vault_Count)
        # We simulate vault count: a sample is a vault if it has Chen/Xu/Chou/Wei
        vault_counts = []
        for s in cluster_samples:
            vc = 0
            for p in s['chart']:
                if p[1] in ['辰', '戌', '丑', '未']: vc += 1
            vault_counts.append(vc)
        
        vc_var = np.var(vault_counts)
        success_var = np.var([s['success_index'] for s in cluster_samples])
        
        print(f"Cluster {i}: Size={len(cluster_samples)}, VC_Var={vc_var:.4f}, Success_Var={success_var:.4f}")
        
        # Logic: 
        # X1: High VC, Low VC_Var -> VAULT
        if np.mean(vault_counts) >= 1.0 and vc_var < 0.5:
            print(f"✅ Cluster {i} Promoted to X1 (SP_A03_VAULT)")
            valid_clusters.append({
                "id": "SP_A03_VAULT",
                "samples": cluster_samples,
                "mu": np.mean(features[cluster_indices], axis=0).tolist()
            })
        elif success_var > 0.5:
            print(f"❌ Cluster {i} identified as X2 (High Variance Noise). DISCARDED.")
        else:
            print(f"ℹ️ Cluster {i} is stable but not a vaulted pattern. (General Singularity)")
            # Still keep for Matrix B? The instruction says "final only X1".
            
    # Save Step 3 Result
    discovery = {
        "x1": valid_clusters[0] if valid_clusters else None,
        "all_singularities": len(extreme_success)
    }
    
    with open("/home/jin/bazi_predict/data/a03_step3_discovery.json", "w") as f:
        json.dump(discovery, f, indent=2)
        
    print("Discovery saved to data/a03_step3_discovery.json")
    return discovery

if __name__ == "__main__":
    step3_discovery()
