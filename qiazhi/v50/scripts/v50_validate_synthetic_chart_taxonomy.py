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

from core.contracts import BirthInputCanonical


TAXONOMY_PATH = V50_ROOT / "data" / "validation" / "fixtures" / "synthetic_chart_taxonomy_v1.json"
REPORT_DIR = V50_ROOT / "data" / "validation" / "reports"

EXPECTED_CASE_TYPES = {
    "month_command_dominant",
    "bridge_node_dominant",
    "converter_dominant",
    "day_branch_anchor",
    "hidden_stem_dark_line",
    "complete_triple_combination",
    "broken_triple_combination",
    "clash_breaks_main_path",
    "output_to_wealth",
    "output_controls_pressure",
    "mixed_officer_killing_with_control",
    "resource_disrupts_output",
    "wealth_generates_officer",
    "peer_competes_for_wealth",
    "mixed_no_obvious_main_path",
    "luck_changes_main_path",
    "year_activates_key_node",
}

FORBIDDEN_FORTUNE_TERMS = {
    "good_fortune",
    "bad_fortune",
    "rich",
    "poor",
    "marriage_success",
    "divorce",
    "career_success",
    "guaranteed_wealth",
    "fortune_claim",
}


def validate_taxonomy(*, write_report: bool = False) -> dict[str, Any]:
    payload = json.loads(TAXONOMY_PATH.read_text(encoding="utf-8"))
    cases = payload["cases"]
    errors: list[str] = []
    case_types = Counter(case["case_type"] for case in cases)
    missing_types = sorted(EXPECTED_CASE_TYPES - set(case_types))
    extra_types = sorted(set(case_types) - EXPECTED_CASE_TYPES)
    if missing_types:
        errors.append(f"missing case types: {missing_types}")
    if extra_types:
        errors.append(f"unexpected case types: {extra_types}")
    for case in cases:
        errors.extend(_validate_case(case))
    summary = {
        "group": payload["group"],
        "total_case_types": len(case_types),
        "total_cases": len(cases),
        "passed": not errors,
        "errors": errors,
        "runtime_active": payload["runtime_active"],
        "llm_used": payload["llm_used"],
        "brain_used": payload["brain_used"],
        "training_performed": payload["training_performed"],
        "case_type_counts": dict(sorted(case_types.items())),
        "timing_overlay_cases": [case["case_type"] for case in cases if "timing_overlay" in case],
    }
    if write_report:
        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        json_path = REPORT_DIR / "synthetic_chart_taxonomy_v1_report.json"
        md_path = REPORT_DIR / "synthetic_chart_taxonomy_v1_report.md"
        json_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        md_path.write_text(_markdown_report(summary), encoding="utf-8")
    return summary


def _validate_case(case: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in ("case_type", "case_id", "chart", "birth_input", "expected_structure", "expected_top_node", "expected_path", "expected_ablation", "must_not"):
        if field not in case:
            errors.append(f"{case.get('case_id', '<unknown>')} missing {field}")
    if errors:
        return errors
    BirthInputCanonical(**case["birth_input"])
    expected_chart = " ".join(
        [
            case["birth_input"]["year_pillar"],
            case["birth_input"]["month_pillar"],
            case["birth_input"]["day_pillar"],
            case["birth_input"]["hour_pillar"],
        ]
    )
    if case["chart"] != expected_chart:
        errors.append(f"{case['case_id']} chart mismatch expected={expected_chart} actual={case['chart']}")
    for field in ("expected_structure", "expected_top_node", "expected_path", "expected_ablation", "must_not"):
        if not isinstance(case[field], list) or not case[field]:
            errors.append(f"{case['case_id']} {field} must be a non-empty list")
    serialized_expectations = json.dumps(
        {
            "expected_structure": case["expected_structure"],
            "expected_top_node": case["expected_top_node"],
            "expected_path": case["expected_path"],
            "expected_ablation": case["expected_ablation"],
        },
        ensure_ascii=False,
    )
    forbidden_present = sorted(term for term in FORBIDDEN_FORTUNE_TERMS if term in serialized_expectations)
    if forbidden_present:
        errors.append(f"{case['case_id']} contains fortune expectation terms: {forbidden_present}")
    if case["case_type"] in {"luck_changes_main_path", "year_activates_key_node"} and "timing_overlay" not in case:
        errors.append(f"{case['case_id']} timing case requires timing_overlay")
    return errors


def _markdown_report(summary: dict[str, Any]) -> str:
    lines = [
        "# Synthetic Chart Taxonomy v1 Report",
        "",
        f"Total case types: {summary['total_case_types']}",
        f"Total cases: {summary['total_cases']}",
        f"Passed: {summary['passed']}",
        "",
        "Boundary:",
        "",
        f"- Runtime active: `{summary['runtime_active']}`",
        f"- LLM used: `{summary['llm_used']}`",
        f"- Brain used: `{summary['brain_used']}`",
        f"- Training performed: `{summary['training_performed']}`",
        "",
        "## Case Type Counts",
        "",
    ]
    for case_type, count in summary["case_type_counts"].items():
        lines.append(f"- `{case_type}`: {count}")
    lines.extend(["", "## Timing Overlay Cases", ""])
    if summary["timing_overlay_cases"]:
        for case_type in summary["timing_overlay_cases"]:
            lines.append(f"- `{case_type}`")
    else:
        lines.append("None.")
    lines.extend(["", "## Errors", ""])
    if summary["errors"]:
        for error in summary["errors"]:
            lines.append(f"- {error}")
    else:
        lines.append("None.")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate V50 Synthetic Chart Taxonomy v1.")
    parser.add_argument("--write-report", action="store_true")
    args = parser.parse_args()
    summary = validate_taxonomy(write_report=args.write_report)
    print(
        json.dumps(
            {
                "group": summary["group"],
                "total_case_types": summary["total_case_types"],
                "total_cases": summary["total_cases"],
                "passed": summary["passed"],
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
