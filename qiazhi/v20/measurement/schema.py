from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class MeasurementTopic:
    topic_key: str
    label: str
    stage: str
    status: str
    confidence: float
    source_feature_ids: tuple[str, ...]
    question_keys: tuple[str, ...]
    answer_section_titles: tuple[str, ...]
    boundary: str
    role: str = "bazi_measurement_topic"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MeasurementReport:
    version: str
    core_focus: str
    selected_question_key: str
    topics: tuple[MeasurementTopic, ...]
    applied_domain_keys: tuple[str, ...]
    portrait_role: str
    guardrails: tuple[str, ...] = (
        "MEASUREMENT_REPORT_IS_RUNTIME_VIEW",
        "FEATURE_SPINE_REMAINS_SOURCE_OF_TRUTH",
        "PORTRAIT_QUESTIONS_AND_ANSWERS_SHARE_TOPIC_CONTRACT",
        "NO_UNBOUNDED_PREDICTION",
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "core_focus": self.core_focus,
            "selected_question_key": self.selected_question_key,
            "topic_count": len(self.topics),
            "topics": [row.to_dict() for row in self.topics],
            "applied_domain_keys": list(self.applied_domain_keys),
            "portrait_role": self.portrait_role,
            "guardrails": list(self.guardrails),
        }
