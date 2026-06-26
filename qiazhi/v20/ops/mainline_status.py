from __future__ import annotations

from typing import Any

from v20.knowledge.completeness_audit import build_knowledge_completeness_audit
from v20.learning.answer_governance_training import build_answer_governance_training_report
from v20.ops.central_brain_architecture import build_central_brain_architecture_status
from v20.ops.runtime_consumption_audit import POINTER_FAMILIES


MAINLINE_STATUS_VERSION = "v20.mainline_status.v1"
KEY_NODE_MIN_SYNTHETIC_CASES = 3


def build_mainline_status() -> dict[str, object]:
    knowledge = build_knowledge_completeness_audit()
    answer_training = build_answer_governance_training_report(max_cases=1)
    central_brain = build_central_brain_architecture_status()
    knowledge_summary = _knowledge_summary(knowledge)
    answer_summary = _answer_governance_summary(answer_training)
    role_summary = _role_view_summary(answer_summary)
    runtime_summary = _runtime_consumption_summary()
    blockers = _blockers(
        knowledge_summary=knowledge_summary,
        answer_summary=answer_summary,
        role_summary=role_summary,
        runtime_summary=runtime_summary,
    )
    completion_percent = _completion_percent(blockers)
    return {
        "version": MAINLINE_STATUS_VERSION,
        "status": "continuous_iteration_ready" if not blockers else "needs_alignment",
        "completion_percent": completion_percent,
        "completion_label": "100%" if completion_percent >= 100 else f"{completion_percent}%",
        "principle": {
            "training_outputs_apply_directly": True,
            "no_human_review_gate_for_training": True,
            "observability_is_not_activation_gate": True,
            "rollback_is_version_pointer_based": True,
        },
        "knowledge": knowledge_summary,
        "central_brain_architecture": _central_brain_summary(central_brain),
        "llm_prompt_context_design": _llm_prompt_context_summary(central_brain),
        "answer_governance_training": answer_summary,
        "role_view": role_summary,
        "runtime_consumption": runtime_summary,
        "blockers": blockers,
        "next_actions": _next_actions(blockers),
        "runtime_mutation": False,
        "guardrails": [
            "MAINLINE_STATUS_OBSERVABILITY_ONLY",
            "NO_HUMAN_REVIEW_GATE_FOR_TRAINING",
            "TRAINING_OUTPUTS_APPLY_THROUGH_RUNTIME_POINTERS",
            "NO_RUNTIME_MUTATION_FROM_STATUS_REPORT",
        ],
    }


def _knowledge_summary(report: dict[str, object]) -> dict[str, object]:
    nodes = [row for row in report.get("node_audits", ()) if isinstance(row, dict)]
    key_nodes = {
        str(row.get("node_key")): {
            "label": str(row.get("label", "")),
            "rule_count": int(row.get("rule_count", 0) or 0),
            "runtime_allowed_count": int(row.get("runtime_allowed_count", 0) or 0),
            "synthetic_case_count": int(row.get("synthetic_case_count", 0) or 0),
            "counterexample_count": int(row.get("counterexample_count", 0) or 0),
        }
        for row in nodes
        if str(row.get("node_key", "")) in {"L7", "L8", "L12"}
    }
    return {
        "status": str(report.get("status", "")),
        "rule_count": int(report.get("rule_count", 0) or 0),
        "runtime_allowed_count": int(report.get("runtime_allowed_count", 0) or 0),
        "synthetic_case_count": int(report.get("synthetic_case_count", 0) or 0),
        "external_topic_covered_count": int(report.get("external_topic_covered_count", 0) or 0),
        "external_topic_count": int(report.get("external_topic_count", 0) or 0),
        "external_completeness_percent": int(report.get("external_completeness_percent", 0) or 0),
        "p0_gap_count": len(report.get("p0_gaps", ()) if isinstance(report.get("p0_gaps", ()), list | tuple) else ()),
        "key_nodes": key_nodes,
        "runtime_mutation": False,
    }


