#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


V50_ROOT = Path(__file__).resolve().parents[1]
for path in (V50_ROOT / "packages", V50_ROOT / "apps"):
    value = str(path)
    if value not in sys.path:
        sys.path.insert(0, value)

from core.contracts import Topic
from core.state import FlowState, TemporalState, build_state_evolution
from core.timing import build_timing_model_candidates_v1


FIXTURE_PATH = V50_ROOT / "data" / "validation" / "fixtures" / "timing_synthetic_validation_v1.json"
REPORT_DIR = V50_ROOT / "data" / "validation" / "reports"


def run_group(group: str = "timing_synthetic_validation_v1", *, write_report: bool = False) -> dict[str, Any]:
    payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    if payload["group"] != group:
        raise ValueError(f"unsupported group {group}")
    candidates = {candidate.model_id: candidate for candidate in build_timing_model_candidates_v1()}
    results = [_run_fixture(fixture=fixture, candidates=candidates) for fixture in payload["fixtures"]]
    summary = {
        "version": "v50.timing_synthetic_validation_result.v1",
        "group": group,
        "fixture_file": str(FIXTURE_PATH),
        "total": len(results),
        "passed": sum(1 for result in results if result["passed"]),
        "failed": sum(1 for result in results if not result["passed"]),
        "llm_used": False,
        "brain_used": False,
        "training_performed": False,
        "runtime_timing_policy_activated": False,
        "layer_counts": _layer_counts(results),
        "results": results,
    }
    if write_report:
        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        json_path = REPORT_DIR / f"{group}_report.json"
        md_path = REPORT_DIR / f"{group}_report.md"
        json_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        md_path.write_text(_markdown_report(summary), encoding="utf-8")
    return summary


