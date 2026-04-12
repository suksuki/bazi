"""Rule junction: bridge L1 facts to L2 semantic routers."""
from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Set, Tuple

from app.core.config.physics_settings import resolve_physics_settings
from app.plugins.base_physics.skill_manifest_loader import skill_id_for_l1_operator
from app.core.rules.decision_inbox_gate import apply_decision_inbox_signal_gate
from app.core.bazi.engine import branch_hidden_stems_effective
from app.skills.physics_rules import ELEMENT_GENERATES, ROOT_MAP, STEM_TO_ELEMENT


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
    hidden = branch_hidden_stems_effective().get(branch) or {}
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


def calculate_interaction_visibility(
    deity_a: str,
    deity_b: str,
    *,
    trace_map: Dict[str, Any],
) -> Dict[str, Any]:
    """
    双侧十神在 trace 中的「明 / 藏」能级：双侧均含天干或地支本气为 Surface，否则 Deep；
    任一侧无 contribution_sources 视为 unresolved（与旧版伤官见官门控一致：按 CRITICAL 处理）。
    """
    ca = _contributions_for_deity(trace_map, deity_a)
    cb = _contributions_for_deity(trace_map, deity_b)
    trace_resolved = bool(ca) and bool(cb)
    if not trace_resolved:
        return {
            "visibility": "unresolved",
            "trace_resolved": False,
            "both_surface": False,
            "deity_a": deity_a,
            "deity_b": deity_b,
        }
    both_surface = _has_surface_channel(ca) and _has_surface_channel(cb)
    vis: Literal["surface", "deep"] = "surface" if both_surface else "deep"
    return {
        "visibility": vis,
        "trace_resolved": True,
        "both_surface": both_surface,
        "deity_a": deity_a,
        "deity_b": deity_b,
    }


