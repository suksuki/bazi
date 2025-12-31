import json
import numpy as np
import os
from scipy.spatial.distance import mahalanobis

INPUT_FILE = "core/subjects/holographic_pattern/mining_cache/a01_tier_a_seeds_v151.json"
MATRIX_FILE = "core/subjects/holographic_pattern/matrix_cache/a01_matrix_v151.json"
OUTPUT_FILE = "scripts/a01_step4_audit_report_v151.json"

print("🕵️ [A-01 AUDIT V1.5.1] Auditing for Singularities (The Rigid)...")

# 1. Load Data & Lens
with open(INPUT_FILE, 'r') as f:
    seeds = json.load(f)['seeds'] # Top 6000+
    
with open(MATRIX_FILE, 'r') as f:
    matrix_data = json.load(f)
    manifold = matrix_data['feature_anchors']['standard_manifold']
    mean_vec = np.array(list(manifold['mean_vector'].values()))
    cov_inv = np.linalg.inv(np.array(manifold['covariance_matrix']))

audit_results = {
    "SP_A01_STANDARD": [],
    "SP_A01_OVERCONTROL": []
}

for seed in seeds:
    t = seed['tensor']
    vec = np.array([t['E'], t['O'], t['M'], t['S'], t['R']])
    
    # 1. Mahalanobis Distance (Deviation from Standard)
    dist = mahalanobis(vec, mean_vec, cov_inv)
    
    # 2. Heuristic Rules (Singularity Discovery)
    
    # [Singularity X1] "The Rigid" (Over-controlled)
    # Extremely High Order, Near-Zero Entropy
    # 物理意义：过刚易折。
    if t['O'] > 0.70 and t['S'] < 0.15:
        audit_results["SP_A01_OVERCONTROL"].append({
            "uid": seed['uid'],
            "dist": dist,
            "tensor": t
        })
    else:
        # Standard Judge (The Bureaucrat)
        # 即使是普通正官，也必须经过 E-Gating (已在 Step 2 完成)
        audit_results["SP_A01_STANDARD"].append({
            "uid": seed['uid'],
            "dist": dist,
            "tensor": t
        })

count_std = len(audit_results['SP_A01_STANDARD'])
count_sing = len(audit_results['SP_A01_OVERCONTROL'])
total = count_std + count_sing
pct_sing = (count_sing / total * 100) if total > 0 else 0

# Generate Sub-Pattern Specs
sub_patterns = [
    {
        "id": "SP_A01_STANDARD",
        "name": "The Bureaucrat (标准正官)",
        "type": "DEFAULT",
        "category": "POWER", # Metadata standardization
        "manifold_data": matrix_data['feature_anchors']['standard_manifold']
    },
    {
        "id": "SP_A01_OVERCONTROL",
        "name": "The Rigid (清官/僵化)",
        "type": "SINGULARITY",
        "category": "POWER",
        "description": "Excessive Order leading to brittleness. Resistant to change. (O>0.7, S<0.15)",
        "matrix_override": {
            "transfer_matrix": {
                "S_row": {
                    "Seven_Killings": 2.5  # Hyper-sensitive to impurity
                },
                "O_row": {
                    "Direct_Officer": 2.5 # Super-saturated Authority
                }
            }
        },
        "manifold_data": {
            # Placeholder: In a real system, we would fit a separate manifold for this cluster
             "mean_vector": matrix_data['feature_anchors']['standard_manifold']['mean_vector'] 
        }
    }
]

output_payload = {
    "audit_stats": {
        "standard_count": count_std,
        "singularity_count": count_sing,
        "singularity_percentage": f"{pct_sing:.2f}%"
    },
    "sub_patterns": sub_patterns
}

with open(OUTPUT_FILE, 'w') as f:
    json.dump(output_payload, f, indent=2, ensure_ascii=False)

print(f"✅ Audit Complete.")
print(f"📊 Audit Stats:")
print(f"   - Standard Bureaucrats: {count_std}")
print(f"   - Rigid/Over-controllers: {count_sing} ({pct_sing:.2f}%)")
print(f"💾 Report Saved: {OUTPUT_FILE}")
