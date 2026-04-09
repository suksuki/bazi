"""Analysis service layer for translation, clash scanning, and verdict orchestration."""
from __future__ import annotations

import json
import time
from typing import Any, Dict, List

from sqlmodel import select

from app.plugins.blind_school.core import run_blind_school_plugin
from app.core.plugins.registry import PluginRegistry
from app.api.contracts import AnalyzeClashRequest, AnalyzeSeedRequest, FinalVerdictRequest, TranslateRequest
from app.api.router_helpers import apply_energy_preview, guess_text_lang, physics_snapshot
from app.core.runtime_config import get_runtime_config
from app.core.scanner import Scanner
from app.db.models import SessionConsensus
from app.llm.client import QwenClient, build_first_observation_messages
from app.schemas.bazi_metadata import BaziMetadata, FlowState
from app.schemas.bazi_metadata import FourPillars
from app.services.helpers.analysis_helpers import (
    build_seed_audit_summary,
    build_translation_messages,
    fallback_clash_prompt,
    normalize_translation_texts,
    parse_translation_response,
)
from app.services.helpers.interaction_pipeline import evaluate_interactions
from app.skills.final_verdict import FinalVerdictSkill
from app.skills.physics_engine import PhysicsInferenceSkill
from app.skills.structure_final_decision import build_structure_final_decision_v0
from app.skills.structure_resolver_v0 import resolve_structure_candidates_v0
from app.skills.energy_topology_skill import EnergyTopologySkill


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
    evaluate_interactions(
        physics_tensor=physics_tensor,
        metadata=metadata_obj,
        interaction_params=physics_skill.get_interaction_params(),
        physics_config=body.physics_config.model_dump(exclude_none=True) if body.physics_config else {},
    )
    registry = PluginRegistry()
    plugin_outputs = registry.run_hook(
        hook="on_physics_complete",
        enabled_plugins=body.enabled_plugins,
        context={"physics_tensor": physics_tensor, "metadata": metadata_obj.model_dump()},
    )
    physics_tensor.setdefault("meta", {})
    if isinstance(physics_tensor.get("meta"), dict):
        physics_tensor["meta"]["enabled_plugins"] = list(body.enabled_plugins or [])
        physics_tensor["meta"]["plugin_specs"] = registry.list_specs()
    physics_tensor["plugin_outputs"] = plugin_outputs
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
    timeline = get_timeline_snapshot(
        body.date,
        body.time,
        body.calendar,
        1 if body.gender == "male" else 0,
    )
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
            enabled_plugins=body.enabled_plugins,
        )
    )
    metadata = result["metadata"]
    metadata["gender"] = body.gender
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
    clear_flag = bool(body.clear_previous_verdict or body.force_clear_cache)
    previous_verdict = "" if clear_flag else (body.previous_verdict or "")
    previous_logical_evidence = [] if clear_flag else (body.previous_logical_evidence or [])
    out = await skill.generate(
        metadata=body.metadata or {},
        physics_tensor=body.physics_tensor or {},
        selected_cards=body.selected_cards or [],
        consensus_history=consensus_history,
        previous_verdict=previous_verdict,
        previous_logical_evidence=previous_logical_evidence,
        lang=body.lang,
        plugin_weights=body.plugin_weights or {},
    )
    return {
        "ok": True,
        "version_id": out.get("version_id"),
        "verdict_body": out.get("verdict_body"),
        "change_log": out.get("change_log", []),
        "logical_evidence": out.get("logical_evidence", []),
        "work_vector": out.get("work_vector", {}),
        "topology_graph_v1": out.get("topology_graph_v1", {}),
        "structure_candidates_v0": out.get("structure_candidates_v0", {}),
        "structure_final_decision_v0": out.get("structure_final_decision_v0", {}),
        "plugin_outputs_verdict_ready": out.get("plugin_outputs_verdict_ready", {}),
        "plugin_conflict_report": out.get("plugin_conflict_report", {}),
        "audit_log": out.get("audit_log", {}),
    }


