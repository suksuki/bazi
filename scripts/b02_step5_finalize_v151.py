import json
import os

# Paths (Absolute Paths for safety)
REGISTRY_FILE = "core/subjects/holographic_pattern/registry.json"
MATRIX_FILE = "core/subjects/holographic_pattern/matrix_cache/b02_matrix_v151.json"
AUDIT_REPORT = "scripts/b02_step4_audit_report_v151.json"

print("📦 [B-02 ASSEMBLY V1.5.1] Finalizing Multi-State Registry Entry...")

# 1. Load Components
if not os.path.exists(REGISTRY_FILE):
    raise FileNotFoundError("Registry file not found!")
if not os.path.exists(MATRIX_FILE):
    raise FileNotFoundError("Matrix cache not found (Run Step 3 first)")
if not os.path.exists(AUDIT_REPORT):
    raise FileNotFoundError("Audit report not found (Run Step 4 first)")

with open(REGISTRY_FILE, 'r') as f:
    full_registry = json.load(f)

with open(MATRIX_FILE, 'r') as f:
    matrix_data = json.load(f)

with open(AUDIT_REPORT, 'r') as f:
    audit_data = json.load(f)

# 2. Construct Sub-Patterns (Multi-State Strategy)
# Using manifold data from the matrix cache or audit placeholders
# For simplicity in this script, we map the IDs to basic manifold data
sub_pattern_defs = audit_data['sub_patterns']
sub_patterns = []

for sp_def in sub_pattern_defs:
    sp_entry = {
        "id": sp_def['id'],
        "name": sp_def['name'],
        "type": sp_def['type'],
        "category": "TALENT", # Strict Enum
        "manifold_data": matrix_data['feature_anchors']['standard_manifold'] # In real prod, would use cluster-specific manifolds
    }
    # Carry over matrix overrides if any
    if 'matrix_override' in sp_def:
        sp_entry['matrix_override'] = sp_def['matrix_override']
    sub_patterns.append(sp_entry)

# 3. Construct Matching Router (Safety Hardening & Bifurcation Logic)
matching_router = {
    "strategy_version": "2.5.1 (Genesis)",
    "description": "Multi-State Bifurcation (Guru/Tycoon/Strategist) w/ Hard Safety Gate.",
    "strategies": [
        # Strategy 1: The Guru (Authority) - High Resource
        {
            "priority": 1,
            "target": "SP_B02_AUTHORITY",
            "description": "Resource Cooled (Guru). High E/Resource.",
            "logic": {
                "condition": "HYBRID",
                "rules": [
                     # [SAFETY GATE]
                     { "axis": "E", "operator": "gt", "value": 0.45, "description": "Safety: Anti-Neurotic" },
                     # [BIFURCATION] High Resource (approximated by E in simplified tensor) or specific check
                     # Note: In compiled tensor, E includes Resource.
                     { "axis": "E", "operator": "gt", "value": 0.65, "description": "High Resource Support" }
                ],
                "distance_check": { "type": "MAHALANOBIS", "threshold": 3.0 }
            }
        },
        # Strategy 2: The Tycoon (Wealth) - High Wealth
        {
            "priority": 2,
            "target": "SP_B02_TYCOON",
            "description": "Wealth Cooled (Tycoon). High M.",
            "logic": {
                "condition": "HYBRID",
                "rules": [
                     # [SAFETY GATE]
                     { "axis": "E", "operator": "gt", "value": 0.45, "description": "Safety: Anti-Neurotic" },
                     # [BIFURCATION] High Wealth
                     { "axis": "M", "operator": "gt", "value": 0.60, "description": "High Commercial Value" }
                ],
                "distance_check": { "type": "MAHALANOBIS", "threshold": 3.0 }
            }
        },
        # Strategy 3: The Strategist (Standard) - Fallback
        {
            "priority": 3,
            "target": "SP_B02_STANDARD",
            "description": "Standard Hurting Officer (Strategist).",
            "logic": {
                "condition": "HYBRID",
                "rules": [
                     # [SAFETY GATE]
                     { "axis": "E", "operator": "gt", "value": 0.45, "description": "Safety: Anti-Neurotic" }
                ],
                "distance_check": { "type": "MAHALANOBIS", "threshold": 3.0 }
            }
        }
    ]
}

# 4. Integrate Core Data
b02_entry = {
    "id": "B-02",
    "name": "Hurting Officer Pattern",
    "version": "1.5.1",
    "active": True,
    "meta_info": {
        "pattern_id": "B-02",
        "name": "Hurting Officer (The Innovator)", 
        "display_name": "Hurting Officer",     # [COMPLIANCE] Pure English
        "chinese_name": "伤官格",             # [COMPLIANCE] Pure Chinese
        "category": "TALENT",                 # [COMPLIANCE] Pure Enum
        "physics_prototype": "Dissipative Structure / Bifurcation",
        "description": "高能量耗散结构。以伤官为动力，依冷却机制分化为学者(印)与巨贾(财)。严禁身弱入格。",
        "compliance": "FDS-V1.5.1 (Multi-State)",
        "calibration_date": "2025-12-31"
    },
    "physics_kernel": matrix_data['physics_kernel'],
    "sub_patterns_registry": sub_patterns,
    "matching_router": matching_router
}

# 5. Write to Registry
full_registry['patterns']['B-02'] = b02_entry

with open(REGISTRY_FILE, 'w', encoding='utf-8') as f:
    json.dump(full_registry, f, indent=2, ensure_ascii=False)

print(f"✅ B-02 Finalized: {b02_entry['meta_info']['display_name']}")
print(f"   - Category: {b02_entry['meta_info']['category']}")
print(f"   - Sub-Patterns: {len(sub_patterns)} (Guru, Tycoon, Strategist)")
print(f"   - Safety Gate: E > 0.45 (Injected Globally)")
print(f"💾 Registry Updated: {REGISTRY_FILE}")
