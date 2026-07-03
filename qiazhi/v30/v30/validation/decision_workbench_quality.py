from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from v30.brain.practitioner_interaction import build_practitioner_interaction_state
from v30.contracts import CoreRuntimeResult
from v30.presentation.client_model import build_presentation_model
from v30.presentation.thinking import build_thinking_projection


DECISION_WORKBENCH_QUALITY_AUDIT_VERSION = "v30.decision_workbench_quality_audit.v1"


def build_decision_workbench_quality_audit(
    runtime: CoreRuntimeResult,
    *,
    locale: str = "zh",
    client: str = "admin",
) -> dict[str, object]:
    thinking = build_thinking_projection(runtime)
    user_view = build_presentation_model(runtime, role_key="user", locale=locale, client="web").model_dump(mode="json")
    practitioner_view = build_presentation_model(
        runtime,
        role_key="practitioner",
        locale=locale,
        client="web",
    ).model_dump(mode="json")
    admin_view = build_presentation_model(runtime, role_key="admin", locale=locale, client=client).model_dump(mode="json")
    practitioner_state = build_practitioner_interaction_state(runtime.reading_id, thinking, role_key="practitioner")

    user_surface = _dict(user_view.get("reading_surface"))
    practitioner_surface = _dict(practitioner_view.get("reading_surface"))
    admin_surface = _dict(admin_view.get("reading_surface"))
    user_workbench = _dict(user_surface.get("decision_workbench"))
    practitioner_workbench = _dict(practitioner_surface.get("decision_workbench"))
    admin_workbench = _dict(admin_surface.get("decision_workbench"))
    user_legacy_dialogue_surface = _dict(user_surface.get("legacy_dialogue_surface"))
    user_calibration_surface = _dict(user_surface.get("calibration_surface"))
    user_conversation_surface = _dict(user_surface.get("conversation_surface"))
    diagnostic_legacy_payload = _dict(_dict(practitioner_surface.get("legacy_dialogue_surface")).get("payload"))
    journey_steps = _list(thinking.get("journey_steps"))
    material_steps = _list(thinking.get("steps"))
    branch_step = _find_step(journey_steps, "journey_branch_calibration")
    verdict_step = _find_step(journey_steps, "journey_decision_verdicts")
    final_step = _find_step(journey_steps, "journey_final_expression")
    branch_option_sets = _stage_option_sets(branch_step)
    practitioner_option_sets = _list(practitioner_state.get("option_sets"))
    central = _dict(runtime.question_plan.policy_effect.get("central_reading_state"))
    decision_result = _dict(central.get("decision_result"))
    final_synthesis = _dict(central.get("final_synthesis"))
    current_turn = _dict(diagnostic_legacy_payload.get("current_dialogue_turn"))

    summary = _summary(
        runtime,
        thinking=thinking,
        user_workbench=user_workbench,
        practitioner_workbench=practitioner_workbench,
        admin_workbench=admin_workbench,
        branch_option_sets=branch_option_sets,
        practitioner_option_sets=practitioner_option_sets,
        current_turn=current_turn,
        material_steps=material_steps,
        decision_result=decision_result,
        final_synthesis=final_synthesis,
        surface_final_synthesis=_dict(user_surface.get("final_synthesis")),
        user_legacy_dialogue_surface=user_legacy_dialogue_surface,
        user_calibration_surface=user_calibration_surface,
        user_conversation_surface=user_conversation_surface,
    )
    checks = _quality_checks(
        summary,
        user_view=user_view,
        user_workbench=user_workbench,
        practitioner_workbench=practitioner_workbench,
        admin_workbench=admin_workbench,
        branch_step=branch_step,
        verdict_step=verdict_step,
        final_step=final_step,
        current_turn=current_turn,
    )
    scores = _quality_scores(summary, checks)
    failed = [row for row in checks if not row["passed"]]
    error_failed = [row for row in failed if row["severity"] == "error"]

    return {
        "version": DECISION_WORKBENCH_QUALITY_AUDIT_VERSION,
        "reading_id": runtime.reading_id,
        "trace_id": runtime.trace_id,
        "status": "ready" if not error_failed else "needs_attention",
        "summary": summary,
        "quality_scores": scores,
        "checks": checks,
        "admin_diff_rows": _admin_diff_rows(summary, scores),
        "decision": {
            "decision_workbench_quality_ready": not error_failed,
            "decision_status": "dca17_decision_workbench_quality_ready"
            if not error_failed else "dca17_decision_workbench_quality_needs_attention",
            "check_count": len(checks),
            "passed_count": len(checks) - len(failed),
            "failed_check_ids": [str(row["check_id"]) for row in failed],
            "next_task_id": "DCA-18-real-case-replay-gate" if not error_failed else "DCA-17-quality-followup",
            "full_pytest_required": False,
            "synthetic_all_required": False,
            "chart_fact_mutation_allowed": False,
            "policy_pointer_write_allowed": False,
        },
        "product_boundary": {
            "llm_role": "expression_and_dialogue_language_only",
            "decision_authority": "DecisionEngineVerdict",
            "brain_role": "orchestrates_evidence_weight_feedback_and_quality_gates",
            "customer_dialogue_entry": "reading_surface.conversation_surface",
            "calibration_entry": "reading_surface.calibration_surface",
            "legacy_customer_dialogue_entry": "reading_surface.current_dialogue_turn",
            "legacy_customer_dialogue_entry_status": "diagnostic_compatibility_only",
            "chart_fact_mutation_allowed": False,
            "boundary": "quality_audit_observes_output_orchestration_without_mutating_runtime",
        },
        "boundary": "decision_workbench_quality_audit_is_read_only_admin_observability",
    }