def _central_brain_summary(report: dict[str, object]) -> dict[str, object]:
    brain_graph = report.get("brain_graph", {}) if isinstance(report.get("brain_graph"), dict) else {}
    return {
        "status": str(report.get("status", "")),
        "completion_percent": int(report.get("completion_percent", 0) or 0),
        "architecture_doc": str(report.get("architecture_doc", "")),
        "module_count": len(report.get("modules", ()) if isinstance(report.get("modules", ()), list | tuple) else ()),
        "training_topic_count": len(
            report.get("training_topics", ()) if isinstance(report.get("training_topics", ()), list | tuple) else ()
        ),
        "brain_graph_node_count": len(
            brain_graph.get("nodes", ()) if isinstance(brain_graph.get("nodes", ()), list | tuple) else ()
        ),
        "ui_alignment_status": "required",
        "runtime_mutation": False,
    }


def _llm_prompt_context_summary(report: dict[str, object]) -> dict[str, object]:
    design = report.get("llm_prompt_context_design", {}) if isinstance(report.get("llm_prompt_context_design"), dict) else {}
    return {
        "status": str(design.get("status", "")),
        "completion_percent": int(design.get("completion_percent", 0) or 0),
        "design_doc": str(design.get("design_doc", "")),
        "prompt_policy": str(design.get("prompt_policy", "")),
        "context_layer_count": len(design.get("context_layers", ()) if isinstance(design.get("context_layers", ()), list | tuple) else ()),
        "runtime_consumer_count": len(
            design.get("runtime_consumers", ()) if isinstance(design.get("runtime_consumers", ()), list | tuple) else ()
        ),
        "retired_context_count": len(
            design.get("retired_context_paths", ()) if isinstance(design.get("retired_context_paths", ()), list | tuple) else ()
        ),
        "runtime_mutation": False,
    }


def _answer_governance_summary(report: dict[str, object]) -> dict[str, object]:
    targets = report.get("parameter_targets", {}) if isinstance(report.get("parameter_targets"), dict) else {}
    role_summary = (
        report.get("role_answer_governance_summary", {})
        if isinstance(report.get("role_answer_governance_summary"), dict)
        else {}
    )
    return {
        "status": str(report.get("status", "")),
        "case_count": int(report.get("case_count", 0) or 0),
        "average_quality_score": float(report.get("average_quality_score", 0.0) or 0.0),
        "weak_or_thin_case_count": int(report.get("weak_or_thin_case_count", 0) or 0),
        "answer_guidance_weight": float(targets.get("answer_guidance_weight", 0.0) or 0.0),
        "role_answer_governance_weight": float(targets.get("role_answer_governance_weight", 0.0) or 0.0),
        "prompt_context_budget_weight": float(targets.get("prompt_context_budget_weight", 0.0) or 0.0),
        "stream_answer_quality_weight": float(targets.get("stream_answer_quality_weight", 0.0) or 0.0),
        "stream_answer_quality_sample_count": int(
            (
                report.get("stream_answer_governance_summary", {})
                if isinstance(report.get("stream_answer_governance_summary", {}), dict)
                else {}
            ).get("sample_count", 0)
            or 0
        ),
        "role_average_quality_score": float(role_summary.get("average_quality_score", 0.0) or 0.0),
        "role_missing_profile_count": int(role_summary.get("missing_profile_count", 0) or 0),
        "direct_parameter_targets_ready": bool(
            float(targets.get("answer_guidance_weight", 0.0) or 0.0) > 0.0
            and float(targets.get("role_answer_governance_weight", 0.0) or 0.0) > 0.0
        ),
        "runtime_mutation": False,
    }


