"""Admin HTTP 鉴权：仅依赖标准库与 FastAPI，避免经 `admin` 路由模块间接加载 DB。"""
from __future__ import annotations

import os
from typing import Optional

from fastapi import Header, HTTPException

# 与 restart_local_services.sh / frontend .env.local.example 对齐；非生产环境可无 QIAZHI_ADMIN_TOKEN（使用回退令牌）。
_FALLBACK_ADMIN_TOKEN = "local-dev-qiazhi-admin"


def is_production_environment() -> bool:
    """与运维约定：`QIAZHI_ENV` / `ENV` 为 production|prod|live 即视为生产。"""
    v = (os.getenv("QIAZHI_ENV") or os.getenv("ENV") or "").strip().lower()
    return v in ("production", "prod", "live")


def _expected_admin_token() -> str:
    if is_production_environment():
        return (os.getenv("QIAZHI_ADMIN_TOKEN") or "").strip()
    raw = (os.getenv("QIAZHI_ADMIN_TOKEN") or "").strip()
    return raw if raw else _FALLBACK_ADMIN_TOKEN


def admin_token_guard(x_admin_token: Optional[str] = Header(default=None)) -> None:
    if is_production_environment():
        configured = (os.getenv("QIAZHI_ADMIN_TOKEN") or "").strip()
        if not configured:
            raise HTTPException(
                status_code=503,
                detail="生产环境必须配置 QIAZHI_ADMIN_TOKEN，禁止用法典/机房默认令牌。",
            )
    expected = _expected_admin_token()
    if not expected:
        raise HTTPException(status_code=503, detail="admin token 未配置")
    if not x_admin_token or str(x_admin_token).strip() != expected:
        raise HTTPException(status_code=401, detail="admin token 无效")
