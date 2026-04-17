"""L2 配置驱动格局阈值：UniversalPatternEngine → meta.pattern_thresholds。"""
from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from typing import Any, Dict

from app.logic.patterns.engine import UniversalPatternEngine, get_pattern_manifest_path
from app.logic.patterns.l2_summary import l2_result_summary_zh, sanitize_pattern_headline_zh

_LOG = logging.getLogger(__name__)

_STRICT_V = "MANIFEST_V5.8_STRICT"


def run_pattern_detector_v2(**ctx: Any) -> Dict[str, Any]:
    """由 `PluginRegistry` 在 `on_physics_complete` 挂载；每次物理总线完成后写入 meta.pattern_thresholds。"""
    # V7.2：stdout 心跳（非 logging），便于容器/进程管理器一眼确认插件链已触达 L2。
    print(
        "[L2_HEARTBEAT] Engine V: MANIFEST_V5.8_STRICT is calling UniversalPatternEngine...",
        flush=True,
    )
    physics_tensor = ctx.get("physics_tensor") or {}
    if not isinstance(physics_tensor, dict):
        return {"verdict": "", "evidence": [], "confidence_score": 1.0}
    metadata = ctx.get("metadata") or {}
    md = metadata if isinstance(metadata, dict) else {}

    engine = UniversalPatternEngine()
    rows = engine.evaluate(physics_tensor, md)
    for r in rows:
        if isinstance(r, dict):
            r["engine_v"] = _STRICT_V
    _LOG.info("DEBUG: L2 Pattern Engine collision completed with %s matches.", len(rows))

    meta = physics_tensor.setdefault("meta", {})
    if isinstance(meta, dict):
        meta["pattern_thresholds"] = rows
        meta["pattern_thresholds_engine"] = "universal_manifest_v1"
        row_dicts = [r for r in rows if isinstance(r, dict)]
        summary = l2_result_summary_zh(row_dicts)
        headline = sanitize_pattern_headline_zh(summary if summary else "常规格")
        meta["l2_pattern_result_summary_v1"] = headline
        meta["hit_pattern_name"] = headline
        meta["l2_pattern_engine"] = _STRICT_V
        mp = get_pattern_manifest_path()
        if isinstance(mp, Path) and mp.is_file():
            meta["pattern_manifest_file_sha256"] = hashlib.sha256(mp.read_bytes()).hexdigest()

    return {
        "verdict": "",
        "evidence": [],
        "confidence_score": 1.0,
        "pattern_rows": rows,
    }
