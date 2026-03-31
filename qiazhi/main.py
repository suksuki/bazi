"""Qiazhi-Bazi 启动入口（MVP）。"""
from __future__ import annotations

import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
for p in (_REPO, _REPO / "legacy", _REPO / "qiazhi"):
    s = str(p)
    if s not in sys.path:
        sys.path.insert(0, s)


def main() -> None:
    import uvicorn

    uvicorn.run(
        "qiazhi_core.main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
    )


if __name__ == "__main__":
    main()
