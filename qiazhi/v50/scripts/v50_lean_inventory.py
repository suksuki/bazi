from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_ROOT = ROOT / "reports" / "v50-lean-consolidation" / "l0-l1"

IGNORED_PARTS = {
    ".git",
    ".pytest_cache",
    ".runtime",
    "__pycache__",
    "node_modules",
}
SOURCE_ROOTS = ("apps", "packages", "scripts", "tools")
METRIC_ROOTS = (
    "apps",
    "packages",
    "docs",
    "tests",
    "scripts",
    "tools",
    "config",
    "data",
    "reports",
    "artifacts",
)
TEXT_SUFFIXES = {
    ".css",
    ".html",
    ".js",
    ".json",
    ".md",
    ".mjs",
    ".py",
    ".sh",
    ".ts",
    ".tsx",
    ".txt",
    ".yaml",
    ".yml",
}
ASSET_SUFFIXES = {
    ".aac",
    ".gif",
    ".jpeg",
    ".jpg",
    ".m4a",
    ".mov",
    ".mp3",
    ".mp4",
    ".ogg",
    ".opus",
    ".png",
    ".svg",
    ".wav",
    ".webm",
    ".webp",
    ".zip",
}
HTTP_METHODS = {"get", "post", "put", "patch", "delete", "websocket"}
CURRENT_AUTHORITY_DOCS = {
    "docs/README.md",
    "docs/CURRENT_PRODUCT_BASELINE.md",
    "docs/CURRENT_ARCHITECTURE.md",
    "docs/CURRENT_IMPLEMENTATION_ROADMAP.md",
    "docs/DECISION_REGISTER.md",
}
PROTOTYPE_CLASSIFICATION = {
    "onecanvas-r1": ("PRESERVE", "active_product_candidate"),
    "xiangfa-generation-v1": ("ADAPT", "isolated_product_validation"),
    "s0-v12-shared": ("ADAPT", "shared_locked_scene_assets"),
    "mingli-onecanvas-c2ar": ("PRESERVE", "active_product_candidate"),
    "xiangfa-s0-v1": ("ADAPT", "isolated_product_validation"),
    "abu-motion-gallery-v1": ("ADAPT", "internal_tool"),
    "abu-says-mingli-s0-v12": ("ADAPT", "locked_internal_milestone"),
    "s0-v11-shared": ("ADAPT", "shared_locked_scene_assets"),
    "mingli-lab-c2a": ("RETIRE", "frozen_functional_fixture"),
    "mingli-scene-c1r": ("RETIRE", "frozen_semantic_proof"),
    "abu-says-mingli-s0": ("RETIRE", "superseded_theater_prototype"),
    "abu-says-mingli-s0-v11": ("RETIRE", "superseded_theater_prototype"),
    "xiangfa-s0-a": ("RETIRE", "superseded_xiangfa_prototype"),
    "s0-shared": ("RETIRE", "superseded_scene_assets"),
}
PROTOTYPE_ROOTS = (
    (ROOT / "apps/product/static/experience/prototypes", "legacy-runtime"),
    (ROOT / "apps/product/static/experience/active", "active"),
    (ROOT / "apps/product/static/experience/internal-tools", "internal-tool"),
    (ROOT / "apps/product/static/experience/shared", "shared"),
    (ROOT / "archive/proofs/prototypes", "archive-proof"),
)


def _relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def _iter_files(base: Path) -> Iterable[Path]:
    if not base.exists():
        return
    for path in base.rglob("*"):
        if not path.is_file() or any(part in IGNORED_PARTS for part in path.parts):
            continue
        yield path


def _tree_metrics(path: Path) -> dict[str, int]:
    files = list(_iter_files(path))
    return {
        "file_count": len(files),
        "size_bytes": sum(item.stat().st_size for item in files),
    }


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


def _python_routes(path: Path) -> list[dict[str, Any]]:
    try:
        tree = ast.parse(_read_text(path), filename=str(path))
    except SyntaxError:
        return []
    routes: list[dict[str, Any]] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for decorator in node.decorator_list:
            if not isinstance(decorator, ast.Call) or not isinstance(decorator.func, ast.Attribute):
                continue
            method = decorator.func.attr.lower()
            if method not in HTTP_METHODS or not decorator.args:
                continue
            argument = decorator.args[0]
            route_path = None
            if isinstance(argument, ast.Constant) and isinstance(argument.value, str):
                route_path = argument.value
            elif isinstance(argument, ast.JoinedStr):
                route_path = ast.unparse(argument)
            if route_path:
                routes.append(
                    {
                        "method": method.upper(),
                        "path": route_path,
                        "module": _relative(path),
                        "handler": node.name,
                        "line": node.lineno,
                    }
                )
    return routes


