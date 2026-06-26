from __future__ import annotations

from dataclasses import dataclass

from v20.interaction.questions import QuestionCandidate


@dataclass(frozen=True)
class QuestionSourceSpec:
    source_key: str
    phase: str
    order: int
    description: str


@dataclass(frozen=True)
class QuestionSourceBatch:
    source_key: str
    phase: str
    order: int
    count: int
    question_ids: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "source_key": self.source_key,
            "phase": self.phase,
            "order": self.order,
            "count": self.count,
            "question_ids": self.question_ids,
        }


QUESTION_SOURCE_SPECS: tuple[QuestionSourceSpec, ...] = (
    QuestionSourceSpec("runtime_fusion", "runtime", 10, "runtime decision fusion candidates"),
    QuestionSourceSpec("mainline", "decision", 20, "mainline decision candidates"),
    QuestionSourceSpec("portrait_axis", "portrait", 30, "portrait projection axis candidates"),
    QuestionSourceSpec("decision_hit", "decision", 40, "direct decision hit candidates"),
    QuestionSourceSpec("feature_hook", "feature", 50, "feature hook candidates"),
    QuestionSourceSpec("decision_loop", "decision", 60, "per-decision primary, secondary, and knowledge candidates"),
    QuestionSourceSpec("time_context", "time", 70, "explicit time layer candidates"),
    QuestionSourceSpec("seed_registry", "seed", 80, "role-aware seed question candidates"),
    QuestionSourceSpec("practitioner_refresh", "interaction", 90, "practitioner calibration refresh candidates"),
    QuestionSourceSpec("latent_event", "interaction", 100, "latent event calibration refresh candidates"),
    QuestionSourceSpec("fallback", "fallback", 900, "fallback structure overview candidate"),
)

QUESTION_SOURCE_BY_KEY = {row.source_key: row for row in QUESTION_SOURCE_SPECS}


class QuestionCandidateManifest:
    def __init__(self) -> None:
        self._batches: list[QuestionSourceBatch] = []

    def extend(self, source_key: str, rows: list[QuestionCandidate]) -> list[QuestionCandidate]:
        spec = QUESTION_SOURCE_BY_KEY[source_key]
        self._batches.append(
            QuestionSourceBatch(
                source_key=spec.source_key,
                phase=spec.phase,
                order=spec.order,
                count=len(rows),
                question_ids=tuple(row.question_id for row in rows if row.question_id),
            )
        )
        return rows

    def batches(self) -> tuple[QuestionSourceBatch, ...]:
        return tuple(self._batches)

    def to_dict(self) -> dict[str, object]:
        return {"batches": tuple(row.to_dict() for row in self._batches)}


def question_source_manifest() -> tuple[dict[str, object], ...]:
    return tuple(
        {
            "source_key": row.source_key,
            "phase": row.phase,
            "order": row.order,
            "description": row.description,
        }
        for row in QUESTION_SOURCE_SPECS
    )
