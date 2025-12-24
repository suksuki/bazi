
import json
import os

def audit_architecture():
    print("🏗️ Running Antigravity V11.1 Meta-Architecture Audit...")
    
    manifest_path = "core/logic_manifest.json"
    if not os.path.exists(manifest_path):
        print("❌ Error: logic_manifest.json not found")
        return

    with open(manifest_path, 'r', encoding='utf-8') as f:
        manifest = json.load(f)

    registry = manifest.get("registry", {})
    modules = manifest.get("modules", {})
    all_logic = {**registry, **modules}

    errors = 0
    warnings = 0

    valid_layers = ["ENVIRONMENT", "FUNDAMENTAL", "STRUCTURAL", "FLOW", "TEMPORAL"]

    for key, data in all_logic.items():
        # Check Layer
        layer = data.get("layer")
        if not layer:
            print(f"❌ ERROR: {key} is missing 'layer'")
            errors += 1
        elif layer not in valid_layers:
            print(f"⚠️ WARNING: {key} has unknown layer '{layer}'")
            warnings += 1

        # Check Priority
        priority = data.get("priority")
        if priority is None:
            print(f"❌ ERROR: {key} is missing 'priority'")
            errors += 1
        elif not isinstance(priority, int):
            print(f"❌ ERROR: {key} priority is not an integer")
            errors += 1

    print("\n" + "="*40)
    print(f"📊 Audit Results: {errors} Errors, {warnings} Warnings")
    if errors == 0:
        print("✅ Architecture Audit PASSED (V11.1 Compliance confirmed)")
    else:
        print("❌ Architecture Audit FAILED")
        exit(1)

if __name__ == "__main__":
    audit_architecture()
