"""Helpers for qiazhi-bazi router orchestration."""
from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Any, Dict, List

from app.schemas.bazi_metadata import BaziMetadata

from .contracts import AuditLlmStructuredResponse


def guess_text_lang(text: str) -> str:
    if not text:
        return "UNKNOWN"
    if any("\uac00" <= ch <= "\ud7a3" for ch in text):
        return "KO"
    if any("\u4e00" <= ch <= "\u9fff" for ch in text):
        return "ZH"
    if text.isascii():
        return "EN"
    return "UNKNOWN"


def now_iso() -> str:
    return datetime.utcnow().isoformat()


def lang_output_instruction(lang: str) -> str:
    upper = (lang or "ZH").upper()
    if upper == "EN":
        return (
            "请基于中文命理逻辑推演，但最终只用英文输出。"
            "若术语无直接对等词，使用标准学术拼音并保留术语一致性。"
        )
    if upper == "KO":
        return "请基于中文命理逻辑推演，但最终只用韩语输出，并使用韩语术语。请务必以“최종 결론:”开头。"
    return "请基于中文命理逻辑推演，并只用中文输出。"


def build_physics_audit_prompt(
    *,
    deity_scores: Dict[str, float],
    root_check: Dict[str, Any],
    seasonal_factors: Dict[str, Any],
    consensus_history: List[Dict[str, Any]],
    lang: str,
) -> List[Dict[str, str]]:
    lang_hint = lang_output_instruction(lang)
    system_text = (
        "你是 0.13 实验室的首席物理命理审计官。只输出严格 JSON，不输出任何非 JSON 文本。"
        "字段固定（字段名/层级必须一致）："
        '{"diagnosis":"","alignment_score":0,"top_anomaly":"","causal_reasoning":"","tuning_suggestions":[""],"sql_patch":"","refresh_hint":"","logic_proposal":{"title":"","param_key":"","suggested_value":0,"reason":"","expected_impact":"","sql_patch":"","source_role":"LLM"}}'
        "若 top_anomaly 非空，则 alignment_score 必须 < 60。"
    )
    user_text = (
        f"Input. 十神分值={json.dumps(deity_scores, ensure_ascii=False)}；"
        f"根气汇总={json.dumps(root_check, ensure_ascii=False)}；"
        f"季节系数={json.dumps(seasonal_factors, ensure_ascii=False)}。\n"
        f"## 已达成逻辑共识\n{json.dumps(consensus_history or [], ensure_ascii=False)}\n"
        "Mandatory: "
        "1) top_anomaly: 最核心不匹配；"
        "2) causal_reasoning: 解释其违背的能量规律；"
        "3) sql_patch: 仅允许 UPDATE physics_interaction_params SET param_value=<float> WHERE param_key='<KEY>';"
        "4) logic_proposal: 必须含 title/param_key/suggested_value/reason/expected_impact/sql_patch/source_role；"
        "5) 对于已达成逻辑共识中的参数，不得重复质疑其已确认值，应在其基础上分析尚未共识的矛盾；"
        f"{lang_hint}"
    )
    return [{"role": "system", "content": system_text}, {"role": "user", "content": user_text}]


def extract_first_json_object(raw: str) -> str:
    text = (raw or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)
    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        raise ValueError("json object not found")
    return match.group(0)


def coerce_alignment_score(score: float, top_anomaly: str) -> float:
    value = max(1.0, min(100.0, float(score)))
    if top_anomaly.strip() and value >= 60.0:
        return 59.0
    return value


