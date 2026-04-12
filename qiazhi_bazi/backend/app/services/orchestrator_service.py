"""系统中枢调度器：无 LLM 的物理闭环（插件 + 因果路由 + 语义 VF 标签）。"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, TypedDict

from app.core.evolution.dna_registry import append_routing_audit_item
from app.core.routing.causal_router import CausalRouter, load_routing_config
from app.schemas.bazi_metadata import BaziMetadata
from app.services.decision_inbox_plugin_service import apply_decision_inbox_pipeline
from app.services.helpers.sys_core_physics_plugin import SYS_CORE_PHYSICS_BUNDLE_SRC_KEY
from app.services.helpers.tensor_adapters import ensure_abs_nodes_on_physics_tensor
from app.services.helpers.interaction_pipeline import evaluate_interactions
from app.services.plugin_service import PluginService
from app.semantic_translator import attach_semantic_labels_to_physics_meta, build_verdict_skeleton

_LOG = logging.getLogger(__name__)


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
                    session_id=session_id,
                    dayun=dayun,
                    liunian=liunian,
                )
            except Exception:
                _LOG.debug("will_injection baseline snapshot skipped", exc_info=True)

        inj = inject_user_decisions(metadata_obj, cfg_working, request_dayun=dayun)
        consumed = physics_skill.consume(
            {
                "metadata": metadata_obj,
                "session_id": session_id,
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

        ps = plugin_service or PluginService()
        plugin_outputs = ps.run_on_physics_complete(
            enabled_plugins=enabled_plugins,
            physics_tensor=physics_tensor,
            metadata=metadata_obj.model_dump(),
            blind_school_features=blind_school_features,
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
            negotiated = CausalRouter(routing_config=load_routing_config()).negotiate_impact(
                plugin_outputs,
                physics_tensor=physics_tensor,
            )
            meta = physics_tensor.get("meta")
            if isinstance(meta, dict):
                meta["causal_routing"] = negotiated
            append_routing_audit_item(physics_tensor, negotiated)
        except Exception:
            _LOG.debug("causal_router negotiate_impact skipped", exc_info=True)

        physics_tensor["plugin_outputs"] = plugin_outputs
        try:
            apply_decision_inbox_pipeline(physics_tensor=physics_tensor, plugin_outputs=plugin_outputs, registry=ps.registry)
        except Exception:
            _LOG.debug("apply_decision_inbox_pipeline skipped", exc_info=True)

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

        requires_refresh = bool(anchor_blocked)
        if baseline_snap is not None:
            try:
                requires_refresh = requires_refresh or narrative_refresh_needed(
                    baseline_snap, snapshot_energy_state(physics_tensor)
                )
            except Exception:
                _LOG.debug("requires_narrative_refresh comparison skipped", exc_info=True)

        out: OrchestratorLoopResult = {
            "metadata": metadata_obj,
            "physics_tensor": physics_tensor,
            "plugin_outputs": plugin_outputs,
            "semantic_label_bundle_v1": bundle,
            "verified_fact_lines": verified,
            "verdict_skeleton": skeleton_md,
            "requires_narrative_refresh": bool(requires_refresh),
            "pre_injection_deity_display": dict(pre_injection_display) if (phys_will or inter_will) else {},
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
    )
