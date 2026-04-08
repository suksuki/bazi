"""Analysis service layer for translation, clash scanning, and verdict orchestration."""
from __future__ import annotations

import json
import time
from typing import Any, Dict, List

from sqlmodel import select

from app.api.contracts import AnalyzeClashRequest, AnalyzeSeedRequest, FinalVerdictRequest, TranslateRequest
from app.api.router_helpers import apply_energy_preview, guess_text_lang, physics_snapshot
from app.core.runtime_config import get_runtime_config
from app.core.scanner import Scanner
from app.db.models import SessionConsensus
from app.llm.client import QwenClient, build_first_observation_messages
from app.schemas.bazi_metadata import BaziMetadata, FlowState
from app.services.helpers.analysis_helpers import (
    build_seed_audit_summary,
    build_translation_messages,
    fallback_clash_prompt,
    normalize_translation_texts,
    parse_translation_response,
)
from app.skills.final_verdict import FinalVerdictSkill
from app.skills.physics_engine import PhysicsInferenceSkill


async def translate_text_items(body: TranslateRequest) -> Dict[str, List[str]]:
    texts, can_return_directly = normalize_translation_texts(body.texts, body.target_lang, guess_text_lang)
    if can_return_directly:
        return {"items": texts}

    cfg = get_runtime_config().get("llm", {})
    client = QwenClient(
        base_url=cfg.get("base_url"),
        api_key=cfg.get("api_key"),
        model=cfg.get("model") or None,
    )
    raw = await client.chat(
        build_translation_messages(texts, body.target_lang),
        temperature=0.1,
        max_tokens=1500,
        stop=["Thinking Process:", "Reasoning:", "思考过程", "推理过程"],
    )
    return parse_translation_response(raw, texts)


async def analyze_clash_flow(body: AnalyzeClashRequest) -> Dict[str, Any]:
    matrix = Scanner().scan(body.pillars)
    metadata_obj = BaziMetadata(
        pillars=body.pillars,
        conflict_matrix=matrix,
        flow_state=FlowState.UNKNOWN,
        notes="已完成原子探测（六冲+六合）",
    )
    apply_energy_preview(metadata_obj)

    location_hint = ""
    if body.latitude is not None and body.longitude is not None:
        location_hint = f" 当前地理参考为纬度{body.latitude}、经度{body.longitude}。"

    cfg = get_runtime_config().get("llm", {})
    model_name = str(cfg.get("model") or "LLM")
    client = QwenClient(
        base_url=cfg.get("base_url"),
        api_key=cfg.get("api_key"),
        model=cfg.get("model") or None,
    )
    llm_elapsed_ms = 0.0
    llm_approx_tokens = 0.0
    t0 = time.perf_counter()
    try:
        llm_text = await client.chat(
            build_first_observation_messages(metadata_obj.model_dump(), location_hint=location_hint, lang=body.lang),
            temperature=0.3,
            max_tokens=512,
            stop=["Thinking Process:", "Reasoning:", "思考过程", "推理过程"],
        )
        llm_elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
        llm_approx_tokens = round(len(llm_text) / 1.8, 2)
    except Exception:
        llm_elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
        observed = [point.detail for point in metadata_obj.conflict_matrix.points]
        llm_text = fallback_clash_prompt(observed)

    physics_skill = PhysicsInferenceSkill.instance()
    consumed = physics_skill.consume(
        {
            "metadata": metadata_obj,
            "session_id": body.session_id,
            "dayun": body.dayun,
            "liunian": body.liunian,
            "physics_config": body.physics_config.model_dump(exclude_none=True) if body.physics_config else {},
        }
    )
    physics_tensor = physics_skill.produce(consumed)
    return {
        "metadata": metadata_obj.model_dump(),
        "llm_prompt": llm_text,
        "llm_meta": {
            "model_name": model_name,
            "elapsed_ms": llm_elapsed_ms,
            "approx_tokens": llm_approx_tokens,
        },
        "physics_tensor": physics_tensor,
    }


async def analyze_seed_flow(body: AnalyzeSeedRequest, get_bazi: Any, get_timeline_snapshot: Any, now_iso_value: str) -> Dict[str, Any]:
    pillars = get_bazi(body.date, body.time, body.calendar)
    timeline = get_timeline_snapshot(body.date, body.time, body.calendar)
    result = await analyze_clash_flow(
        AnalyzeClashRequest(
            pillars=pillars,
            latitude=body.latitude,
            longitude=body.longitude,
            lang=body.lang,
            session_id=body.session_id,
            dayun=(timeline or {}).get("dayun"),
            liunian=(timeline or {}).get("liunian"),
            physics_config=body.physics_config,
        )
    )
    metadata = result["metadata"]
    llm_meta = result.get("llm_meta", {})
    snapshot_summary = physics_snapshot(result.get("physics_tensor", {}) or {})
    result["audit_summary"] = build_seed_audit_summary(
        body,
        metadata,
        result["llm_prompt"],
        result.get("llm_meta", {}),
        result.get("physics_tensor", {}) or {},
        now_iso_value,
        snapshot_summary,
    )
    result["timeline"] = timeline
    return result


def load_consensus_history(session: Any, consultation_id: int | None) -> List[Dict[str, Any]]:
    if not consultation_id:
        return []
    rows = session.exec(select(SessionConsensus).where(SessionConsensus.session_id == consultation_id)).all()
    return [
        {
            "decision_key": str(row.decision_key or ""),
            "confirmed_value": float(row.confirmed_value) if row.confirmed_value is not None else None,
            "reasoning": str(row.reasoning or ""),
        }
        for row in rows
    ]


def resolve_consensus_history(
    *,
    explicit_history: List[Dict[str, Any]] | None,
    consultation_id: int | None,
    session_scope: Any,
) -> List[Dict[str, Any]]:
    history = list(explicit_history or [])
    if consultation_id and not history:
        try:
            with session_scope() as s:
                history = load_consensus_history(s, consultation_id)
        except Exception:
            history = []
    return history


async def generate_final_verdict(body: FinalVerdictRequest, consensus_history: List[Dict[str, Any]]) -> Dict[str, Any]:
    skill = FinalVerdictSkill.instance()
    out = await skill.generate(
        metadata=body.metadata or {},
        physics_tensor=body.physics_tensor or {},
        selected_cards=body.selected_cards or [],
        consensus_history=consensus_history,
        previous_verdict=body.previous_verdict or "",
        previous_logical_evidence=body.previous_logical_evidence or [],
        lang=body.lang,
    )
    return {
        "ok": True,
        "version_id": out.get("version_id"),
        "verdict_body": out.get("verdict_body"),
        "change_log": out.get("change_log", []),
        "logical_evidence": out.get("logical_evidence", []),
        "work_vector": out.get("work_vector", {}),
        "audit_log": out.get("audit_log", {}),
    }
