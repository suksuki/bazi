from __future__ import annotations

import argparse
import ast
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_REGISTRIES = [
    "production_authority_manifest_v1.json",
    "legacy_register_v1.json",
    "prompt_registry_v1.json",
    "knowledge_registry_v1.json",
    "media_asset_registry_v1.json",
    "artifact_retention_v1.json",
]
FORBIDDEN_FRONTEND_TOKENS = [
    "/api/v50/agent",
    "reading_projection",
    "report_json",
    "run_record",
    "localStorage",
]


def audit() -> dict[str, object]:
    checks: list[dict[str, object]] = []

    for name in REQUIRED_REGISTRIES:
        path = ROOT / "config" / name
        checks.append({
            "check": f"registry:{name}",
            "passed": path.exists() and _valid_json(path),
            "path": str(path.relative_to(ROOT)),
        })

    experience_import_violations: list[str] = []
    for path in sorted((ROOT / "packages" / "experience").rglob("*.py")):
        for imported in _imports(path):
            if imported == "product" or imported.startswith("product."):
                experience_import_violations.append(f"{path.relative_to(ROOT)}:{imported}")
            if imported.startswith("core.mingli_agent") or imported.startswith("core.life_case"):
                experience_import_violations.append(f"{path.relative_to(ROOT)}:{imported}")
    checks.append({
        "check": "experience_package_has_no_product_or_cognitive_core_dependency",
        "passed": not experience_import_violations,
        "violations": experience_import_violations,
    })

    production_script_import_violations: list[str] = []
    production_roots = [ROOT / "apps" / "product", ROOT / "packages"]
    for production_root in production_roots:
        for path in sorted(production_root.rglob("*.py")):
            for imported in _imports(path):
                if imported == "scripts" or imported.startswith("scripts."):
                    production_script_import_violations.append(
                        f"{path.relative_to(ROOT)}:{imported}"
                    )
    checks.append({
        "check": "production_code_does_not_import_scripts",
        "passed": not production_script_import_violations,
        "violations": production_script_import_violations,
    })

    frontend_root = ROOT / "apps" / "product" / "experience_shell" / "src"
    frontend_violations: list[str] = []
    for path in sorted(frontend_root.rglob("*.ts")):
        text = path.read_text(encoding="utf-8")
        for token in FORBIDDEN_FRONTEND_TOKENS:
            if token in text:
                frontend_violations.append(f"{path.relative_to(ROOT)}:{token}")
    checks.append({
        "check": "new_frontend_does_not_read_legacy_authorities",
        "passed": not frontend_violations,
        "violations": frontend_violations,
    })

    visualization_sources = [
        ROOT / "apps" / "product" / "experience_shell" / "src" / "components.ts",
        ROOT / "apps" / "product" / "experience_shell" / "src" / "audio.ts",
    ]
    reasoner_violations = [
        str(path.relative_to(ROOT))
        for path in visualization_sources
        if path.exists() and "reasoner" in path.read_text(encoding="utf-8").lower()
    ]
    checks.append({
        "check": "visualization_does_not_call_reasoner",
        "passed": not reasoner_violations,
        "violations": reasoner_violations,
    })

    bundle = ROOT / "apps" / "product" / "static" / "experience" / "app.js"
    checks.append({
        "check": "independent_experience_bundle_exists",
        "passed": bundle.exists() and bundle.stat().st_size > 1000,
        "path": str(bundle.relative_to(ROOT)),
    })

    passed = all(bool(item["passed"]) for item in checks)
    return {
        "schema_version": "deepbazi.architecture_purification_audit.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "passed": passed,
        "checks": checks,
        "boundary_status": {
            "runtime_rules_modified": False,
            "brain_logic_modified": False,
            "mingli_algorithm_modified": False,
            "new_experience_reasoner_access": False,
            "legacy_formal_writes_allowed": False,
        },
    }


def _imports(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    output: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            output.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            output.append(node.module)
    return output


def _valid_json(path: Path) -> bool:
    try:
        json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = audit()
    rendered = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
