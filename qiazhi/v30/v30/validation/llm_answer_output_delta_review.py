from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

from v30.llm.acceptance import bazi_llm_output_text, validate_bazi_llm_output_payload
from v30.llm.prompt_registry import build_bazi_llm_prompt_request
from v30.runtime import attach_question_outcome, create_smoke_runtime


LLM_ANSWER_OUTPUT_DELTA_REVIEW_VERSION = "v30.llm_answer_output_delta_review.v1"


def run_llm_answer_output_delta_review(
    *,
    reading_id: str = "core-evidence-4-llm-answer-output",
) -> dict[str, Any]:
    runtime = create_smoke_runtime(
        reading_id,
        day_master="庚",
        luck_pillar="戊寅",
        flow_year_pillar="庚子",
    )
    followup = attach_question_outcome(
        runtime,
        runtime.question_anchors[0].question_id,
        {"answer": "事业方向", "selected_option": "career", "confidence": 0.8},
    )
    requests = {
        "customer_initial_reading": build_bazi_llm_prompt_request(
            runtime,
            task_type="customer_initial_reading",
            role_key="user",
        ),
        "domain_followup": build_bazi_llm_prompt_request(
            followup,
            task_type="domain_followup",
            domain="career",
            role_key="user",
        ),
        "hidden_factor_dialogue": build_bazi_llm_prompt_request(
            followup,
            task_type="hidden_factor_dialogue",
            role_key="user",
        ),
        "practitioner_analysis": build_bazi_llm_prompt_request(
            runtime,
            task_type="practitioner_analysis",
            role_key="practitioner",
        ),
    }
    rows = [
        _accepted_row(
            "customer_initial_reading_quality",
            requests["customer_initial_reading"],
            {
                "answer_text": (
                    "庚日主的命盘先看官杀压力能否被印星承接，事业和时运判断落在官印相生路径上。"
                    "当前只沿已验证结构、画像和候选路径说明，不新增年份或固定结论。"
                ),
                "evidence_ids": ["evidence-1"],
                "boundaries": ["rule_bound_answer_no_llm_fact_mutation"],
                "next_question_hint": "继续确认一个近期反复出现的状态。",
            },
        ),
        _accepted_row(
            "domain_followup_quality",
            requests["domain_followup"],
            {
                "domain": "career",
                "answer_text": (
                    "事业追问以庚日主的官杀压力和印星承接为核心，重点看职责、资质和平台能否形成官印相生路径。"
                    "这里使用已知反馈和结构特征说明，不新增年份或固定结论。"
                ),
                "used_user_signals": ["career"],
                "boundaries": ["rule_bound_answer_no_llm_fact_mutation"],
            },
        ),
        _accepted_row(
            "hidden_factor_dialogue_quality",
            requests["hidden_factor_dialogue"],
            {
                "dialogue_text": "请从给出的年份或反复状态选项里确认一个最明显的反馈点；如果不确定，可以选择暂不确认。",
                "probe_target": "event_year_or_repeated_state",
                "confirmed_feedback_only": True,
                "boundaries": ["hidden_factor_feedback_is_dialogue_signal_not_chart_fact"],
            },
        ),
        _accepted_row(
            "practitioner_analysis_quality",
            requests["practitioner_analysis"],
            {
                "analysis_text": (
                    "命理师侧看庚日主的官杀压力、印星承接和财星资源转换，核心证据落在M3结构路径、M4十神信号和M5候选决策。"
                    "事业可按官印相生复盘职责与资质承接，仍不把单一反馈年份提升为定论。"
                ),
                "module_evidence": ["M3", "M4", "M5", "M6"],
                "candidate_boundaries": ["ranked_decisions_are_candidate_scores_not_fixed_verdicts"],
                "diagnostics_used": ["structure_dynamics", "model_signals"],
            },
        ),
        _rejected_row(
            "generic_customer_output_rejected",
            requests["customer_initial_reading"],
            {
                "answer_text": "当前回答只按已验证的趋势边界说明，后续需要结合问题继续观察。",
                "evidence_ids": ["evidence-1"],
                "boundaries": ["rule_bound_answer_no_llm_fact_mutation"],
                "next_question_hint": "继续确认问题。",
            },
            expected_failure="missing_bazi_mechanism_language",
        ),
    ]
    return build_llm_answer_output_delta_review(acceptance_rows=rows, reading_id=reading_id)


def build_llm_answer_output_delta_review(
    *,
    acceptance_rows: Sequence[Mapping[str, Any]],
    reading_id: str = "core-evidence-4-llm-answer-output",
) -> dict[str, Any]:
    rows = [dict(row) for row in acceptance_rows]
    summary = _summary(rows)
    decision = _decision(summary, rows)
    return {
        "version": LLM_ANSWER_OUTPUT_DELTA_REVIEW_VERSION,
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "status": "completed" if decision["llm_answer_output_delta_ready"] else "blocked",
        "reading_id": reading_id,
        "decision": decision,
        "quality_summary": summary,
        "acceptance_rows": rows,
        "core_scope": {
            "task_id": "CORE-EVIDENCE-4",
            "title": "LLM Answer Output Delta Review",
            "acceptance_target": (
                "LLM accepted output must contain concrete Bazi mechanism language, role/domain expression, "
                "schema fields, evidence/boundaries, and no customer-visible system leakage"
            ),
        },
        "policy_boundary": {
            "live_llm_execution_performed": False,
            "chart_fact_mutation_allowed": False,
            "full_pytest_run_by_default": False,
            "boundary": "core_evidence_4_validates_output_acceptance_without_live_provider",
        },
        "next_mainline_selection": _next_selection(decision),
        "boundary": "llm_answer_output_delta_review_keeps_llm_as_expression_over_verified_bazi_context",
    }


