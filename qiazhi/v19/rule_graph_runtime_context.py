from __future__ import annotations

from typing import Any, Dict, List

from v19.rule_graph_orchestrator import audit_selected_paths_for_answer, infer_question_intent, orchestrate_rule_graph_paths


RULE_GRAPH_RUNTIME_CONTEXT_VERSION = "v19.p47.rule_graph_runtime_context.v1"


def build_rule_graph_runtime_context(
    agent_data: Dict[str, Any],
    *,
    message: str = "",
    selected_question_key: str = "",
    limit: int = 10,
) -> Dict[str, Any]:
    chart = dict(agent_data.get("chart") or {})
    if not chart:
        return {
            "ok": False,
            "version": RULE_GRAPH_RUNTIME_CONTEXT_VERSION,
            "status": "chart_unavailable",
            "runtime_scope": "measurement_route_pack_no_result_mutation",
            "guardrails": ["RULE_GRAPH_RUNTIME_CONTEXT", "NO_RESULT_MUTATION"],
        }

    routes = _route_requests(message=message, selected_question_key=selected_question_key)
    route_reports = []
    for route in routes:
        report = orchestrate_rule_graph_paths(
            agent_data,
            question_key=route["question_key"],
            message=route["message"],
            answer_kind=route["answer_kind"],
            limit=limit,
        )
        route_reports.append(_compact_route_report(route, report))

    selected_paths = _merge_selected_paths(route_reports, limit=limit + 4)
    answer_audit = audit_selected_paths_for_answer(selected_paths)
    return {
        "ok": True,
        "version": RULE_GRAPH_RUNTIME_CONTEXT_VERSION,
        "status": "rule_graph_runtime_context_ready",
        "runtime_scope": "measurement_route_pack_no_result_mutation",
        "route_count": len(route_reports),
        "routes": route_reports,
        "selected_paths": selected_paths,
        "knowledge_route": {
            "selected_knowledge_ids": [str(row.get("knowledge_id") or "") for row in selected_paths if row.get("knowledge_id")],
            "selected_rule_ids": [str(row.get("candidate_rule_id") or "") for row in selected_paths if row.get("candidate_rule_id")],
            "by_topic_lane": _count_by(selected_paths, "topic_lane"),
            "by_domain": _count_by(selected_paths, "domain"),
            "prompt_context": rule_graph_runtime_context_to_prompt_context(
                {
                    "version": RULE_GRAPH_RUNTIME_CONTEXT_VERSION,
                    "status": "rule_graph_runtime_context_ready",
                    "routes": route_reports,
                    "selected_paths": selected_paths,
                }
            ),
        },
        "summary": {
            "candidate_count": max([int(row.get("candidate_count") or 0) for row in route_reports] or [0]),
            "route_selected_total": sum(int(row.get("selected_count") or 0) for row in route_reports),
            "selected_path_count": len(selected_paths),
            "canary_internal_count": sum(1 for row in selected_paths if row.get("framework_state") == "canary_isolated_passed"),
            "runtime_allowed_count": sum(1 for row in selected_paths if row.get("runtime_allowed") is True),
            "engine_enabled_count": 0,
            "answer_mutation_count": 0,
            "runtime_mutation": False,
        },
        "answer_audit": answer_audit,
        "integration_points": [
            "agent_turn.structured.rule_graph_runtime_context",
            "guided_question_context.rule_graph_context",
            "guided_question_answer.retrieved_facts.rule_graph_context",
            "llm.compact.rule_graph_runtime_context",
        ],
        "future_model_slots": {
            "gnn": "reserved_for_route_rerank_after_eval_labels_exist",
            "rl": "reserved_for_question_ordering_not_core_rule_truth",
            "current": "deterministic_rule_graph_runtime_route_pack",
        },
        "guardrails": [
            "RULE_GRAPH_RUNTIME_CONTEXT",
            "PATH_SELECTION_ONLY",
            "NO_RUNTIME_RULE_ACTIVATION",
            "NO_RESULT_MUTATION",
            "NO_ANSWER_MUTATION",
            "NO_BLACK_BOX_CORE_INFERENCE",
        ],
    }


