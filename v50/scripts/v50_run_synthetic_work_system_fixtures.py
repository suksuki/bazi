from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


V50_ROOT = Path(__file__).resolve().parents[1]
PACKAGES_ROOT = V50_ROOT / "packages"
APPS_ROOT = V50_ROOT / "apps"
for path in (PACKAGES_ROOT, APPS_ROOT, V50_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from core.contracts import BirthInputCanonical
from core.engines import normalize_birth_input
from core.engines.bazi import build_bazi_material_store
from core.graph import (
    NODE_IMPORTANCE_POLICY_V2,
    LEGACY_PATH_SCORE_POLICY_V2,
    analyze_mingli_graph,
    build_mingli_graph_from_material_store,
    classify_node_roles,
    explore_mingli_paths,
)
from core.simulation import build_mingli_state_from_graph_analysis, run_ablation_simulation


FIXTURE_PATH = V50_ROOT / "data" / "validation" / "fixtures" / "synthetic_work_system_v1.json"
REPORT_DIR = V50_ROOT / "data" / "validation" / "reports"


def run_group(group: str = "synthetic_work_system_v1", *, write_report: bool = False) -> dict[str, Any]:
    payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    if payload["group"] != group:
        raise ValueError(f"unsupported group {group}")
    results = [_run_case(index=index, case=case) for index, case in enumerate(payload["cases"], start=1)]
    summary = {
        "group": group,
        "total": len(results),
        "passed": sum(1 for result in results if result["passed"]),
        "failed": sum(1 for result in results if not result["passed"]),
        "legacy_observation_count": sum(
            len(result["legacy_unvalidated_observations"]) for result in results
        ),
        "llm_used": False,
        "brain_used": False,
        "ui_used": False,
        "training_performed": False,
        "node_importance_policy_version": NODE_IMPORTANCE_POLICY_V2["policy_version"],
        "legacy_unvalidated_path_score_policy_version": LEGACY_PATH_SCORE_POLICY_V2["policy_version"],
        "results": results,
    }
    if write_report:
        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        json_path = REPORT_DIR / f"{group}_report.json"
        md_path = REPORT_DIR / f"{group}_report.md"
        json_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        md_path.write_text(_markdown_report(summary), encoding="utf-8")
    return summary


def _run_case(*, index: int, case: dict[str, Any]) -> dict[str, Any]:
    reading_id = f"reading.synthetic.work.{index:03d}"
    birth = BirthInputCanonical(**case["birth_input"])
    calendar = normalize_birth_input(birth)
    store = build_bazi_material_store(reading_id=reading_id, birth_input=birth, calendar=calendar)
    graph = build_mingli_graph_from_material_store(store)
    paths = explore_mingli_paths(graph)
    roles = classify_node_roles(graph, paths)
    analysis = analyze_mingli_graph(graph, path_result=paths, role_result=roles)
    state = build_mingli_state_from_graph_analysis(analysis)
    ablation = run_ablation_simulation(state, target_node_ids=[metric.node_id for metric in analysis.node_metrics[:5]])

    role_map = _role_map(roles.assignments)
    candidate_path_hints = sorted(
        {hint for path in paths.paths for hint in path.mechanism_hints}
    )
    critical_nodes = [_node_key(metric.label, metric.position) for metric in analysis.node_metrics[:5]]
    ablation_order = [_node_key(result.target_label, result.target_position) for result in ablation.ablation_results]
    errors: list[str] = []
    errors.extend(_check_expected_roles(case, role_map))
    errors.extend(_check_must_not_roles(case, role_map))
    errors.extend(_check_expected_hints(case, candidate_path_hints))
    errors.extend(_check_expected_critical_nodes(case, critical_nodes))
    legacy_observations = _check_ablation_prefix(case, ablation_order)

    return {
        "case_id": case["case_id"],
        "structural_variable": case["structural_variable"],
        "chart": " ".join(
            [
                case["birth_input"]["year_pillar"],
                case["birth_input"]["month_pillar"],
                case["birth_input"]["day_pillar"],
                case["birth_input"]["hour_pillar"],
            ]
        ),
        "passed": not errors,
        "errors": errors,
        "legacy_unvalidated_observations": legacy_observations,
        "top_paths": [
            {
                "path_id": path.path_id,
                "legacy_unvalidated_path_score": path.legacy_unvalidated_metrics.path_score,
                "validation_state": path.validation_state.value,
                "evidence_vector": path.evidence_vector.model_dump(mode="json"),
                "node_labels": [_label_for_node(graph, node_id) for node_id in path.node_ids],
                "mechanism_hints": path.mechanism_hints,
            }
            for path in paths.paths[:5]
        ],
        "node_roles": {key: sorted(values) for key, values in role_map.items()},
        "critical_nodes": critical_nodes,
        "ablation_order": ablation_order,
        "checks": {
            "no_llm": True,
            "no_brain": True,
            "no_ui": True,
            "no_training": True,
            "paths_explored": len(paths.paths),
            "roles_assigned": len(roles.assignments),
        },
    }


def _role_map(assignments: list[Any]) -> dict[str, set[str]]:
    mapped: dict[str, set[str]] = {}
    for assignment in assignments:
        mapped.setdefault(_node_key(assignment.label, assignment.position), set()).add(assignment.role.value)
    return mapped


def _node_key(label: str, position: str) -> str:
    return f"{label}:{position}"


def _label_for_node(graph: Any, node_id: str) -> str:
    node = next(node for node in graph.nodes if node.node_id == node_id)
    return _node_key(node.label, node.position)


def _check_expected_roles(case: dict[str, Any], role_map: dict[str, set[str]]) -> list[str]:
    errors = []
    for key, expected_roles in case.get("expected_roles", {}).items():
        actual = role_map.get(key, set())
        missing = sorted(set(expected_roles) - actual)
        if missing:
            errors.append(f"missing expected roles for {key}: {missing}")
    return errors


def _check_must_not_roles(case: dict[str, Any], role_map: dict[str, set[str]]) -> list[str]:
    errors = []
    for key, forbidden_roles in case.get("must_not_roles", {}).items():
        actual = role_map.get(key, set())
        present = sorted(set(forbidden_roles) & actual)
        if present:
            errors.append(f"forbidden roles present for {key}: {present}")
    return errors


def _check_expected_hints(case: dict[str, Any], actual_hints: list[str]) -> list[str]:
    expected = set(case.get("expected_path_hints", []))
    missing = sorted(expected - set(actual_hints))
    return [f"missing expected path hints: {missing}"] if missing else []


def _check_expected_critical_nodes(case: dict[str, Any], critical_nodes: list[str]) -> list[str]:
    expected = set(case.get("expected_critical_nodes", []))
    if not expected:
        return []
    actual = set(critical_nodes)
    missing = sorted(expected - actual)
    return [f"missing expected critical nodes: {missing}"] if missing else []


def _check_ablation_prefix(case: dict[str, Any], ablation_order: list[str]) -> list[str]:
    expected = case.get("expected_ablation_prefix", [])
    if not expected:
        return []
    actual_prefix = ablation_order[: len(expected)]
    return [f"ablation prefix mismatch expected={expected} actual={actual_prefix}"] if actual_prefix != expected else []


def _markdown_report(summary: dict[str, Any]) -> str:
    lines = [
        f"# {summary['group']} Report",
        "",
        f"Total: {summary['total']}",
        f"Passed: {summary['passed']}",
        f"Failed: {summary['failed']}",
        f"Legacy unvalidated observations: {summary['legacy_observation_count']}",
        f"Node importance policy: `{summary['node_importance_policy_version']}`",
        f"Legacy unvalidated path score policy: `{summary['legacy_unvalidated_path_score_policy_version']}`",
        "",
        "## Failed Cases",
        "",
    ]
    failed = [result for result in summary["results"] if not result["passed"]]
    if not failed:
        lines.append("None.")
    for result in failed:
        lines.append(f"### {result['case_id']}")
        lines.append("")
        lines.append(f"Chart: `{result['chart']}`")
        lines.append("")
        for error in result["errors"]:
            lines.append(f"- {error}")
        lines.append("")
    lines.extend(["", "## Case Summary", ""])
    for result in summary["results"]:
        status = "PASS" if result["passed"] else "FAIL"
        lines.append(f"- {status} `{result['case_id']}`: {result['chart']}")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--group", default="synthetic_work_system_v1")
    parser.add_argument("--write-report", action="store_true")
    args = parser.parse_args()
    summary = run_group(args.group, write_report=args.write_report)
    print(json.dumps({key: summary[key] for key in ("group", "total", "passed", "failed", "llm_used", "brain_used", "training_performed")}, ensure_ascii=False, indent=2))
    if summary["failed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
