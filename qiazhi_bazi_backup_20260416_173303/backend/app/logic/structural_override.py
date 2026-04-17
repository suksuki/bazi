"""
V6.3：结构类意志（L1_STRUCTURE / 三合局锁定）在推荐预览中的张量侧写。
在 dry-run 插件链之前对 ``physics_tensor`` 深拷贝执行 ``apply_structural_override``。
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Mapping, Optional

from app.services.helpers.structural_preview_semantics import normalize_structural_preview_hint
from app.services.helpers.tensor_adapters import sanhe_clusters_from_physics_tensor

# 与前端 `sortedSanheBranchKey` 一致：地支 Unicode 排序后的键 → 合局场强对十神分布的启发式「锁轴」偏移
_SANHE_COHESION_BY_BRANCH_KEY: Dict[str, Dict[str, float]] = {
    "丑巳酉": {"比肩": 0.045, "劫财": 0.045, "偏财": 0.03, "正财": 0.03, "食神": -0.03, "伤官": -0.03},
    "午寅戌": {"食神": 0.055, "伤官": 0.055, "比肩": -0.025, "劫财": -0.025},
    "子申辰": {"正印": 0.04, "偏印": 0.04, "正官": 0.02, "七杀": 0.02, "伤官": -0.03, "食神": -0.03},
    "卯亥未": {"偏财": 0.045, "正财": 0.045, "比肩": -0.02, "劫财": -0.02},
}

_L1_GENERIC_COHESION: Dict[str, float] = {"食神": 0.03, "伤官": 0.03, "比肩": -0.015, "劫财": -0.015}


def _sorted_branch_key(branches: List[str]) -> str:
    norm = [str(b).strip() for b in branches if str(b).strip()]
    return "".join(sorted(set(norm)))


def _branch_key_from_card_id(card_id: str) -> str:
    s = str(card_id or "").strip()
    if s.startswith("inbox-sanhe-"):
        return s[len("inbox-sanhe-") :].strip()
    return ""


def _delta_for_sanhe_tensor(tensor: Mapping[str, Any], branch_key: str) -> Dict[str, float]:
    if branch_key and branch_key in _SANHE_COHESION_BY_BRANCH_KEY:
        return dict(_SANHE_COHESION_BY_BRANCH_KEY[branch_key])
    clusters = sanhe_clusters_from_physics_tensor(dict(tensor) if isinstance(tensor, dict) else {})
    for cl in clusters:
        if not isinstance(cl, dict):
            continue
        brs = [str(x) for x in (cl.get("branches") or []) if x is not None]
        k = _sorted_branch_key(brs)
        if k and k in _SANHE_COHESION_BY_BRANCH_KEY:
            return dict(_SANHE_COHESION_BY_BRANCH_KEY[k])
    return dict(_L1_GENERIC_COHESION)


def _bureau_key_from_label(label: str) -> str:
    """从卡片 label / displayText 中解析局名，回退到分支键。"""
    lab = str(label or "")
    if "巳酉丑" in lab or "丑巳酉" in lab or "金局" in lab:
        return "丑巳酉"
    if "寅午戌" in lab or "午寅戌" in lab or "火局" in lab:
        return "午寅戌"
    if "申子辰" in lab or "子申辰" in lab or "水局" in lab:
        return "子申辰"
    if "亥卯未" in lab or "卯亥未" in lab or "木局" in lab:
        return "卯亥未"
    m = re.search(r"inbox-sanhe-([^\s]+)", lab)
    if m:
        return m.group(1).strip()
    return ""


def _apply_deity_delta_inplace(tensor: Dict[str, Any], delta: Mapping[str, float]) -> None:
    ds = tensor.setdefault("deity_scores", {})
    if not isinstance(ds, dict):
        tensor["deity_scores"] = {}
        ds = tensor["deity_scores"]
    for k, v in delta.items():
        ks = str(k).strip()
        if not ks:
            continue
        try:
            fv = float(v)
        except (TypeError, ValueError):
            continue
        base = float(ds.get(ks) or 0.0) if isinstance(ds.get(ks), (int, float)) else 0.0
        ds[ks] = max(0.0, base + fv)


def apply_structural_override(
    *,
    hint: Mapping[str, Any],
    physics_tensor: Dict[str, Any],
    unused_metadata: Optional[Mapping[str, Any]] = None,
) -> None:
    """
    对 ``physics_tensor`` 就地写入结构预览态（调用方须持有深拷贝）。
    当前实现：``L1_STRUCTURE``（三合局锁定等）→ 合局场强对 ``deity_scores`` 的启发式锁轴偏移；
    其它 kind 暂不修改张量（仍可由 VF / 预警语义层消费）。
    """
    norm = normalize_structural_preview_hint(dict(hint))
    if not norm:
        return
    kind = str(norm.get("kind") or "")
    if kind != "L1_STRUCTURE":
        return
    card_id = str(norm.get("card_id") or "").strip()
    label = str(norm.get("label") or "").strip()
    bkey = _branch_key_from_card_id(card_id) or _bureau_key_from_label(label)
    delta = _delta_for_sanhe_tensor(physics_tensor, bkey)
    if not delta:
        return
    _apply_deity_delta_inplace(physics_tensor, delta)
    meta = physics_tensor.setdefault("meta", {})
    if isinstance(meta, dict):
        meta["structural_preview_recommendation"] = {
            "kind": "L1_STRUCTURE",
            "card_id": card_id,
            "label": label,
            "branch_key": bkey or None,
        }
