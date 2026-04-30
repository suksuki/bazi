from __future__ import annotations

from typing import Any, Dict, List


GUIDED_EVIDENCE_PACK_VERSION = "v19.p50.guided_answer_evidence_pack.v1"


def build_guided_answer_evidence_pack(
    *,
    question_key: str,
    question_text: str,
    answer_kind: str,
    intent: Dict[str, Any],
    source_signal: Dict[str, Any],
    retrieved_facts: Dict[str, Any],
    applied_knowledge: List[Dict[str, Any]],
    knowledge_context: Dict[str, Any],
    rule_graph_context: Dict[str, Any],
    rule_graph_runtime_context: Dict[str, Any],
) -> Dict[str, Any]:
    applied = [dict(row) for row in applied_knowledge if isinstance(row, dict)]
    answer_paths = [dict(row) for row in rule_graph_context.get("selected_paths") or [] if isinstance(row, dict)]
    runtime_paths = [dict(row) for row in rule_graph_runtime_context.get("selected_paths") or [] if isinstance(row, dict)]
    bindings = _evidence_bindings(applied, answer_paths, runtime_paths)
    fact_summary = _fact_summary(retrieved_facts)
    return {
        "ok": True,
        "version": GUIDED_EVIDENCE_PACK_VERSION,
        "status": "ready",
        "runtime_scope": "guided_answer_evidence_pack_context_only_no_mutation",
        "question": {
            "question_key": question_key,
            "question_text": question_text,
            "answer_kind": answer_kind,
            "intent_id": intent.get("intent_id") or "",
            "supported": intent.get("supported") is not False,
            "source_signal_id": source_signal.get("signal_id") or "",
            "source_signal_category": source_signal.get("category") or "",
        },
        "fact_evidence": fact_summary,
        "knowledge_evidence": {
            "mode": knowledge_context.get("mode") or "",
            "retrieved_count": len(knowledge_context.get("items") or []),
            "applied_count": len(applied),
            "applied_ids": [str(row.get("knowledge_id") or "") for row in applied if row.get("knowledge_id")],
            "route_context_status": (knowledge_context.get("route_context") or {}).get("status") or "",
            "items": [
                {
                    "knowledge_id": row.get("knowledge_id") or "",
                    "domain": row.get("domain") or "",
                    "title": row.get("title") or "",
                    "match_score": row.get("match_score"),
                    "route_match_score": row.get("route_match_score"),
                    "route_match_reasons": list(row.get("route_match_reasons") or []),
                }
                for row in applied
            ],
        },
        "rule_graph_evidence": {
            "answer_graph_status": rule_graph_context.get("status") or "",
            "answer_graph_audit_status": (rule_graph_context.get("answer_audit") or {}).get("status") or "",
            "answer_graph_selected_knowledge_ids": [str(row.get("knowledge_id") or "") for row in answer_paths if row.get("knowledge_id")],
            "runtime_graph_status": rule_graph_runtime_context.get("status") or "",
            "runtime_graph_audit_status": (rule_graph_runtime_context.get("answer_audit") or {}).get("status") or "",
            "runtime_selected_knowledge_ids": list((rule_graph_runtime_context.get("knowledge_route") or {}).get("selected_knowledge_ids") or [])[:12],
            "runtime_selected_rule_ids": list((rule_graph_runtime_context.get("knowledge_route") or {}).get("selected_rule_ids") or [])[:12],
        },
        "evidence_bindings": bindings,
        "summary": {
            "fact_scope_count": len(fact_summary.get("present_fact_scopes") or []),
            "knowledge_binding_count": sum(1 for row in bindings if row.get("kind") == "knowledge"),
            "rule_graph_binding_count": sum(1 for row in bindings if row.get("kind") == "rule_graph_path"),
            "engine_enabled_count": 0,
            "answer_mutation_count": 0,
            "runtime_mutation": False,
        },
        "audit": {
            "status": "pass",
            "checks": [
                {"name": "facts_present", "passed": bool(fact_summary.get("present_fact_scopes")), "note": "Evidence pack includes retrieved fact scopes."},
                {"name": "answer_mutation_disabled", "passed": True, "note": "Evidence pack is context only."},
                {"name": "rule_activation_disabled", "passed": True, "note": "Evidence pack does not activate rules."},
            ],
        },
        "guardrails": [
            "GUIDED_ANSWER_EVIDENCE_PACK",
            "FACTS_KNOWLEDGE_RULE_GRAPH_UNIFIED",
            "CONTEXT_ONLY_NO_RESULT_MUTATION",
            "NO_RUNTIME_RULE_ACTIVATION",
            "NO_ANSWER_MUTATION",
            "NO_DOMAIN_RESULT_PREDICTION",
        ],
    }


