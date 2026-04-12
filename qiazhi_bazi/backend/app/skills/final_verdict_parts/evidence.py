from __future__ import annotations

from typing import Any, Dict, List, Tuple

# 与终判证据模板一致：EnergyType（五行局名）+ 地支按传统三合序拼接
_SANHE_ENERGY_AND_BRANCH_KEY: Tuple[Tuple[frozenset[str], str, str], ...] = (
    (frozenset({"寅", "午", "戌"}), "火局", "寅午戌"),
    (frozenset({"申", "子", "辰"}), "水局", "申子辰"),
    (frozenset({"亥", "卯", "未"}), "木局", "亥卯未"),
    (frozenset({"巳", "酉", "丑"}), "金局", "巳酉丑"),
)

_PILLAR_KEY_TO_NODE_LABEL = {
    "year": "Year",
    "month": "Month",
    "day": "Day",
    "hour": "Hour",
}


def _sanhe_energy_type_and_branch_key(br_list: List[str]) -> Tuple[str, str]:
    key = frozenset(br_list)
    for grp, energy, bkey in _SANHE_ENERGY_AND_BRANCH_KEY:
        if grp == key:
            return energy, bkey
    return "三合局", "".join(sorted(br_list))


def _sanhe_nodes_labels(nodes: List[Any]) -> str:
    """按 Year,Month,Day,Hour 顺序列出参与柱位；无则 UNKNOWN。"""
    present: Dict[str, str] = {}
    for n in nodes:
        if not isinstance(n, dict):
            continue
        pk = str(n.get("pillar") or "").strip().lower()
        if pk in _PILLAR_KEY_TO_NODE_LABEL:
            present[pk] = _PILLAR_KEY_TO_NODE_LABEL[pk]
    ordered = [present[k] for k in ("year", "month", "day", "hour") if k in present]
    return ",".join(ordered) if ordered else "UNKNOWN"


def _collect_sanhe_evidence_lines(physics_tensor: Dict[str, Any]) -> List[str]:
    """地支三合脱水行（供 [Physical Evidence] 置顶，避免被十神长列表淹没）。"""
    from app.services.helpers.tensor_adapters import sanhe_clusters_from_physics_tensor

    out: List[str] = []
    clusters: List[Dict[str, Any]] = sanhe_clusters_from_physics_tensor(physics_tensor)
    if not clusters and isinstance(physics_tensor, dict):
        meta_iv = physics_tensor.get("meta") if isinstance(physics_tensor.get("meta"), dict) else {}
        iv2 = meta_iv.get("interaction_v2") if isinstance(meta_iv.get("interaction_v2"), dict) else {}
        for item in iv2.get("attribute_collapse") or []:
            if not isinstance(item, dict) or str(item.get("kind") or "") != "sanhe":
                continue
            brs = [str(x) for x in (item.get("branches") or []) if x]
            if len(brs) >= 3:
                clusters.append(
                    {
                        "branches": brs,
                        "energy_vault_status": "AGGREGATED",
                        "nodes": [],
                    }
                )
    for cl in clusters:
        if not isinstance(cl, dict):
            continue
        brs_raw = cl.get("branches") or []
        brs = sorted({str(x) for x in brs_raw if x})
        if len(brs) < 3:
            continue
        energy_type, branch_key = _sanhe_energy_type_and_branch_key(brs)
        stat = str(cl.get("energy_vault_status") or "AGGREGATED").upper()
        nodes = cl.get("nodes") if isinstance(cl.get("nodes"), list) else []
        nodes_out = _sanhe_nodes_labels(nodes)
        out.append(f"地支.三合.{energy_type}={branch_key}|Status={stat}|Nodes={nodes_out}")
    return out


