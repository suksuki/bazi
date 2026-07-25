from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = ROOT / "reports" / "discovery-archaeology" / "v1"
SEARCH_ROOTS = (
    ROOT.parent / "v30" / ".runtime" / "validation" / "518k",
    ROOT.parent / "v30" / "reports",
    ROOT.parent / "v30" / "docs",
    ROOT.parent / "v30" / "scripts",
    ROOT / "reports",
    ROOT / "data" / "research",
)
TOKENS = {
    "universe_518k": ("518k", "518000", "universe"),
    "ten_god_vector": ("ten_god", "十神", "vector"),
    "cluster": ("cluster", "聚类"),
    "singularity": ("singular", "奇点", "outlier", "anomaly"),
    "energy_break": ("energy_break", "断裂", "break_year"),
    "special_year": ("special_year", "特殊年份", "timing"),
    "embedding": ("embedding", "embed"),
    "llm_analysis": ("gemini", "gpt", "claude", "llm_analysis"),
}


def inventory() -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    missing_roots: list[str] = []
    for root in SEARCH_ROOTS:
        if not root.exists():
            missing_roots.append(str(root))
            continue
        for path in root.rglob("*"):
            if not path.is_file() or ".git" in path.parts or "__pycache__" in path.parts:
                continue
            family = _family(path)
            if family == "unclassified" and "518k" not in str(root).lower():
                continue
            stat = path.stat()
            rows.append(
                {
                    "path": str(path.resolve()),
                    "relative_to_search_root": str(path.relative_to(root)),
                    "search_root": str(root.resolve()),
                    "artifact_family": family if family != "unclassified" else "universe_518k",
                    "suffix": path.suffix.lower(),
                    "size_bytes": stat.st_size,
                    "modified_at": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
                    "reproducibility_clues": _clues(path),
                    "known_status": "found_unreviewed",
                    "production_eligible": False,
                    "theory_evidence_claimed": False,
                }
            )
    family_counts = Counter(row["artifact_family"] for row in rows)
    suffix_counts = Counter(row["suffix"] or "no_suffix" for row in rows)
    return {
        "version": "deepbazi.discovery_archaeology_inventory.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "completed",
        "observed_data": {
            "search_roots": [str(path) for path in SEARCH_ROOTS],
            "missing_roots": missing_roots,
            "artifact_count": len(rows),
            "total_size_bytes": sum(row["size_bytes"] for row in rows),
            "family_counts": dict(sorted(family_counts.items())),
            "suffix_counts": dict(sorted(suffix_counts.items())),
        },
        "artifacts": rows,
        "interpretation": {
            "observed": "Historical research assets were located and classified without reading them into production reasoning.",
            "inference": "Presence is not reproducibility, evidence quality, or theory validity.",
            "recommendation": "Review one artifact family at a time and preserve its original input, algorithm, output, and abandonment reason.",
        },
        "boundary_status": {
            "read_only": True,
            "files_copied": False,
            "files_moved": False,
            "files_deleted": False,
            "production_runtime_modified": False,
            "theory_modified": False,
            "research_asset_promoted": False,
            "training_performed": False,
        },
    }


def _family(path: Path) -> str:
    text = str(path).lower()
    for family, tokens in TOKENS.items():
        if any(token.lower() in text for token in tokens):
            return family
    return "unclassified"


def _clues(path: Path) -> list[str]:
    clues: list[str] = []
    if path.suffix.lower() in {".py", ".sh"}:
        clues.append("executable_source")
    if path.suffix.lower() in {".json", ".jsonl", ".csv", ".parquet", ".npy", ".npz"}:
        clues.append("structured_data")
    if path.name.lower().startswith(("readme", "manifest", "index")):
        clues.append("documentation_or_manifest")
    if "report" in path.name.lower() or path.suffix.lower() == ".md":
        clues.append("human_readable_report")
    return clues or ["unknown_reproducibility"]


def write_report(report: dict[str, Any], output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "discovery_archaeology_inventory_v1.json"
    md_path = output_dir / "discovery_archaeology_inventory_v1.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    observed = report["observed_data"]
    lines = [
        "# Discovery Archaeology Inventory v1",
        "",
        f"- Status: `{report['status']}`",
        f"- Artifacts: `{observed['artifact_count']}`",
        f"- Total bytes: `{observed['total_size_bytes']}`",
        f"- Missing roots: `{len(observed['missing_roots'])}`",
        "",
        "## Families",
        "",
        "| Family | Files |",
        "| --- | ---: |",
    ]
    for family, count in observed["family_counts"].items():
        lines.append(f"| {family} | {count} |")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            f"- Observed: {report['interpretation']['observed']}",
            f"- Inference: {report['interpretation']['inference']}",
            f"- Recommendation: {report['interpretation']['recommendation']}",
            "",
            "## Boundary",
            "",
            "```json",
            json.dumps(report["boundary_status"], ensure_ascii=False, indent=2),
            "```",
            "",
            "完整逐文件清单见同目录 JSON。",
            "",
        ]
    )
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return json_path, md_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Inventory historical Discovery assets without mutating them.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()
    report = inventory()
    paths = write_report(report, Path(args.output_dir))
    print(json.dumps({"status": report["status"], "reports": [str(path) for path in paths]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
