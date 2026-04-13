"""app.prompts 注册表与 LanguageEngine 回归。"""

from __future__ import annotations

import pytest

from app.prompts import CHAT_DEFAULT_SYSTEM_PROMPT, FIRST_OBSERVATION_SYSTEM_PROMPT, get_prompt, list_prompt_ids
from app.prompts.evolution_contracts import EVOLUTION_LEARNING_CONTEXT_RULE
from app.prompts.final_verdict_contracts import build_final_verdict_system_message
from app.prompts.language import LanguageEngine


def test_registry_lists_stable_ids() -> None:
    ids = list_prompt_ids()
    assert "chat.default_system" in ids
    assert "first_observation.system" in ids
    assert "physics_audit.schema_line" in ids
    assert "admin.conclusion_rewriter_system" in ids
    assert "evolution.learning_context_rule" in ids
    assert "evolution.physics_audit_high_sql_discipline" in ids
    assert "evolution.physics_audit_high_causal_trace" in ids
    assert get_prompt("chat.default_system") == CHAT_DEFAULT_SYSTEM_PROMPT
    assert get_prompt("evolution.learning_context_rule") == EVOLUTION_LEARNING_CONTEXT_RULE


def test_registry_unknown_raises() -> None:
    with pytest.raises(KeyError):
        get_prompt("does.not.exist")


def test_language_engine_structured_en_contains_chinese_logic() -> None:
    s = LanguageEngine.output_directive_for_structured_flow("EN")
    assert "英文" in s or "English" in s


def test_final_verdict_system_merges_heading_rules_into_json_contract_only() -> None:
    sys_hi = build_final_verdict_system_message(high_reasoning=True, lang="ZH")
    sys_lo = build_final_verdict_system_message(high_reasoning=False, lang="ZH")
    assert "[STRICT_JSON_ONLY]" in sys_hi
    assert "### 核心气象" in sys_hi
    assert "Final Narrator" in sys_hi
    assert "Verified Facts" in sys_lo and "VF01" in sys_lo
    assert FIRST_OBSERVATION_SYSTEM_PROMPT not in sys_hi
    assert "reasoning_feedback_loop" in sys_hi
    assert "Structural Observer" in FIRST_OBSERVATION_SYSTEM_PROMPT


def test_final_verdict_system_message_en_localizes_contract_headings() -> None:
    sys_en = build_final_verdict_system_message(high_reasoning=True, lang="EN")
    assert "[STRICT_JSON_ONLY]" in sys_en
    assert "### Core climate" in sys_en
    assert "Final Narrator" in sys_en
    assert "VF01" in sys_en
    assert "Please output strictly in English." in sys_en


def test_final_verdict_contract_polish_mode_inserts_contract_mode() -> None:
    s = build_final_verdict_system_message(high_reasoning=False, lang="ZH", contract_polish_mode=True)
    assert "[CONTRACT_MODE]" in s
    assert "语义润色代理" in s
    assert "VF01" in s
