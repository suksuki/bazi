from __future__ import annotations

from typing import Any, Dict, List

from v19.rule_graph_orchestrator import build_chart_rule_graph, infer_question_intent
from v19.synthetic_validation.guided_cases import GuidedSyntheticCase


LEGACY_SYNTHETIC_FRAMEWORK_BACKFILL_VERSION = "v19.p53.legacy_synthetic_framework_backfill.v1"


def build_legacy_framework_adaptation_matrix() -> Dict[str, Any]:
    rows = [
        _matrix_row("P10", "P10 Synthetic Collision Review", "backfilled_to_rule_graph_runtime_contract", "framework_backfill", "pass"),
        _matrix_row("P11", "P11 Synthetic Expansion + Review UI", "backfilled_to_rule_graph_runtime_contract", "framework_backfill", "pass"),
        _matrix_row("P12-P27", "Governance / promotion / catalog expansion", "governance_boundary_compatible", "no_runtime_inference_adapter_required", "pass"),
        _matrix_row("P28-P30", "Ten God mechanism condition models", "native_condition_model_eval_dataset", "p28j_p28k_p28l_p29_p30", "pass"),
        _matrix_row("P31-P38", "Knowledge directory and priority topic expansion", "native_knowledge_catalog_to_condition_model_track", "p31_priority_topic_registry", "pass"),
        _matrix_row("P39-P45", "Rule conversion, audit, smart gate, canary", "native_condition_model_and_smart_gate_track", "p39_to_p45_validation_pipeline", "pass"),
        _matrix_row("P46-P52", "Rule Graph runtime, personalized questions, route-aware retrieval, UI", "native_rule_graph_runtime_track", "p46_to_p52_runtime_pipeline", "pass"),
    ]
    return {
        "version": LEGACY_SYNTHETIC_FRAMEWORK_BACKFILL_VERSION,
        "status": "pass" if all(row["status"] == "pass" for row in rows) else "fail",
        "runtime_scope": "p10_to_p52_framework_adaptation_inventory",
        "rows": rows,
        "summary": {
            "row_count": len(rows),
            "backfilled_rows": sum(1 for row in rows if "backfilled" in row["framework_track"]),
            "native_rows": sum(1 for row in rows if row["framework_track"].startswith("native_")),
            "governance_boundary_rows": sum(1 for row in rows if row["framework_track"] == "governance_boundary_compatible"),
        },
        "guardrails": [
            "P53_FRAMEWORK_ADAPTATION_MATRIX",
            "INVENTORY_ONLY",
            "NO_RUNTIME_RULE_ACTIVATION",
            "NO_RESULT_MUTATION",
            "NO_ANSWER_MUTATION",
        ],
    }


def build_guided_case_framework_backfill(case: GuidedSyntheticCase, agent_data: Dict[str, Any]) -> Dict[str, Any]:
    runtime_context = dict(agent_data.get("rule_graph_runtime_context") or {})
    chart_graph = build_chart_rule_graph(dict(agent_data.get("chart") or {}), dict(agent_data.get("time_context") or {}))
    expected = _expected_framework_contract(case)
    actual = _actual_framework_state(runtime_context, chart_graph)
    failures = _validate_backfill(expected, actual)
    return {
        "version": LEGACY_SYNTHETIC_FRAMEWORK_BACKFILL_VERSION,
        "status": "pass" if not failures else "fail",
        "case_id": case.case_id,
        "legacy_phase": _legacy_phase(case),
        "runtime_scope": "legacy_guided_synthetic_case_backfilled_to_rule_graph_contract",
        "expected": expected,
        "actual": actual,
        "failures": failures,
        "guardrails": [
            "P53_LEGACY_SYNTHETIC_FRAMEWORK_BACKFILL",
            "BACKFILL_EXPECTATIONS_ONLY",
            "NO_RUNTIME_RULE_ACTIVATION",
            "NO_RESULT_MUTATION",
            "NO_ANSWER_MUTATION",
            "NO_DOMAIN_RESULT_PREDICTION",
        ],
    }


