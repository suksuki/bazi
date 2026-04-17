"""Analysis service layer for translation, clash scanning, and verdict orchestration."""
from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import time
import uuid
from datetime import datetime
from typing import Any, AsyncIterator, Awaitable, Callable, Dict, List, Mapping, Optional

from app.plugins.blind_school.core import run_blind_school_plugin
from app.api.contracts import (
    AnalyzeClashRequest,
    AnalyzeSeedRequest,
    BlindSchoolFeatureFlags,
    FinalVerdictRequest,
    HotReloadPhysicsRequest,
    TranslateRequest,
)
from app.api.router_helpers import guess_text_lang, physics_snapshot
from app.core.runtime_config import get_runtime_config
from app.core.scanner import Scanner
from app.llm.client import QwenClient
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
from app.services.helpers.audit_helpers import secondary_refresh_physics_tensor_before_final_verdict_v14_01
from app.services.helpers.tensor_adapters import (
    collect_conflict_matrix_points_for_llm,
    ensure_abs_nodes_on_physics_tensor,
)
from app.core.errors import DatabaseFetchError, V12SchemaViolationError
from app.db.models import BrainDissentLedger, BrainHtnSnapshot
from app.db.learning_ledger import sync_gold_training_set
from app.db.session import session_scope
from app.logic.brain.decision_hub import DecisionEvolutionFrameProtocol, NarrativeFragmentCollector
from app.logic.brain.hub import BrainHub
from app.logic.brain.seeds import KNOWLEDGE_SEEDS
from app.logic.brain.htn_domain import plan_htn_route
from app.services.orchestrator_service import OrchestratorService
from app.skills.final_verdict import FinalVerdictSkill
from app.services.helpers.l2_structure_bundle import build_structure_bundle_with_l2
from app.skills.energy_topology_skill import EnergyTopologySkill
from app.services.narrative.sanitizer import sanitize_fragment_text

_LOG = logging.getLogger(__name__)
_FACT_ID_BINDING_RE = re.compile(r"Fact_ID=([a-zA-Z0-9_-]+)")
_EVIDENCE_BLOCK_RE = re.compile(r"【证据】(?P<body>[\s\S]*?)(?:\n【|$)")

OrchestratorStatusHook = Optional[Callable[[str, str], Awaitable[None]]]


def _now_iso() -> str:
    return datetime.utcnow().isoformat()


def _as_dict(v: Any) -> Dict[str, Any]:
    return v if isinstance(v, dict) else {}


def _json_safe(value: Any, _seen: Optional[set[int]] = None) -> Any:
    """递归转为 JSON 安全结构，打断循环引用。"""
    seen = _seen if _seen is not None else set()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    oid = id(value)
    if oid in seen:
        return "[CIRCULAR_REF]"
    if isinstance(value, dict):
        seen.add(oid)
        out: Dict[str, Any] = {}
        for k, v in value.items():
            out[str(k)] = _json_safe(v, seen)
        seen.remove(oid)
        return out
    if isinstance(value, (list, tuple, set)):
        seen.add(oid)
        out = [_json_safe(x, seen) for x in value]
        seen.remove(oid)
        return out
    try:
        return str(value)
    except Exception:
        return "[UNSERIALIZABLE]"


def _ensure_messages_with_system(messages: Any, *, system_fallback: str) -> List[Dict[str, str]]:
    raw = messages if isinstance(messages, list) else []
    out: List[Dict[str, str]] = []
    for m in raw:
        if not isinstance(m, dict):
            continue
        role = str(m.get("role") or "").strip().lower()
        content = str(m.get("content") or "").strip()
        if not role or not content:
            continue
        out.append({"role": role, "content": content})
    if not out:
        out = [{"role": "system", "content": system_fallback}, {"role": "user", "content": "trace message unavailable"}]
    if not any(str(x.get("role") or "").lower() == "system" for x in out):
        out.insert(0, {"role": "system", "content": system_fallback})
    return out[:24]


def _collect_first_observation_trace(out: Dict[str, Any]) -> List[Dict[str, Any]]:
    fo = _as_dict(out.get("first_observation_llm"))
    msgs = fo.get("messages") if isinstance(fo.get("messages"), list) else []
    resp = str(fo.get("response_text") or "").strip()
    meta = _as_dict(fo.get("meta"))
    if not msgs and not resp and not meta:
        return []
    fact_ids: List[str] = []
    tree = _as_dict(out.get("assertion_tree"))
    nodes = tree.get("nodes") if isinstance(tree.get("nodes"), list) else []
    for n in nodes:
        if not isinstance(n, dict):
            continue
        nid = str(n.get("node_id") or "").strip()
        if nid:
            fact_ids.append(nid)
    return [
        {
            "trace_id": f"fo-{uuid.uuid4().hex[:10]}",
            "stage": "FIRST_OBSERVATION",
            "at": _now_iso(),
            "messages": _json_safe(_ensure_messages_with_system(msgs, system_fallback="FIRST_OBSERVATION_SYSTEM")),
            "response_text": resp,
            "llm_meta": _json_safe(meta),
            "fact_ids": fact_ids[:24],
        }
    ]


