"""L1 十二长生状态机：十神在地支环境下的能效（Work_Efficiency），墓支触发门态提示，并驱动流通审计。"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Mapping, MutableMapping

from app.skills.physics_rules import STEM_TO_ELEMENT, TEN_DEITIES, deity_from_self_and_target_stem

OP_ID = "L1_OP_STATUS"
SKILL_ID = "l1_status_01"
_MANIFEST_PATH = Path(__file__).resolve().parent.parent / "manifests" / "l1_status_manifest.json"

_ELEMENT_ORDER = ("wood", "fire", "earth", "metal", "water")


@lru_cache(maxsize=1)
def _load_status_manifest() -> Dict[str, Any]:
    raw = _MANIFEST_PATH.read_text(encoding="utf-8")
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("l1_status_manifest.json root must be object")
    return data


def _stage_lookup() -> Dict[tuple[str, str], str]:
    pairs = _load_status_manifest().get("pairs")
    out: Dict[tuple[str, str], str] = {}
    if isinstance(pairs, list):
        for row in pairs:
            if isinstance(row, (list, tuple)) and len(row) >= 3:
                out[(str(row[0]), str(row[1]))] = str(row[2])
    return out


def stem_twelve_stage(stem: str, branch: str) -> str:
    if not stem or not branch:
        return ""
    return _stage_lookup().get((stem, branch), "")


def status_work_efficiency(stage: str, settings: Mapping[str, float]) -> float:
    """长生/帝旺→峰值能效；死/绝→低谷；墓→封印向阻尼；其余为中性。"""
    if not stage:
        return float(settings.get("STATUS_EFFICIENCY_NEUTRAL", 1.0))
    peak = max(0.2, min(2.5, float(settings.get("STATUS_EFFICIENCY_PEAK", 1.25))))
    valley = max(0.05, min(1.0, float(settings.get("STATUS_EFFICIENCY_VALLEY", 0.4))))
    tomb = max(0.1, min(1.0, float(settings.get("STATUS_EFFICIENCY_TOMB", 0.72))))
    neu = max(0.2, min(1.5, float(settings.get("STATUS_EFFICIENCY_NEUTRAL", 1.0))))
    lin = max(0.5, min(1.4, float(settings.get("STATUS_EFFICIENCY_LIN_GUAN", 1.12))))
    if stage in ("长生", "帝旺"):
        return peak
    if stage in ("死", "绝"):
        return valley
    if stage == "墓":
        return tomb
    if stage == "临官":
        return lin
    return neu


def _pillars_blob(metadata: Any) -> Dict[str, Any]:
    if metadata is None:
        return {}
    if isinstance(metadata, dict):
        p = metadata.get("pillars")
    else:
        p = getattr(metadata, "pillars", None)
    if p is None:
        return {}
    if hasattr(p, "model_dump"):
        return p.model_dump()
    if isinstance(p, dict):
        return p
    return {}


def _stem_branch(pillars: Mapping[str, Any], key: str) -> tuple[str, str]:
    col = pillars.get(key)
    if not col:
        return "", ""
    if isinstance(col, dict):
        return str(col.get("stem") or ""), str(col.get("branch") or "")
    return str(getattr(col, "stem", "") or ""), str(getattr(col, "branch", "") or "")


def _element_flow_efficiency(
    pillars: Mapping[str, Any],
    month_branch: str,
    day_branch: str,
    settings: Mapping[str, float],
) -> Dict[str, float]:
    buckets: Dict[str, List[float]] = {e: [] for e in _ELEMENT_ORDER}
    for pk in ("year", "month", "day", "hour"):
        st, _br = _stem_branch(pillars, pk)
        if not st:
            continue
        el = STEM_TO_ELEMENT.get(st, "")
        if el not in buckets:
            continue
        sm = stem_twelve_stage(st, month_branch)
        sd = stem_twelve_stage(st, day_branch)
        eff = (status_work_efficiency(sm, settings) + status_work_efficiency(sd, settings)) / 2.0
        buckets[el].append(eff)
    return {
        e: round(sum(v) / len(v), 4) if v else 1.0
        for e, v in buckets.items()
    }


def apply_l1_status_to_physics_tensor(
    *,
    physics_tensor: MutableMapping[str, Any],
    metadata: Any,
    settings: Mapping[str, float],
) -> List[Dict[str, Any]]:
    """
    调整 deity_energy_axes；写入 l1_status_v1、l1_status_element_flow_efficiency、l1_status_tomb_hint（供墓库门态合并）。
    开关：`L1_STATUS_OP_ENABLE` ≥ 0.5。
    """
    if float(settings.get("L1_STATUS_OP_ENABLE", 1.0)) < 0.5:
        return []

    axes = physics_tensor.get("deity_energy_axes")
    if not isinstance(axes, dict) or not axes:
        return []

    pillars = _pillars_blob(metadata)
    day_stem, day_branch = _stem_branch(pillars, "day")
    _, month_branch = _stem_branch(pillars, "month")
    if not day_stem or not month_branch or not day_branch:
        return []

    tomb_day = stem_twelve_stage(day_stem, day_branch) == "墓"
    tomb_month = stem_twelve_stage(day_stem, month_branch) == "墓"
    seal_energy = bool(tomb_day or tomb_month)
    tomb_ref = day_branch if tomb_day else (month_branch if tomb_month else "")

    el_flow = _element_flow_efficiency(pillars, month_branch, day_branch, settings)

    per_deity: Dict[str, Dict[str, Any]] = {}
    for deity in TEN_DEITIES:
        stems: List[str] = []
        for pk in ("year", "month", "day", "hour"):
            st, _br = _stem_branch(pillars, pk)
            if not st:
                continue
            if deity_from_self_and_target_stem(day_stem=day_stem, target_stem=st) != deity:
                continue
            stems.append(st)
        if not stems:
            mult = 1.0
            stages: List[str] = []
            work_eff = 1.0
        else:
            acc = 0.0
            stages = []
            effs: List[float] = []
            for st in stems:
                sm = stem_twelve_stage(st, month_branch)
                sd = stem_twelve_stage(st, day_branch)
                stages.append(f"{st}:月{sm or '?'}/日{sd or '?'}")
                wm = status_work_efficiency(sm, settings)
                wd = status_work_efficiency(sd, settings)
                effs.append((wm + wd) / 2.0)
                acc += (wm + wd) / 2.0
            mult = acc / max(1, len(stems))
            work_eff = mult
        block = axes.get(deity)
        if not isinstance(block, dict):
            continue
        old_abs = float(block.get("absolute_energy") or 0.0)
        new_abs = round(max(0.0, old_abs * mult), 4)
        block["absolute_energy"] = new_abs
        per_deity[deity] = {
            "factor": mult,
            "work_efficiency": round(float(work_eff), 4),
            "absolute_energy_before": round(old_abs, 4),
            "absolute_energy_after": new_abs,
            "stages": stages[:6],
        }

    total = sum(float((axes.get(d) or {}).get("absolute_energy") or 0.0) for d in TEN_DEITIES) or 1.0
    for deity in TEN_DEITIES:
        blk = axes.get(deity)
        if isinstance(blk, dict):
            abs_e = float(blk.get("absolute_energy") or 0.0)
            blk["relative_percentage"] = round(100.0 * abs_e / total, 2)

    meta = physics_tensor.setdefault("meta", {})
    if isinstance(meta, dict):
        meta["l1_status_v1"] = {
            "applied": True,
            "per_deity": per_deity,
            "STATUS_EFFICIENCY_MAP": {
                "长生": status_work_efficiency("长生", settings),
                "帝旺": status_work_efficiency("帝旺", settings),
                "死": status_work_efficiency("死", settings),
                "绝": status_work_efficiency("绝", settings),
                "墓": status_work_efficiency("墓", settings),
                "临官": status_work_efficiency("临官", settings),
                "neutral_default": float(settings.get("STATUS_EFFICIENCY_NEUTRAL", 1.0)),
            },
        }
        meta["l1_status_element_flow_efficiency"] = el_flow
        meta["l1_status_tomb_hint"] = {
            "seal_energy": seal_energy,
            "branch": tomb_ref,
            "on_day_branch": tomb_day,
            "on_month_branch": tomb_month,
            "source": "twelve_status",
        }

    step = {
        "plugin": "base.l1_status",
        "edge": [month_branch, day_branch],
        "delta": {
            "effect": "twelve_status_work_efficiency",
            "per_deity_factors": {k: round(float(v.get("factor", 1.0)), 4) for k, v in per_deity.items()},
            "per_deity_work_efficiency": {k: float(v.get("work_efficiency", 1.0)) for k, v in per_deity.items()},
        },
        "l1_operator_id": OP_ID,
        "l1_operator_ids": [OP_ID],
        "skill_ids": [SKILL_ID],
    }
    return [step]
