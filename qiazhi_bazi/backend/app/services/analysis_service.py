"""Analysis service layer for translation, clash scanning, and verdict orchestration."""
from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any, AsyncIterator, Dict, List

from app.plugins.blind_school.core import run_blind_school_plugin
from app.api.contracts import (
    AnalyzeClashRequest,
    AnalyzeSeedRequest,
    BlindSchoolFeatureFlags,
    FinalVerdictRequest,
    TranslateRequest,
)
from app.api.router_helpers import guess_text_lang, physics_snapshot
from app.core.runtime_config import get_runtime_config
from app.core.scanner import Scanner
from app.llm.client import QwenClient, build_first_observation_messages
from app.schemas.bazi_metadata import BaziMetadata, ConflictMatrix, FlowState
from app.schemas.bazi_metadata import FourPillars
from app.services.helpers.analysis_helpers import (
    build_seed_audit_summary,
    build_translation_messages,
    fallback_clash_prompt,
    normalize_translation_texts,
    parse_translation_response,
)
from app.services.helpers.session_consensus_query import fetch_latest_session_consensus_rows
from app.services.helpers.tensor_adapters import ensure_abs_nodes_on_physics_tensor
from app.core.errors import DatabaseFetchError
from app.services.orchestrator_service import OrchestratorService
from app.skills.final_verdict import FinalVerdictSkill
from app.services.helpers.l2_structure_bundle import build_structure_bundle_with_l2
from app.skills.energy_topology_skill import EnergyTopologySkill

_LOG = logging.getLogger(__name__)


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
    raw, _tel = await client.chat_with_telemetry(
        build_translation_messages(texts, body.target_lang),
        temperature=0.1,
        max_tokens=1500,
        stop=["Thinking Process:", "Reasoning:", "思考过程", "推理过程"],
    )
    return parse_translation_response(raw, texts)


