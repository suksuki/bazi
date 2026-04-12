"""物理审计 LLM：compact / standard 双档 system+user（单一事实来源）。"""

from __future__ import annotations

import json
from typing import Any, Dict, List

from app.prompts.evolution_contracts import (
    PHYSICS_AUDIT_HIGH_REASONING_CAUSAL_TRACE,
    PHYSICS_AUDIT_HIGH_REASONING_SQL_DISCIPLINE,
)
from app.prompts.language import LanguageEngine
from app.prompts.physics_audit_contracts import AUDIT_JSON_SCHEMA_LINE
from app.utils.semantic_firewall import strip_float_literals
from app.skills.final_verdict_parts.evidence import format_deity_abs_semantic_slices

# 与 AuditLlmStructuredResponse 对齐的单行示例（键名层级须一致）
def _deity_semantic_block_for_audit_user(deity_scores: Dict[str, float]) -> str:
    """审计 User：十神只给档位行，禁止把 Abs 浮点当算术材料。"""
    fake: Dict[str, Any] = {"deity_energy_axes": {}, "abs_nodes": {}}
    for k, v in (deity_scores or {}).items():
        if isinstance(v, (int, float)):
            fake["deity_energy_axes"][str(k)] = {"absolute_energy": float(v)}
    lines = format_deity_abs_semantic_slices(fake, label_only=True)
    return "\n".join(lines) if lines else "语义.十神总览=（无档位行）"


def _strip_audit_messages(msgs: List[Dict[str, str]]) -> List[Dict[str, str]]:
    return [{"role": m["role"], "content": strip_float_literals(m.get("content") or "")} for m in msgs]


SYSTEM_FACT_CONFLICT_ANCHOR = (
    "[SYSTEM_FACT] 必须基于以上探测到的物理点进行诊断，严禁忽视三合、六冲、六合、穿害等已登记结构；"
    "若上表非空且含 sanhe、clash、combine 等标签，diagnosis 与 causal_reasoning 须显式呼应至少一项关键结构语义。"
)


