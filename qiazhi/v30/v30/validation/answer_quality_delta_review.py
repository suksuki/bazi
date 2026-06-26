from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

from v30.answer.composer import build_answer_context, compose_rule_bound_answer
from v30.contracts import AnswerResult, BaziQuestionAnchor
from v30.runtime import create_smoke_runtime


ANSWER_QUALITY_DELTA_REVIEW_VERSION = "v30.answer_quality_delta_review.v1"

CORE_DOMAIN_QUESTIONS: tuple[tuple[str, str], ...] = (
    ("career", "q_v30_user_career_direction"),
    ("wealth", "q_v30_user_wealth_tendency"),
    ("relationship", "q_v30_user_relationship_pattern"),
    ("timing", "q_v30_user_timing_pressure"),
    ("hidden_factor", "q_v30_hidden_factor_boundary_discovery"),
)

DOMAIN_REQUIRED_TOKENS: dict[str, tuple[str, ...]] = {
    "career": ("事业", "职责", "官", "印", "平台", "岗位", "资质"),
    "wealth": ("财", "财星", "财务", "财运", "现金流", "资源", "分配"),
    "relationship": ("关系", "互动", "边界", "官杀", "财星", "责任", "张力"),
    "timing": ("大运", "流年", "时运", "触发", "戊寅", "庚子", "时间"),
    "hidden_factor": ("年份", "反复", "隐藏", "状态", "反馈", "边界", "线索"),
}

MECHANISM_TOKENS = (
    "财官印",
    "官印相生",
    "食伤生财",
    "食伤制官杀",
    "比劫争财",
    "官杀",
    "印星",
    "财星",
    "结构路径",
    "动态",
)

EVIDENCE_LAYER_TOKENS = (
    "画像",
    "特征",
    "路径",
    "结构",
    "格局",
    "五行",
    "十神",
)

BOUNDARY_TOKENS = (
    "不把",
    "不直接",
    "不能",
    "只作为",
    "边界",
    "未确认",
    "不生成",
)

FORBIDDEN_GENERIC_TOKENS = (
    "旺衰、格局、用神综合参考",
    "需结合后续问答复核",
    "格局需结合时运观察",
    "用神需结合具体问题复核",
    "Current chart supports",
    "policy_effect",
    "raw_score",
    "feature_evidence_count",
)


def run_answer_quality_delta_review(*, reading_id: str = "core-evidence-2-answer-quality") -> dict[str, Any]:
    runtime = create_smoke_runtime(
        reading_id,
        day_master="庚",
        luck_pillar="戊寅",
        flow_year_pillar="庚子",
    )
    anchor_by_id = {anchor.question_id: anchor for anchor in runtime.question_anchors}
    answer_rows = []
    for domain, question_id in CORE_DOMAIN_QUESTIONS:
        anchor = anchor_by_id.get(question_id)
        if anchor is None:
            answer_rows.append(_missing_anchor_row(domain, question_id))
            continue
        answer = compose_rule_bound_answer(build_answer_context(runtime, anchor), runtime)
        answer_rows.append(_answer_quality_row(domain=domain, anchor=anchor, answer=answer))
    return build_answer_quality_delta_review(answer_rows=answer_rows, reading_id=reading_id)


def build_answer_quality_delta_review(
    *,
    answer_rows: Sequence[Mapping[str, Any]],
    reading_id: str = "core-evidence-2-answer-quality",
) -> dict[str, Any]:
    rows = [dict(row) for row in answer_rows]
    summary = _summary(rows)
    decision = _decision(summary, rows)
    return {
        "version": ANSWER_QUALITY_DELTA_REVIEW_VERSION,
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "status": "completed" if decision["answer_quality_delta_ready"] else "blocked",
        "reading_id": reading_id,
        "decision": decision,
        "quality_summary": summary,
        "answer_rows": rows,
        "core_scope": {
            "task_id": "CORE-EVIDENCE-2",
            "title": "Answer Quality Delta Review",
            "acceptance_target": (
                "customer-visible Bazi answers must carry domain-specific mechanisms, "
                "evidence layers, dynamic paths or portraits, and bounded chart facts"
            ),
            "covered_domains": [domain for domain, _ in CORE_DOMAIN_QUESTIONS],
            "required_layers": [
                "M1_M2_chart_time_context",
                "M3_features_portraits_paths_rules",
                "M4_ten_god_energy",
                "M5_ranked_decision_context",
                "M6_practical_answer_expression",
                "interaction_anchor",
            ],
        },
        "policy_boundary": {
            "full_pytest_run_by_default": False,
            "chart_fact_mutation_allowed": False,
            "llm_fact_mutation_allowed": False,
            "hidden_factor_question_visible_as_internal_term": False,
            "boundary": "core_evidence_2_is_read_only_answer_quality_review",
        },
        "next_mainline_selection": _next_selection(decision),
        "boundary": "answer_quality_delta_review_validates_text_quality_not_final_fortune_certainty",
    }


