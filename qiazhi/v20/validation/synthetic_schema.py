from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class SyntheticCase:
    case_id: str
    pillar_displays: tuple[str, str, str, str]
    expected_feature_domains: tuple[str, ...] = field(default_factory=tuple)
    expected_question_keys: tuple[str, ...] = field(default_factory=tuple)
    forbidden_text: tuple[str, ...] = ("发财", "破财", "疾病", "应期", "一定", "必然")
    mutation_invariants: tuple[str, ...] = ("no_rule_mutation", "no_answer_mutation", "no_core_fact_mutation")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
