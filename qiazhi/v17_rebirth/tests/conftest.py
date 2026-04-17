"""V17 Rebirth pytest：仓库根下执行 `pytest qiazhi/v17_rebirth/tests`（依赖根目录 pytest.ini 的 pythonpath）。"""
from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def bazi_repo_root() -> Path:
    """…/bazi（含 qiazhi/v17_rebirth）。"""
    return Path(__file__).resolve().parents[3]
