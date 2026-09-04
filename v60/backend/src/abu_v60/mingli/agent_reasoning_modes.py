from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from abu_v60.provenance import content_hash, stable_ref

MINGLI_AGENT_REASONING_MODE_VERSION = "v60.mingli-agent-reasoning-mode.001"

MingliAgentReasoningMode = Literal["BLIND_READING", "RECONCILIATION"]


class MingliAgentReasoningModeContract(BaseModel):
    """Hash-locked boundary between chart-first judgment and reality calibration."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    contract_ref: str = Field(min_length=1)
    contract_hash: str = Field(min_length=64, max_length=64)
    contract_version: Literal["v60.mingli-agent-reasoning-mode.001"]
    reasoning_mode: MingliAgentReasoningMode
    admission_status: Literal["ACTIVE", "CONTRACT_RESERVED"]
    allowed_contexts: tuple[str, ...] = Field(min_length=1)
    forbidden_contexts: tuple[str, ...] = Field(min_length=1)
    base_blind_reading_required: bool
    observation_ledger_required: bool
    generation_allowed: bool
    creates_new_reading_revision: bool
    canonical_fact_write_allowed: Literal[False]
    read_only: Literal[True]

    @model_validator(mode="after")
    def boundary_is_valid(self) -> MingliAgentReasoningModeContract:
        if self.allowed_contexts != tuple(sorted(set(self.allowed_contexts))):
            raise ValueError("mingli_agent_mode_allowed_contexts_not_sorted_unique")
        if self.forbidden_contexts != tuple(sorted(set(self.forbidden_contexts))):
            raise ValueError("mingli_agent_mode_forbidden_contexts_not_sorted_unique")
        if set(self.allowed_contexts).intersection(self.forbidden_contexts):
            raise ValueError("mingli_agent_mode_context_overlap")
        if self.reasoning_mode == "BLIND_READING":
            if (
                self.admission_status != "ACTIVE"
                or self.base_blind_reading_required
                or self.observation_ledger_required
                or not self.generation_allowed
                or self.creates_new_reading_revision
            ):
                raise ValueError("mingli_agent_blind_mode_policy_invalid")
        elif (
            self.admission_status != "CONTRACT_RESERVED"
            or not self.base_blind_reading_required
            or not self.observation_ledger_required
            or self.generation_allowed
            or not self.creates_new_reading_revision
        ):
            raise ValueError("mingli_agent_reconciliation_mode_policy_invalid")
        identity = self.model_dump(
            mode="json",
            exclude={"contract_ref", "contract_hash"},
        )
        if self.contract_hash != content_hash(identity):
            raise ValueError("mingli_agent_mode_contract_hash_mismatch")
        if self.contract_ref != stable_ref("v60-mingli-agent-mode", identity):
            raise ValueError("mingli_agent_mode_contract_ref_mismatch")
        return self

    @classmethod
    def issue(cls, **values: Any) -> MingliAgentReasoningModeContract:
        identity = {
            "contract_version": MINGLI_AGENT_REASONING_MODE_VERSION,
            **values,
            "canonical_fact_write_allowed": False,
            "read_only": True,
        }
        return cls(
            contract_ref=stable_ref("v60-mingli-agent-mode", identity),
            contract_hash=content_hash(identity),
            **identity,
        )


BLIND_READING_CONTRACT = MingliAgentReasoningModeContract.issue(
    reasoning_mode="BLIND_READING",
    admission_status="ACTIVE",
    allowed_contexts=tuple(
        sorted(
            {
                "ADMITTED_KNOWLEDGE_AND_RULES",
                "CANONICAL_CHART_FACTS",
                "CURRENT_TIME_COORDINATES",
                "PROFESSIONAL_CASE_PACKET",
                "RESEARCH_CANDIDATES_MARKED_AS_CANDIDATES",
            }
        )
    ),
    forbidden_contexts=tuple(
        sorted(
            {
                "INTERACTIVE_EXPERIENCE_CHOICES",
                "HISTORICAL_QUESTIONS_AND_ANSWERS",
                "LIFECASE_EVENTS",
                "PREVIOUS_READING_PROSE",
                "PROFILE_LABELS",
                "REALITY_OBSERVATIONS",
                "SUBJECT_DISPLAY_NAME",
            }
        )
    ),
    base_blind_reading_required=False,
    observation_ledger_required=False,
    generation_allowed=True,
    creates_new_reading_revision=False,
)

RECONCILIATION_CONTRACT = MingliAgentReasoningModeContract.issue(
    reasoning_mode="RECONCILIATION",
    admission_status="CONTRACT_RESERVED",
    allowed_contexts=tuple(
        sorted(
            {
                "ADMITTED_OBSERVATION_LEDGER",
                "FROZEN_BLIND_READING",
                "USER_CONFIRMED_CORRECTIONS",
            }
        )
    ),
    forbidden_contexts=tuple(
        sorted(
            {
                "FICTIONAL_SCENE_AS_REALITY",
                "UNADMITTED_PROFILE_INFERENCE",
                "UNSOURCED_LIFE_EVENTS",
            }
        )
    ),
    base_blind_reading_required=True,
    observation_ledger_required=True,
    generation_allowed=False,
    creates_new_reading_revision=True,
)

MINGLI_AGENT_REASONING_MODE_REGISTRY = {
    BLIND_READING_CONTRACT.reasoning_mode: BLIND_READING_CONTRACT,
    RECONCILIATION_CONTRACT.reasoning_mode: RECONCILIATION_CONTRACT,
}
