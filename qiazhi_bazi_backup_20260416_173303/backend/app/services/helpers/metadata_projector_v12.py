"""V12 M1：将旧 metadata + physics_tensor 投影为三色结构（纯搬运，无 LLM）。"""

from __future__ import annotations

import copy
from typing import Any, Dict, List, Mapping

from app.schemas.tri_layer_v12 import ArbiterBias, DynamicInference, StaticFact, TriLayerMetadata

# 根级张量键进入 baseline_tensor（与白皮书 baseline 一致）
_BASELINE_ROOT_KEYS = frozenset(
    {
        "deity_scores",
        "deity_energy_axes",
        "deity_components",
        "abs_nodes",
        "normalized",
        "confidence",
    }
)

# meta 键 → DynamicInference.l1_audit
_L1_META_KEYS = frozenset(
    {
        "l1_robber_wealth_v1",
        "energy_vault_flags",
        "work_eligible",
        "PATTERN_SOVEREIGNTY_PROTECTION",
    }
)

# meta 键 → l2_engine_provenance
_L2_PROVENANCE_KEYS = frozenset(
    {
        "pattern_thresholds_engine",
        "pattern_thresholds_status",
        "l2_pattern_result_summary_v1",
        "hit_pattern_name",
        "pattern_manifest_file_sha256",
        "l2_pattern_engine",
    }
)

# meta 键 → plugin_registry_snapshot
_PLUGIN_REGISTRY_KEYS = frozenset(
    {
        "enabled_plugins",
        "plugin_specs",
        "blind_school_features",
    }
)

# meta 键 → conflict_and_topology
_CONFLICT_TOPOLOGY_KEYS = frozenset(
    {
        "conflict_topology_v1",
        "branch_interactions",
    }
)

# meta 键放入 current_tensor_snapshot（展示/审计用，非 baseline）
_META_SNAPSHOT_KEYS = frozenset(
    {
        "params",
        "month_branch",
        "active_structures",
        "pattern_thresholds_status",
    }
)


def _as_dict(obj: Any) -> Dict[str, Any]:
    if obj is None:
        return {}
    if isinstance(obj, dict):
        return dict(obj)
    if hasattr(obj, "model_dump"):
        return obj.model_dump(mode="python")
    return {}


