"""BaziMetadata 深度审计：L1 流水线证据回写 conflict_matrix、插件入选轨迹。"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Set, Tuple

from app.core.plugins.registry import PluginRegistry
from app.schemas.bazi_metadata import (
    ConflictMatrix,
    ConflictPoint,
    FourPillars,
    InferenceTrace,
    InferenceTraceStep,
    PluginSelectionTraceEntry,
)


def _point_key(p: ConflictPoint) -> Tuple[str, str, str]:
    pos = ",".join(p.positions or [])
    return (p.kind or "", (p.detail or "")[:240], pos)


def _dedupe_points(points: List[ConflictPoint]) -> List[ConflictPoint]:
    seen: Set[Tuple[str, str, str]] = set()
    out: List[ConflictPoint] = []
    for p in points:
        k = _point_key(p)
        if k in seen:
            continue
        seen.add(k)
        out.append(p)
    return out


def _infer_step_kind(step: Dict[str, Any]) -> str:
    plug = str(step.get("plugin") or "").lower()
    op = str(step.get("op_id") or step.get("operator") or step.get("kind") or "").lower()
    lab = str(step.get("label") or step.get("summary") or "").lower()
    if "sanhe" in plug or "sanhe" in op or "三合" in lab:
        return "sanhe"
    if "liuhe" in plug or "六合" in lab or "combine" in op:
        return "combine"
    if "clash" in plug or "chong" in op or "冲" in lab:
        return "clash"
    if "punish" in plug or "刑" in lab:
        return "punish"
    if "harm" in plug or "pierce" in plug or "穿" in lab or "害" in lab:
        return "harm"
    if "grave" in plug or "墓" in lab:
        return "grave"
    if "stem_fusion" in plug or "天干" in lab:
        return "stem_fusion"
    if "blade" in plug:
        return "blade_clash"
    return "atomic"


def _sanhe_detail(cluster: Dict[str, Any]) -> str:
    brs = [str(x) for x in (cluster.get("branches") or []) if x is not None]
    if not brs:
        return "三合簇"
    return f"三合局·支池[{'、'.join(brs)}]·{cluster.get('energy_vault_status', '')}".strip("·")


def _positions_for_branches(branches: List[str], branch_to_columns: Dict[str, str]) -> List[str]:
    out: List[str] = []
    for br in branches:
        col = branch_to_columns.get(br)
        if col and col in ("year", "month", "day", "hour"):
            out.append(f"{col}_branch")
    return sorted(set(out))


def enrich_metadata_conflict_matrix_from_pipeline(
    metadata: Any,
    *,
    steps: List[Dict[str, Any]],
    composite: Dict[str, Any],
    branches: Dict[str, str],
) -> None:
    """将 L1 原子流水线与合成场证据合并进 metadata.conflict_matrix.points（供 Debug / 拓扑 / 终判引用）。"""
    if metadata is None:
        return
    derived: List[ConflictPoint] = []
    branch_to_col: Dict[str, str] = {}
    for col, br in (branches or {}).items():
        if br and col in ("year", "month", "day", "hour", "dayun", "liunian"):
            branch_to_col[str(br)] = col

    for i, cl in enumerate(composite.get("sanhe_clusters") or []):
        if not isinstance(cl, dict):
            continue
        brs = [str(x) for x in (cl.get("branches") or []) if x is not None]
        if len(brs) < 3:
            continue
        derived.append(
            ConflictPoint(
                id=f"sanhe_cluster_{i}",
                kind="sanhe",
                positions=_positions_for_branches(brs, branch_to_col) or ["composite_field"],
                detail=_sanhe_detail(cl),
                source="l1_physics",
            )
        )

    for i, s in enumerate(steps or []):
        if not isinstance(s, dict):
            continue
        lab = str(s.get("label") or s.get("summary") or s.get("reason") or "").strip()
        op = str(s.get("op_id") or s.get("operator") or "").strip()
        plug = str(s.get("plugin") or "").strip()
        if len(lab) < 6 and len(op) < 4:
            continue
        kind = _infer_step_kind(s)
        detail = (lab or op or plug)[:280]
        derived.append(
            ConflictPoint(
                id=f"l1_step_{i}",
                kind=kind,
                positions=[],
                detail=detail,
                source="l1_physics",
            )
        )

    existing: List[ConflictPoint] = []
    cm = getattr(metadata, "conflict_matrix", None)
    if cm is not None and hasattr(cm, "points"):
        existing = list(cm.points or [])
    elif isinstance(metadata, dict):
        raw = (metadata.get("conflict_matrix") or {}).get("points") or []
        for j, p in enumerate(raw):
            if isinstance(p, dict):
                existing.append(
                    ConflictPoint(
                        id=str(p.get("id") or f"cp_scan_{j}"),
                        kind=str(p.get("kind") or "unknown"),
                        positions=[str(x) for x in (p.get("positions") or [])],
                        detail=str(p.get("detail") or ""),
                        source=str(p.get("source") or "scanner"),
                    )
                )
            elif isinstance(p, ConflictPoint):
                existing.append(p)

    fixed_existing: List[ConflictPoint] = []
    for j, p in enumerate(existing):
        if p.id is None or str(p.id).strip() == "":
            fixed_existing.append(p.model_copy(update={"id": f"cp_scan_{j}", "source": p.source or "scanner"}))
        else:
            fixed_existing.append(p)
    existing = fixed_existing

    merged = _dedupe_points(existing + derived)
    new_cm = ConflictMatrix(points=merged[:160])
    if hasattr(metadata, "conflict_matrix") and hasattr(metadata, "model_dump"):
        setattr(metadata, "conflict_matrix", new_cm)
    elif isinstance(metadata, dict):
        metadata["conflict_matrix"] = {"points": [pt.model_dump(exclude_none=True) for pt in merged[:160]]}


def build_plugin_selection_trace(
    *,
    registry: PluginRegistry,
    plugin_outputs: Dict[str, Dict[str, Any]],
    physics_tensor: Dict[str, Any],
) -> List[PluginSelectionTraceEntry]:
    """L0 常驻 + L1–L4 插件入选理由（与 Inbox MatchScore / 生命周期对齐）。"""
    layers = {str(r.get("plugin_id")): str(r.get("layer_id") or "L4") for r in registry.list_specs()}
    out: List[PluginSelectionTraceEntry] = [
        PluginSelectionTraceEntry(
            plugin_id="sys.core.physics",
            layer_id="L0",
            status="ALWAYS_ON",
            reason="系统基准物理总线；on_physics_complete 必跑",
        )
    ]
    meta = physics_tensor.get("meta") if isinstance(physics_tensor.get("meta"), dict) else {}
    inbox = meta.get("decision_inbox_v1") if isinstance(meta.get("decision_inbox_v1"), dict) else {}
    scores_raw = inbox.get("match_scores") if isinstance(inbox.get("match_scores"), list) else []
    score_by_pid = {str(s.get("plugin_id")): s for s in scores_raw if isinstance(s, dict)}

    def _layer_rank(layer: str) -> int:
        order = {"L0": 0, "L1": 1, "L2": 2, "L3": 3, "L4": 4}
        return order.get(str(layer or "").upper()[:2], 9)

    for pid, row in (plugin_outputs or {}).items():
        if not isinstance(row, dict):
            continue
        layer = layers.get(pid, "L4")
        if layer == "L0":
            if pid == "sys.core.physics":
                continue
            out.append(
                PluginSelectionTraceEntry(
                    plugin_id=pid,
                    layer_id="L0",
                    status="ALWAYS_ON",
                    reason="L0 层插件；与 sys.core.physics 同批挂载",
                )
            )
            continue
        if _layer_rank(layer) < _layer_rank("L1"):
            continue
        sc = score_by_pid.get(pid)
        reasons = sc.get("reasons") if isinstance(sc, dict) else None
        reason_txt = ", ".join(str(x) for x in (reasons or []) if x)[:320]
        score_v = float((sc or {}).get("score") or 0.0) if isinstance(sc, dict) else 0.0
        if reason_txt:
            reason = f"MatchScore {score_v:.4f} ({reason_txt})"
        else:
            reason = f"管线输出已登记；MatchScore {score_v:.4f}"
        out.append(
            PluginSelectionTraceEntry(
                plugin_id=str(pid),
                layer_id=str(layer),
                status="SELECTED",
                reason=reason,
            )
        )
    return out


def sync_metadata_pillar_energy_from_tensor(metadata: Any, physics_tensor: Dict[str, Any]) -> None:
    """将 physics_tensor.by_pillar.raw_energy 归一化写回 metadata.pillars.*.energy_value，与 StateMonitor 同源快照对齐。"""
    if metadata is None:
        return
    by_pillar = physics_tensor.get("by_pillar") if isinstance(physics_tensor.get("by_pillar"), dict) else {}
    if not by_pillar:
        return
    raws: List[float] = []
    for key in ("year", "month", "day", "hour"):
        blk = by_pillar.get(key) or {}
        try:
            raws.append(float(blk.get("raw_energy") or 0.0))
        except (TypeError, ValueError):
            raws.append(0.0)
    mx = max(raws) or 1.0

    def _scaled(i: int) -> int:
        v = int(round(100.0 * min(1.0, max(0.0, raws[i] / mx))))
        return max(0, min(100, v))

    if hasattr(metadata, "pillars") and metadata.pillars is not None:
        p = metadata.pillars
        try:
            ny = p.year.model_copy(update={"energy_value": _scaled(0)})
            nm = p.month.model_copy(update={"energy_value": _scaled(1)})
            nd = p.day.model_copy(update={"energy_value": _scaled(2)})
            nh = p.hour.model_copy(update={"energy_value": _scaled(3)})
            np = FourPillars(year=ny, month=nm, day=nd, hour=nh)
            setattr(metadata, "pillars", np)
        except Exception:
            pass


def attach_plugin_selection_trace_to_metadata(metadata: Any, entries: List[PluginSelectionTraceEntry]) -> None:
    if metadata is None or not entries:
        return
    if hasattr(metadata, "model_copy"):
        try:
            object.__setattr__(metadata, "plugin_selection_trace", entries)
        except Exception:
            setattr(metadata, "plugin_selection_trace", entries)
    elif isinstance(metadata, dict):
        metadata["plugin_selection_trace"] = [e.model_dump() for e in entries]


def build_inference_trace(
    *,
    physics_tensor: Dict[str, Any],
    plugin_outputs: Dict[str, Dict[str, Any]],
    registry: PluginRegistry,
) -> InferenceTrace:
    """L0 physics_trace + Inbox MatchScore 摘要 → 可回放 inference_trace。"""
    meta = physics_tensor.get("meta") if isinstance(physics_tensor.get("meta"), dict) else {}
    negotiated = meta.get("causal_routing") if isinstance(meta.get("causal_routing"), dict) else {}
    arb_note = str(negotiated.get("strategy_applied") or negotiated.get("zone") or "")[:200]

    layers = {str(r.get("plugin_id")): str(r.get("layer_id") or "L4") for r in registry.list_specs()}
    steps: List[InferenceTraceStep] = []
    si = 0

    core_row = (plugin_outputs or {}).get("sys.core.physics") or {}
    core_pl = core_row.get("payload") if isinstance(core_row.get("payload"), dict) else {}
    trace = core_pl.get("physics_trace") if isinstance(core_pl.get("physics_trace"), list) else []
    for t in trace[:40]:
        if not isinstance(t, dict):
            continue
        steps.append(
            InferenceTraceStep(
                step_index=si,
                layer_id="L0",
                plugin_id=str(t.get("plugin") or "sys.core.physics"),
                input_summary=str(t.get("op_id") or "")[:120],
                match_score=None,
                output_summary=str(t.get("reason") or "")[:220],
                arbitration_note=arb_note if si == 0 else "",
            )
        )
        si += 1

    inbox = meta.get("decision_inbox_v1") if isinstance(meta.get("decision_inbox_v1"), dict) else {}
    scores = inbox.get("match_scores") if isinstance(inbox.get("match_scores"), list) else []
    for sc in scores[:40]:
        if not isinstance(sc, dict):
            continue
        pid = str(sc.get("plugin_id") or "")
        reasons = sc.get("reasons") if isinstance(sc.get("reasons"), list) else []
        out_s = ", ".join(str(x) for x in reasons[:8])[:220]
        steps.append(
            InferenceTraceStep(
                step_index=si,
                layer_id=str(sc.get("layer_id") or layers.get(pid, "L4")),
                plugin_id=pid,
                input_summary="plugin_outputs + inbox",
                match_score=float(sc.get("score") or 0.0) if sc.get("score") is not None else None,
                output_summary=out_s,
                arbitration_note="",
            )
        )
        si += 1

    return InferenceTrace(version="1.0", steps=steps[:120])


def attach_inference_trace_to_metadata(metadata: Any, trace: InferenceTrace) -> Any:
    """写回 inference_trace；Pydantic v2 优先 model_copy 并返回新实例供调用方覆盖引用。"""
    if metadata is None:
        return metadata
    if hasattr(metadata, "model_copy"):
        try:
            return metadata.model_copy(update={"inference_trace": trace, "memory_schema_version": "2.0"})
        except Exception:
            pass
    if isinstance(metadata, dict):
        metadata["inference_trace"] = trace.model_dump()
        metadata["memory_schema_version"] = "2.0"
        return metadata
    try:
        setattr(metadata, "inference_trace", trace)
        setattr(metadata, "memory_schema_version", "2.0")
    except Exception:
        pass
    return metadata