def _run_fixture(*, fixture: dict[str, Any], candidates: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    checks: dict[str, bool] = {}
    observed: dict[str, Any] = {}

    candidate = candidates.get(fixture["candidate_model_id"])
    if candidate is None:
        errors.append(f"candidate_missing:{fixture['candidate_model_id']}")
        return _result(fixture=fixture, errors=errors, checks=checks, observed=observed)

    current_flow = _flow_state(fixture=fixture, payload=fixture["current_flow_state"], suffix="current")
    previous_payload = fixture.get("previous_flow_state")
    previous_flow = _flow_state(fixture=fixture, payload=previous_payload, suffix="previous") if previous_payload else None
    temporal_state = _temporal_state(fixture=fixture)
    evolution = build_state_evolution(
        reading_id=fixture["reading_id"],
        domain=Topic(fixture["domain"]),
        current_flow_state=current_flow,
        previous_flow_state=previous_flow,
        temporal_state=temporal_state,
    )
    expected = fixture["expected"]

    observed.update(
        {
            "candidate_model_id": candidate.model_id,
            "timing_layer": candidate.timing_layer.value,
            "candidate_outputs": sorted(output.value for output in candidate.simulator_outputs),
            "delta_keys": sorted(evolution.delta_by_dimension),
            "trend": evolution.trend.value,
            "velocity": evolution.velocity,
            "activated_by": sorted(evolution.activated_by),
            "suppressed_by": sorted(evolution.suppressed_by),
            "reason_codes": sorted(evolution.reason_codes),
            "current_state_refs": sorted(evolution.current_state_refs),
            "evidence_refs": sorted(evolution.evidence_refs),
        }
    )

    _check_subset(
        name="candidate_outputs",
        expected_values=expected["candidate_outputs"],
        actual_values=observed["candidate_outputs"],
        errors=errors,
        checks=checks,
    )
    _check_subset(
        name="delta_keys",
        expected_values=expected["delta_keys"],
        actual_values=observed["delta_keys"],
        errors=errors,
        checks=checks,
    )
    _check_subset(
        name="activated_by",
        expected_values=expected["activated_by"],
        actual_values=observed["activated_by"],
        errors=errors,
        checks=checks,
    )
    _check_subset(
        name="suppressed_by",
        expected_values=expected["suppressed_by"],
        actual_values=observed["suppressed_by"],
        errors=errors,
        checks=checks,
    )
    _check_subset(
        name="reason_codes",
        expected_values=expected["reason_codes"],
        actual_values=observed["reason_codes"],
        errors=errors,
        checks=checks,
    )

    checks["expected_trend"] = observed["trend"] == expected["trend"]
    if not checks["expected_trend"]:
        errors.append(f"trend_mismatch:{observed['trend']}")

    checks["candidate_not_runtime_active"] = candidate.runtime_active is False
    checks["candidate_does_not_mutate_natal"] = candidate.mutates_natal_structure is False
    checks["candidate_does_not_create_judgment"] = candidate.creates_judgment is False
    checks["candidate_no_brain"] = candidate.calls_brain is False
    checks["candidate_no_llm"] = candidate.calls_llm is False
    checks["temporal_does_not_mutate_natal"] = temporal_state.mutates_natal_structure is False
    checks["evolution_no_judgment"] = evolution.creates_judgment is False
    checks["evolution_no_brain"] = evolution.calls_brain is False
    checks["evolution_no_llm"] = evolution.calls_llm is False
    checks["must_not_change_preserved"] = all(item in candidate.does_not_change for item in expected["must_not_change"])
    for key, passed in checks.items():
        if not passed and not any(error.startswith(key) for error in errors):
            errors.append(f"check_failed:{key}")

    return _result(fixture=fixture, errors=errors, checks=checks, observed=observed)


def _flow_state(*, fixture: dict[str, Any], payload: dict[str, Any], suffix: str) -> FlowState:
    return FlowState(
        state_id=f"flow_state:{fixture['fixture_id']}:{suffix}",
        reading_id=fixture["reading_id"],
        mechanism=payload["mechanism"],
        path_refs=list(payload["path_refs"]),
        node_refs=list(payload["node_refs"]),
        mechanism_refs=list(payload["mechanism_refs"]),
        output_strength=float(payload["output_strength"]),
        path_score=float(payload["path_score"]),
        ablation_sensitivity=float(payload["ablation_sensitivity"]),
        evidence_refs=list(payload["evidence_refs"]),
        confidence=0.72,
    )


def _temporal_state(*, fixture: dict[str, Any]) -> TemporalState:
    payload = fixture["temporal_state"]
    return TemporalState(
        state_id=f"temporal_state:{fixture['fixture_id']}",
        reading_id=fixture["reading_id"],
        timing_layer=payload["timing_layer"],
        activated_paths=list(payload["activated_paths"]),
        weakened_nodes=list(payload["weakened_nodes"]),
        rerouted_flows=list(payload["rerouted_flows"]),
        mechanism_shifts=dict(payload["mechanism_shifts"]),
        state_delta_refs=list(payload["state_delta_refs"]),
        evidence_refs=list(payload["evidence_refs"]),
        confidence=float(payload["confidence"]),
    )


def _check_subset(
    *,
    name: str,
    expected_values: list[str],
    actual_values: list[str],
    errors: list[str],
    checks: dict[str, bool],
) -> None:
    missing = sorted(set(expected_values) - set(actual_values))
    checks[name] = not missing
    if missing:
        errors.append(f"{name}_missing:{missing}")


def _result(*, fixture: dict[str, Any], errors: list[str], checks: dict[str, bool], observed: dict[str, Any]) -> dict[str, Any]:
    return {
        "fixture_id": fixture["fixture_id"],
        "candidate_model_id": fixture["candidate_model_id"],
        "domain": fixture["domain"],
        "passed": not errors and all(checks.values()),
        "errors": errors,
        "checks": checks,
        "observed": observed,
        "llm_used": False,
        "brain_used": False,
        "training_performed": False,
    }


def _layer_counts(results: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for result in results:
        layer = str(result.get("observed", {}).get("timing_layer", "unknown"))
        counts[layer] = counts.get(layer, 0) + 1
    return dict(sorted(counts.items()))


def _markdown_report(summary: dict[str, Any]) -> str:
    lines = [
        f"# {summary['group']} Report",
        "",
        f"Total: {summary['total']}",
        f"Passed: {summary['passed']}",
        f"Failed: {summary['failed']}",
        f"LLM used: {summary['llm_used']}",
        f"Brain used: {summary['brain_used']}",
        f"Training performed: {summary['training_performed']}",
        f"Runtime timing policy activated: {summary['runtime_timing_policy_activated']}",
        "",
        "## Layer Counts",
        "",
    ]
    for layer, count in summary["layer_counts"].items():
        lines.append(f"- `{layer}`: {count}")
    lines.extend(["", "## Failed Cases", ""])
    failed = [result for result in summary["results"] if not result["passed"]]
    if not failed:
        lines.append("None.")
    for result in failed:
        lines.append(f"### {result['fixture_id']}")
        for error in result["errors"]:
            lines.append(f"- {error}")
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run V50 timing synthetic validation fixtures.")
    parser.add_argument("--group", default="timing_synthetic_validation_v1")
    parser.add_argument("--write-report", action="store_true")
    parser.add_argument("--fail-on-error", action="store_true")
    args = parser.parse_args()

    summary = run_group(args.group, write_report=args.write_report)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    if args.fail_on_error and summary["failed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
