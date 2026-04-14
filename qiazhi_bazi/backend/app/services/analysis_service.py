"""Analysis service layer for translation, clash scanning, and verdict orchestration."""
from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from datetime import datetime
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
from app.schemas.bazi_metadata import BaziMetadata, BrainHubPersistence, ConflictMatrix, FlowState, PersistenceLayer
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
from app.core.errors import DatabaseFetchError, V12SchemaViolationError
from app.db.models import BrainDissentLedger, BrainHtnSnapshot
from app.db.learning_ledger import sync_gold_training_set
from app.db.session import session_scope
from app.logic.brain.hub import BrainHub
from app.logic.brain.htn_domain import plan_htn_route
from app.services.orchestrator_service import OrchestratorService
from app.skills.final_verdict import FinalVerdictSkill
from app.services.helpers.l2_structure_bundle import build_structure_bundle_with_l2
from app.skills.energy_topology_skill import EnergyTopologySkill

_LOG = logging.getLogger(__name__)


def _build_node_chain_seed(metadata_obj: BaziMetadata) -> str:
    points = list((metadata_obj.conflict_matrix.points or []))
    focus = ""
    for p in points:
        d = str(getattr(p, "detail", "") or "").strip()
        if "寅巳" in d and ("穿" in d or "害" in d):
            focus = d
            break
    if not focus and points:
        focus = str(getattr(points[0], "detail", "") or "").strip()
    if not focus:
        focus = "局部冲合待复核"
    return f"FACT_NODE: {focus}"


def _build_fact_node_seeds(metadata_obj: BaziMetadata) -> List[Dict[str, str]]:
    points = list((metadata_obj.conflict_matrix.points or []))
    if not points:
        seed = _build_node_chain_seed(metadata_obj)
        return [
            {
                "node_id": "fact-0",
                "node_type": "FACT",
                "seed": seed,
                "evidence_ref": "node_chain_execution.fallback",
            }
        ]
    out: List[Dict[str, str]] = []
    for i, p in enumerate(points):
        detail = str(getattr(p, "detail", "") or "").strip()
        kind = str(getattr(p, "kind", "") or "").strip()
        text = detail or kind
        if not text:
            raise V12SchemaViolationError(
                f"Node_Chain_Execution 失败：冲突点[{i}] 未映射到 FACT_NODE。",
                pulse_id=f"pulse-node-missing-{i}",
            )
        out.append(
            {
                "node_id": f"fact-{i}",
                "node_type": "FACT",
                "seed": f"FACT_NODE: {text}",
                "evidence_ref": f"conflict_matrix.points[{i}]",
            }
        )
    return out


