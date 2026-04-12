"""
L1 物理引擎：**唯一**对外结构面为 `plugin_outputs["sys.core.physics"]`。

`interaction_pipeline` 将合成场与原子流水线写入 `physics_tensor[SYS_CORE_PHYSICS_BUNDLE_SRC_KEY]`，
本插件在 `on_physics_complete` 中消费该 bundle 并 `pop` 清理；外界禁止再依赖 tensor 顶层的
`composite_field_impact` / `l1_atomic_pipeline`。
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

# 流水线 → 插件的临时挂载点（仅存在于 run_hook 之前，由本插件消费后移除）
SYS_CORE_PHYSICS_BUNDLE_SRC_KEY = "_sys_core_physics_bundle_src"

# plugin_outputs 键（与前端 l1_branch_* 对齐）
L1_BRANCH_SANHE = "l1_branch_sanhe"
L1_BRANCH_LIUHE = "l1_branch_liuhe"
L1_BRANCH_LIUCHONG = "l1_branch_liuchong"
L1_BRANCH_GOV_KILL_MIX = "l1_branch_gov_kill_mix"
SYS_CORE_PHYSICS_ID = "sys.core.physics"

L1_SANHE_SKILL_ID = "l1_branch_sanhe"
L1_LIUHE_SKILL_ID = "l1_branch_liuhe"
L1_LIUCHONG_SKILL_ID = "l1_branch_liuchong"
L1_GOV_KILL_SKILL_ID = "l1_gov_kill_mix_01"

_SANHE_SORTED_KEY_TO_TITLE: Dict[str, str] = {
    "午寅戌": "寅午戌火局",
    "子申辰": "申子辰水局",
    "卯亥未": "亥卯未木局",
    "丑巳酉": "巳酉丑金局",
}


def _sorted_branch_key(branches: List[str]) -> str:
    return "".join(sorted({str(b).strip() for b in branches if str(b).strip()}))


def _sanhe_bureau_title(branches: List[str]) -> str:
    key = _sorted_branch_key(branches)
    return _SANHE_SORTED_KEY_TO_TITLE.get(key) or f"地支三合（{'、'.join(branches)}）"


def extract_sanhe_clusters(physics_tensor: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not physics_tensor or not isinstance(physics_tensor, dict):
        return []
    comp = physics_tensor.get("composite_field_impact")
    clusters: List[Any] = []
    if isinstance(comp, dict):
        raw = comp.get("sanhe_clusters")
        if isinstance(raw, list):
            clusters = list(raw)
    if not clusters:
        meta = physics_tensor.get("meta")
        if isinstance(meta, dict):
            iv2 = meta.get("interaction_v2")
            if isinstance(iv2, dict):
                collapse = iv2.get("attribute_collapse")
                if isinstance(collapse, list):
                    for item in collapse:
                        if not isinstance(item, dict):
                            continue
                        if str(item.get("kind") or "") != "sanhe":
                            continue
                        brs = [str(x) for x in (item.get("branches") or []) if x is not None]
                        if len(brs) >= 3:
                            clusters.append({"branches": brs, "energy_vault_status": "AGGREGATED", "nodes": []})
    out: List[Dict[str, Any]] = []
    for cl in clusters:
        if not isinstance(cl, dict):
            continue
        brs = [str(x) for x in (cl.get("branches") or []) if x is not None]
        if len(brs) < 3:
            continue
        row = dict(cl)
        row["branches"] = brs
        out.append(row)
    return out


def _conflict_points(metadata: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not metadata or not isinstance(metadata, dict):
        return []
    cm = metadata.get("conflict_matrix")
    if not isinstance(cm, dict):
        return []
    pts = cm.get("points")
    if not isinstance(pts, list):
        return []
    return [p for p in pts if isinstance(p, dict)]


def _l1_step_summaries(physics_tensor: Dict[str, Any]) -> List[str]:
    pipe = physics_tensor.get("l1_atomic_pipeline")
    if not isinstance(pipe, dict):
        return []
    steps = pipe.get("steps")
    if not isinstance(steps, list):
        return []
    out: List[str] = []
    for s in steps[:32]:
        if not isinstance(s, dict):
            continue
        op = str(s.get("op_id") or s.get("operator") or s.get("kind") or "").strip()
        label = str(s.get("label") or s.get("summary") or "")[:96].strip()
        if op and label:
            out.append(f"{op}: {label}")
        elif op:
            out.append(op)
        elif label:
            out.append(label)
    return out


def _stem_fusion_evidence(meta: Dict[str, Any]) -> List[str]:
    sf = meta.get("stem_fusion_v1")
    if not isinstance(sf, dict) or not sf:
        return []
    locked = sf.get("is_locked")
    lines = [f"stem_fusion_v1.is_locked={locked}"]
    ld = sf.get("locked_deities")
    if isinstance(ld, list) and ld:
        lines.append(f"locked_deities={','.join(str(x) for x in ld[:8])}")
    return lines


def _delta_summary_for_trace(delta: Any) -> str:
    if delta is None:
        return ""
    if isinstance(delta, dict):
        parts = [f"{k}={str(v)[:36]}" for k, v in list(delta.items())[:8]]
        return ";".join(parts)[:200]
    return str(delta)[:160]


def build_physics_trace_from_pipeline(pipe: Dict[str, Any]) -> List[Dict[str, Any]]:
    """L0 全链路轨迹：由原子流水线 steps 生成（支冲合化等触发原因摘要）。"""
    steps = pipe.get("steps") if isinstance(pipe.get("steps"), list) else []
    trace: List[Dict[str, Any]] = []
    for i, raw in enumerate(steps[:200]):
        if not isinstance(raw, dict):
            continue
        op = str(raw.get("op_id") or raw.get("operator") or raw.get("kind") or "")[:72]
        plug = str(raw.get("plugin") or "")[:56]
        label = str(raw.get("label") or raw.get("summary") or "")[:240]
        reason = (label.strip() or op or plug or "atomic_step")[:280]
        trace.append(
            {
                "step_index": i,
                "op_id": op,
                "plugin": plug,
                "reason": reason,
                "delta_summary": _delta_summary_for_trace(raw.get("delta")),
            }
        )
    return trace


def _branch_hub_digest(physics_tensor: Dict[str, Any]) -> List[str]:
    meta = physics_tensor.get("meta")
    if not isinstance(meta, dict):
        return []
    iv2 = meta.get("interaction_v2")
    if not isinstance(iv2, dict):
        return []
    collapse = iv2.get("attribute_collapse")
    if not isinstance(collapse, list) or not collapse:
        return []
    kinds: Dict[str, int] = {}
    for item in collapse:
        if not isinstance(item, dict):
            continue
        k = str(item.get("kind") or "unknown")
        kinds[k] = kinds.get(k, 0) + 1
    if not kinds:
        return []
    return ["interaction_v2.attribute_collapse=" + ",".join(f"{k}:{v}" for k, v in sorted(kinds.items()))]


def run_l1_branch_sanhe_plugin(**ctx: Any) -> Dict[str, Any]:
    pt = ctx.get("physics_tensor") if isinstance(ctx.get("physics_tensor"), dict) else {}
    clusters = extract_sanhe_clusters(pt)
    if not clusters:
        return {
            "verdict": "未登记地支三合合成场（四柱内未凑齐三支成局）。",
            "evidence": ["sanhe_clusters=0"],
            "confidence_score": 0.38,
            "skill_id": L1_SANHE_SKILL_ID,
            "plugin": L1_BRANCH_SANHE,
            "matcher_logic": "无三合簇",
            "sanhe_clusters": [],
        }
    ev: List[str] = []
    for cl in clusters:
        brs = [str(x) for x in (cl.get("branches") or [])]
        title = _sanhe_bureau_title(brs)
        stat = str(cl.get("energy_vault_status") or "AGGREGATED")
        ev.append(f"sanhe_cluster={title};status={stat};branches=[{', '.join(brs)}]")
    br0 = [str(x) for x in (clusters[0].get("branches") or [])]
    pool0 = "[" + ", ".join(br0) + "]"
    verdict = f"地支三合已成局：{_sanhe_bureau_title(br0)}（{len(clusters)} 组）。"
    matcher = f"地支池满足 {pool0} 聚合条件；" + verdict
    return {
        "verdict": verdict,
        "evidence": ev,
        "confidence_score": round(min(1.0, 0.92 + min(0.08, 0.02 * max(0, len(clusters) - 1))), 4),
        "skill_id": L1_SANHE_SKILL_ID,
        "plugin": L1_BRANCH_SANHE,
        "matcher_logic": matcher[:400],
        "sanhe_clusters": clusters,
    }


def run_l1_branch_liuhe_plugin(**ctx: Any) -> Dict[str, Any]:
    md = ctx.get("metadata") if isinstance(ctx.get("metadata"), dict) else {}
    pts = [p for p in _conflict_points(md) if str(p.get("kind") or "") == "combine"]
    if not pts:
        return {
            "verdict": "未检出四柱内地支六合成对。",
            "evidence": ["liuhe_pairs=0"],
            "confidence_score": 0.42,
            "skill_id": L1_LIUHE_SKILL_ID,
            "plugin": L1_BRANCH_LIUHE,
            "matcher_logic": "无六合扫描点",
            "liuhe_pairs": [],
        }
    ev = [f"liuhe:{str(p.get('detail') or '')};positions={p.get('positions')}" for p in pts[:12]]
    verdict = f"已登记 {len(pts)} 组地支六合：{'；'.join(str(p.get('detail') or '') for p in pts[:4])}{'…' if len(pts) > 4 else ''}"
    return {
        "verdict": verdict,
        "evidence": ev,
        "confidence_score": round(min(1.0, 0.72 + 0.04 * min(len(pts), 4)), 4),
        "skill_id": L1_LIUHE_SKILL_ID,
        "plugin": L1_BRANCH_LIUHE,
        "matcher_logic": verdict[:400],
        "liuhe_pairs": pts,
    }


def run_l1_branch_liuchong_plugin(**ctx: Any) -> Dict[str, Any]:
    md = ctx.get("metadata") if isinstance(ctx.get("metadata"), dict) else {}
    pts = [p for p in _conflict_points(md) if str(p.get("kind") or "") == "clash"]
    if not pts:
        return {
            "verdict": "未检出四柱内地支六冲成对。",
            "evidence": ["liuchong_pairs=0"],
            "confidence_score": 0.42,
            "skill_id": L1_LIUCHONG_SKILL_ID,
            "plugin": L1_BRANCH_LIUCHONG,
            "matcher_logic": "无六冲扫描点",
            "liuchong_pairs": [],
        }
    ev = [f"liuchong:{str(p.get('detail') or '')};positions={p.get('positions')}" for p in pts[:12]]
    verdict = f"已登记 {len(pts)} 组地支六冲：{'；'.join(str(p.get('detail') or '') for p in pts[:4])}{'…' if len(pts) > 4 else ''}"
    return {
        "verdict": verdict,
        "evidence": ev,
        "confidence_score": round(min(1.0, 0.74 + 0.05 * min(len(pts), 3)), 4),
        "skill_id": L1_LIUCHONG_SKILL_ID,
        "plugin": L1_BRANCH_LIUCHONG,
        "matcher_logic": verdict[:400],
        "liuchong_pairs": pts,
    }


def run_l1_branch_gov_kill_mix_plugin(**ctx: Any) -> Dict[str, Any]:
    pt = ctx.get("physics_tensor") if isinstance(ctx.get("physics_tensor"), dict) else {}
    meta = pt.get("meta") if isinstance(pt.get("meta"), dict) else {}
    gk = meta.get("l1_gov_kill_mix_v1")
    if not isinstance(gk, dict) or gk.get("efficiency_loss") is None:
        return {
            "verdict": "未登记官杀混杂（正官七杀同透）效率折损。",
            "evidence": ["l1_gov_kill_mix_v1=absent"],
            "confidence_score": 0.4,
            "skill_id": L1_GOV_KILL_SKILL_ID,
            "plugin": L1_BRANCH_GOV_KILL_MIX,
            "matcher_logic": "无 meta.l1_gov_kill_mix_v1",
            "gov_kill_mix": {},
        }
    ineff = float(gk.get("efficiency_loss") or 0.0)
    idx = float(gk.get("efficiency_index") or 0.0)
    verdict = f"官杀混杂已登记：效率折损系数 {ineff:.4f}，效率指数 {idx:.4f}。"
    return {
        "verdict": verdict,
        "evidence": [f"l1_gov_kill_mix_v1.efficiency_loss={ineff}", f"efficiency_index={idx}"],
        "confidence_score": round(min(1.0, 0.68 + min(0.25, ineff)), 4),
        "skill_id": L1_GOV_KILL_SKILL_ID,
        "plugin": L1_BRANCH_GOV_KILL_MIX,
        "matcher_logic": verdict[:400],
        "gov_kill_mix": dict(gk),
    }


def run_sys_core_physics_bundle_plugin(**ctx: Any) -> Dict[str, Any]:
    """消费流水线 bundle，产出唯一物理审计 payload；不从 tensor 顶栏回读已废弃字段。"""
    pt = ctx.get("physics_tensor") if isinstance(ctx.get("physics_tensor"), dict) else {}
    md = ctx.get("metadata") if isinstance(ctx.get("metadata"), dict) else {}
    meta = pt.get("meta") if isinstance(pt.get("meta"), dict) else {}
    bundle = pt.pop(SYS_CORE_PHYSICS_BUNDLE_SRC_KEY, None)
    if not isinstance(bundle, dict):
        return {
            "verdict": "物理引擎 bundle 缺失：流水线未写入或已被消费。",
            "evidence": ["sys.core.physics.bundle=missing"],
            "confidence_score": 0.0,
            "skill_id": "sys_core_physics_bundle",
            "plugin": SYS_CORE_PHYSICS_ID,
            "matcher_logic": "无流水线 bundle",
            "composite_field_impact": {},
            "l1_atomic_pipeline": {"version": "", "steps": []},
            "sanhe_clusters": [],
            "liuhe_pairs": [],
            "liuchong_pairs": [],
            "gov_kill_mix": {},
            "facets": {},
            "physics_trace": [],
        }
    comp = bundle.get("composite_field_impact") if isinstance(bundle.get("composite_field_impact"), dict) else {}
    pipe = bundle.get("l1_atomic_pipeline") if isinstance(bundle.get("l1_atomic_pipeline"), dict) else {}
    synth: Dict[str, Any] = {**pt, "composite_field_impact": comp, "l1_atomic_pipeline": pipe}
    sanhe_inner = run_l1_branch_sanhe_plugin(physics_tensor=synth, metadata=md)
    liuhe_inner = run_l1_branch_liuhe_plugin(physics_tensor=synth, metadata=md)
    chong_inner = run_l1_branch_liuchong_plugin(physics_tensor=synth, metadata=md)
    gkm_inner = run_l1_branch_gov_kill_mix_plugin(physics_tensor=synth, metadata=md)
    steps = _l1_step_summaries(synth)
    stem_ev = _stem_fusion_evidence(meta)
    hub_digest = _branch_hub_digest(pt)
    evidence: List[str] = ["sys.core.physics=canonical_engine_output"]
    evidence.extend(f"l1_step:{s}" for s in steps[:16])
    evidence.extend(stem_ev)
    evidence.extend(hub_digest)
    conf = max(
        float(sanhe_inner.get("confidence_score") or 0.0),
        float(liuhe_inner.get("confidence_score") or 0.0),
        float(chong_inner.get("confidence_score") or 0.0),
        float(gkm_inner.get("confidence_score") or 0.0),
    )
    conf = max(conf, 0.5 + (0.12 if steps else 0.0) + (0.1 if stem_ev else 0.0) + (0.08 if hub_digest else 0.0))
    parts = [
        str(sanhe_inner.get("verdict") or "").strip(),
        str(liuhe_inner.get("verdict") or "").strip(),
        str(chong_inner.get("verdict") or "").strip(),
        str(gkm_inner.get("verdict") or "").strip(),
    ]
    verdict = "｜".join([p for p in parts if p])[:520]
    if not verdict.strip():
        verdict = "物理引擎已汇总 L1 流水线；当前未检出需单独强调的结构性判词。"
    sanhe_list = sanhe_inner.get("sanhe_clusters") if isinstance(sanhe_inner.get("sanhe_clusters"), list) else []
    if not sanhe_list and isinstance(comp.get("sanhe_clusters"), list):
        sanhe_list = [c for c in comp["sanhe_clusters"] if isinstance(c, dict)]
    physics_trace = build_physics_trace_from_pipeline(pipe)
    return {
        "verdict": verdict,
        "evidence": evidence[:48],
        "confidence_score": round(min(1.0, conf), 4),
        "skill_id": "sys_core_physics_bundle",
        "plugin": SYS_CORE_PHYSICS_ID,
        "matcher_logic": (str(sanhe_inner.get("matcher_logic") or "") or verdict)[:400],
        "composite_field_impact": comp,
        "l1_atomic_pipeline": pipe,
        "sanhe_clusters": sanhe_list,
        "liuhe_pairs": liuhe_inner.get("liuhe_pairs") if isinstance(liuhe_inner.get("liuhe_pairs"), list) else [],
        "liuchong_pairs": chong_inner.get("liuchong_pairs") if isinstance(chong_inner.get("liuchong_pairs"), list) else [],
        "gov_kill_mix": gkm_inner.get("gov_kill_mix") if isinstance(gkm_inner.get("gov_kill_mix"), dict) else {},
        "facets": {
            "sanhe": sanhe_inner,
            "liuhe": liuhe_inner,
            "liuchong": chong_inner,
            "gov_kill_mix": gkm_inner,
        },
        "l1_step_summaries": steps,
        "stem_fusion_snippet": stem_ev,
        "branch_hub_digest": hub_digest,
        "physics_trace": physics_trace,
    }
