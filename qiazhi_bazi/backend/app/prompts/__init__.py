"""Qiazhi-Bazi 提示词单一事实来源（Registry + LanguageEngine）。"""

from app.prompts.admin_surface import ADMIN_CONCLUSION_COMPRESSOR_SYSTEM, ADMIN_CONCLUSION_REWRITER_SYSTEM
from app.prompts.audit import AUDIT_JSON_REPAIR_SYSTEM
from app.prompts.chat import CHAT_DEFAULT_SYSTEM_PROMPT
from app.prompts.first_observation import FIRST_OBSERVATION_SYSTEM_PROMPT
from app.prompts.language import LanguageEngine
from app.prompts.physics_audit_contracts import AUDIT_JSON_SCHEMA_LINE
from app.prompts.registry import get_prompt, list_prompt_ids
from app.prompts.translation import TRANSLATION_SYSTEM_PROMPT

__all__ = [
    "ADMIN_CONCLUSION_COMPRESSOR_SYSTEM",
    "ADMIN_CONCLUSION_REWRITER_SYSTEM",
    "AUDIT_JSON_REPAIR_SYSTEM",
    "AUDIT_JSON_SCHEMA_LINE",
    "CHAT_DEFAULT_SYSTEM_PROMPT",
    "FIRST_OBSERVATION_SYSTEM_PROMPT",
    "LanguageEngine",
    "TRANSLATION_SYSTEM_PROMPT",
    "get_prompt",
    "list_prompt_ids",
]
