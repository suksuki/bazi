"""深度地支交互：三合/六合/半合/六冲/三刑/六害/六破/暗合/墓库 的判定摘要、Abs 微调与 meta.interaction_v2 / 墓库门态。"""
from __future__ import annotations

from typing import Any, Dict, FrozenSet, List, Mapping, MutableMapping, Set

from app.core.rules.junction import EnergyVaultStatus
from app.plugins.base_physics.core_operators.sub_branch_condition_eval import (
    LIU_HAI_PAIRS,
    LIU_PO_PAIRS,
    eval_anhe_hits,
    eval_banhe_hits,
    eval_branch_pair_hits,
    eval_liu_chong_hits,
    eval_liuhe_hits,
    sanhe_trine_allowed_by_wang_zhi_switch,
    sanxing_detect_geometry,
    sanxing_from_steps,
)
from app.skills.physics_rules import STEM_TOMB_BRANCH, TEN_DEITIES, deity_from_self_and_target_stem

OP_ID = "L1_OP_SUB_BRANCH_INTERACTION"


def is_sanhe_triggered(
    group: FrozenSet[str],
    branches: Mapping[str, str],
    settings: Mapping[str, Any],
) -> bool:
    """三合是否成立：三支在四柱中出现 + `SUB_BRANCH_SANHE_REQ_WANG_ZHI` 旺支门控（委托 `sanhe_trine_allowed_by_wang_zhi_switch`）。"""
    present = frozenset(branches.values())
    if not group.issubset(present):
        return False
    return sanhe_trine_allowed_by_wang_zhi_switch(group, branches, settings)


def verify_sanhe_phi_consistency(
    *,
    clusters: List[Dict[str, Any]],
    steps: List[Dict[str, Any]],
    clamp_on: bool,
) -> Dict[str, Any]:
    """校验：AGGREGATED 节点在流水线上 φ 显式为 0，除非对应 cluster 已标记解锁。"""
    gates = [s for s in steps if s.get("plugin") == "composite.aggregated_phi"]
    if not clamp_on:
        return {"ok": True, "reasons": [], "phi_gate_count": len(gates), "skipped_clamp": True}
    ok = True
    reasons: List[str] = []
    for cl in clusters:
        if (cl.get("energy_vault_status") or "") != EnergyVaultStatus.AGGREGATED.value:
            continue
        unlocked = bool(cl.get("cluster_phi_unlock", False))
        for node in cl.get("nodes") or []:
            pname = str(node.get("pillar") or "")
            found = [g for g in gates if g.get("pillar") == pname]
            if not found:
                ok = False
                reasons.append(f"missing_phi_gate:{pname}")
                continue
            phi = float(found[0].get("phi_work", -1.0))
            if clamp_on and not unlocked and phi != 0.0:
                ok = False
                reasons.append(f"phi_not_zero:{pname}")
            if clamp_on and unlocked and phi != 1.0:
                ok = False
                reasons.append(f"phi_not_released:{pname}")
    return {"ok": ok, "reasons": reasons, "phi_gate_count": len(gates)}


def clamp_node_metric_for_entropy(
    *,
    composite: Mapping[str, Any],
    steps: List[Dict[str, Any]],
    branches: Mapping[str, str],
) -> float:
    """AGGREGATED 或墓库 LOCKED 所触及柱位占四柱比例，归一化到 0..1（供全局熵 m_clamp）。"""
    touched: Set[str] = set()
    for cl in composite.get("sanhe_clusters") or []:
        for node in cl.get("nodes") or []:
            p = str(node.get("pillar") or "")
            if p:
                touched.add(p)
    for s in steps:
        if s.get("plugin") != "base.grave":
            continue
        d = s.get("delta") or {}
        if str(d.get("energy_vault_status") or "") != EnergyVaultStatus.LOCKED.value:
            continue
        tb = str(s.get("tomb_branch") or "")
        for pname, br in branches.items():
            if br == tb:
                touched.add(str(pname))
    return min(1.0, len(touched) / 4.0)