def summarize_framework_backfill(case_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    rows = [dict(row.get("framework_backfill") or {}) for row in case_results if isinstance(row.get("framework_backfill"), dict)]
    failures = [row for row in rows if row.get("status") != "pass"]
    expected_lanes = sorted({lane for row in rows for lane in ((row.get("expected") or {}).get("expected_topic_lanes") or [])})
    expected_features = sorted({feature for row in rows for feature in ((row.get("expected") or {}).get("expected_graph_features") or [])})
    phases = sorted({str(row.get("legacy_phase") or "") for row in rows if row.get("legacy_phase")})
    return {
        "version": LEGACY_SYNTHETIC_FRAMEWORK_BACKFILL_VERSION,
        "status": "pass" if not failures and rows else "fail",
        "case_count": len(rows),
        "passed": sum(1 for row in rows if row.get("status") == "pass"),
        "failed": len(failures),
        "legacy_phases": phases,
        "expected_topic_lanes_covered": expected_lanes,
        "expected_graph_features_covered": expected_features,
        "failure_case_ids": [str(row.get("case_id") or "") for row in failures],
        "runtime_scope": "p10_p11_legacy_synthetic_matrix_rule_graph_compatibility_review",
        "guardrails": [
            "P53_LEGACY_SYNTHETIC_FRAMEWORK_BACKFILL",
            "DETERMINISTIC_RULE_GRAPH_COMPATIBILITY_CHECK",
            "NO_RUNTIME_RULE_ACTIVATION",
            "NO_RESULT_MUTATION",
            "NO_ANSWER_MUTATION",
        ],
    }


def _expected_framework_contract(case: GuidedSyntheticCase) -> Dict[str, Any]:
    primary_intent = infer_question_intent(case.question_key, case.message, "").get("intent") or "structure_overview"
    return {
        "primary_intent": primary_intent,
        "expected_route_ids": ["primary_question_route", "income_structure_route", "structure_overview_route"],
        "expected_topic_lanes": _expected_topic_lanes(case),
        "expected_graph_features": _expected_graph_features(case),
        "condition_axes_expected": _condition_axes_expected(case),
        "condition_axis_projection": _condition_axis_projection(case),
        "mutation_policy": {
            "engine_enabled_count": 0,
            "answer_mutation_count": 0,
            "runtime_mutation": False,
        },
    }


def _actual_framework_state(runtime_context: Dict[str, Any], chart_graph: Dict[str, Any]) -> Dict[str, Any]:
    routes = [dict(row) for row in runtime_context.get("routes") or [] if isinstance(row, dict)]
    selected_paths = [dict(row) for row in runtime_context.get("selected_paths") or [] if isinstance(row, dict)]
    selected_axes = sorted(
        {
            str(axis)
            for row in selected_paths
            for axis in row.get("condition_axes_required") or []
            if str(axis)
        }
    )
    matched_features = sorted(
        {
            str(feature)
            for row in selected_paths
            for feature in row.get("matched_features") or []
            if str(feature)
        }
    )
    return {
        "runtime_status": runtime_context.get("status") or "",
        "runtime_scope": runtime_context.get("runtime_scope") or "",
        "route_ids": [str(row.get("route_id") or "") for row in routes],
        "route_intents": {str(row.get("route_id") or ""): str(row.get("intent") or "") for row in routes},
        "route_scopes": {str(row.get("route_id") or ""): str(row.get("runtime_scope") or "") for row in routes},
        "selected_path_count": len(selected_paths),
        "selected_by_route_count": sum(1 for row in selected_paths if row.get("selected_by_route")),
        "topic_lanes": sorted((runtime_context.get("knowledge_route") or {}).get("by_topic_lane") or {}),
        "domains": sorted((runtime_context.get("knowledge_route") or {}).get("by_domain") or {}),
        "graph_features": sorted(str(tag) for tag in chart_graph.get("feature_tags") or [] if str(tag)),
        "matched_features": matched_features,
        "condition_axes_available": selected_axes,
        "summary": dict(runtime_context.get("summary") or {}),
        "answer_audit_status": (runtime_context.get("answer_audit") or {}).get("status") or "",
        "guardrails": list(runtime_context.get("guardrails") or []),
    }


def _validate_backfill(expected: Dict[str, Any], actual: Dict[str, Any]) -> List[Dict[str, Any]]:
    failures: List[Dict[str, Any]] = []
    if actual.get("runtime_status") != "rule_graph_runtime_context_ready":
        failures.append(_failure("framework_runtime_not_ready", expected="rule_graph_runtime_context_ready", actual=actual.get("runtime_status")))
    if actual.get("runtime_scope") != "measurement_route_pack_no_result_mutation":
        failures.append(_failure("framework_runtime_scope_mismatch", expected="measurement_route_pack_no_result_mutation", actual=actual.get("runtime_scope")))
    failures.extend(_missing("framework_route_missing", expected.get("expected_route_ids") or [], actual.get("route_ids") or []))
    primary_intent = (actual.get("route_intents") or {}).get("primary_question_route")
    if primary_intent != expected.get("primary_intent"):
        failures.append(_failure("framework_primary_intent_mismatch", expected=expected.get("primary_intent"), actual=primary_intent))
    if any(scope != "route_selection_only_no_result_mutation" for scope in (actual.get("route_scopes") or {}).values()):
        failures.append(_failure("framework_route_scope_mismatch", expected="route_selection_only_no_result_mutation", actual=actual.get("route_scopes")))
    failures.extend(_missing("framework_topic_lane_missing", expected.get("expected_topic_lanes") or [], actual.get("topic_lanes") or []))
    failures.extend(_missing("framework_graph_feature_missing", expected.get("expected_graph_features") or [], actual.get("graph_features") or []))
    failures.extend(_validate_axis_projection(expected.get("condition_axis_projection") or {}, actual))
    summary = actual.get("summary") or {}
    policy = expected.get("mutation_policy") or {}
    for key, expected_value in policy.items():
        if summary.get(key) != expected_value:
            failures.append(_failure("framework_mutation_policy_mismatch", expected={key: expected_value}, actual={key: summary.get(key)}))
    if actual.get("answer_audit_status") != "pass":
        failures.append(_failure("framework_answer_audit_failed", expected="pass", actual=actual.get("answer_audit_status")))
    if int(actual.get("selected_path_count") or 0) <= 0:
        failures.append(_failure("framework_selected_paths_missing", expected="selected_paths", actual=actual.get("selected_path_count")))
    if actual.get("selected_by_route_count") != actual.get("selected_path_count"):
        failures.append(_failure("framework_selected_route_binding_missing", expected=actual.get("selected_path_count"), actual=actual.get("selected_by_route_count")))
    return failures


def _validate_axis_projection(projection: Dict[str, str], actual: Dict[str, Any]) -> List[Dict[str, Any]]:
    failures: List[Dict[str, Any]] = []
    axes = set(actual.get("condition_axes_available") or [])
    matched = set(actual.get("matched_features") or [])
    graph_features = set(actual.get("graph_features") or [])
    route_intents = set((actual.get("route_intents") or {}).values())
    for axis, target in projection.items():
        if target == "condition_axis" and axis not in axes:
            failures.append(_failure("framework_condition_axis_missing", expected=axis, actual=sorted(axes)))
        elif target == "time_relation_feature" and not ({"time_relation", "time_layer"} & matched or {"time_relation", "time_layer"} & graph_features or "time_boundary" in route_intents):
            failures.append(_failure("framework_time_axis_projection_missing", expected="time_relation_or_time_boundary", actual={"matched": sorted(matched), "routes": sorted(route_intents)}))
        elif target == "branch_relation_feature" and not ("branch_relation" in matched or "branch_relation" in graph_features):
            failures.append(_failure("framework_branch_axis_projection_missing", expected="branch_relation", actual={"matched": sorted(matched), "graph": sorted(graph_features)}))
    return failures


def _expected_topic_lanes(case: GuidedSyntheticCase) -> List[str]:
    lanes = {"core_strength_foundation"}
    tags = set(case.tags)
    source = case.expected_source_signal_category
    answer_kind = case.expected_answer_kind
    if answer_kind == "income_structure" or source.startswith("wealth") or "income_structure" in tags:
        lanes.add("wealth_career_bridge")
        lanes.add("ten_god_mechanism")
    if source == "ten_god" or "ten_god" in tags:
        lanes.add("ten_god_mechanism")
    if source in {"branch_relation", "hidden_stem", "vault"} or case.expected_relation_types or {"branch_relation", "time_layer", "hidden_stem", "vault"} & tags:
        lanes.add("branch_time_activation")
    return sorted(lanes)


def _expected_graph_features(case: GuidedSyntheticCase) -> List[str]:
    features = {"branch", "hidden_stem", "stem"}
    tags = set(case.tags)
    source = case.expected_source_signal_category
    if source in {"ten_god", "wealth_feature"} or "ten_god" in tags or "income_structure" in tags:
        features.add("ten_god")
    if source in {"branch_relation", "vault"} or case.expected_relation_types or "branch_relation" in tags:
        features.add("branch_relation")
    if case.time_context or "time_layer" in tags:
        features.add("time_layer")
        if _has_time_relations(case.time_context):
            features.add("time_relation")
    return sorted(features)


def _condition_axes_expected(case: GuidedSyntheticCase) -> List[Dict[str, str]]:
    tags = set(case.tags)
    source_layer = "time_context" if case.time_context or "time_layer" in tags else "hidden_background" if case.expected_source_signal_category in {"hidden_stem", "vault"} else "natal_structure"
    same_layer_action = "branch_relation_path" if case.expected_relation_types or case.expected_source_signal_category == "branch_relation" else "metadata_or_domain_structure_path"
    if case.expected_answer_kind == "income_structure":
        same_layer_action = "wealth_structure_path"
    return [
        {"key": "source_layer", "expected": source_layer},
        {"key": "capacity_strength", "expected": "structural_capacity_hint_only"},
        {"key": "same_layer_action", "expected": same_layer_action},
        {"key": "rescue_path", "expected": "not_required_for_legacy_guided_collision"},
        {"key": "answer_boundary", "expected": "structure_only_no_prediction"},
        {"key": "time_layer", "expected": "trigger_context_only" if case.time_context or "time_layer" in tags else "natal_only"},
    ]


def _condition_axis_projection(case: GuidedSyntheticCase) -> Dict[str, str]:
    projection = {
        "source_layer": "condition_axis",
        "capacity_strength": "condition_axis",
        "same_layer_action": "condition_axis",
        "answer_boundary": "condition_axis",
    }
    if case.expected_relation_types or case.expected_source_signal_category == "branch_relation":
        projection["same_layer_action"] = "branch_relation_feature"
    if case.time_context or "time_layer" in set(case.tags):
        projection["time_layer"] = "time_relation_feature"
    return projection


def _has_time_relations(time_context: Dict[str, Any]) -> bool:
    for layer_name in ["luck_cycle", "flow_year"]:
        relations = (time_context.get(layer_name) or {}).get("relations_with_natal") or {}
        if any(relations.values()):
            return True
    return False


def _legacy_phase(case: GuidedSyntheticCase) -> str:
    if any(tag == "p11" for tag in case.tags):
        return "p11_synthetic_expansion"
    if any(tag == "p10" for tag in case.tags):
        return "p10_synthetic_collision_review"
    return "legacy_guided_synthetic"


def _missing(failure_type: str, expected: List[str], actual: List[str]) -> List[Dict[str, Any]]:
    actual_set = set(actual)
    return [_failure(failure_type, expected=item, actual=actual) for item in expected if item not in actual_set]


def _failure(failure_type: str, *, expected: Any, actual: Any) -> Dict[str, Any]:
    return {
        "failure_type": failure_type,
        "expected": expected,
        "actual": actual,
        "attribution_layer": "framework",
    }


def _matrix_row(phase: str, name: str, framework_track: str, adapter: str, status: str) -> Dict[str, str]:
    return {
        "phase": phase,
        "name": name,
        "framework_track": framework_track,
        "adapter": adapter,
        "status": status,
    }