def _summary(
    runtime: CoreRuntimeResult,
    *,
    thinking: Mapping[str, Any],
    user_workbench: Mapping[str, Any],
    practitioner_workbench: Mapping[str, Any],
    admin_workbench: Mapping[str, Any],
    branch_option_sets: list[dict[str, Any]],
    practitioner_option_sets: list[Any],
    current_turn: Mapping[str, Any],
    material_steps: list[Any],
    decision_result: Mapping[str, Any],
    final_synthesis: Mapping[str, Any],
    surface_final_synthesis: Mapping[str, Any],
    user_legacy_dialogue_surface: Mapping[str, Any],
    user_calibration_surface: Mapping[str, Any],
    user_conversation_surface: Mapping[str, Any],
) -> dict[str, object]:
    user_summary = _dict(user_workbench.get("summary"))
    admin_summary = _dict(admin_workbench.get("summary"))
    journey_steps = _list(thinking.get("journey_steps"))
    branch_option_set_count = len(branch_option_sets)
    practitioner_option_set_count = len([row for row in practitioner_option_sets if isinstance(row, dict)])
    journey_policy_rows = [
        _dict(row.get("summary_policy"))
        for row in journey_steps
        if isinstance(row, dict)
    ]
    not_required_count = sum(1 for row in journey_policy_rows if row.get("llm_enhancement") == "not_required")
    current_question = _dict(current_turn.get("question"))
    visible_probe_cards = _list(user_calibration_surface.get("visible_probe_cards"))
    suggested_question = _dict(user_conversation_surface.get("suggested_question"))
    direct_legacy_fields_exposed = (
        bool(user_legacy_dialogue_surface.get("direct_fields_exposed"))
        or bool(user_legacy_dialogue_surface.get("payload"))
    )
    return {
        "reading_id": runtime.reading_id,
        "journey_step_count": len(journey_steps),
        "material_step_count": len(material_steps),
        "uses_seven_step_journey": len(journey_steps) == 7,
        "journey_llm_not_required_count": not_required_count,
        "journey_llm_policy_count": len(journey_policy_rows),
        "verdict_count": _int(user_summary.get("verdict_count") or admin_summary.get("verdict_count")),
        "visible_verdict_count": _int(user_summary.get("visible_verdict_count")),
        "conflict_count": _int(user_summary.get("conflict_count") or admin_summary.get("conflict_count")),
        "branch_option_set_count": branch_option_set_count,
        "practitioner_option_set_count": practitioner_option_set_count,
        "workbench_status": str(user_workbench.get("status") or admin_workbench.get("status") or ""),
        "user_training_signal_visible": "training_signal" in user_workbench,
        "practitioner_training_signal_visible": "training_signal" in practitioner_workbench,
        "admin_training_signal_visible": "training_signal" in admin_workbench,
        "score_mutation_allowed": bool(user_summary.get("score_mutation_allowed")),
        "verdict_mutation_allowed": bool(user_summary.get("verdict_mutation_allowed")),
        "decision_engine_mutation_allowed": bool(decision_result.get("score_mutation_allowed")),
        "final_synthesis_status": str(final_synthesis.get("status") or ""),
        "final_synthesis_uses_verdicts": bool(final_synthesis.get("decision_focus"))
        or bool(final_synthesis.get("action_steps"))
        or bool(surface_final_synthesis.get("decision_focus"))
        or bool(surface_final_synthesis.get("action_steps")),
        "dialogue_action": str(current_turn.get("action") or ""),
        "dialogue_question_id": str(current_question.get("question_id") or ""),
        "dialogue_source": str(current_turn.get("decision_source") or ""),
        "customer_visible_question_count": len(visible_probe_cards) + (1 if suggested_question.get("question_id") else 0),
        "customer_direct_legacy_fields_exposed": direct_legacy_fields_exposed,
        "calibration_surface_ready": bool(user_calibration_surface),
        "conversation_surface_ready": bool(user_conversation_surface),
        "legacy_dialogue_surface_status": str(user_legacy_dialogue_surface.get("status") or ""),
        "chart_fact_mutation_allowed": False,
    }