def _missing_anchor_row(domain: str, question_id: str) -> dict[str, Any]:
    return {
        "domain": domain,
        "question_id": question_id,
        "quality_ready": False,
        "answer_text": "",
        "answer_length": 0,
        "evidence_count": 0,
        "checks": {
            "question_anchor_present": False,
            "answer_has_customer_visible_text": False,
            "domain_specific_language_present": False,
            "bazi_mechanism_present": False,
            "evidence_layer_present": False,
            "boundary_language_present": False,
            "source_evidence_traceable": False,
            "generic_or_internal_filler_absent": True,
        },
        "failed_check_ids": ["question_anchor_present"],
    }


def _answer_quality_row(*, domain: str, anchor: BaziQuestionAnchor, answer: AnswerResult) -> dict[str, Any]:
    text = str(answer.text or "")
    checks = {
        "question_anchor_present": bool(anchor.question_id),
        "answer_has_customer_visible_text": len(text) >= 90,
        "domain_specific_language_present": _has_any(text, DOMAIN_REQUIRED_TOKENS[domain]),
        "bazi_mechanism_present": _has_any(text, MECHANISM_TOKENS),
        "evidence_layer_present": _has_any(text, EVIDENCE_LAYER_TOKENS),
        "boundary_language_present": _has_any(text, BOUNDARY_TOKENS),
        "source_evidence_traceable": len(answer.evidence_ids or []) >= 5,
        "generic_or_internal_filler_absent": not _has_any(text, FORBIDDEN_GENERIC_TOKENS),
    }
    failed = [check_id for check_id, passed in checks.items() if not passed]
    return {
        "domain": domain,
        "question_id": anchor.question_id,
        "intent_id": anchor.intent_id,
        "quality_ready": not failed,
        "answer_text": text,
        "answer_length": len(text),
        "evidence_count": len(answer.evidence_ids or []),
        "answer_source": answer.source,
        "answer_boundary": answer.boundary,
        "checks": checks,
        "failed_check_ids": failed,
        "matched_domain_tokens": _matched(text, DOMAIN_REQUIRED_TOKENS[domain]),
        "matched_mechanism_tokens": _matched(text, MECHANISM_TOKENS),
        "matched_evidence_layer_tokens": _matched(text, EVIDENCE_LAYER_TOKENS),
        "matched_boundary_tokens": _matched(text, BOUNDARY_TOKENS),
    }


def _summary(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    ready_rows = [row for row in rows if row.get("quality_ready") is True]
    domains = [str(row.get("domain") or "") for row in rows]
    failed = [str(row.get("question_id") or row.get("domain") or "") for row in rows if row.get("failed_check_ids")]
    return {
        "domain_count": len({domain for domain in domains if domain}),
        "answer_row_count": len(rows),
        "ready_answer_count": len(ready_rows),
        "failed_answer_count": len(rows) - len(ready_rows),
        "ready_ratio": round(len(ready_rows) / max(1, len(rows)), 3),
        "covered_domains": sorted(domain for domain in set(domains) if domain),
        "failed_question_ids": failed,
        "min_answer_length": min((int(row.get("answer_length", 0) or 0) for row in rows), default=0),
        "min_evidence_count": min((int(row.get("evidence_count", 0) or 0) for row in rows), default=0),
    }


def _decision(summary: Mapping[str, Any], rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    blockers: list[str] = []
    failed_rows = [row for row in rows if row.get("failed_check_ids")]
    required_domains = {domain for domain, _ in CORE_DOMAIN_QUESTIONS}
    covered_domains = set(summary.get("covered_domains", []))
    if not required_domains.issubset(covered_domains):
        blockers.append("core_answer_domain_coverage_incomplete")
    if failed_rows:
        blockers.append("answer_quality_rows_failed")
    if int(summary.get("min_evidence_count", 0) or 0) < 5:
        blockers.append("answer_evidence_trace_below_minimum")
    ready = not blockers
    return {
        "answer_quality_delta_ready": ready,
        "decision_status": "core_evidence_2_answer_quality_ready" if ready else "core_evidence_2_answer_quality_blocked",
        "check_count": len(rows) * 8,
        "passed_check_count": sum(1 for row in rows for passed in row.get("checks", {}).values() if passed),
        "failed_check_ids": sorted(
            {
                str(check_id)
                for row in rows
                for check_id in row.get("failed_check_ids", [])
                if check_id
            }
        ),
        "blockers": blockers,
        "full_pytest_required": False,
        "next_action": (
            "promote_core_evidence_2_and_continue_llm_prompt_context_delta"
            if ready
            else "harden_answer_expression_before_next_mainline_task"
        ),
    }


def _next_selection(decision: Mapping[str, Any]) -> dict[str, Any]:
    if decision.get("answer_quality_delta_ready") is True:
        return {
            "task_id": "CORE-EVIDENCE-3",
            "title": "LLM Prompt Context Delta Review",
            "rationale": "Answer quality gate is ready; next verify LLM context packs use module-specific context without prompt bloat.",
            "full_pytest_required_before_start": False,
        }
    return {
        "task_id": "CORE-EVIDENCE-2A",
        "title": "Focused Answer Expression Hardening",
        "rationale": "At least one core answer lacks domain-specific mechanism, evidence layer, boundary language, or traceable evidence.",
        "full_pytest_required_before_start": False,
    }


def _has_any(text: str, tokens: Sequence[str]) -> bool:
    return any(token in text for token in tokens)


def _matched(text: str, tokens: Sequence[str]) -> list[str]:
    return [token for token in tokens if token in text]
