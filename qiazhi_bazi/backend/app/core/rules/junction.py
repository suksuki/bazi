"""Rule junction: bridge L1 facts to L2 semantic routers."""
from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from app.core.config.physics_settings import resolve_physics_settings
from app.core.rules.decision_inbox_gate import apply_decision_inbox_signal_gate
from app.skills.physics_rules import BRANCH_HIDDEN_STEMS, ELEMENT_GENERATES, ROOT_MAP, STEM_TO_ELEMENT


class EnergyVaultStatus(str, Enum):
    """墓库 / 合局等通道态：独立记账下的做功门控（L2 可读）。"""

    ACTIVE = "ACTIVE"
    LOCKED = "LOCKED"
    AGGREGATED = "AGGREGATED"


# 地支半合（任两支同现即视为存在半合路径）
_BANHE_PAIRS: Tuple[frozenset[str], ...] = (
    frozenset({"申", "子"}),
    frozenset({"子", "辰"}),
    frozenset({"亥", "卯"}),
    frozenset({"卯", "未"}),
    frozenset({"寅", "午"}),
    frozenset({"午", "戌"}),
    frozenset({"巳", "酉"}),
    frozenset({"酉", "丑"}),
)

_ELEMENT_REF_YANG_STEM: Dict[str, str] = {
    "wood": "甲",
    "fire": "丙",
    "earth": "戊",
    "metal": "庚",
    "water": "壬",
}


def _physics_settings(physics_tensor: Dict[str, Any], explicit: Dict[str, float] | None) -> Dict[str, float]:
    if explicit is not None:
        return explicit
    meta = physics_tensor.get("meta") if isinstance(physics_tensor, dict) else None
    overrides = meta.get("runtime_physics_config") if isinstance(meta, dict) else None
    return resolve_physics_settings(overrides if isinstance(overrides, dict) else None)


