"""终判 LLM 请求：剔除审计/SQL/参数表 JSON，仅保留断言可用语义面。"""
from __future__ import annotations

import copy
import re
from typing import Any, Dict

_FORBIDDEN_KEYS = frozenset(
    {
        "logic_proposal",
        "sql_patch",
        "physics_interaction_params",
        "tuning_suggestions",
    }
)
_MAX_DEPTH = 20
_MAX_LIST = 200


def _looks_like_physics_sql(s: str) -> bool:
    u = s.upper()
    return "UPDATE" in u and "PHYSICS_INTERACTION" in u.replace(" ", "")


def _scrub_value(obj: Any, depth: int = 0) -> Any:
    if depth > _MAX_DEPTH:
        return {} if isinstance(obj, dict) else ([] if isinstance(obj, list) else obj)
    if isinstance(obj, dict):
        out: Dict[str, Any] = {}
        for k, v in obj.items():
            if k in _FORBIDDEN_KEYS:
                continue
            if str(k).lower() in _FORBIDDEN_KEYS:
                continue
            out[k] = _scrub_value(v, depth + 1)
        return out
    if isinstance(obj, list):
        return [_scrub_value(x, depth + 1) for x in obj[:_MAX_LIST]]
    if isinstance(obj, str):
        if _looks_like_physics_sql(obj):
            return "[已省略 SQL 参数草案—详见审计舱]"
        if len(obj) > 4000 and ("logic_proposal" in obj or '"sql_patch"' in obj):
            return obj[:800] + "…[已截断：含审计 JSON 碎片]"
        return obj
    return obj


def sanitize_metadata_for_verdict_llm(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """深拷贝并递归删除 logic_proposal / sql_patch / physics_interaction_params 等。"""
    if not isinstance(metadata, dict):
        return {}
    scrubbed = _scrub_value(copy.deepcopy(metadata), 0)
    return scrubbed if isinstance(scrubbed, dict) else {}


def shallow_physics_for_llm_evidence(physics_tensor: Dict[str, Any]) -> Dict[str, Any]:
    """供 [Physical Evidence] 脱水：去掉 meta 内试运行参数大块，避免弱模型失语。"""
    if not isinstance(physics_tensor, dict):
        return {}
    out = dict(physics_tensor)
    meta = out.get("meta")
    if isinstance(meta, dict):
        m2 = dict(meta)
        m2.pop("runtime_physics_config", None)
        m2.pop("physics_interaction_params", None)
        m2.pop("last_physics_audit", None)
        m2.pop("audit_chamber_sql_draft", None)
        out["meta"] = m2
    out.pop("interaction_params", None)
    return out


def scrub_previous_verdict_sql(text: str) -> str:
    """上一版终判正文中若夹带审计 SQL/JSON，做行级剔除。"""
    if not text or not isinstance(text, str):
        return ""
    lines: list[str] = []
    for line in text.split("\n"):
        tl = line.strip()
        if _looks_like_physics_sql(tl):
            continue
        if '"sql_patch"' in tl or '"logic_proposal"' in tl:
            continue
        if re.match(r"^\s*[`'\"]*\s*UPDATE\s+physics_interaction_params", tl, re.I):
            continue
        lines.append(line)
    return "\n".join(lines)[:24000]
