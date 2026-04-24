"""v17_rebirth 包内路径（避免写死 /home/hlsystem/...，便于 macOS / 多机部署）。"""
from __future__ import annotations

from pathlib import Path

# 本文件位于 qiazhi/v17_rebirth/paths.py → 包根即 v17_rebirth 目录
V17_REBIRTH_ROOT: Path = Path(__file__).resolve().parent
RUNTIME_DIR: Path = V17_REBIRTH_ROOT / ".runtime"
RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