def _python_imports(path: Path) -> list[str]:
    try:
        tree = ast.parse(_read_text(path), filename=str(path))
    except SyntaxError:
        return []
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
    return sorted(set(imports))


def _script_imports(path: Path) -> list[str]:
    text = _read_text(path)
    imports = re.findall(
        r"(?:from\s+|import\s*\(|require\s*\()\s*['\"]([^'\"]+)['\"]",
        text,
    )
    return sorted(set(imports))


def _test_owners(token: str, test_texts: dict[str, str]) -> list[str]:
    variants = {token, Path(token).name, Path(token).stem}
    return sorted(
        path
        for path, text in test_texts.items()
        if any(variant and variant in text for variant in variants)
    )


def _document_status(path: Path) -> str:
    relative = _relative(path)
    if relative in CURRENT_AUTHORITY_DOCS:
        return "active"
    if "/archive/proofs/" in relative:
        return "historical-proof"
    if "/archive/" in relative:
        return "archive"
    if relative.endswith("V50_CURRENT_ARCHITECTURE.md"):
        return "superseded"
    if any(token in path.name for token in ("PROTOTYPE", "PROOF", "FIXTURE")):
        return "fixture-only"
    return "archive"


def _prototype_inventory(test_texts: dict[str, str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for root, surface in PROTOTYPE_ROOTS:
        if not root.exists():
            continue
        for path in sorted(item for item in root.iterdir() if item.is_dir()):
            classification, state = PROTOTYPE_CLASSIFICATION.get(
                path.name, ("RETIRE", "unclassified_prototype")
            )
            metrics = _tree_metrics(path)
            rows.append(
                {
                    "id": path.name,
                    "path": _relative(path),
                    "classification": classification,
                    "state": state,
                    "surface": surface,
                    "runtime_exposed": surface != "archive-proof",
                    **metrics,
                    "test_owners": _test_owners(path.name, test_texts),
                }
            )
    return rows


def _asset_inventory(reference_text: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    roots = (
        ROOT / "apps" / "product" / "static",
        ROOT / "artifacts",
        ROOT / "reports",
    )
    rows: list[dict[str, Any]] = []
    by_hash: dict[tuple[str, int], list[str]] = defaultdict(list)
    for root in roots:
        for path in _iter_files(root):
            if path.suffix.lower() not in ASSET_SUFFIXES:
                continue
            size = path.stat().st_size
            digest = _sha256(path)
            relative = _relative(path)
            referenced = path.name in reference_text or relative in reference_text
            rows.append(
                {
                    "path": relative,
                    "suffix": path.suffix.lower(),
                    "size_bytes": size,
                    "sha256": digest,
                    "reference_signal": referenced,
                    "candidate_unreferenced": not referenced,
                }
            )
            by_hash[(digest, size)].append(relative)

    duplicate_groups = []
    duplicate_bytes = 0
    for (digest, size), paths in sorted(by_hash.items(), key=lambda item: (-item[0][1], item[0][0])):
        if len(paths) < 2:
            continue
        reclaimable = size * (len(paths) - 1)
        duplicate_bytes += reclaimable
        duplicate_groups.append(
            {
                "sha256": digest,
                "size_bytes": size,
                "copies": len(paths),
                "reclaimable_bytes": reclaimable,
                "paths": sorted(paths),
            }
        )
    report = {
        "schema_version": "deepbazi.asset_dedup_report.v1",
        "asset_count": len(rows),
        "asset_bytes": sum(row["size_bytes"] for row in rows),
        "duplicate_group_count": len(duplicate_groups),
        "duplicate_bytes": duplicate_bytes,
        "candidate_unreferenced_count": sum(row["candidate_unreferenced"] for row in rows),
        "duplicate_groups": duplicate_groups,
    }
    return rows, report


def build_inventory(
    phase: str,
    *,
    regression_passed: int | None = None,
    regression_failed: int | None = None,
) -> dict[str, Any]:
    generated_at = datetime.now(timezone.utc).isoformat()
    tests = {
        _relative(path): _read_text(path)
        for path in _iter_files(ROOT / "tests")
        if path.suffix == ".py"
    }
    reference_files = []
    for root_name in ("apps", "packages", "tests", "docs", "scripts", "tools", "config"):
        for path in _iter_files(ROOT / root_name):
            if path.suffix.lower() in TEXT_SUFFIXES and path.stat().st_size <= 5 * 1024 * 1024:
                reference_files.append(_read_text(path))
    reference_text = "\n".join(reference_files)

    routes = []
    dependency_nodes = []
    dependency_edges = []
    incoming: dict[str, int] = defaultdict(int)
    for root_name in SOURCE_ROOTS:
        for path in _iter_files(ROOT / root_name):
            if path.suffix == ".py":
                routes.extend(_python_routes(path))
                imports = _python_imports(path)
                node_kind = "python"
            elif path.suffix.lower() in {".js", ".mjs", ".ts", ".tsx"}:
                imports = _script_imports(path)
                node_kind = "javascript"
            else:
                continue
            relative = _relative(path)
            dependency_nodes.append(
                {
                    "path": relative,
                    "kind": node_kind,
                    "size_bytes": path.stat().st_size,
                    "test_owners": _test_owners(relative, tests),
                }
            )
            for imported in imports:
                dependency_edges.append({"from": relative, "to": imported})
                incoming[imported] += 1

    prototypes = _prototype_inventory(tests)
    assets, asset_report = _asset_inventory(reference_text)
    docs = [
        {
            "path": _relative(path),
            "status": _document_status(path),
            "size_bytes": path.stat().st_size,
        }
        for path in sorted(_iter_files(ROOT / "docs"))
        if path.suffix.lower() == ".md"
    ]

    metrics = {
        "schema_version": "deepbazi.lean_metrics.v1",
        "phase": phase,
        "generated_at": generated_at,
        "roots": {
            name: _tree_metrics(ROOT / name)
            for name in METRIC_ROOTS
            if (ROOT / name).exists()
        },
        "repository": _tree_metrics(ROOT),
        "python_dependency_count": len(
            [edge for edge in dependency_edges if edge["from"].endswith(".py")]
        ),
        "frontend_dependency_count": len(
            [edge for edge in dependency_edges if not edge["from"].endswith(".py")]
        ),
        "http_route_count": len(routes),
        "active_product_routes": len(
            [
                row
                for row in prototypes
                if row["state"] == "active_product_candidate" and row["runtime_exposed"]
            ]
        ),
        "isolated_product_validation_routes": len(
            [
                row
                for row in prototypes
                if row["state"] == "isolated_product_validation" and row["runtime_exposed"]
            ]
        ),
        "prototype_count": len(prototypes),
        "runtime_exposed_prototype_count": len(
            [row for row in prototypes if row["runtime_exposed"]]
        ),
        "archived_prototype_count": len(
            [row for row in prototypes if not row["runtime_exposed"]]
        ),
        "active_prototype_count": len(
            [
                row
                for row in prototypes
                if row["state"]
                in {"active_product_candidate", "isolated_product_validation"}
            ]
        ),
        "default_document_count": len(CURRENT_AUTHORITY_DOCS),
        "document_count": len(docs),
        "duplicate_media_bytes": asset_report["duplicate_bytes"],
        "candidate_unreferenced_asset_count": asset_report["candidate_unreferenced_count"],
        "baseline_regression": (
            {
                "passed": regression_passed,
                "failed": regression_failed,
                "status": "pass" if regression_failed == 0 else "fail",
            }
            if regression_passed is not None and regression_failed is not None
            else None
        ),
    }

    return {
        "schema_version": "deepbazi.v50_lean_inventory.v1",
        "phase": phase,
        "generated_at": generated_at,
        "classification_vocabulary": ["PRESERVE", "EXTRACT", "ADAPT", "REBUILD", "RETIRE"],
        "metrics": metrics,
        "routes": sorted(routes, key=lambda row: (row["module"], row["line"])),
        "prototypes": prototypes,
        "dependencies": {
            "nodes": sorted(dependency_nodes, key=lambda row: row["path"]),
            "edges": sorted(dependency_edges, key=lambda row: (row["from"], row["to"])),
        },
        "assets": assets,
        "asset_dedup": asset_report,
        "documents": docs,
        "tests": {
            "count": len(tests),
            "files": sorted(tests),
        },
        "boundary": {
            "read_only_inventory": True,
            "mingli_behavior_modified": False,
            "formal_state_modified": False,
            "candidate_unreferenced_is_deletion_authority": False,
        },
    }


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_inventory(inventory: dict[str, Any], output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs = {
        "machine_inventory.json": inventory,
        "active_route_inventory.json": {
            "schema_version": "deepbazi.active_route_inventory.v1",
            "generated_at": inventory["generated_at"],
            "routes": inventory["routes"],
            "prototypes": inventory["prototypes"],
        },
        "asset_dedup_report.json": inventory["asset_dedup"],
        "dependency_graph.json": inventory["dependencies"],
        "document_status_inventory.json": {
            "schema_version": "deepbazi.document_status_inventory.v1",
            "documents": inventory["documents"],
        },
        "test_ownership_matrix.json": {
            "schema_version": "deepbazi.test_ownership_matrix.v1",
            "nodes": [
                {"path": row["path"], "test_owners": row["test_owners"]}
                for row in inventory["dependencies"]["nodes"]
            ],
            "prototypes": [
                {"path": row["path"], "test_owners": row["test_owners"]}
                for row in inventory["prototypes"]
            ],
        },
        f"{inventory['phase']}_metrics.json": inventory["metrics"],
    }
    paths: list[Path] = []
    for name, payload in outputs.items():
        path = output_dir / name
        _write_json(path, payload)
        paths.append(path)

    dot_path = output_dir / "dependency_graph.dot"
    dot_lines = ["digraph v50_dependencies {", "  rankdir=LR;"]
    for edge in inventory["dependencies"]["edges"]:
        source = edge["from"].replace('"', '\\"')
        target = edge["to"].replace('"', '\\"')
        dot_lines.append(f'  "{source}" -> "{target}";')
    dot_lines.append("}")
    dot_path.write_text("\n".join(dot_lines) + "\n", encoding="utf-8")
    paths.append(dot_path)

    summary_path = output_dir / "LEAN_EXECUTION_SUMMARY.md"
    metrics = inventory["metrics"]
    summary_path.write_text(
        "\n".join(
            [
                f"# V50 Lean Inventory — {inventory['phase'].title()}",
                "",
                f"- Generated: `{inventory['generated_at']}`",
                f"- Repository: `{metrics['repository']['size_bytes']}` bytes / `{metrics['repository']['file_count']}` files",
                f"- HTTP routes: `{metrics['http_route_count']}`",
                f"- Product routes: `{metrics['active_product_routes']}` active / `{metrics['isolated_product_validation_routes']}` isolated validation",
                f"- Prototypes: `{metrics['prototype_count']}` total / `{metrics['runtime_exposed_prototype_count']}` runtime exposed / `{metrics['archived_prototype_count']}` archived",
                f"- Documents: `{metrics['document_count']}` total / `{metrics['default_document_count']}` current-authority entries",
                f"- Exact duplicate media bytes: `{metrics['duplicate_media_bytes']}`",
                f"- Candidate unreferenced assets: `{metrics['candidate_unreferenced_asset_count']}`",
                "",
                "## Boundaries",
                "",
                "This inventory is read-only. Candidate-unreferenced status is not deletion authority.",
                "Only preserve/extract/adapt/rebuild/retire classifications are used.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    paths.append(summary_path)
    return paths


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate V50 Lean & Consolidation machine inventory.")
    parser.add_argument("--phase", choices=("before", "after"), required=True)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--regression-passed", type=int)
    parser.add_argument("--regression-failed", type=int)
    args = parser.parse_args()
    output_dir = args.output_dir or DEFAULT_OUTPUT_ROOT / args.phase
    inventory = build_inventory(
        args.phase,
        regression_passed=args.regression_passed,
        regression_failed=args.regression_failed,
    )
    paths = write_inventory(inventory, output_dir)
    print(
        json.dumps(
            {
                "phase": args.phase,
                "output_dir": str(output_dir),
                "files": [str(path) for path in paths],
                "metrics": inventory["metrics"],
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