def rule_graph_runtime_context_to_prompt_context(runtime_context: Dict[str, Any], *, limit: int = 8) -> Dict[str, Any]:
    selected_paths = [dict(row) for row in runtime_context.get("selected_paths") or [] if isinstance(row, dict)]
    routes = [dict(row) for row in runtime_context.get("routes") or [] if isinstance(row, dict)]
    return {
        "version": RULE_GRAPH_RUNTIME_CONTEXT_VERSION,
        "status": runtime_context.get("status") or "",
        "runtime_scope": "llm_context_route_hints_only_no_answer_mutation",
        "selected_knowledge_ids": [str(row.get("knowledge_id") or "") for row in selected_paths[:limit] if row.get("knowledge_id")],
        "route_plan": [
            {
                "route_id": row.get("route_id") or "",
                "intent": row.get("intent") or "",
                "selected_knowledge_ids": list(row.get("selected_knowledge_ids") or [])[:4],
                "by_topic_lane": dict(row.get("by_topic_lane") or {}),
            }
            for row in routes[:4]
        ],
        "evidence_bindings": [
            {
                "knowledge_id": row.get("knowledge_id") or "",
                "title": row.get("title") or "",
                "domain": row.get("domain") or "",
                "topic_lane": row.get("topic_lane") or "",
                "framework_state": row.get("framework_state") or "",
                "runtime_allowed": row.get("runtime_allowed") is True,
                "reason": row.get("reason") or "",
                "answer_boundary": "structure_evidence_only_not_prediction",
            }
            for row in selected_paths[:limit]
        ],
        "guardrails": [
            "USE_AS_ROUTE_HINTS_ONLY",
            "DO_NOT_OUTPUT_INTERNAL_IDS_UNLESS_EXPLAINING_AUDIT",
            "NO_FORTUNE",
            "NO_RESULT_MUTATION",
        ],
    }


def _route_requests(*, message: str, selected_question_key: str) -> List[Dict[str, str]]:
    primary = infer_question_intent(selected_question_key, message, "")
    routes = [
        {
            "route_id": "primary_question_route",
            "question_key": selected_question_key,
            "message": message,
            "answer_kind": str(primary.get("intent") or "structure_overview"),
        },
        {
            "route_id": "income_structure_route",
            "question_key": "q_income_stability",
            "message": "我的收入稳定性结构如何？",
            "answer_kind": "income_structure",
        },
        {
            "route_id": "structure_overview_route",
            "question_key": "q_structure_overview",
            "message": "如果只看结构，这张命盘先呈现哪些特征？",
            "answer_kind": "structure_overview",
        },
    ]
    return routes


def _compact_route_report(route: Dict[str, str], report: Dict[str, Any]) -> Dict[str, Any]:
    selected = [dict(row) for row in report.get("selected_paths") or [] if isinstance(row, dict)]
    return {
        "route_id": route.get("route_id") or "",
        "question_key": route.get("question_key") or "",
        "intent": (report.get("question_intent") or {}).get("intent") or route.get("answer_kind") or "",
        "candidate_count": (report.get("summary") or {}).get("candidate_count") or 0,
        "selected_count": len(selected),
        "selected_path_ids": [str(row.get("path_id") or "") for row in selected if row.get("path_id")],
        "selected_knowledge_ids": [str(row.get("knowledge_id") or "") for row in selected if row.get("knowledge_id")],
        "by_topic_lane": _count_by(selected, "topic_lane"),
        "answer_audit_status": (report.get("answer_audit") or {}).get("status") or "",
        "runtime_scope": "route_selection_only_no_result_mutation",
        "selected_paths": selected,
    }


def _merge_selected_paths(route_reports: List[Dict[str, Any]], *, limit: int) -> List[Dict[str, Any]]:
    selected: List[Dict[str, Any]] = []
    seen: set[str] = set()
    for report in route_reports:
        route_id = str(report.get("route_id") or "")
        for path in report.get("selected_paths") or []:
            if not isinstance(path, dict):
                continue
            key = str(path.get("knowledge_id") or path.get("path_id") or "")
            if not key or key in seen:
                continue
            row = dict(path)
            row["selected_by_route"] = route_id
            selected.append(row)
            seen.add(key)
            if len(selected) >= limit:
                return selected
    return selected


def _count_by(rows: List[Dict[str, Any]], key: str) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for row in rows:
        value = str(row.get(key) or "unknown")
        counts[value] = counts.get(value, 0) + 1
    return counts
