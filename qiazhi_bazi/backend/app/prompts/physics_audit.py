"""物理审计 LLM：compact / standard 双档 system+user（单一事实来源）。"""

from __future__ import annotations

import json
from typing import Any, Dict, List

from app.prompts.evolution_contracts import (
    PHYSICS_AUDIT_HIGH_REASONING_CAUSAL_TRACE,
    PHYSICS_AUDIT_HIGH_REASONING_SQL_DISCIPLINE,
)
from app.prompts.language import LanguageEngine

# 与 AuditLlmStructuredResponse 对齐的单行示例（键名层级须一致）
AUDIT_JSON_SCHEMA_LINE = (
    '{"diagnosis":"","alignment_score":0,"top_anomaly":"","causal_reasoning":"",'
    '"tuning_suggestions":[""],"sql_patch":"","refresh_hint":"",'
    '"logic_proposal":{"title":"","param_key":"","suggested_value":0,"reason":"","expected_impact":"",'
    '"sql_patch":"","source_role":"LLM"}}'
)


def build_physics_audit_messages(
    *,
    deity_scores: Dict[str, float],
    root_check: Dict[str, Any],
    seasonal_factors: Dict[str, Any],
    consensus_history: List[Dict[str, Any]],
    lang: str,
    blind_skill_system_suffix: str = "",
    tier: str = "compact",
    high_reasoning: bool = False,
    inference_trace: Dict[str, Any] | None = None,
) -> List[Dict[str, str]]:
    lang_hint = LanguageEngine.output_directive_for_structured_flow(lang)
    t = (tier or "compact").strip().lower()
    if t not in ("standard", "compact"):
        t = "compact"
    extra = (blind_skill_system_suffix or "").strip()
    high_tail = ""
    if high_reasoning:
        high_tail = (
            "\n"
            + PHYSICS_AUDIT_HIGH_REASONING_SQL_DISCIPLINE
            + "\n"
            + PHYSICS_AUDIT_HIGH_REASONING_CAUSAL_TRACE
        )

    trace_user = ""
    if high_reasoning and isinstance(inference_trace, dict) and inference_trace.get("steps"):
        try:
            tb = json.dumps(
                {
                    "version": inference_trace.get("version", "1.0"),
                    "steps": (inference_trace.get("steps") or [])[:96],
                },
                ensure_ascii=False,
            )
        except (TypeError, ValueError):
            tb = "{}"
        if len(tb) > 8000:
            tb = tb[:8000] + "…"
        trace_user = f"\n## InferenceTrace（供 causal_reasoning 逐步溯源）\n{tb}\n"

    if t == "compact":
        system_text = (
            "你是物理命理审计助手。请只输出一个 JSON 对象：不要使用 markdown 代码围栏，不要在 JSON 前后写任何说明。"
            "键名与嵌套必须与下例完全一致："
            f"{AUDIT_JSON_SCHEMA_LINE}"
            "规则：若 top_anomaly 非空，则 alignment_score 必须小于 60；"
            "sql_patch 只能是单条 UPDATE physics_interaction_params SET param_value=<小数> WHERE param_key='<键>';。"
            + high_tail
        )
        if extra:
            system_text = f"{system_text}\n{extra}"
        user_text = (
            "用中文填各字符串字段，只输出 JSON。\n"
            f"十神:{json.dumps(deity_scores, ensure_ascii=False)} "
            f"根气:{json.dumps(root_check, ensure_ascii=False)} "
            f"季节:{json.dumps(seasonal_factors, ensure_ascii=False)} "
            f"共识:{json.dumps(consensus_history or [], ensure_ascii=False)}\n"
            + trace_user
            + "top_anomaly=主要矛盾一句；causal_reasoning=原因；"
            "logic_proposal 含 title/param_key/suggested_value/reason/expected_impact/sql_patch/source_role；"
            "sql_patch 单条 UPDATE physics_interaction_params…；已共识参数勿再否定其数值。"
            f"{lang_hint}"
        )
        return [{"role": "system", "content": system_text}, {"role": "user", "content": user_text}]

    system_text = (
        "你是 0.13 实验室的首席物理命理审计官。只输出严格 JSON，不输出任何非 JSON 文本。"
        "字段固定（字段名/层级必须一致）："
        f"{AUDIT_JSON_SCHEMA_LINE}"
        "若 top_anomaly 非空，则 alignment_score 必须 < 60。"
        + high_tail
    )
    if extra:
        system_text = f"{system_text}\n{extra}"
    user_text = (
        f"Input. 十神分值={json.dumps(deity_scores, ensure_ascii=False)}；"
        f"根气汇总={json.dumps(root_check, ensure_ascii=False)}；"
        f"季节系数={json.dumps(seasonal_factors, ensure_ascii=False)}。\n"
        f"## 已达成逻辑共识\n{json.dumps(consensus_history or [], ensure_ascii=False)}\n"
        + trace_user
        + "Mandatory: "
        "1) top_anomaly: 最核心不匹配；"
        "2) causal_reasoning: 解释其违背的能量规律；"
        "3) sql_patch: 仅允许 UPDATE physics_interaction_params SET param_value=<float> WHERE param_key='<KEY>';"
        "4) logic_proposal: 必须含 title/param_key/suggested_value/reason/expected_impact/sql_patch/source_role；"
        "5) 对于已达成逻辑共识中的参数，不得重复质疑其已确认值，应在其基础上分析尚未共识的矛盾；"
        f"{lang_hint}"
    )
    return [{"role": "system", "content": system_text}, {"role": "user", "content": user_text}]
