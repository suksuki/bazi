from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

if __package__:
    from scripts.v50_audit_architecture_purification import audit as audit_architecture
    from scripts.v50_audit_runtime_authority import audit_runtime_authority
    from scripts.v50_export_experience_schemas import TYPESCRIPT_OUTPUT, render_typescript_contracts
else:
    from v50_audit_architecture_purification import audit as audit_architecture
    from v50_audit_runtime_authority import audit_runtime_authority
    from v50_export_experience_schemas import TYPESCRIPT_OUTPUT, render_typescript_contracts


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "config/production_authority_manifest_v1.json"
CAL01_REPORT = (
    ROOT
    / "reports/v50-lean-consolidation/cal01-late-zi-v1"
    / "cal01_late_zi_audit_v1.json"
)
RA0_SUMMARY = (
    ROOT
    / "reports/v50-lean-consolidation/ra0-518k-realizability-v1"
    / "ra0_518k_execution_summary_v1.json"
)
R1_MANIFEST = (
    ROOT
    / "reports/mingli-onecanvas-r1/review-v6-ready/r1_v6_review_build.sha256"
)
SPLIT_AUTHORITY_REGISTRIES = (
    "canonical_scene_authority_v1.json",
    "data_authority_v1.json",
    "frontend_state_authority_v1.json",
    "runtime_authority_v1.json",
)


def run_architecture_gate() -> dict[str, Any]:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    runtime_audit = audit_runtime_authority()
    architecture_audit = audit_architecture()
    cal01 = json.loads(CAL01_REPORT.read_text(encoding="utf-8"))
    ra0 = json.loads(RA0_SUMMARY.read_text(encoding="utf-8"))["semantic_summary"]
    checks: list[dict[str, Any]] = []

    _record(checks, "one_formal_case_owner", manifest["module_ownership"]["formal_relation_path"] == "core.life_case.LifeCase")
    _record(checks, "one_canonical_scene_owner", _class_count("CanonicalSceneOwner") == 1 and manifest["module_ownership"]["canonical_scene"] == "product.canonical_scene.CanonicalSceneOwner")
    _record(checks, "one_authority_registry", all(not (ROOT / "config" / name).exists() for name in SPLIT_AUTHORITY_REGISTRIES))
    _record(checks, "one_database_ddl_owner", _ddl_owners() == ["deploy/postgres_v50_schema.sql"])
    _record(checks, "one_baseline_command_owner", manifest["module_ownership"]["baseline_command"] == "product.agent_command_service.BaselineCaseCommandService" and _baseline_delegate_count() == 2)
    _record(checks, "one_schema_source", manifest["schema_ownership"]["authoritative_source"] == "Python Pydantic models" and TYPESCRIPT_OUTPUT.read_text(encoding="utf-8") == render_typescript_contracts())
    _record(checks, "stable_relation_path_identity", _provenance_contracts_present())
    _record(checks, "projection_never_owns_facts", manifest["projection_rules"]["projection_owns_facts"] is False)
    _record(checks, "client_cannot_write_formal_facts", all(manifest["projection_rules"][key] is False for key in ("client_may_submit_formal_chart_facts", "client_may_submit_formal_relation_or_path")))
    _record(checks, "role_filter_cannot_fallback", manifest["projection_rules"]["role_hidden_content_may_reappear_by_fallback"] is False)
    _record(checks, "runtime_authority_audit", runtime_audit["status"] == "passed")
    _record(checks, "architecture_purification_audit", bool(architecture_audit["passed"]))
    _record(checks, "cal01_closed", cal01["status"] == "PASS" and cal01["counts"]["formal_invalid_outputs"] == 0)
    _record(checks, "ra0_universe_retained", ra0["reconstructed_universe"]["content_sha256"] == "05c97a1518ff840ef3d4955f92dd0a22de9c4729ef7ff2ec8601efbcb14a454c")
    r1_ok, r1_count = _verify_r1_manifest()
    _record(checks, "r1_regression_reference", r1_ok and r1_count == 20)
    _record(checks, "no_new_transitional_layer", manifest["classification"]["new_transitional_layers_allowed"] is False)
    _record(checks, "repeatable_validation_assets", all((ROOT / path).exists() for path in ("scripts/v50_run_ra0_518k_realizability_audit.py", "scripts/v50_audit_cal01_late_zi.py", "tests/test_v50_relation_path_provenance_cag04.py", "tests/test_v50_schema_module_ownership_cag05.py")))

    source_hashes = {
        path: _sha256(ROOT / path)
        for path in (
            "config/production_authority_manifest_v1.json",
            "deploy/postgres_v50_schema.sql",
            "packages/core/life_case/contracts.py",
            "packages/core/graph/provenance.py",
            "apps/product/canonical_scene.py",
            "packages/core/engines/birth_calendar.py",
        )
    }
    return {
        "schema_version": "v50.architecture_consolidation_gate.v1",
        "status": "PASS" if all(item["passed"] for item in checks) else "FAIL",
        "checks": checks,
        "source_hashes": source_hashes,
        "authority_chain": [
            "ChartWorldInstance",
            "Reasoner candidate cognition",
            "LifeCase committed cognition",
            "CanonicalSceneOwner",
            "role-filtered Projection",
        ],
        "r1_locked_assets": r1_count,
        "cal01_scan_sha256": cal01["scan_sha256"],
        "universe_sha256": ra0["reconstructed_universe"]["content_sha256"],
        "llm_used": False,
        "production_migration_performed": False,
    }


def _record(checks: list[dict[str, Any]], name: str, passed: bool) -> None:
    checks.append({"check": name, "passed": bool(passed)})


def _class_count(name: str) -> int:
    token = f"class {name}"
    return sum(
        path.read_text(encoding="utf-8").count(token)
        for path in (ROOT / "apps/product").glob("*.py")
    )


def _ddl_owners() -> list[str]:
    owners: list[str] = []
    candidates = [
        *sorted((ROOT / "apps/product").glob("*.py")),
        ROOT / "deploy/postgres_v50_schema.sql",
    ]
    for path in candidates:
        source = path.read_text(encoding="utf-8")
        if "CREATE TABLE" in source or "ALTER TABLE" in source:
            owners.append(path.relative_to(ROOT).as_posix())
    return owners


def _baseline_delegate_count() -> int:
    source = (ROOT / "apps/product/agent_api.py").read_text(encoding="utf-8")
    return source.count("baseline_commands.execute(")


def _provenance_contracts_present() -> bool:
    source = (ROOT / "packages/core/graph/provenance.py").read_text(encoding="utf-8")
    return all(
        f"class {name}" in source
        for name in (
            "NodeRef",
            "RelationKey",
            "PathKey",
            "ProvenanceRecord",
            "RelationAssertion",
            "PathAssertion",
        )
    )


def _verify_r1_manifest() -> tuple[bool, int]:
    rows = [line.split(maxsplit=1) for line in R1_MANIFEST.read_text(encoding="utf-8").splitlines() if line.strip()]
    return all(_sha256(ROOT / relative) == expected for expected, relative in rows), len(rows)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the V50 Architecture Consolidation Gate")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run_architecture_gate()
    rendered = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
