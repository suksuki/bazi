from __future__ import annotations

from time import perf_counter
from typing import Any, Callable, TypeVar

from v20.orchestrator.schema import ReasoningOrchestrator, ReasoningStep


ORCHESTRATOR_VERSION = "v20.reasoning_orchestrator.v1"

T = TypeVar("T")


class ReasoningRecorder:
    def __init__(self) -> None:
        self._steps: list[ReasoningStep] = []

    def run(
        self,
        step_key: str,
        label: str,
        source: str,
        output_ref: str,
        fn: Callable[[], T],
        *,
        evidence_refs: tuple[str, ...] = (),
    ) -> T:
        started = perf_counter()
        result = fn()
        self.add(
            step_key,
            label,
            source,
            output_ref,
            evidence_refs=evidence_refs,
            elapsed_ms=(perf_counter() - started) * 1000,
        )
        return result

    def add(
        self,
        step_key: str,
        label: str,
        source: str,
        output_ref: str,
        *,
        status: str = "ready",
        evidence_refs: tuple[str, ...] = (),
        elapsed_ms: float = 0.0,
    ) -> None:
        self._steps.append(
            ReasoningStep(
                step_key=step_key,
                label=label,
                status=status,
                source=source,
                output_ref=output_ref,
                evidence_refs=evidence_refs,
                elapsed_ms=round(elapsed_ms, 3),
            )
        )

    def to_orchestrator(self, primary_outputs: dict[str, str]) -> dict[str, Any]:
        return build_reasoning_orchestrator(tuple(self._steps), primary_outputs)


def build_reasoning_orchestrator(
    steps: tuple[ReasoningStep, ...],
    primary_outputs: dict[str, str],
) -> dict[str, Any]:
    payload = ReasoningOrchestrator(
        version=ORCHESTRATOR_VERSION,
        status="ready" if steps else "empty",
        mode="deterministic_runtime_spine",
        steps=steps,
        primary_outputs=primary_outputs,
    )
    return payload.to_dict()
