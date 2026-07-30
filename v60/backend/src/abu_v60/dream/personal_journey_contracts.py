from __future__ import annotations

from datetime import date
from typing import Any, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from abu_v60.provenance import content_hash, stable_ref

DREAM_PRIVATE_INQUIRY_VERSION = "v60.dream-private-inquiry.001"
DREAM_PERSONAL_OBSERVATION_VERSION = (
    "v60.dream-personal-observation.001"
)
DREAM_PERSONAL_CHECKIN_VERSION = "v60.dream-personal-check-in.001"
DREAM_PERSONAL_JOURNEY_VERSION = "v60.dream-personal-journey.001"

DreamLifeDomain = Literal["career", "wealth", "relationship"]
DreamPersonalCheckInStatus = Literal[
    "OBSERVED",
    "NOT_OBSERVED",
    "STILL_OBSERVING",
]


def _normalize_private_text(value: str) -> str:
    normalized = " ".join(value.split())
    if any(ord(character) < 32 for character in normalized):
        raise ValueError("dream_private_text_control_character_forbidden")
    return normalized


class DreamPrivateInquiryRequest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    domain: DreamLifeDomain
    question: str = Field(min_length=4, max_length=120)
    idempotency_key: str = Field(min_length=1, max_length=180)

    @field_validator("question")
    @classmethod
    def normalize_question(cls, value: str) -> str:
        normalized = _normalize_private_text(value)
        if len(normalized) < 4:
            raise ValueError("dream_private_inquiry_too_short")
        return normalized


class DreamPersonalObservationRequest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    inquiry_ref: str = Field(min_length=1)
    inquiry_hash: str = Field(min_length=64, max_length=64)
    option_ref: str = Field(min_length=1)
    idempotency_key: str = Field(min_length=1, max_length=180)