def _extract_vf_tags(bundle: Dict[str, Any]) -> List[str]:
    tags: List[str] = []
    if not isinstance(bundle, dict):
        return tags
    for k in ("verified_facts", "vf_tags", "labels"):
        raw = bundle.get(k)
        if isinstance(raw, list):
            tags.extend([str(x).strip() for x in raw if str(x).strip()])
    return tags[:3]


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
    active_probing = loop_out.get("active_probing") or {}
    interrupt_request = loop_out.get("interrupt_request") or {}

    from app.semantic_translator.labels import format_bundle_for_first_observation

    _label_hint = format_bundle_for_first_observation(_bundle) if isinstance(_bundle, dict) else ""

    client = QwenClient(
        base_url=cfg.get("base_url"),
        api_key=cfg.get("api_key"),
        model=cfg.get("model") or None,
    )
    node_seeds = _build_fact_node_seeds(metadata_obj)
    conflict_points_payload = []
    for p in list((metadata_obj.conflict_matrix.points or [])):
        conflict_points_payload.append({"kind": str(getattr(p, "kind", "") or ""), "detail": str(getattr(p, "detail", "") or "")})
    deity_scores = physics_tensor.get("deity_scores") if isinstance(physics_tensor, dict) else {}
    out_vec = 0.0
    if isinstance(deity_scores, dict):
        out_vec = float(deity_scores.get("食神", 0.0) or 0.0) + float(deity_scores.get("伤官", 0.0) or 0.0)
    self_abs = float((((physics_tensor.get("meta") or {}) if isinstance(physics_tensor, dict) else {}).get("self_abs", 0.0) or 0.0))
    hub = BrainHub()
    orchestration = hub.orchestrate(
        conflict_points=conflict_points_payload,
        verified_facts=_extract_vf_tags(_bundle if isinstance(_bundle, dict) else {}),
        user_confirmed=False,
        self_abs=self_abs,
        output_vector_present=out_vec > 0.0,
    )
    md_p = metadata_obj.persistence_layer if isinstance(metadata_obj.persistence_layer, PersistenceLayer) else PersistenceLayer()
    bh_meta = md_p.brain_hub if isinstance(md_p.brain_hub, BrainHubPersistence) else BrainHubPersistence()
    bh_meta = bh_meta.model_copy(
        update={
            "lineage": "HTN_DRIVEN",
            "seeds_matched": [orchestration.seed_short] if orchestration.seed_short else [],
            "htn_plan": orchestration.htn_plan,
        }
    )
    md_p = md_p.model_copy(update={"brain_hub": bh_meta})
    metadata_obj = metadata_obj.model_copy(update={"persistence_layer": md_p})
    if orchestration.flow_state == "PROBE_WAITING":
        metadata_obj = metadata_obj.model_copy(update={"flow_state": FlowState.PROBE_WAITING})
    htn_plan = plan_htn_route(
        {
            "has_raw_data": True,
            "has_clash_matrix": bool(conflict_points_payload),
            "logic_gap_detected": orchestration.flow_state == "PROBE_WAITING",
            "introspection_clear": orchestration.flow_state != "PROBE_WAITING",
            "will_assimilated": False,
            "seeds_matched": [orchestration.seed_short] if orchestration.seed_short else [],
        }
    )
    probe_started_at = datetime.utcnow().isoformat() if orchestration.flow_state == "PROBE_WAITING" else ""
    first_messages: List[Dict[str, str]] = []
    llm_elapsed_ms = 0.0
    llm_approx_tokens = 0.0
    assertion_nodes: List[Dict[str, Any]] = []
    llm_lines: List[str] = []
    seed_hint = f"Target_Node_ID={orchestration.target_node_id};VF={','.join(orchestration.vf_tags[:2])};Seed={orchestration.seed_key}"
    for idx, item in enumerate(node_seeds):
        node_seed = str(item.get("seed") or "").strip()
        if not node_seed:
            node_seed = _build_node_chain_seed(metadata_obj)
        node_messages = build_first_observation_messages(
            node_seed,
            location_hint=location_hint,
            lang=body.lang,
            semantic_label_json=seed_hint if seed_hint.strip() else (_label_hint or None),
        )
        if idx == 0:
            first_messages = node_messages
        try:
            line_text, tel = await client.chat_with_telemetry(
                node_messages,
                temperature=0.3,
                max_tokens=256,
                stop=["Thinking Process:", "Reasoning:", "思考过程", "推理过程"],
            )
            llm_elapsed_ms += float(tel.get("elapsed_ms") or 0.0)
            llm_approx_tokens += float(tel.get("approx_tokens") or 0.0)
        except Exception:
            line_text = node_seed
        line_text = str(line_text or "").strip()[:220]
        if not line_text:
            line_text = str(node_seed or "FACT_NODE: 局部结构待复核").strip()[:220]
            req_id = str(getattr(body, "request_id", "") or "").strip() or "NO_REQUEST_ID"
            node_id = str(item.get("node_id") or f"fact-{idx}")
            _LOG.warning(
                "node_chain_execution empty output fallback applied node_id=%s request_id=%s",
                node_id,
                req_id,
            )
        llm_lines.append(line_text)
        assertion_nodes.append(
            {
                "node_id": str(item.get("node_id") or f"fact-{idx}"),
                "node_type": "FACT",
                "text": line_text,
                "evidence_refs": [str(item.get("evidence_ref") or f"conflict_matrix.points[{idx}]")],
            }
        )

    prompt_variant = "with_semantic_labels" if str(_label_hint or "").strip() else "minimal"
    llm_meta = {
        "model_name": model_name,
        "elapsed_ms": llm_elapsed_ms,
        "approx_tokens": llm_approx_tokens,
        "prompt_scenario": "Node_Chain_Execution",
        "prompt_variant": prompt_variant,
    }
    assertion_tree_preview = {
        "protocol": "assertion_tree.v1",
        "root_id": "root",
        "nodes": assertion_nodes,
        "edges": [],
    }
    llm_text = "\n".join(llm_lines).strip()
    hub_preview: Dict[str, Any] = {"psv": [], "audit": {"audit_state": "PASS", "reason_code": "PASS", "is_passed": True}}
    try:
        ctx = hub.build_context(
            metadata=metadata_obj.model_dump(),
            physics_tensor=physics_tensor,
            user_intention=str(getattr(metadata_obj, "user_intention", "") or ""),
        )
        audit = hub.audit(llm_text, ctx.psv_list)
        hub_preview = {
            "psv": [s.model_dump() for s in ctx.psv_list],
            "audit": audit.model_dump(),
        }
    except Exception:
        _LOG.debug("analyze_clash brain_hub_preview skipped", exc_info=True)
    return {
        "metadata": metadata_obj.model_dump(),
        "llm_prompt": llm_text,
        "llm_meta": llm_meta,
        "first_observation_llm": {
            "messages": first_messages,
            "response_text": llm_text,
            "meta": {
                **dict(llm_meta),
                "logic_introspection": {
                    "target_node_id": orchestration.target_node_id,
                    "flow_state": orchestration.flow_state,
                    "seed_key": orchestration.seed_key,
                    "seed_short": orchestration.seed_short,
                    "why_probe": orchestration.why_probe,
                    "path": orchestration.introspection_path,
                    "htn_tasks": orchestration.htn_tasks,
                    "htn_plan": htn_plan,
                    "probe_started_at": probe_started_at,
                },
            },
        },
        "assertion_tree": assertion_tree_preview,
        "physics_tensor": physics_tensor,
        "active_probing": active_probing,
        "interrupt_request": (
            {
                **dict(interrupt_request),
                "state": "pending",
                "reason_code": str(interrupt_request.get("reason_code") or orchestration.seed_key or "PROBE_PENDING"),
                "probe_query": orchestration.probe_query,
                "target_node_id": orchestration.target_node_id,
            }
            if orchestration.flow_state == "PROBE_WAITING"
            else interrupt_request
        ),
        "psv_manifest": hub_preview.get("psv") or [],
        "brain_hub_preview": hub_preview,
        "logic_introspection": {
            "target_node_id": orchestration.target_node_id,
            "flow_state": orchestration.flow_state,
            "seed_key": orchestration.seed_key,
            "seed_short": orchestration.seed_short,
            "why_probe": orchestration.why_probe,
            "path": orchestration.introspection_path,
            "htn_tasks": orchestration.htn_tasks,
            "htn_plan": htn_plan,
            "probe_started_at": probe_started_at,
        },
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
            request_id=getattr(body, "request_id", None),
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
        "brain_hub": out.get("brain_hub") or {},
        "narrative_strategy": str(out.get("narrative_strategy") or ""),
        "assertion_tree": out.get("assertion_tree") or {},
    }


