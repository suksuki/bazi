"""服务层导出。延迟加载，避免 skills ↔ analysis_service 循环导入。"""
from __future__ import annotations

import importlib
from typing import Any

__all__ = [
    "analyze_clash_flow",
    "analyze_seed_flow",
    "audit_physics_with_llm_flow",
    "build_audit_prompt_payload",
    "build_chat_messages",
    "confirm_structure_for_consultation",
    "create_consultation_record",
    "create_decision_step_record",
    "ensure_physics_tensor",
    "generate_final_verdict",
    "get_bazi",
    "get_timeline_snapshot",
    "list_history_items",
    "load_consensus_history",
    "rollback_decision_step_record",
    "run_chat_completion",
    "compose_realtime_narration",
    "stream_chat_events",
    "translate_text_items",
]

_LAZY_SUBMODULES = frozenset(
    {
        "analysis_service",
        "audit_service",
        "llm_service",
        "admin_service",
        "consultation_service",
        "bazi_engine",
    }
)


def __getattr__(name: str) -> Any:
    if name in _LAZY_SUBMODULES:
        return importlib.import_module(f"app.services.{name}")
    if name == "analyze_clash_flow":
        from app.services.analysis_service import analyze_clash_flow

        return analyze_clash_flow
    if name == "analyze_seed_flow":
        from app.services.analysis_service import analyze_seed_flow

        return analyze_seed_flow
    if name == "generate_final_verdict":
        from app.services.analysis_service import generate_final_verdict

        return generate_final_verdict
    if name == "load_consensus_history":
        from app.services.analysis_service import load_consensus_history

        return load_consensus_history
    if name == "translate_text_items":
        from app.services.analysis_service import translate_text_items

        return translate_text_items
    if name == "audit_physics_with_llm_flow":
        from app.services.audit_service import audit_physics_with_llm_flow

        return audit_physics_with_llm_flow
    if name == "build_audit_prompt_payload":
        from app.services.audit_service import build_audit_prompt_payload

        return build_audit_prompt_payload
    if name == "ensure_physics_tensor":
        from app.services.audit_service import ensure_physics_tensor

        return ensure_physics_tensor
    if name == "get_bazi":
        from app.services.bazi_engine import get_bazi

        return get_bazi
    if name == "get_timeline_snapshot":
        from app.services.bazi_engine import get_timeline_snapshot

        return get_timeline_snapshot
    if name == "confirm_structure_for_consultation":
        from app.services.consultation_service import confirm_structure_for_consultation

        return confirm_structure_for_consultation
    if name == "create_consultation_record":
        from app.services.consultation_service import create_consultation_record

        return create_consultation_record
    if name == "create_decision_step_record":
        from app.services.consultation_service import create_decision_step_record

        return create_decision_step_record
    if name == "list_history_items":
        from app.services.consultation_service import list_history_items

        return list_history_items
    if name == "rollback_decision_step_record":
        from app.services.consultation_service import rollback_decision_step_record

        return rollback_decision_step_record
    if name == "build_chat_messages":
        from app.services.llm_service import build_chat_messages

        return build_chat_messages
    if name == "run_chat_completion":
        from app.services.llm_service import run_chat_completion

        return run_chat_completion
    if name == "stream_chat_events":
        from app.services.llm_service import stream_chat_events

        return stream_chat_events
    if name == "compose_realtime_narration":
        from app.services.narrative.realtime_narrator import compose_realtime_narration

        return compose_realtime_narration
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