def _collect_arbiter_trace(out: Dict[str, Any]) -> List[Dict[str, Any]]:
    pt = _as_dict(out.get("physics_tensor"))
    meta = _as_dict(pt.get("meta"))
    feed = meta.get("arbitration_audit_feed_v1") if isinstance(meta.get("arbitration_audit_feed_v1"), list) else []
    rows: List[Dict[str, Any]] = []
    for i, row in enumerate(feed):
        if not isinstance(row, dict):
            continue
        prompt_raw = row.get("llm_prompt")
        msgs = prompt_raw if isinstance(prompt_raw, list) else []
        if not msgs and isinstance(prompt_raw, str) and prompt_raw.strip():
            msgs = [{"role": "user", "content": prompt_raw}]
        resp = str(row.get("llm_raw_response") or row.get("raw_response") or "").strip()
        if not msgs and not resp:
            continue
        fact_ids = []
        conflict = _as_dict(row.get("conflict"))
        ckind = str(conflict.get("kind") or "").strip()
        cdetail = str(conflict.get("detail") or "").strip()
        if ckind or cdetail:
            fact_ids.append(f"{ckind}:{cdetail}".strip(":"))
        rows.append(
            {
                "trace_id": str(row.get("audit_id") or f"arb-{i}-{uuid.uuid4().hex[:8]}"),
                "stage": "ARBITRATION",
                "at": str(row.get("timestamp") or _now_iso()),
                "messages": _json_safe(_ensure_messages_with_system(msgs, system_fallback="ARBITRATION_SYSTEM")),
                "response_text": resp,
                "llm_meta": _json_safe({
                    "decision": row.get("decision"),
                    "confidence": row.get("confidence"),
                    "reason": row.get("reason"),
                }),
                "fact_ids": fact_ids[:8],
            }
        )
    return rows


def _collect_final_verdict_trace(out: Dict[str, Any]) -> List[Dict[str, Any]]:
    msgs = out.get("llm_request_messages") if isinstance(out.get("llm_request_messages"), list) else []
    raw = str(out.get("llm_raw_response") or out.get("raw") or "").strip()
    rendered = str(out.get("verdict_body") or "").strip()
    meta = _as_dict(out.get("llm_meta"))
    if not msgs and not raw and not meta and not rendered:
        return []
    rows: List[Dict[str, Any]] = [
        {
            "trace_id": f"fv-{uuid.uuid4().hex[:10]}",
            "stage": "FINAL_VERDICT",
            "at": _now_iso(),
            "messages": _json_safe(_ensure_messages_with_system(msgs, system_fallback="FINAL_VERDICT_SYSTEM")),
            "response_text": raw,
            "rendered_verdict_body": rendered,
            "llm_meta": _json_safe(meta),
            "fact_ids": [str(x).strip() for x in (out.get("logical_evidence") or []) if str(x).strip()][:24],
        }
    ]
    evidence_block = ""
    m = _EVIDENCE_BLOCK_RE.search(rendered)
    if m:
        evidence_block = str(m.group("body") or "")
    fact_ids = list(dict.fromkeys([str(x).strip() for x in _FACT_ID_BINDING_RE.findall(evidence_block) if str(x).strip()]))
    if len(fact_ids) < 3:
        rows.append(
            {
                "trace_id": f"fv-audit-{uuid.uuid4().hex[:10]}",
                "stage": "AUDIT_DISSENT",
                "at": _now_iso(),
                "messages": _json_safe(
                    [
                        {"role": "system", "content": "FINAL_VERDICT_RENDER_AUDIT"},
                        {
                            "role": "user",
                            "content": "rendered_verdict_body 的【证据】段 Fact_ID 绑定不足，触发后置硬审计。",
                        },
                    ]
                ),
                "response_text": "FACT_ID_GUARD_REJECT",
                "rendered_verdict_body": rendered,
                "llm_meta": _json_safe(
                    {
                        "reason_code": "FACT_ID_BINDING_MISSING_IN_EVIDENCE_SECTION",
                        "detected_fact_ids": fact_ids,
                        "required_min": 3,
                        "fallback_applied": bool(
                            isinstance(meta, dict)
                            and (
                                str(meta.get("semantic_guard_fallback") or "").strip().upper() == "SCENE_ARCHITECT"
                                or str((_as_dict(meta.get("prompt_router")).get("scene") or "")).strip().upper()
                                == "SCENE_ARCHITECT"
                            )
                        ),
                    }
                ),
                "fact_ids": fact_ids,
            }
        )
    return rows


