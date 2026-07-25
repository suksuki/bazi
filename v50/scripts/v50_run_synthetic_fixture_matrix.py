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

from core.contracts import BirthInputCanonical, Topic
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
from core.state import FlowState, StateEvolution, TemporalState, build_bazi_flow_states, build_state_evolution


FIXTURE_DIR = V50_ROOT / "data" / "validation" / "fixtures"
FIXTURE_PATHS = {
    "synthetic_fixture_matrix_v1": FIXTURE_DIR / "synthetic_fixture_matrix_v1.json",
    "synthetic_fixture_matrix_v2": FIXTURE_DIR / "synthetic_fixture_matrix_v2.json",
}
REPORT_DIR = V50_ROOT / "data" / "validation" / "reports"


def run_group(group: str = "synthetic_fixture_matrix_v1", *, write_report: bool = False) -> dict[str, Any]:
    fixture_path = FIXTURE_PATHS.get(group)
    if fixture_path is None:
        raise ValueError(f"unsupported group {group}")
    payload = json.loads(fixture_path.read_text(encoding="utf-8"))
    if payload["group"] != group:
        raise ValueError(f"unsupported group {group}")

    source_payload = json.loads((FIXTURE_DIR / payload["source_fixture"]).read_text(encoding="utf-8"))
    source_cases = {case["case_id"]: case for case in source_payload["cases"]}
    if group == "synthetic_fixture_matrix_v2":
        results = [_run_taxonomy_case(index=index, case=case, source_cases=source_cases) for index, case in enumerate(payload["cases"], start=1)]
    else:
        results = [_run_case(index=index, case=case, source_cases=source_cases) for index, case in enumerate(payload["cases"], start=1)]
    summary = {
        "group": group,
        "source_fixture": payload["source_fixture"],
        "total": len(results),
        "passed": sum(1 for result in results if result["passed"]),
        "failed": sum(1 for result in results if not result["passed"]),
        "expected_gap_count": sum(len(result.get("expected_gaps", [])) for result in results),
        "legacy_observation_count": sum(
            len(result.get("legacy_unvalidated_observations", [])) for result in results
        ),
        "expected_gap_cases": [result["case_id"] for result in results if result.get("expected_gaps")],
        "llm_used": False,
        "brain_used": False,
        "ui_used": False,
        "training_performed": False,
        "node_importance_policy_version": NODE_IMPORTANCE_POLICY_V2["policy_version"],
        "legacy_unvalidated_path_score_policy_version": LEGACY_PATH_SCORE_POLICY_V2["policy_version"],
        "checks": {
            "graph_path_role_importance_ablation": True,
            "flow_state_adapter": True,
            "state_delta": True,
            "judgment_checked": False,
        },
        "results": results,
    }
    if write_report:
        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        json_path = REPORT_DIR / f"{group}_report.json"
        md_path = REPORT_DIR / f"{group}_report.md"
        json_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        md_path.write_text(_markdown_report(summary), encoding="utf-8")
    return summary


def _run_taxonomy_case(*, index: int, case: dict[str, Any], source_cases: dict[str, dict[str, Any]]) -> dict[str, Any]:
    source_case = source_cases[case["source_case_id"]]
    reading_id = f"reading.synthetic.matrix.v2.{index:03d}"
    birth = BirthInputCanonical(**source_case["birth_input"])
    calendar = normalize_birth_input(birth)
    store = build_bazi_material_store(reading_id=reading_id, birth_input=birth, calendar=calendar)
    graph = build_mingli_graph_from_material_store(store)
    paths = explore_mingli_paths(graph)
    roles = classify_node_roles(graph, paths)
    analysis = analyze_mingli_graph(graph, path_result=paths, role_result=roles)
    state = build_mingli_state_from_graph_analysis(analysis)
    ablation = run_ablation_simulation(state, target_node_ids=[metric.node_id for metric in analysis.node_metrics[:5]])

    node_labels_by_id = {node.node_id: _node_key(node.label, node.position) for node in graph.nodes}
    snapshot = _taxonomy_snapshot(
        source_case=source_case,
        graph=graph,
        paths=paths,
        roles=roles,
        analysis=analysis,
        state=state,
        ablation=ablation,
        node_labels_by_id=node_labels_by_id,
    )
    errors, expected_gaps = _check_taxonomy_case(case=case, source_case=source_case, snapshot=snapshot)

    return {
        "case_id": case["case_id"],
        "source_case_id": case["source_case_id"],
        "matrix_category": case["matrix_category"],
        "chart": source_case["chart"],
        "passed": not errors,
        "errors": errors,
        "expected_gaps": expected_gaps,
        "gap_count": len(expected_gaps),
        "active_flows": state.active_flows,
        "path_hints": snapshot["path_hints"],
        "top_nodes": snapshot["top_nodes"],
        "roles_by_node": snapshot["roles_by_node"],
        "ablation_order": snapshot["ablation_order"],
        "checks": {
            "taxonomy_backed": True,
            "no_llm": True,
            "no_brain": True,
            "no_ui": True,
            "no_training": True,
            "known_gaps_are_reported_not_tuned": True,
        },
    }