def judgment_protocol_dynamic_lines_for_sub_branch_operator(
    operator_plugin_id: str,
    settings: Mapping[str, Any],
) -> List[str]:
    """与 `apply_op_sub_branch_interaction` 及 composite 三合门控同源键值，供 Admin 卡片「判定协议」随 DB 解析结果刷新。"""
    oid = str(operator_plugin_id)
    out: List[str] = []

    def g(key: str, default: float) -> float:
        try:
            return float(settings.get(key, default))
        except (TypeError, ValueError):
            return default

    out.append(f"[运行时] L1_SUB_BRANCH_OP_ENABLE={g('L1_SUB_BRANCH_OP_ENABLE', 1.0):.2f}（<0.5 跳过地支深度交互算子）")
    if oid == "base.physics.op_branch_sanhe":
        out.append(
            f"[运行时] SUB_BRANCH_SANHE_REQ_WANG_ZHI={g('SUB_BRANCH_SANHE_REQ_WANG_ZHI', 0.0):.2f}（≥0.5 则三合中神须在月/日支）"
        )
        out.append(f"[运行时] SANHE_ALPHA_LEAKAGE={g('SANHE_ALPHA_LEAKAGE', 0.0):.3f}（Abs 有效 boost 乘 (1−α)）")
        out.append(f"[运行时] SUB_BRANCH_SANHE_ABS_BOOST={g('SUB_BRANCH_SANHE_ABS_BOOST', 0.06):.4f}")
    elif oid == "base.physics.op_branch_banhe":
        out.append(f"[运行时] SUB_BRANCH_BANHE_PHI={g('SUB_BRANCH_BANHE_PHI', 0.6):.3f}")
        out.append(f"[运行时] SUB_BRANCH_BANHE_ABS_BOOST={g('SUB_BRANCH_BANHE_ABS_BOOST', 0.02):.4f}")
        out.append(f"[运行时] SUB_BRANCH_BANHE_VECTOR_BOOST={g('SUB_BRANCH_BANHE_VECTOR_BOOST', 0.028):.4f}")
    elif oid == "base.physics.op_branch_liuhe":
        out.append(f"[运行时] SUB_BRANCH_LIUHE_ABS_BOOST={g('SUB_BRANCH_LIUHE_ABS_BOOST', 0.04):.4f}")
    elif oid == "base.physics.op_branch_liuchong":
        out.append(f"[运行时] SUB_BRANCH_LIUCHONG_ABS_DAMP={g('SUB_BRANCH_LIUCHONG_ABS_DAMP', 1.0):.4f}")
    elif oid == "base.physics.op_branch_sanxing":
        out.append(f"[运行时] SUB_BRANCH_SANXING_ABS_DAMP={g('SUB_BRANCH_SANXING_ABS_DAMP', 0.97):.4f}")
    elif oid == "base.physics.op_branch_liuhai":
        out.append(f"[运行时] SUB_BRANCH_LIUHAI_ENABLE={g('SUB_BRANCH_LIUHAI_ENABLE', 1.0):.2f}（<0.5 不算六害）")
        out.append(f"[运行时] SUB_BRANCH_LIUHAI_ABS_DAMP={g('SUB_BRANCH_LIUHAI_ABS_DAMP', 0.998):.5f}")
    elif oid == "base.physics.op_branch_liupo":
        out.append(f"[运行时] SUB_BRANCH_LIUPO_ENABLE={g('SUB_BRANCH_LIUPO_ENABLE', 1.0):.2f}（<0.5 不算六破）")
        out.append(f"[运行时] SUB_BRANCH_LIUPO_ABS_DAMP={g('SUB_BRANCH_LIUPO_ABS_DAMP', 0.998):.5f}")
    return out


def _stem_of(pillars: Mapping[str, Any], key: str) -> str:
    col = pillars.get(key)
    if isinstance(col, dict):
        return str(col.get("stem") or "")
    return str(getattr(col, "stem", "") or "")


def _apply_interaction_marks(
    marks: Dict[str, List[str]],
    *,
    pillars: Mapping[str, Any],
    day_stem: str,
    pillar_keys: List[str],
    tag: str,
) -> None:
    if not day_stem:
        return
    seen: Set[str] = set()
    for pk in pillar_keys:
        pk_s = str(pk).strip()
        if not pk_s or pk_s in seen:
            continue
        seen.add(pk_s)
        st = _stem_of(pillars, pk_s)
        if not st:
            continue
        d = deity_from_self_and_target_stem(day_stem=day_stem, target_stem=st)
        ds = str(d or "").strip()
        if not ds:
            continue
        bucket = marks.setdefault(ds, [])
        if tag not in bucket:
            bucket.append(tag)