def evidence_pack_to_prompt_context(evidence_pack: Dict[str, Any], *, limit: int = 8) -> Dict[str, Any]:
    bindings = [dict(row) for row in evidence_pack.get("evidence_bindings") or [] if isinstance(row, dict)]
    return {
        "version": GUIDED_EVIDENCE_PACK_VERSION,
        "status": evidence_pack.get("status") or "",
        "runtime_scope": "llm_prompt_evidence_pack_context_only",
        "question": dict(evidence_pack.get("question") or {}),
        "fact_evidence": dict(evidence_pack.get("fact_evidence") or {}),
        "bindings": [
            {
                "kind": row.get("kind") or "",
                "id": row.get("id") or "",
                "title": row.get("title") or "",
                "domain": row.get("domain") or "",
                "reason": row.get("reason") or "",
                "answer_boundary": row.get("answer_boundary") or "structure_evidence_only_not_prediction",
            }
            for row in bindings[:limit]
        ],
        "guardrails": [
            "USE_EVIDENCE_PACK_ONLY",
            "DO_NOT_OUTPUT_INTERNAL_IDS_UNLESS_ASKED_FOR_AUDIT",
            "NO_FORTUNE",
            "NO_RESULT_MUTATION",
        ],
    }


def evidence_pack_summary(evidence_pack: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "version": evidence_pack.get("version") or GUIDED_EVIDENCE_PACK_VERSION,
        "status": evidence_pack.get("status") or "",
        "runtime_scope": evidence_pack.get("runtime_scope") or "",
        "knowledge_ids": list((evidence_pack.get("knowledge_evidence") or {}).get("applied_ids") or []),
        "runtime_selected_knowledge_ids": list((evidence_pack.get("rule_graph_evidence") or {}).get("runtime_selected_knowledge_ids") or [])[:8],
        "binding_count": len(evidence_pack.get("evidence_bindings") or []),
        "audit_status": (evidence_pack.get("audit") or {}).get("status") or "",
        "answer_mutation_count": (evidence_pack.get("summary") or {}).get("answer_mutation_count", 0),
        "runtime_mutation": (evidence_pack.get("summary") or {}).get("runtime_mutation", False),
    }


def _fact_summary(retrieved_facts: Dict[str, Any]) -> Dict[str, Any]:
    present = []
    for key in ["chart_anchor", "relations", "vaults", "hidden_stems", "time_context", "income_signals", "source_signal"]:
        value = retrieved_facts.get(key)
        if value:
            present.append(key)
    return {
        "present_fact_scopes": present,
        "relation_count": len(retrieved_facts.get("relations") or []),
        "vault_count": len(retrieved_facts.get("vaults") or []),
        "income_signal_keys": sorted(str(key) for key in (retrieved_facts.get("income_signals") or {}).keys()),
        "time_context_scope": (retrieved_facts.get("time_context") or {}).get("scope") or "",
        "guardrails": ["FACTS_ARE_INPUTS_NOT_PREDICTIONS"],
    }


def _evidence_bindings(
    applied_knowledge: List[Dict[str, Any]],
    answer_paths: List[Dict[str, Any]],
    runtime_paths: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    bindings: List[Dict[str, Any]] = []
    seen = set()
    for row in applied_knowledge:
        knowledge_id = str(row.get("knowledge_id") or "")
        if not knowledge_id or ("knowledge", knowledge_id) in seen:
            continue
        seen.add(("knowledge", knowledge_id))
        bindings.append(
            {
                "kind": "knowledge",
                "id": knowledge_id,
                "title": row.get("title") or "",
                "domain": row.get("domain") or "",
                "match_score": row.get("match_score"),
                "route_match_score": row.get("route_match_score"),
                "reason": ", ".join(str(item) for item in row.get("route_match_reasons") or [] if str(item)),
                "answer_boundary": "knowledge_evidence_template_only_not_prediction",
            }
        )
    for row in answer_paths + runtime_paths:
        path_id = str(row.get("path_id") or row.get("knowledge_id") or "")
        if not path_id or ("rule_graph_path", path_id) in seen:
            continue
        seen.add(("rule_graph_path", path_id))
        bindings.append(
            {
                "kind": "rule_graph_path",
                "id": path_id,
                "knowledge_id": row.get("knowledge_id") or "",
                "rule_id": row.get("candidate_rule_id") or "",
                "title": row.get("title") or "",
                "domain": row.get("domain") or "",
                "topic_lane": row.get("topic_lane") or "",
                "framework_state": row.get("framework_state") or "",
                "runtime_allowed": row.get("runtime_allowed") is True,
                "reason": row.get("reason") or "",
                "answer_boundary": "rule_graph_route_only_not_prediction",
            }
        )
    return bindings[:24]
