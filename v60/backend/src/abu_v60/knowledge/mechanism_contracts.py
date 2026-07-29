from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from abu_v60.provenance import content_hash


class MechanismRoleDefinition(BaseModel):
    """One required semantic role in a bounded mechanism pattern."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    role_id: Literal["SOURCE", "BRIDGE", "TARGET"]
    accepted_ten_god_labels: tuple[str, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def labels_are_unique(self) -> MechanismRoleDefinition:
        if len(self.accepted_ten_god_labels) != len(set(self.accepted_ten_god_labels)):
            raise ValueError("mechanism_role_labels_must_be_unique")
        return self


class MechanismPatternDefinition(BaseModel):
    """A structural role sequence, not a verdict that the mechanism works."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    pattern_id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    roles: tuple[MechanismRoleDefinition, ...] = Field(min_length=2, max_length=3)
    structural_statement: str = Field(min_length=1)
    forbidden_shortcut: str = Field(min_length=1)

    @model_validator(mode="after")
    def role_sequence_is_valid(self) -> MechanismPatternDefinition:
        role_ids = [role.role_id for role in self.roles]
        if role_ids[0] != "SOURCE" or role_ids[-1] != "TARGET":
            raise ValueError("mechanism_pattern_requires_source_and_target")
        if len(role_ids) != len(set(role_ids)):
            raise ValueError("mechanism_pattern_roles_must_be_unique")
        if len(role_ids) == 3 and role_ids[1] != "BRIDGE":
            raise ValueError("mechanism_pattern_middle_role_must_be_bridge")
        return self

    @property
    def pattern_ref(self) -> str:
        return f"{self.pattern_id}@1"


class BaziMechanismEvidenceProfile(BaseModel):
    """Owner-bounded grammar for compiling inspectable mechanism candidates."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    profile_id: str = Field(min_length=1)
    profile_version: str = Field(min_length=1)
    governance_status: Literal["OWNER_AUTHORIZED_RESEARCH_CANDIDATES"]
    runtime_scope: Literal["MECHANISM_CANDIDATE_EVIDENCE_ONLY"]
    professionally_reviewed: Literal[False]
    source_refs: tuple[str, ...] = Field(min_length=1)
    patterns: tuple[MechanismPatternDefinition, ...] = Field(min_length=1)
    candidate_presence_rule: Literal["ALL_ROLES_PRESENT_AND_SOURCE_OR_BRIDGE_VISIBLE"]
    required_blockers: tuple[str, ...] = Field(min_length=1)
    forbidden_conclusions: tuple[str, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def profile_values_are_unique(self) -> BaziMechanismEvidenceProfile:
        pattern_ids = [pattern.pattern_id for pattern in self.patterns]
        if len(pattern_ids) != len(set(pattern_ids)):
            raise ValueError("mechanism_pattern_identity_must_be_unique")
        if len(self.required_blockers) != len(set(self.required_blockers)):
            raise ValueError("mechanism_required_blockers_must_be_unique")
        if len(self.forbidden_conclusions) != len(set(self.forbidden_conclusions)):
            raise ValueError("mechanism_forbidden_conclusions_must_be_unique")
        return self

    @property
    def source_ref(self) -> str:
        return f"{self.profile_id}@{self.profile_version}"

    @property
    def profile_hash(self) -> str:
        return content_hash(self.model_dump(mode="json"))