def _scale_axes(physics_tensor: MutableMapping[str, Any], factor: float) -> None:
    axes = physics_tensor.get("deity_energy_axes")
    if not isinstance(axes, dict) or factor <= 0:
        return
    f = max(0.05, min(3.0, float(factor)))
    for d in TEN_DEITIES:
        blk = axes.get(d)
        if not isinstance(blk, dict):
            continue
        try:
            blk["absolute_energy"] = round(float(blk.get("absolute_energy") or 0.0) * f, 4)
        except (TypeError, ValueError):
            continue
    if "abs_nodes" in physics_tensor:
        del physics_tensor["abs_nodes"]


def apply_op_sub_branch_interaction(
    *,
    physics_tensor: MutableMapping[str, Any],
    metadata: Any,
    settings: Mapping[str, float],
    combined_steps: List[Dict[str, Any]],
    composite: Mapping[str, Any],
    branches: Dict[str, str],
    pillars: Dict[str, Any],
) -> List[Dict[str, Any]]:
    if float(settings.get("L1_SUB_BRANCH_OP_ENABLE", 1.0)) < 0.5:
        return []
    day_stem = ""
    day_col = pillars.get("day")
    if isinstance(day_col, dict) and day_col.get("stem"):
        day_stem = str(day_col["stem"])
    tomb_branch = STEM_TOMB_BRANCH.get(day_stem, "")

    collapse: List[Dict[str, Any]] = []
    for cl in composite.get("sanhe_clusters") or []:
        if not isinstance(cl, dict):
            continue
        brs = list(cl.get("branches") or [])
        if (cl.get("energy_vault_status") or "") == EnergyVaultStatus.AGGREGATED.value:
            collapse.append({"kind": "sanhe", "branches": brs, "attribute_collapse": True})

    liuhe = eval_liuhe_hits(branches)
    for h in liuhe:
        collapse.append({"kind": "liuhe", "pair": h.get("pair"), "attribute_collapse": True})

    sanxing_steps = sanxing_from_steps(combined_steps)
    sanxing_geo = sanxing_detect_geometry(branches)
    sanxing_merged = sanxing_steps or [{"edge": x.get("edge"), "branches": x.get("branches")} for x in sanxing_geo]

    anhe = eval_anhe_hits(branches)
    leakage_audit: List[Dict[str, Any]] = []
    for item in anhe:
        leakage_audit.append(
            {
                "type": "INTERNAL_LEAKAGE",
                "pair": item.get("pair"),
                "pillars": item.get("pillars"),
                "note": "暗合支间存在潜在内耗泄漏通道",
            }
        )

    banhe_raw = eval_banhe_hits(branches)
    phi_banhe = max(0.0, min(1.0, float(settings.get("SUB_BRANCH_BANHE_PHI", 0.6))))
    banhe: List[Dict[str, Any]] = [{**dict(h), "phi": round(phi_banhe, 4)} for h in banhe_raw]
    liu_chong = eval_liu_chong_hits(branches)
    liu_hai = (
        eval_branch_pair_hits(branches, LIU_HAI_PAIRS)
        if float(settings.get("SUB_BRANCH_LIUHAI_ENABLE", 1.0)) >= 0.5
        else []
    )
    liu_po = (
        eval_branch_pair_hits(branches, LIU_PO_PAIRS)
        if float(settings.get("SUB_BRANCH_LIUPO_ENABLE", 1.0)) >= 0.5
        else []
    )

    branch_interaction_audit: List[Dict[str, Any]] = []
    for h in banhe:
        branch_interaction_audit.append({"type": "BANHE", **dict(h)})
    for h in liu_chong:
        branch_interaction_audit.append({"type": "LIU_CHONG", **dict(h)})
    for h in liu_hai:
        branch_interaction_audit.append({"type": "LIU_HAI", **dict(h)})
    for h in liu_po:
        branch_interaction_audit.append({"type": "LIU_PO", **dict(h)})

    interaction_marks: Dict[str, List[str]] = {}
    for h in liuhe:
        _apply_interaction_marks(
            interaction_marks,
            pillars=pillars,
            day_stem=day_stem,
            pillar_keys=list(h.get("pillars") or []),
            tag="he",
        )
    for h in banhe:
        _apply_interaction_marks(
            interaction_marks,
            pillars=pillars,
            day_stem=day_stem,
            pillar_keys=list(h.get("pillars") or []),
            tag="he",
        )
    for h in liu_chong:
        _apply_interaction_marks(
            interaction_marks,
            pillars=pillars,
            day_stem=day_stem,
            pillar_keys=list(h.get("pillars") or []),
            tag="chong",
        )
    for h in liu_hai:
        _apply_interaction_marks(
            interaction_marks,
            pillars=pillars,
            day_stem=day_stem,
            pillar_keys=list(h.get("pillars") or []),
            tag="hai",
        )
    for h in liu_po:
        _apply_interaction_marks(
            interaction_marks,
            pillars=pillars,
            day_stem=day_stem,
            pillar_keys=list(h.get("pillars") or []),
            tag="po",
        )
    for sx in sanxing_merged:
        edge = sx.get("edge") or []
        if isinstance(edge, list) and len(edge) >= 2:
            _apply_interaction_marks(
                interaction_marks,
                pillars=pillars,
                day_stem=day_stem,
                pillar_keys=[str(edge[0]), str(edge[1])],
                tag="xing",
            )

    muku_state: Dict[str, Any] = {"active": False, "tomb_branch": tomb_branch, "locked": False}
    for s in combined_steps:
        if s.get("plugin") != "base.grave":
            continue
        delta = s.get("delta") or {}
        if str(delta.get("energy_vault_status") or "") == EnergyVaultStatus.LOCKED.value:
            muku_state["active"] = True
            muku_state["locked"] = True
            muku_state["tomb_branch"] = str(s.get("tomb_branch") or tomb_branch)
            break

    _meta_early = physics_tensor.get("meta")
    _tomb_hint = _meta_early.get("l1_status_tomb_hint") if isinstance(_meta_early, dict) else None
    if isinstance(_tomb_hint, dict) and bool(_tomb_hint.get("seal_energy")) and not muku_state["locked"]:
        muku_state["active"] = True
        muku_state["locked"] = True
        tb_hint = str(_tomb_hint.get("branch") or "").strip()
        muku_state["tomb_branch"] = tb_hint or str(muku_state.get("tomb_branch") or tomb_branch)

    damp_muku_merge = 1.0
    meta = physics_tensor.setdefault("meta", {})
    if isinstance(meta, dict):
        meta["interaction_v2"] = {
            "version": "interaction_v2.v1",
            "attribute_collapse": collapse,
            "sanxing": sanxing_merged,
            "anhe": anhe,
            "banhe": banhe,
            "liu_chong": liu_chong,
            "liu_hai": liu_hai,
            "liu_po": liu_po,
            "internal_leakage_audit": leakage_audit,
        }
        meta["interaction_marks_per_deity"] = interaction_marks
        if muku_state["locked"]:
            damp = max(0.1, min(1.0, float(settings.get("MUKU_DEITY_DAMPING", 0.8))))
            tb = str(muku_state.get("tomb_branch") or tomb_branch)
            meta["MUKU_GATE_STATE"] = {
                "locked": True,
                "tomb_branch": tb,
                "damping": round(damp, 4),
            }
            if branches.get("day") == tb:
                damp_muku_merge = damp
        else:
            meta["MUKU_GATE_STATE"] = {"locked": False, "tomb_branch": tomb_branch, "damping": 1.0}

    sh_boost = max(0.0, float(settings.get("SUB_BRANCH_SANHE_ABS_BOOST", 0.06)))
    sanhe_alpha = max(0.0, min(1.0, float(settings.get("SANHE_ALPHA_LEAKAGE", 0.0))))
    lh_boost = max(0.0, float(settings.get("SUB_BRANCH_LIUHE_ABS_BOOST", 0.04)))
    sx_damp = max(0.1, min(1.0, float(settings.get("SUB_BRANCH_SANXING_ABS_DAMP", 0.97))))
    an_damp = max(0.1, min(1.0, float(settings.get("SUB_BRANCH_ANHE_ABS_DAMP", 0.985))))
    banhe_abs_b = max(0.0, float(settings.get("SUB_BRANCH_BANHE_ABS_BOOST", 0.02)))
    vboost = max(0.0, float(settings.get("SUB_BRANCH_BANHE_VECTOR_BOOST", 0.028)))
    hai_damp = max(0.9995, min(1.0, float(settings.get("SUB_BRANCH_LIUHAI_ABS_DAMP", 0.998))))
    po_damp = max(0.9995, min(1.0, float(settings.get("SUB_BRANCH_LIUPO_ABS_DAMP", 0.998))))

    vec = physics_tensor.get("vector")
    if isinstance(vec, dict) and banhe:
        for h in banhe:
            el = str(h.get("element") or "")
            if el not in vec:
                continue
            bump = 1.0 + vboost * phi_banhe
            try:
                vec[el] = float(vec.get(el, 0.0) or 0.0) * bump
            except (TypeError, ValueError):
                continue
        tot = sum(float(vec.get(k, 0.0) or 0.0) for k in ("wood", "fire", "earth", "metal", "water"))
        if tot > 1e-9:
            physics_tensor["normalized"] = {
                k: round(float(vec.get(k, 0.0) or 0.0) / tot, 6) for k in ("wood", "fire", "earth", "metal", "water")
            }

    f = 1.0
    if collapse:
        has_sanhe = any(c.get("kind") == "sanhe" for c in collapse)
        has_liuhe = any(c.get("kind") == "liuhe" for c in collapse)
        if has_sanhe:
            eff_sh = sh_boost * max(0.0, 1.0 - sanhe_alpha)
            f *= 1.0 + eff_sh
        if has_liuhe:
            f *= 1.0 + lh_boost
    if banhe:
        f *= 1.0 + len(banhe) * banhe_abs_b * phi_banhe
    if sanxing_merged:
        f *= sx_damp ** min(3, len(sanxing_merged))
    if anhe:
        f *= an_damp ** min(3, len(anhe))
    if liu_hai:
        f *= hai_damp ** min(4, len(liu_hai))
    if liu_po:
        f *= po_damp ** min(4, len(liu_po))
    chong_damp = max(0.85, min(1.0, float(settings.get("SUB_BRANCH_LIUCHONG_ABS_DAMP", 1.0))))
    if liu_chong:
        f *= chong_damp ** min(4, len(liu_chong))
    f *= damp_muku_merge
    if abs(f - 1.0) > 1e-6:
        _scale_axes(physics_tensor, f)

    audit = physics_tensor.setdefault("audit_log", {})
    if isinstance(audit, dict):
        if branch_interaction_audit:
            prev_b = list(audit.get("branch_interaction_audit") or [])
            audit["branch_interaction_audit"] = prev_b + branch_interaction_audit
        if leakage_audit:
            prev = list(audit.get("internal_leakage_audit") or [])
            audit["internal_leakage_audit"] = prev + leakage_audit

    skill_ids_out: List[str] = []
    if any(c.get("kind") == "sanhe" for c in collapse):
        skill_ids_out.append("l1_branch_sanhe")
    if liuhe:
        skill_ids_out.append("l1_branch_liuhe")
    if banhe:
        skill_ids_out.append("l1_branch_banhe")
    if liu_chong:
        skill_ids_out.append("l1_branch_liuchong")
    if sanxing_merged:
        skill_ids_out.append("l1_branch_sanxing")
    if liu_hai:
        skill_ids_out.append("l1_branch_liuhai")
    if liu_po:
        skill_ids_out.append("l1_branch_liupo")
    if not skill_ids_out:
        skill_ids_out = ["l1_branch_banhe"]

    return [
        {
            "plugin": "base.sub_branch_interaction",
            "edge": ["branch", "interaction_v2"],
            "delta": {
                "collapse_count": len(collapse),
                "sanxing_count": len(sanxing_merged),
                "anhe_count": len(anhe),
                "banhe_count": len(banhe),
                "liu_chong_count": len(liu_chong),
                "liu_hai_count": len(liu_hai),
                "liu_po_count": len(liu_po),
                "muku_locked": bool(muku_state.get("locked")),
            },
            "l1_operator_id": OP_ID,
            "l1_operator_ids": [OP_ID],
            "skill_ids": skill_ids_out,
        }
    ]
