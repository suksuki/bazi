from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

from v30.answer.composer import build_answer_context, compose_rule_bound_answer
from v30.runtime import create_smoke_runtime


SYNTHETIC_TYPICAL_BAZI_ANSWER_CALIBRATION_VERSION = "v30.synthetic_typical_bazi_answer_calibration.v1"

TYPICAL_ANSWER_CASES: tuple[dict[str, Any], ...] = (
    {
        "case_id": "core_cal_s1.metal_career_official_resource",
        "label": "庚金事业官印相生",
        "day_master": "庚",
        "day_master_element": "metal",
        "question_id": "q_v30_user_career_direction",
        "expected_domain_tokens": {"事业", "职责", "资质", "平台"},
        "expected_mechanism_tokens": {"官杀", "印星", "官印相生"},
    },
    {
        "case_id": "core_cal_s1.metal_wealth_finance_path",
        "label": "庚金财务财官印路径",
        "day_master": "庚",
        "day_master_element": "metal",
        "question_id": "q_v30_user_wealth_tendency",
        "expected_domain_tokens": {"财运", "财星", "资源", "分配"},
        "expected_mechanism_tokens": {"财官印", "财星", "印星"},
    },
    {
        "case_id": "core_cal_s1.metal_relationship_boundary",
        "label": "庚金关系官印边界",
        "day_master": "庚",
        "day_master_element": "metal",
        "question_id": "q_v30_user_relationship_pattern",
        "expected_domain_tokens": {"关系", "互动", "边界", "责任"},
        "expected_mechanism_tokens": {"官杀", "印星", "官印相生"},
    },
    {
        "case_id": "core_cal_s1.water_timing_trigger",
        "label": "壬水时运触发",
        "day_master": "壬",
        "day_master_element": "water",
        "question_id": "q_v30_user_timing_pressure",
        "expected_domain_tokens": {"时运", "戊寅", "庚子", "触发"},
        "expected_mechanism_tokens": {"官印相生", "结构路径"},
    },
    {
        "case_id": "core_cal_s1.hidden_attribute_feedback",
        "label": "隐藏属性反馈边界",
        "day_master": "庚",
        "day_master_element": "metal",
        "question_id": "q_v30_hidden_factor_boundary_discovery",
        "expected_domain_tokens": {"背景校准", "反复状态", "特殊年份", "放大线索"},
        "expected_mechanism_tokens": {"藏干", "反馈", "命局事实"},
    },
)

FORBIDDEN_TEXT_TOKENS = (
    "Use domain language",
    "life-result prediction",
    "该画像维度由规则",
    "v30.",
    "policy_effect",
    "raw_score",
    "prompt_contract_id",
    "context_pack_id",
    "llm_bazi_answer_draft",
    "LLM accepted",
    "证据数=",
)


def run_synthetic_typical_bazi_answer_calibration() -> dict[str, Any]:
    rows = []
    for spec in TYPICAL_ANSWER_CASES:
        runtime = create_smoke_runtime(
            str(spec["case_id"]),
            day_master=str(spec["day_master"]),
            day_master_element=str(spec["day_master_element"]),
            luck_pillar="戊寅",
            flow_year_pillar="庚子",
        )
        anchor_by_id = {anchor.question_id: anchor for anchor in runtime.question_anchors}
        anchor = anchor_by_id.get(str(spec["question_id"]))
        answer = compose_rule_bound_answer(build_answer_context(runtime, anchor), runtime) if anchor else None
        rows.append(_case_row(spec, answer.model_dump(mode="json") if answer else {}))
    return build_synthetic_typical_bazi_answer_calibration(case_rows=rows)


