"""加载盲派 skill_manifest.json（供插件 manifest 与 LLM 按需引用）。"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List


@lru_cache(maxsize=1)
def load_blind_skill_manifest() -> Dict[str, Any]:
    path = Path(__file__).resolve().parent / "skill_manifest.json"
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def list_blind_skills() -> List[Dict[str, Any]]:
    data = load_blind_skill_manifest()
    skills = data.get("skills")
    return list(skills) if isinstance(skills, list) else []
