from __future__ import annotations

from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from abu_v60.mingli.stage_contracts import MingliStageProjection

SYNTHETIC_EXPERIMENT_RUN_VERSION = "v60.mingli-synthetic-experiment-run.001"
SYNTHETIC_EXPERIMENT_SNAPSHOT_VERSION = (
    "v60.mingli-synthetic-experiment-snapshot.002"
)
SyntheticExperimentOutcome = Literal[
    "PASS",
    "PRODUCT_SAFE_MODEL_FAIL",
    "MODEL_FAIL",
    "INVALID_EXPERIMENT",
]


class SyntheticExperimentCheck(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    check_ref: str = Field(min_length=1)
    group: Literal["EXPERIMENT_VALIDITY", "MUST_HOLD", "EXPECTED_CHANGE"]
    status: Literal["PASS", "FAIL"]
    statement: str = Field(min_length=1)
    A: Any
    B: Any


class SyntheticExperimentIssueKeys(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    A: tuple[str, ...]
    B: tuple[str, ...]


class SyntheticExperimentEvaluation(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    evaluator_version: Literal["v60.mingli-synthetic-experiment-evaluator.001"]
    dev_gold_version: Literal["v60.mingli-synthetic-experiment-dev-gold.001"]
    dev_gold_hash: str = Field(min_length=64, max_length=64)
    outcome: SyntheticExperimentOutcome
    checks: tuple[SyntheticExperimentCheck, ...] = Field(min_length=1)
    server_issue_keys: SyntheticExperimentIssueKeys
    changed_pass_count: int = Field(ge=0)
    hold_pass_count: int = Field(ge=0)
    drift_checks: tuple[str, ...]
    qualification_effect: Literal["DEV_EVIDENCE_ONLY_NOT_METHOD_QUALIFICATION"]
    summary: str = Field(min_length=1)

    @model_validator(mode="after")
    def derived_counts_are_exact(self) -> SyntheticExperimentEvaluation:
        if len({item.check_ref for item in self.checks}) != len(self.checks):
            raise ValueError("mingli_synthetic_experiment_check_ref_duplicate")
        changed_pass_count = sum(
            item.group == "EXPECTED_CHANGE" and item.status == "PASS"
            for item in self.checks
        )
        hold_pass_count = sum(
            item.group == "MUST_HOLD" and item.status == "PASS"
            for item in self.checks
        )
        drift_checks = tuple(
            item.check_ref
            for item in self.checks
            if item.group == "MUST_HOLD" and item.status == "FAIL"
        )
        if (
            self.changed_pass_count != changed_pass_count
            or self.hold_pass_count != hold_pass_count
            or self.drift_checks != drift_checks
        ):
            raise ValueError("mingli_synthetic_experiment_derived_counts_invalid")
        validity_failed = any(
            item.group in {"EXPERIMENT_VALIDITY", "MUST_HOLD"}
            and item.status == "FAIL"
            for item in self.checks
        )
        expected_outcome = (
            "INVALID_EXPERIMENT"
            if validity_failed
            else "PRODUCT_SAFE_MODEL_FAIL"
            if self.server_issue_keys.A or self.server_issue_keys.B
            else "MODEL_FAIL"
            if any(
                item.group == "EXPECTED_CHANGE" and item.status == "FAIL"
                for item in self.checks
            )
            else "PASS"
        )
        if self.outcome != expected_outcome:
            raise ValueError("mingli_synthetic_experiment_outcome_invalid")
        return self


class SyntheticExperimentRunIdentity(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    run_version: Literal["v60.mingli-synthetic-experiment-run.001"]
    experiment_ref: str = Field(min_length=1)
    definition_hash: str = Field(min_length=64, max_length=64)
    evaluator_version: Literal["v60.mingli-synthetic-experiment-evaluator.001"]
    analysis_date: date
    member_a_agent_reading_ref: str = Field(min_length=1)
    member_b_agent_reading_ref: str = Field(min_length=1)
    member_a_stage_json: MingliStageProjection
    member_b_stage_json: MingliStageProjection
    outcome: SyntheticExperimentOutcome
    evaluation_json: SyntheticExperimentEvaluation

    @model_validator(mode="after")
    def run_bindings_are_consistent(self) -> SyntheticExperimentRunIdentity:
        if self.outcome != self.evaluation_json.outcome:
            raise ValueError("mingli_synthetic_experiment_run_outcome_mismatch")
        if self.evaluator_version != self.evaluation_json.evaluator_version:
            raise ValueError("mingli_synthetic_experiment_run_evaluator_mismatch")
        if self.member_a_agent_reading_ref == self.member_b_agent_reading_ref:
            raise ValueError("mingli_synthetic_experiment_run_readings_not_distinct")
        if (
            self.member_a_stage_json.subject_id
            == self.member_b_stage_json.subject_id
            or self.member_a_stage_json.case_ref == self.member_b_stage_json.case_ref
        ):
            raise ValueError("mingli_synthetic_experiment_run_members_not_distinct")
        return self
