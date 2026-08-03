from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from abu_v60.mingli.synthetic_suite_contracts import SyntheticSuiteCandidateIdentity
from abu_v60.provenance import content_hash

SYNTHETIC_SUITE_RUN_REQUEST_VERSION = "v60.mingli-synthetic-suite-run-request.001"
SYNTHETIC_TRAINING_STATUS_VERSION = "v60.mingli-synthetic-training-status.001"

SyntheticSuiteRunRequestStatus = Literal[
    "QUEUED",
    "RUNNING",
    "SEALING",
    "SUCCEEDED",
    "FAILED",
]
SyntheticSuiteRunProgressEvent = Literal[
    "QUEUED",
    "START",
    "SEALED",
    "ERROR",
    "SEALING",
    "SUCCEEDED",
    "FAILED",
]
SyntheticTrainingReviewDisposition = Literal[
    "MODEL_INDEPENDENT_DEV",
    "CANDIDATE_REVISION_REQUIRED",
    "EXPERIMENT_REVISION_REQUIRED",
    "EXECUTION_REPAIR_REQUIRED",
]


class SyntheticSuiteRunRequestInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_version: Literal["v60.mingli-synthetic-suite-run-request.001"] = (
        SYNTHETIC_SUITE_RUN_REQUEST_VERSION
    )
    suite_ref: str = Field(min_length=1, max_length=180)
    expected_suite_definition_hash: str = Field(min_length=64, max_length=64)
    expected_execution_fingerprint: str = Field(min_length=64, max_length=64)
    idempotency_key: str = Field(min_length=1, max_length=180)


class SyntheticSuiteRunRequestProjection(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    request_version: Literal["v60.mingli-synthetic-suite-run-request.001"]
    request_ref: str = Field(min_length=1)
    request_hash: str = Field(min_length=64, max_length=64)
    suite_ref: str = Field(min_length=1)
    suite_definition_hash: str = Field(min_length=64, max_length=64)
    candidate_identity: SyntheticSuiteCandidateIdentity
    candidate_identity_hash: str = Field(min_length=64, max_length=64)
    execution_fingerprint: str = Field(min_length=64, max_length=64)
    status: SyntheticSuiteRunRequestStatus
    progress_event: SyntheticSuiteRunProgressEvent
    current_position: int = Field(ge=0)
    completed_count: int = Field(ge=0)
    total_count: int = Field(ge=1)
    current_experiment_ref: str | None = None
    suite_run_ref: str | None = None
    suite_run_hash: str | None = None
    review_disposition: SyntheticTrainingReviewDisposition | None = None
    error_code: str | None = None
    created_at: datetime
    updated_at: datetime
    projection_hash: str = Field(min_length=64, max_length=64)

    @model_validator(mode="after")
    def state_is_coherent(self) -> SyntheticSuiteRunRequestProjection:
        if self.completed_count > self.total_count or self.current_position > self.total_count:
            raise ValueError("mingli_synthetic_training_progress_invalid")
        completed = self.status == "SUCCEEDED"
        failed = self.status == "FAILED"
        if completed != bool(
            self.suite_run_ref and self.suite_run_hash and self.review_disposition
        ):
            raise ValueError("mingli_synthetic_training_result_invalid")
        if not completed and self.review_disposition is not None:
            raise ValueError("mingli_synthetic_training_disposition_invalid")
        if failed != bool(self.error_code):
            raise ValueError("mingli_synthetic_training_error_invalid")
        return self


def synthetic_training_execution_fingerprint(
    *,
    suite_definition_hash: str,
    candidate_identity_hash: str,
    runner_version: str,
    experiment_contracts: tuple[dict[str, str], ...],
) -> str:
    return content_hash(
        {
            "suite_definition_hash": suite_definition_hash,
            "candidate_identity_hash": candidate_identity_hash,
            "runner_version": runner_version,
            "experiment_contracts": experiment_contracts,
        }
    )
