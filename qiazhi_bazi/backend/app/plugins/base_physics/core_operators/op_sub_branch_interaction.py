"""深度地支交互：三合/六合/三刑/暗合/墓库 的判定摘要、Abs 微调与 meta.interaction_v2 / 墓库门态。"""
from __future__ import annotations

from typing import Any, Dict, List, Mapping, MutableMapping, Set, Tuple

from app.core.rules.junction import EnergyVaultStatus
from app.skills.physics_rules import SANHE_GROUPS, SANXING_EDGES, STEM_TOMB_BRANCH, TEN_DEITIES

OP_ID = "L1_OP_SUB_BRANCH_INTERACTION"
SKILL_ID = "l1_sub_branch_interaction_01"

_LIUHE_PAIRS: Tuple[Tuple[str, str], ...] = (
    ("子", "丑"),
    ("寅", "亥"),
    ("卯", "戌"),
    ("辰", "酉"),
    ("巳", "申"),
    ("午", "未"),
)

# 常见地支暗合（两支同现即记 INTERNAL_LEAKAGE 审计）
_ANHE_PAIRS: Tuple[frozenset[str], ...] = (
    frozenset({"子", "巳"}),
    frozenset({"丑", "午"}),
    frozenset({"寅", "未"}),
    frozenset({"卯", "申"}),
    frozenset({"亥", "午"}),
)


def _pillars_branches(branches: Mapping[str, str]) -> Set[str]:
    return set(branches.values())


def _liuhe_hits(branches: Mapping[str, str]) -> List[Dict[str, Any]]:
    present = _pillars_branches(branches)
    hits: List[Dict[str, Any]] = []
    for a, b in _LIUHE_PAIRS:
        if a in present and b in present:
            pa = next((p for p, br in branches.items() if br == a), "")
            pb = next((p for p, br in branches.items() if br == b), "")
            if pa and pb and pa != pb:
                hits.append({"pair": [a, b], "pillars": sorted([pa, pb])})
    return hits


def _anhe_hits(branches: Mapping[str, str]) -> List[Dict[str, Any]]:
    present = _pillars_branches(branches)
    out: List[Dict[str, Any]] = []
    for pair in _ANHE_PAIRS:
        if not pair.issubset(present):
            continue
        b1, b2 = sorted(pair)
        pa = next((p for p, br in branches.items() if br == b1), "")
        pb = next((p for p, br in branches.items() if br == b2), "")
        if pa and pb and pa != pb:
            out.append({"pair": sorted(list(pair)), "pillars": sorted([pa, pb])})
    return out


def _sanxing_from_steps(combined_steps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for s in combined_steps:
        if s.get("plugin") != "base.punish":
            continue
        mode = str(s.get("mode") or "")
        if mode != "sanxing":
            continue
        out.append({"edge": list(s.get("edge") or []), "mode": mode})
    return out


def _sanxing_detect(branches: Mapping[str, str]) -> List[Dict[str, Any]]:
    """与原子池一致：任两支成三刑边即记一条（若 steps 未覆盖则补记）。"""
    present = _pillars_branches(branches)
    hits: List[Dict[str, Any]] = []
    seen: Set[Tuple[str, str]] = set()
    for b1, b2 in SANXING_EDGES:
        if b1 in present and b2 in present:
            key = tuple(sorted((b1, b2)))
            if key in seen:
                continue
            seen.add(key)
            pa = next((p for p, br in branches.items() if br == b1), "")
            pb = next((p for p, br in branches.items() if br == b2), "")
            if pa and pb and pa != pb:
                hits.append({"edge": sorted([pa, pb]), "branches": sorted([b1, b2])})
    return hits


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

    liuhe = _liuhe_hits(branches)
    for h in liuhe:
        collapse.append({"kind": "liuhe", "pair": h.get("pair"), "attribute_collapse": True})

    sanxing_steps = _sanxing_from_steps(combined_steps)
    sanxing_geo = _sanxing_detect(branches)
    sanxing_merged = sanxing_steps or [{"edge": x.get("edge"), "branches": x.get("branches")} for x in sanxing_geo]

    anhe = _anhe_hits(branches)
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
            "internal_leakage_audit": leakage_audit,
        }
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
    lh_boost = max(0.0, float(settings.get("SUB_BRANCH_LIUHE_ABS_BOOST", 0.04)))
    sx_damp = max(0.1, min(1.0, float(settings.get("SUB_BRANCH_SANXING_ABS_DAMP", 0.97))))
    an_damp = max(0.1, min(1.0, float(settings.get("SUB_BRANCH_ANHE_ABS_DAMP", 0.985))))

    f = 1.0
    if collapse:
        has_sanhe = any(c.get("kind") == "sanhe" for c in collapse)
        has_liuhe = any(c.get("kind") == "liuhe" for c in collapse)
        if has_sanhe:
            f *= 1.0 + sh_boost
        if has_liuhe:
            f *= 1.0 + lh_boost
    if sanxing_merged:
        f *= sx_damp ** min(3, len(sanxing_merged))
    if anhe:
        f *= an_damp ** min(3, len(anhe))
    f *= damp_muku_merge
    if abs(f - 1.0) > 1e-6:
        _scale_axes(physics_tensor, f)

    audit = physics_tensor.setdefault("audit_log", {})
    if isinstance(audit, dict) and leakage_audit:
        prev = list(audit.get("internal_leakage_audit") or [])
        audit["internal_leakage_audit"] = prev + leakage_audit

    return [
        {
            "plugin": "base.sub_branch_interaction",
            "edge": ["branch", "interaction_v2"],
            "delta": {
                "collapse_count": len(collapse),
                "sanxing_count": len(sanxing_merged),
                "anhe_count": len(anhe),
                "muku_locked": bool(muku_state.get("locked")),
            },
            "l1_operator_id": OP_ID,
            "l1_operator_ids": [OP_ID],
            "skill_ids": [SKILL_ID],
        }
    ]