def _quality_checks(
    summary: Mapping[str, Any],
    *,
    user_view: Mapping[str, Any],
    user_workbench: Mapping[str, Any],
    practitioner_workbench: Mapping[str, Any],
    admin_workbench: Mapping[str, Any],
    branch_step: Mapping[str, Any],
    verdict_step: Mapping[str, Any],
    final_step: Mapping[str, Any],
    current_turn: Mapping[str, Any],
) -> list[dict[str, object]]:
    projection_contract = _dict(user_view.get("projection_contract"))
    leak_scan = _dict(projection_contract.get("leak_scan"))
    checks = [
        _check(
            "seven_step_journey_active",
            bool(summary.get("uses_seven_step_journey")),
            "error",
            "测算流程必须是 7 个高层阶段，不能回退到旧 11/13 步解释流。",
            {"journey_step_count": summary.get("journey_step_count")},
        ),
        _check(
            "journey_pages_do_not_require_llm",
            _int(summary.get("journey_llm_not_required_count")) == _int(summary.get("journey_llm_policy_count")) == 7,
            "error",
            "步骤页只沉淀素材和裁决入口，默认不调用 LLM 长文解释。",
            {
                "not_required": summary.get("journey_llm_not_required_count"),
                "policy_count": summary.get("journey_llm_policy_count"),
            },
        ),
        _check(
            "decision_workbench_output_bound",
            str(summary.get("workbench_status") or "") == "ready" and _int(summary.get("verdict_count")) > 0,
            "error",
            "Decision Workbench 必须消费 Verdict，并把断语变成用户结果。",
            {"verdict_count": summary.get("verdict_count"), "workbench_status": summary.get("workbench_status")},
        ),
        _check(
            "conflict_cards_have_calibration_entry",
            _int(summary.get("conflict_count")) == 0 or _int(summary.get("branch_option_set_count")) > 0,
            "error",
            "存在分支冲突时，必须给命理师校准入口，而不是强行吞掉分支。",
            {"conflict_count": summary.get("conflict_count"), "branch_option_set_count": summary.get("branch_option_set_count")},
        ),
        _check(
            "practitioner_options_cover_branch_workbench",
            _int(summary.get("practitioner_option_set_count")) >= _int(summary.get("branch_option_set_count")),
            "warning",
            "命理师可交互选项应覆盖分支冲突页。",
            {
                "branch_option_set_count": summary.get("branch_option_set_count"),
                "practitioner_option_set_count": summary.get("practitioner_option_set_count"),
            },
        ),
        _check(
            "customer_training_signal_hidden",
            not bool(summary.get("user_training_signal_visible")),
            "error",
            "普通用户不能看到训练信号、候选权重或工程调参字段。",
            {"user_training_signal_visible": summary.get("user_training_signal_visible")},
        ),
        _check(
            "diagnostic_training_signal_visible",
            bool(summary.get("practitioner_training_signal_visible")) and bool(summary.get("admin_training_signal_visible")),
            "warning",
            "命理师/Admin 需要看到可训练投影，用于校准和回放。",
            {
                "practitioner": summary.get("practitioner_training_signal_visible"),
                "admin": summary.get("admin_training_signal_visible"),
            },
        ),
        _check(
            "customer_projection_leak_scan_passed",
            bool(leak_scan.get("passed")),
            "error",
            "普通用户投影不能泄漏内部诊断字段。",
            {"leak_scan": leak_scan},
        ),
        _check(
            "dialogue_is_separate_surface_route",
            bool(summary.get("calibration_surface_ready"))
            and bool(summary.get("conversation_surface_ready"))
            and not bool(summary.get("customer_direct_legacy_fields_exposed"))
            and _int(summary.get("customer_visible_question_count")) <= 1,
            "error",
            "智能对话必须通过 conversation_surface / calibration_surface 独立挂载，不能混进步骤导航或直接暴露 legacy turn。",
            {
                "dialogue_source": summary.get("dialogue_source"),
                "visible_question_count": summary.get("customer_visible_question_count"),
                "legacy_status": summary.get("legacy_dialogue_surface_status"),
                "customer_direct_legacy_fields_exposed": summary.get("customer_direct_legacy_fields_exposed"),
            },
        ),
        _check(
            "no_score_or_verdict_mutation",
            not bool(summary.get("score_mutation_allowed"))
            and not bool(summary.get("verdict_mutation_allowed"))
            and not bool(summary.get("decision_engine_mutation_allowed")),
            "error",
            "质量审计和 UI 投影不能修改 Decision score 或 Verdict。",
            {
                "score_mutation_allowed": summary.get("score_mutation_allowed"),
                "verdict_mutation_allowed": summary.get("verdict_mutation_allowed"),
                "decision_engine_mutation_allowed": summary.get("decision_engine_mutation_allowed"),
            },
        ),
        _check(
            "final_expression_consumes_verdicts",
            bool(summary.get("final_synthesis_uses_verdicts")) and str(summary.get("final_synthesis_status") or ""),
            "warning",
            "最终表达应该消费 Decision Verdict，再交给 LLM 做用户语言。",
            {
                "final_synthesis_status": summary.get("final_synthesis_status"),
                "uses_verdicts": summary.get("final_synthesis_uses_verdicts"),
            },
        ),
        _check(
            "journey_stage_ids_present",
            bool(branch_step) and bool(verdict_step) and bool(final_step),
            "error",
            "7 阶段必须包含分支校准、裁决和最终表达三个产品阶段。",
            {
                "branch_step": bool(branch_step),
                "verdict_step": bool(verdict_step),
                "final_step": bool(final_step),
            },
        ),
    ]
    checks.append(
        _check(
            "chart_fact_mutation_blocked",
            user_workbench.get("boundary") and admin_workbench.get("boundary"),
            "error",
            "Workbench 只能是用户产出投影，不是命盘事实来源。",
            {
                "user_boundary": user_workbench.get("boundary"),
                "admin_boundary": admin_workbench.get("boundary"),
            },
        )
    )
    return checks