def _role_view_summary(answer_summary: dict[str, object]) -> dict[str, object]:
    direct_ready = bool(answer_summary.get("role_answer_governance_weight", 0.0) > 0.0)
    return {
        "pointer_family": "role_view",
        "pointer_consumer_status": "consumed",
        "runtime_allowed_when_artifact_written": direct_ready,
        "runtime_answer_governance_direct_path": direct_ready,
        "answer_governance_style_policy_target_roles": ("guest", "user", "analyst", "admin", "lab")
        if direct_ready
        else (),
        "direct_strategy_path_ready": direct_ready,
        "runtime_effect": "role_answer_governance_policy_direct_ready" if direct_ready else "baseline_role_view_policy_active",
        "blocking_gate": "" if direct_ready else "role_answer_governance_parameter_target_missing",
        "runtime_mutation": False,
    }


def _runtime_consumption_summary() -> dict[str, object]:
    rows = [row for row in POINTER_FAMILIES if isinstance(row, dict)]
    consumed = sum(1 for row in rows if row.get("runtime_consumer_status") == "consumed")
    return {
        "status": "complete" if consumed == len(rows) else "needs_runtime_consumers",
        "family_count": len(rows),
        "consumed_family_count": consumed,
        "consumption_percent": round(consumed / max(1, len(rows)) * 100),
        "families": tuple(
            {
                "family": str(row.get("family", "")),
                "label": str(row.get("label", "")),
                "runtime_consumer_status": str(row.get("runtime_consumer_status", "")),
                "expected_consumers": tuple(str(item) for item in row.get("expected_consumers", ()) if str(item)),
            }
            for row in rows
        ),
        "runtime_mutation": False,
    }


def _blockers(
    *,
    knowledge_summary: dict[str, object],
    answer_summary: dict[str, object],
    role_summary: dict[str, object],
    runtime_summary: dict[str, object],
) -> list[dict[str, object]]:
    blockers: list[dict[str, object]] = []
    if knowledge_summary.get("status") != "complete" or int(knowledge_summary.get("p0_gap_count", 0) or 0) > 0:
        blockers.append({"area": "knowledge", "reason": "p0_knowledge_gap_remaining"})
    for node_key, row in _dict(knowledge_summary.get("key_nodes")).items():
        if int(_dict(row).get("synthetic_case_count", 0) or 0) < KEY_NODE_MIN_SYNTHETIC_CASES:
            blockers.append(
                {
                    "area": "knowledge",
                    "reason": "key_node_synthetic_cases_too_few",
                    "node_key": node_key,
                    "required": KEY_NODE_MIN_SYNTHETIC_CASES,
                    "actual": int(_dict(row).get("synthetic_case_count", 0) or 0),
                }
            )
    if answer_summary.get("direct_parameter_targets_ready") is not True:
        blockers.append({"area": "answer_governance_training", "reason": "parameter_targets_not_ready"})
    if role_summary.get("direct_strategy_path_ready") is not True:
        blockers.append({"area": "role_view", "reason": "role_answer_governance_direct_path_not_ready"})
    if runtime_summary.get("status") != "complete":
        blockers.append({"area": "runtime_consumption", "reason": "runtime_pointer_consumer_missing"})
    return blockers


def _completion_percent(blockers: list[dict[str, object]]) -> int:
    if not blockers:
        return 100
    return max(80, 99 - len(blockers) * 3)


def _next_actions(blockers: list[dict[str, object]]) -> list[dict[str, object]]:
    if blockers:
        return [
            {
                "area": str(row.get("area", "")),
                "action": str(row.get("reason", "")),
                "activation_policy": "fix_machine_path_then_apply_directly",
            }
            for row in blockers
        ]
    return [
        {
            "area": "continuous_iteration",
            "action": "new_training_tasks_must_emit_parameter_targets_and_connect_runtime_pointers",
            "activation_policy": "direct_apply_without_human_review_gate",
        },
        {
            "area": "knowledge_growth",
            "action": "new_bazi_topics_must_include_rules_counterexamples_synthetic_cases_answer_guidance",
            "activation_policy": "status_report_observes_only",
        },
    ]


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}
