"""Admin HTTP 鉴权：仅依赖标准库与 FastAPI，避免经 `admin` 路由模块间接加载 DB。"""
from __future__ import annotations

import os
from typing import Optional

from fastapi import Header, HTTPException

# 与 restart_local_services.sh / frontend .env.local.example 对齐；未配置 env 时不再 503，仍须请求头匹配。
_FALLBACK_ADMIN_TOKEN = "local-dev-qiazhi-admin"


def _expected_admin_token() -> str:
    raw = (os.getenv("QIAZHI_ADMIN_TOKEN") or "").strip()
    return raw if raw else _FALLBACK_ADMIN_TOKEN


def admin_token_guard(x_admin_token: Optional[str] = Header(default=None)) -> None:
    expected = _expected_admin_token()
    if not x_admin_token or str(x_admin_token).strip() != expected:
        raise HTTPException(status_code=401, detail="admin token 无效")