def _validate_final_verdict_schema(out: Dict[str, Any]) -> None:
    tree = out.get("assertion_tree")
    nodes = tree.get("nodes") if isinstance(tree, dict) else None
    if not isinstance(nodes, list) or len(nodes) == 0:
        pulse_id = str(out.get("version_id") or f"pulse-{datetime.utcnow().isoformat()}")
        raise V12SchemaViolationError("assertion_tree 为空，禁止回退。", pulse_id=pulse_id)


def _persist_dissent_ledger_if_needed(out: Dict[str, Any], consultation_id: int | None) -> None:
    if str(os.getenv("QIAZHI_SKIP_DISSENT_LEDGER_PERSIST", "")).strip() in {"1", "true", "TRUE"}:
        return
    brain_hub = out.get("brain_hub") if isinstance(out.get("brain_hub"), dict) else {}
    audit = brain_hub.get("audit") if isinstance(brain_hub.get("audit"), dict) else {}
    if str(audit.get("audit_state") or "").upper() != "REJECT":
        return
    psv_raw = brain_hub.get("psv") if isinstance(brain_hub.get("psv"), list) else []
    row = BrainDissentLedger(
        session_id=consultation_id,
        pulse_id=str(out.get("version_id") or f"pulse-{datetime.utcnow().isoformat()}"),
        reason_code=str(audit.get("reason_code") or "UNKNOWN_REJECT"),
        ai_raw_text=str(out.get("llm_raw_response") or out.get("verdict_body") or ""),
        psv_manifest=[x for x in psv_raw if isinstance(x, dict)],
        audit_payload=audit,
    )
    try:
        with session_scope() as s:
            s.add(row)
    except Exception:
        _LOG.warning("brain_dissent_ledger persist skipped: db unavailable", exc_info=True)


