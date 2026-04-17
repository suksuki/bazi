"""Pytest 根配置：单元测试导入 app 前提供合法 DATABASE_URL（不实际连库）。"""
from __future__ import annotations

import os

os.environ.setdefault("DATABASE_URL", "postgresql://test:test@127.0.0.1:5432/test")
