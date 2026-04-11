"""L1 五行长生状态算子：按天干在月令、日支的长生位对十神 Abs 做非线性缩放。"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Mapping, MutableMapping

from app.skills.physics_rules import TEN_DEITIES, deity_from_self_and_target_stem

OP_ID = "L1_OP_STATUS"
SKILL_ID = "l1_status_01"
_MANIFEST_PATH = Path(__file__).resolve().parent.parent / "manifests" / "l1_status_manifest.json"


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


def _stage_strength_table() -> Dict[str, float]:
    raw = _load_status_manifest().get("stage_strength")
    if not isinstance(raw, dict):
        return {}
    out: Dict[str, float] = {}
    for k, v in raw.items():
        try:
            out[str(k)] = float(v)
        except (TypeError, ValueError):
            continue
    return out


def status_multiplier(stage: str, settings: Mapping[str, float]) -> float:
    t = float(_stage_strength_table().get(stage, 0.5))
    d = float(settings.get("STATUS_DRAIN_MULTIPLIER", 0.85))
    b = float(settings.get("STATUS_BOOST_MULTIPLIER", 1.15))
    return round(max(0.05, min(2.5, d + t * (b - d))), 4)


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


def apply_l1_status_to_physics_tensor(
    *,
    physics_tensor: MutableMapping[str, Any],
    metadata: Any,
    settings: Mapping[str, float],
) -> List[Dict[str, Any]]:
    """
    原地调整 `deity_energy_axes[*].absolute_energy` 与 `relative_percentage`，并返回可审计 steps。
    开关：`L1_STATUS_OP_ENABLE` ≥ 0.5 且存在 `deity_energy_axes`。
    """
    if float(settings.get("L1_STATUS_OP_ENABLE", 1.0)) < 0.5:
        return []

    axes = physics_tensor.get("deity_energy_axes")
    if not isinstance(axes, dict) or not axes:
        return []

    pillars = _pillars_blob(metadata)
    day_stem, _db0 = _stem_branch(pillars, "day")
    _, month_branch = _stem_branch(pillars, "month")
    _, day_branch = _stem_branch(pillars, "day")
    if not day_stem or not month_branch or not day_branch:
        return []

    per_deity: Dict[str, Dict[str, Any]] = {}
    for deity in TEN_DEITIES:
        stems: List[str] = []
        for pk in ("year", "month", "day", "hour"):
            st, _br = _stem_branch(pillars, pk)
            if not st:
                continue
            if pk == "day" and st == day_stem:
                pass
            if deity_from_self_and_target_stem(day_stem=day_stem, target_stem=st) != deity:
                continue
            stems.append(st)
        if not stems:
            mult = 1.0
            stages: List[str] = []
        else:
            acc = 0.0
            stages = []
            for st in stems:
                sm = stem_twelve_stage(st, month_branch)
                sd = stem_twelve_stage(st, day_branch)
                stages.append(f"{st}:月{sm or '?'}/日{sd or '?'}")
                acc += (status_multiplier(sm, settings) + status_multiplier(sd, settings)) / 2.0
            mult = acc / max(1, len(stems))
        block = axes.get(deity)
        if not isinstance(block, dict):
            continue
        old_abs = float(block.get("absolute_energy") or 0.0)
        new_abs = round(max(0.0, old_abs * mult), 4)
        block["absolute_energy"] = new_abs
        per_deity[deity] = {
            "factor": mult,
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
        meta["l1_status_v1"] = {"applied": True, "per_deity": per_deity}

    step = {
        "plugin": "base.l1_status",
        "edge": [month_branch, day_branch],
        "delta": {
            "effect": "twelve_status_scale",
            "per_deity_factors": {k: round(float(v.get("factor", 1.0)), 4) for k, v in per_deity.items()},
        },
        "l1_operator_id": OP_ID,
        "l1_operator_ids": [OP_ID],
        "skill_ids": [SKILL_ID],
    }
    return [step]