def format_audit_snapshot_inline(metadata: Dict[str, Any], physics_tensor: Dict[str, Any]) -> str:
    """八字元数据一行快照：四柱干/支 + 十神 Abs（供断语 1:1 审计）。"""
    pillars = (metadata or {}).get("pillars") if isinstance((metadata or {}).get("pillars"), dict) else {}
    stems: List[str] = []
    branches: List[str] = []
    for k in ("year", "month", "day", "hour"):
        col = pillars.get(k) if isinstance(pillars.get(k), dict) else {}
        stems.append(str(col.get("stem") or "?"))
        branches.append(str(col.get("branch") or "?"))
    stem_s = "".join(stems)
    branch_s = "".join(branches)
    abs_nodes = physics_tensor.get("abs_nodes") if isinstance(physics_tensor.get("abs_nodes"), dict) else {}
    axes = physics_tensor.get("deity_energy_axes") if isinstance(physics_tensor.get("deity_energy_axes"), dict) else {}
    ten_bits: List[str] = []
    for d in ["比肩", "劫财", "食神", "伤官", "正财", "偏财", "正官", "七杀", "正印", "偏印"]:
        v = abs_nodes.get(d) if isinstance(abs_nodes.get(d), (int, float)) else None
        if v is None and isinstance(axes.get(d), dict):
            try:
                v = float((axes.get(d) or {}).get("absolute_energy") or 0.0)
            except (TypeError, ValueError):
                v = None
        if isinstance(v, (int, float)):
            ten_bits.append(f"{d}:{float(v):.3f}")
    ten_s = ",".join(ten_bits[:10])[:280]
    return f"[快照|干={stem_s}|支={branch_s}|十神Abs={ten_s}]"


def _annotate_evidence_line(line: str, snap: str) -> str:
    s = str(line or "")
    if not s:
        return s
    if s.startswith("四柱=") or s.startswith("性别=") or s.startswith("共识."):
        return s
    if s.startswith("十神.") or s.startswith("地支.") or s.startswith("裁决项.") or s.startswith("根气."):
        return f"{snap} :: {s}"
    return s


def strength_qualifier(abs_energy: float) -> str:
    if abs_energy < 0.5:
        return "熄灭/虚存"
    if abs_energy < 2.0:
        return "衰微/无力"
    if abs_energy < 5.0:
        return "中和/可用"
    return "强旺/执拗"


def format_deity_abs_semantic_slices(physics_tensor: Dict[str, Any]) -> List[str]:
    """十神 Abs → 短中文档位行，供弱模型在 [Physical Evidence] 顶部做语义锚（非原始 JSON）。"""
    if not isinstance(physics_tensor, dict):
        return []
    axes = physics_tensor.get("deity_energy_axes") if isinstance(physics_tensor.get("deity_energy_axes"), dict) else {}
    abs_nodes = physics_tensor.get("abs_nodes") if isinstance(physics_tensor.get("abs_nodes"), dict) else {}
    deities = ["比肩", "劫财", "食神", "伤官", "正财", "偏财", "正官", "七杀", "正印", "偏印"]
    lines: List[str] = []
    for d in deities:
        abs_energy: float | None = None
        axis = axes.get(d) if isinstance(axes, dict) else None
        if isinstance(axis, dict):
            try:
                abs_energy = float(axis.get("absolute_energy") or 0.0)
            except (TypeError, ValueError):
                abs_energy = None
        if abs_energy is None:
            raw = abs_nodes.get(d)
            if isinstance(raw, (int, float)):
                try:
                    abs_energy = float(raw)
                except (TypeError, ValueError):
                    abs_energy = None
        if abs_energy is None:
            continue
        if abs_energy < 0.15:
            label = "全无/可忽略"
        elif abs_energy < 1.0:
            label = "极弱"
        elif abs_energy < 2.5:
            label = "偏弱"
        elif abs_energy < 5.0:
            label = "中庸可用"
        elif abs_energy < 12.0:
            label = "偏强"
        else:
            label = "独强/执拗"
        lines.append(f"语义.十神.{d}={label}（Abs≈{abs_energy:.2f}）")
    if lines:
        lines.insert(
            0,
            "语义.十神总览=以下为能量档位叙事锚，与十神.*.Abs 数值行一致；断言请引用 plugin.sys.core.physics 或柱位锚。",
        )
    return lines


