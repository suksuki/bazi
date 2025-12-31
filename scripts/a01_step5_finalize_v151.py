import json
import os

# Paths (Absolute Paths for safety)
REGISTRY_FILE = "core/subjects/holographic_pattern/registry.json"
MATRIX_FILE = "core/subjects/holographic_pattern/matrix_cache/a01_matrix_v151.json"
AUDIT_REPORT = "scripts/a01_step4_audit_report_v151.json"

print("📦 [A-01 ASSEMBLY V1.5.1] Finalizing Registry Entry...")

# 1. Load Components
if not os.path.exists(REGISTRY_FILE):
    raise FileNotFoundError("Registry file not found!")
if not os.path.exists(MATRIX_FILE):
    raise FileNotFoundError("Matrix cache not found (Run Step 3 first)")
    
with open(REGISTRY_FILE, 'r') as f:
    full_registry = json.load(f)

with open(MATRIX_FILE, 'r') as f:
    matrix_data = json.load(f)

# 2. Construct Sub-Patterns (Single State Strategy)
# Step 4 Decision: Strict Drop of "Rigid". Only Standard remains.
sub_patterns = [
    {
        "id": "SP_A01_STANDARD",
        "name": "The Judge (标准正官)",
        "type": "DEFAULT",
        "category": "POWER", # Metadata Compliance (Enum)
        "manifold_data": matrix_data['feature_anchors']['standard_manifold']
    }
]

# 3. Construct Matching Router (Safety Hardening Injection)
matching_router = {
    "strategy_version": "2.5.1 (Genesis)",
    "description": "Single-State Monolithic Crystal. Strict E-Gating.",
    "strategies": [
        {
            "priority": 1,
            "target": "SP_A01_STANDARD",
            "description": "Standard Direct Officer (The Judge)",
            "logic": {
                "condition": "HYBRID",
                "rules": [
                     # [SAFETY GATE] FDS-V1.5.1 Compliance
                     # "Weak Self cannot hold Power"
                     { 
                         "axis": "E", 
                         "operator": "gt", 
                         "value": 0.45, 
                         "description": "Safety: Hardened Floor (Anti-Puppet)" 
                     }
                ],
                "distance_check": {
                    "type": "MAHALANOBIS",
                    "threshold": 3.0
                }
            }
        }
    ]
}

# 4. Integrate Core Data
# Ensure top-level metadata matches FDS-V1.5.1
a01_entry = {
    "id": "A-01",
    "name": "Direct Officer Pattern",
    "version": "1.5.1",
    "active": True,
    "meta_info": {
        "pattern_id": "A-01",
        "name": "Direct Officer (The Judge)", # Full English Name
        "display_name": "Direct Officer",     # [COMPLIANCE] Pure English Index
        "chinese_name": "正官格",             # [COMPLIANCE] Pure Chinese Title
        "category": "POWER",                  # [COMPLIANCE] Pure Enum
        "physics_prototype": "Monolithic Crystalline Lattice",
        "description": "高度秩序化的单态晶体结构。以正官为核心，排斥伤官杂质。必须身旺方可入格。",
        "compliance": "FDS-V1.5.1 (Single-State)",
        "calibration_date": "2025-12-31"
    },
    "physics_kernel": matrix_data['physics_kernel'], # Start from Fitted Kernel
    "sub_patterns_registry": sub_patterns,
    "matching_router": matching_router
}

# 5. Write to Registry
full_registry['patterns']['A-01'] = a01_entry

with open(REGISTRY_FILE, 'w', encoding='utf-8') as f:
    json.dump(full_registry, f, indent=2, ensure_ascii=False)

print(f"✅ A-01 Finalized: {a01_entry['meta_info']['display_name']}")
print(f"   - Category: {a01_entry['meta_info']['category']}")
print(f"   - Sub-Patterns: {len(sub_patterns)} (Single-State)")
print(f"   - Safety Gate: E > 0.45 (Injected)")
print(f"💾 Registry Updated: {REGISTRY_FILE}")