def _persist_brain_snapshot_if_needed(out: Dict[str, Any], consultation_id: int | None) -> None:
    if str(os.getenv("QIAZHI_SKIP_DISSENT_LEDGER_PERSIST", "")).strip() in {"1", "true", "TRUE"}:
        return
    bh = out.get("brain_hub") if isinstance(out.get("brain_hub"), dict) else {}
    lineage = str(bh.get("lineage") or "").strip()
    if lineage != "HTN_DRIVEN":
        return
    htn_plan = bh.get("htn_plan") if isinstance(bh.get("htn_plan"), dict) else {}
    row = BrainHtnSnapshot(
        session_id=consultation_id,
        version_id=str(out.get("version_id") or ""),
        lineage=lineage,
        assimilated=bool(bh.get("assimilated") or len(list(bh.get("confirmed_facts") or [])) > 0),
        full_path=[str(x) for x in (htn_plan.get("plan") or []) if str(x).strip()] if isinstance(htn_plan, dict) else [],
        seeds_matched=[str(x) for x in (bh.get("seeds_matched") or []) if str(x).strip()],
        snapshot_payload={"htn_plan": htn_plan, "brain_hub": bh},
    )
    try:
        with session_scope() as s:
            s.add(row)
            s.flush()
            sync_gold_training_set(s)
    except Exception:
        _LOG.warning("brain_htn_snapshot persist skipped: db unavailable", exc_info=True)


async def generate_final_verdict(body: FinalVerdictRequest, consensus_history: List[Dict[str, Any]]) -> Dict[str, Any]:
    md = body.metadata if isinstance(body.metadata, dict) else {}
    if str(md.get("flow_state") or "").strip().lower() == "probe_waiting":
        raise PermissionError("PROBE_PENDING：需先完成主动追问确认，终判阶段已锁定。")
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
    _validate_final_verdict_schema(out)
    bh = out.get("brain_hub") if isinstance(out.get("brain_hub"), dict) else {}
    if str(bh.get("lineage") or "") != "HTN_DRIVEN":
        raise V12SchemaViolationError("非 HTN 血统输出，已阻断。", pulse_id="pulse-lineage-guard")
    hp = bh.get("htn_plan") if isinstance(bh.get("htn_plan"), dict) else {}
    if not isinstance(hp.get("plan"), list) or len(hp.get("plan") or []) == 0:
        raise V12SchemaViolationError("未经过 HTN_Planner 的终判输出，已阻断。", pulse_id="pulse-htn-planner-guard")
    _persist_dissent_ledger_if_needed(out, body.consultation_id)
    _persist_brain_snapshot_if_needed(out, body.consultation_id)
    return pack_final_verdict_http_response(out)


async def iter_final_verdict_ndjson(
    body: FinalVerdictRequest,
    consensus_history: List[Dict[str, Any]],
) -> AsyncIterator[bytes]:
    md = body.metadata if isinstance(body.metadata, dict) else {}
    if str(md.get("flow_state") or "").strip().lower() == "probe_waiting":
        yield (
            json.dumps(
                {
                    "type": "error",
                    "code": "FINAL_VERDICT_FLOW_STATE_CONFLICT",
                    "status_code": 409,
                    "detail": "PROBE_PENDING：需先完成主动追问确认，终判阶段已锁定。",
                },
                ensure_ascii=False,
            )
            + "\n"
        ).encode("utf-8")
        return
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
            _validate_final_verdict_schema(out)
            bh = out.get("brain_hub") if isinstance(out.get("brain_hub"), dict) else {}
            if str(bh.get("lineage") or "") != "HTN_DRIVEN":
                raise V12SchemaViolationError("非 HTN 血统输出，已阻断。", pulse_id="pulse-lineage-guard")
            hp = bh.get("htn_plan") if isinstance(bh.get("htn_plan"), dict) else {}
            if not isinstance(hp.get("plan"), list) or len(hp.get("plan") or []) == 0:
                raise V12SchemaViolationError("未经过 HTN_Planner 的终判输出，已阻断。", pulse_id="pulse-htn-planner-guard")
            _persist_dissent_ledger_if_needed(out, body.consultation_id)
            _persist_brain_snapshot_if_needed(out, body.consultation_id)
            await queue.put({"type": "complete", "data": pack_final_verdict_http_response(out)})
        except Exception as exc:
            if isinstance(exc, V12SchemaViolationError):
                await queue.put(
                    {
                        "type": "error",
                        "detail": str(exc),
                        "code": "V12_SCHEMA_VIOLATION_ERROR",
                        "pulse_id": exc.pulse_id,
                    }
                )
            else:
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