class DreamPersonalCheckInRequest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    task_ref: str = Field(min_length=1)
    task_hash: str = Field(min_length=64, max_length=64)
    status: DreamPersonalCheckInStatus
    note: str | None = Field(default=None, max_length=160)
    idempotency_key: str = Field(min_length=1, max_length=180)

    @field_validator("note")
    @classmethod
    def normalize_note(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = _normalize_private_text(value)
        return normalized or None


class DreamPrivateInquiryRecord(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    contract_version: Literal[
        "v60.dream-private-inquiry.001"
    ] = DREAM_PRIVATE_INQUIRY_VERSION
    inquiry_ref: str = Field(min_length=1)
    inquiry_hash: str = Field(min_length=64, max_length=64)
    viewer_account_ref: str = Field(min_length=1)
    case_ref: str = Field(min_length=1)
    life_case_revision_ref: str = Field(min_length=1)
    reading_ref: str = Field(min_length=1)
    reading_hash: str = Field(min_length=64, max_length=64)
    domain: DreamLifeDomain
    question: str = Field(min_length=4, max_length=120)
    candidate_ref: str = Field(min_length=1)
    candidate_hash: str = Field(min_length=64, max_length=64)
    public_alias: str = Field(min_length=1)
    actor_ref: str = Field(min_length=1)
    tree_ref: str = Field(min_length=1)
    encounter_ref: str = Field(min_length=1)
    episode_question_ref: str = Field(min_length=1)
    supersedes_inquiry_ref: str | None
    supersedes_inquiry_hash: str | None = Field(
        default=None,
        min_length=64,
        max_length=64,
    )
    idempotency_key: str = Field(min_length=1, max_length=180)
    matched_by: Literal["EXACT_USER_SELECTED_DOMAIN"]
    private_to_account: Literal[True]
    owner_self_report_only: Literal[True]
    mingli_evidence_role: Literal["NOT_MINGLI_EVIDENCE"]
    reading_used_to_select_candidate: Literal[False]
    llm_interpretation_used: Literal[False]
    dream_answers_owner_question: Literal[False]
    tree_candidate_set_or_order_changed: Literal[False]
    chapter_route_changed: Literal[False]
    episode_question_changed: Literal[False]
    answer_changed: Literal[False]
    npc_choice_changed: Literal[False]
    world_outcome_changed: Literal[False]
    mingli_write_allowed: Literal[False]
    decision_write_allowed: Literal[False]
    knowledge_write_allowed: Literal[False]

    @model_validator(mode="after")
    def identity_is_valid(self) -> DreamPrivateInquiryRecord:
        if (self.supersedes_inquiry_ref is None) != (
            self.supersedes_inquiry_hash is None
        ):
            raise ValueError(
                "dream_private_inquiry_supersession_identity_incomplete"
            )
        identity = self.model_dump(
            mode="json",
            exclude={"inquiry_ref", "inquiry_hash"},
        )
        if self.inquiry_hash != content_hash(identity):
            raise ValueError("dream_private_inquiry_hash_mismatch")
        if self.inquiry_ref != stable_ref(
            "v60-dream-private-inquiry",
            identity,
        ):
            raise ValueError("dream_private_inquiry_ref_mismatch")
        return self

    @classmethod
    def issue(cls, **values: Any) -> DreamPrivateInquiryRecord:
        identity = {
            "contract_version": DREAM_PRIVATE_INQUIRY_VERSION,
            **values,
            "matched_by": "EXACT_USER_SELECTED_DOMAIN",
            "private_to_account": True,
            "owner_self_report_only": True,
            "mingli_evidence_role": "NOT_MINGLI_EVIDENCE",
            "reading_used_to_select_candidate": False,
            "llm_interpretation_used": False,
            "dream_answers_owner_question": False,
            "tree_candidate_set_or_order_changed": False,
            "chapter_route_changed": False,
            "episode_question_changed": False,
            "answer_changed": False,
            "npc_choice_changed": False,
            "world_outcome_changed": False,
            "mingli_write_allowed": False,
            "decision_write_allowed": False,
            "knowledge_write_allowed": False,
        }
        return cls(
            inquiry_ref=stable_ref("v60-dream-private-inquiry", identity),
            inquiry_hash=content_hash(identity),
            **identity,
        )


class DreamPersonalObservationOption(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    option_ref: str = Field(min_length=1)
    inquiry_ref: str = Field(min_length=1)
    domain: DreamLifeDomain
    label: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    checkpoint_days: Literal[7]

    @model_validator(mode="after")
    def identity_is_valid(self) -> DreamPersonalObservationOption:
        identity = self.model_dump(mode="json", exclude={"option_ref"})
        if self.option_ref != stable_ref(
            "v60-dream-personal-observation-option",
            identity,
        ):
            raise ValueError(
                "dream_personal_observation_option_ref_mismatch"
            )
        return self

    @classmethod
    def issue(
        cls,
        *,
        inquiry_ref: str,
        domain: DreamLifeDomain,
        label: str,
        summary: str,
    ) -> DreamPersonalObservationOption:
        identity = {
            "inquiry_ref": inquiry_ref,
            "domain": domain,
            "label": label,
            "summary": summary,
            "checkpoint_days": 7,
        }
        return cls(
            option_ref=stable_ref(
                "v60-dream-personal-observation-option",
                identity,
            ),
            inquiry_ref=inquiry_ref,
            domain=domain,
            label=label,
            summary=summary,
            checkpoint_days=7,
        )


class DreamPersonalObservationTask(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    contract_version: Literal[
        "v60.dream-personal-observation.001"
    ] = DREAM_PERSONAL_OBSERVATION_VERSION
    task_ref: str = Field(min_length=1)
    task_hash: str = Field(min_length=64, max_length=64)
    viewer_account_ref: str = Field(min_length=1)
    inquiry_ref: str = Field(min_length=1)
    inquiry_hash: str = Field(min_length=64, max_length=64)
    encounter_ref: str = Field(min_length=1)
    option: DreamPersonalObservationOption
    checkpoint_on: date
    idempotency_key: str = Field(min_length=1, max_length=180)
    semantics: Literal["PRIVATE_REALITY_OBSERVATION_ONLY"]
    private_to_account: Literal[True]
    owner_self_report_only: Literal[True]
    mingli_evidence_role: Literal["NOT_MINGLI_EVIDENCE"]
    dream_result_validates_owner_question: Literal[False]
    tree_candidate_set_or_order_changed: Literal[False]
    chapter_route_changed: Literal[False]
    episode_question_changed: Literal[False]
    answer_changed: Literal[False]
    npc_choice_changed: Literal[False]
    world_outcome_changed: Literal[False]
    mingli_write_allowed: Literal[False]
    decision_write_allowed: Literal[False]
    knowledge_write_allowed: Literal[False]

    @model_validator(mode="after")
    def identity_is_valid(self) -> DreamPersonalObservationTask:
        identity = self.model_dump(
            mode="json",
            exclude={"task_ref", "task_hash"},
        )
        if self.task_hash != content_hash(identity):
            raise ValueError("dream_personal_observation_hash_mismatch")
        if self.task_ref != stable_ref(
            "v60-dream-personal-observation",
            identity,
        ):
            raise ValueError("dream_personal_observation_ref_mismatch")
        return self

    @classmethod
    def issue(cls, **values: Any) -> DreamPersonalObservationTask:
        identity = {
            "contract_version": DREAM_PERSONAL_OBSERVATION_VERSION,
            **values,
            "semantics": "PRIVATE_REALITY_OBSERVATION_ONLY",
            "private_to_account": True,
            "owner_self_report_only": True,
            "mingli_evidence_role": "NOT_MINGLI_EVIDENCE",
            "dream_result_validates_owner_question": False,
            "tree_candidate_set_or_order_changed": False,
            "chapter_route_changed": False,
            "episode_question_changed": False,
            "answer_changed": False,
            "npc_choice_changed": False,
            "world_outcome_changed": False,
            "mingli_write_allowed": False,
            "decision_write_allowed": False,
            "knowledge_write_allowed": False,
        }
        normalized = {
            key: (
                value.model_dump(mode="json")
                if isinstance(value, BaseModel)
                else value
            )
            for key, value in identity.items()
        }
        return cls(
            task_ref=stable_ref(
                "v60-dream-personal-observation",
                normalized,
            ),
            task_hash=content_hash(normalized),
            **normalized,
        )


class DreamPersonalCheckInRecord(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    contract_version: Literal[
        "v60.dream-personal-check-in.001"
    ] = DREAM_PERSONAL_CHECKIN_VERSION
    checkin_ref: str = Field(min_length=1)
    checkin_hash: str = Field(min_length=64, max_length=64)
    viewer_account_ref: str = Field(min_length=1)
    inquiry_ref: str = Field(min_length=1)
    inquiry_hash: str = Field(min_length=64, max_length=64)
    task_ref: str = Field(min_length=1)
    task_hash: str = Field(min_length=64, max_length=64)
    previous_checkin_ref: str | None
    previous_checkin_hash: str | None = Field(
        default=None,
        min_length=64,
        max_length=64,
    )
    status: DreamPersonalCheckInStatus
    note: str | None = Field(default=None, max_length=160)
    checked_in_on: date
    idempotency_key: str = Field(min_length=1, max_length=180)
    semantics: Literal["PRIVATE_SELF_REPORTED_CHECK_IN"]
    private_to_account: Literal[True]
    owner_self_report_only: Literal[True]
    mingli_evidence_role: Literal["NOT_MINGLI_EVIDENCE"]
    validates_dream_or_mingli: Literal[False]
    mingli_write_allowed: Literal[False]
    decision_write_allowed: Literal[False]
    knowledge_write_allowed: Literal[False]
    world_write_allowed: Literal[False]
    story_write_allowed: Literal[False]

    @model_validator(mode="after")
    def identity_is_valid(self) -> DreamPersonalCheckInRecord:
        if (self.previous_checkin_ref is None) != (
            self.previous_checkin_hash is None
        ):
            raise ValueError(
                "dream_personal_checkin_previous_identity_incomplete"
            )
        identity = self.model_dump(
            mode="json",
            exclude={"checkin_ref", "checkin_hash"},
        )
        if self.checkin_hash != content_hash(identity):
            raise ValueError("dream_personal_checkin_hash_mismatch")
        if self.checkin_ref != stable_ref(
            "v60-dream-personal-check-in",
            identity,
        ):
            raise ValueError("dream_personal_checkin_ref_mismatch")
        return self

    @classmethod
    def issue(cls, **values: Any) -> DreamPersonalCheckInRecord:
        identity = {
            "contract_version": DREAM_PERSONAL_CHECKIN_VERSION,
            **values,
            "semantics": "PRIVATE_SELF_REPORTED_CHECK_IN",
            "private_to_account": True,
            "owner_self_report_only": True,
            "mingli_evidence_role": "NOT_MINGLI_EVIDENCE",
            "validates_dream_or_mingli": False,
            "mingli_write_allowed": False,
            "decision_write_allowed": False,
            "knowledge_write_allowed": False,
            "world_write_allowed": False,
            "story_write_allowed": False,
        }
        return cls(
            checkin_ref=stable_ref(
                "v60-dream-personal-check-in",
                identity,
            ),
            checkin_hash=content_hash(identity),
            **identity,
        )


class DreamPrivateInquiryView(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    contract_version: Literal["v60.dream-private-inquiry.001"]
    inquiry_ref: str
    inquiry_hash: str
    domain: DreamLifeDomain
    question: str
    candidate_ref: str
    candidate_hash: str
    public_alias: str
    tree_ref: str
    encounter_ref: str
    episode_question_ref: str
    private_to_account: Literal[True]
    owner_self_report_only: Literal[True]
    mingli_evidence_role: Literal["NOT_MINGLI_EVIDENCE"]
    reading_used_to_select_candidate: Literal[False]
    llm_interpretation_used: Literal[False]
    dream_answers_owner_question: Literal[False]

    @classmethod
    def from_record(
        cls,
        record: DreamPrivateInquiryRecord,
    ) -> DreamPrivateInquiryView:
        return cls.model_validate(
            record.model_dump(
                mode="json",
                include=set(cls.model_fields),
            )
        )


class DreamPersonalObservationView(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    contract_version: Literal["v60.dream-personal-observation.001"]
    task_ref: str
    task_hash: str
    inquiry_ref: str
    inquiry_hash: str
    encounter_ref: str
    option: DreamPersonalObservationOption
    checkpoint_on: date
    semantics: Literal["PRIVATE_REALITY_OBSERVATION_ONLY"]
    private_to_account: Literal[True]
    owner_self_report_only: Literal[True]
    mingli_evidence_role: Literal["NOT_MINGLI_EVIDENCE"]
    dream_result_validates_owner_question: Literal[False]

    @classmethod
    def from_record(
        cls,
        record: DreamPersonalObservationTask,
    ) -> DreamPersonalObservationView:
        return cls.model_validate(
            record.model_dump(
                mode="json",
                include=set(cls.model_fields),
            )
        )


class DreamPersonalCheckInView(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    contract_version: Literal["v60.dream-personal-check-in.001"]
    checkin_ref: str
    checkin_hash: str
    task_ref: str
    task_hash: str
    status: DreamPersonalCheckInStatus
    note: str | None
    checked_in_on: date
    semantics: Literal["PRIVATE_SELF_REPORTED_CHECK_IN"]
    private_to_account: Literal[True]
    owner_self_report_only: Literal[True]
    mingli_evidence_role: Literal["NOT_MINGLI_EVIDENCE"]
    validates_dream_or_mingli: Literal[False]

    @classmethod
    def from_record(
        cls,
        record: DreamPersonalCheckInRecord,
    ) -> DreamPersonalCheckInView:
        return cls.model_validate(
            record.model_dump(
                mode="json",
                include=set(cls.model_fields),
            )
        )


class DreamPersonalJourneyProjection(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    contract_version: Literal[
        "v60.dream-personal-journey.001"
    ] = DREAM_PERSONAL_JOURNEY_VERSION
    status: Literal[
        "IN_DREAM",
        "DREAM_INTERRUPTED",
        "AWAITING_OBSERVATION",
        "OBSERVING",
        "FOLLOWED_UP",
    ]
    inquiry: DreamPrivateInquiryView
    observation_options: tuple[
        DreamPersonalObservationOption,
        ...,
    ]
    observation: DreamPersonalObservationView | None
    latest_checkin: DreamPersonalCheckInView | None
    checkin_count: int = Field(ge=0)
    private_to_account: Literal[True]
    owner_self_report_only: Literal[True]
    mingli_evidence_role: Literal["NOT_MINGLI_EVIDENCE"]
    dream_answers_owner_question: Literal[False]
    tree_candidate_set_or_order_changed: Literal[False]
    chapter_route_changed: Literal[False]
    episode_question_changed: Literal[False]
    answer_changed: Literal[False]
    npc_choice_changed: Literal[False]
    world_outcome_changed: Literal[False]
    mingli_write_allowed: Literal[False]
    decision_write_allowed: Literal[False]
    knowledge_write_allowed: Literal[False]

    @model_validator(mode="after")
    def state_is_coherent(self) -> DreamPersonalJourneyProjection:
        option_count = len(self.observation_options)
        if self.status in {"IN_DREAM", "DREAM_INTERRUPTED"}:
            if option_count or self.observation is not None:
                raise ValueError(
                    "dream_personal_journey_premature_observation"
                )
        else:
            if option_count != 3:
                raise ValueError(
                    "dream_personal_journey_option_count_invalid"
                )
            if self.status == "AWAITING_OBSERVATION":
                if self.observation is not None:
                    raise ValueError(
                        "dream_personal_journey_unexpected_observation"
                    )
            elif self.observation is None:
                raise ValueError(
                    "dream_personal_journey_observation_missing"
                )
        if self.status == "FOLLOWED_UP":
            if self.latest_checkin is None or self.checkin_count < 1:
                raise ValueError(
                    "dream_personal_journey_checkin_missing"
                )
        elif self.latest_checkin is not None or self.checkin_count != 0:
            raise ValueError(
                "dream_personal_journey_unexpected_checkin"
            )
        return self

    @classmethod
    def issue(
        cls,
        **values: Any,
    ) -> DreamPersonalJourneyProjection:
        return cls(
            **values,
            private_to_account=True,
            owner_self_report_only=True,
            mingli_evidence_role="NOT_MINGLI_EVIDENCE",
            dream_answers_owner_question=False,
            tree_candidate_set_or_order_changed=False,
            chapter_route_changed=False,
            episode_question_changed=False,
            answer_changed=False,
            npc_choice_changed=False,
            world_outcome_changed=False,
            mingli_write_allowed=False,
            decision_write_allowed=False,
            knowledge_write_allowed=False,
        )
