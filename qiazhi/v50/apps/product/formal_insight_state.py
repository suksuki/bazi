from __future__ import annotations

from typing import Any, Literal

from core.contracts import FormalInsightLifecycleState


OperationalCognitionStatus = Literal[
    "not_started",
    "queued",
    "running",
    "completed",
    "completed_local",
    "completed_partial",
    "failed",
    "superseded",
]


def cognition_background(
    existing: dict[str, Any] | None = None,
    *,
    operational_status: OperationalCognitionStatus,
    insight_status: Literal["draft", "partial", "reviewed", "committed", "failed"],
    active: bool = True,
    persistence_status: Literal["draft", "persisted", "failed"] | None = None,
    professional_release_status: Literal[
        "unreviewed", "passed", "blocked", "partially_blocked"
    ] = "unreviewed",
    **updates: Any,
) -> dict[str, Any]:
    """Persist one lifecycle vocabulary and derive every downstream safety flag."""

    lifecycle = FormalInsightLifecycleState(
        status=insight_status,
        active=active,
        persistence_status=(
            persistence_status
            or (
                "persisted"
                if insight_status == "committed"
                else "failed"
                if insight_status == "failed"
                else "draft"
            )
        ),
        professional_release_status=professional_release_status,
    )
    return {
        **(existing or {}),
        **updates,
        "status": operational_status,
        "insight_status": insight_status,
        "insight_safety": lifecycle.model_dump(mode="json"),
    }


def lifecycle_from_background(
    background: dict[str, Any] | None,
    *,
    committed: bool = False,
    active: bool = True,
) -> FormalInsightLifecycleState:
    payload = background if isinstance(background, dict) else {}
    stored = payload.get("insight_safety")
    if isinstance(stored, dict):
        return FormalInsightLifecycleState.model_validate({**stored, "active": active})
    status = str(payload.get("insight_status") or "")
    if committed:
        status = "committed"
    elif status not in {"draft", "partial", "reviewed", "committed", "failed"}:
        operational = str(payload.get("status") or "")
        status = (
            "partial"
            if operational == "completed_partial" or bool(payload.get("partial_result"))
            else "failed"
            if operational == "failed"
            else "draft"
        )
    return FormalInsightLifecycleState(status=status, active=active)


__all__ = ["cognition_background", "lifecycle_from_background"]
