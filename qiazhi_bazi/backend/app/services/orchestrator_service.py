"""系统中枢调度器：无 LLM 的物理闭环（插件 + 因果路由 + 语义 VF 标签）。"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, AsyncIterator, Callable, Dict, List, Optional, TypedDict

from app.core.evolution.dna_registry import append_routing_audit_item
from app.core.routing.causal_router import CausalRouter, load_routing_config
from app.schemas.bazi_metadata import BaziMetadata
from app.services.decision_inbox_plugin_service import apply_decision_inbox_pipeline
from app.services.helpers.sys_core_physics_plugin import SYS_CORE_PHYSICS_BUNDLE_SRC_KEY
from app.services.helpers.tensor_adapters import ensure_abs_nodes_on_physics_tensor
from app.services.helpers.interaction_pipeline import evaluate_interactions
from app.services.plugin_service import PluginService
from app.semantic_translator import attach_semantic_labels_to_physics_meta, build_verdict_skeleton
from app.logic.patterns.l2_summary import sanitize_pattern_headline_zh
from app.plugins.modern.will_proxy_v1 import apply_intention_physics_to_cfg, normalize_user_intention
from app.services.helpers.structural_preview_semantics import (
    build_structural_preview_pattern_alert_bundle,
    build_structural_preview_vf_payloads,
    normalize_structural_preview_hint,
)

_LOG = logging.getLogger(__name__)

EmitFn = Callable[[str, Dict[str, Any]], None]

_STRICT_ENGINE_V = "MANIFEST_V5.8_STRICT"


def _is_strict_manifest_pattern_rows(rows: Any) -> bool:
    """V6.9：仅带 L2 指纹的行视为合法水位线数据；禁止旧 SSE 形态混用。"""
    if not isinstance(rows, list) or len(rows) == 0:
        return False
    for r in rows:
        if not isinstance(r, dict):
            return False
        if str(r.get("engine_v") or "") != _STRICT_ENGINE_V:
            return False
        if "name" not in r or "progress" not in r:
            return False
    return True


def _float_dict(d: Any) -> Dict[str, float]:
    out: Dict[str, float] = {}
    if not isinstance(d, dict):
        return out
    for k, v in d.items():
        ks = str(k).strip()
        if not ks:
            continue
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            fv = float(v)
            if fv == fv:  # not NaN
                out[ks] = fv
    return out


def build_physics_update_payload(
    physics_tensor: Dict[str, Any],
    reference_metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """供 SSE `physics_update`：Abs（abs_nodes）与 Rel（deity_energy_axes）及仪表盘相关标量。"""
    meta = physics_tensor.get("meta") if isinstance(physics_tensor.get("meta"), dict) else {}
    axes = physics_tensor.get("deity_energy_axes") if isinstance(physics_tensor.get("deity_energy_axes"), dict) else {}
    scores = physics_tensor.get("deity_scores") if isinstance(physics_tensor.get("deity_scores"), dict) else {}
    abs_nodes = physics_tensor.get("abs_nodes") if isinstance(physics_tensor.get("abs_nodes"), dict) else {}
    ge = meta.get("global_entropy")
    conf = physics_tensor.get("confidence")
    params = meta.get("params") if isinstance(meta.get("params"), dict) else {}
    out: Dict[str, Any] = {
        "abs_nodes": _float_dict(abs_nodes),
        "deity_scores": _float_dict(scores),
        "deity_energy_axes": axes,
        "confidence": float(conf) if isinstance(conf, (int, float)) and not isinstance(conf, bool) else conf,
        "meta_params": params,
        "global_entropy": float(ge) if isinstance(ge, (int, float)) and not isinstance(ge, bool) and ge == ge else None,
    }
    try:
        ref = reference_metadata if isinstance(reference_metadata, dict) else {}
        if not ref and isinstance(meta, dict):
            ref = meta
        eng = str(meta.get("pattern_thresholds_engine") or "") if isinstance(meta, dict) else ""
        pt_meta = meta.get("pattern_thresholds") if isinstance(meta, dict) else None
        # V6.9：严禁 centroid/旧 SSE 水位线回退；无 L2 strict 产出则显式空态供前端 EMPTY/NO_DATA。
        if eng == "universal_manifest_v1" and _is_strict_manifest_pattern_rows(pt_meta):
            out["pattern_thresholds"] = list(pt_meta)
            out["pattern_thresholds_status"] = "OK"
        else:
            out["pattern_thresholds"] = []
            out["pattern_thresholds_status"] = "EMPTY_NO_DATA"
    except Exception:
        _LOG.debug("pattern_thresholds attach skipped", exc_info=True)
        out["pattern_thresholds"] = []
        out["pattern_thresholds_status"] = "EMPTY_NO_DATA"
    return out


def _audit_pulse_chunks(text: str, chunk_size: int = 96) -> List[str]:
    t = str(text or "").strip()
    if not t:
        return []
    if len(t) <= chunk_size:
        return [t]
    return [t[i : i + chunk_size] for i in range(0, len(t), chunk_size)]


class OrchestratorLoopResult(TypedDict, total=False):
    """`run_internal_loop` 返回值（物理定论包；不含任何 LLM 字段）。"""

    metadata: BaziMetadata
    physics_tensor: Dict[str, Any]
    plugin_outputs: Dict[str, Any]
    semantic_label_bundle_v1: Dict[str, Any]
    verified_fact_lines: List[str]
    verdict_skeleton: str
    requires_narrative_refresh: bool
    pre_injection_deity_display: Dict[str, Any]
    is_preview: bool
    preview_pattern_alert: str
    preview_pattern_alert_meta: Dict[str, Any]


class OrchestratorService:
    """
    内部循环：Scanner 已写入的 conflict_matrix + L1 物理引擎 + PluginService + SemanticTranslator。

    可独立调用：不触达 Qwen/OpenAI 等 LLM；输出完整 `physics_tensor`（含 VF 标签包）。
    """

    @staticmethod
    def run_internal_loop(
        *,
        metadata_obj: BaziMetadata,
        enabled_plugins: List[str],
        blind_school_features: Dict[str, Any],
        physics_config: Dict[str, Any],
        session_id: Optional[int] = None,
        dayun: Optional[str] = None,
        liunian: Optional[str] = None,
        plugin_service: Optional[PluginService] = None,
        emit: Optional[EmitFn] = None,
        is_preview: bool = False,
        structural_preview: Optional[Dict[str, Any]] = None,
    ) -> OrchestratorLoopResult:
        from app.core.config.physics_settings import resolve_physics_settings
        from app.services.helpers.will_conflict_duel import build_will_conflict_risk_lines
        from app.services.helpers.will_injection import (
            collect_will_physics_param_merges,
            compute_pre_injection_physics_bundle,
            inject_user_decisions,
            narrative_refresh_needed,
            snapshot_energy_state,
            temporal_will_stale_warnings,
            will_temporal_anchor_blocks_injection,
        )
        from app.skills.physics_engine import PhysicsInferenceSkill

        physics_skill = PhysicsInferenceSkill.instance()
        cfg_working: Dict[str, Any] = dict(physics_config or {})
        user_intention = normalize_user_intention(cfg_working.pop("user_intention", None))
        apply_intention_physics_to_cfg(cfg_working, user_intention)
        sid = None if is_preview else session_id
        sp_norm = normalize_structural_preview_hint(structural_preview) if is_preview else None

        md_for_patterns = metadata_obj.model_dump()
        if user_intention:
            md_for_patterns = {**md_for_patterns, "user_intention": user_intention}

        def _emit_phys(tensor: Dict[str, Any]) -> None:
            if emit is None:
                return
            pl = build_physics_update_payload(tensor, md_for_patterns)
            if is_preview:
                pl = {**pl, "is_preview": True}
            try:
                emit("physics_update", pl)
            except Exception:
                _LOG.debug("orchestrator emit physics_update failed", exc_info=True)

        phys_will, inter_will = collect_will_physics_param_merges(metadata_obj)
        baseline_snap = None
        pre_injection_display: Dict[str, Any] = {}
        # 无意志注塑时不做 baseline 双算，保持单次 consume→produce 主路径（低延迟）
        if phys_will or inter_will:
            try:
                baseline_snap, pre_injection_display = compute_pre_injection_physics_bundle(
                    metadata_obj=metadata_obj,
                    physics_config=cfg_working,
                    physics_skill=physics_skill,
                    session_id=sid,
                    dayun=dayun,
                    liunian=liunian,
                )
            except Exception:
                _LOG.debug("will_injection baseline snapshot skipped", exc_info=True)

        inj = inject_user_decisions(metadata_obj, cfg_working, request_dayun=dayun)
        consumed = physics_skill.consume(
            {
                "metadata": metadata_obj,
                "session_id": sid,
                "dayun": dayun,
                "liunian": liunian,
                "physics_config": cfg_working,
            }
        )
        inter_ov = dict(inj.get("interaction_overrides") or {})
        if inter_ov:
            merged_co = dict(consumed.get("consensus_overrides") or {})
            merged_co.update(inter_ov)
            consumed["consensus_overrides"] = merged_co
        physics_tensor: Dict[str, Any] = physics_skill.produce(consumed)
        evaluate_interactions(
            physics_tensor=physics_tensor,
            metadata=metadata_obj,
            interaction_params=physics_skill.get_interaction_params(),
            physics_config=cfg_working,
        )
        try:
            from app.services.helpers.metadata_enrichment import sync_metadata_pillar_energy_from_tensor

            sync_metadata_pillar_energy_from_tensor(metadata_obj, physics_tensor)
        except Exception:
            _LOG.debug("sync_metadata_pillar_energy_from_tensor skipped", exc_info=True)
        _emit_phys(physics_tensor)

        ps = plugin_service or PluginService()
        md_for_plugins: Dict[str, Any] = dict(metadata_obj.model_dump())
        if user_intention:
            md_for_plugins["user_intention"] = user_intention
        plugin_outputs = ps.run_on_physics_complete(
            enabled_plugins=enabled_plugins,
            physics_tensor=physics_tensor,
            metadata=md_for_plugins,
            blind_school_features=blind_school_features,
            is_preview=bool(is_preview),
            dry_run=bool(is_preview),
        )

        physics_tensor.setdefault("meta", {})
        if isinstance(physics_tensor.get("meta"), dict):
            physics_tensor["meta"]["enabled_plugins"] = list(enabled_plugins or [])
            physics_tensor["meta"]["plugin_specs"] = ps.list_specs()
            physics_tensor["meta"]["blind_school_features"] = blind_school_features
            blind_payload = (plugin_outputs.get("classical.blind_school.v1") or {}).get("payload") or {}
            chips = blind_payload.get("mangpai_chip_logs") or []
            if chips:
                physics_tensor["meta"]["mangpai_chip_logs"] = list(chips)
            hub_mangpai = blind_payload.get("interaction_hub_overlay_mangpai")
            if isinstance(hub_mangpai, dict) and hub_mangpai:
                physics_tensor["meta"]["interaction_hub_mangpai"] = dict(hub_mangpai)
            pierce_sem = blind_payload.get("mangpai_pierce_semantics")
            if isinstance(pierce_sem, list) and pierce_sem:
                physics_tensor["meta"]["mangpai_pierce_semantics"] = list(pierce_sem)

        try:
            meta_pt = physics_tensor.setdefault("meta", {})
            if isinstance(meta_pt, dict):
                eng = str(meta_pt.get("pattern_thresholds_engine") or "")
                pt_rows = meta_pt.get("pattern_thresholds")
                if eng == "universal_manifest_v1" and _is_strict_manifest_pattern_rows(pt_rows):
                    meta_pt["pattern_thresholds_status"] = "OK"
                else:
                    meta_pt["pattern_thresholds"] = []
                    meta_pt["pattern_thresholds_engine"] = "none"
                    meta_pt["pattern_thresholds_status"] = "EMPTY_NO_DATA"
                # V8.4.1：StreamBoard 顶栏「当前格局」以法典插件写入的
                # physics_tensor.meta.l2_pattern_result_summary_v1 / hit_pattern_name 为准；
                # 中枢不在此处用 structure_final_decision_v0 回填 pattern 标题。
                l2_line = str(meta_pt.get("l2_pattern_result_summary_v1") or "").strip()
                meta_pt["l2_pattern_result_summary_v1"] = sanitize_pattern_headline_zh(l2_line if l2_line else "常规格")
                meta_pt["hit_pattern_name"] = meta_pt["l2_pattern_result_summary_v1"]
        except Exception:
            _LOG.debug("pattern_thresholds meta cleanup skipped", exc_info=True)

        negotiated: Optional[Dict[str, Any]] = None
        try:
            negotiated = CausalRouter(routing_config=load_routing_config()).negotiate_impact(
                plugin_outputs,
                physics_tensor=physics_tensor,
            )
            meta = physics_tensor.get("meta")
            if isinstance(meta, dict):
                meta["causal_routing"] = negotiated
            append_routing_audit_item(physics_tensor, negotiated)
            if emit is not None and negotiated:
                try:
                    rd = str(negotiated.get("routing_decision") or "").strip()
                    for piece in _audit_pulse_chunks(rd):
                        emit("audit_pulse", {"fragment": piece})
                except Exception:
                    _LOG.debug("orchestrator emit audit_pulse failed", exc_info=True)
        except Exception:
            _LOG.debug("causal_router negotiate_impact skipped", exc_info=True)

        physics_tensor["plugin_outputs"] = plugin_outputs
        try:
            apply_decision_inbox_pipeline(physics_tensor=physics_tensor, plugin_outputs=plugin_outputs, registry=ps.registry)
        except Exception:
            _LOG.debug("apply_decision_inbox_pipeline skipped", exc_info=True)

        if not is_preview:
            try:
                from app.services.helpers.metadata_enrichment import (
                    attach_plugin_selection_trace_to_metadata,
                    build_plugin_selection_trace,
                )

                _pst = build_plugin_selection_trace(
                    registry=ps.registry, plugin_outputs=plugin_outputs, physics_tensor=physics_tensor
                )
                attach_plugin_selection_trace_to_metadata(metadata_obj, _pst)
            except Exception:
                _LOG.debug("plugin_selection_trace skipped", exc_info=True)

            try:
                from app.services.helpers.metadata_enrichment import attach_inference_trace_to_metadata, build_inference_trace

                _inf = build_inference_trace(physics_tensor=physics_tensor, plugin_outputs=plugin_outputs, registry=ps.registry)
                metadata_obj = attach_inference_trace_to_metadata(metadata_obj, _inf) or metadata_obj
            except Exception:
                _LOG.debug("inference_trace skipped", exc_info=True)

        try:
            if "abs_nodes" not in physics_tensor:
                ensure_abs_nodes_on_physics_tensor(physics_tensor)
        except ValueError:
            pass
        if isinstance(physics_tensor, dict):
            physics_tensor.pop(SYS_CORE_PHYSICS_BUNDLE_SRC_KEY, None)

        _emit_phys(physics_tensor)

        _settings = resolve_physics_settings(overrides=cfg_working)
        # SemanticTranslator：离散 VF 标签写入 physics_tensor.meta.semantic_label_bundle_v1
        attach_semantic_labels_to_physics_meta(physics_tensor, physics_settings=_settings)

        bundle: Dict[str, Any] = {}
        meta_out = physics_tensor.get("meta")
        if isinstance(meta_out, dict):
            raw = meta_out.get("semantic_label_bundle_v1")
            if isinstance(raw, dict):
                bundle = raw
        vf_lines = bundle.get("verified_fact_lines") if isinstance(bundle.get("verified_fact_lines"), list) else []
        verified = [str(x).strip() for x in vf_lines if str(x or "").strip()]

        if emit is not None and sp_norm:
            for row in build_structural_preview_vf_payloads(sp_norm):
                try:
                    emit(
                        "vf_discovered",
                        {
                            "line": row.get("line") or "",
                            "is_preview_structural": True,
                            "i18n_template": row.get("i18n_template"),
                            "i18n_params": row.get("i18n_params") or {},
                        },
                    )
                except Exception:
                    _LOG.debug("orchestrator emit vf_discovered structural preview failed", exc_info=True)
                    break

        if emit is not None:
            for ln in verified:
                try:
                    emit("vf_discovered", {"line": ln})
                except Exception:
                    _LOG.debug("orchestrator emit vf_discovered failed", exc_info=True)
                    break

        risk_lines = build_will_conflict_risk_lines(
            merged_physics_keys=set(phys_will.keys()),
            merged_interaction_keys=set(inter_will.keys()),
            plugin_outputs=plugin_outputs,
            physics_tensor=physics_tensor,
        )
        temporal_lines = temporal_will_stale_warnings(metadata_obj, request_dayun=dayun)
        anchor_blocked = will_temporal_anchor_blocks_injection(metadata_obj, request_dayun=dayun)
        skeleton_md = build_verdict_skeleton(verified, risk_lines=risk_lines, temporal_warnings=temporal_lines)
        val = metadata_obj.verdict_anchor_layer
        updated_layer = val.model_copy(update={"verdict_skeleton": skeleton_md})
        metadata_obj = metadata_obj.model_copy(update={"verdict_anchor_layer": updated_layer})

        if not is_preview:
            hc = metadata_obj.history_context
            la = dict(hc.learning_annotation or {})
            ent = list(la.get("entries") or [])
            snippet = " | ".join(verified[:5]) if verified else ""
            ent.append(
                {
                    "occurred_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
                    "kind": "orchestrator_vf_refresh",
                    "reason": f"中枢静默环：已验事实 {len(verified)} 条；verdict_skeleton 已同步。{snippet[:220]}",
                }
            )
            la["entries"] = ent[-200:]
            la.setdefault("schema", "learning_annotation.v1")
            metadata_obj = metadata_obj.model_copy(
                update={"history_context": hc.model_copy(update={"learning_annotation": la})}
            )

        requires_refresh = bool(anchor_blocked) and not is_preview
        if baseline_snap is not None and not is_preview:
            try:
                requires_refresh = requires_refresh or narrative_refresh_needed(
                    baseline_snap, snapshot_energy_state(physics_tensor)
                )
            except Exception:
                _LOG.debug("requires_narrative_refresh comparison skipped", exc_info=True)

        preview_alert = ""
        preview_pattern_alert_meta: Dict[str, Any] = {}
        if sp_norm:
            _bundle = build_structural_preview_pattern_alert_bundle(sp_norm, physics_tensor)
            preview_alert = str(_bundle.get("fallback_zh") or "")
            raw_meta = _bundle.get("i18n")
            preview_pattern_alert_meta = raw_meta if isinstance(raw_meta, dict) else {}

        out: OrchestratorLoopResult = {
            "metadata": metadata_obj,
            "physics_tensor": physics_tensor,
            "plugin_outputs": plugin_outputs,
            "semantic_label_bundle_v1": bundle,
            "verified_fact_lines": verified,
            "verdict_skeleton": skeleton_md,
            "requires_narrative_refresh": bool(requires_refresh),
            "pre_injection_deity_display": dict(pre_injection_display) if (phys_will or inter_will) else {},
            "is_preview": bool(is_preview),
            "preview_pattern_alert": preview_alert if is_preview else "",
            "preview_pattern_alert_meta": preview_pattern_alert_meta if is_preview else {},
        }
        return out


def run_internal_loop(
    *,
    metadata_obj: BaziMetadata,
    enabled_plugins: List[str],
    blind_school_features: Dict[str, Any],
    physics_config: Dict[str, Any],
    session_id: Optional[int] = None,
    dayun: Optional[str] = None,
    liunian: Optional[str] = None,
    plugin_service: Optional[PluginService] = None,
    emit: Optional[EmitFn] = None,
    is_preview: bool = False,
    structural_preview: Optional[Dict[str, Any]] = None,
) -> OrchestratorLoopResult:
    """模块级别名，等价于 `OrchestratorService.run_internal_loop`。"""
    return OrchestratorService.run_internal_loop(
        metadata_obj=metadata_obj,
        enabled_plugins=enabled_plugins,
        blind_school_features=blind_school_features,
        physics_config=physics_config,
        session_id=session_id,
        dayun=dayun,
        liunian=liunian,
        plugin_service=plugin_service,
        emit=emit,
        is_preview=is_preview,
        structural_preview=structural_preview,
    )


async def run_full_cycle(
    *,
    metadata_obj: BaziMetadata,
    enabled_plugins: List[str],
    blind_school_features: Dict[str, Any],
    physics_config: Dict[str, Any],
    session_id: Optional[int] = None,
    dayun: Optional[str] = None,
    liunian: Optional[str] = None,
    plugin_service: Optional[PluginService] = None,
    is_preview: bool = False,
    structural_preview: Optional[Dict[str, Any]] = None,
) -> AsyncIterator[Dict[str, Any]]:
    """
    异步事件流：与 `run_internal_loop` 同构，按序 yield 逻辑事件，末帧 `complete` 携带与 JSON 接口一致的总包。

    事件名（SSE `event:` 对齐）：physics_update、vf_discovered、audit_pulse；终判 token 由 `/v1/final-verdict/stream` 另行输出。
    """
    buf: List[tuple[str, Dict[str, Any]]] = []

    def sink(event: str, data: Dict[str, Any]) -> None:
        buf.append((event, data))

    result = OrchestratorService.run_internal_loop(
        metadata_obj=metadata_obj,
        enabled_plugins=enabled_plugins,
        blind_school_features=blind_school_features,
        physics_config=physics_config,
        session_id=session_id,
        dayun=dayun,
        liunian=liunian,
        plugin_service=plugin_service,
        emit=sink,
        is_preview=is_preview,
        structural_preview=structural_preview,
    )
    for ev, payload in buf:
        yield {"event": ev, "data": payload}
        await asyncio.sleep(0)
    md = result["metadata"]
    complete_payload: Dict[str, Any] = {
        "metadata": md.model_dump(),
        "physics_tensor": result["physics_tensor"],
        "plugin_outputs": result.get("plugin_outputs") or {},
        "semantic_label_bundle_v1": result.get("semantic_label_bundle_v1") or {},
        "verified_fact_lines": result.get("verified_fact_lines") or [],
        "verdict_skeleton": result.get("verdict_skeleton") or "",
        "requires_narrative_refresh": bool(result.get("requires_narrative_refresh")),
        "pre_injection_deity_display": result.get("pre_injection_deity_display") or {},
        "is_preview": bool(is_preview),
    }
    if is_preview:
        complete_payload["preview_pattern_alert"] = str(result.get("preview_pattern_alert") or "")
        _meta = result.get("preview_pattern_alert_meta")
        if isinstance(_meta, dict) and _meta:
            complete_payload["preview_pattern_alert_meta"] = _meta
    yield {"event": "complete", "data": complete_payload}