def _verified_conflict_block_user(conflict_points: List[Dict[str, Any]]) -> str:
    if not conflict_points:
        body = "- （本轮无结构化冲突点登记；若仅有能量配比问题，如实输出 diagnosis。）\n"
    else:
        try:
            blob = json.dumps(conflict_points[:40], ensure_ascii=False)
        except (TypeError, ValueError):
            blob = "[]"
        if len(blob) > 3600:
            blob = blob[:3599] + "…"
        body = f"{blob}\n"
    return f"[Verified Facts·冲突矩阵 / L1 探测]\n{body}{SYSTEM_FACT_CONFLICT_ANCHOR}\n\n"


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
    conflict_points: List[Dict[str, Any]] | None = None,
    will_conflict_duel_context: str = "",
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

    cpts = list(conflict_points or [])
    vf_conflict = _verified_conflict_block_user(cpts)
    conflict_system_anchor = (
        "User 消息首段 [Verified Facts·冲突矩阵] 为引擎已收敛的结构事实；审计 JSON 须与之对齐，"
        "不得忽略表中已登记的三合/六冲/六合/穿害等标签，亦不得编造表中未出现的柱位关系。\n"
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

    duel_tail = ""
    wd = (will_conflict_duel_context or "").strip()
    if wd:
        duel_tail = (
            "\n若 User 含 [Will-Conflict Duel] 段：diagnosis/causal_reasoning 须用一两句点出「用户意志参数」与「盲派/体伤/熵」张力，"
            "不得无视该段；仍须输出合法 JSON，不得仅复述该段而不给 top_anomaly。\n"
        )

    if t == "compact":
        system_text = (
            "角色：Diagnostic Auditor（逻辑质检）。只输出单个 JSON，无代码围栏、无 JSON 外任何自然语言段落。"
            f"{conflict_system_anchor}"
            f"{duel_tail}"
            f"键名/层级与示例一致：{AUDIT_JSON_SCHEMA_LINE}"
            "diagnosis：工程师短句，≤200 字，无修辞与分点叙事；须始终非空；"
            "causal_reasoning：因果链要点，≤200 字；"
            "偏差与补丁意图只写入 logic_proposal（含 suggested_value/sql_patch）与根字段 sql_patch，即个体化调参 JSON。"
            "alignment_score 与 top_anomaly 须一致：凡 top_anomaly 写实质结构/战局矛盾，score 须 <60；"
            "入库时若仍≥60 会被后端收敛为 59。若以调参备忘为主、无实质矛盾，可清空 top_anomaly 或写「无」再给出较高分。"
            "sql_patch 为单条 UPDATE physics_interaction_params SET param_value=<小数> WHERE param_key='<白名单键>'；"
            "logic_proposal.param_key ∈ {CF_FLOATING_DECAY,THROUGH_STEM_BOOST,CONFLICT_PENALTY_GAMMA,A_PROTRUSION,"
            "OFFICER_RESTRAINT_ALPHA,POWER_DISTRIBUTION_GAMMA}。"
            "若当前无法给出合法 sql_patch：diagnosis 与 causal_reasoning 仍须非空，用文字写清逻辑冲突与根因，不得返回空 JSON 或全空字符串字段。"
            + high_tail
        )
        if extra:
            system_text = f"{system_text}\n{extra}"
        duel_user = f"\n[Will-Conflict Duel · 意志对系统]\n{wd[:8000]}\n\n" if wd else ""
        user_text = (
            "中文字段，仅输出 JSON。\n"
            f"{vf_conflict}"
            "[十神·仅语义档位，禁止复述 Abs 浮点或据此排序比大小]\n"
            f"{_deity_semantic_block_for_audit_user(deity_scores)}\n"
            f"根气:{json.dumps(root_check, ensure_ascii=False)} "
            f"季节:{json.dumps(seasonal_factors, ensure_ascii=False)} "
            f"共识:{json.dumps(consensus_history or [], ensure_ascii=False)}\n"
            + trace_user
            + duel_user
            + "top_anomaly、causal_reasoning、logic_proposal 按 schema；param_key 限上述白名单；已共识参数在其上继续推演。"
            f"{lang_hint}"
        )
        return _strip_audit_messages([{"role": "system", "content": system_text}, {"role": "user", "content": user_text}])

    system_text = (
        "角色：Diagnostic Auditor（逻辑质检·标准档）。只输出严格 JSON；JSON 外不得有说明段落。"
        f"{conflict_system_anchor}"
        f"{duel_tail}"
        f"字段与示例一致：{AUDIT_JSON_SCHEMA_LINE}"
        "diagnosis 须非空（工程师短句，≤200 字）；causal_reasoning≤200 字；调参意图写入 logic_proposal/sql_patch；"
        "若无法输出合法 sql_patch，仍须返回完整 JSON 且在 diagnosis 写明冲突根因。"
        "logic_proposal.param_key 白名单：CF_FLOATING_DECAY,THROUGH_STEM_BOOST,CONFLICT_PENALTY_GAMMA,A_PROTRUSION,"
        "OFFICER_RESTRAINT_ALPHA,POWER_DISTRIBUTION_GAMMA。"
        "alignment_score 与 top_anomaly 一致：实质矛盾则 score<60（否则入库时会被收敛）；调参备忘类可清空 top_anomaly 再高分。"
        + high_tail
    )
    if extra:
        system_text = f"{system_text}\n{extra}"
    duel_user_std = f"\n[Will-Conflict Duel · 意志对系统]\n{wd[:8000]}\n\n" if wd else ""
    user_text = (
        f"{vf_conflict}"
        "[十神·仅语义档位]\n"
        f"{_deity_semantic_block_for_audit_user(deity_scores)}\n"
        f"根气={json.dumps(root_check, ensure_ascii=False)}；"
        f"季节={json.dumps(seasonal_factors, ensure_ascii=False)}。\n"
        f"共识\n{json.dumps(consensus_history or [], ensure_ascii=False)}\n"
        + trace_user
        + duel_user_std
        + "输出须含非空 diagnosis、top_anomaly、causal_reasoning、logic_proposal；sql_patch 可为空串但须说明原因于 diagnosis；param_key 限白名单；"
        "已确认共识参数不重复否定，只分析剩余矛盾。"
        f"{lang_hint}"
    )
    return _strip_audit_messages([{"role": "system", "content": system_text}, {"role": "user", "content": user_text}])