def _quality_scores(summary: Mapping[str, Any], checks: list[dict[str, object]]) -> dict[str, object]:
    error_checks = [row for row in checks if row["severity"] == "error"]
    warning_checks = [row for row in checks if row["severity"] == "warning"]
    error_passed = sum(1 for row in error_checks if row["passed"])
    warning_passed = sum(1 for row in warning_checks if row["passed"])
    output_bound_score = 1.0 if _int(summary.get("verdict_count")) > 0 and summary.get("workbench_status") == "ready" else 0.0
    calibration_score = 1.0 if _int(summary.get("conflict_count")) == 0 or _int(summary.get("branch_option_set_count")) > 0 else 0.0
    role_boundary_score = 1.0 if not summary.get("user_training_signal_visible") else 0.0
    journey_score = 1.0 if summary.get("uses_seven_step_journey") else 0.0
    check_score = round((error_passed * 1.0 + warning_passed * 0.5) / max(1.0, len(error_checks) + len(warning_checks) * 0.5), 3)
    overall = round(
        output_bound_score * 0.24
        + calibration_score * 0.18
        + role_boundary_score * 0.20
        + journey_score * 0.18
        + check_score * 0.20,
        3,
    )
    return {
        "version": "v30.decision_workbench_quality_scores.v1",
        "overall_score": overall,
        "output_bound_score": round(output_bound_score, 3),
        "calibration_score": round(calibration_score, 3),
        "role_boundary_score": round(role_boundary_score, 3),
        "journey_score": round(journey_score, 3),
        "check_score": check_score,
        "error_passed_count": error_passed,
        "error_check_count": len(error_checks),
        "warning_passed_count": warning_passed,
        "warning_check_count": len(warning_checks),
        "chart_fact_mutation_allowed": False,
        "boundary": "quality_scores_rank_observability_only_without_changing_decision_policy",
    }


