from __future__ import annotations

from typing import Any, Dict, List, Set

from v19.bazi_guided_questions import build_guided_question_answer
from v19.rule_graph_orchestrator import orchestrate_rule_graph_paths
from v19.synthetic_validation.domain_route_backfill import build_p61_domain_route_backfill_candidates
from v19.synthetic_validation.guided_cases import P11_GUIDED_SYNTHETIC_CASES
from v19.synthetic_validation.guided_runner import _agent_data_for_case
from v19.synthetic_validation.mainline_p1_safe_wrappers import build_p69_mainline_p1_safe_wrappers
from v19.synthetic_validation.rule_conversion_validation import build_p39_rule_conversion_candidates, run_p39_rule_conversion_regression


P65_MAINLINE_COMPLETION_AUDIT_VERSION = "v19.p65.mainline_completion_audit.v1"
P65_MAINLINE_COMPLETION_REGRESSION_VERSION = "v19.p65.mainline_completion_regression.v1"

P65_ROUTE_SPECS = [
    {
        "route_id": "income",
        "question_key": "q_income_stability",
        "message": "我的收入稳定性结构如何？",
        "answer_kind": "income_structure",
        "expected_answer_kind": "income_structure",
    },
    {
        "route_id": "career",
        "question_key": "",
        "message": "我的事业结构怎么看？",
        "answer_kind": "career_structure",
        "expected_answer_kind": "career_structure",
    },
    {
        "route_id": "relationship",
        "question_key": "",
        "message": "我的感情关系结构怎么看？",
        "answer_kind": "relationship_structure",
        "expected_answer_kind": "relationship_structure",
    },
    {
        "route_id": "health",
        "question_key": "",
        "message": "我的健康结构有什么需要注意的边界？",
        "answer_kind": "health_structure",
        "expected_answer_kind": "health_structure",
    },
    {
        "route_id": "time",
        "question_key": "q_time_context_boundary",
        "message": "这个流年只作为时间背景，会触发哪些结构关系？",
        "answer_kind": "time_boundary",
        "expected_answer_kind": "time_boundary",
    },
    {
        "route_id": "metadata",
        "question_key": "q_day_master_month_anchor",
        "message": "这张命盘先看日主和月令，能读出什么结构基点？",
        "answer_kind": "metadata_boundary",
        "expected_answer_kind": "metadata_boundary",
    },
]

P65_GUARDRAILS = [
    "P65_MAINLINE_COMPLETION_AUDIT",
    "AUDIT_ONLY",
    "NO_RUNTIME_RULE_ACTIVATION",
    "NO_RESULT_MUTATION",
    "NO_ANSWER_MUTATION",
    "NO_NEW_FRAMEWORK_EXPANSION",
    "PRIORITIZE_CORE_MEASUREMENT_CHAIN",
]


