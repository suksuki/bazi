from __future__ import annotations

import json
import re
from typing import Any, Dict


def extract_json_from_llm_text(raw: str) -> Dict[str, Any]:
    text = (raw or "").strip()
    if not text:
        return {}
    m = re.search(r"\{[\s\S]*\}", text)
    if not m:
        return {}
    try:
        return json.loads(m.group(0))
    except Exception:
        return {}
