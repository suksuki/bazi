from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class ReasoningStep:
    step_key: str
    label: str
    status: str
    source: str
    output_ref: str
    evidence_refs: tuple[str, ...] = ()
    elapsed_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ReasoningOrchestrator:
    version: str
    status: str
    mode: str
    steps: tuple[ReasoningStep, ...]
    primary_outputs: dict[str, str]
    runtime_mutation: bool = False
    guardrails: tuple[str, ...] = (
        "ORCHESTRATOR_IS_DETERMINISTIC_RUNTIME_SPINE",
        "ORCHESTRATOR_COORDINATES_MODULES_NOT_REPLACING_RULES",
        "LLM_CAN_EXPLAIN_NOT_OVERRIDE_ARBITRATION",
        "TRACE_SUMMARIES_EXCLUDE_SECRET_VALUES",
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "status": self.status,
            "mode": self.mode,
            "step_count": len(self.steps),
            "steps": [row.to_dict() for row in self.steps],
            "primary_outputs": dict(self.primary_outputs),
            "runtime_mutation": self.runtime_mutation,
            "guardrails": list(self.guardrails),
        }


@dataclass(frozen=True)
class MainlineCandidate:
    candidate_key: str
    title: str
    domain: str
    nodes: tuple[str, ...]
    score: float
    status: str
    source: str
    evidence: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
