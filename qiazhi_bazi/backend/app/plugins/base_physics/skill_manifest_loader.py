"""加载 `skill_manifest.json`（L1 算子 ↔ Skill ID ↔ 物理键）。"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List

_MANIFEST_PATH = Path(__file__).resolve().parent / "skill_manifest.json"


@lru_cache(maxsize=1)
def load_base_physics_skill_manifest() -> Dict[str, Any]:
    raw = _MANIFEST_PATH.read_text(encoding="utf-8")
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("skill_manifest.json root must be an object")
    return data


def reload_base_physics_skill_manifest_for_tests() -> Dict[str, Any]:
    load_base_physics_skill_manifest.cache_clear()
    return load_base_physics_skill_manifest()


def list_base_physics_skills() -> List[Dict[str, Any]]:
    skills = load_base_physics_skill_manifest().get("skills")
    return list(skills) if isinstance(skills, list) else []


def skill_id_for_l1_operator(operator_id: str) -> str:
    m = load_base_physics_skill_manifest().get("operator_to_skill")
    if not isinstance(m, dict):
        return str(operator_id)
    mapped = m.get(str(operator_id))
    return str(mapped) if mapped else str(operator_id)
