from __future__ import annotations

import time
from typing import Any, Callable, TypeVar

from pydantic import Field

from core.contracts.base import V50Model
from core.mingli_agent.context import ReasoningContextPack
from core.mingli_agent.model_policy import ModelRoute


T = TypeVar("T")


class CognitiveStageReceipt(V50Model):
    stage: str
    model: str
    context_hash: str
    fact_count: int
    knowledge_count: int
    artifact_type: str
    status: str
    duration_ms: int
    error_type: str = ""
    transport_total_ms: int | None = None
    load_duration_ms: int | None = None
    prompt_eval_count: int | None = None
    prompt_eval_duration_ms: int | None = None
    eval_count: int | None = None
    eval_duration_ms: int | None = None
    schema_attempts: int | None = None
    response_bytes: int | None = None


class CognitiveRunReceipt(V50Model):
    stage_receipts: list[CognitiveStageReceipt] = Field(default_factory=list)


class CognitiveOrchestrator:
    """Runs authorized cognition stages and records receipts without choosing a verdict."""

    def __init__(self) -> None:
        self._receipts: list[CognitiveStageReceipt] = []

    def reset(self) -> None:
        self._receipts = []

    def execute(
        self,
        *,
        stage: str,
        route: ModelRoute,
        context: ReasoningContextPack,
        artifact_type: str,
        operation: Callable[[], T],
    ) -> T:
        started = time.monotonic()
        try:
            result = operation()
        except Exception as exc:
            self._receipts.append(self._receipt(
                stage=stage,
                route=route,
                context=context,
                artifact_type=artifact_type,
                status="failed",
                started=started,
                error_type=type(exc).__name__,
            ))
            raise
        self._receipts.append(self._receipt(
            stage=stage,
            route=route,
            context=context,
            artifact_type=artifact_type,
            status="completed",
            started=started,
        ))
        return result

    def receipt(self) -> CognitiveRunReceipt:
        return CognitiveRunReceipt(stage_receipts=list(self._receipts))

    def annotate_last(self, *, stage: str, metrics: dict[str, Any] | None) -> None:
        if not metrics or not self._receipts:
            return
        index = next((index for index in range(len(self._receipts) - 1, -1, -1) if self._receipts[index].stage == stage), None)
        if index is None:
            return
        allowed = {
            "transport_total_ms",
            "load_duration_ms",
            "prompt_eval_count",
            "prompt_eval_duration_ms",
            "eval_count",
            "eval_duration_ms",
            "schema_attempts",
            "response_bytes",
        }
        self._receipts[index] = self._receipts[index].model_copy(
            update={key: value for key, value in metrics.items() if key in allowed}
        )

    @staticmethod
    def _receipt(
        *,
        stage: str,
        route: ModelRoute,
        context: ReasoningContextPack,
        artifact_type: str,
        status: str,
        started: float,
        error_type: str = "",
    ) -> CognitiveStageReceipt:
        return CognitiveStageReceipt(
            stage=stage,
            model=route.model,
            context_hash=context.content_hash,
            fact_count=len(context.fact_refs),
            knowledge_count=len(context.knowledge_refs),
            artifact_type=artifact_type,
            status=status,
            duration_ms=round((time.monotonic() - started) * 1000),
            error_type=error_type,
        )
