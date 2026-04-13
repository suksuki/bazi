"""Helpers for qiazhi-bazi router orchestration."""
from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Dict, List

from app.schemas.bazi_metadata import BaziMetadata

from .contracts import AuditLlmStructuredResponse

from app.prompts.language import LanguageEngine
from app.prompts.physics_audit import build_physics_audit_messages


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
    """委托 LanguageEngine，保持函数名供路由与旧代码引用。"""
    return LanguageEngine.output_directive_for_structured_flow(lang)


def build_physics_audit_prompt(
    *,
    deity_scores: Dict[str, float],
    root_check: Dict[str, Any],
    climate_season_context: Dict[str, Any],
    consensus_history: List[Dict[str, Any]],
    lang: str,
    blind_skill_system_suffix: str = "",
    tier: str = "compact",
    high_reasoning: bool = False,
    inference_trace: Dict[str, Any] | None = None,
    conflict_points: List[Dict[str, Any]] | None = None,
    will_conflict_duel_context: str = "",
) -> List[Dict[str, str]]:
    """委托 ``app.prompts.physics_audit``，保留函数名供路由与审计服务。"""
    return build_physics_audit_messages(
        deity_scores=deity_scores,
        root_check=root_check,
        climate_season_context=climate_season_context,
        consensus_history=consensus_history,
        lang=lang,
        blind_skill_system_suffix=blind_skill_system_suffix,
        tier=tier,
        high_reasoning=high_reasoning,
        inference_trace=inference_trace,
        conflict_points=conflict_points,
        will_conflict_duel_context=will_conflict_duel_context,
    )


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
            kv_match = re.search(
                r"(CF_FLOATING_DECAY|A_PROTRUSION|OFFICER_RESTRAINT_ALPHA|POWER_DISTRIBUTION_GAMMA)\s*[:：=]\s*([0-9]*\.?[0-9]+)",
                text,
                flags=re.IGNORECASE,
            )
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


