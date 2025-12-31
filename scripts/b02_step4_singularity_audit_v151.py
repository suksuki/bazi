import json
import numpy as np
import os
from scipy.spatial.distance import mahalanobis

INPUT_FILE = "core/subjects/holographic_pattern/mining_cache/b02_tier_a_seeds_v151.json"
MATRIX_FILE = "core/subjects/holographic_pattern/matrix_cache/b02_matrix_v151.json"
OUTPUT_FILE = "scripts/b02_step4_audit_report_v151.json"

print("🕵️ [B-02 AUDIT V1.5.1] Auditing for Coolant Mechanisms (Guru vs Tycoon)...")

# 1. Load Data & Lens
with open(INPUT_FILE, 'r') as f:
    mining_data = json.load(f)
    seeds = mining_data['seeds'] # Top ~10k Survivors
    
with open(MATRIX_FILE, 'r') as f:
    matrix_data = json.load(f)
    manifold = matrix_data['feature_anchors']['standard_manifold']
    mean_vec = np.array(list(manifold['mean_vector'].values()))
    cov_inv = np.linalg.inv(np.array(manifold['covariance_matrix']))

audit_results = {
    "SP_B02_STANDARD": [],  # The Strategist (Mixed)
    "SP_B02_AUTHORITY": [], # The Guru (Resource Cooled)
    "SP_B02_TYCOON": []     # The Tycoon (Wealth Cooled)
}

for seed in seeds:
    t = seed['tensor']
    vec = np.array([t['E'], t['O'], t['M'], t['S'], t['R']])
    dist = mahalanobis(vec, mean_vec, cov_inv)
    
    # 2. Singularity Discovery Logic (Cooling Mechanism)
    # Note: All these seeds are Tier A Survivors (E-Gated, High O/S, High Y)
    # We are classifying HOW they survived.
    
    # [Target A] SP_B02_AUTHORITY (The Guru / 伤官配印)
    # Mechanism: High Resource (E/R components) controls Output.
    # In tensor, Resource contributes to E (Energy).
    # Heuristic: High Energy (from Resource) + High Output. 
    # But strictly speaking, we check the raw components or the E-level relative to M.
    # Here we use Tensor E > 0.65 (Strong Support) and M < 0.45 (Not commercial)
    is_guru = False
    if t['E'] > 0.65 and t['M'] < 0.45:
        is_guru = True
        
    # [Target B] SP_B02_TYCOON (The Rainmaker / 伤官生财)
    # Mechanism: Output flows into Wealth.
    # Heuristic: High Material (M) > 0.60.
    is_tycoon = False
    if t['M'] > 0.60:
        is_tycoon = True
        
    # Classification Priority
    if is_guru:
        audit_results["SP_B02_AUTHORITY"].append({
            "uid": seed['uid'],
            "dist": dist,
            "tensor": t
        })
    elif is_tycoon:
         audit_results["SP_B02_TYCOON"].append({
            "uid": seed['uid'],
            "dist": dist,
            "tensor": t
        })
    else:
        # Balanced / Mixed Strategy
        audit_results["SP_B02_STANDARD"].append({
            "uid": seed['uid'],
            "dist": dist,
            "tensor": t
        })

# Stats
counts = {k: len(v) for k, v in audit_results.items()}
total = sum(counts.values())

# Generate Sub-Pattern Specs
sub_patterns = [
    {
        "id": "SP_B02_STANDARD",
        "name": "The Strategist (混合型伤官)",
        "type": "DEFAULT",
        "category": "TALENT",
        "manifold_data": matrix_data['feature_anchors']['standard_manifold'] # Base manifold
    },
    {
        "id": "SP_B02_AUTHORITY",
        "name": "The Guru (伤官配印)",
        "type": "SINGULARITY",
        "category": "TALENT",
        "description": "High Resource (E) suppressing Chaos. Academic/Authority figures. (E>0.65, M<0.45)",
        "matrix_override": {
            "transfer_matrix": {
                "S_row": { "Resource": -3.0 } # Enhanced Cooling from Resource
            }
        },
        "manifold_data": { "mean_vector": matrix_data['feature_anchors']['standard_manifold']['mean_vector'] } # Placeholder
    },
    {
        "id": "SP_B02_TYCOON",
        "name": "The Tycoon (伤官生财)",
        "type": "SINGULARITY",
        "category": "TALENT",
        "description": "High Wealth (M) channeling Chaos. Commercial Giants. (M>0.60)",
        "matrix_override": {
            "transfer_matrix": {
                "S_row": { "Direct_Wealth": -2.0 } # Enhanced Cooling from Wealth
            }
        },
        "manifold_data": { "mean_vector": matrix_data['feature_anchors']['standard_manifold']['mean_vector'] } # Placeholder
    }
]

output_payload = {
    "audit_stats": counts,
    "percentages": {k: f"{v/total*100:.2f}%" for k, v in counts.items()},
    "sub_patterns": sub_patterns
}

with open(OUTPUT_FILE, 'w') as f:
    json.dump(output_payload, f, indent=2, ensure_ascii=False)

print(f"✅ Audit Complete.")
print(f"📊 B-02 Cooling Spectrum:")
print(f"   - The Strategist (Mixed):   {counts['SP_B02_STANDARD']} ({counts['SP_B02_STANDARD']/total*100:.2f}%)")
print(f"   - The Guru (Authority):     {counts['SP_B02_AUTHORITY']} ({counts['SP_B02_AUTHORITY']/total*100:.2f}%)")
print(f"   - The Tycoon (Wealth):      {counts['SP_B02_TYCOON']} ({counts['SP_B02_TYCOON']/total*100:.2f}%)")
print(f"💾 Report Saved: {OUTPUT_FILE}")
