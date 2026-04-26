from __future__ import annotations

import json
from typing import Any, Dict, Iterable, List, Literal

from .decision_brain_protocol import build_plan_claim

LLM_PROMPT_CONTRACT_VERSION = "v17.prompt.contract.v1.0"
PLAN_PROMPT_VERSION = "v17.plan.arbitration.v1.0"
CONFLICT_PROMPT_VERSION = "v17.conflict.arbitration.v1.0"
WEALTH_ASSERTION_PROMPT_VERSION = "v17.topic.wealth_assertion_prompt.v1.0"
OUTPUT_LANGUAGE = Literal["zh", "en", "ko"]


def _normalize_output_language(value: Any) -> OUTPUT_LANGUAGE:
    raw = str(value or "").strip().lower()
    if raw == "en":
        return "en"
    if raw == "ko":
        return "ko"
    return "zh"


def _safe_str(value: Any, default: str = "") -> str:
    return str(value or "").strip() or default


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def _safe_list(value: Any) -> List[Any]:
    return [x for x in (value or []) if x is not None]


def _safe_dict(value: Any) -> Dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _profile_from_inputs(
    *,
    wealth_profile: Dict[str, Any] | None = None,
    physics_tensor: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    from v17_rebirth.backend.logic.L3_modern_narrative.wealth_profile_core import (
        normalize_wealth_profile_meta,
        resolve_wealth_profile,
    )

    if isinstance(wealth_profile, dict) and wealth_profile:
        return normalize_wealth_profile_meta(wealth_profile)
    pt = physics_tensor if isinstance(physics_tensor, dict) else {}
    meta = pt.get("meta") if isinstance(pt.get("meta"), dict) else {}
    if isinstance(meta.get("wealth_profile"), dict) and meta.get("wealth_profile"):
        return normalize_wealth_profile_meta(meta.get("wealth_profile"))
    if pt:
        return normalize_wealth_profile_meta(resolve_wealth_profile(pt).get("wealth_profile"))
    return {}


def _compact_profile_list(value: Any, limit: int = 6) -> List[str]:
    out: List[str] = []
    seen: set[str] = set()
    for item in _safe_list(value):
        text = _safe_str(item)
        if not text or text in seen:
            continue
        seen.add(text)
        out.append(text)
        if len(out) >= limit:
            break
    return out


def _compact_channel_rows(value: Any, limit: int = 4) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for row in _safe_list(value):
        if not isinstance(row, dict):
            continue
        channel_id = _safe_str(row.get("id"))
        label = _safe_str(row.get("label") or channel_id)
        if not channel_id and not label:
            continue
        rows.append(
            {
                "id": channel_id,
                "label": label,
                "score": round(max(0.0, min(1.0, _safe_float(row.get("score"), 0.0))), 3),
                "evidence": _compact_profile_list(row.get("evidence"), limit=3),
            }
        )
        if len(rows) >= limit:
            break
    return rows


def _wealth_forbidden_claims(lang: OUTPUT_LANGUAGE) -> List[str]:
    if lang == "en":
        return [
            "guaranteed fortune",
            "no wealth",
            "bankruptcy",
            "exact money amount",
            "exact year",
            "treating strong wealth stars as money already obtained",
            "treating weak wealth stars as inability to earn",
        ]
    if lang == "ko":
        return [
            "반드시 큰돈을 번다",
            "재물이 없다",
            "파산한다",
            "정확한 금액",
            "정확한 연도",
            "재성이 강하니 이미 돈이 많다",
            "재성이 약하니 돈을 벌 수 없다",
        ]
    return [
        "必发财",
        "无财",
        "破产",
        "确定金额",
        "确定年份",
        "把财星强等同于钱多",
        "把财星弱等同于不能赚钱",
    ]


def build_wealth_assertion_prompt_bundle(
    *,
    wealth_profile: Dict[str, Any] | None = None,
    physics_tensor: Dict[str, Any] | None = None,
    output_language: Any = "zh",
) -> Dict[str, Any]:
    lang = _normalize_output_language(output_language)
    profile = _profile_from_inputs(wealth_profile=wealth_profile, physics_tensor=physics_tensor)
    assertion_style = _safe_dict(profile.get("assertion_style"))
    channels = _compact_channel_rows(profile.get("primary_channels"))
    return {
        "prompt_contract_version": LLM_PROMPT_CONTRACT_VERSION,
        "task_type": "wealth_topic_assertion",
        "policy_version": WEALTH_ASSERTION_PROMPT_VERSION,
        "output_language": lang,
        "input_contract": _safe_str(profile.get("contract"), default="v17.topic.wealth_profile.v1"),
        "profile_present": bool(profile),
        "summary": {
            "topic": _safe_str(profile.get("topic"), default="wealth"),
            "score": round(_safe_float(profile.get("score"), 0.0), 3),
            "confidence": round(_safe_float(profile.get("confidence"), 0.0), 3),
            "risk": round(_safe_float(profile.get("risk"), 0.0), 3),
            "stance": _safe_str(profile.get("stance")),
            "visibility": _safe_str(profile.get("visibility")),
            "usable_state": _safe_str(profile.get("usable_state")),
            "top_channel": channels[0] if channels else {},
        },
        "wealth_profile": {
            "primary_channels": channels,
            "strengths": _compact_profile_list(profile.get("strengths"), limit=6),
            "risks": _compact_profile_list(profile.get("risks"), limit=6),
            "contradictions": _compact_profile_list(profile.get("contradictions"), limit=6),
            "bridge_requirements": _compact_profile_list(profile.get("bridge_requirements"), limit=6),
            "timing_hooks": _compact_profile_list(profile.get("timing_hooks"), limit=4),
            "evidence": _compact_profile_list(profile.get("evidence"), limit=8),
            "llm_prompt_focus": _compact_profile_list(profile.get("llm_prompt_focus"), limit=6),
            "assertion_style": {
                "tone": _safe_str(assertion_style.get("tone"), default="practical"),
                "must_include": _compact_profile_list(assertion_style.get("must_include"), limit=8),
                "must_avoid": _compact_profile_list(assertion_style.get("must_avoid"), limit=8),
            },
        },
        "output_contract": {
            "required_blocks": ["wealth_verdict", "wealth_source", "usable_and_bridge", "risk", "action"],
            "must_cite_evidence_count": 2,
            "must_preserve": ["score", "confidence", "risk", "usable_state", "primary_channels"],
            "forbidden_claims": _wealth_forbidden_claims(lang),
            "output_mode": "domain_specific_natural_language",
            "max_chars": 520 if lang == "zh" else 900,
        },
    }


def build_wealth_assertion_prompt_text(
    *,
    wealth_profile: Dict[str, Any] | None = None,
    physics_tensor: Dict[str, Any] | None = None,
    output_language: Any = "zh",
) -> str:
    contract = build_wealth_assertion_prompt_bundle(
        wealth_profile=wealth_profile,
        physics_tensor=physics_tensor,
        output_language=output_language,
    )
    lang = _normalize_output_language(output_language)
    if lang == "en":
        lines: List[str] = [
            "You are the V17 wealth-topic assertion writer.",
            "Task: write a wealth-specific BaZi assertion using only the supplied wealth_profile.",
            "Boundary: do not read raw chart data freely, do not re-infer the chart, and do not change confidence, risk, channels, or usable_state.",
            "Forbidden: guaranteed fortune, guaranteed poverty, bankruptcy claims, exact money amounts, exact years, or treating strong wealth stars as money already obtained.",
            "",
            "## Required Output",
            "Use five compact blocks: [Wealth Verdict], [Wealth Source], [Usable & Bridge], [Risk], [Action].",
            "Cite at least two evidence items from wealth_profile.evidence or channel evidence.",
            "",
            "## Wealth Profile",
        ]
        output_label = "## Output Contract"
    elif lang == "ko":
        lines = [
            "당신은 V17 재물 주제 단언 작성자입니다.",
            "작업: 제공된 wealth_profile 만 사용하여 재물 전용 명리 단언을 작성하십시오.",
            "경계: 원국 자료를 자유롭게 다시 해석하지 말고, confidence/risk/channel/usable_state 를 바꾸지 마십시오.",
            "금지: 반드시 큰돈을 번다, 재물이 없다, 파산한다, 정확한 금액·연도, 재성이 강하니 이미 돈이 많다는 식의 표현.",
            "",
            "## 필수 출력",
            "[재물 총단], [재물 출처], [사용 가능성과 연결 조건], [위험], [행동]의 다섯 짧은 블록을 사용하십시오.",
            "wealth_profile.evidence 또는 channel evidence 에서 최소 2개 근거를 인용하십시오.",
            "",
            "## 재물 프로필",
        ]
        output_label = "## 출력 계약"
    else:
        lines = [
            "你是 V17 财富专题断言器。",
            "任务：只基于输入的 wealth_profile 写财富专属断言。",
            "边界：不得自由重读原始八字，不得重新推盘，不得改写置信度、风险、主通道或可用状态。",
            "禁区：不得写必发财、无财、破产、确定金额、确定年份，也不得把财星强等同于已经有钱。",
            "",
            "## 必须输出",
            "使用五个紧凑段落：【财富总断】【财富来源】【可用与承接】【风险】【行动】。",
            "至少引用 2 条 wealth_profile.evidence 或通道证据。",
            "",
            "## 财富画像",
        ]
        output_label = "## 输出契约"
    lines.append(json.dumps(contract["wealth_profile"], ensure_ascii=False, indent=2))
    lines.extend(
        [
            "",
            "## Summary",
            json.dumps(contract["summary"], ensure_ascii=False, indent=2),
            "",
            output_label,
            json.dumps(contract["output_contract"], ensure_ascii=False, indent=2),
        ]
    )
    if not contract.get("profile_present"):
        missing = {
            "zh": "缺少 wealth_profile 时，只能说明资料不足，不能生成财富断言。",
            "en": "If wealth_profile is missing, say the material is insufficient and do not generate a wealth assertion.",
            "ko": "wealth_profile 이 없으면 자료가 부족하다고 말하고 재물 단언을 생성하지 마십시오.",
        }[lang]
        lines.extend(["", "## Missing Profile Rule", missing])
    return "\n".join(lines).strip()


def _normalize_decision_rows(rows: Iterable[Dict[str, Any]], max_rows: int = 16) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        label = _safe_str(row.get("label") or row.get("title"))
        impact = row.get("physical_impact") if isinstance(row.get("physical_impact"), dict) else {}
        target = _safe_str(impact.get("target_god") or row.get("target_god"), default="未定目标")
        ratio = _safe_float(impact.get("impact_ratio"), 0.0)
        source = _safe_str(row.get("source") or row.get("plugin_id"), default="unknown")
        out.append(
            {
                "id": _safe_str(row.get("id")),
                "label": label,
                "target_god": target,
                "source": source,
                "ratio": round(ratio, 6),
                "direction": "enhance" if ratio > 0 else "weaken" if ratio < 0 else "neutral",
                "priority": _safe_float(row.get("priority"), 0.0),
                "severity_hint": _safe_str(row.get("routing_claim", {}).get("severity"))
                if isinstance(row.get("routing_claim"), dict)
                else "",
                "raw": row,
            }
        )
        if len(out) >= max_rows:
            break
    return out


def build_plan_prompt_contract(
    *,
    rows: List[Dict[str, Any]],
    action: str,
    anchor: str,
    max_rows: int = 16,
    output_language: Any = "zh",
) -> Dict[str, Any]:
    lang = _normalize_output_language(output_language)
    safe_action = _safe_str(action)
    safe_anchor = _safe_str(anchor)
    compact_rows = _normalize_decision_rows(rows=rows, max_rows=max_rows)
    decision_count = len([dict(row or {}).get("id") for row in _safe_list(rows) if dict(row or {}).get("id")])
    total_abs = sum(abs(_safe_float(r.get("physical_impact", {}).get("impact_ratio"), 0.0)) for r in _safe_list(rows) if isinstance(r, dict))
    net_ratio = sum(_safe_float(r.get("physical_impact", {}).get("impact_ratio"), 0.0) for r in _safe_list(rows) if isinstance(r, dict))
    contract = {
        "prompt_contract_version": LLM_PROMPT_CONTRACT_VERSION,
        "task_id": f"decision_plan:{safe_action}:{safe_anchor or 'anchor'}:{decision_count}",
        "task_type": "decision_batch_arbitration",
        "policy_version": PLAN_PROMPT_VERSION,
        "anchor": safe_anchor,
        "action": safe_action,
        "output_language": lang,
        "summary": {
            "decision_count": decision_count,
            "truncated": max(0, len(_safe_list(rows)) - len(compact_rows)),
            "total_abs_ratio": round(total_abs, 6),
            "net_ratio": round(net_ratio, 6),
        },
        "decision_rows": compact_rows,
        "output_contract": {
            "required_fields": ["decision_id", "action", "reason"],
            "action_scope": ["KEEP", "DROP", "ESCALATE"],
            "reason_language": lang,
            "max_reason_chars": 120,
            "output_format": "json_array",
            "example": {
                "decision_id": compact_rows[0]["id"] if compact_rows else "d1",
                "action": "KEEP",
                "reason": {
                    "zh": "方向与十神主脉一致，保持为主。",
                    "en": "It matches the main ten-god direction; keep it.",
                    "ko": "십신 주 흐름과 맞으므로 유지합니다.",
                }[lang],
            },
            "fallback_when_unparseable": "保守处理（优先KEEP）",
        },
    }
    return contract


def build_plan_prompt_text(
    *,
    rows: List[Dict[str, Any]],
    action: str,
    anchor: str,
    max_rows: int = 16,
    output_language: Any = "zh",
) -> str:
    contract = build_plan_prompt_contract(rows=rows, action=action, anchor=anchor, max_rows=max_rows, output_language=output_language)
    lang = _normalize_output_language(output_language)
    if lang == "en":
        lines: List[str] = [
            "You are the V17 decision arbitration subsystem (v17.prompt.contract.v1.0).",
            "Task: arbitrate one batch of decision candidates. Output JSON only; no explanatory prose.",
            "",
            "Rules:",
            "1) Return executable choices only; do not rewrite physical boundaries.",
            "2) Each item must include decision_id/action/reason.",
            "3) action must be KEEP / DROP / ESCALATE.",
            "4) Use only the given candidates; do not add decisions.",
            "5) reason must be English and no longer than 120 characters.",
            "",
            "[Task Summary]",
        ]
        candidate_header = "[Decision Candidates]"
        output_header = "[Output Format]"
        empty_line = "No valid candidates."
        rest_line = "...handle the remaining {count} items by the same rules."
        example_reason = "Aligned with the chart's main direction; keep it."
    elif lang == "ko":
        lines = [
            "당신은 V17 결정 중재 하위 시스템입니다 (v17.prompt.contract.v1.0).",
            "작업: 같은 배치의 결정 후보를 중재합니다. JSON만 출력하고 설명문은 쓰지 마십시오.",
            "",
            "규칙:",
            "1) 실행 가능한 결과만 반환하고 물리 경계를 바꾸지 마십시오.",
            "2) 각 항목에는 decision_id/action/reason 이 반드시 있어야 합니다.",
            "3) action은 KEEP / DROP / ESCALATE 중 하나입니다.",
            "4) 주어진 후보만 사용하고 새 결정을 만들지 마십시오.",
            "5) reason은 한국어로 120자 이내로 쓰십시오.",
            "",
            "[작업 요약]",
        ]
        candidate_header = "[결정 후보]"
        output_header = "[출력 형식]"
        empty_line = "유효한 후보가 없습니다."
        rest_line = "...나머지 {count}개도 같은 규칙으로 처리하십시오."
        example_reason = "명식의 주 흐름과 맞으므로 유지합니다."
    else:
        lines = [
            "你是 V17 决策仲裁子系统（协议 v17.prompt.contract.v1.0）。",
            "任务：对同一批决策候选做统一裁决，只输出 JSON，不允许解释性文本。",
            "",
            "规则：",
            "1) 只给出可执行结果，不改写系统物理边界。",
            "2) 每条输出必须包含 decision_id/action/reason 三字段。",
            "3) action 仅可为 KEEP / DROP / ESCALATE。",
            "4) 仅使用给定候选；不得新增决策项。",
            "5) 字段 reason 用中文，建议≤120字。",
            "",
            "【任务摘要】",
        ]
        candidate_header = "【候选决策】"
        output_header = "【输出格式】"
        empty_line = "当前无有效候选。"
        rest_line = "...其余 {count} 条按相同规则处理。"
        example_reason = "与命局主线一致，默认保留。"
    lines.extend(
        [
            f"action={contract['action'] or '未给动作'}",
            f"anchor={contract['anchor'] or '未命名锚点'}",
            f"decision_count={contract['summary']['decision_count']}",
            f"truncated={contract['summary']['truncated']}",
            "",
        ]
    )
    lines.append(candidate_header)
    if compact := contract["decision_rows"]:
        for idx, row in enumerate(compact, start=1):
            reason = _safe_str(row.get("label") or row.get("raw", {}).get("label") or row.get("raw", {}).get("title"), default=f"决策{idx}")
            lines.append(
                f"{idx}. id={row['id']} | label={reason} | target={row['target_god']} | "
                f"direction={row['direction']} {abs(float(row['ratio']) * 100):.1f}% | source={row['source']}"
            )
        if len(_safe_list(rows)) > len(compact):
            lines.append(rest_line.format(count=len(_safe_list(rows)) - len(compact)))
    else:
        lines.append(empty_line)

    lines.extend(
        [
            "",
            output_header,
            {
                "zh": "请仅输出标准 JSON 数组，示例：",
                "en": "Output a standard JSON object only, for example:",
                "ko": "표준 JSON 객체만 출력하십시오. 예:",
            }[lang],
            json.dumps(
                {
                    "version": "v17.decision.choices.v1",
                    "decisions": [
                        {
                            "decision_id": compact[0]["id"] if compact else "d1",
                            "action": "KEEP",
                            "reason": example_reason,
                        },
                    ],
                },
                ensure_ascii=False,
            ),
        ]
    )
    return "\n".join(lines).strip()


def build_conflict_prompt_bundle(
    *,
    bundle: Dict[str, Any],
    output_language: Any = "zh",
) -> Dict[str, Any]:
    lang = _normalize_output_language(output_language)
    conflicts = _safe_list(bundle.get("conflicts"))
    claims = _safe_list(bundle.get("claims"))
    conflict_ids = [str(c.get("conflict_id") or "").strip() for c in conflicts if str(c.get("conflict_id") or "").strip()]
    conflict_count = len(conflict_ids)
    claim_ids = [str(c.get("claim_id") or "").strip() for c in claims if str(c.get("claim_id") or "").strip()]
    return {
        "prompt_contract_version": LLM_PROMPT_CONTRACT_VERSION,
        "task_type": "conflict_bundle_arbitration",
        "policy_version": CONFLICT_PROMPT_VERSION,
        "output_language": lang,
        "summary": {
            "conflict_count": conflict_count,
            "conflict_ids": conflict_ids,
            "claim_count": len(claim_ids),
        },
        "conflicts": conflicts,
        "claims": claims,
        "output_contract": {
            "required_fields": [
                "resolution_type",
                "preferred_arbiter",
                "winner_claim_ids",
                "dropped_claim_ids",
                "reason",
                "confidence",
            ],
            "resolution_type_scope": ["merge", "reject", "escalate_user", "context_only"],
            "preferred_arbiter_scope": ["system", "llm", "user"],
            "confidence_range": "[0.0,1.0]",
            "map_mode": "results_by_conflict" if conflict_count > 1 else "single",
            "output_format": "json",
            "fallback_when_unparseable": "context_only + 0.0",
            "reason_language": lang,
        },
    }


def build_conflict_prompt_text(
    *,
    bundle: Dict[str, Any],
    output_language: Any = "zh",
) -> str:
    contract = build_conflict_prompt_bundle(bundle=bundle, output_language=output_language)
    lang = _normalize_output_language(output_language)
    conflicts = contract["conflicts"]
    claims = contract["claims"]
    knowledge_snapshot = contract.get("knowledge_snapshot", {})
    if lang == "en":
        lines: List[str] = [
            "You are the V17 conflict arbiter (v17.prompt.contract.v1.0). Output structured JSON only.",
            "Task: give a compliant model judgement for the conflict cluster.",
            "Constraint: no explanatory prose, no fact rewriting, fields only.",
            "Output JSON only. Do not add code fences or explanations.",
            "",
        ]
        single_note = "Single-conflict arbitration. Return resolution_type and related fields."
        multi_note = "Multi-conflict batch. Return a results_by_conflict dictionary."
        reason_example = "Candidate handling under the shared constraint."
        claims_intro = "Conflict objects:"
        output_contract_label = "## Output Contract"
    elif lang == "ko":
        lines = [
            "당신은 V17 충돌 중재자입니다 (v17.prompt.contract.v1.0). 구조화된 JSON만 출력하십시오.",
            "작업: 충돌 묶음에 대해 규격화된 모델 판정을 제공합니다.",
            "제약: 설명문을 쓰지 말고 사실을 바꾸지 말며 필드화된 결론만 반환하십시오.",
            "JSON만 출력하고 코드 블록이나 설명은 붙이지 마십시오.",
            "",
        ]
        single_note = "단일 충돌 중재입니다. resolution_type 등 필드를 반환하십시오."
        multi_note = "다중 충돌 배치입니다. results_by_conflict 딕셔너리를 반환하십시오."
        reason_example = "공통 제약 아래의 후보 처리입니다."
        claims_intro = "충돌 객체:"
        output_contract_label = "## 출력 계약"
    else:
        lines = [
            "你是 V17 冲突仲裁器（协议 v17.prompt.contract.v1.0），只输出结构化 JSON。",
            "任务：对冲突簇给出合规模型化裁决。",
            "约束：禁止输出解释文本，不要改写事实，只给出字段化结论。",
            "输出仅为 JSON，不要附加代码块与解释。",
            "只输出 JSON，不要带解释文本。",
            "",
        ]
        single_note = "说明：这是单冲突裁决。返回 resolution_type 等字段。"
        multi_note = "说明：这是多冲突批处理。请返回 results_by_conflict 字典。"
        reason_example = "统一约束下的候选处理"
        claims_intro = "以下是冲突对象："
        output_contract_label = "## 输出契约"
    conflict_count = int(contract["summary"]["conflict_count"])
    if conflict_count > 1:
        lines.append("## Conflict")
        lines.append(multi_note)
        lines.append(json.dumps({"results_by_conflict": {cid: "..." for cid in contract["summary"]["conflict_ids"]},}, ensure_ascii=False))
    else:
        lines.append("## Conflict")
        lines.append(single_note)
    lines.append("")
    lines.append("## Claims")
    lines.append(claims_intro)
    lines.extend([json.dumps(c, ensure_ascii=False, indent=2) for c in conflicts])
    lines.append("")
    lines.append("## Claims Detail")
    lines.extend([json.dumps(c, ensure_ascii=False, indent=2) for c in claims])
    lines.append("")
    lines.append("## Knowledge Snapshot")
    lines.append(json.dumps(knowledge_snapshot, ensure_ascii=False, indent=2))
    lines.append("")
    lines.append(output_contract_label)
    lines.append(json.dumps(contract["output_contract"], ensure_ascii=False, indent=2))
    lines.append("")
    lines.append("## Output JSON")
    if conflict_count > 1:
        lines.append(
            json.dumps(
                {
                    "results_by_conflict": {
                        contract["summary"]["conflict_ids"][0]: {
                            "resolution_type": "merge",
                            "preferred_arbiter": "system",
                            "winner_claim_ids": [],
                            "dropped_claim_ids": [],
                            "reason": reason_example,
                            "confidence": 0.7,
                        },
                    },
                },
                ensure_ascii=False,
            )
        )
    else:
        lines.append(
            json.dumps(
                {
                    "resolution_type": "merge",
                    "preferred_arbiter": "system",
                    "winner_claim_ids": [],
                    "dropped_claim_ids": [],
                    "reason": reason_example,
                    "confidence": 0.7,
                },
                ensure_ascii=False,
            )
        )
    return "\n".join(lines).strip()
