import json
import os

# Paths
REGISTRY_FILE = "core/subjects/holographic_pattern/registry.json"
FRAGMENT_FILE = "core/subjects/holographic_pattern/registry_fragment_a01.json"
AUDIT_REPORT = "scripts/a01_step4_audit_report.json"

print("📦 [A-01 ASSEMBLY] Finalizing Registry Entry...")

# 1. Load Components
with open(REGISTRY_FILE, 'r') as f:
    full_registry = json.load(f)

with open(FRAGMENT_FILE, 'r') as f:
    a01_core = json.load(f)

with open(AUDIT_REPORT, 'r') as f:
    audit_data = json.load(f)

# 2. Construct Sub-Patterns
sub_patterns = audit_data['sub_patterns']

# 3. Construct Matching Router (Shift Left Security)
# Priority: Singularity (Rigid) -> Standard
matching_router = {
    "strategy_version": "2.5 (Genesis)",
    "description": "Strict Priority: Rigid First, then Standard.",
    "strategies": [
        {
            "priority": 1,
            "target": "SP_A01_OVERCONTROL",
            "description": "Check for Rigid Structure (High Order, Low Entropy)",
            "logic": {
                "condition": "AND",
                "rules": [
                    { "axis": "O", "operator": "gt", "value": 0.70 },
                    { "axis": "S", "operator": "lt", "value": 0.15 },
                    { "axis": "E", "operator": "gt", "value": 0.45, "description": "Safety: Hardened Floor (Anti-Puppet)" } 
                ]
            }
        },
        {
            "priority": 2,
            "target": "SP_A01_STANDARD",
            "description": "Standard Direct Officer",
            "logic": {
                "condition": "HYBRID",
                "rules": [
                     { "axis": "E", "operator": "gt", "value": 0.45, "description": "E-Gating (Must be Strong)" }
                ],
                "distance_check": {
                    "type": "MAHALANOBIS",
                    "threshold": 3.0
                }
            }
        }
    ]
}

# 4. Integrate
a01_core['sub_patterns_registry'] = sub_patterns
a01_core['matching_router'] = matching_router

# 5. Write to Registry
full_registry['patterns']['A-01'] = a01_core

with open(REGISTRY_FILE, 'w', encoding='utf-8') as f:
    json.dump(full_registry, f, indent=2, ensure_ascii=False)

print(f"✅ A-01 Registered: {a01_core['meta_info']['name']}")
print(f"   - Sub-Patterns: {len(sub_patterns)}")
print(f"   - Routing Strategies: {len(matching_router['strategies'])}")