def patch_audit_json_from_text(raw_text: str, draft: AuditLlmStructuredResponse) -> tuple[AuditLlmStructuredResponse, bool]:
    text = (raw_text or "").strip()
    changed = False
    result = draft.model_copy(deep=True)
    sentinel_missing = "未拿到结构化审计结论" in (result.top_anomaly or "")

    if not result.top_anomaly or sentinel_missing:
        match = re.search(r"\"top_anomaly\"\s*[:：]\s*\"([^\"]+)\"", text, flags=re.IGNORECASE)
        if not match:
            match = re.search(r"(?:anomaly|异常|预警)[:：]\s*([^\n]+)", text, flags=re.IGNORECASE)
        if match:
            result.top_anomaly = match.group(1).strip()
            changed = True

    if (result.alignment_score is None) or float(result.alignment_score) <= 0 or (sentinel_missing and float(result.alignment_score) == 35.0):
        match = re.search(
            r"(?:alignment[_\s-]*score|对齐分|alignment|对齐)[：:\s]*([0-9]{1,3}(?:\.[0-9]+)?)",
            text,
            flags=re.IGNORECASE,
        )
        if not match:
            match = re.search(r"score[:：\s]*([0-9]{1,3}(?:\.[0-9]+)?)", text, flags=re.IGNORECASE)
        if not match:
            match = re.search(r"([0-9]{1,3}(?:\.[0-9]+)?)\s*分", text)
        if match:
            result.alignment_score = float(match.group(1))
            changed = True

    if not result.sql_patch or (sentinel_missing and "param_value=0.20" in (result.sql_patch or "")):
        match = re.search(
            r"(UPDATE\s+physics_interaction_params\s+SET\s+param_value\s*=\s*[0-9]*\.?[0-9]+\s+WHERE\s+param_key\s*=\s*'[A-Za-z0-9_]+'\s*;?)",
            text,
            flags=re.IGNORECASE,
        )
        if match:
            result.sql_patch = match.group(1).strip()
            changed = True
        if not result.sql_patch:
            kv_match = re.search(r"(CF_FLOATING_DECAY|A_PROTRUSION)\s*[:：=]\s*([0-9]*\.?[0-9]+)", text, flags=re.IGNORECASE)
            if kv_match:
                key = kv_match.group(1)
                value = float(kv_match.group(2))
                if 0.0 <= value <= 2.0:
                    result.sql_patch = f"UPDATE physics_interaction_params SET param_value={value:.2f} WHERE param_key='{key}';"
                    changed = True

    existing_suggestions = [str(item).strip() for item in (result.tuning_suggestions or []) if str(item).strip()]
    if not existing_suggestions:
        ten_gods = r"(比肩|劫财|食神|伤官|正财|偏财|正官|七杀|正印|偏印|官杀)"
        down_pattern = re.compile(rf"{ten_gods}(?:\s*(?:应该|应当|应))?\s*(降到|降为)\s*([0-9]{{1,3}}(?:\.[0-9]+)?)", flags=re.IGNORECASE)
        up_pattern = re.compile(rf"{ten_gods}(?:\s*(?:应该|应当|应))?\s*(升到|升为|提高到)\s*([0-9]{{1,3}}(?:\.[0-9]+)?)", flags=re.IGNORECASE)
        extracted: List[str] = []
        for match in down_pattern.finditer(text):
            extracted.append(f"正文提取：{match.group(1)} 目标{match.group(2)}{match.group(3)}（用于对齐物理现实）")
        for match in up_pattern.finditer(text):
            extracted.append(f"正文提取：{match.group(1)} 目标{match.group(2)}{match.group(3)}（用于对齐物理现实）")
        if extracted:
            result.tuning_suggestions = extracted[:5]
            changed = True

    if not result.diagnosis:
        result.diagnosis = "语义修补：由正文提取关键字段后完成结构化补全。"
        changed = True

    return result, changed


def sql_filter(sql_patch: str) -> str:
    sql = (sql_patch or "").strip()
    if not sql:
        return ""
    if "--" in sql or "/*" in sql or "*/" in sql or sql.count(";") > 1:
        return ""
    pattern = re.compile(
        r"^UPDATE\s+physics_interaction_params\s+SET\s+param_value\s*=\s*([0-9]*\.?[0-9]+)\s+WHERE\s+param_key\s*=\s*'([A-Za-z0-9_]+)'\s*;?$",
        re.IGNORECASE,
    )
    match = pattern.match(sql)
    if not match:
        return ""
    value = float(match.group(1))
    key = match.group(2)
    if not (0.0 <= value <= 2.0):
        return ""
    return f"UPDATE physics_interaction_params SET param_value={value:.2f} WHERE param_key='{key}';"


def physics_snapshot(physics_tensor: Dict[str, Any]) -> str:
    deity = (physics_tensor.get("deity_scores", {}) if isinstance(physics_tensor, dict) else {}) or {}
    audit_log = (physics_tensor.get("audit_log", {}) if isinstance(physics_tensor, dict) else {}) or {}
    trace = (audit_log.get("trace", {}) if isinstance(audit_log, dict) else {}) or {}
    root_check = trace.get("root_check", {}) if isinstance(trace, dict) else {}
    meta = (physics_tensor.get("meta", {}) if isinstance(physics_tensor, dict) else {}) or {}
    self_score = float(deity.get("比肩", 0.0)) + float(deity.get("劫财", 0.0))
    root_state = "None" if bool(root_check.get("no_root")) else "Linked"
    season = str(meta.get("solar_term") or "derived")
    return f"[Self: {self_score:.1f} | Root: {root_state} | Season: {season}]"


