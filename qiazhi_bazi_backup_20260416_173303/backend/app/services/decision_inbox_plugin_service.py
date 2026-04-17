"""
Decision Inbox：L1+ 插件信号的登记、PluginMatchScore 推荐与生命周期轨迹（v1）。

v1 策略：默认自动确认所有信号（不阻塞 CausalRouter / 终判），完整写入 lifecycle_traces
供 Debug 与后续「人工确认」接口切换；post_process 占位为 noop。
"""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from app.core.plugins.registry import PluginRegistry, plugin_authority_level
from app.logic.brain.decision_hub import (
    append_physics_autonomy_log,
    apply_physical_sanity_check,
    apply_plugin_authority_tiers,
    maybe_two_stage_fact_closure,
)

_LAYER_ORDER = {"L0": 0, "L1": 1, "L2": 2, "L3": 3, "L4": 4}


def _layer_rank(layer: str) -> int:
    return _LAYER_ORDER.get(str(layer or "").upper()[:2], 9)


def _spec_layers(registry: PluginRegistry) -> Dict[str, str]:
    return {str(r.get("plugin_id")): str(r.get("layer_id") or "L4") for r in registry.list_specs()}


def _axis_spread(physics_tensor: Dict[str, Any]) -> float:
    axes = physics_tensor.get("deity_energy_axes") if isinstance(physics_tensor.get("deity_energy_axes"), dict) else {}
    vals: List[float] = []
    for k, v in axes.items():
        if isinstance(v, dict):
            try:
                vals.append(float(v.get("absolute_energy") or 0.0))
            except (TypeError, ValueError):
                pass
    if len(vals) < 2:
        return 0.0
    return float(max(vals) - min(vals))


def compute_plugin_match_scores(
    *,
    physics_tensor: Dict[str, Any],
    plugin_outputs: Dict[str, Dict[str, Any]],
    registry: PluginRegistry,
) -> List[Dict[str, Any]]:
    """根据 L0 张量为 L1–L3 插件生成推荐分（Dispatcher v1 预览）。"""
    layers = _spec_layers(registry)
    spread = _axis_spread(physics_tensor)
    meta = physics_tensor.get("meta") if isinstance(physics_tensor.get("meta"), dict) else {}
    jf = meta.get("l1_junction_flags") if isinstance(meta.get("l1_junction_flags"), dict) else {}
    jf_n = sum(1 for v in jf.values() if v) if jf else 0
    core = (plugin_outputs.get("sys.core.physics") or {}).get("payload") if isinstance(plugin_outputs.get("sys.core.physics"), dict) else {}
    core = core if isinstance(core, dict) else {}
    core_conf = float((plugin_outputs.get("sys.core.physics") or {}).get("confidence_score") or 0.0)

    out: List[Dict[str, Any]] = []
    for pid, row in (plugin_outputs or {}).items():
        layer = layers.get(pid, "L4")
        if _layer_rank(layer) < _layer_rank("L1") or _layer_rank(layer) > _layer_rank("L3"):
            continue
        score = 0.35
        reasons: List[str] = ["baseline_L1plus"]
        if spread > 4.0:
            score += 0.12
            reasons.append("deity_axis_spread>4")
        if jf_n:
            score += min(0.2, 0.04 * jf_n)
            reasons.append(f"l1_junction_flags={jf_n}")
        if core_conf > 0.75:
            score += 0.08
            reasons.append("L0_engine_high_conf")
        if pid == "classical.blind_school.v1":
            score += 0.1
            reasons.append("blind_school_L2_prior")
        if pid == "classical.wangshuai.v1":
            pl = row.get("payload") if isinstance(row.get("payload"), dict) else {}
            sa = float(pl.get("self_abs") or 0.0)
            if sa > 1.0:
                score += min(0.15, sa / 80.0)
                reasons.append(f"wangshuai_self_abs={round(sa, 3)}")
        if pid == "base.chronos":
            score += 0.05
            reasons.append("chronos_temporal_prior")
        out.append(
            {
                "plugin_id": pid,
                "layer_id": layer,
                "score": round(min(1.0, score), 4),
                "reasons": reasons,
                "authority_level": plugin_authority_level(pid),
            }
        )
    out.sort(key=lambda x: -float(x.get("score") or 0.0))
    return out


