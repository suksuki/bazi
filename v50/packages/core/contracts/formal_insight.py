from __future__ import annotations

from typing import Any, Literal

from pydantic import model_validator

from core.contracts.base import V50Model
from core.contracts.professional_review import PersistenceStatus, ProfessionalReleaseStatus


FormalInsightLifecycle = Literal["draft", "partial", "reviewed", "committed", "failed"]


class FormalInsightLifecycleState(V50Model):
    """One cognition attempt and its downstream formal-use boundary."""

    version: str = "deepbazi.formal_insight_lifecycle_state.v1"
    status: FormalInsightLifecycle = "draft"
    persistence_status: PersistenceStatus = "draft"
    professional_release_status: ProfessionalReleaseStatus = "unreviewed"
    complete: bool = False
    active: bool = True
    formal_projection_eligible: bool = False
    role_projection_eligible: bool = False
    path_assertion_eligible: bool = False
    reminder_eligible: bool = False
    hidden_attribute_evidence_eligible: bool = False

    @model_validator(mode="before")
    @classmethod
    def derive_safety_boundary(cls, value: Any) -> Any:
        if not isinstance(value, dict):
            return value
        normalized = dict(value)
        status = str(normalized.get("status") or "draft")
        complete = status in {"reviewed", "committed"}
        active = bool(normalized.get("active", True))
        persistence = str(normalized.get("persistence_status") or "")
        if persistence not in {"draft", "persisted", "failed"}:
            persistence = "persisted" if status == "committed" else "failed" if status == "failed" else "draft"
        release = str(normalized.get("professional_release_status") or "unreviewed")
        eligible = (
            status == "committed"
            and complete
            and active
            and persistence == "persisted"
            and release in {"passed", "partially_blocked"}
        )
        normalized.update({
            "complete": complete,
            "persistence_status": persistence,
            "professional_release_status": release,
            "formal_projection_eligible": eligible,
            "role_projection_eligible": eligible,
            "path_assertion_eligible": eligible and release == "passed",
            "reminder_eligible": eligible and release == "passed",
            "hidden_attribute_evidence_eligible": eligible and release == "passed",
        })
        return normalized


__all__ = ["FormalInsightLifecycle", "FormalInsightLifecycleState"]
