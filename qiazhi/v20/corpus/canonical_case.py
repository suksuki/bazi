from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class CanonicalCase:
    case_id: str
    pillar_displays: tuple[str, str, str, str]
    corpus_space: str = "explicit_pillar_sample"
    calendar_assumption: str = "explicit_pillars_no_calendar_conversion"

    @property
    def input_hash(self) -> str:
        raw = "|".join((self.case_id, *self.pillar_displays, self.corpus_space, self.calendar_assumption))
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["input_hash"] = self.input_hash
        payload["guardrails"] = ["CORPUS_STRUCTURAL_MAP_ONLY", "NO_DESTINY_TRUTH_LABEL"]
        return payload
