import json
import numpy as np
import os
from scipy.spatial.distance import mahalanobis

INPUT_FILE = "core/subjects/holographic_pattern/mining_cache/a01_tier_a_seeds_v151.json"
MATRIX_FILE = "core/subjects/holographic_pattern/matrix_cache/a01_matrix_v151.json"
OUTPUT_FILE = "scripts/a01_step4_audit_report_v151.json"

print("🕵️ [A-01 AUDIT V1.5.1] Auditing for Singularities (Judge vs Statue)...")

# 1. Load Data & Lens
with open(INPUT_FILE, 'r') as f:
    mining_data = json.load(f)
    seeds = mining_data['seeds'] # Top 6000+
    
with open(MATRIX_FILE, 'r') as f:
    matrix_data = json.load(f)
    manifold = matrix_data['feature_anchors']['standard_manifold']
    mean_vec = np.array(list(manifold['mean_vector'].values()))
    cov_inv = np.linalg.inv(np.array(manifold['covariance_matrix']))

audit_results = {
    "SP_A01_STANDARD": [], # The Judge
    "SP_A01_RIGID": []     # The Statue (Over-controlled)
}

# Stats for tuning
o_levels = []
m_levels = []

for seed in seeds:
    t = seed['tensor']
    vec = np.array([t['E'], t['O'], t['M'], t['S'], t['R']])
    
    # Track stats
    o_levels.append(t['O'])
    m_levels.append(t['M'])
    
    # 1. Mahalanobis Distance
    dist = mahalanobis(vec, mean_vec, cov_inv)
    
    # 2. Singularity Discovery Logic (Physics-based)
    
    # [Target B] SP_A01_RIGID (The Statue)
    # Definition: Extreme Order, Low Matter (No Flex), Zero Entropy, High Energy
    # Why Low M? Because "Bureaucracy" often stifles "Production" (M).
    # Why High E? Weak Self + High O = Puppet (Already filtered in Step 2).
    
    is_rigid = False
    if t['O'] > 0.70:       # Extreme Order
        if t['S'] < 0.15:   # Zero Entropy (Deadly Stable)
            if t['M'] < 0.40: # Low Resource/Flexibility (The key differentiator from a powerful CEO/Judge)
                 if t['E'] > 0.45: # Must be strong enough to withstand the rigidity
                     is_rigid = True
    
    if is_rigid:
        audit_results["SP_A01_RIGID"].append({
            "uid": seed['uid'],
            "dist": dist,
            "tensor": t
        })
    else:
        # [Target A] SP_A01_STANDARD (The Judge)
        # The balanced functional state.
        audit_results["SP_A01_STANDARD"].append({
            "uid": seed['uid'],
            "dist": dist,
            "tensor": t
        })

count_std = len(audit_results['SP_A01_STANDARD'])
count_rigid = len(audit_results['SP_A01_RIGID'])
total = count_std + count_rigid
pct_rigid = (count_rigid / total * 100) if total > 0 else 0

# Generate Sub-Pattern Specs
sub_patterns = [
    {
        "id": "SP_A01_STANDARD",
        "name": "The Judge (标准正官)",
        "type": "DEFAULT",
        "category": "POWER",
        "manifold_data": matrix_data['feature_anchors']['standard_manifold']
    },
    {
        "id": "SP_A01_RIGID",
        "name": "The Statue (石像/僵化)",
        "type": "SINGULARITY",
        "category": "POWER",
        "description": "Extreme Order, Low Flexibility. A perfect but lifeless crystal. (O>0.7, S<0.15, M<0.4)",
        "matrix_override": {
            "transfer_matrix": {
                "S_row": {
                    "Seven_Killings": 2.5  # Hyper-sensitive
                },
                "O_row": {
                    "Direct_Officer": 2.5  # Fixed weight
                }
            }
        },
        "manifold_data": {
             "mean_vector": matrix_data['feature_anchors']['standard_manifold']['mean_vector'] # Placeholder
        }
    }
]

output_payload = {
    "audit_stats": {
        "standard_count": count_std,
        "rigid_count": count_rigid,
        "rigid_percentage": f"{pct_rigid:.2f}%",
        "avg_O": float(np.mean(o_levels)),
        "avg_M": float(np.mean(m_levels))
    },
    "sub_patterns": sub_patterns
}

with open(OUTPUT_FILE, 'w') as f:
    json.dump(output_payload, f, indent=2, ensure_ascii=False)

print(f"✅ Audit Complete.")
print(f"📊 Audit Stats (Spectrum Analysis):")
print(f"   - Standard Judges: {count_std}")
print(f"   - Rigid Statues:   {count_rigid} ({pct_rigid:.2f}%)")
if count_rigid < 30:
    print(f"⚠️  WARNING: Rigid count ({count_rigid}) is below threshold (30). May not be viable.")
else:
    print(f"✅ VIABILITY: Rigid singularity is statistically significant.")
print(f"💾 Report Saved: {OUTPUT_FILE}")
