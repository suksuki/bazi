from __future__ import annotations

import json
from typing import Any, Dict, Iterable, List, Literal, Mapping

from .decision_brain_protocol import build_plan_claim

LLM_PROMPT_CONTRACT_VERSION = "v17.prompt.contract.v1.0"
PLAN_PROMPT_VERSION = "v17.plan.arbitration.v1.0"
CONFLICT_PROMPT_VERSION = "v17.conflict.arbitration.v1.0"
WEALTH_ASSERTION_PROMPT_VERSION = "v17.topic.wealth_assertion_prompt.v1.0"
OUTPUT_LANGUAGE = Literal["zh", "en", "ko"]

_ZH_WEALTH_FORBIDDEN_TERMS = [
    "正财",
    "偏财",
    "食神",
    "伤官",
    "正官",
    "七杀",
    "正印",
    "偏印",
    "比肩",
    "劫财",
    "财星",
    "食伤",
    "比劫",
    "官杀",
    "体用",
    "用神",
    "忌神",
    "桥接神",
]


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


def _wealth_code_from_inputs(
    *,
    wealth_code: Dict[str, Any] | None = None,
    physics_tensor: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    from v17_rebirth.backend.logic.L3_modern_narrative.wealth_code_core import (
        normalize_wealth_code_meta,
        resolve_wealth_code,
    )

    if isinstance(wealth_code, dict) and wealth_code:
        return normalize_wealth_code_meta(wealth_code)
    pt = physics_tensor if isinstance(physics_tensor, dict) else {}
    meta = pt.get("meta") if isinstance(pt.get("meta"), dict) else {}
    if isinstance(meta.get("wealth_code"), dict) and meta.get("wealth_code"):
        return normalize_wealth_code_meta(meta.get("wealth_code"))
    if pt:
        return normalize_wealth_code_meta(resolve_wealth_code(pt).get("wealth_code"))
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


def _plain_usable_state(value: Any) -> str:
    key = _safe_str(value)
    if key == "wealth_as_use":
        return "赚钱机会比较容易落地"
    if key == "wealth_as_taboo":
        return "赚钱机会伴随压力，需要先管住风险"
    if key == "wealth_needs_bridge":
        return "需要先靠产品、平台、专业背书或稳定交付把钱接住"
    return "收入来源还不够清晰，先观察稳定性"


def _plain_wealth_summary(profile: Dict[str, Any], channels: List[Dict[str, Any]]) -> Dict[str, Any]:
    top_channel = channels[0] if channels else {}
    return {
        "user_question": "钱怎么来、能不能接住、哪里会漏钱、下一步怎么做",
        "main_money_path": _safe_str(top_channel.get("label"), default="待观察") if top_channel else "待观察",
        "opportunity_strength": round(_safe_float(profile.get("score"), 0.0), 3),
        "risk_level": round(_safe_float(profile.get("risk"), 0.0), 3),
        "confidence": round(_safe_float(profile.get("confidence"), 0.0), 3),
        "usable_explanation": _plain_usable_state(profile.get("usable_state")),
    }


def _compact_code_rows(value: Any, limit: int = 4) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for row in _safe_list(value):
        if not isinstance(row, dict):
            continue
        plain_name = _safe_str(row.get("plain_name") or row.get("focus") or row.get("plain_summary") or row.get("id") or row.get("year"))
        if not plain_name:
            continue
        rows.append(
            {
                "id": _safe_str(row.get("id")),
                "year": row.get("year"),
                "plain_name": plain_name,
                "focus": _safe_str(row.get("focus")),
                "attention_type": _safe_str(row.get("attention_type")),
                "plain_summary": _safe_str(row.get("plain_summary")),
                "score": round(max(0.0, min(1.0, _safe_float(row.get("score"), 0.0))), 3),
                "risk": round(max(0.0, min(1.0, _safe_float(row.get("risk"), 0.0))), 3),
                "tags": _compact_profile_list(row.get("triggered_components") or row.get("tags"), limit=4),
                "evidence": _compact_profile_list(row.get("evidence"), limit=3),
                "activated_chains": [
                    {
                        "chain_id": _safe_str(item.get("chain_id") or item.get("id")),
                        "plain_name": _safe_str(item.get("plain_name")),
                        "closure_state": _safe_str(item.get("closure_state")),
                        "activation_score": round(max(0.0, min(1.0, _safe_float(item.get("activation_score"), 0.0))), 3),
                        "reason": _safe_str(item.get("reason")),
                        "risk_modes": _compact_profile_list(item.get("risk_modes"), limit=4),
                    }
                    for item in _safe_list(row.get("activated_chains"))
                    if isinstance(item, Mapping)
                ],
            }
        )
        if len(rows) >= limit:
            break
    return rows


def _compact_path_rankings(value: Any, limit: int = 6) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for row in _safe_list(value):
        if not isinstance(row, dict):
            continue
        row_dict = {
            "rank": int(max(1, _safe_float(row.get("rank"), len(rows) + 1))),
            "id": _safe_str(row.get("id")),
            "plain_name": _safe_str(row.get("plain_name") or row.get("focus") or row.get("plain_summary") or row.get("id")),
            "size": _safe_str(row.get("size"), "中"),
            "combined_score": round(max(0.0, min(1.0, _safe_float(row.get("combined_score"), 0.0))), 3),
            "score": round(max(0.0, min(1.0, _safe_float(row.get("score"), 0.0))), 3),
            "risk": round(max(0.0, min(1.0, _safe_float(row.get("risk"), 0.0))), 3),
            "evidence_count": int(_safe_float(row.get("evidence_count"), 0)),
        }
        if row_dict["id"]:
            rows.append(row_dict)
        if len(rows) >= limit:
            break
    return rows


def _compact_wealth_code(code: Dict[str, Any]) -> Dict[str, Any]:
    primary = _safe_dict(code.get("primary_wealth_path"))
    source = _safe_dict(code.get("wealth_source"))
    engine = _safe_dict(code.get("monetization_engine"))
    carrier = _safe_dict(code.get("carrier"))
    vault = _safe_dict(code.get("wealth_vault"))
    mechanism_chains = _safe_list(code.get("mechanism_chains"))
    return {
        "plain_summary": {
            "user_question": "钱从哪里来、靠什么变现、怎么接住、哪里漏钱、哪些年份值得看",
            "primary_path": _safe_str(primary.get("plain_name"), default="待观察"),
            "primary_path_summary": _safe_str(primary.get("plain_summary")),
            "wealth_source": _safe_str(source.get("plain_source"), default="待观察"),
            "wealth_source_material": _safe_str(source.get("material")),
            "monetization_driver": _safe_str(engine.get("plain_driver"), default="待观察"),
            "carrier": _safe_str(carrier.get("plain_type"), default="待观察"),
            "vault": _safe_str(vault.get("plain_summary")),
        },
        "primary_wealth_path": {
            "id": _safe_str(primary.get("id")),
            "plain_name": _safe_str(primary.get("plain_name")),
            "plain_summary": _safe_str(primary.get("plain_summary")),
            "score": round(max(0.0, min(1.0, _safe_float(primary.get("score"), 0.0))), 3),
            "confidence": round(max(0.0, min(1.0, _safe_float(primary.get("confidence"), 0.0))), 3),
            "risk": round(max(0.0, min(1.0, _safe_float(primary.get("risk"), 0.0))), 3),
            "evidence": _compact_profile_list(primary.get("evidence"), limit=4),
        },
        "mechanism_chains": [
            {
                "id": _safe_str(chain.get("id")),
                "plain_name": _safe_str(chain.get("plain_name")),
                "chain_name": _safe_str(chain.get("chain_name")),
                "plain_summary": _safe_str(chain.get("plain_summary")),
                "met": bool(chain.get("met")),
                "score": round(max(0.0, min(1.0, _safe_float(chain.get("score"), 0.0))), 3),
                "activation_score": round(max(0.0, min(1.0, _safe_float(chain.get("activation_score"), 0.0))), 3),
                "closure_state": _safe_str(chain.get("closure_state")),
                "state_reason": _safe_str(chain.get("state_reason")),
                "risk": round(max(0.0, min(1.0, _safe_float(chain.get("risk"), 0.0))), 3),
                "completeness": round(max(0.0, min(1.0, _safe_float(chain.get("completeness"), 0.0))), 3),
                "risk_modes": _compact_profile_list(chain.get("risk_modes"), limit=4),
                "timing_triggers": _compact_profile_list(chain.get("timing_triggers"), limit=4),
                "steps": [
                    {
                        "path_id": _safe_str(item.get("path_id")),
                        "plain_name": _safe_str(item.get("plain_name")),
                        "present": bool(item.get("present")),
                        "path_score": _safe_float(item.get("path_score"), 0.0),
                    }
                    for item in _safe_list(chain.get("steps")) if isinstance(item, dict)
                ][:4],
            }
            for chain in mechanism_chains[:2]
            if isinstance(chain, dict)
        ],
        "secondary_paths": _compact_code_rows(code.get("secondary_paths"), limit=4),
        "path_rankings": _compact_path_rankings(code.get("path_rankings"), limit=5),
        "wealth_source": {
            "plain_source": _safe_str(source.get("plain_source")),
            "material": _safe_str(source.get("material")),
            "evidence": _compact_profile_list(source.get("evidence"), limit=4),
        },
        "monetization_engine": {
            "plain_driver": _safe_str(engine.get("plain_driver")),
            "chain_integrity": round(max(0.0, min(1.0, _safe_float(engine.get("chain_integrity"), 0.0))), 3),
        },
        "carrier": {
            "plain_type": _safe_str(carrier.get("plain_type")),
            "score": round(max(0.0, min(1.0, _safe_float(carrier.get("score"), 0.0))), 3),
            "requirements": _compact_profile_list(carrier.get("requirements"), limit=5),
        },
        "wealth_vault": {
            "has_vault_signal": bool(vault.get("has_vault_signal")),
            "plain_summary": _safe_str(vault.get("plain_summary")),
            "evidence": _compact_profile_list(vault.get("evidence"), limit=4),
        },
        "leakage_points": _compact_code_rows(code.get("leakage_points"), limit=5),
        "flow_year_watchlist": _compact_code_rows(code.get("flow_year_watchlist"), limit=5),
        "evidence": _compact_profile_list(code.get("evidence"), limit=10),
    }


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
    wealth_code: Dict[str, Any] | None = None,
    wealth_profile: Dict[str, Any] | None = None,
    physics_tensor: Dict[str, Any] | None = None,
    output_language: Any = "zh",
) -> Dict[str, Any]:
    lang = _normalize_output_language(output_language)
    code = _wealth_code_from_inputs(wealth_code=wealth_code, physics_tensor=physics_tensor)
    profile = _profile_from_inputs(wealth_profile=wealth_profile, physics_tensor=physics_tensor)
    assertion_style = _safe_dict(profile.get("assertion_style"))
    channels = _compact_channel_rows(profile.get("primary_channels"))
    prompt_channels = [] if code else channels
    material_contract = _safe_str(code.get("contract")) if code else _safe_str(profile.get("contract"), default="v17.topic.wealth_profile.v1")
    return {
        "prompt_contract_version": LLM_PROMPT_CONTRACT_VERSION,
        "task_type": "wealth_topic_assertion",
        "policy_version": WEALTH_ASSERTION_PROMPT_VERSION,
        "output_language": lang,
        "input_contract": material_contract,
        "input_priority": ["wealth_code", "wealth_profile"],
        "wealth_code_present": bool(code),
        "profile_present": bool(profile),
        "material_present": bool(code or profile),
        "summary": {
            "topic": _safe_str(profile.get("topic"), default="wealth"),
            "score": round(_safe_float(code.get("score") if code else profile.get("score"), 0.0), 3),
            "confidence": round(_safe_float(code.get("confidence") if code else profile.get("confidence"), 0.0), 3),
            "risk": round(_safe_float(code.get("risk") if code else profile.get("risk"), 0.0), 3),
            "stance": _safe_str(profile.get("stance")),
            "visibility": _safe_str(profile.get("visibility")),
            "usable_state": _safe_str(profile.get("usable_state")),
            "top_channel": prompt_channels[0] if prompt_channels else {},
            "primary_wealth_path": _safe_dict(code.get("primary_wealth_path")) if code else {},
        },
        "wealth_code": _compact_wealth_code(code) if code else {},
        "wealth_profile": {
            "usage_role": "secondary_conditions_when_wealth_code_present" if code else "primary_material",
            "plain_summary": _plain_wealth_summary(profile, prompt_channels),
            "primary_channels": prompt_channels,
            "strengths": [] if code else _compact_profile_list(profile.get("strengths"), limit=6),
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
            "must_preserve": (
                ["wealth_code.primary_wealth_path", "wealth_code.wealth_source", "wealth_code.carrier", "score", "confidence", "risk"]
                if code
                else ["score", "confidence", "risk", "usable_state", "primary_channels"]
            ),
            "forbidden_claims": _wealth_forbidden_claims(lang),
            "output_mode": "domain_specific_natural_language",
            "audience": "ordinary_user_not_practitioner",
            "writing_rules": [
                "write in plain wealth language: income source, earning path, cash flow, clients, projects, pricing, contracts, savings, cooperation, risk control",
                "if wealth_code is present, make it the primary basis for wealth path, monetization, carrier, leakage, vault, and year watchlist",
                "if wealth_code and wealth_profile.primary_channels disagree, follow wealth_code.primary_wealth_path and use primary_channels only as secondary conditions",
                "organize responses by mechanism chain order: trigger condition -> conversion -> carrying and monetization, and mention path_rankings from wealth_code in descending order of size from highest to lowest",
                "when mechanism chain is output-to-wealth, explain as: solve high-difficulty problems, convert outputs into saleable or project outputs, then lock in cash-flow via contracts/positions/contracts.",
                "do not expose internal BaZi or ten-god terminology to the user",
                "each block should answer a real user question, not describe the system contract",
            ],
            "forbidden_user_terms": _ZH_WEALTH_FORBIDDEN_TERMS if lang == "zh" else [],
            "max_chars": 520 if lang == "zh" else 900,
            "mechanism_chain_required": code.get("mechanism_chains", []) if code else [],
        },
    }