def _axis_abs(axes: Dict[str, Any], deity: str) -> float:
    block = (axes or {}).get(deity) if isinstance(axes, dict) else None
    if not isinstance(block, dict):
        return 0.0
    try:
        return float(block.get("absolute_energy", 0.0) or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _dominant_deity(axes: Dict[str, Any], candidates: Tuple[str, ...]) -> Tuple[str, float]:
    best = candidates[0]
    best_v = _axis_abs(axes, best)
    for d in candidates[1:]:
        v = _axis_abs(axes, d)
        if v > best_v:
            best, best_v = d, v
    return best, best_v


def _severity_from_visibility(vis: str, *, trace_resolved: bool) -> str:
    if not trace_resolved or vis == "unresolved":
        return "CRITICAL"
    if vis == "surface":
        return "CRITICAL"
    return "MINOR_INTERFERENCE"


def _control_energy_for_pair(
    *,
    raw_min: float,
    max_axis: float,
    severity: str,
    coord_factor: float,
    settings: Dict[str, float],
    trace_resolved: bool,
    visibility: str,
) -> float:
    """Deep 且 trace 已解析时，对基础项乘以 L1_DEEP_VISIBILITY_ABS_DECAY；MINOR 仍受余气 cap。"""
    minor_ratio = float(settings.get("SGJG_MINOR_ABS_LOSS_CAP_RATIO", 0.02))
    deep_decay = float(settings.get("L1_DEEP_VISIBILITY_ABS_DECAY", 0.2))
    apply_deep = trace_resolved and visibility == "deep" and severity == "MINOR_INTERFERENCE"
    decay = deep_decay if apply_deep else 1.0
    scaled = raw_min * coord_factor * decay
    if severity == "MINOR_INTERFERENCE":
        cap_abs = minor_ratio * max_axis if max_axis > 0 else 0.0
        return round(min(scaled, cap_abs), 4)
    return round(scaled, 4)


class VisibilityFilter:
    """L1 核心十神交互的能级过滤：双侧天干/本气为 Surface(明)，否则 Deep(藏)。

    坐标畸变（SGJG_*）仅在 Junction 的伤官×正官对撞路径上启用；与干支维轴 `INTERDIMENSIONAL_*` 传导协议独立。
    """

    __slots__ = ()


def sync_l1_junction_flags_to_meta(
    *,
    metadata: Dict[str, Any],
    physics_tensor: Dict[str, Any],
    physics_settings: Dict[str, float] | None = None,
    sanhe_clusters_precomputed: List[Dict[str, Any]] | None = None,
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
            if sanhe_clusters_precomputed is not None:
                sc = [c for c in sanhe_clusters_precomputed if isinstance(c, dict)]
            else:
                from app.services.helpers.tensor_adapters import sanhe_clusters_from_physics_tensor

                sc = sanhe_clusters_from_physics_tensor(physics_tensor)
            has_sanhe_cluster = len(sc) > 0
            block = apply_decision_inbox_signal_gate(
                meta=meta,
                settings=settings,
                clash_abs_loss_total=clash,
                has_sanhe_cluster=has_sanhe_cluster,
            )
            try:
                from app.core.plugins.conflict_telemetry import record_decision_inbox_signal

                enabled = meta.get("enabled_plugins")
                parts: list[str] = []
                if isinstance(enabled, list):
                    parts.extend(sorted(str(x) for x in enabled))
                blind = meta.get("blind_school_features")
                if isinstance(blind, dict):
                    for k in sorted(blind.keys()):
                        parts.append(f"{k}={blind.get(k)}")
                sig = "||".join(parts) if parts else "unknown_plugins"
                record_decision_inbox_signal(
                    signature=sig,
                    eligible=bool(block.get("inbox_conflict_cards_eligible")),
                )
            except Exception:
                pass
    return flags


def _append_core_interaction(
    out: List[Dict[str, Any]],
    *,
    interaction_id: str,
    label_zh: str,
    deity_a: str,
    deity_b: str,
    axes: Dict[str, Any],
    trace_map: Dict[str, Any],
    metadata: Dict[str, Any],
    settings: Dict[str, float],
    apply_sg_coordinate_distortion: bool,
) -> None:
    a_abs = _axis_abs(axes, deity_a)
    b_abs = _axis_abs(axes, deity_b)
    active = a_abs > 0.0 and b_abs > 0.0
    if not active:
        out.append(
            {
                "id": interaction_id,
                "label_zh": label_zh,
                "deity_a": deity_a,
                "deity_b": deity_b,
                "active": False,
                "severity": "NONE",
                "visibility": "none",
                "trace_resolved": False,
                "control_energy": 0.0,
                "blind_rule_premium_eligible": False,
            }
        )
        return

    vis_info = calculate_interaction_visibility(deity_a, deity_b, trace_map=trace_map)
    vis_raw = str(vis_info.get("visibility") or "unresolved")
    trace_resolved_pair = bool(vis_info.get("trace_resolved"))
    severity = _severity_from_visibility(vis_raw, trace_resolved=trace_resolved_pair)
    vis_norm = "deep" if vis_raw == "deep" else "surface"
    coord_factor, coord_applied = (1.0, False)
    if apply_sg_coordinate_distortion and trace_resolved_pair and isinstance(metadata, dict):
        sg_c = _contributions_for_deity(trace_map, "伤官")
        zg_c = _contributions_for_deity(trace_map, "正官")
        coord_factor, coord_applied = _coordinate_distortion_factor(
            metadata=metadata, sg_contrib=sg_c, zg_contrib=zg_c, settings=settings
        )

    raw_min = min(a_abs, b_abs)
    max_axis = max(a_abs, b_abs)
    control_energy = _control_energy_for_pair(
        raw_min=raw_min,
        max_axis=max_axis,
        severity=severity,
        coord_factor=coord_factor,
        settings=settings,
        trace_resolved=trace_resolved_pair,
        visibility=vis_norm,
    )

    blind_ok = False
    if interaction_id == "SHANG_GUAN_JIAN_GUAN":
        blind_ok = severity != "MINOR_INTERFERENCE"
    else:
        blind_ok = (
            severity == "CRITICAL"
            and trace_resolved_pair
            and vis_norm == "surface"
        )

    ui_level = "Level: Surface (明)" if severity == "CRITICAL" else ("Level: Deep (藏)" if severity == "MINOR_INTERFERENCE" else "")

    out.append(
        {
            "id": interaction_id,
            "label_zh": label_zh,
            "deity_a": deity_a,
            "deity_b": deity_b,
            "active": True,
            "severity": severity,
            "visibility": vis_raw if vis_raw in ("surface", "deep", "unresolved") else "unresolved",
            "trace_resolved": trace_resolved_pair,
            "control_energy": control_energy,
            "coordinate_distortion_factor": round(coord_factor, 4) if apply_sg_coordinate_distortion else 1.0,
            "coordinate_distortion_applied": bool(coord_applied) if apply_sg_coordinate_distortion else False,
            "blind_rule_premium_eligible": blind_ok,
            "ui_level_label": ui_level,
        }
    )


def detect_universal_flags(
    *,
    metadata: Dict[str, Any],
    physics_tensor: Dict[str, Any],
    physics_settings: Dict[str, float] | None = None,
) -> Dict[str, Any]:
    axes = ((physics_tensor or {}).get("deity_energy_axes") or {}) if isinstance(physics_tensor, dict) else {}
    settings = _physics_settings(physics_tensor if isinstance(physics_tensor, dict) else {}, physics_settings)
    trace_map = _trace_map(physics_tensor if isinstance(physics_tensor, dict) else {})
    md = metadata if isinstance(metadata, dict) else {}

    l1_core: List[Dict[str, Any]] = []
    _append_core_interaction(
        l1_core,
        interaction_id="SHANG_GUAN_JIAN_GUAN",
        label_zh="伤官见官",
        deity_a="伤官",
        deity_b="正官",
        axes=axes,
        trace_map=trace_map,
        metadata=md,
        settings=settings,
        apply_sg_coordinate_distortion=True,
    )

    cai_max = max(_axis_abs(axes, "正财"), _axis_abs(axes, "偏财"))
    yin_max = max(_axis_abs(axes, "正印"), _axis_abs(axes, "偏印"))
    if cai_max > 0.0 and yin_max > 0.0:
        d_cai, _ = _dominant_deity(axes, ("正财", "偏财"))
        d_yin, _ = _dominant_deity(axes, ("正印", "偏印"))
        _append_core_interaction(
            l1_core,
            interaction_id="CAI_XING_PO_YIN",
            label_zh="财星破印",
            deity_a=d_cai,
            deity_b=d_yin,
            axes=axes,
            trace_map=trace_map,
            metadata=md,
            settings=settings,
            apply_sg_coordinate_distortion=False,
        )

    _append_core_interaction(
        l1_core,
        interaction_id="XIAO_SHEN_DUO_SHI",
        label_zh="枭神夺食",
        deity_a="偏印",
        deity_b="食神",
        axes=axes,
        trace_map=trace_map,
        metadata=md,
        settings=settings,
        apply_sg_coordinate_distortion=False,
    )

    _append_core_interaction(
        l1_core,
        interaction_id="YANG_REN_FENG_CHONG",
        label_zh="羊刃逢冲",
        deity_a="劫财",
        deity_b="七杀",
        axes=axes,
        trace_map=trace_map,
        metadata=md,
        settings=settings,
        apply_sg_coordinate_distortion=False,
    )

    sg_entry = next((x for x in l1_core if x.get("id") == "SHANG_GUAN_JIAN_GUAN"), {})
    shangguan_abs = round(_axis_abs(axes, "伤官"), 4)
    zhengguan_abs = round(_axis_abs(axes, "正官"), 4)
    control_energy = float(sg_entry.get("control_energy") or 0.0)
    severity = str(sg_entry.get("severity") or "NONE")
    shangguan_jian_guan = bool(sg_entry.get("active"))
    trace_resolved = bool(sg_entry.get("trace_resolved"))
    sg_c = _contributions_for_deity(trace_map, "伤官")
    zg_c = _contributions_for_deity(trace_map, "正官")
    has_surface_sg = _has_surface_channel(sg_c) if sg_c else True
    has_surface_zg = _has_surface_channel(zg_c) if zg_c else True
    both_surface = bool(has_surface_sg and has_surface_zg) if trace_resolved else False
    coord_factor = float(sg_entry.get("coordinate_distortion_factor") or 1.0)
    coord_applied = bool(sg_entry.get("coordinate_distortion_applied"))
    minor_ratio = float(settings.get("SGJG_MINOR_ABS_LOSS_CAP_RATIO", 0.02))
    ui_level = str(sg_entry.get("ui_level_label") or "")

    l1_inbox_signal_bypass = False
    for it in l1_core:
        if not it.get("active"):
            continue
        if str(it.get("severity") or "") != "CRITICAL":
            continue
        iid = str(it.get("id") or "")
        vis_i = str(it.get("visibility") or "")
        if iid == "SHANG_GUAN_JIAN_GUAN":
            l1_inbox_signal_bypass = True
            break
        if vis_i == "surface":
            l1_inbox_signal_bypass = True
            break

    return {
        "SHANG_GUAN_JIAN_GUAN": bool(shangguan_jian_guan),
        "XIAO_SHEN_DUO_SHI": bool(next((x for x in l1_core if x.get("id") == "XIAO_SHEN_DUO_SHI"), {}).get("active")),
        "CAI_XING_PO_YIN": bool(next((x for x in l1_core if x.get("id") == "CAI_XING_PO_YIN"), {}).get("active")),
        "YANG_REN_FENG_CHONG": bool(next((x for x in l1_core if x.get("id") == "YANG_REN_FENG_CHONG"), {}).get("active")),
        "shangguan_abs": shangguan_abs,
        "zhengguan_abs": zhengguan_abs,
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
        "l1_core_interactions": l1_core,
        "l1_inbox_signal_bypass": bool(l1_inbox_signal_bypass),
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


# L1 原子算子 ID（与 plugins/base_physics/core_operators 及 audit 对齐）
L1_OP_PROD = "L1_OP_PROD"
L1_OP_DEST = "L1_OP_DEST"
L1_OP_CONN = "L1_OP_CONN"


def build_l1_operator_audit_items_from_steps(
    steps: List[Dict[str, Any]],
    *,
    timestamp: str,
) -> List[Dict[str, Any]]:
    """由 L1 流水线 steps 生成可并入 audit_summary 的条目，便于因果脉冲追溯到子算子。"""
    rows: List[Dict[str, Any]] = []
    for idx, step in enumerate(steps):
        ids = step.get("l1_operator_ids")
        if not isinstance(ids, list) or not ids:
            pid = step.get("l1_operator_id")
            ids = [pid] if pid else []
        ids = [str(x) for x in ids if x]
        skill_ids_raw = step.get("skill_ids")
        skill_ids = [str(x) for x in skill_ids_raw] if isinstance(skill_ids_raw, list) else []
        lone_skill = str(step.get("skill_id") or "").strip()
        plugin = str(step.get("plugin") or "")
        edge = step.get("edge") if step.get("edge") is not None else step.get("tomb_branch")
        delta = step.get("delta") if isinstance(step.get("delta"), dict) else {}
        if not ids and lone_skill:
            rows.append(
                {
                    "id": f"l1op-{idx}-skill",
                    "step": f"L1-{idx + 1:02d}",
                    "role": "Physics",
                    "action": f"{lone_skill} · {plugin}",
                    "timestamp": timestamp,
                    "payload": {
                        "skill_id": lone_skill,
                        "plugin": plugin,
                        "edge": edge,
                        "delta_keys": sorted(delta.keys()) if isinstance(delta, dict) else [],
                        "delta": delta,
                    },
                }
            )
            continue
        if not ids:
            continue
        for j, oid in enumerate(ids):
            skill_id = skill_ids[j] if j < len(skill_ids) else skill_id_for_l1_operator(oid)
            rows.append(
                {
                    "id": f"l1op-{idx}-{oid}",
                    "step": f"L1-{idx + 1:02d}",
                    "role": "Physics",
                    "action": f"{skill_id} · {oid} · {plugin}",
                    "timestamp": timestamp,
                    "payload": {
                        "skill_id": skill_id,
                        "l1_operator_id": oid,
                        "plugin": plugin,
                        "edge": edge,
                        "delta_keys": sorted(delta.keys()) if isinstance(delta, dict) else [],
                        "delta": delta,
                    },
                }
            )
    return rows
