from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


V50_ROOT = Path(__file__).resolve().parents[1]
PACKAGES_ROOT = V50_ROOT / "packages"
APPS_ROOT = V50_ROOT / "apps"
for path in (PACKAGES_ROOT, APPS_ROOT, V50_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from core.timing import TimingLayer, build_timing_model_candidates_v1


FIXTURE_DIR = V50_ROOT / "data" / "validation" / "fixtures"
REPORT_DIR = V50_ROOT / "data" / "validation" / "reports"
FIXTURE_PATH = FIXTURE_DIR / "timing_model_candidates_v1.json"


def build_fixture_payload() -> dict[str, Any]:
    candidates = build_timing_model_candidates_v1()
    return {
        "group": "timing_model_candidates_v1",
        "description": "Competing timing models for luck/year/month. They are research policy candidates, not runtime truth.",
        "runtime_active": False,
        "llm_used": False,
        "brain_used": False,
        "training_performed": False,
        "candidates": [candidate.model_dump(mode="json") for candidate in candidates],
    }


def validate_candidates(*, write_fixture: bool = False, write_report: bool = False) -> dict[str, Any]:
    payload = build_fixture_payload()
    candidates = build_timing_model_candidates_v1()
    layer_counts = Counter(candidate.timing_layer.value for candidate in candidates)
    family_counts = Counter(candidate.model_family.value for candidate in candidates)
    errors: list[str] = []
    expected_layer_counts = {
        TimingLayer.LUCK.value: 4,
        TimingLayer.YEAR.value: 4,
        TimingLayer.MONTH.value: 4,
    }
    if dict(layer_counts) != expected_layer_counts:
        errors.append(f"unexpected layer counts: {dict(layer_counts)}")
    if len(family_counts) != 12:
        errors.append("Timing Model Candidate v1 should keep 12 distinct model families")
    for candidate in candidates:
        if candidate.runtime_active or candidate.creates_judgment or candidate.calls_brain or candidate.calls_llm or candidate.mutates_natal_structure:
            errors.append(f"{candidate.model_id} violates runtime boundary")
        if "natal_immutable_facts" not in candidate.does_not_change:
            errors.append(f"{candidate.model_id} does not protect natal immutable facts")

    summary = {
        "group": payload["group"],
        "total": len(candidates),
        "passed": not errors,
        "errors": errors,
        "layer_counts": dict(sorted(layer_counts.items())),
        "family_counts": dict(sorted(family_counts.items())),
        "runtime_active": payload["runtime_active"],
        "llm_used": payload["llm_used"],
        "brain_used": payload["brain_used"],
        "training_performed": payload["training_performed"],
        "candidate_ids": [candidate.model_id for candidate in candidates],
        "highest_confidence_by_layer": _highest_confidence_by_layer(candidates),
    }
    if write_fixture:
        FIXTURE_DIR.mkdir(parents=True, exist_ok=True)
        FIXTURE_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    if write_report:
        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        (REPORT_DIR / "timing_model_candidates_v1_report.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        (REPORT_DIR / "timing_model_candidates_v1_report.md").write_text(_markdown_report(summary), encoding="utf-8")
    return summary


def _highest_confidence_by_layer(candidates: list[Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for layer in TimingLayer:
        layer_candidates = [candidate for candidate in candidates if candidate.timing_layer == layer]
        winner = max(layer_candidates, key=lambda candidate: candidate.current_confidence)
        result[layer.value] = {
            "model_id": winner.model_id,
            "model_family": winner.model_family.value,
            "confidence": winner.current_confidence,
        }
    return result


def _markdown_report(summary: dict[str, Any]) -> str:
    lines = [
        "# Timing Model Candidates v1 Report",
        "",
        f"Total: {summary['total']}",
        f"Passed: {summary['passed']}",
        "",
        "Boundary:",
        "",
        f"- Runtime active: `{summary['runtime_active']}`",
        f"- LLM used: `{summary['llm_used']}`",
        f"- Brain used: `{summary['brain_used']}`",
        f"- Training performed: `{summary['training_performed']}`",
        "",
        "## Layer Counts",
        "",
    ]
    for layer, count in summary["layer_counts"].items():
        lines.append(f"- `{layer}`: {count}")
    lines.extend(["", "## Highest Confidence By Layer", ""])
    for layer, item in summary["highest_confidence_by_layer"].items():
        lines.append(f"- `{layer}`: `{item['model_id']}` ({item['confidence']})")
    lines.extend(["", "## Errors", ""])
    if summary["errors"]:
        for error in summary["errors"]:
            lines.append(f"- {error}")
    else:
        lines.append("None.")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate V50 Timing Model Candidates v1.")
    parser.add_argument("--write-fixture", action="store_true")
    parser.add_argument("--write-report", action="store_true")
    args = parser.parse_args()
    summary = validate_candidates(write_fixture=args.write_fixture, write_report=args.write_report)
    print(
        json.dumps(
            {
                "group": summary["group"],
                "total": summary["total"],
                "passed": summary["passed"],
                "layer_counts": summary["layer_counts"],
                "runtime_active": summary["runtime_active"],
                "llm_used": summary["llm_used"],
                "brain_used": summary["brain_used"],
                "training_performed": summary["training_performed"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    if not summary["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