def build_p65_mainline_completion_audit() -> Dict[str, Any]:
    p39 = build_p39_rule_conversion_candidates()
    p61 = build_p61_domain_route_backfill_candidates()
    p69 = build_p69_mainline_p1_safe_wrappers()
    p39_candidates = [dict(row) for row in p39.get("candidates") or [] if isinstance(row, dict)]
    p61_candidates = [dict(row) for row in p61.get("candidates") or [] if isinstance(row, dict)]
    p69_candidates = [dict(row) for row in p69.get("candidates") or [] if isinstance(row, dict)]
    blocked = [dict(row) for row in p39.get("blocked") or [] if isinstance(row, dict)]
    all_candidates = p39_candidates + p61_candidates + p69_candidates
    safe_wrapped_ids = {str(row.get("knowledge_id") or "") for row in p61_candidates + p69_candidates if row.get("knowledge_id")}
    unwrapped_blocked = [row for row in blocked if str(row.get("knowledge_id") or "") not in safe_wrapped_ids]
    route_matrix = _route_selection_matrix(all_candidates)
    answer_surface = _answer_surface_matrix()
    selected_ids = {kid for row in route_matrix for kid in row.get("selected_knowledge_ids") or []}
    candidate_ids = {str(row.get("knowledge_id") or "") for row in all_candidates if row.get("knowledge_id")}
    never_selected = sorted(candidate_ids - selected_ids)
    answer_kind_gaps = [row for row in answer_surface if row.get("answer_kind_gap") is True]
    route_not_applied = [row for row in answer_surface if row.get("route_selected_not_applied_count", 0) > 0]
    priority_actions = _priority_actions(
        answer_kind_gaps=answer_kind_gaps,
        route_not_applied=route_not_applied,
        blocked=unwrapped_blocked,
        never_selected_ids=never_selected,
        candidates=all_candidates,
    )
    return {
        "ok": True,
        "version": P65_MAINLINE_COMPLETION_AUDIT_VERSION,
        "status": "mainline_completion_audit_ready",
        "runtime_scope": "audit_only_no_runtime_mutation",
        "summary": {
            "knowledge_draft_count": int((p39.get("summary") or {}).get("draft_count") or 0),
            "p39_candidate_count": len(p39_candidates),
            "p39_blocked_count": len(blocked),
            "p61_route_wrapper_count": len(p61_candidates),
            "p69_safe_wrapper_count": len(p69_candidates),
            "r3_r4_safe_wrapper_coverage_count": len({str(row.get("knowledge_id") or "") for row in blocked} & safe_wrapped_ids),
            "r3_r4_unwrapped_count": len(unwrapped_blocked),
            "rule_graph_candidate_count": len(all_candidates),
            "route_matrix_row_count": len(route_matrix),
            "route_selected_unique_count": len(selected_ids),
            "never_selected_candidate_count": len(never_selected),
            "answer_surface_row_count": len(answer_surface),
            "answer_kind_gap_count": len(answer_kind_gaps),
            "route_selected_not_applied_row_count": len(route_not_applied),
            "p0_action_count": sum(1 for row in priority_actions if row.get("priority") == "P0"),
            "p1_action_count": sum(1 for row in priority_actions if row.get("priority") == "P1"),
            "engine_enabled_count": 0,
            "answer_mutation_count": 0,
            "runtime_mutation": False,
        },
        "conversion_coverage": {
            "by_domain": _count_by(all_candidates, "domain"),
            "blocked_by_domain": _count_by(blocked, "domain"),
            "blocked_by_risk": _count_by(blocked, "risk_level"),
            "never_selected_by_domain": _count_never_selected_by_domain(never_selected, all_candidates),
        },
        "route_selection_matrix": route_matrix,
        "answer_surface_matrix": answer_surface,
        "priority_actions": priority_actions,
        "recommended_focus": [
            "Keep P62-P64 as framework standpoints only.",
            "Keep user-visible answer surface locked for income, career, relationship, health, time, and metadata routes.",
            "Keep Rule Graph selected knowledge bound into answer evidence before adding more framework layers.",
            "Use P39/P61 candidates as the active rule-candidate pool; do not expand GNN/RL now.",
        ],
        "guardrails": P65_GUARDRAILS,
    }


def run_p65_mainline_completion_regression() -> Dict[str, Any]:
    audit = build_p65_mainline_completion_audit()
    p39_regression = run_p39_rule_conversion_regression()
    failures: List[Dict[str, str]] = []
    summary = audit.get("summary") or {}
    if int(summary.get("rule_graph_candidate_count") or 0) < 300:
        failures.append(_failure("candidate_pool_too_small", "Rule Graph candidate pool should include P39 candidates and P61 wrappers."))
    if int(summary.get("answer_kind_gap_count") or 0) != 0:
        failures.append(_failure("answer_surface_gap_present", "Mainline answer routes should resolve to supported answer kinds."))
    if int(summary.get("route_selected_not_applied_row_count") or 0) != 0:
        failures.append(_failure("rule_graph_binding_gap_present", "Rule Graph selected knowledge should be bound into answer evidence."))
    if p39_regression.get("status") != "pass":
        failures.append(_failure("p39_regression_not_pass", "Mainline audit requires current rule conversion regression to pass."))
    if int(summary.get("engine_enabled_count") or 0) != 0 or int(summary.get("answer_mutation_count") or 0) != 0 or summary.get("runtime_mutation") is True:
        failures.append(_failure("mutation_not_allowed", "P65 is audit-only."))
    status = "pass" if not failures else "fail"
    return {
        "ok": status == "pass",
        "version": P65_MAINLINE_COMPLETION_REGRESSION_VERSION,
        "status": status,
        "runtime_scope": "mainline_completion_regression_no_runtime_mutation",
        "summary": {
            "rule_graph_candidate_count": int(summary.get("rule_graph_candidate_count") or 0),
            "answer_kind_gap_count": int(summary.get("answer_kind_gap_count") or 0),
            "route_selected_not_applied_row_count": int(summary.get("route_selected_not_applied_row_count") or 0),
            "p0_action_count": int(summary.get("p0_action_count") or 0),
            "p1_action_count": int(summary.get("p1_action_count") or 0),
            "failure_count": len(failures),
            "p39_regression_status": p39_regression.get("status"),
            "engine_enabled_count": 0,
            "answer_mutation_count": 0,
            "runtime_mutation": False,
        },
        "audit": audit,
        "failures": failures,
        "guardrails": P65_GUARDRAILS,
    }


