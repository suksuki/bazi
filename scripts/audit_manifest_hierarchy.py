import json
import os
import sys

# Color codes for terminal
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"

def audit_hierarchy():
    manifest_path = 'core/logic_manifest.json'
    print(f"--- 🏛️ Grand Unified Architecture Audit (V12.1.0) ---")
    
    if not os.path.exists(manifest_path):
        print(f"{RED}[ERROR]{RESET} Manifest not found at {manifest_path}")
        return

    with open(manifest_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    themes = data.get('themes', {})
    modules = data.get('modules', {})
    registry = data.get('registry', {})
    
    errors = 0
    warnings = 0

    # 1. Theme Integrity
    print(f"\n[1] Theme Registry Audit:")
    if not themes:
        print(f"  {RED}✖ No themes defined!{RESET}")
        errors += 1
    else:
        for t_id, t_data in themes.items():
            print(f"  {GREEN}✔{RESET} Theme: {t_id} ({t_data.get('name')})")

    # 2. Module Theme Mapping
    print(f"\n[2] Module-Theme Mapping Audit:")
    for m_id, m_data in modules.items():
        theme_id = m_data.get('theme')
        if not theme_id:
            print(f"  {RED}✖ Module {m_id} is ORPHANED (no theme field).{RESET}")
            errors += 1
        elif theme_id not in themes:
            print(f"  {RED}✖ Module {m_id} maps to UNKNOWN theme: {theme_id}{RESET}")
            errors += 1
        else:
            status = "Active" if m_data.get('active', True) else "Inactive"
            print(f"  {GREEN}✔{RESET} Module {m_id} -> {theme_id} ({status})")

    # 3. Registry Linkage Audit
    print(f"\n[3] Registry Linkage Audit (Orphan Detection):")
    linked_rules = set()
    for m_data in modules.values():
        linked_rules.update(m_data.get('linked_rules', []))

    for r_id in registry:
        if r_id not in linked_rules:
            # We recently added MOD_18_BASE_APP to fix this, so any remaining should be flagged
            print(f"  {YELLOW}⚠ Warning:{RESET} Rule {r_id} is not linked to any Module.")
            warnings += 1
        else:
            pass # Linked

    # 4. Consistency: Topic Hierarchy
    print(f"\n[4] Topic Consistency Audit:")
    for r_id, r_data in registry.items():
        origin = r_data.get('origin_trace', [])
        # We don't strictly enforce origin matching module ID yet, but it's good practice
        pass

    print(f"\n--- Audit Summary ---")
    if errors == 0:
        print(f"  {GREEN}Structure Status: SOLID{RESET}")
    else:
        print(f"  {RED}Structure Status: COMPROMISED ({errors} errors){RESET}")
    
    print(f"  Errors: {errors}, Warnings: {warnings}")
    
    if errors > 0:
        sys.exit(1)

if __name__ == "__main__":
    audit_hierarchy()