def _merge_logic_full_trace(metadata: Dict[str, Any], rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    md = dict(metadata or {})
    li = _as_dict(md.get("logic_introspection"))
    base = li.get("full_trace") if isinstance(li.get("full_trace"), list) else []
    merged: List[Dict[str, Any]] = []
    for x in base:
        if isinstance(x, dict):
            merged.append(x)
    for x in rows:
        if isinstance(x, dict):
            merged.append(x)
    li["full_trace"] = _json_safe(merged[-120:])
    md["logic_introspection"] = li
    return md


async def _orchestrator_status(hook: OrchestratorStatusHook, phase: str, message: str) -> None:
    """V13.05：计算心跳；失败不影响主链路。"""
    if hook is None:
        return
    try:
        await hook(phase, message)
    except Exception:
        _LOG.debug("update_orchestrator_status hook failed phase=%s", phase, exc_info=True)


def _pattern_summary_from_physics_meta(physics_tensor: Dict[str, Any]) -> str:
    """V13.02：从 physics_tensor.meta 抽取格局摘要，供 Node Chain 首观上下文。"""
    if not isinstance(physics_tensor, dict):
        return ""
    meta = physics_tensor.get("meta") if isinstance(physics_tensor.get("meta"), dict) else {}
    hit = str(meta.get("hit_pattern_name") or "").strip()
    l2 = str(meta.get("l2_pattern_result_summary_v1") or "").strip()
    parts = [p for p in (hit, l2) if p]
    if not parts:
        return ""
    return " | ".join(dict.fromkeys(parts))[:360]


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


def _build_fact_node_seeds(metadata_obj: BaziMetadata, physics_tensor: Dict[str, Any]) -> List[Dict[str, str]]:
    pat = _pattern_summary_from_physics_meta(physics_tensor)
    pat_prefix = f"【格局摘要】{pat} — " if pat else ""

    def _seed_body(core: str) -> str:
        body = f"{pat_prefix}{core}".strip()
        return body[:520] if len(body) > 520 else body

    points = list((metadata_obj.conflict_matrix.points or []))
    if not points:
        seed = _build_node_chain_seed(metadata_obj)
        return [
            {
                "node_id": "fact-0",
                "node_type": "FACT",
                "seed": _seed_body(seed),
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
                "seed": _seed_body(f"FACT_NODE: {text}"),
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


def _read_global_tension(physics_tensor: Dict[str, Any]) -> float:
    """V12.99：与插件 registry 的 global_conflict_tension 对齐；缺失时视为高张力（不触发误收敛）。"""
    meta = physics_tensor.get("meta") if isinstance(physics_tensor.get("meta"), dict) else {}
    raw = meta.get("global_conflict_tension")
    if isinstance(raw, (int, float)) and not isinstance(raw, bool):
        return max(0.0, min(1.0, float(raw)))
    return 1.0


def _core_dimensions_covered_for_convergence(*, bundle: Dict[str, Any], orchestration: Any) -> bool:
    """核心语义维度：verified_fact_lines 或 Hub VF 标签至少两条非空。"""
    vf_lines = bundle.get("verified_fact_lines") if isinstance(bundle.get("verified_fact_lines"), list) else []
    n_vf = len([str(x).strip() for x in vf_lines if str(x).strip()])
    if n_vf >= 2:
        return True
    tags = _extract_vf_tags(bundle)
    hub_tags = [str(x).strip() for x in (getattr(orchestration, "vf_tags", None) or []) if str(x).strip()]
    return len(tags) >= 2 or len(hub_tags) >= 2


def _merge_interrupt_request_atomic(
    *,
    orchestration: Any,
    loop_interrupt: Any,
    session_hint: Any,
) -> Any:
    """V12.93：PROBE_WAITING 必须与完整 interrupt_request 同事务出现；禁止“有状态无载荷”。"""
    if str(getattr(orchestration, "flow_state", "") or "").strip().upper() != "PROBE_WAITING":
        return loop_interrupt
    loop_ir = dict(loop_interrupt) if isinstance(loop_interrupt, dict) else {}
    hub_ir = dict(getattr(orchestration, "interrupt_request", None) or {})
    merged: Dict[str, Any] = {**hub_ir, **loop_ir}
    merged["state"] = "pending"
    pq = str(merged.get("probe_query") or getattr(orchestration, "probe_query", "") or "").strip()
    if not pq:
        sk = str(getattr(orchestration, "seed_key", "") or "").strip()
        pq = str((KNOWLEDGE_SEEDS.get(sk) or {}).get("probe_query") or "").strip()
    if not pq:
        pq = str(getattr(orchestration, "why_probe", "") or "").strip()
    if not pq:
        _LOG.error(
            "FATAL_LOGIC_SKEW code=ANALYZE_CLASH_PROBE_WAITING_EMPTY_PROBE session_hint=%s seed_key=%s loop_keys=%s",
            session_hint,
            getattr(orchestration, "seed_key", ""),
            sorted(loop_ir.keys()),
        )
        pq = "系统检测到逻辑断点，请确认后再继续终判。"
    merged["probe_query"] = pq[:520]
    merged["target_node_id"] = str(
        merged.get("target_node_id") or getattr(orchestration, "target_node_id", "") or "node:unknown"
    ).strip()
    if not str(merged.get("interrupt_id") or "").strip():
        merged["interrupt_id"] = str(hub_ir.get("interrupt_id") or f"skew-repair-{uuid.uuid4().hex[:12]}")
    if not str(merged.get("source") or "").strip():
        merged["source"] = str(hub_ir.get("source") or "brain_hub_orchestrate")
    rc = str(merged.get("reason_code") or "").strip()
    if not rc:
        merged["reason_code"] = str(getattr(orchestration, "seed_short", "") or getattr(orchestration, "seed_key", "") or "PROBE_PENDING")
    return merged


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


async def analyze_clash_flow(
    body: AnalyzeClashRequest,
    *,
    update_orchestrator_status: OrchestratorStatusHook = None,
) -> Dict[str, Any]:
    _tc = body.temporal_context if isinstance(body.temporal_context, dict) else {}
    _scene = str(
        _tc.get("scene")
        or (_as_dict(_tc.get("prompt_router")).get("scene"))
        or ""
    ).strip().upper()
    if _scene in {"SCENE_OBSERVE", "OBSERVE"}:
        return {}
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
    await _orchestrator_status(update_orchestrator_status, "PHASE_PHYSICS", "解析天干地支能量场...")
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
    await _orchestrator_status(update_orchestrator_status, "PHASE_PLUGINS", "多维命理插件博弈中...")
    metadata_obj = loop_out["metadata"]
    physics_tensor = loop_out["physics_tensor"]
    two_stage_resume_boost = False
    resume_hist_for_hub: List[Any] = []
    try:
        _raw_sid = getattr(body, "session_id", None)
        _sid_int = int(_raw_sid) if _raw_sid is not None else 0
    except (TypeError, ValueError):
        _sid_int = 0
    if _sid_int > 0:
        try:
            from app.db.models import Consultation
            from app.db.session import session_scope

            with session_scope() as db:
                cons = db.get(Consultation, _sid_int)
                if cons and isinstance(cons.input_meta, dict):
                    pl0 = cons.input_meta.get("persistence_layer") or {}
                    if isinstance(pl0, dict):
                        rh0 = pl0.get("resume_feedback_history")
                        if isinstance(rh0, list):
                            resume_hist_for_hub = list(rh0)
                            if len(rh0) >= 1:
                                two_stage_resume_boost = True
        except Exception:
            _LOG.debug("v1301 resume_feedback_history preload skipped", exc_info=True)
    if two_stage_resume_boost and isinstance(physics_tensor, dict):
        meta_ts = physics_tensor.setdefault("meta", {})
        if isinstance(meta_ts, dict):
            meta_ts["global_conflict_tension"] = 0.0
            meta_ts["v1301_two_stage_convergence_v1"] = True
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
    node_seeds = _build_fact_node_seeds(metadata_obj, physics_tensor if isinstance(physics_tensor, dict) else {})
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
        resume_feedback_history=resume_hist_for_hub,
        physics_tensor=physics_tensor if isinstance(physics_tensor, dict) else None,
    )
    md_p = metadata_obj.persistence_layer if isinstance(metadata_obj.persistence_layer, PersistenceLayer) else PersistenceLayer()
    if bool(getattr(orchestration, "finality_hammer_applied", False)):
        md_p = md_p.model_copy(update={"interrupt_request": {}})
        metadata_obj = metadata_obj.model_copy(update={"flow_state": FlowState.UNKNOWN, "persistence_layer": md_p})
        interrupt_request = {}
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
    llm_elapsed_ms = 0.0
    llm_approx_tokens = 0.0
    assertion_nodes: List[Dict[str, Any]] = []
    llm_lines: List[str] = []
    seed_hint = f"Target_Node_ID={orchestration.target_node_id};VF={','.join(orchestration.vf_tags[:2])};Seed={orchestration.seed_key}"
    _bundle_d = _bundle if isinstance(_bundle, dict) else {}
    _pt = physics_tensor if isinstance(physics_tensor, dict) else {}
    _gt0 = _read_global_tension(_pt)
    _core_ok0 = _core_dimensions_covered_for_convergence(bundle=_bundle_d, orchestration=orchestration)
    convergence_skip_secondary = _core_ok0 and (_gt0 < 0.2 or two_stage_resume_boost)
    await _orchestrator_status(update_orchestrator_status, "PHASE_SYNTHESIS", "汇聚意志，生成终审报告...")
    for idx, item in enumerate(node_seeds):
        if convergence_skip_secondary and idx > 0:
            _LOG.info(
                "v1299_convergence_gate: skip_non_core_node_chain idx=%s global_tension=%.4f core_ok=%s",
                idx,
                _gt0,
                _core_ok0,
            )
            break
        node_seed = str(item.get("seed") or "").strip()
        if not node_seed:
            node_seed = _build_node_chain_seed(metadata_obj)
        # V15.0: 废弃 First Observation 的首轮 LLM 定调，改为事实种子直连。
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

    v1299_probe_force_ready = False
    if convergence_skip_secondary and str(orchestration.flow_state or "").strip().upper() == "PROBE_WAITING":
        v1299_probe_force_ready = True
        orchestration = orchestration.model_copy(
            update={
                "flow_state": "READY",
                "probe_query": "",
                "why_probe": "",
                "interrupt_request": {},
            }
        )
        probe_started_at = ""
        metadata_obj = metadata_obj.model_copy(update={"flow_state": FlowState.UNKNOWN})
        htn_plan = plan_htn_route(
            {
                "has_raw_data": True,
                "has_clash_matrix": bool(conflict_points_payload),
                "logic_gap_detected": False,
                "introspection_clear": True,
                "will_assimilated": False,
                "seeds_matched": [orchestration.seed_short] if orchestration.seed_short else [],
            }
        )
        _LOG.info(
            "v1299_convergence_gate: force_ready flow_state global_tension=%.4f core_ok=%s two_stage=%s",
            _gt0,
            _core_ok0,
            two_stage_resume_boost,
        )

    if v1299_probe_force_ready:
        _v1307_meta = physics_tensor.setdefault("meta", {})
        if isinstance(_v1307_meta, dict):
            _v1307_meta["v1299_convergence_skip"] = True

    if v1299_probe_force_ready and llm_lines:
        _tag = "[逻辑共振确认]"
        if not str(llm_lines[0]).strip().startswith(_tag):
            llm_lines[0] = f"{_tag} {llm_lines[0]}".strip()
        if assertion_nodes and isinstance(assertion_nodes[0], dict):
            _t0 = str(assertion_nodes[0].get("text") or "")
            if not _t0.strip().startswith(_tag):
                assertion_nodes[0] = {**assertion_nodes[0], "text": f"{_tag} {_t0}".strip()}

    prompt_variant = "with_semantic_labels" if str(_label_hint or "").strip() else "minimal"
    llm_meta = {
        "model_name": model_name,
        "elapsed_ms": llm_elapsed_ms,
        "approx_tokens": llm_approx_tokens,
        "prompt_scenario": "Node_Chain_Execution",
        "prompt_variant": prompt_variant,
        "v1299_resonance_confirmation_tag": bool(v1299_probe_force_ready and llm_lines),
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
    out: Dict[str, Any] = {
        "metadata": metadata_obj.model_dump(),
        "llm_prompt": llm_text,
        "llm_meta": llm_meta,
        "assertion_tree": assertion_tree_preview,
        "physics_tensor": physics_tensor,
        "active_probing": active_probing,
        "interrupt_request": _merge_interrupt_request_atomic(
            orchestration=orchestration,
            loop_interrupt=interrupt_request,
            session_hint=getattr(body, "session_id", None),
        ),
        "psv_manifest": hub_preview.get("psv") or [],
        "brain_hub_preview": hub_preview,
        "logic_introspection": {
            "target_node_id": orchestration.target_node_id,
            "flow_state": orchestration.flow_state,
            "seed_key": orchestration.seed_key,
            "seed_short": orchestration.seed_short,
            "probe_query": orchestration.probe_query,
            "why_probe": orchestration.why_probe,
            "path": orchestration.introspection_path,
            "htn_tasks": orchestration.htn_tasks,
            "htn_plan": htn_plan,
            "probe_started_at": probe_started_at,
        },
    }
    _md_snapshot = _as_dict(out.get("metadata"))
    _append_shadow_snapshot_frame(
        _md_snapshot,
        state={
            "cursor": len(_as_dict(_md_snapshot).get("assertion_evolution_frames_v14") or []),
            "new_fragments": [],
        },
        physics_tensor=physics_tensor if isinstance(physics_tensor, dict) else {},
        skeleton_text=str(loop_out.get("verdict_skeleton") or ""),
    )
    out["metadata"] = _md_snapshot
    await _orchestrator_status(update_orchestrator_status, "PHASE_ARBITER", "AI 正在批量裁决逻辑分歧...")
    try:
        from app.services.helpers.v1294_silent_arbiter import maybe_apply_v1294_silent_arbiter_to_analyze_clash

        _raw_sid = getattr(body, "session_id", None)
        try:
            _sid = int(_raw_sid) if _raw_sid is not None else None
        except (TypeError, ValueError):
            _sid = None
        out = await maybe_apply_v1294_silent_arbiter_to_analyze_clash(
            out=out,
            session_id=_sid,
            lang=str(getattr(body, "lang", "zh") or "zh"),
            client=client,
        )
    except Exception:
        _LOG.debug("v1294 silent arbiter skipped", exc_info=True)
    md_full = _merge_logic_full_trace(
        _as_dict(out.get("metadata")),
        _collect_arbiter_trace(out),
    )
    out["metadata"] = md_full
    out["logic_introspection"] = _as_dict(md_full.get("logic_introspection"))
    return out


async def analyze_seed_flow(
    body: AnalyzeSeedRequest,
    get_bazi: Any,
    get_timeline_snapshot: Any,
    now_iso_value: str,
    *,
    update_orchestrator_status: OrchestratorStatusHook = None,
) -> Dict[str, Any]:
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
        ),
        update_orchestrator_status=update_orchestrator_status,
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
    return _json_safe(result)


async def hot_reload_physics_context(body: HotReloadPhysicsRequest) -> Dict[str, Any]:
    """V14：前端调整 physics_config / 插件开关后，重跑与 analyze-seed 相同的物理合成栈（analyze_clash_flow）。"""
    clash = AnalyzeClashRequest(
        pillars=body.pillars,
        latitude=body.latitude,
        longitude=body.longitude,
        lang=body.lang,
        session_id=body.session_id,
        dayun=body.dayun,
        liunian=body.liunian,
        physics_config=body.physics_config,
        enabled_plugins=list(body.enabled_plugins or []),
        blind_school_features=body.blind_school_features,
        temporal_context=body.temporal_context,
        request_id=body.request_id,
    )
    result = await analyze_clash_flow(clash)
    md = result.get("metadata")
    carry = body.metadata_carryover if isinstance(body.metadata_carryover, dict) else {}
    if isinstance(md, dict) and carry:
        result["metadata"] = _merge_metadata_hot_reload(md, carry)
    pt = result.get("physics_tensor")
    if isinstance(pt, dict):
        meta_pt = pt.setdefault("meta", {})
        if isinstance(meta_pt, dict):
            meta_pt["hot_reload_physics_at"] = datetime.utcnow().isoformat() + "Z"
            meta_pt["hot_reload_protocol"] = "v14.00"
    result["hot_reload"] = {"ok": True, "protocol": "hot_reload_physics.v14"}
    return _json_safe(result)


async def iter_analyze_seed_ndjson(
    body: AnalyzeSeedRequest,
    get_bazi: Any,
    get_timeline_snapshot: Any,
    now_iso_value: str,
) -> AsyncIterator[bytes]:
    """V13.05：以 NDJSON 流式输出 analyze-seed（phase 心跳 + 末帧 complete）。

    行协议：``{"type":"phase","phase":"PHASE_*","message":"…"}``，
    成功末行 ``{"type":"complete","data":{...}}``；失败 ``{"type":"error",...}``。
    """
    queue: asyncio.Queue[Optional[Dict[str, Any]]] = asyncio.Queue()

    async def hook(phase: str, message: str) -> None:
        await queue.put({"type": "phase", "phase": phase, "message": message})

    async def runner() -> None:
        try:
            data = await analyze_seed_flow(
                body,
                get_bazi,
                get_timeline_snapshot,
                now_iso_value,
                update_orchestrator_status=hook,
            )
            await queue.put({"type": "complete", "data": _json_safe(data)})
        except V12SchemaViolationError as exc:
            await queue.put(
                {
                    "type": "error",
                    "code": "V12_SCHEMA_VIOLATION_ERROR",
                    "detail": str(exc),
                    "pulse_id": getattr(exc, "pulse_id", None),
                }
            )
        except ValueError as exc:
            await queue.put({"type": "error", "code": "ANALYZE_SEED_INVALID_INPUT", "detail": str(exc)})
        except Exception as exc:
            _LOG.exception("iter_analyze_seed_ndjson failed")
            await queue.put({"type": "error", "detail": str(exc)})
        finally:
            await queue.put(None)

    task = asyncio.create_task(runner())
    try:
        while True:
            item = await queue.get()
            if item is None:
                break
            yield (json.dumps(item, ensure_ascii=False) + "\n").encode("utf-8")
    finally:
        await task


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


def _merge_metadata_hot_reload(base: Dict[str, Any], carry: Mapping[str, Any]) -> Dict[str, Any]:
    """热重载：将会话态字段合并回新计算的 metadata（浅合并 + 白名单 dict 深合并）。"""
    out = dict(base)
    deep_keys = frozenset({"incremental_context_v14", "iterative_verdict_v14", "m5_will_anchor_v14"})
    for k, v in carry.items():
        if k in deep_keys and isinstance(v, dict) and isinstance(out.get(k), dict):
            merged = dict(out[k])
            merged.update(v)
            out[k] = merged
        else:
            out[k] = v
    return out


def _tensor_bridge_fill_verified_fact_lines(physics_tensor: Dict[str, Any], metadata: Dict[str, Any]) -> None:
    """终判入口：若 VF 行不足，则从 conflict_matrix（及 tensor 回补点）动态补齐至少三行，避免「无可用 VF」空窗。"""
    meta_pt = physics_tensor.get("meta")
    if not isinstance(meta_pt, dict):
        return
    bundle = meta_pt.get("semantic_label_bundle_v1")
    if not isinstance(bundle, dict):
        bundle = {}
        meta_pt["semantic_label_bundle_v1"] = bundle
    vfp = bundle.get("verified_fact_lines")
    rows = [str(x).strip() for x in (vfp if isinstance(vfp, list) else []) if str(x).strip()]
    if len(rows) >= 3:
        return
    points = [p for p in collect_conflict_matrix_points_for_llm(metadata, physics_tensor, limit=48) if isinstance(p, dict)]
    need = 3 - len(rows)
    extra: List[str] = []
    for j in range(need):
        if points:
            p = points[j % len(points)]
            detail = str(p.get("detail") or "").strip()
            kind = str(p.get("kind") or "").strip()
            base = detail or kind or "冲突矩阵条目"
            slot = j % 3
            if slot == 0:
                extra.append(f"检测到物理冲突：{base}")
            elif slot == 1:
                extra.append(f"冲突矩阵记录：{base}")
            else:
                extra.append(f"盘面张力锚点：{base}")
        else:
            extra.append(f"检测到物理冲突：命盘已接入演算（补位 {j + 1}）")
    bundle["verified_fact_lines"] = rows + extra


def _physics_meta_final_verdict_probe_relaxed(physics_tensor: Mapping[str, Any]) -> bool:
    """V13.07：物理收敛已发生则放宽终判准入，避免过时的 PROBE_WAITING 假性锁死。"""
    meta = physics_tensor.get("meta") if isinstance(physics_tensor.get("meta"), dict) else {}
    if bool(meta.get("v1299_convergence_skip")):
        return True
    if bool(meta.get("v1301_two_stage_convergence_v1")):
        return True
    return False


def _build_antecedent_verdict_v0_5_from_fragments(metadata: Dict[str, Any]) -> str:
    rows = metadata.get("narrative_fragments_v14") if isinstance(metadata.get("narrative_fragments_v14"), list) else []
    frags = [str((x or {}).get("narrative_fragment") or "").strip() for x in rows if isinstance(x, dict)]
    frags = [x for x in frags if x]
    if not frags:
        return ""
    head = "【V0.5 初始断言】\n"
    body = "\n".join(f"- {x}" for x in frags[-6:])
    return f"{head}{body}"


def _collect_shadow_new_fragments(
    _metadata: Dict[str, Any],
    physics_tensor: Dict[str, Any],
) -> List[Dict[str, Any]]:
    rows = NarrativeFragmentCollector._collect_plugin_fact_rows(physics_tensor if isinstance(physics_tensor, dict) else {})
    out: List[Dict[str, Any]] = []
    for r in rows:
        frag = sanitize_fragment_text(str(r.get("narrative_fragment") or "").strip())
        if not frag:
            continue
        out.append(
            {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "source_id": str(r.get("source_id") or "plugin:unknown"),
                "narrative_fragment": frag,
            }
        )
    return out


def _fire_and_forget_emit_narrative(meta: Dict[str, Any], physics_tensor: Dict[str, Any]) -> None:
    try:
        asyncio.create_task(
            NarrativeFragmentCollector.collect_and_emit(
                meta,
                physics_tensor if isinstance(physics_tensor, dict) else {},
            )
        )
    except Exception:
        _LOG.debug("fire_and_forget_narrative_emit_failed", exc_info=True)


def _update_verdict_shadow_state_v15(
    metadata: Dict[str, Any],
    *,
    new_fragments: List[Dict[str, Any]],
    antecedent_v05: str,
) -> Dict[str, Any]:
    prev = metadata.get("Verdict_Shadow_State") if isinstance(metadata.get("Verdict_Shadow_State"), dict) else {}
    hist = list(prev.get("history") or []) if isinstance(prev.get("history"), list) else []
    for f in new_fragments[-12:]:
        if not isinstance(f, dict):
            continue
        hist.append(
            {
                "at": str(f.get("timestamp") or datetime.utcnow().isoformat() + "Z"),
                "source_id": str(f.get("source_id") or "plugin:unknown"),
                "fragment": str(f.get("narrative_fragment") or "")[:220],
            }
        )
    state = {
        "protocol": "verdict_shadow_state.v15",
        "cursor": int(prev.get("cursor") or 0) + len(new_fragments),
        "antecedent_v0_5": str(antecedent_v05 or "")[:1800],
        "new_fragments": hist[-24:],
        "history": hist[-120:],
    }
    metadata["Verdict_Shadow_State"] = state
    return state


def _append_shadow_snapshot_frame(
    metadata: Dict[str, Any],
    *,
    state: Dict[str, Any],
    physics_tensor: Optional[Dict[str, Any]] = None,
    skeleton_text: str = "",
) -> None:
    """V15.2：影子态更新后立即泵送 SNAPSHOT 帧，驱动前端实时显影。"""
    if not isinstance(metadata, dict):
        return
    sk = str(skeleton_text or "").strip()
    if not sk:
        va = metadata.get("verdict_anchor_layer") if isinstance(metadata.get("verdict_anchor_layer"), dict) else {}
        sk = str(va.get("verdict_skeleton") or "").strip()
    shadow_frags = state.get("new_fragments") if isinstance(state.get("new_fragments"), list) else []
    frag_lines = [str((x or {}).get("fragment") or "").strip() for x in shadow_frags if isinstance(x, dict)]
    frag_lines = [x for x in frag_lines if x][:3]
    sfd = metadata.get("structure_final_decision_v0") if isinstance(metadata.get("structure_final_decision_v0"), dict) else {}
    strat = sfd.get("strategic_advice") if isinstance(sfd.get("strategic_advice"), dict) else {}
    raw_use = sfd.get("utility_god")
    if not isinstance(raw_use, list):
        raw_use = strat.get("core_useful_gods")
    raw_taboo = sfd.get("obstacle_god")
    if not isinstance(raw_taboo, list):
        raw_taboo = strat.get("core_obstacle_gods")
    god_of_use = [str(x).strip() for x in (raw_use or []) if str(x).strip()][:6] if isinstance(raw_use, list) else []
    god_of_taboo = [str(x).strip() for x in (raw_taboo or []) if str(x).strip()][:6] if isinstance(raw_taboo, list) else []
    if not god_of_use or not god_of_taboo:
        va = metadata.get("verdict_anchor_layer") if isinstance(metadata.get("verdict_anchor_layer"), dict) else {}
        assertions = va.get("assertions") if isinstance(va.get("assertions"), list) else []
        for a in assertions:
            if not isinstance(a, dict):
                continue
            txt = str(a.get("text") or "").strip()
            if not txt:
                continue
            if not god_of_use and any(x in txt for x in ("宜", "有利", "可用")):
                god_of_use.append(txt[:24])
            if not god_of_taboo and any(x in txt for x in ("忌", "避", "谨防")):
                god_of_taboo.append(txt[:24])
            if god_of_use and god_of_taboo:
                break
    avs = metadata.get("active_verdict_skeleton") if isinstance(metadata.get("active_verdict_skeleton"), dict) else {}
    will_lines = [str(x).strip() for x in (avs.get("user_will_lines") or []) if str(x).strip()] if isinstance(avs.get("user_will_lines"), list) else []
    if not god_of_use and will_lines:
        god_of_use = [will_lines[0][:24]]
    p_scores = physics_tensor.get("deity_scores") if isinstance(physics_tensor, dict) and isinstance(physics_tensor.get("deity_scores"), dict) else {}
    if isinstance(p_scores, dict) and (not god_of_use or not god_of_taboo):
        ranked = sorted(
            [(str(k).strip(), float(v or 0.0)) for k, v in p_scores.items() if str(k).strip()],
            key=lambda kv: kv[1],
            reverse=True,
        )
        if ranked:
            if not god_of_use:
                god_of_use = [x[0] for x in ranked[:2]]
            if not god_of_taboo:
                god_of_taboo = [x[0] for x in ranked[-2:]]
    summary_lines: List[str] = []
    if sk:
        summary_lines.append(sk.replace("\n", " ")[:220])
    summary_lines.extend(frag_lines)
    if not summary_lines:
        return
    DecisionEvolutionFrameProtocol.append_frame(
        metadata,
        source_id="orchestrator_vf_refresh.snapshot",
        content_delta="\n".join(summary_lines[:4]),
        layer="SNAPSHOT",
        payload={
            "protocol": "verdict_shadow_snapshot.v15_2",
            "shadow_cursor": int(state.get("cursor") or 0),
            "skeleton_excerpt": sk[:220],
            "god_of_use": god_of_use,
            "god_of_taboo": god_of_taboo,
            "runtime_deity_map": p_scores if isinstance(p_scores, dict) else {},
            "render_text": sanitize_fragment_text(" ".join(summary_lines[:2])),
        },
    )


async def generate_final_verdict(body: FinalVerdictRequest, consensus_history: List[Dict[str, Any]]) -> Dict[str, Any]:
    md = body.metadata if isinstance(body.metadata, dict) else {}
    physics_tensor = body.physics_tensor or {}
    if not isinstance(physics_tensor, dict):
        raise ValueError("physics_tensor 必须为对象")
    if not isinstance(physics_tensor.get("meta"), dict):
        raise ValueError("physics_tensor.meta 缺失")
    _tensor_bridge_fill_verified_fact_lines(physics_tensor, md)
    fs = str(md.get("flow_state") or "").strip().lower()
    if fs == "probe_waiting" and not _physics_meta_final_verdict_probe_relaxed(physics_tensor):
        raise PermissionError("PROBE_PENDING：需先完成主动追问确认，终判阶段已锁定。")
    if "abs_nodes" not in physics_tensor:
        try:
            ensure_abs_nodes_on_physics_tensor(physics_tensor)
        except ValueError as exc:
            raise ValueError("physics_tensor.abs_nodes 缺失") from exc

    _sr = secondary_refresh_physics_tensor_before_final_verdict_v14_01(md, physics_tensor)
    if _sr.get("applied"):
        _LOG.debug("v14_01_secondary_physics_refresh applied=%s", _sr.get("applied_param_keys"))
        DecisionEvolutionFrameProtocol.append_frame(
            md,
            source_id="audit_helpers.secondary_refresh",
            content_delta=f"secondary_refresh:{','.join([str(x) for x in (_sr.get('applied_param_keys') or [])][:6])}",
            layer="PHYSICS",
            payload={"secondary_refresh": dict(_sr)},
        )
    _new_frags = _collect_shadow_new_fragments(md, physics_tensor if isinstance(physics_tensor, dict) else {})
    _fire_and_forget_emit_narrative(md, physics_tensor if isinstance(physics_tensor, dict) else {})
    antecedent_v05 = _build_antecedent_verdict_v0_5_from_fragments(md)
    if antecedent_v05:
        md["antecedent_verdict_v0_5"] = antecedent_v05
        DecisionEvolutionFrameProtocol.append_frame(
            md,
            source_id="analysis_service.antecedent_v0_5",
            content_delta=antecedent_v05.replace("\n", " ")[:500],
            layer="PLUGIN",
            payload={"protocol": "antecedent_verdict.v14_30"},
        )
    md["priority_overwrite_v14"] = DecisionEvolutionFrameProtocol.priority_overwrite_view(md)
    _shadow_state = _update_verdict_shadow_state_v15(md, new_fragments=_new_frags, antecedent_v05=antecedent_v05)
    _append_shadow_snapshot_frame(
        md,
        state=_shadow_state,
        physics_tensor=physics_tensor if isinstance(physics_tensor, dict) else {},
        skeleton_text=str((((physics_tensor.get("meta") or {}) if isinstance(physics_tensor, dict) else {}).get("verdict_skeleton") or "")),
    )

    skill = FinalVerdictSkill.instance()
    clear_flag = bool(body.clear_previous_verdict or body.force_clear_cache)
    previous_verdict = "" if clear_flag else (body.previous_verdict or "")
    previous_logical_evidence = [] if clear_flag else (body.previous_logical_evidence or [])
    reg_ctx = body.regeneration_context.model_dump() if body.regeneration_context is not None else None
    out = await skill.generate(
        metadata=md,
        physics_tensor=physics_tensor,
        selected_cards=body.selected_cards or [],
        consensus_history=consensus_history,
        previous_verdict=previous_verdict,
        previous_logical_evidence=previous_logical_evidence,
        lang=body.lang,
        plugin_weights=body.plugin_weights or {},
        regeneration_context=reg_ctx,
        mandatory_final_synthesis=bool(body.mandatory_final_synthesis),
        iterative_verdict_round=int(getattr(body, "iterative_verdict_round", 0) or 0),
    )
    patch = _as_dict(out.get("metadata_memory_patch"))
    md_in = body.metadata if isinstance(body.metadata, dict) else {}
    merged_md = _merge_logic_full_trace(dict(md_in), _collect_final_verdict_trace(out))
    patch["logic_introspection"] = _as_dict(merged_md.get("logic_introspection"))
    out["metadata_memory_patch"] = patch
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
    """NDJSON：多行 `{"type":"token","text":"..."}`，末行 `{"type":"complete","data":{...}}` 或 error。"""
    md = body.metadata if isinstance(body.metadata, dict) else {}
    physics_tensor = body.physics_tensor or {}
    if not isinstance(physics_tensor, dict):
        yield (json.dumps({"type": "error", "detail": "physics_tensor 必须为对象"}, ensure_ascii=False) + "\n").encode("utf-8")
        return
    if not isinstance(physics_tensor.get("meta"), dict):
        yield (json.dumps({"type": "error", "detail": "physics_tensor.meta 缺失"}, ensure_ascii=False) + "\n").encode("utf-8")
        return
    _tensor_bridge_fill_verified_fact_lines(physics_tensor, md)
    fs = str(md.get("flow_state") or "").strip().lower()
    if fs == "probe_waiting" and not _physics_meta_final_verdict_probe_relaxed(physics_tensor):
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
    if "abs_nodes" not in physics_tensor:
        try:
            ensure_abs_nodes_on_physics_tensor(physics_tensor)
        except ValueError as exc:
            yield (json.dumps({"type": "error", "detail": str(exc)}, ensure_ascii=False) + "\n").encode("utf-8")
            return

    _sr = secondary_refresh_physics_tensor_before_final_verdict_v14_01(md, physics_tensor)
    if _sr.get("applied"):
        _LOG.debug("v14_01_secondary_physics_refresh stream applied=%s", _sr.get("applied_param_keys"))
        DecisionEvolutionFrameProtocol.append_frame(
            md,
            source_id="audit_helpers.secondary_refresh.stream",
            content_delta=f"secondary_refresh_stream:{','.join([str(x) for x in (_sr.get('applied_param_keys') or [])][:6])}",
            layer="PHYSICS",
            payload={"secondary_refresh": dict(_sr)},
        )
    _new_frags = _collect_shadow_new_fragments(md, physics_tensor if isinstance(physics_tensor, dict) else {})
    _fire_and_forget_emit_narrative(md, physics_tensor if isinstance(physics_tensor, dict) else {})
    antecedent_v05 = _build_antecedent_verdict_v0_5_from_fragments(md)
    if antecedent_v05:
        md["antecedent_verdict_v0_5"] = antecedent_v05
        DecisionEvolutionFrameProtocol.append_frame(
            md,
            source_id="analysis_service.antecedent_v0_5.stream",
            content_delta=antecedent_v05.replace("\n", " ")[:500],
            layer="PLUGIN",
            payload={"protocol": "antecedent_verdict.v14_30"},
        )
    md["priority_overwrite_v14"] = DecisionEvolutionFrameProtocol.priority_overwrite_view(md)
    _shadow_state = _update_verdict_shadow_state_v15(md, new_fragments=_new_frags, antecedent_v05=antecedent_v05)
    _append_shadow_snapshot_frame(
        md,
        state=_shadow_state,
        physics_tensor=physics_tensor if isinstance(physics_tensor, dict) else {},
        skeleton_text=str((((physics_tensor.get("meta") or {}) if isinstance(physics_tensor, dict) else {}).get("verdict_skeleton") or "")),
    )

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
            if antecedent_v05:
                await queue.put({"type": "token", "text": antecedent_v05 + "\n\n"})
            out = await skill.generate(
                metadata=md,
                physics_tensor=physics_tensor,
                selected_cards=body.selected_cards or [],
                consensus_history=consensus_history,
                previous_verdict=previous_verdict,
                previous_logical_evidence=previous_logical_evidence,
                lang=body.lang,
                plugin_weights=body.plugin_weights or {},
                regeneration_context=reg_ctx,
                mandatory_final_synthesis=bool(body.mandatory_final_synthesis),
                iterative_verdict_round=int(getattr(body, "iterative_verdict_round", 0) or 0),
                stream_tokens=emit_tok,
            )
            patch = _as_dict(out.get("metadata_memory_patch"))
            md_in = body.metadata if isinstance(body.metadata, dict) else {}
            merged_md = _merge_logic_full_trace(dict(md_in), _collect_final_verdict_trace(out))
            patch["logic_introspection"] = _as_dict(merged_md.get("logic_introspection"))
            out["metadata_memory_patch"] = patch
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