def get_logical_evidence(
    *,
    metadata: Dict[str, Any],
    physics_tensor: Dict[str, Any],
    selected_cards: List[Dict[str, Any]],
    consensus_history: List[Dict[str, Any]],
) -> List[str]:
    """
    元数据投影：把复杂 JSON 脱水为 Key-Value 证据行，便于 LLM 读取。
    """
    lines: List[str] = []
    sanhe_block = _collect_sanhe_evidence_lines(physics_tensor if isinstance(physics_tensor, dict) else {})
    lines.extend(sanhe_block)
    lines.extend(format_deity_abs_semantic_slices(physics_tensor if isinstance(physics_tensor, dict) else {}))
    pillars = ((metadata or {}).get("pillars", {}) if isinstance(metadata, dict) else {}) or {}
    if pillars:
        y = pillars.get("year", {})
        m = pillars.get("month", {})
        d = pillars.get("day", {})
        h = pillars.get("hour", {})
        lines.append(
            f"四柱={y.get('stem', '?')}{y.get('branch', '?')}/{m.get('stem', '?')}{m.get('branch', '?')}/"
            f"{d.get('stem', '?')}{d.get('branch', '?')}/{h.get('stem', '?')}{h.get('branch', '?')}"
        )
    if isinstance(metadata, dict) and metadata.get("gender"):
        lines.append(f"性别={metadata.get('gender')}")
    deity_axes = (physics_tensor.get("deity_energy_axes", {}) if isinstance(physics_tensor, dict) else {}) or {}
    climate_trace = (
        (((physics_tensor.get("meta", {}) or {}).get("climate_adjustment", {})) if isinstance(physics_tensor, dict) else {})
        or {}
    )
    deity_before = (climate_trace.get("deity_before", {}) if isinstance(climate_trace, dict) else {}) or {}
    deity_after = (climate_trace.get("deity_after", {}) if isinstance(climate_trace, dict) else {}) or {}
    for deity in ["比肩", "劫财", "食神", "伤官", "正财", "偏财", "正官", "七杀", "正印", "偏印"]:
        axis = deity_axes.get(deity) if isinstance(deity_axes, dict) else None
        if isinstance(axis, dict):
            abs_energy = float(axis.get("absolute_energy", 0.0) or 0.0)
            qualifier = strength_qualifier(abs_energy)
            before = float(deity_before.get(deity, 0.0) or 0.0)
            after = float(deity_after.get(deity, abs_energy) or abs_energy)
            factor = (after / before) if before > 0 else 1.0
            lines.append(
                f"十神.{deity}.Abs={abs_energy:.2f} "
                f"(Before:{before:.2f}, Climate_Factor:{factor:.2f}) [状态:{qualifier}]"
            )
    root_check = (
        (((physics_tensor.get("audit_log", {}) or {}).get("trace", {}) or {}).get("root_check", {}))
        if isinstance(physics_tensor, dict)
        else {}
    ) or {}
    if isinstance(root_check, dict):
        lines.append(f"根气.no_root={bool(root_check.get('no_root', False))}")
        lines.append(f"根气.decay_factor={root_check.get('decay_factor', 'N/A')}")
        lines.append(f"根气.record={str(root_check.get('record', ''))[:180]}")
    for i, c in enumerate(consensus_history or []):
        if isinstance(c, dict):
            lines.append(
                f"共识.{i + 1}={c.get('decision_key', '')}:{c.get('confirmed_value', '?')}|{str(c.get('reasoning', ''))[:80]}"
            )
    for i, s in enumerate(selected_cards or []):
        if isinstance(s, dict):
            lines.append(f"裁决项.{i + 1}={s.get('cardType', 'conflict')}|{s.get('displayText') or s.get('title') or ''}")
    snap = format_audit_snapshot_inline(metadata or {}, physics_tensor if isinstance(physics_tensor, dict) else {})
    return [_annotate_evidence_line(x, snap) for x in lines]