def apply_decision_inbox_pipeline(
    *,
    physics_tensor: Dict[str, Any],
    plugin_outputs: Dict[str, Dict[str, Any]],
    registry: PluginRegistry,
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    """将 L1+ 插件登记为 Inbox 信号并写入生命周期轨迹（默认自动确认）。"""
    meta = physics_tensor.setdefault("meta", {})
    if not isinstance(meta, dict):
        return
    layers = _spec_layers(registry)
    now = time.time()
    traces: List[Dict[str, Any]] = []
    signals: List[Dict[str, Any]] = []
    scores = compute_plugin_match_scores(
        physics_tensor=physics_tensor, plugin_outputs=plugin_outputs, registry=registry
    )
    md_ref = metadata if isinstance(metadata, dict) else {}
    cm = md_ref.get("conflict_matrix") if isinstance(md_ref.get("conflict_matrix"), dict) else {}
    pts = cm.get("points") if isinstance(cm.get("points"), list) else []
    conflict_seq: List[Dict[str, Any]] = []
    for p in pts:
        if isinstance(p, dict):
            conflict_seq.append({"kind": str(p.get("kind") or ""), "detail": str(p.get("detail") or "")})
    if not conflict_seq:
        conflict_seq = [{"kind": "", "detail": ""}]

    scores = apply_plugin_authority_tiers(scores, physics_meta_sink=meta)
    scores = apply_physical_sanity_check(
        conflict_seq,
        physics_tensor=physics_tensor,
        match_scores=scores,
        physics_meta_sink=meta,
    )
    scores = maybe_two_stage_fact_closure(metadata=md_ref, physics_tensor=physics_tensor, match_scores=scores)

    score_by_pid = {str(s.get("plugin_id")): float(s.get("score") or 0.0) for s in scores}
    allowed = {str(s.get("plugin_id")).strip() for s in scores if str(s.get("plugin_id") or "").strip()}

    for pid, row in (plugin_outputs or {}).items():
        layer = layers.get(pid, "L4")
        if layer == "L0":
            continue
        if _layer_rank(layer) < _layer_rank("L1"):
            continue
        if pid not in allowed:
            append_physics_autonomy_log(
                meta,
                {
                    "kind": "INBOX_SKIP",
                    "reason": "v1303_pipeline_filtered",
                    "plugin_id": pid,
                },
            )
            continue
        match_score = score_by_pid.get(pid, 0.0)
        traces.append(
            {
                "ts": now,
                "event": "signal_detected",
                "plugin_id": pid,
                "layer_id": layer,
                "detail": f"match_score={match_score}",
            }
        )
        signals.append(
            {
                "plugin_id": pid,
                "layer_id": layer,
                "status": "auto_confirmed",
                "match_score": match_score,
                "confidence_score": float(row.get("confidence_score") or 0.0) if isinstance(row, dict) else 0.0,
            }
        )
        traces.append(
            {
                "ts": now,
                "event": "auto_confirmed",
                "plugin_id": pid,
                "layer_id": layer,
                "detail": "dispatcher_v1_default_on",
            }
        )
        traces.append(
            {
                "ts": now,
                "event": "post_process_applied",
                "plugin_id": pid,
                "layer_id": layer,
                "detail": "noop_v1_plugin_outputs_unchanged",
            }
        )

    meta["decision_inbox_v1"] = {
        "version": "1.0",
        "dispatcher_version": "PluginMatchScore_v1_v1303",
        "signals": signals,
        "lifecycle_traces": traces,
        "match_scores": scores,
    }