async def analyze_clash_flow(body: AnalyzeClashRequest) -> Dict[str, Any]:
    matrix = Scanner().scan(body.pillars)
    points = list(matrix.points)
    blind_flags = (
        body.blind_school_features.model_dump()
        if body.blind_school_features
        else BlindSchoolFeatureFlags().model_dump()
    )
    if blind_flags.get("enable_pierce_harm", True) and "classical.blind_school.v1" in (body.enabled_plugins or []):
        from app.plugins.blind_school.mangpai_engine import scan_six_harm_points

        points.extend(scan_six_harm_points(body.pillars))
    metadata_obj = BaziMetadata(
        pillars=body.pillars,
        conflict_matrix=ConflictMatrix(points=points),
        flow_state=FlowState.UNKNOWN,
        notes="已完成原子探测（六冲+六合+盲派六穿可选）",
        temporal_context=body.temporal_context,
    )
    location_hint = ""
    if body.latitude is not None and body.longitude is not None:
        location_hint = f" 当前地理参考为纬度{body.latitude}、经度{body.longitude}。"

    cfg = get_runtime_config().get("llm", {})
    model_name = str(cfg.get("model") or "LLM")

    physics_cfg = body.physics_config.model_dump(exclude_none=True) if body.physics_config else {}
    loop_out = OrchestratorService.run_internal_loop(
        metadata_obj=metadata_obj,
        enabled_plugins=list(body.enabled_plugins or []),
        blind_school_features=blind_flags,
        physics_config=physics_cfg,
        session_id=body.session_id,
        dayun=body.dayun,
        liunian=body.liunian,
    )
    metadata_obj = loop_out["metadata"]
    physics_tensor = loop_out["physics_tensor"]
    _bundle = loop_out.get("semantic_label_bundle_v1") or {}

    from app.semantic_translator.labels import format_bundle_for_first_observation

    _label_hint = format_bundle_for_first_observation(_bundle) if isinstance(_bundle, dict) else ""

    client = QwenClient(
        base_url=cfg.get("base_url"),
        api_key=cfg.get("api_key"),
        model=cfg.get("model") or None,
    )
    first_messages = build_first_observation_messages(
        metadata_obj.model_dump(),
        location_hint=location_hint,
        lang=body.lang,
        semantic_label_json=_label_hint or None,
    )
    llm_elapsed_ms = 0.0
    llm_approx_tokens = 0.0
    try:
        llm_text, tel = await client.chat_with_telemetry(
            first_messages,
            temperature=0.3,
            max_tokens=512,
            stop=["Thinking Process:", "Reasoning:", "思考过程", "推理过程"],
        )
        llm_elapsed_ms = float(tel.get("elapsed_ms") or 0.0)
        llm_approx_tokens = float(tel.get("approx_tokens") or 0.0)
    except Exception:
        llm_elapsed_ms = 0.0
        llm_approx_tokens = 0.0
        observed = [point.detail for point in metadata_obj.conflict_matrix.points]
        llm_text = fallback_clash_prompt(observed)

    prompt_variant = "with_semantic_labels" if str(_label_hint or "").strip() else "minimal"
    llm_meta = {
        "model_name": model_name,
        "elapsed_ms": llm_elapsed_ms,
        "approx_tokens": llm_approx_tokens,
        "prompt_scenario": "first_observation",
        "prompt_variant": prompt_variant,
    }
    return {
        "metadata": metadata_obj.model_dump(),
        "llm_prompt": llm_text,
        "llm_meta": llm_meta,
        "first_observation_llm": {
            "messages": first_messages,
            "response_text": llm_text,
            "meta": dict(llm_meta),
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
        body.reference_year,
    )
    timeline_out: Dict[str, Any] = dict(timeline) if isinstance(timeline, dict) else {}
    eo = body.external_overrides if isinstance(getattr(body, "external_overrides", None), dict) else {}
    liu = str(timeline_out.get("liunian") or "")
    dy = str(timeline_out.get("dayun") or "")
    if eo.get("liunian_ganzhi"):
        liu = str(eo["liunian_ganzhi"]).strip()
        timeline_out["liunian"] = liu
    if eo.get("dayun_ganzhi"):
        dy = str(eo["dayun_ganzhi"]).strip()
        timeline_out["dayun"] = dy
    temporal_ctx: Dict[str, Any] = {
        "reference_year": body.reference_year,
        "liunian_ganzhi": liu or None,
        "dayun_ganzhi": dy or None,
    }
    result = await analyze_clash_flow(
        AnalyzeClashRequest(
            pillars=pillars,
            latitude=body.latitude,
            longitude=body.longitude,
            lang=body.lang,
            session_id=body.session_id,
            dayun=dy or None,
            liunian=liu or None,
            physics_config=body.physics_config,
            enabled_plugins=body.enabled_plugins,
            blind_school_features=body.blind_school_features,
            temporal_context=temporal_ctx,
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
    result["timeline"] = timeline_out
    return result


def load_consensus_history(session: Any, consultation_id: int | None) -> List[Dict[str, Any]]:
    if not consultation_id:
        return []
    return fetch_latest_session_consensus_rows(session, int(consultation_id))


def resolve_consensus_history(
    *,
    explicit_history: List[Dict[str, Any]] | None,
    consultation_id: int | None,
    session_scope: Any,
    rethrow_db: bool = False,
) -> List[Dict[str, Any]]:
    history = list(explicit_history or [])
    if consultation_id and not history:
        try:
            with session_scope() as s:
                history = load_consensus_history(s, consultation_id)
        except Exception as exc:
            _LOG.exception(
                "consensus_history_db_fetch_failed consultation_id=%s",
                consultation_id,
            )
            if rethrow_db:
                raise DatabaseFetchError("读取会话共识历史失败") from exc
            history = []
    return history


def pack_final_verdict_http_response(out: Dict[str, Any]) -> Dict[str, Any]:
    """与 POST /v1/final-verdict JSON 响应字段一致。

    ``hit_pattern_name``：L2 法典顶栏口径（与 ``physics_tensor.meta`` 同步）。
    ``structure_*_v0`` 键名仅为历史兼容，负载由 ``build_structure_bundle_with_l2`` 写入，不经过已移除的 V0 manifest 链。
    """
    return {
        "ok": True,
        "version_id": out.get("version_id"),
        "verdict_body": out.get("verdict_body"),
        "change_log": out.get("change_log", []),
        "logical_evidence": out.get("logical_evidence", []),
        "work_vector": out.get("work_vector", {}),
        "topology_graph_v1": out.get("topology_graph_v1", {}),
        "hit_pattern_name": out.get("hit_pattern_name", ""),
        "structure_candidates_v0": out.get("structure_candidates_v0", {}),
        "structure_final_decision_v0": out.get("structure_final_decision_v0", {}),
        "plugin_outputs_verdict_ready": out.get("plugin_outputs_verdict_ready", {}),
        "plugin_conflict_report": out.get("plugin_conflict_report", {}),
        "audit_log": out.get("audit_log", {}),
        "confirmed_decisions": out.get("confirmed_decisions", []),
        "llm_request_messages": out.get("llm_request_messages") or [],
        "llm_raw_response": str(out.get("llm_raw_response") or out.get("raw") or ""),
        "llm_meta": out.get("llm_meta") or {},
        "narrative_chunks": out.get("narrative_chunks") or [],
        "metadata_memory_patch": out.get("metadata_memory_patch") or {},
        "l1_junction_flags": out.get("l1_junction_flags") or {},
    }


async def generate_final_verdict(body: FinalVerdictRequest, consensus_history: List[Dict[str, Any]]) -> Dict[str, Any]:
    physics_tensor = body.physics_tensor or {}
    if not isinstance(physics_tensor, dict):
        raise ValueError("physics_tensor 必须为对象")
    if not isinstance(physics_tensor.get("meta"), dict):
        raise ValueError("physics_tensor.meta 缺失")
    if "abs_nodes" not in physics_tensor:
        try:
            ensure_abs_nodes_on_physics_tensor(physics_tensor)
        except ValueError as exc:
            raise ValueError("physics_tensor.abs_nodes 缺失") from exc

    skill = FinalVerdictSkill.instance()
    clear_flag = bool(body.clear_previous_verdict or body.force_clear_cache)
    previous_verdict = "" if clear_flag else (body.previous_verdict or "")
    previous_logical_evidence = [] if clear_flag else (body.previous_logical_evidence or [])
    reg_ctx = body.regeneration_context.model_dump() if body.regeneration_context is not None else None
    out = await skill.generate(
        metadata=body.metadata or {},
        physics_tensor=physics_tensor,
        selected_cards=body.selected_cards or [],
        consensus_history=consensus_history,
        previous_verdict=previous_verdict,
        previous_logical_evidence=previous_logical_evidence,
        lang=body.lang,
        plugin_weights=body.plugin_weights or {},
        regeneration_context=reg_ctx,
        mandatory_final_synthesis=bool(body.mandatory_final_synthesis),
    )
    return pack_final_verdict_http_response(out)


async def iter_final_verdict_ndjson(
    body: FinalVerdictRequest,
    consensus_history: List[Dict[str, Any]],
) -> AsyncIterator[bytes]:
    """NDJSON：多行 `{"type":"token","text":"..."}`，末行 `{"type":"complete","data":{...}}` 或 error。"""
    physics_tensor = body.physics_tensor or {}
    if not isinstance(physics_tensor, dict):
        yield (json.dumps({"type": "error", "detail": "physics_tensor 必须为对象"}, ensure_ascii=False) + "\n").encode("utf-8")
        return
    if not isinstance(physics_tensor.get("meta"), dict):
        yield (json.dumps({"type": "error", "detail": "physics_tensor.meta 缺失"}, ensure_ascii=False) + "\n").encode("utf-8")
        return
    if "abs_nodes" not in physics_tensor:
        try:
            ensure_abs_nodes_on_physics_tensor(physics_tensor)
        except ValueError as exc:
            yield (json.dumps({"type": "error", "detail": str(exc)}, ensure_ascii=False) + "\n").encode("utf-8")
            return

    skill = FinalVerdictSkill.instance()
    clear_flag = bool(body.clear_previous_verdict or body.force_clear_cache)
    previous_verdict = "" if clear_flag else (body.previous_verdict or "")
    previous_logical_evidence = [] if clear_flag else (body.previous_logical_evidence or [])
    reg_ctx = body.regeneration_context.model_dump() if body.regeneration_context is not None else None

    queue: asyncio.Queue = asyncio.Queue()

    async def emit_tok(s: str) -> None:
        await queue.put({"type": "token", "text": s})

    async def worker() -> None:
        try:
            out = await skill.generate(
                metadata=body.metadata or {},
                physics_tensor=physics_tensor,
                selected_cards=body.selected_cards or [],
                consensus_history=consensus_history,
                previous_verdict=previous_verdict,
                previous_logical_evidence=previous_logical_evidence,
                lang=body.lang,
                plugin_weights=body.plugin_weights or {},
                regeneration_context=reg_ctx,
                mandatory_final_synthesis=bool(body.mandatory_final_synthesis),
                stream_tokens=emit_tok,
            )
            await queue.put({"type": "complete", "data": pack_final_verdict_http_response(out)})
        except Exception as exc:
            await queue.put({"type": "error", "detail": str(exc)})
        finally:
            await queue.put(None)

    task = asyncio.create_task(worker())
    try:
        while True:
            item = await queue.get()
            if item is None:
                break
            yield (json.dumps(item, ensure_ascii=False) + "\n").encode("utf-8")
    finally:
        try:
            await task
        except Exception:
            _LOG.debug("final_verdict_stream_task_cleanup", exc_info=True)


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
    baseline_candidates, computed_baseline = build_structure_bundle_with_l2(
        physics_tensor=baseline_tensor, work_vector=baseline_work
    )
    stress_candidates, stress_decision = build_structure_bundle_with_l2(
        physics_tensor=stress_tensor, work_vector=stress_work
    )
    baseline_decision = body.baseline_structure_final_decision or computed_baseline
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
