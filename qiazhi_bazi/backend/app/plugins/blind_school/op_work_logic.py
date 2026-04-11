"""贼捕做功阶梯：结合 op_status 十二长生对受制方标定 Work_Intensity，并写入 meta.work_audit_v1。"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Mapping, MutableMapping, Tuple

from app.core.config.physics_settings import resolve_physics_settings

_STAGE_GROWTH = frozenset({"长生", "帝旺"})
_STAGE_DEAD_TOMB = frozenset({"死", "绝", "墓"})
_STAGE_RE = re.compile(r"[月日]([^/\\s]+?)(?=/|$)")


def _stages_from_per_deity(per_deity: Mapping[str, Any], deity: str) -> List[str]:
    row = per_deity.get(deity)
    if not isinstance(row, dict):
        return []
    raw = row.get("stages")
    if not isinstance(raw, list):
        return []
    out: List[str] = []
    for s in raw:
        if not isinstance(s, str):
            continue
        for m in _STAGE_RE.finditer(s):
            st = (m.group(1) or "").strip()
            if st and st not in ("?", "？"):
                out.append(st)
    return out


def _work_intensity_for_stages(
    stages: List[str],
    settings: Mapping[str, float],
) -> Tuple[float, str]:
    """长生/帝旺优先视为「制不住」；否则死/绝/墓为「制得干净」。"""
    clean = float(settings.get("BLIND_WORK_INTENSITY_DEAD_TOMB", 1.5))
    stuck = float(settings.get("BLIND_WORK_INTENSITY_GROWTH", 0.5))
    neutral = float(settings.get("BLIND_WORK_INTENSITY_NEUTRAL", 1.0))
    if any(st in _STAGE_GROWTH for st in stages):
        return stuck, "controlled_growth_peak"
    if any(st in _STAGE_DEAD_TOMB for st in stages):
        return clean, "controlled_dead_tomb_valley"
    return neutral, "controlled_neutral_stage"


def _controller_and_controlled(vector: Mapping[str, Any]) -> Tuple[str, str]:
    """主制方 = Abs 较高侧；受制方 = 另一侧。"""
    sa = float(vector.get("source_abs") or 0.0)
    ta = float(vector.get("target_abs") or 0.0)
    sd = str(vector.get("source_deity") or "")
    td = str(vector.get("target_deity") or "")
    if sa >= ta:
        return sd, td
    return td, sd


def apply_work_intensity_and_meta_audit(
    *,
    work_vector: MutableMapping[str, Any],
    physics_tensor: MutableMapping[str, Any],
) -> None:
    """
    为每条 work_vector 注入 work_intensity / work_score，并把聚合审计写入 physics_tensor.meta.work_audit_v1。
    work_score = expected_work * work_intensity（不改变原有 expected_work，以免破坏下游契约）。
    """
    meta_pt = physics_tensor.setdefault("meta", {})
    if not isinstance(meta_pt, dict):
        return
    rcfg = meta_pt.get("runtime_physics_config")
    settings = resolve_physics_settings(rcfg if isinstance(rcfg, dict) else None)

    l1_status = meta_pt.get("l1_status_v1")
    per_deity = (l1_status or {}).get("per_deity") if isinstance(l1_status, dict) else None
    if not isinstance(per_deity, dict):
        per_deity = {}

    wvs = list(work_vector.get("work_vectors") or [])
    audit_items: List[Dict[str, Any]] = []
    weighted_total = 0.0
    raw_total = 0.0

    for v in wvs:
        if not isinstance(v, dict):
            continue
        ctrl, controlled = _controller_and_controlled(v)
        stages = _stages_from_per_deity(per_deity, controlled)
        intensity, profile = _work_intensity_for_stages(stages, settings)
        ew = float(v.get("expected_work") or 0.0)
        raw_total += ew
        ws = round(ew * intensity, 4)
        weighted_total += ws
        v["work_intensity"] = round(float(intensity), 4)
        v["work_score"] = ws
        v["controller_deity"] = ctrl
        v["controlled_deity"] = controlled
        v["controlled_stage_profile"] = profile
        v["controlled_status_stages"] = stages[:8]
        audit_items.append(
            {
                "detail": str(v.get("detail") or ""),
                "type": str(v.get("type") or ""),
                "controller_deity": ctrl,
                "controlled_deity": controlled,
                "work_intensity": round(float(intensity), 4),
                "expected_work": round(ew, 4),
                "work_score": ws,
                "controlled_stage_profile": profile,
            }
        )

    meta_pt["work_audit_v1"] = {
        "source": "blind_school.op_work_logic",
        "items": audit_items,
        "totals": {
            "expected_work_sum": round(raw_total, 4),
            "weighted_work_score_sum": round(weighted_total, 4),
        },
    }
