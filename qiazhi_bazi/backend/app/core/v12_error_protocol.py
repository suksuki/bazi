"""V12 错误协议：将基础设施错误转为可读结构。"""
from __future__ import annotations

from typing import Any, Dict, List


def build_v12_error(
    *,
    code: str,
    user_message: str,
    diagnosis: str = "",
    hints: List[str] | None = None,
    extra: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    out = {
        "protocol": "V12_ERROR_PROTOCOL",
        "code": str(code or "UNKNOWN_ERROR"),
        "user_message": str(user_message or "系统异常，请稍后重试。"),
        "diagnosis": str(diagnosis or ""),
        "hints": [str(x) for x in (hints or []) if str(x).strip()],
    }
    if isinstance(extra, dict) and extra:
        out.update(extra)
    return out


__all__ = ["build_v12_error"]