def _hit_rollback_triggers(triggers: List[str], self_abs: float, work_vector: Dict[str, Any]) -> List[str]:
    hits: List[str] = []
    risk = float(work_vector.get("backfire_risk", 0.0) or 0.0)
    gain = float(work_vector.get("unlock_gain", 0.0) or 0.0)
    released = float(work_vector.get("released_energy", 0.0) or 0.0)
    for t in triggers:
        line = str(t)
        if "Self_Abs > 1.2" in line and self_abs > 1.2:
            hits.append(line)
        elif "Self_Abs < 2.0" in line and self_abs < 2.0:
            hits.append(line)
        elif "released_energy > 6.0" in line and released > 6.0 and risk > gain * 0.5:
            hits.append(line)
        elif "net_effect == risk" in line and str(work_vector.get("net_effect")) == "risk":
            hits.append(line)
    return hits


async def run_stress_test(body: Any) -> Dict[str, Any]:
    metadata = body.metadata or {}
    pillars = metadata.get("pillars") or {}
    conflicts = ((metadata.get("conflict_matrix") or {}).get("points") or [])
    if not pillars:
        return {"ok": False, "detail": "metadata.pillars missing"}

    baseline_resp = await analyze_clash_flow(
        AnalyzeClashRequest(
            pillars=FourPillars(**pillars),
            lang=body.lang,
            physics_config=body.physics_config,
            enabled_plugins=body.enabled_plugins,
        )
    )
    stress_resp = await analyze_clash_flow(
        AnalyzeClashRequest(
            pillars=FourPillars(**pillars),
            lang=body.lang,
            dayun=body.luck_pillar,
            liunian=body.year_pillar,
            physics_config=body.physics_config,
            enabled_plugins=body.enabled_plugins,
        )
    )
    baseline_tensor = baseline_resp.get("physics_tensor", {}) or {}
    stress_tensor = stress_resp.get("physics_tensor", {}) or {}
    baseline_work = run_blind_school_plugin(physics_tensor=baseline_tensor, metadata=metadata)
    stress_work = run_blind_school_plugin(physics_tensor=stress_tensor, metadata=metadata)
    stress_topology = EnergyTopologySkill().produce({"metadata": metadata, "physics_tensor": stress_tensor})
    baseline_candidates = resolve_structure_candidates_v0(physics_tensor=baseline_tensor, work_vector=baseline_work)
    stress_candidates = resolve_structure_candidates_v0(physics_tensor=stress_tensor, work_vector=stress_work)
    baseline_decision = body.baseline_structure_final_decision or build_structure_final_decision_v0(
        structure_candidates_v0=baseline_candidates,
        work_vector=baseline_work,
    )
    stress_decision = build_structure_final_decision_v0(
        structure_candidates_v0=stress_candidates,
        work_vector=stress_work,
    )
    baseline_self_abs = float(baseline_candidates.get("self_abs", 0.0) or 0.0)
    stress_self_abs = float(stress_candidates.get("self_abs", 0.0) or 0.0)
    hit_triggers = _hit_rollback_triggers(
        list((baseline_decision or {}).get("rollback_triggers") or []),
        stress_self_abs,
        stress_work,
    )
    return {
        "ok": True,
        "gender": body.gender,
        "luck_pillar": body.luck_pillar,
        "year_pillar": body.year_pillar,
        "delta_abs": round(stress_self_abs - baseline_self_abs, 4),
        "structure_stability_shift": {
            "from": baseline_decision.get("stability_risk"),
            "to": stress_decision.get("stability_risk"),
        },
        "rollback_triggered": len(hit_triggers) > 0,
        "hit_triggers": hit_triggers,
        "stress_structure_final_decision_v0": stress_decision,
        "stress_topology_graph_v1": stress_topology,
        "stress_work_vector": stress_work,
        "baseline_conflicts_count": len(conflicts),
    }
