"""
V9.0：冲突拓扑审计（L0）。从 ``conflict_manifest.json`` 读取线性能量乘子与 ``PAIR_DECAYS`` 五行折损，
扫描 ``meta.branch_interactions``（由 ``build_branch_interactions`` 从冲突矩阵生成），
写入 ``meta.conflict_topology_v1``，供 ``build_energy_fields`` 消费 ``conflict_factor`` × 按支五行乘子。
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Mapping, MutableMapping, Optional, Tuple

from app.logic.physics.branch_interactions import build_branch_interactions

_MANIFEST_DIR = Path(__file__).resolve().parent
_DEFAULT_MANIFEST = _MANIFEST_DIR / "conflict_manifest.json"

_ELEMENT_KEYS = ("wood", "fire", "earth", "metal", "water")
_ZH_EL = {"wood": "木", "fire": "火", "earth": "土", "metal": "金", "water": "水"}
_LEGACY_DECAY_KEYS = {
    "water_decay": "water",
    "fire_decay": "fire",
    "earth_decay": "earth",
    "metal_decay": "metal",
    "wood_decay": "wood",
}


def _identity_element_mods() -> Dict[str, float]:
    return {k: 1.0 for k in _ELEMENT_KEYS}


def _normalize_pair(pair: Any) -> Optional[Tuple[str, str]]:
    if not isinstance(pair, (list, tuple)) or len(pair) < 2:
        return None
    a, b = str(pair[0]).strip(), str(pair[1]).strip()
    if len(a) != 1 or len(b) != 1:
        return None
    return tuple(sorted([a, b]))


def _pair_decay_row_matches_interaction(row: Mapping[str, Any], bi: Mapping[str, Any]) -> bool:
    rt = str(row.get("type") or "CLASH").strip().upper()
    it = str(bi.get("type") or "CLASH").strip().upper()
    if rt != it:
        return False
    rp = _normalize_pair(row.get("pair"))
    ip = _normalize_pair(bi.get("pair"))
    if not rp or not ip:
        return False
    return rp == ip


def _extract_element_decay(row: Mapping[str, Any]) -> Dict[str, float]:
    out: Dict[str, float] = {}
    ed = row.get("element_decay")
    if isinstance(ed, dict):
        for k, v in ed.items():
            key = str(k).strip().lower()
            if key in _ELEMENT_KEYS:
                out[key] = float(v)
    for lk, el in _LEGACY_DECAY_KEYS.items():
        if lk in row and row[lk] is not None:
            out[el] = float(row[lk])
    return out


def _apply_pair_decays(
    loaded: Mapping[str, Any], branch_interactions: List[Dict[str, Any]]
) -> Tuple[Dict[str, float], List[Dict[str, Any]]]:
    """法典 ``PAIR_DECAYS``：按支匹配后叠乘五行乘子，并生成 Admin 可读的损耗行。"""
    mods = _identity_element_mods()
    extra_entries: List[Dict[str, Any]] = []
    pd = loaded.get("PAIR_DECAYS")
    if not isinstance(pd, list):
        return mods, extra_entries
    for bi in branch_interactions:
        if not isinstance(bi, dict):
            continue
        detail = str(bi.get("detail") or "").strip()
        pair = bi.get("pair") if isinstance(bi.get("pair"), list) else []
        for row in pd:
            if not isinstance(row, dict):
                continue
            if not _pair_decay_row_matches_interaction(row, bi):
                continue
            ed = _extract_element_decay(row)
            if not ed:
                continue
            eid = str(row.get("id") or row.get("manifest_entry_id") or "PAIR_DECAYS").strip() or "PAIR_DECAYS"
            loss_parts: List[str] = []
            for el, dec in ed.items():
                if el not in _ELEMENT_KEYS:
                    continue
                dec = max(0.0, min(1.0, float(dec)))
                mods[el] *= max(0.05, 1.0 - dec)
                pct = round(dec * 1000) / 10.0
                loss_parts.append(f"{_ZH_EL.get(el, el)}能量 -{pct}%")
            label = detail if detail else (f"{pair[0]}{pair[1]}冲" if len(pair) == 2 else "冲突")
            extra_entries.append(
                {
                    "detail": label,
                    "kind": str(bi.get("type") or "CLASH").lower(),
                    "linear_multiplier": None,
                    "pct_change_display": None,
                    "source": "Manifest_PAIR_DECAYS",
                    "manifest_entry_id": eid,
                    "element_loss_display": "、".join(loss_parts),
                }
            )
            break
    return mods, extra_entries


def get_conflict_manifest_path() -> Path:
    raw = (os.environ.get("QIAZHI_CONFLICT_MANIFEST_PATH") or "").strip()
    if raw:
        return Path(raw).expanduser().resolve()
    return _DEFAULT_MANIFEST


def load_conflict_manifest(source: Optional[Mapping[str, Any] | str | Path] = None) -> Dict[str, Any]:
    if source is None:
        p = get_conflict_manifest_path()
        return json.loads(p.read_text(encoding="utf-8"))
    if isinstance(source, (str, Path)):
        return json.loads(Path(source).read_text(encoding="utf-8"))
    if isinstance(source, Mapping):
        return dict(source)
    raise TypeError("source must be None, Path/str, or Mapping")


def _default_kind_table() -> Dict[str, Dict[str, Any]]:
    """与旧 ``1 - n*0.12`` 单冲约 0.88 对齐的兜底表（无法读取磁盘 JSON 时使用）。"""
    return {
        "clash": {"linear_multiplier": 0.88, "label_zh": "冲"},
        "combine": {"linear_multiplier": 1.0, "label_zh": "合"},
        "punish": {"linear_multiplier": 0.93, "label_zh": "刑"},
        "harm": {"linear_multiplier": 0.94, "label_zh": "害"},
        "sanhe": {"linear_multiplier": 1.0, "label_zh": "三合"},
        "default": {"linear_multiplier": 0.92, "label_zh": "其他"},
    }


def _bounds(doc: Mapping[str, Any]) -> Dict[str, float]:
    b = doc.get("BOUNDS") if isinstance(doc.get("BOUNDS"), dict) else {}
    return {
        "aggregate_floor": float(b.get("aggregate_floor", 0.35) or 0.35),
        "per_point_floor": float(b.get("per_point_floor", 0.55) or 0.55),
    }


def _resolve_point_multiplier(doc: Mapping[str, Any], kind: str, detail: str) -> tuple[float, str, str]:
    """返回 (linear_multiplier, source_tag, manifest_entry_id)。"""
    detail_l = detail.lower()
    overrides = doc.get("OVERRIDES")
    if isinstance(overrides, list):
        for row in overrides:
            if not isinstance(row, dict):
                continue
            needle = str(row.get("detail_contains") or "").strip().lower()
            if needle and needle in detail_l:
                m = float(row.get("linear_multiplier", 0.9) or 0.9)
                eid = str(row.get("id") or row.get("manifest_entry_id") or "OVERRIDE").strip() or "OVERRIDE"
                src = f"Manifest_{eid}"
                return max(0.05, min(1.0, m)), src, eid
    kinds = doc.get("KIND_LINEAR") if isinstance(doc.get("KIND_LINEAR"), dict) else {}
    row = kinds.get(kind) if isinstance(kinds.get(kind), dict) else None
    if row is None and isinstance(kinds.get("default"), dict):
        row = kinds["default"]
    if row is None:
        row = _default_kind_table()["default"]
    m = float(row.get("linear_multiplier", 0.92) or 0.92)
    return max(0.05, min(1.0, m)), "KIND_DEFAULT", str(kind or "default")


def compute_conflict_topology_v1(
    metadata: Mapping[str, Any],
    *,
    doc: Optional[Mapping[str, Any]] = None,
    physics_config: Optional[Mapping[str, Any]] = None,
    branch_interactions: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    由 ``metadata.conflict_matrix.points`` 与法典生成拓扑块；``aggregate_conflict_linear_factor`` 为
    各点乘子之积（每点先夹到 ``per_point_floor..1``），再夹 ``aggregate_floor..1``。
    ``PAIR_DECAYS`` 在此基础上给出 ``element_conflict_mods``（五行场强额外乘子）。
    """
    cfg = dict(physics_config or {})
    if bool(cfg.get("CONFLICT_USE_LEGACY_GAMMA")):
        pts = _conflict_points(metadata)
        n = len(pts)
        gamma = float(cfg.get("conflict_penalty_gamma", 0.12) or 0.12)
        legacy = max(0.5, 1.0 - n * gamma)
        return {
            "version": "legacy_gamma",
            "aggregate_conflict_linear_factor": legacy,
            "entries": [
                {
                    "detail": str(p.get("detail") or ""),
                    "kind": str(p.get("kind") or ""),
                    "linear_multiplier": None,
                    "pct_change_display": None,
                    "source": "LEGACY_CONFLICT_PENALTY_GAMMA",
                    "manifest_entry_id": f"legacy_{i}",
                }
                for i, p in enumerate(pts)
            ],
            "element_conflict_mods": _identity_element_mods(),
            "manifest_path": str(get_conflict_manifest_path()),
        }

    try:
        loaded = dict(doc) if isinstance(doc, Mapping) else load_conflict_manifest()
    except (OSError, json.JSONDecodeError):
        loaded = {
            "ENGINE": {"schema_version": "0.0-fallback"},
            "KIND_LINEAR": _default_kind_table(),
            "OVERRIDES": [],
            "BOUNDS": {"aggregate_floor": 0.35, "per_point_floor": 0.55},
        }

    bounds = _bounds(loaded)
    per_floor = bounds["per_point_floor"]
    agg_floor = bounds["aggregate_floor"]

    bi = list(branch_interactions) if branch_interactions is not None else build_branch_interactions(metadata)

    pts = _conflict_points(metadata)
    entries: List[Dict[str, Any]] = []
    product = 1.0
    for i, p in enumerate(pts):
        kind = str(p.get("kind") or "default").strip().lower() or "default"
        detail = str(p.get("detail") or "")
        mult, src, eid = _resolve_point_multiplier(loaded, kind, detail)
        mult = max(per_floor, min(1.0, mult))
        product *= mult
        pct = round((mult - 1.0) * 1000) / 10.0
        entries.append(
            {
                "index": i,
                "detail": detail,
                "kind": kind,
                "linear_multiplier": mult,
                "pct_change_display": pct,
                "source": src,
                "manifest_entry_id": eid,
            }
        )

    aggregate = max(agg_floor, min(1.0, product))
    element_mods, pair_entries = _apply_pair_decays(loaded, bi)
    eng = loaded.get("ENGINE") if isinstance(loaded.get("ENGINE"), dict) else {}
    return {
        "version": str(eng.get("schema_version") or "0.2"),
        "aggregate_conflict_linear_factor": aggregate,
        "entries": entries + pair_entries,
        "element_conflict_mods": element_mods,
        "branch_interactions": bi,
        "manifest_path": str(get_conflict_manifest_path()),
        "source_plugin": "classical.conflict_auditor.v1",
    }


