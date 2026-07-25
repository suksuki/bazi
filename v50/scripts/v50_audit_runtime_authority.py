from __future__ import annotations

import argparse
import ast
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "config/production_authority_manifest_v1.json"


def audit_runtime_authority() -> dict[str, Any]:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    runtime = manifest["runtime_boundaries"]
    allowed_statuses = set(manifest["allowed_statuses"])
    invalid_statuses = [
        {"authority": name, "status": item.get("status")}
        for name, item in manifest["authorities"].items()
        if item.get("status") not in allowed_statuses
    ]
    production_files = [
        *sorted((ROOT / "apps/product").glob("*.py")),
        *sorted((ROOT / "packages/core/mingli_agent").glob("*.py")),
    ]
    imports = {
        path.relative_to(ROOT).as_posix(): sorted(_imports(path))
        for path in production_files
    }
    forbidden = []
    for source, names in imports.items():
        for name in names:
            if any(name == prefix or name.startswith(f"{prefix}.") for prefix in runtime["research_only"]):
                forbidden.append({"source": source, "import": name})

    reasoner = (ROOT / "packages/core/mingli_agent/reasoner.py").read_text(encoding="utf-8")
    context = (ROOT / "packages/core/mingli_agent/context.py").read_text(encoding="utf-8")
    leakage_tokens = [
        token
        for token in (
            "expert_structure_prior",
            "expected_path 含 output_controls_pressure",
            "乙木生丁火",
            "巳酉丑三合只说明",
        )
        if token in reasoner or token in context
    ]
    projection_source = (ROOT / "apps/product/reading_projection.py").read_text(encoding="utf-8")
    public_base = _assigned_string_set(projection_source, "_PUBLIC_BASE_FIELDS")
    forbidden_projection_fields = sorted(
        set(manifest["guest_member_forbidden_fields"]) & public_base
    )
    graph_authority_violations = _graph_relation_authority_violations(
        ROOT / "packages/core/mingli_agent/world.py"
    )
    result = {
        "version": "deepbazi.runtime_authority_audit.v1.2",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": (
            "passed"
            if not forbidden
            and not leakage_tokens
            and not invalid_statuses
            and not forbidden_projection_fields
            and not graph_authority_violations
            else "failed"
        ),
        "observed_data": {
            "production_file_count": len(production_files),
            "forbidden_research_imports": forbidden,
            "synthetic_answer_leakage_tokens": leakage_tokens,
            "production_authoritative": runtime["production_authoritative"],
            "experimental_advisory_tools": runtime["experimental_advisory_tools"],
            "research_projection_authority": runtime["research_projection_authority"],
            "research_only": runtime["research_only"],
            "retired_capabilities": runtime["retired_capabilities"],
            "production_authority_manifest": manifest,
            "invalid_authority_statuses": invalid_statuses,
            "guest_member_public_base_fields": sorted(public_base),
            "guest_member_forbidden_projection_fields": forbidden_projection_fields,
            "graph_relation_authority_violations": graph_authority_violations,
        },
        "interpretation": (
            "Production uses deterministic modules as fact authorities; Graph/Path/Role/Ablation "
            "remain experimental advisory observations, and the validated LLM policy is the only "
            "whole-chart cognitive reasoner."
        ),
        "boundary_status": {
            "runtime_rules_modified": False,
            "mingli_algorithm_modified": False,
            "research_modules_promoted": False,
            "retired_brain_restored": False,
        },
    }
    return result


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    output: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            output.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            output.add(node.module)
    return output


def _assigned_string_set(source: str, name: str) -> set[str]:
    tree = ast.parse(source)
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(target, ast.Name) and target.id == name for target in node.targets):
            continue
        if isinstance(node.value, ast.Set):
            return {
                item.value
                for item in node.value.elts
                if isinstance(item, ast.Constant) and isinstance(item.value, str)
            }
    return set()


def _graph_relation_authority_violations(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    function = next(
        (
            node
            for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name == "_graph_relation_facts"
        ),
        None,
    )
    if function is None:
        return ["graph_relation_factory_missing"]
    authorities: list[str] = []
    for node in ast.walk(function):
        if not isinstance(node, ast.Call):
            continue
        name = node.func.id if isinstance(node.func, ast.Name) else ""
        if name != "WorldFact":
            continue
        values = {
            keyword.arg: keyword.value.value
            for keyword in node.keywords
            if keyword.arg
            and isinstance(keyword.value, ast.Constant)
            and isinstance(keyword.value.value, str)
        }
        if values.get("category") == "graph_relation":
            authorities.append(values.get("authority", ""))
    if not authorities:
        return ["graph_relation_authority_missing"]
    return [
        f"graph_relation_authority:{authority or 'default'}"
        for authority in authorities
        if authority != "experimental_tool_observation"
    ]


def _write(report: dict[str, Any], output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "runtime_authority_audit_v1.json"
    md_path = output_dir / "runtime_authority_audit_v1.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    observed = report["observed_data"]
    md_path.write_text(
        "\n".join(
            [
                "# Runtime Authority Audit v1",
                "",
                f"- Status: `{report['status']}`",
                f"- Production files scanned: `{observed['production_file_count']}`",
                f"- Forbidden research imports: `{len(observed['forbidden_research_imports'])}`",
                f"- Synthetic answer leakage tokens: `{observed['synthetic_answer_leakage_tokens']}`",
                "",
                "## Authority",
                "",
                "```json",
                json.dumps(observed["production_authoritative"], ensure_ascii=False, indent=2),
                "```",
                "",
                "## Research-only",
                "",
                "```json",
                json.dumps(observed["research_only"], ensure_ascii=False, indent=2),
                "```",
                "",
                "## Experimental Advisory Tools",
                "",
                "```json",
                json.dumps(observed["experimental_advisory_tools"], ensure_ascii=False, indent=2),
                "```",
                "",
                "## Research Projection Authority",
                "",
                "```json",
                json.dumps(observed["research_projection_authority"], ensure_ascii=False, indent=2),
                "```",
                "",
                "## Boundaries",
                "",
                "```json",
                json.dumps(report["boundary_status"], ensure_ascii=False, indent=2),
                "```",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return json_path, md_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit production runtime authority boundaries.")
    parser.add_argument("--output-dir", default=str(ROOT / "reports/runtime-authority/v1"))
    args = parser.parse_args()
    report = audit_runtime_authority()
    paths = _write(report, Path(args.output_dir))
    print(json.dumps({"status": report["status"], "reports": [str(path) for path in paths]}, ensure_ascii=False))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
