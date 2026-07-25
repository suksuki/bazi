from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from core.contracts.base import V50Model, require_non_empty


class PillarConstraint(V50Model):
    """A partial user target; legality is decided by the chart solver."""

    pillar: str = ""
    stem: str = ""
    branch: str = ""


class PillarTargetDraft(V50Model):
    version: str = "v50.pillar_target_draft.v1"
    target_draft_id: str
    year: PillarConstraint = Field(default_factory=PillarConstraint)
    month: PillarConstraint = Field(default_factory=PillarConstraint)
    day: PillarConstraint = Field(default_factory=PillarConstraint)
    hour: PillarConstraint = Field(default_factory=PillarConstraint)
    cycle_year_anchor: int | None = None
    boundary: str = "target_draft_is_a_constraint_set_and_never_a_chart_fact"

    @model_validator(mode="after")
    def _boundary(self) -> "PillarTargetDraft":
        require_non_empty(self.target_draft_id, "target_draft_id")
        return self


class ChartVariant(V50Model):
    version: str = "v50.chart_variant.v1"
    variant_id: str
    pillars: list[str]
    cycle_year_anchor: int | None = None
    presentation_distance: int = 0
    source_mode: str = "constraint_solver"

    @model_validator(mode="after")
    def _boundary(self) -> "ChartVariant":
        require_non_empty(self.variant_id, "variant_id")
        if len(self.pillars) != 4:
            raise ValueError("chart_variant_requires_four_pillars")
        return self


class ConstraintIssue(V50Model):
    field: str
    code: str
    detail: str = ""


class ChartResolution(V50Model):
    version: str = "v50.chart_resolution.v1"
    resolution_id: str
    target_draft_id: str
    status: Literal["no_solution", "single_solution", "multiple_solutions"]
    candidate_count: int = Field(ge=0)
    candidates: list[ChartVariant] = Field(default_factory=list)
    selected_variant: ChartVariant | None = None
    conflicts: list[ConstraintIssue] = Field(default_factory=list)
    releasable_constraints: list[str] = Field(default_factory=list)
    invalidated_constraints: list[ConstraintIssue] = Field(default_factory=list)
    cycle_year_anchor: int | None = None
    ranking_is_presentation_only: bool = True
    candidates_truncated: bool = False
    boundary: str = "only_a_single_solution_may_be_selected_without_user_choice"

    @model_validator(mode="after")
    def _boundary(self) -> "ChartResolution":
        require_non_empty(self.resolution_id, "resolution_id")
        require_non_empty(self.target_draft_id, "target_draft_id")
        if self.status == "single_solution" and self.selected_variant is None:
            raise ValueError("single_solution_requires_selected_variant")
        if self.status != "single_solution" and self.selected_variant is not None:
            raise ValueError("non_single_solution_cannot_select_variant")
        return self