def _conflict_points(metadata: Mapping[str, Any]) -> List[Dict[str, Any]]:
    cm = metadata.get("conflict_matrix")
    if not isinstance(cm, dict):
        return []
    pts = cm.get("points")
    if not isinstance(pts, list):
        return []
    return [p for p in pts if isinstance(p, dict)]


def merge_conflict_topology_into_meta(meta: MutableMapping[str, Any], topology: Mapping[str, Any]) -> None:
    meta["conflict_topology_v1"] = dict(topology)


def run_conflict_auditor_v1(**ctx: Any) -> Dict[str, Any]:
    """Registry ``on_physics_complete``：将拓扑写回 ``physics_tensor.meta``（与 infer 内预计算一致，可幂等刷新）。"""
    physics_tensor = ctx.get("physics_tensor") or {}
    if not isinstance(physics_tensor, dict):
        return {"verdict": "", "evidence": [], "confidence_score": 1.0}
    metadata = ctx.get("metadata") or {}
    md = metadata if isinstance(metadata, dict) else {}
    rc = physics_tensor.get("meta") if isinstance(physics_tensor.get("meta"), dict) else {}
    runtime = rc.get("runtime_physics_config") if isinstance(rc.get("runtime_physics_config"), dict) else {}

    meta = physics_tensor.setdefault("meta", {})
    bi_existing = meta.get("branch_interactions") if isinstance(meta.get("branch_interactions"), list) else None
    branch_ix = bi_existing if bi_existing else build_branch_interactions(md)
    if isinstance(meta, dict) and not bi_existing:
        meta["branch_interactions"] = branch_ix

    topo = compute_conflict_topology_v1(md, physics_config=runtime, branch_interactions=branch_ix)
    if isinstance(meta, dict):
        merge_conflict_topology_into_meta(meta, topo)

    evidence: List[str] = []
    for e in topo.get("entries") or []:
        if not isinstance(e, dict):
            continue
        detail = str(e.get("detail") or "").strip() or "(无 detail)"
        mult = e.get("linear_multiplier")
        pct = e.get("pct_change_display")
        src = str(e.get("source") or "")
        mid = str(e.get("manifest_entry_id") or "")
        eloss = str(e.get("element_loss_display") or "").strip()
        if eloss:
            evidence.append(f"{detail} -> {eloss} (Source: {src}{' · ' + mid if mid else ''})")
        elif mult is not None and pct is not None:
            evidence.append(f"{detail} -> 线性能量 ×{mult} ({pct:+.1f}%) (Source: {src}{' · ' + mid if mid else ''})")
        else:
            evidence.append(f"{detail} [{src}]")

    return {
        "verdict": f"冲突拓扑：aggregate={topo.get('aggregate_conflict_linear_factor')}",
        "evidence": evidence,
        "confidence_score": 1.0,
        "topology": topo,
    }
