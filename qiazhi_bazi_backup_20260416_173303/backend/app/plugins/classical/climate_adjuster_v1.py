"""
V8.0+ 调候：从 ``climate_manifest.json`` 读取月令五行乘子，写入 ``meta.climate_field_correction_v1``，
供 ``UniversalPatternEngine`` 与 ``PhysicsInferenceSkill`` 场强计算共用（单一数据源）。

``ClimateInferenceSkill.apply_climate_correction`` 仍为矢量/十神 Abs 的独立硬修正通道，与 manifest 月令表解耦。
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Mapping, MutableMapping, Optional

_ELEMENTS = ("wood", "fire", "earth", "metal", "water")
_MANIFEST_DIR = Path(__file__).resolve().parent
_DEFAULT_MANIFEST = _MANIFEST_DIR / "climate_manifest.json"


def get_climate_manifest_path() -> Path:
    raw = (os.environ.get("QIAZHI_CLIMATE_MANIFEST_PATH") or "").strip()
    if raw:
        return Path(raw).expanduser().resolve()
    return _DEFAULT_MANIFEST


def load_climate_manifest(source: Optional[Mapping[str, Any] | str | Path] = None) -> Dict[str, Any]:
    if source is None:
        p = get_climate_manifest_path()
        return json.loads(p.read_text(encoding="utf-8"))
    if isinstance(source, (str, Path)):
        return json.loads(Path(source).read_text(encoding="utf-8"))
    if isinstance(source, Mapping):
        return dict(source)
    raise TypeError("source must be None, Path/str, or Mapping")


def _mods_from_row(row: Mapping[str, Any]) -> Dict[str, float]:
    out: Dict[str, float] = {}
    for el in _ELEMENTS:
        km = f"{el}_mod"
        if km in row:
            out[el] = float(row[km])
        elif el in row:
            out[el] = float(row[el])
    for el in _ELEMENTS:
        out.setdefault(el, 1.0)
    return out


def _lookup_table(table: Any, month_branch: str) -> Optional[Dict[str, Any]]:
    if not isinstance(table, list):
        return None
    mb = str(month_branch or "").strip()
    if not mb:
        return None
    for row in table:
        if not isinstance(row, dict):
            continue
        key = str(row.get("month_branch") or row.get("month") or "").strip()
        if key == mb:
            return row
    return None


def _resolve_month_branch(physics_tensor: Dict[str, Any], metadata: Mapping[str, Any]) -> str:
    meta = physics_tensor.get("meta") if isinstance(physics_tensor.get("meta"), dict) else {}
    mb = str(meta.get("month_branch") or "").strip()
    if mb:
        return mb
    pillars = metadata.get("pillars") if isinstance(metadata, dict) else None
    if isinstance(pillars, dict):
        month = pillars.get("month")
        if isinstance(month, dict):
            b = str(month.get("branch") or "").strip()
            if b:
                return b
    return ""


def apply_climate_manifest_to_meta(
    meta: MutableMapping[str, Any],
    metadata: Mapping[str, Any],
    *,
    doc: Optional[Mapping[str, Any]] = None,
) -> Dict[str, float]:
    """
    将 ``climate_manifest.json`` 表写入 ``meta['climate_field_correction_v1']``，并返回五行乘子
    ``{wood, fire, earth, metal, water}``（供 ``build_energy_fields`` 等作为场强乘子使用）。
    """
    loaded = dict(doc) if isinstance(doc, Mapping) else load_climate_manifest()
    table = loaded.get("TABLE") or loaded.get("rows") or []
    mb = _resolve_month_branch({"meta": dict(meta)}, metadata)
    row = _lookup_table(table, mb)
    element_mods = _mods_from_row(row) if row else {el: 1.0 for el in _ELEMENTS}
    meta["climate_field_correction_v1"] = {
        "version": str((loaded.get("ENGINE") or {}).get("schema_version") or "0.1"),
        "month_branch": mb or None,
        "element_mods": dict(element_mods),
        "source": "classical.climate_adjuster.v1",
        "manifest_path": str(get_climate_manifest_path()),
    }
    return dict(element_mods)


def run_climate_adjuster_v1(**ctx: Any) -> Dict[str, Any]:
    """Registry ``on_physics_complete``：写入 ``meta.climate_field_correction_v1``，不修改 deity_scores。"""
    physics_tensor = ctx.get("physics_tensor") or {}
    if not isinstance(physics_tensor, dict):
        return {"verdict": "", "evidence": [], "confidence_score": 1.0}
    metadata = ctx.get("metadata") or {}
    md = metadata if isinstance(metadata, dict) else {}

    meta = physics_tensor.setdefault("meta", {})
    if not isinstance(meta, dict):
        return {"verdict": "", "evidence": [], "confidence_score": 1.0}
    element_mods = apply_climate_manifest_to_meta(meta, md)

    return {"verdict": "", "evidence": [], "confidence_score": 1.0, "climate_element_mods": dict(element_mods)}
