from __future__ import annotations

from typing import Literal

from pydantic import Field

from v30.contracts import V30Model


PRODUCT_CONTRACT_VERSION = "v30.output_runtime_product_contracts.v1"

RoleVisibility = Literal["guest", "user", "practitioner", "analyst", "admin", "lab"]


class PractitionerAction(V30Model):
    action_id: str
    label: str
    meaning: str
    effect: str
    trainable: bool = True
    mutates_chart_facts: bool = False


class ProductVerdictCard(V30Model):
    version: str = "v30.product_verdict_card.v1"
    card_id: str
    source_verdict_id: str = ""
    domain: str = ""
    domain_label: str = ""
    title: str = ""
    primary_text: str = ""
    advice_points: list[str] = Field(default_factory=list)
    confidence: float = 0.0
    confidence_label: str = ""
    assertion_level: str = ""
    evidence_count: int = 0
    counter_evidence_count: int = 0
    branch_hint: str = ""
    role_visibility: list[RoleVisibility] = Field(default_factory=list)
    allowed_user_text: list[str] = Field(default_factory=list)
    forbidden_user_text: list[str] = Field(default_factory=list)
    diagnostic_trace: dict[str, object] = Field(default_factory=dict)
    boundary: str = "product_verdict_card_projects_decision_verdict_without_mutating_facts"


class BranchCard(V30Model):
    version: str = "v30.product_branch_card.v1"
    branch_card_id: str
    source_conflict_id: str = ""
    domain: str = ""
    domain_label: str = ""
    topic: str = ""
    title: str = ""
    user_summary: str = ""
    practitioner_summary: str = ""
    key_question: str = ""
    status: str = "needs_calibration"
    top_confidence: float = 0.0
    runner_up_confidence: float = 0.0
    confidence_gap: float = 0.0
    confidence_label: str = ""
    signal_bound_candidate_count: int = 0
    candidate_signal_count: int = 0
    source_candidate_ids: list[str] = Field(default_factory=list)
    conflict_types: list[str] = Field(default_factory=list)
    practitioner_actions: list[PractitionerAction] = Field(default_factory=list)
    role_visibility: list[RoleVisibility] = Field(default_factory=list)
    allowed_user_text: list[str] = Field(default_factory=list)
    forbidden_user_text: list[str] = Field(default_factory=list)
    boundary: str = "product_branch_card_preserves_uncertainty_without_exposing_internal_policy_keys"


class ProductAdviceCard(V30Model):
    version: str = "v30.product_advice_card.v1"
    card_id: str
    domain: str = ""
    domain_label: str = ""
    title: str = ""
    advice_points: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    role_visibility: list[RoleVisibility] = Field(default_factory=list)
    boundary: str = "product_advice_card_uses_verdict_bound_advice_only"


class ProbeCard(V30Model):
    version: str = "v30.product_probe_card.v1"
    card_id: str
    domain: str = ""
    domain_label: str = ""
    question: str = ""
    reason: str = ""
    submit_contract: dict[str, object] = Field(default_factory=dict)
    role_visibility: list[RoleVisibility] = Field(default_factory=list)
    boundary: str = "product_probe_card_is_invited_calibration_not_auto_dialogue"


class ThinkingStepCard(V30Model):
    version: str = "v30.product_thinking_step_card.v1"
    card_id: str
    title: str = ""
    text: str = ""
    evidence_refs: list[str] = Field(default_factory=list)
    role_visibility: list[RoleVisibility] = Field(default_factory=list)
    boundary: str = "product_thinking_step_card_is_request_only_explanation"


class ConversationSeed(V30Model):
    version: str = "v30.product_conversation_seed.v1"
    seed_id: str
    text: str
    domain: str = ""
    domain_label: str = ""
    source: str = "system"
    answer_first: bool = True
    role_visibility: list[RoleVisibility] = Field(default_factory=list)
    boundary: str = "product_conversation_seed_starts_independent_dialogue_session"


class ProductProjectionBundle(V30Model):
    version: str = "v30.product_projection_bundle.v1"
    role_key: str
    verdict_cards: list[ProductVerdictCard] = Field(default_factory=list)
    branch_cards: list[BranchCard] = Field(default_factory=list)
    advice_cards: list[ProductAdviceCard] = Field(default_factory=list)
    probe_cards: list[ProbeCard] = Field(default_factory=list)
    conversation_seeds: list[ConversationSeed] = Field(default_factory=list)
    leakage_scan: dict[str, object] = Field(default_factory=dict)
    boundary: str = "product_projection_bundle_is_surface_ready_projection_not_decision_authority"