def _run_case(*, index: int, case: dict[str, Any], source_cases: dict[str, dict[str, Any]]) -> dict[str, Any]:
    source_case = source_cases[case["source_case_id"]]
    reading_id = f"reading.synthetic.matrix.{index:03d}"
    birth = BirthInputCanonical(**source_case["birth_input"])
    calendar = normalize_birth_input(birth)
    store = build_bazi_material_store(reading_id=reading_id, birth_input=birth, calendar=calendar)
    graph = build_mingli_graph_from_material_store(store)
    paths = explore_mingli_paths(graph)
    roles = classify_node_roles(graph, paths)
    analysis = analyze_mingli_graph(graph, path_result=paths, role_result=roles)
    state = build_mingli_state_from_graph_analysis(analysis)
    ablation = run_ablation_simulation(state, target_node_ids=[metric.node_id for metric in analysis.node_metrics[:5]])
    flow_states = build_bazi_flow_states(analysis=analysis, path_result=paths, state=state, simulation_report=ablation)
    temporal_state = _temporal_state(reading_id=reading_id, case=case)
    state_evolution = _state_evolution(reading_id=reading_id, case=case, flow_states=flow_states, temporal_state=temporal_state)

    node_labels_by_id = {node.node_id: _node_key(node.label, node.position) for node in graph.nodes}
    flow_summary = [_flow_summary(flow_state, node_labels_by_id=node_labels_by_id) for flow_state in flow_states]
    errors: list[str] = []
    flow_errors, legacy_observations = _check_expected_flow_states(
        case,
        flow_states,
        node_labels_by_id=node_labels_by_id,
    )
    errors.extend(flow_errors)
    errors.extend(_check_forbidden_flow_mechanisms(case, flow_states))
    if state_evolution is not None:
        legacy_observations.extend(_check_state_evolution(case, state_evolution))
    elif "expected_state_evolution" in case:
        legacy_observations.append("missing expected legacy StateEvolution")
    errors.extend(_check_boundaries(flow_states, state_evolution=state_evolution))

    return {
        "case_id": case["case_id"],
        "source_case_id": case["source_case_id"],
        "matrix_category": case["matrix_category"],
        "chart": " ".join(
            [
                source_case["birth_input"]["year_pillar"],
                source_case["birth_input"]["month_pillar"],
                source_case["birth_input"]["day_pillar"],
                source_case["birth_input"]["hour_pillar"],
            ]
        ),
        "passed": not errors,
        "errors": errors,
        "legacy_unvalidated_observations": legacy_observations,
        "active_flows": state.active_flows,
        "flow_states": flow_summary,
        "state_evolution": _evolution_summary(state_evolution),
        "top_nodes": [
            {
                "node": _node_key(metric.label, metric.position),
                "importance": metric.final_importance,
                "codes": metric.explanation_codes,
            }
            for metric in analysis.node_metrics[:5]
        ],
        "ablation_order": [
            {
                "node": _node_key(result.target_label, result.target_position),
                "state_delta": result.state_delta,
                "affected_flows": result.affected_flows,
            }
            for result in ablation.ablation_results[:5]
        ],
        "checks": {
            "no_llm": True,
            "no_brain": True,
            "no_ui": True,
            "no_training": True,
            "flow_state_count": len(flow_states),
            "state_evolution_checked": state_evolution is not None,
        },
    }