def _accepted_row(row_id: str, prompt_request: Mapping[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    task_type = str(prompt_request.get("task_type") or "")
    text = bazi_llm_output_text(payload, task_type)
    acceptance = validate_bazi_llm_output_payload(
        payload,
        prompt_request=dict(prompt_request),
        text=text,
        drift_check={"passed": True, "failures": []},
    )
    checks = {
        "output_was_accepted": acceptance.get("accepted") is True,
        "schema_fields_present": not acceptance.get("missing_fields"),
        "role_visibility_passed": acceptance.get("role_visibility_passed") is True,
        "content_quality_passed": acceptance.get("content_quality_passed") is True,
        "drift_passed": acceptance.get("drift_passed") is True,
        "chart_fact_mutation_blocked": acceptance.get("chart_fact_mutation_allowed") is False,
    }
    return _row(row_id, task_type, text, acceptance, checks)


def _rejected_row(
    row_id: str,
    prompt_request: Mapping[str, Any],
    payload: dict[str, Any],
    *,
    expected_failure: str,
) -> dict[str, Any]:
    task_type = str(prompt_request.get("task_type") or "")
    text = bazi_llm_output_text(payload, task_type)
    acceptance = validate_bazi_llm_output_payload(
        payload,
        prompt_request=dict(prompt_request),
        text=text,
        drift_check={"passed": True, "failures": []},
    )
    content_failures = [str(row) for row in acceptance.get("content_failures", [])]
    checks = {
        "output_was_rejected": acceptance.get("accepted") is False,
        "expected_content_failure_present": expected_failure in content_failures,
        "schema_would_otherwise_pass": not acceptance.get("missing_fields"),
        "role_visibility_would_otherwise_pass": acceptance.get("role_visibility_passed") is True,
        "chart_fact_mutation_blocked": acceptance.get("chart_fact_mutation_allowed") is False,
    }
    return _row(row_id, task_type, text, acceptance, checks)


def _row(
    row_id: str,
    task_type: str,
    text: str,
    acceptance: Mapping[str, Any],
    checks: Mapping[str, bool],
) -> dict[str, Any]:
    failed = [check_id for check_id, passed in checks.items() if not passed]
    return {
        "row_id": row_id,
        "task_type": task_type,
        "quality_ready": not failed,
        "accepted": acceptance.get("accepted"),
        "answer_text": text,
        "answer_length": len(text),
        "schema_id": acceptance.get("schema_id", ""),
        "checks": dict(checks),
        "failed_check_ids": failed,
        "content_failures": acceptance.get("content_failures", []),
        "role_failures": acceptance.get("role_failures", []),
        "missing_fields": acceptance.get("missing_fields", []),
        "boundary": acceptance.get("boundary", ""),
    }


def _summary(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    ready_rows = [row for row in rows if row.get("quality_ready") is True]
    return {
        "row_count": len(rows),
        "ready_row_count": len(ready_rows),
        "failed_row_count": len(rows) - len(ready_rows),
        "accepted_quality_rows": sum(1 for row in rows if row.get("accepted") is True and row.get("quality_ready") is True),
        "rejection_quality_rows": sum(1 for row in rows if row.get("accepted") is False and row.get("quality_ready") is True),
        "task_types": sorted({str(row.get("task_type") or "") for row in rows}),
    }


def _decision(summary: Mapping[str, Any], rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    failed_rows = [row for row in rows if row.get("failed_check_ids")]
    blockers: list[str] = []
    if failed_rows:
        blockers.append("llm_answer_output_delta_rows_failed")
    if int(summary.get("accepted_quality_rows", 0) or 0) < 4:
        blockers.append("accepted_output_quality_coverage_below_minimum")
    if int(summary.get("rejection_quality_rows", 0) or 0) < 1:
        blockers.append("generic_output_rejection_missing")
    ready = not blockers
    return {
        "llm_answer_output_delta_ready": ready,
        "decision_status": "core_evidence_4_llm_answer_output_ready"
        if ready
        else "core_evidence_4_llm_answer_output_blocked",
        "check_count": sum(len(_dict(row.get("checks"))) for row in rows),
        "passed_check_count": sum(1 for row in rows for passed in _dict(row.get("checks")).values() if passed),
        "failed_check_ids": sorted(
            {
                str(check_id)
                for row in rows
                for check_id in _list(row.get("failed_check_ids"))
                if check_id
            }
        ),
        "blockers": blockers,
        "live_llm_execution_performed": False,
        "full_pytest_required": False,
        "next_action": "continue_to_core_answer_runtime_integration_review"
        if ready
        else "harden_llm_output_acceptance_quality_gate",
    }


def _next_selection(decision: Mapping[str, Any]) -> dict[str, Any]:
    if decision.get("llm_answer_output_delta_ready") is True:
        return {
            "task_id": "CORE-EVIDENCE-5",
            "title": "Runtime Answer Integration Delta Review",
            "rationale": "LLM output quality gate is ready; next verify runtime answer panels use the strengthened output/fallback path end to end.",
            "full_pytest_required_before_start": False,
        }
    return {
        "task_id": "CORE-EVIDENCE-4A",
        "title": "LLM Output Quality Hardening",
        "rationale": "One or more accepted/rejected output rows failed the content quality contract.",
        "full_pytest_required_before_start": False,
    }


def _dict(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list(value: object) -> list[Any]:
    return value if isinstance(value, list) else []
