from __future__ import annotations

import json
from pathlib import Path

from v40.contracts.evaluation import EvaluationCaseSpec


def load_evaluation_cases(path: str | Path) -> list[EvaluationCaseSpec]:
    artifact_path = Path(path)
    payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    rows = payload.get("cases", payload) if isinstance(payload, dict) else payload
    if not isinstance(rows, list):
        raise ValueError("evaluation case artifact must be a list or {'cases': [...]}")
    return [EvaluationCaseSpec.model_validate(row) for row in rows]
