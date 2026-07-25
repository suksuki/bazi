from __future__ import annotations

import re

from core.mingli_agent.contracts import CognitiveHypothesis


def _unique(values: list[str]) -> list[str]:
    output: list[str] = []
    for value in values:
        if value and value not in output:
            output.append(value)
    return output

def _hypothesis_signature(hypothesis: CognitiveHypothesis) -> str:
    text = f"{hypothesis.name} {hypothesis.thesis}".lower()
    return re.sub(r"[^0-9a-z\u4e00-\u9fff]", "", text)