def _route_selection_matrix(candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    candidate_by_id = {str(row.get("knowledge_id") or ""): row for row in candidates}
    rows: List[Dict[str, Any]] = []
    for case in P11_GUIDED_SYNTHETIC_CASES[:4]:
        agent_data = _agent_data_for_case(case)
        for spec in P65_ROUTE_SPECS:
            report = orchestrate_rule_graph_paths(
                agent_data,
                question_key=spec["question_key"],
                message=spec["message"],
                answer_kind=spec["answer_kind"],
                limit=8,
            )
            selected = [dict(row) for row in report.get("selected_paths") or [] if isinstance(row, dict)]
            selected_ids = [str(row.get("knowledge_id") or "") for row in selected if row.get("knowledge_id")]
            rows.append(
                {
                    "case_id": case.case_id,
                    "route_id": spec["route_id"],
                    "expected_intent": spec["answer_kind"],
                    "observed_intent": (report.get("question_intent") or {}).get("intent") or "",
                    "selected_count": len(selected),
                    "selected_knowledge_ids": selected_ids,
                    "selected_domains": sorted({str((candidate_by_id.get(kid) or {}).get("domain") or row.get("domain") or "") for kid, row in zip(selected_ids, selected)}),
                    "by_topic_lane": (report.get("summary") or {}).get("by_topic_lane") or {},
                    "answer_audit_status": (report.get("answer_audit") or {}).get("status") or "",
                    "engine_enabled_count": int((report.get("summary") or {}).get("engine_enabled_count") or 0),
                    "answer_mutation_count": int((report.get("summary") or {}).get("answer_mutation_count") or 0),
                }
            )
    return rows


def _answer_surface_matrix() -> List[Dict[str, Any]]:
    agent_data = _agent_data_for_case(P11_GUIDED_SYNTHETIC_CASES[0])
    rows = []
    for spec in P65_ROUTE_SPECS:
        answer = build_guided_question_answer(agent_data, spec["question_key"], spec["message"])
        retrieved = answer.get("retrieved_facts") or {}
        rule_graph = retrieved.get("rule_graph_context") or {}
        selected_ids = [str(item) for item in rule_graph.get("selected_knowledge_ids") or [] if str(item)]
        applied_ids = [str(row.get("knowledge_id") or "") for row in answer.get("applied_knowledge") or [] if row.get("knowledge_id")]
        not_applied = sorted(set(selected_ids) - set(applied_ids))
        observed = str(answer.get("answer_kind") or "")
        rows.append(
            {
                "route_id": spec["route_id"],
                "question_key": spec["question_key"],
                "expected_answer_kind": spec["expected_answer_kind"],
                "observed_answer_kind": observed,
                "answer_kind_gap": observed != spec["expected_answer_kind"],
                "supported": (answer.get("intent") or {}).get("supported") is not False,
                "unsupported_reason": (answer.get("intent") or {}).get("unsupported_reason") or "",
                "rule_graph_selected_knowledge_ids": selected_ids,
                "applied_knowledge_ids": applied_ids,
                "route_selected_not_applied_count": len(not_applied),
                "route_selected_not_applied_ids": not_applied[:8],
                "evidence_pack_status": (answer.get("evidence_pack") or {}).get("status") or "",
                "answer_audit_status": (answer.get("rule_graph_answer_audit") or {}).get("status") or "",
                "runtime_mutation": False,
            }
        )
    return rows


def _priority_actions(
    *,
    answer_kind_gaps: List[Dict[str, Any]],
    route_not_applied: List[Dict[str, Any]],
    blocked: List[Dict[str, Any]],
    never_selected_ids: List[str],
    candidates: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    actions: List[Dict[str, Any]] = []
    if answer_kind_gaps:
        actions.append(
            {
                "priority": "P0",
                "action_id": "p65.p0.answer_surface_domain_routes",
                "title": "补齐用户可见回答层的事业/关系/健康结构边界",
                "reason": "Rule Graph 已能选择领域路径，但 deterministic guided answer 仍缺少对应 answer_kind 或被 unsupported gate 拦截。",
                "affected_routes": [row["route_id"] for row in answer_kind_gaps],
                "next_step": "新增安全 answer_kind 与模板，只输出结构边界，不输出领域结论。",
            }
        )
    if route_not_applied:
        actions.append(
            {
                "priority": "P0",
                "action_id": "p65.p0.bind_rule_graph_to_answer_evidence",
                "title": "把 Rule Graph 选中的知识稳定绑定到回答证据层",
                "reason": "部分代表问题中，Rule Graph selected knowledge 未进入 applied_knowledge；用户回答可能看不到新增知识的影响。",
                "affected_routes": [row["route_id"] for row in route_not_applied],
                "next_step": "优先修 route-aware answer knowledge binding，再继续大规模扩知识。",
            }
        )
    if blocked:
        actions.append(
            {
                "priority": "P1",
                "action_id": "p65.p1.r3_r4_safe_wrapper_review",
                "title": "分专题处理 R3/R4 档案知识的安全转化",
                "reason": "高风险知识不能直接转规则，但可抽取 route-only / boundary-only wrapper。",
                "affected_domains": sorted(_count_by(blocked, "domain").keys())[:12],
                "blocked_count": len(blocked),
                "next_step": "按专题做安全降级包装，类似 P61 关系/健康路由包装。",
            }
        )
    if never_selected_ids:
        actions.append(
            {
                "priority": "P1",
                "action_id": "p65.p1.rule_graph_selection_coverage",
                "title": "提升候选规则在代表问题矩阵中的命中覆盖",
                "reason": "大量候选已转成规则合同，但代表问题矩阵未选中；需要补问题、调 scorer 或补合成样本。",
                "never_selected_count": len(never_selected_ids),
                "top_domains": _top_never_selected_domains(never_selected_ids, candidates),
                "next_step": "先按十神机制、格局、盲派、时间引动四组扩代表问题和合成验证。",
            }
        )
    actions.append(
        {
            "priority": "P2",
            "action_id": "p65.p2.freeze_new_framework_expansion",
            "title": "冻结 P62-P64 的继续扩展，只保留接口",
            "reason": "当前主线需要先修知识转规则和回答表面，不继续横向扩自学习、交互校准、GNN/RL。",
            "next_step": "P62-P64 只作为后续接口，不进入当前迭代主线。",
        }
    )
    return actions


def _top_never_selected_domains(knowledge_ids: List[str], candidates: List[Dict[str, Any]]) -> Dict[str, int]:
    by_id = {str(row.get("knowledge_id") or ""): row for row in candidates}
    rows = [by_id[kid] for kid in knowledge_ids if kid in by_id]
    counts = _count_by(rows, "domain")
    return dict(sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:10])


def _count_never_selected_by_domain(knowledge_ids: List[str], candidates: List[Dict[str, Any]]) -> Dict[str, int]:
    by_id = {str(row.get("knowledge_id") or ""): row for row in candidates}
    rows = [by_id[kid] for kid in knowledge_ids if kid in by_id]
    return _count_by(rows, "domain")


def _count_by(rows: List[Dict[str, Any]], key: str) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for row in rows:
        value = str(row.get(key) or "unknown")
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items(), key=lambda item: item[0]))


def _failure(failure_type: str, detail: str) -> Dict[str, str]:
    return {"failure_type": failure_type, "detail": detail}
