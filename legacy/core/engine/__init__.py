"""
FDS 静态引擎：只读全息图谱与流形基准。
"""
from pathlib import Path
from typing import Any, Dict, List

_ATLAS_PATH = Path(__file__).resolve().parent / "static_atlas.json"


def load_static_atlas() -> Dict[str, Any]:
    """加载只读全息图谱（FDS 1.0 封卷版）。所有动态位移计算以此为基准。"""
    if not _ATLAS_PATH.exists():
        return {"schema": "", "patterns": [], "total_patterns": 0}
    with open(_ATLAS_PATH, "r", encoding="utf-8") as f:
        import json
        return json.load(f)