def _taxonomy_snapshot(
    *,
    source_case: dict[str, Any],
    graph: Any,
    paths: Any,
    roles: Any,
    analysis: Any,
    state: Any,
    ablation: Any,
    node_labels_by_id: dict[str, str],
) -> dict[str, Any]:
    roles_by_node: dict[str, list[str]] = {}
    for assignment in roles.assignments:
        node_key = _node_key(assignment.label, assignment.position)
        roles_by_node.setdefault(node_key, []).append(assignment.role.value)
    path_hints = sorted({hint for path in paths.paths for hint in path.mechanism_hints})
    top_nodes = [
        {
            "node": _node_key(metric.label, metric.position),
            "importance": metric.final_importance,
            "codes": metric.explanation_codes,
        }
        for metric in analysis.node_metrics[:5]
    ]
    ablation_order = [
        {
            "node": _node_key(result.target_label, result.target_position),
            "state_delta": result.state_delta,
            "affected_flows": result.affected_flows,
        }
        for result in ablation.ablation_results[:5]
    ]
    return {
        "case_type": source_case["case_type"],
        "chart": source_case["chart"],
        "active_flows": state.active_flows,
        "mechanism_scores": state.mechanism_scores,
        "path_hints": path_hints,
        "top_nodes": top_nodes,
        "top_node_set": {item["node"] for item in top_nodes},
        "roles_by_node": roles_by_node,
        "ablation_order": ablation_order,
        "ablation_node_set": {item["node"] for item in ablation_order},
    }


def _check_taxonomy_case(*, case: dict[str, Any], source_case: dict[str, Any], snapshot: dict[str, Any]) -> tuple[list[str], list[dict[str, Any]]]:
    errors: list[str] = []
    expected_gaps: list[dict[str, Any]] = []
    expected_gap_codes = set(case.get("expected_gap_codes", []))

    top_node_options = _node_expectation_options(source_case.get("expected_top_node", []))
    if top_node_options and not any(option in snapshot["top_node_set"] for option in top_node_options):
        code = "top_node:" + "|".join(top_node_options)
        _append_gap_or_error(
            errors=errors,
            expected_gaps=expected_gaps,
            expected_gap_codes=expected_gap_codes,
            code=code,
            message=f"top nodes do not include taxonomy expected options {top_node_options}",
            actual=snapshot["top_nodes"],
        )

    ablation_options = _ablation_expectation_options(source_case.get("expected_ablation", []))
    if ablation_options and not any(option in snapshot["ablation_node_set"] for option in ablation_options):
        code = "ablation:" + "|".join(ablation_options)
        _append_gap_or_error(
            errors=errors,
            expected_gaps=expected_gaps,
            expected_gap_codes=expected_gap_codes,
            code=code,
            message=f"ablation order does not include taxonomy expected options {ablation_options}",
            actual=snapshot["ablation_order"],
        )

    for expected_path in source_case.get("expected_path", []):
        if not _path_satisfied(expected_path, source_case=source_case, snapshot=snapshot):
            code = f"path:{expected_path}"
            _append_gap_or_error(
                errors=errors,
                expected_gaps=expected_gaps,
                expected_gap_codes=expected_gap_codes,
                code=code,
                message=f"path expectation not satisfied: {expected_path}",
                actual={
                    "active_flows": snapshot["active_flows"],
                    "path_hints": snapshot["path_hints"],
                    "roles_by_node": snapshot["roles_by_node"],
                },
            )

    errors.extend(_check_taxonomy_must_not(source_case=source_case, snapshot=snapshot))
    return errors, expected_gaps


def _append_gap_or_error(
    *,
    errors: list[str],
    expected_gaps: list[dict[str, Any]],
    expected_gap_codes: set[str],
    code: str,
    message: str,
    actual: Any,
) -> None:
    if code in expected_gap_codes:
        expected_gaps.append({"code": code, "message": message, "actual": actual})
    else:
        errors.append(message)


def _node_expectation_options(values: list[str]) -> list[str]:
    options: list[str] = []
    for value in values:
        if "_or_" in value:
            options.extend(part for part in value.split("_or_") if ":" in part)
        elif ":" in value:
            options.append(value)
    return options


def _ablation_expectation_options(values: list[str]) -> list[str]:
    options: list[str] = []
    for value in values:
        if value == "no_strong_prefix_required":
            continue
        text = value.removeprefix("remove_").replace("_under_luck_overlay", "")
        if "_or_" in text:
            options.extend(part for part in text.split("_or_") if ":" in part)
        elif ":" in text:
            options.append(text)
    return options


