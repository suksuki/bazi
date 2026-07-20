from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "reports" / "vnext-phase0-g1" / "snapshot-candidate-v1"
INCLUDED_PREFIXES = (
    "config/vnext_phase0_",
    "data/validation/phase0/",
    "packages/core/mingli_agent/",
    "scripts/v50_prepare_vnext_phase0_",
    "scripts/v50_run_vnext_phase0_",
    "tests/test_v50_vnext_phase0_",
    "docs/VNEXT_PHASE0_",
)
INCLUDED_EXACT = {
    "config/vnext_phase0_dependencies_v1.txt",
}


def prepare_snapshot(*, output_dir: Path, freeze: bool) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    files = _snapshot_files()
    manifest_rows = [
        {
            "path": str(path.relative_to(ROOT)),
            "sha256": sha256(path.read_bytes()).hexdigest(),
            "bytes": path.stat().st_size,
        }
        for path in files
    ]
    git = _git_state()
    source_hash = sha256(
        json.dumps(manifest_rows, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    blockers = []
    if not git["v50_snapshot_tracked"]:
        blockers.append("v50_code_snapshot_not_committed")
    if git["dirty_tree"]:
        blockers.append("v50_snapshot_scope_not_clean")
    status = "frozen" if freeze and not blockers else "candidate_blocked" if blockers else "candidate_ready_to_freeze"
    if freeze and blockers:
        raise ValueError(f"snapshot_freeze_rejected:{','.join(blockers)}")
    report = {
        "version": "deepbazi.vnext_phase0.execution_snapshot.v1",
        "status": status,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "git_commit": git["commit"],
        "git_state": git,
        "scope": {
            "purpose": "phase0_cognitive_benchmark_execution",
            "file_count": len(manifest_rows),
            "total_bytes": sum(row["bytes"] for row in manifest_rows),
            "included_prefixes": list(INCLUDED_PREFIXES),
            "production_ui_or_media_included": False,
        },
        "source_manifest_sha256": source_hash,
        "files": manifest_rows,
        "blockers": blockers,
        "boundaries": {
            "formal_execution_allowed": status == "frozen",
            "working_tree_snapshot_accepted_as_committed": False,
            "automatic_git_commit_performed": False,
            "unrelated_worktree_changes_modified": False,
        },
    }
    path = output_dir / ("FROZEN_EXECUTION_SNAPSHOT.json" if status == "frozen" else "EXECUTION_SNAPSHOT_CANDIDATE.json")
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output_dir / "EXECUTION_SNAPSHOT_README.md").write_text(_markdown(report), encoding="utf-8")
    return report


def _snapshot_files() -> list[Path]:
    files = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or "__pycache__" in path.parts or ".pytest_cache" in path.parts:
            continue
        relative = str(path.relative_to(ROOT))
        if relative in INCLUDED_EXACT or any(relative.startswith(prefix) for prefix in INCLUDED_PREFIXES):
            files.append(path)
    return sorted(files)


def _git_state() -> dict[str, Any]:
    try:
        top = Path(subprocess.check_output(["git", "rev-parse", "--show-toplevel"], cwd=ROOT, text=True).strip())
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
        relative = ROOT.resolve().relative_to(top.resolve())
        status = subprocess.check_output(
            ["git", "status", "--porcelain", "--", str(relative)], cwd=top, text=True
        ).splitlines()
    except (OSError, subprocess.CalledProcessError, ValueError):
        return {
            "commit": "unavailable",
            "dirty_tree": True,
            "v50_status": ["git_state_unavailable"],
            "v50_snapshot_tracked": False,
        }
    tracked = not any(row.startswith("??") for row in status)
    return {
        "commit": commit,
        "dirty_tree": bool(status),
        "v50_status": status,
        "v50_snapshot_tracked": tracked and not status,
    }


def _markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Phase 0 Execution Snapshot",
            "",
            f"- Status: `{report['status']}`",
            f"- Git commit: `{report['git_commit']}`",
            f"- Files: `{report['scope']['file_count']}`",
            f"- Source manifest: `{report['source_manifest_sha256']}`",
            "",
            "## Blockers",
            "",
            *[f"- `{item}`" for item in report["blockers"]],
            "",
            "This tool never commits automatically. A working-tree hash is useful for diagnosis but cannot substitute for a clean committed formal snapshot.",
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare the Phase 0 reproducible execution snapshot.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--freeze", action="store_true")
    args = parser.parse_args()
    report = prepare_snapshot(output_dir=Path(args.output_dir), freeze=args.freeze)
    print(json.dumps({"status": report["status"], "blockers": report["blockers"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