def build_wealth_assertion_prompt_text(
    *,
    wealth_code: Dict[str, Any] | None = None,
    wealth_profile: Dict[str, Any] | None = None,
    physics_tensor: Dict[str, Any] | None = None,
    output_language: Any = "zh",
) -> str:
    contract = build_wealth_assertion_prompt_bundle(
        wealth_code=wealth_code,
        wealth_profile=wealth_profile,
        physics_tensor=physics_tensor,
        output_language=output_language,
    )
    lang = _normalize_output_language(output_language)
    if lang == "en":
        lines: List[str] = [
            "You are the V17 wealth-topic assertion writer.",
            "Task: write a wealth-specific reading for an ordinary user using only the supplied wealth_code first, falling back to wealth_profile only when wealth_code is missing.",
            "Boundary: do not read raw chart data freely, do not re-infer the chart, and do not change confidence, risk, channels, or usable_state.",
            "Priority: if wealth_code.primary_wealth_path disagrees with wealth_profile.primary_channels, use wealth_code as the main path and treat profile channels as supporting conditions.",
            "Forbidden: guaranteed fortune, guaranteed poverty, bankruptcy claims, exact money amounts, exact years, or treating strong wealth stars as money already obtained.",
            "Style: translate every technical signal into wealth language: income source, earning path, cash flow, clients, projects, contracts, cooperation, pricing, and risk control.",
            "Do not mention ten-god names or internal contract fields in the user-facing answer.",
            "Mechanism rule: first describe trigger conditions, then conversion path, then carry/closure (contracts/platform/jobs).",
            "",
            "## Required Output",
            "Use five compact blocks: [Overall], [How Money Comes], [Can It Be Held], [Money Leaks], [Next Actions].",
            "Cite at least two evidence items from wealth_code.evidence, path evidence, wealth_profile.evidence, or channel evidence.",
            "In your outline, prioritize the highest-score item in contract.wealth_code.mechanism_chains, and use contract.wealth_code.path_rankings to describe money paths from highest to lowest scale.",
            "",
            "## Wealth Code",
            json.dumps(contract["wealth_code"], ensure_ascii=False, indent=2),
            "",
            "## Wealth Profile",
        ]
        output_label = "## Output Contract"
    elif lang == "ko":
        lines = [
            "당신은 V17 재물 주제 단언 작성자입니다.",
            "작업: 제공된 wealth_code 를 우선 사용하고, 없을 때만 wealth_profile 을 보조로 사용하여 일반 사용자가 이해할 수 있는 재물 해석을 작성하십시오.",
            "경계: 원국 자료를 자유롭게 다시 해석하지 말고, confidence/risk/channel/usable_state 를 바꾸지 마십시오.",
            "우선순위: wealth_code.primary_wealth_path 와 wealth_profile.primary_channels 가 다르면 wealth_code 를 주 경로로 삼고 profile channels 는 보조 조건으로만 쓰십시오.",
            "금지: 반드시 큰돈을 번다, 재물이 없다, 파산한다, 정확한 금액·연도, 재성이 강하니 이미 돈이 많다는 식의 표현.",
            "문체: 모든 기술적 신호를 수입원, 돈 버는 방식, 현금흐름, 고객, 프로젝트, 계약, 협업, 가격 책정, 위험 관리 언어로 바꾸십시오.",
            "사용자에게 십성 이름이나 내부 계약 필드를 드러내지 마십시오.",
            "절차는 먼저 트리거 조건을 말하고, 그 다음 현금화 전환 단계(서비스/제품/프로젝트), 마지막으로 계약/조직/포지션으로의 수용단계를 설명하십시오.",
            "",
            "## 필수 출력",
            "[전체 판단], [돈이 들어오는 방식], [돈을 받아내는 조건], [새는 돈], [다음 행동]의 다섯 짧은 블록을 사용하십시오.",
            "wealth_code.evidence, path evidence, wealth_profile.evidence 또는 channel evidence 에서 최소 2개 근거를 인용하십시오.",
            "우선 contract.mechanism_chains 의 최고 점수 체인을 스토리 중심축으로 반영하고, 이어서 path_rankings 을 규모(大→小) 순으로 정리하세요。",
            "",
            "## 재물 코드",
            json.dumps(contract["wealth_code"], ensure_ascii=False, indent=2),
            "",
            "## 재물 프로필",
        ]
        output_label = "## 출력 계약"
    else:
        lines = [
            "你是 V17 财富解读写作者。",
            "任务：只基于输入的 wealth_code 优先写财富解读；没有 wealth_code 时，才退回使用 wealth_profile。",
            "边界：不得自由重读原始八字，不得重新推盘，不得改写置信度、风险、主通道或可用状态。",
            "优先级：如果 wealth_code.primary_wealth_path 与 wealth_profile.primary_channels 不一致，必须以 wealth_code 的财富路径为主，primary_channels 只作为承接条件或辅助风险。",
            "禁区：不得写必发财、无财、破产、确定金额、确定年份，也不得把财星强等同于已经有钱。",
            "文风：把所有技术信号翻译成财富语言，只讲收入来源、赚钱方式、现金流、客户/项目、合同、合作、定价、储蓄和风险控制。",
            "用户正文里不要出现正财、偏财、食伤、比劫、官杀、体用、用神、忌神、桥接神等内部术语。",
            "不要说“画像显示”“系统判定”“可用状态”；要直接说“你更适合怎样赚钱、哪里容易漏钱、先做什么”。",
            "写作顺序：先讲触发条件，再讲变现转换（方案/服务/产品），最后讲承接机制（岗位、平台、合同、边界）。",
            "",
            "## 必须输出",
            "使用五个紧凑段落：【总体判断】【钱怎么来】【能不能接住】【要避开的坑】【接下来怎么做】。",
            "至少引用 2 条 wealth_code.evidence、财富路径证据、wealth_profile.evidence 或通道证据。",
            "先读 contract.wealth_code.mechanism_chains，并优先用分数最高的机制链组织叙事；同时结合 path_rankings 从规模从高到低说明财富路径排序。",
            "",
            "## 财富密码",
            json.dumps(contract["wealth_code"], ensure_ascii=False, indent=2),
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
    if not contract.get("material_present"):
        missing = {
            "zh": "缺少 wealth_code 和 wealth_profile 时，只能说明资料不足，不能生成财富解读。",
            "en": "If both wealth_code and wealth_profile are missing, say the material is insufficient and do not generate a wealth assertion.",
            "ko": "wealth_code 와 wealth_profile 이 모두 없으면 자료가 부족하다고 말하고 재물 단언을 생성하지 마십시오.",
        }[lang]
        lines.extend(["", "## Missing Material Rule", missing])
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