def _admin_diff_rows(summary: Mapping[str, Any], scores: Mapping[str, Any]) -> list[dict[str, object]]:
    rows = [
        _diff_row("journey_step_count", summary.get("journey_step_count"), 7, "eq", "7 阶段产品流程"),
        _diff_row("verdict_count", summary.get("verdict_count"), 5, "gte", "裁决卡进入用户结果"),
        _diff_row("visible_verdict_count", summary.get("visible_verdict_count"), 3, "gte", "普通用户可读裁决数量"),
        _diff_row("branch_option_set_count", summary.get("branch_option_set_count"), 1, "gte", "冲突校准入口"),
        _diff_row("practitioner_option_set_count", summary.get("practitioner_option_set_count"), 1, "gte", "命理师交互入口"),
        _diff_row("overall_score", scores.get("overall_score"), 0.9, "gte", "质量总分"),
    ]
    if _int(summary.get("conflict_count")) == 0:
        rows = [row for row in rows if row["metric"] != "branch_option_set_count"]
    return rows


def _diff_row(metric: str, current: object, target: object, comparator: str, label: str) -> dict[str, object]:
    current_value = _float(current)
    target_value = _float(target)
    if comparator == "eq":
        passed = current_value == target_value
    else:
        passed = current_value >= target_value
    return {
        "metric": metric,
        "label": label,
        "current": current,
        "target": target,
        "delta": round(current_value - target_value, 3),
        "judgement": "ready" if passed else "needs_attention",
        "comparator": comparator,
        "boundary": "admin_quality_diff_is_observability_baseline_not_policy_pointer",
    }


def _check(
    check_id: str,
    passed: bool,
    severity: str,
    message: str,
    details: Mapping[str, Any] | None = None,
) -> dict[str, object]:
    return {
        "check_id": check_id,
        "passed": bool(passed),
        "severity": severity,
        "message": message,
        "details": dict(details or {}),
    }


def _find_step(steps: list[Any], step_id: str) -> dict[str, Any]:
    for step in steps:
        if isinstance(step, Mapping) and step.get("step_id") == step_id:
            return dict(step)
    return {}


def _stage_option_sets(step: Mapping[str, Any]) -> list[dict[str, Any]]:
    point_set = _dict(step.get("stage_point_set"))
    return [dict(row) for row in _list(point_set.get("option_sets")) if isinstance(row, Mapping)]


def _dict(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _list(value: object) -> list[Any]:
    return list(value) if isinstance(value, list) else []


def _int(value: object) -> int:
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 0


def _float(value: object) -> float:
    try:
        return round(float(value), 3)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 0.0
