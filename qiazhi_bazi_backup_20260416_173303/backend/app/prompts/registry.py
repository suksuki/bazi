"""提示词注册表：静态片段的唯一入口，便于审计与版本对比。"""

from __future__ import annotations

from typing import Final

from app.prompts.admin_surface import ADMIN_CONCLUSION_COMPRESSOR_SYSTEM, ADMIN_CONCLUSION_REWRITER_SYSTEM
from app.prompts.audit import AUDIT_JSON_REPAIR_SYSTEM
from app.prompts.chat import CHAT_DEFAULT_SYSTEM_PROMPT
from app.prompts.evolution_contracts import (
    EVOLUTION_LEARNING_CONTEXT_RULE,
    PHYSICS_AUDIT_HIGH_REASONING_CAUSAL_TRACE,
    PHYSICS_AUDIT_HIGH_REASONING_SQL_DISCIPLINE,
)
from app.prompts.first_observation import FIRST_OBSERVATION_SYSTEM_PROMPT
from app.prompts.physics_audit_contracts import AUDIT_JSON_SCHEMA_LINE
from app.prompts.translation import TRANSLATION_SYSTEM_PROMPT

_PROMPTS: Final[dict[str, str]] = {
    "chat.default_system": CHAT_DEFAULT_SYSTEM_PROMPT,
    "first_observation.system": FIRST_OBSERVATION_SYSTEM_PROMPT,
    "audit.json_repair_system": AUDIT_JSON_REPAIR_SYSTEM,
    "translation.system": TRANSLATION_SYSTEM_PROMPT,
    "physics_audit.schema_line": AUDIT_JSON_SCHEMA_LINE,
    "admin.conclusion_rewriter_system": ADMIN_CONCLUSION_REWRITER_SYSTEM,
    "admin.conclusion_compressor_system": ADMIN_CONCLUSION_COMPRESSOR_SYSTEM,
    # 终判已内联本段；Registry 保留副本供 diff/审计与非终判编排按需拼接。
    "evolution.learning_context_rule": EVOLUTION_LEARNING_CONTEXT_RULE,
    "evolution.physics_audit_high_sql_discipline": PHYSICS_AUDIT_HIGH_REASONING_SQL_DISCIPLINE,
    "evolution.physics_audit_high_causal_trace": PHYSICS_AUDIT_HIGH_REASONING_CAUSAL_TRACE,
}


def get_prompt(prompt_id: str) -> str:
    """按 ID 取静态提示词；未知 ID 抛 KeyError（避免静默回退）。"""
    return _PROMPTS[prompt_id]


def list_prompt_ids() -> tuple[str, ...]:
    return tuple(sorted(_PROMPTS.keys()))
