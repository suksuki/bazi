"""加载 `skill_manifest.json`（L1 算子 ↔ Skill ID ↔ 物理键）；支持 DB `causal_skills` 覆盖。"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List

_MANIFEST_PATH = Path(__file__).resolve().parent / "skill_manifest.json"


@lru_cache(maxsize=1)
def _file_skill_manifest_core() -> Dict[str, Any]:
    raw = _MANIFEST_PATH.read_text(encoding="utf-8")
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("skill_manifest.json root must be an object")
    return data


def load_base_physics_skill_manifest() -> Dict[str, Any]:
    data = dict(_file_skill_manifest_core())
    try:
        from app.core.physics.settings_manager import _load_operator_map_from_db, _load_skills_from_db

        db_ops = _load_operator_map_from_db()
        if db_ops:
            data["operator_to_skill"] = db_ops
        db_skills = _load_skills_from_db()
        if db_skills:
            data["skills"] = db_skills
    except Exception:
        pass
    return data


def reload_base_physics_skill_manifest_for_tests() -> Dict[str, Any]:
    _file_skill_manifest_core.cache_clear()
    from app.core.physics.settings_manager import reload_file_skill_manifest_cache

    reload_file_skill_manifest_cache()
    return load_base_physics_skill_manifest()


def list_base_physics_skills() -> List[Dict[str, Any]]:
    skills = load_base_physics_skill_manifest().get("skills")
    if not isinstance(skills, list):
        return []
    return [s for s in skills if isinstance(s, dict)]


def skill_id_for_l1_operator(operator_id: str) -> str:
    m = load_base_physics_skill_manifest().get("operator_to_skill")
    if not isinstance(m, dict):
        return str(operator_id)
    mapped = m.get(str(operator_id))
    return str(mapped) if mapped else str(operator_id)