def _trace_map(physics_tensor: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(physics_tensor, dict):
        return {}
    td = physics_tensor.get("deity_trace_details")
    if isinstance(td, dict) and td:
        return td
    meta = physics_tensor.get("meta")
    if isinstance(meta, dict):
        inner = meta.get("deity_trace_details")
        if isinstance(inner, dict):
            return inner
    return {}


def _contributions_for_deity(trace_map: Dict[str, Any], deity: str) -> List[Dict[str, Any]]:
    block = trace_map.get(deity) or {}
    base = block.get("base_energy") if isinstance(block, dict) else None
    if not isinstance(base, dict):
        return []
    raw = base.get("contribution_sources")
    return list(raw) if isinstance(raw, list) else []


def _hidden_tier(branch: str, stem: str) -> str:
    """本气 / 中气 / 余气：按藏干比例排序，最小比例为余气。"""
    hidden = BRANCH_HIDDEN_STEMS.get(branch) or {}
    if stem not in hidden:
        return "main"
    ratios = sorted(((s, float(r)) for s, r in hidden.items()), key=lambda x: -x[1])
    if not ratios:
        return "main"
    max_r = ratios[0][1]
    min_r = ratios[-1][1]
    r = float(hidden[stem])
    if r >= max_r - 1e-6:
        return "main"
    if len(ratios) >= 2 and r <= min_r + 1e-6:
        return "residual"
    return "mid"


def _parse_branch_hidden(source: str) -> Optional[Tuple[str, str]]:
    if ".branch:" not in source or ".hidden:" not in source:
        return None
    mid = source.split(".branch:", 1)[1]
    if ".hidden:" not in mid:
        return None
    branch_char, _, hid = mid.partition(".hidden:")
    return branch_char, hid


def _has_surface_channel(contributions: List[Dict[str, Any]]) -> bool:
    """Rule1：天干透干或地支本气计为「明」通道。"""
    for item in contributions:
        e = float(item.get("contribution_energy", 0.0) or 0.0)
        if e <= 1e-12:
            continue
        src = str(item.get("source", ""))
        if ".stem:" in src:
            return True
        parsed = _parse_branch_hidden(src)
        if parsed:
            br, hid = parsed
            stem_key = hid.strip()
            if stem_key and _hidden_tier(br, stem_key) == "main":
                return True
    return False


def _stem_hidden_energy(contributions: List[Dict[str, Any]]) -> Tuple[float, float]:
    stem_e = 0.0
    hid_e = 0.0
    for item in contributions:
        e = float(item.get("contribution_energy", 0.0) or 0.0)
        src = str(item.get("source", ""))
        if ".stem:" in src:
            stem_e += e
        elif ".hidden:" in src:
            hid_e += e
    return stem_e, hid_e


def _pillars_branch_set(metadata: Dict[str, Any]) -> Set[str]:
    pillars = metadata.get("pillars") if isinstance(metadata, dict) else None
    if not isinstance(pillars, dict):
        return set()
    out: Set[str] = set()
    for key in ("year", "month", "day", "hour"):
        col = pillars.get(key)
        if isinstance(col, dict):
            b = col.get("branch")
            if b:
                out.add(str(b))
    return out


def _day_stem(metadata: Dict[str, Any]) -> str:
    pillars = metadata.get("pillars") if isinstance(metadata, dict) else None
    if not isinstance(pillars, dict):
        return ""
    day = pillars.get("day")
    if isinstance(day, dict) and day.get("stem"):
        return str(day["stem"])
    return ""


def _has_tong_gen(day_stem: str, branches: Set[str]) -> bool:
    if not day_stem or not branches:
        return False
    self_el = STEM_TO_ELEMENT.get(day_stem, "earth")
    out_el = ELEMENT_GENERATES.get(self_el, "earth")
    ref = _ELEMENT_REF_YANG_STEM.get(out_el, "甲")
    roots = ROOT_MAP.get(ref, set())
    return bool(roots & branches)


def _has_banhe(branches: Set[str]) -> bool:
    bl = sorted(branches)
    for i in range(len(bl)):
        for j in range(i + 1, len(bl)):
            if frozenset({bl[i], bl[j]}) in _BANHE_PAIRS:
                return True
    return False


def _cross_coordinate_stem_sg_branch_zg(
    sg_contrib: List[Dict[str, Any]], zg_contrib: List[Dict[str, Any]]
) -> bool:
    """天干侧伤官主导且地支侧正官主导时视为干支跨坐标对撞。"""
    s_stem, s_hid = _stem_hidden_energy(sg_contrib)
    z_stem, z_hid = _stem_hidden_energy(zg_contrib)
    sg_stem_led = s_stem >= s_hid - 1e-9
    zg_branch_led = z_hid > z_stem + 1e-9
    return sg_stem_led and zg_branch_led


def _coordinate_distortion_factor(
    *,
    metadata: Dict[str, Any],
    sg_contrib: List[Dict[str, Any]],
    zg_contrib: List[Dict[str, Any]],
    settings: Dict[str, float],
) -> Tuple[float, bool]:
    """
    Rule3 CoordinateDistortion：跨坐标且无通根、无半合时，Abs 损耗系数衰减。
    返回 (乘到 control_energy 上的系数, 是否施加了畸变)。
    """
    base = float(settings.get("SGJG_COORDINATE_DISTORTION_BASE", 1.0))
    decay = float(settings.get("SGJG_COORDINATE_DISTORTION_DECAY", 0.3))
    if not _cross_coordinate_stem_sg_branch_zg(sg_contrib, zg_contrib):
        return base, False
    branches = _pillars_branch_set(metadata)
    ds = _day_stem(metadata)
    if _has_tong_gen(ds, branches) or _has_banhe(branches):
        return base, False
    return decay, True


class VisibilityFilter:
    """伤官见官能级过滤：明面本气 vs 藏干余气 vs 干支坐标畸变。"""

    __slots__ = ()


def sync_l1_junction_flags_to_meta(
    *,
    metadata: Dict[str, Any],
    physics_tensor: Dict[str, Any],
    physics_settings: Dict[str, float] | None = None,
) -> Dict[str, Any]:
    """计算 L1 伤官见官等联结标志并写入 physics_tensor.meta，供盲派 chip 与前端 Inbox 读取。"""
    settings_for_flags = _physics_settings(physics_tensor, physics_settings)
    flags = detect_universal_flags(
        metadata=metadata, physics_tensor=physics_tensor, physics_settings=settings_for_flags
    )
    if isinstance(physics_tensor, dict):
        meta = physics_tensor.setdefault("meta", {})
        if isinstance(meta, dict):
            meta["l1_junction_flags"] = flags
            settings = settings_for_flags
            ge = meta.get("global_entropy_metrics")
            clash: float | None = None
            if isinstance(ge, dict) and ge.get("clash_abs_loss_total") is not None:
                try:
                    clash = float(ge["clash_abs_loss_total"])
                except (TypeError, ValueError):
                    clash = None
            apply_decision_inbox_signal_gate(meta=meta, settings=settings, clash_abs_loss_total=clash)
    return flags


def detect_universal_flags(
    *,
    metadata: Dict[str, Any],
    physics_tensor: Dict[str, Any],
    physics_settings: Dict[str, float] | None = None,
) -> Dict[str, Any]:
    axes = ((physics_tensor or {}).get("deity_energy_axes") or {}) if isinstance(physics_tensor, dict) else {}
    shangguan_abs = float((((axes or {}).get("伤官") or {}).get("absolute_energy", 0.0) or 0.0))
    zhengguan_abs = float((((axes or {}).get("正官") or {}).get("absolute_energy", 0.0) or 0.0))
    active = shangguan_abs > 0.0 and zhengguan_abs > 0.0
    settings = _physics_settings(physics_tensor if isinstance(physics_tensor, dict) else {}, physics_settings)

    trace_map = _trace_map(physics_tensor if isinstance(physics_tensor, dict) else {})
    sg_c = _contributions_for_deity(trace_map, "伤官")
    zg_c = _contributions_for_deity(trace_map, "正官")
    trace_resolved = bool(sg_c) and bool(zg_c)

    has_surface_sg = _has_surface_channel(sg_c) if sg_c else True
    has_surface_zg = _has_surface_channel(zg_c) if zg_c else True
    both_surface = has_surface_sg and has_surface_zg

    coord_factor, coord_applied = (1.0, False)
    if trace_resolved and isinstance(metadata, dict):
        coord_factor, coord_applied = _coordinate_distortion_factor(
            metadata=metadata, sg_contrib=sg_c, zg_contrib=zg_c, settings=settings
        )

    minor_ratio = float(settings.get("SGJG_MINOR_ABS_LOSS_CAP_RATIO", 0.02))

    if not active:
        severity = "NONE"
        ui_level = ""
    elif not trace_resolved:
        severity = "CRITICAL"
        ui_level = "Level: Surface (明)"
    elif both_surface:
        severity = "CRITICAL"
        ui_level = "Level: Surface (明)"
    else:
        severity = "MINOR_INTERFERENCE"
        ui_level = "Level: Deep (藏)"

    raw_control = min(shangguan_abs, zhengguan_abs) if active else 0.0
    if not active:
        control_energy = 0.0
    elif not trace_resolved:
        control_energy = round(raw_control * coord_factor, 4)
    elif severity == "CRITICAL":
        control_energy = round(raw_control * coord_factor, 4)
    else:
        cap_abs = minor_ratio * max(shangguan_abs, zhengguan_abs)
        control_energy = round(min(raw_control * coord_factor, cap_abs), 4)

    shangguan_jian_guan = bool(active)

    return {
        "SHANG_GUAN_JIAN_GUAN": bool(shangguan_jian_guan),
        "shangguan_abs": round(shangguan_abs, 4),
        "zhengguan_abs": round(zhengguan_abs, 4),
        "control_energy": control_energy,
        "source": "L1_Junction",
        "sgjg_severity": severity,
        "sgjg_visibility": "surface" if severity == "CRITICAL" else ("deep" if severity == "MINOR_INTERFERENCE" else "none"),
        "sgjg_level_label": ui_level,
        "sgjg_has_surface_shangguan": bool(has_surface_sg),
        "sgjg_has_surface_zhengguan": bool(has_surface_zg),
        "sgjg_coordinate_distortion_factor": round(coord_factor, 4),
        "sgjg_coordinate_distortion_applied": bool(coord_applied),
        "sgjg_abs_loss_rate_cap": minor_ratio if severity == "MINOR_INTERFERENCE" else None,
        "VisibilityFilter": {
            "trace_resolved": trace_resolved,
            "rule_surface_critical": both_surface if trace_resolved else None,
            "rule_residual_minor": (severity == "MINOR_INTERFERENCE") if trace_resolved else None,
            "CoordinateDistortion": {
                "factor": round(coord_factor, 4),
                "applied": bool(coord_applied),
            },
        },
    }