def _path_satisfied(expected_path: str, *, source_case: dict[str, Any], snapshot: dict[str, Any]) -> bool:
    active_flows = set(snapshot["active_flows"])
    path_hints = set(snapshot["path_hints"])
    roles_by_node = snapshot["roles_by_node"]
    expected_nodes = _node_expectation_options(source_case.get("expected_top_node", []))
    if expected_path in {"environment_path"}:
        return any(node.endswith(":month_branch") for node in snapshot["top_node_set"])
    if expected_path in {"combination_bridge"}:
        return "mechanism_hint.combination_bridge" in path_hints
    if expected_path in {"output_controls_pressure", "natal_output_controls_pressure"}:
        return "flow.output_controls_pressure" in active_flows or "mechanism_hint.output_controls_pressure" in path_hints
    if expected_path in {"output_to_wealth"}:
        return "flow.output_to_wealth_potential" in active_flows or "mechanism_hint.output_to_wealth" in path_hints
    if expected_path in {"converter_path", "output_path"}:
        return any("converter_node" in roles_by_node.get(node, []) for node in expected_nodes)
    if expected_path in {"anchor_path"}:
        return any("anchor_node" in roles_by_node.get(node, []) for node in expected_nodes)
    if expected_path in {"storage_path"}:
        return any("buffer_node" in roles_by_node.get(node, []) for node in expected_nodes)
    if expected_path in {"baseline_structure", "structural_baseline"}:
        return "flow.structural_baseline" in active_flows or "mechanism_hint.structural_path" in path_hints
    if expected_path in {"bridge_under_pressure"}:
        return "mechanism_hint.combination_bridge" in path_hints or "flow.output_controls_pressure" in active_flows
    return False


