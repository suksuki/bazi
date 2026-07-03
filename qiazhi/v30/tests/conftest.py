from __future__ import annotations

import os


def pytest_configure() -> None:
    os.environ.setdefault("V30_LLM_SYNC_MODE", "fast")
