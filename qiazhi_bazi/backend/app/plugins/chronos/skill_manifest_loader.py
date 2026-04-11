from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List

_PATH = Path(__file__).resolve().parent / "skill_manifest.json"


@lru_cache(maxsize=1)
def load_chronos_skill_manifest() -> Dict[str, Any]:
    data = json.loads(_PATH.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("chronos skill_manifest root must be object")
    return data


def list_chronos_skills() -> List[Dict[str, Any]]:
    raw = load_chronos_skill_manifest().get("skills")
    return list(raw) if isinstance(raw, list) else []