def _check_taxonomy_must_not(*, source_case: dict[str, Any], snapshot: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    roles_by_node = snapshot["roles_by_node"]
    active_flows = set(snapshot["active_flows"])
    path_hints = set(snapshot["path_hints"])
    top_node_set = snapshot["top_node_set"]
    must_not = set(source_case.get("must_not", []))

    if "fortune_claim" in must_not or "annual_fortune_claim" in must_not:
        serialized = json.dumps(
            {
                "active_flows": snapshot["active_flows"],
                "path_hints": snapshot["path_hints"],
                "top_nodes": snapshot["top_nodes"],
                "roles_by_node": snapshot["roles_by_node"],
                "ablation_order": snapshot["ablation_order"],
            },
            ensure_ascii=False,
        )
        fortune_terms = ["guaranteed_wealth", "fortune_claim", "必然发财", "大富大贵", "一定离婚"]
        present = [term for term in fortune_terms if term in serialized]
        if present:
            errors.append(f"fortune terms leaked into structural matrix: {present}")

    if {"bridge_node_forced", "forced_bridge_node", "fake_metal_bridge"} & must_not:
        if any("bridge_node" in role_list for role_list in roles_by_node.values()):
            errors.append("bridge node was forced in non-bridge taxonomy case")

    if "bridge_role_survives_after_required_node_removed" in must_not:
        if any("bridge_node" in role_list for role_list in roles_by_node.values()):
            errors.append("bridge role survived in broken combination taxonomy case")

    if {"forced_output_controls_pressure", "output_controls_pressure_forced"} & must_not:
        if "flow.output_controls_pressure" in active_flows or "mechanism_hint.output_controls_pressure" in path_hints:
            errors.append("output_controls_pressure was forced in taxonomy case")

    if "ignore_original_bridge" in must_not:
        if not any("bridge_node" in role_list for role_list in roles_by_node.values()):
            errors.append("original bridge was ignored")

    if "ignore_output_converter" in must_not:
        if not any("converter_node" in role_list for role_list in roles_by_node.values()):
            errors.append("output converter was ignored")

    if "year_or_luck_rewrites_natal_structure" in must_not or "year_rewrites_natal_structure" in must_not:
        expected_nodes = set(_node_expectation_options(source_case.get("expected_top_node", [])))
        if expected_nodes and not (expected_nodes & top_node_set):
            errors.append("timing overlay rewrote natal top-node structure")

    return errors


def _temporal_state(*, reading_id: str, case: dict[str, Any]) -> TemporalState | None:
    payload = case.get("temporal_state")
    if not payload:
        return None
    return TemporalState(
        state_id=f"temporal_state:{reading_id}:{case['case_id']}",
        reading_id=reading_id,
        timing_layer=payload["timing_layer"],
        activated_paths=payload.get("activated_paths", []),
        weakened_nodes=payload.get("weakened_nodes", []),
        rerouted_flows=payload.get("rerouted_flows", []),
        mechanism_shifts=payload.get("mechanism_shifts", {}),
        state_delta_refs=[f"state_delta:{case['case_id']}:candidate"],
        evidence_refs=payload["evidence_refs"],
        confidence=payload.get("confidence", 0.6),
    )


def _state_evolution(
    *,
    reading_id: str,
    case: dict[str, Any],
    flow_states: list[FlowState],
    temporal_state: TemporalState | None,
) -> StateEvolution | None:
    expected = case.get("expected_state_evolution")
    if not expected:
        return None
    flow_state = next((item for item in flow_states if item.mechanism == expected["mechanism"]), None)
    if flow_state is None:
        return None
    return build_state_evolution(
        reading_id=reading_id,
        domain=Topic(expected["domain"]),
        current_flow_state=flow_state,
        temporal_state=temporal_state,
    )


def _check_expected_flow_states(
    case: dict[str, Any],
    flow_states: list[FlowState],
    *,
    node_labels_by_id: dict[str, str],
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    legacy_observations: list[str] = []
    by_mechanism = {flow_state.mechanism: flow_state for flow_state in flow_states}
    for expected in case.get("expected_flow_states", []):
        flow_state = by_mechanism.get(expected["mechanism"])
        if flow_state is None:
            errors.append(f"missing expected flow mechanism: {expected['mechanism']}")
            continue
        for field_name, actual in (
            ("min_output_strength", flow_state.output_strength),
            ("min_path_score", flow_state.path_score),
            ("min_ablation_sensitivity", flow_state.ablation_sensitivity),
        ):
            threshold = expected.get(field_name)
            if threshold is not None and actual < threshold:
                legacy_observations.append(
                    f"{flow_state.mechanism} {field_name} expected>={threshold} actual={actual}"
                )
        actual_nodes = {node_labels_by_id.get(node_id, node_id) for node_id in flow_state.node_refs}
        missing_nodes = sorted(set(expected.get("required_node_labels", [])) - actual_nodes)
        if missing_nodes:
            legacy_observations.append(
                f"{flow_state.mechanism} missing required node labels: {missing_nodes}"
            )
    return errors, legacy_observations


def _check_forbidden_flow_mechanisms(case: dict[str, Any], flow_states: list[FlowState]) -> list[str]:
    actual = {flow_state.mechanism for flow_state in flow_states}
    present = sorted(set(case.get("forbidden_flow_mechanisms", [])) & actual)
    return [f"forbidden flow mechanisms present: {present}"] if present else []


def _check_state_evolution(case: dict[str, Any], evolution: StateEvolution) -> list[str]:
    expected = case.get("expected_state_evolution", {})
    errors: list[str] = []
    if expected.get("trend") and evolution.trend.value != expected["trend"]:
        errors.append(f"StateEvolution trend mismatch expected={expected['trend']} actual={evolution.trend.value}")
    if evolution.velocity < expected.get("min_velocity", 0.0):
        errors.append(f"StateEvolution velocity expected>={expected['min_velocity']} actual={evolution.velocity}")
    for dimension, sign in expected.get("required_delta_signs", {}).items():
        value = evolution.delta_by_dimension.get(dimension)
        if value is None:
            errors.append(f"StateEvolution missing delta dimension: {dimension}")
            continue
        if sign == "positive" and value <= 0.05:
            errors.append(f"StateEvolution {dimension} expected positive actual={value}")
        if sign == "negative" and value >= -0.05:
            errors.append(f"StateEvolution {dimension} expected negative actual={value}")
    for field_name, actual_values in (
        ("required_activated_by", evolution.activated_by),
        ("required_suppressed_by", evolution.suppressed_by),
    ):
        missing = sorted(set(expected.get(field_name, [])) - set(actual_values))
        if missing:
            errors.append(f"StateEvolution missing {field_name}: {missing}")
    return errors


def _check_boundaries(flow_states: list[FlowState], *, state_evolution: StateEvolution | None) -> list[str]:
    errors: list[str] = []
    for flow_state in flow_states:
        if flow_state.creates_judgment or flow_state.calls_brain or flow_state.calls_llm:
            errors.append(f"FlowState boundary violated: {flow_state.state_id}")
    if state_evolution is not None and (state_evolution.creates_judgment or state_evolution.calls_brain or state_evolution.calls_llm):
        errors.append(f"StateEvolution boundary violated: {state_evolution.evolution_id}")
    return errors


def _flow_summary(flow_state: FlowState, *, node_labels_by_id: dict[str, str]) -> dict[str, Any]:
    return {
        "state_id": flow_state.state_id,
        "mechanism": flow_state.mechanism,
        "output_strength": flow_state.output_strength,
        "legacy_unvalidated_path_score": flow_state.path_score,
        "ablation_sensitivity": flow_state.ablation_sensitivity,
        "confidence": flow_state.confidence,
        "node_labels": [node_labels_by_id.get(node_id, node_id) for node_id in flow_state.node_refs],
        "path_refs_count": len(flow_state.path_refs),
        "evidence_refs_count": len(flow_state.evidence_refs),
    }


def _evolution_summary(evolution: StateEvolution | None) -> dict[str, Any] | None:
    if evolution is None:
        return None
    return {
        "evolution_id": evolution.evolution_id,
        "domain": evolution.domain.value,
        "trend": evolution.trend.value,
        "velocity": evolution.velocity,
        "delta_by_dimension": evolution.delta_by_dimension,
        "activated_by": evolution.activated_by,
        "suppressed_by": evolution.suppressed_by,
        "confidence": evolution.confidence,
    }


def _node_key(label: str, position: str) -> str:
    return f"{label}:{position}"


def _markdown_report(summary: dict[str, Any]) -> str:
    lines = [
        f"# {summary['group']} Report",
        "",
        f"Source fixture: `{summary['source_fixture']}`",
        "",
        f"Total: {summary['total']}",
        f"Passed: {summary['passed']}",
        f"Failed: {summary['failed']}",
        f"Legacy unvalidated observations: `{summary['legacy_observation_count']}`",
        "",
        "Boundary:",
        "",
        f"- LLM used: `{summary['llm_used']}`",
        f"- Brain used: `{summary['brain_used']}`",
        f"- UI used: `{summary['ui_used']}`",
        f"- Training performed: `{summary['training_performed']}`",
        f"- Node importance policy: `{summary['node_importance_policy_version']}`",
        f"- Legacy unvalidated path score policy: `{summary['legacy_unvalidated_path_score_policy_version']}`",
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
    lines.extend(["", "## Expected Algorithm Gaps", ""])
    gap_results = [result for result in summary["results"] if result.get("expected_gaps")]
    if not gap_results:
        lines.append("None.")
    for result in gap_results:
        lines.append(f"### {result['case_id']}")
        lines.append("")
        for gap in result["expected_gaps"]:
            lines.append(f"- `{gap['code']}`: {gap['message']}")
        lines.append("")
    lines.extend(["", "## Case Summary", ""])
    for result in summary["results"]:
        status = "PASS" if result["passed"] else "FAIL"
        if "flow_states" in result:
            flow_labels = ", ".join(flow["mechanism"] for flow in result["flow_states"])
        else:
            flow_labels = ", ".join(result.get("active_flows", []))
        evolution = result.get("state_evolution")
        evolution_label = f" / evolution={evolution['trend']}" if evolution else ""
        gap_label = f" / expected_gaps={len(result.get('expected_gaps', []))}" if result.get("expected_gaps") else ""
        lines.append(f"- {status} `{result['case_id']}`: {flow_labels}{evolution_label}{gap_label}")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run V50 Synthetic Fixture Matrix v1.")
    parser.add_argument("--group", default="synthetic_fixture_matrix_v1")
    parser.add_argument("--write-report", action="store_true")
    args = parser.parse_args()
    summary = run_group(args.group, write_report=args.write_report)
    print(
        json.dumps(
            {key: summary[key] for key in ("group", "source_fixture", "total", "passed", "failed", "llm_used", "brain_used", "training_performed")},
            ensure_ascii=False,
            indent=2,
        )
    )
    if summary["failed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