def build_synthetic_typical_bazi_answer_calibration(
    *,
    case_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    rows = [_review_row(row) for row in case_rows]
    summary = _summary(rows)
    decision = _decision(summary, rows)
    return {
        "version": SYNTHETIC_TYPICAL_BAZI_ANSWER_CALIBRATION_VERSION,
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "status": "completed" if decision["synthetic_typical_answer_calibration_ready"] else "blocked",
        "task": {
            "task_id": "CORE-CAL-S1",
            "title": "Synthetic Typical Bazi Answer Calibration Pack",
            "scope": "calibrate_customer_answer_text_against_synthetic_representative_bazi_patterns",
        },
        "case_count": len(rows),
        "case_reviews": rows,
        "calibration_summary": summary,
        "decision": decision,
        "calibration_queue": _calibration_queue(rows),
        "policy_boundary": {
            "real_person_truth_label_allowed": False,
            "chart_fact_mutation_allowed": False,
            "policy_pointer_promotion_allowed": False,
            "full_pytest_required": False,
            "synthetic_all_required": False,
            "full_518k_required": False,
            "live_llm_required": False,
            "boundary": "core_cal_s1_uses_synthetic_patterns_to_calibrate_answer_text_only",
        },
        "next_mainline_selection": _next_selection(decision),
        "boundary": "synthetic_typical_answer_calibration_does_not_claim_real_life_truth",
    }


def _case_row(spec: Mapping[str, Any], answer: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "case_id": str(spec.get("case_id") or ""),
        "label": str(spec.get("label") or ""),
        "day_master": str(spec.get("day_master") or ""),
        "question_id": str(spec.get("question_id") or ""),
        "expected_domain_tokens": sorted(str(row) for row in spec.get("expected_domain_tokens", set())),
        "expected_mechanism_tokens": sorted(str(row) for row in spec.get("expected_mechanism_tokens", set())),
        "answer": dict(answer),
    }


def _review_row(row: Mapping[str, Any]) -> dict[str, Any]:
    answer = _mapping(row.get("answer"))
    text = str(answer.get("text") or "")
    expected_domain = set(_str_list(row.get("expected_domain_tokens")))
    expected_mechanisms = set(_str_list(row.get("expected_mechanism_tokens")))
    matched_domain = {token for token in expected_domain if token in text}
    matched_mechanisms = {token for token in expected_mechanisms if token in text}
    checks = {
        "answer_present": bool(text),
        "answer_mentions_day_master_or_chart": str(row.get("day_master") or "") in text and ("日主" in text or "命盘" in text),
        "domain_tokens_covered": expected_domain <= matched_domain,
        "mechanism_tokens_covered": expected_mechanisms <= matched_mechanisms,
        "boundary_language_present": any(token in text for token in ("不把", "不能", "只作为", "未确认", "不新增", "不改写")),
        "evidence_trace_present": len(answer.get("evidence_ids", []) if isinstance(answer.get("evidence_ids"), list) else []) >= 5,
        "no_internal_or_english_leak": not any(token in text for token in FORBIDDEN_TEXT_TOKENS),
        "answer_boundary_non_mutating": answer.get("boundary") == "rule_bound_answer_no_llm_fact_mutation",
    }
    failed = [check_id for check_id, passed in checks.items() if not passed]
    return {
        "case_id": str(row.get("case_id") or ""),
        "label": str(row.get("label") or ""),
        "question_id": str(row.get("question_id") or ""),
        "passed": not failed,
        "failed_check_ids": failed,
        "checks": checks,
        "answer_text": text,
        "matched_domain_tokens": sorted(matched_domain),
        "matched_mechanism_tokens": sorted(matched_mechanisms),
        "expected_domain_tokens": sorted(expected_domain),
        "expected_mechanism_tokens": sorted(expected_mechanisms),
        "calibration_target_modules": _target_modules(failed),
        "boundary": "typical_answer_case_checks_text_quality_not_real_life_truth",
    }


def _summary(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    passed_rows = [row for row in rows if row.get("passed") is True]
    target_modules: dict[str, int] = {}
    for row in rows:
        for module in _str_list(row.get("calibration_target_modules")):
            target_modules[module] = target_modules.get(module, 0) + 1
    return {
        "case_count": len(rows),
        "passed_case_count": len(passed_rows),
        "failed_case_count": len(rows) - len(passed_rows),
        "coverage_domains": sorted({str(row.get("question_id") or "") for row in rows}),
        "calibration_target_modules": target_modules,
    }


def _decision(summary: Mapping[str, Any], rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    failed_rows = [row for row in rows if row.get("passed") is not True]
    blockers: list[str] = []
    if int(summary.get("case_count", 0) or 0) < 5:
        blockers.append("typical_answer_case_count_below_minimum")
    if failed_rows:
        blockers.append("typical_answer_cases_failed")
    ready = not blockers
    return {
        "synthetic_typical_answer_calibration_ready": ready,
        "decision_status": "core_cal_s1_synthetic_typical_answer_calibration_ready"
        if ready
        else "core_cal_s1_synthetic_typical_answer_calibration_blocked",
        "case_count": int(summary.get("case_count", 0) or 0),
        "passed_case_count": int(summary.get("passed_case_count", 0) or 0),
        "failed_case_count": int(summary.get("failed_case_count", 0) or 0),
        "failed_case_ids": [str(row.get("case_id") or "") for row in failed_rows],
        "failed_check_ids": sorted(
            {
                str(check_id)
                for row in failed_rows
                for check_id in _str_list(row.get("failed_check_ids"))
                if check_id
            }
        ),
        "blockers": blockers,
        "full_pytest_required": False,
        "synthetic_all_required": False,
        "full_518k_required": False,
        "live_llm_required": False,
        "next_action": "register_typical_answer_synthetic_tier" if ready else "repair_answer_text_calibration_failures",
    }


def _calibration_queue(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    queue = []
    for row in rows:
        if row.get("passed") is True:
            continue
        queue.append(
            {
                "case_id": row.get("case_id"),
                "failed_check_ids": row.get("failed_check_ids", []),
                "target_modules": row.get("calibration_target_modules", []),
                "chart_fact_mutation_allowed": False,
                "boundary": "calibration_queue_item_targets_answer_expression_not_chart_facts",
            }
        )
    return queue


def _target_modules(failed: Sequence[str]) -> list[str]:
    modules = []
    for check_id in failed:
        if check_id in {"domain_tokens_covered", "mechanism_tokens_covered", "boundary_language_present"}:
            modules.append("M6_answer_expression")
        elif check_id == "no_internal_or_english_leak":
            modules.append("M3_guidance_or_presentation_sanitization")
        elif check_id == "evidence_trace_present":
            modules.append("M3_M5_evidence_trace")
        else:
            modules.append("runtime_answer_composer")
    return sorted(set(modules))


def _next_selection(decision: Mapping[str, Any]) -> dict[str, Any]:
    if decision.get("synthetic_typical_answer_calibration_ready") is True:
        return {
            "task_id": "CORE-CAL-S2",
            "title": "Synthetic Typical Answer Tier Registration And Training Signals",
            "rationale": "Typical answer calibration cases are green; next register the tier and expose training-signal summaries.",
            "full_pytest_required_before_start": False,
        }
    return {
        "task_id": "CORE-CAL-S1A",
        "title": "Repair Synthetic Typical Answer Calibration",
        "rationale": "One or more synthetic typical answer cases failed text quality expectations.",
        "full_pytest_required_before_start": False,
    }


def _mapping(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _str_list(value: object) -> list[str]:
    return [str(row) for row in value] if isinstance(value, (list, set, tuple)) else []