class MetadataProjectorV12:
    """将 legacy bundle 投影为 TriLayerMetadata。"""

    def project(self, old_meta: Mapping[str, Any]) -> TriLayerMetadata:
        """
        old_meta 约定：
        - ``metadata``：``dict`` 或与 BaziMetadata 兼容的可 ``model_dump`` 对象
        - ``physics_tensor``：完整 physics 张量 dict
        - 可选 ``user_intention``：顶层字符串，写入 ArbiterBias.user_intention_id
        """
        md_raw = old_meta.get("metadata")
        pt_raw = old_meta.get("physics_tensor")
        metadata = _as_dict(md_raw)
        physics_tensor = _as_dict(pt_raw)
        meta = physics_tensor.get("meta") if isinstance(physics_tensor.get("meta"), dict) else {}
        meta = dict(meta)

        static = self._project_static_fact(metadata, physics_tensor, meta)
        dynamic = self._project_dynamic_inference(physics_tensor, meta)
        arbiter = self._project_arbiter_bias(metadata, old_meta)

        return TriLayerMetadata(static_fact=static, dynamic_inference=dynamic, arbiter_bias=arbiter)

    def _project_static_fact(
        self,
        metadata: Dict[str, Any],
        physics_tensor: Dict[str, Any],
        meta: Dict[str, Any],
    ) -> StaticFact:
        pillars = {}
        if metadata.get("pillars") is not None:
            pillars = _as_dict(metadata.get("pillars"))

        temporal = {}
        if metadata.get("temporal_context") is not None:
            tc = metadata.get("temporal_context")
            temporal = _as_dict(tc)

        audit_log = physics_tensor.get("audit_log") if isinstance(physics_tensor.get("audit_log"), dict) else {}
        param_vid = str(audit_log.get("param_version_id") or "")

        baseline: Dict[str, Any] = {}
        for k in _BASELINE_ROOT_KEYS:
            if k in physics_tensor and physics_tensor[k] is not None:
                baseline[k] = copy.deepcopy(physics_tensor[k])

        climate = {}
        raw_climate = meta.get("climate_field_correction_v1")
        if isinstance(raw_climate, dict):
            climate = copy.deepcopy(raw_climate)

        hidden: Dict[str, Any] = {}
        interp = metadata.get("interpretation")
        if isinstance(interp, dict) and isinstance(interp.get("hidden_stems"), dict):
            hidden = copy.deepcopy(interp["hidden_stems"])

        return StaticFact(
            schema_version="static_fact.v1",
            pillars=pillars,
            hidden_stems_profile=hidden,
            temporal_anchors=temporal,
            physics_param_version_id=param_vid,
            baseline_tensor=baseline,
            climate_baseline=climate,
        )

    def _project_dynamic_inference(
        self,
        physics_tensor: Dict[str, Any],
        meta: Dict[str, Any],
    ) -> DynamicInference:
        l1_audit = {k: copy.deepcopy(meta[k]) for k in _L1_META_KEYS if k in meta}

        l2_rows: List[Dict[str, Any]] = []
        pt_rows = meta.get("pattern_thresholds")
        if isinstance(pt_rows, list):
            l2_rows = [copy.deepcopy(r) for r in pt_rows if isinstance(r, dict)]

        l2_prov = {k: copy.deepcopy(meta[k]) for k in _L2_PROVENANCE_KEYS if k in meta}

        plugin_snap = {k: copy.deepcopy(meta[k]) for k in _PLUGIN_REGISTRY_KEYS if k in meta}

        will_ctx = {}
        if isinstance(meta.get("intention_context"), dict):
            will_ctx = copy.deepcopy(meta["intention_context"])

        conflict_top: Dict[str, Any] = {}
        for k in _CONFLICT_TOPOLOGY_KEYS:
            if k in meta:
                conflict_top[k] = copy.deepcopy(meta[k])

        sem = {}
        if isinstance(meta.get("semantic_label_bundle_v1"), dict):
            sem = copy.deepcopy(meta["semantic_label_bundle_v1"])

        routing = {}
        if isinstance(meta.get("causal_routing"), dict):
            routing = copy.deepcopy(meta["causal_routing"])

        current_snap: Dict[str, Any] = {}
        for k in _META_SNAPSHOT_KEYS:
            if k in meta:
                current_snap[k] = copy.deepcopy(meta[k])
        if isinstance(physics_tensor.get("audit_log"), dict):
            current_snap["audit_log"] = copy.deepcopy(physics_tensor["audit_log"])

        plugin_out = physics_tensor.get("plugin_outputs")
        plugin_outputs_snapshot = copy.deepcopy(plugin_out) if isinstance(plugin_out, dict) else {}

        # 盲派等大块日志保留在 meta 余量：归入 current_snap 避免丢失
        for k in (
            "mangpai_chip_logs",
            "interaction_hub_mangpai",
            "mangpai_pierce_semantics",
            "chronos_v1",
            "structural_preview_recommendation",
            "pattern_profile",
        ):
            if k in meta:
                current_snap[k] = copy.deepcopy(meta[k])

        return DynamicInference(
            schema_version="dynamic_inference.v1",
            l1_audit=l1_audit,
            l2_pattern_rows=l2_rows,
            l2_engine_provenance=l2_prov,
            plugin_registry_snapshot=plugin_snap,
            will_intention_context=will_ctx,
            conflict_and_topology=conflict_top,
            semantic_label_bundle=sem,
            causal_routing=routing,
            post_will_tensor_delta={},
            current_tensor_snapshot=current_snap,
            plugin_outputs_snapshot=plugin_outputs_snapshot,
        )

    def _project_arbiter_bias(
        self,
        metadata: Dict[str, Any],
        old_meta: Mapping[str, Any],
    ) -> ArbiterBias:
        uid = ""
        top = old_meta.get("user_intention") if isinstance(old_meta.get("user_intention"), str) else None
        if top:
            uid = str(top).strip()
        if not uid and isinstance(metadata.get("user_intention"), str):
            uid = str(metadata["user_intention"]).strip()

        trace = []
        pst = metadata.get("plugin_selection_trace")
        if isinstance(pst, list):
            trace = [copy.deepcopy(x) for x in pst if isinstance(x, dict)]

        persistence = _as_dict(metadata.get("persistence_layer"))
        history = _as_dict(metadata.get("history_context"))
        avs = _as_dict(metadata.get("active_verdict_skeleton"))
        mep = _as_dict(metadata.get("manual_energy_patch"))

        psv_overrides: Dict[str, Any] = {}
        raw_psv = metadata.get("psv_runtime_overrides")
        if isinstance(raw_psv, dict):
            psv_overrides = copy.deepcopy(raw_psv)
        elif isinstance(persistence.get("psv_runtime_overrides"), dict):
            psv_overrides = copy.deepcopy(persistence["psv_runtime_overrides"])
        interrupt_request = _as_dict(metadata.get("interrupt_request"))
        if not interrupt_request and isinstance(persistence.get("interrupt_request"), dict):
            interrupt_request = copy.deepcopy(persistence["interrupt_request"])
        interrupt_state = str(metadata.get("interrupt_state") or persistence.get("interrupt_state") or "").strip()

        ack_tokens: List[Dict[str, Any]] = []
        raw_ack = metadata.get("bias_ack_tokens")
        if isinstance(raw_ack, list):
            ack_tokens = [copy.deepcopy(x) for x in raw_ack if isinstance(x, dict)]
        elif isinstance(persistence.get("bias_ack_tokens"), list):
            ack_tokens = [copy.deepcopy(x) for x in persistence["bias_ack_tokens"] if isinstance(x, dict)]

        return ArbiterBias(
            schema_version="arbiter_bias.v1",
            user_intention_id=uid,
            inbox_selection_trace=trace,
            persistence_layer=persistence,
            history_context=history,
            active_verdict_skeleton=avs,
            manual_energy_patch=mep,
            psv_runtime_overrides=psv_overrides,
            interrupt_request=interrupt_request,
            interrupt_state=interrupt_state,
            bias_ack_tokens=ack_tokens,
        )


__all__ = ["MetadataProjectorV12"]
