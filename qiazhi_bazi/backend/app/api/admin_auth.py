"""Admin HTTP 鉴权：仅依赖标准库与 FastAPI，避免经 `admin` 路由模块间接加载 DB。"""
from __future__ import annotations

import os
from typing import Optional

from fastapi import Header, HTTPException


def admin_token_guard(x_admin_token: Optional[str] = Header(default=None)) -> None:
    expected = os.getenv("QIAZHI_ADMIN_TOKEN")
    if not expected:
        return
    if not x_admin_token or x_admin_token != expected:
        raise HTTPException(status_code=401, detail="admin token 无效")
