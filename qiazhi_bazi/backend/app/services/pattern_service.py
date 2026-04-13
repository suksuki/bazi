"""V7.3：对外 Pattern API 用集中服务（纯 dict 载荷，路由层包 JSONResponse）。"""
from __future__ import annotations

from typing import Any, Dict, Optional

from app.logic.patterns.engine import UniversalPatternEngine, load_pattern_manifest
from app.services import pattern_manifest_admin as pma


class PatternService:
    """与 ``/api/v1/patterns/*`` 对齐；不抛业务异常，由路由固定返回 JSON。"""

    @staticmethod
    def reload_fingerprint() -> Dict[str, Any]:
        """只读磁盘法典并返回 ``sha256``；签名校验失败时 ``status: SIGNATURE_ERROR``。"""
        disk = load_pattern_manifest(None)
        if isinstance(disk, dict) and disk.get("status") == "SIGNATURE_ERROR":
            return dict(disk)
        return {"status": "ok", "sha256": pma.manifest_sha256(disk)}

    @staticmethod
    def evaluate_rows(
        physics_tensor: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        eng = UniversalPatternEngine()
        if eng.manifest_signature_error:
            return {**dict(eng.manifest_signature_error), "rows": []}
        rows = eng.evaluate(physics_tensor, metadata or {})
        return {"status": "ok", "rows": rows}
