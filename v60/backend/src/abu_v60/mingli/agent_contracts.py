from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from abu_v60.mingli.agent_adjudication import (
    AgentExcludedCandidate,
    AgentHypothesis,
    AgentHypothesisDecision,
)
from abu_v60.mingli.agent_method_cards import (
    fallback_hypothesis_method_card,
    mechanism_method_card,
)
from abu_v60.mingli.agent_method_distillation import (
    bound_method_context,
    cross_card_discriminator,
    day_master_regime_method_asset,
    domain_method_assets,
)
from abu_v60.provenance import content_hash, stable_ref

MINGLI_AGENT_PACKET_VERSION = "v60.mingli-agent-case-packet.002"
MINGLI_AGENT_PROMPT_VIEW_VERSION = "v60.mingli-agent-prompt-view.009"
MINGLI_AGENT_READING_VERSION = "v60.mingli-agent-reading.003"

Confidence = Literal["LOW", "MEDIUM", "HIGH"]
EvidenceKind = Literal[
    "PILLAR",
    "SUPPORT",
    "RELATION",
    "SOURCE",
    "MECHANISM_CANDIDATE",
    "TIMING",
]
LifeDomain = Literal["personality", "career", "wealth", "relationship", "family"]
NarrativeStep = Annotated[str, StringConstraints(min_length=4, max_length=160)]


class AgentEvidenceItem(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    evidence_id: str = Field(pattern=r"^E\d{3}$")
    kind: EvidenceKind
    statement: str = Field(min_length=1, max_length=800)
    source_refs: tuple[str, ...] = Field(min_length=1, max_length=24)

    @model_validator(mode="after")
    def refs_are_unique(self) -> AgentEvidenceItem:
        if self.source_refs != tuple(sorted(set(self.source_refs))):
            raise ValueError("mingli_agent_evidence_source_refs_not_sorted_unique")
        return self


class AgentPillarContext(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    slot: Literal["year", "month", "day", "hour"]
    pillar: str = Field(min_length=2, max_length=2)
    stem: str = Field(min_length=1, max_length=1)
    branch: str = Field(min_length=1, max_length=1)
    stem_element: Literal["wood", "fire", "earth", "metal", "water"]
    stem_polarity: Literal["yin", "yang"]
    visible_ten_god: str = Field(min_length=1, max_length=8)
    hidden_stems: tuple[str, ...] = Field(min_length=1, max_length=3)
    hidden_ten_gods: tuple[str, ...] = Field(min_length=1, max_length=3)
    evidence_id: str = Field(pattern=r"^E\d{3}$")

    @model_validator(mode="after")
    def pillar_shape_is_valid(self) -> AgentPillarContext:
        if self.pillar != f"{self.stem}{self.branch}":
            raise ValueError("mingli_agent_pillar_identity_mismatch")
        if len(self.hidden_stems) != len(self.hidden_ten_gods):
            raise ValueError("mingli_agent_hidden_ten_god_shape_mismatch")
        return self


class AgentDayMasterSupportContext(BaseModel):
    """Observable support coordinates, without deciding strength by counting."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    same_identity_hidden_support: tuple[str, ...]
    same_element_hidden_support: tuple[str, ...]
    visible_peer_support: tuple[str, ...]
    resource_support: tuple[str, ...]
    root_language_policy: Literal["ONLY_SAME_ELEMENT_HIDDEN_STEMS_ARE_ROOT_CANDIDATES"]
    evidence_id: str = Field(pattern=r"^E\d{3}$")


class AgentRelationContext(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    relation_type: Literal[
        "same_branch_membership",
        "six_clash_membership",
        "six_harmony_membership",
    ]
    left_layer: str = Field(min_length=1, max_length=32)
    left_slot: str = Field(min_length=1, max_length=32)
    left_branch: str = Field(min_length=1, max_length=1)
    right_layer: str = Field(min_length=1, max_length=32)
    right_slot: str = Field(min_length=1, max_length=32)
    right_branch: str = Field(min_length=1, max_length=1)
    evidence_id: str = Field(pattern=r"^E\d{3}$")


class AgentSourceContext(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    visible_slot: str = Field(min_length=1, max_length=16)
    visible_stem: str = Field(min_length=1, max_length=1)
    source_slot: str = Field(min_length=1, max_length=16)
    source_branch: str = Field(min_length=1, max_length=1)
    hidden_stem: str = Field(min_length=1, max_length=1)
    match_kind: Literal["EXACT_IDENTITY", "SAME_ELEMENT_DIFFERENT_IDENTITY"]
    evidence_id: str = Field(pattern=r"^E\d{3}$")


class AgentMechanismContext(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    candidate_ref: str = Field(min_length=1)
    pattern_ref: str = Field(min_length=1)
    label: str = Field(min_length=1, max_length=80)
    structural_statement: str = Field(min_length=1, max_length=500)
    role_summary: tuple[str, ...] = Field(min_length=2, max_length=3)
    blocker_codes: tuple[str, ...]
    evidence_id: str = Field(pattern=r"^E\d{3}$")


class AgentTimingCoordinate(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    layer: Literal["DAYUN", "ANNUAL", "MONTHLY"]
    pillar: str = Field(min_length=2, max_length=2)
    ten_god_label: str = Field(min_length=1, max_length=8)
    start_year: int | None = None
    end_year: int | None = None
    evidence_id: str = Field(pattern=r"^E\d{3}$")


class MingliAgentCasePacket(BaseModel):
    """Compact professional dossier supplied to exactly one Mingli Agent call."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    packet_ref: str = Field(min_length=1)
    packet_hash: str = Field(min_length=64, max_length=64)
    packet_version: Literal["v60.mingli-agent-case-packet.002"]
    case_ref: str = Field(min_length=1)
    chart_version_ref: str = Field(min_length=1)
    life_case_revision_ref: str = Field(min_length=1)
    reading_ref: str = Field(min_length=1)
    reading_hash: str = Field(min_length=64, max_length=64)
    subject_kind: Literal["HUMAN_OWNER", "HUMAN_REFERENCE", "CANONICAL_SYNTHETIC"]
    gender: str = Field(min_length=1, max_length=32)
    birth_timezone: str = Field(min_length=1, max_length=80)
    day_master_stem: str = Field(min_length=1, max_length=1)
    day_master_element: Literal["wood", "fire", "earth", "metal", "water"]
    month_command_branch: str = Field(min_length=1, max_length=1)
    pillars: tuple[AgentPillarContext, ...] = Field(min_length=4, max_length=4)
    day_master_support: AgentDayMasterSupportContext
    natal_relations: tuple[AgentRelationContext, ...]
    source_contexts: tuple[AgentSourceContext, ...]
    mechanism_observations: tuple[AgentMechanismContext, ...]
    timing_analysis_date: str = Field(min_length=10, max_length=10)
    timing_coordinates: tuple[AgentTimingCoordinate, ...] = Field(
        min_length=2,
        max_length=2,
    )
    timing_relations: tuple[AgentRelationContext, ...]
    element_cycles: tuple[str, ...] = Field(min_length=5, max_length=5)
    evidence_catalog: tuple[AgentEvidenceItem, ...] = Field(min_length=7, max_length=64)
    interpretation_tasks: tuple[str, ...] = Field(min_length=6, max_length=12)
    read_only: Literal[True]

    @model_validator(mode="after")
    def identity_and_refs_are_valid(self) -> MingliAgentCasePacket:
        if tuple(item.slot for item in self.pillars) != ("year", "month", "day", "hour"):
            raise ValueError("mingli_agent_packet_pillar_order_invalid")
        if tuple(item.layer for item in self.timing_coordinates) != (
            "DAYUN",
            "ANNUAL",
        ):
            raise ValueError("mingli_agent_packet_timing_order_invalid")
        evidence_ids = tuple(item.evidence_id for item in self.evidence_catalog)
        expected_ids = tuple(f"E{index:03d}" for index in range(1, len(evidence_ids) + 1))
        if evidence_ids != expected_ids:
            raise ValueError("mingli_agent_packet_evidence_ids_not_contiguous")
        allowed = set(evidence_ids)
        cited = {
            *(item.evidence_id for item in self.pillars),
            self.day_master_support.evidence_id,
            *(item.evidence_id for item in self.natal_relations),
            *(item.evidence_id for item in self.source_contexts),
            *(item.evidence_id for item in self.mechanism_observations),
            *(item.evidence_id for item in self.timing_coordinates),
            *(item.evidence_id for item in self.timing_relations),
        }
        if not cited.issubset(allowed):
            raise ValueError("mingli_agent_packet_unknown_evidence_id")
        identity = self.model_dump(mode="json", exclude={"packet_ref", "packet_hash"})
        if self.packet_hash != content_hash(identity):
            raise ValueError("mingli_agent_packet_hash_mismatch")
        if self.packet_ref != stable_ref("v60-mingli-agent-packet", identity):
            raise ValueError("mingli_agent_packet_ref_mismatch")
        return self

    @property
    def allowed_evidence_ids(self) -> frozenset[str]:
        return frozenset(item.evidence_id for item in self.evidence_catalog)

    def model_prompt_view(self) -> dict[str, Any]:
        """Compact professional view; the full packet remains the audit authority."""

        return {
            "prompt_view_version": MINGLI_AGENT_PROMPT_VIEW_VERSION,
            "reasoning_contract": {
                "mode": "BLIND_READING",
                "profile_context_allowed": False,
                "life_case_observations_allowed": False,
                "historical_answers_allowed": False,
                "previous_reading_prose_allowed": False,
                "whole_chart_judgment_required": True,
                "uncertainty_expression": ("COMPETING_HYPOTHESIS_CONDITION_AND_CONFIDENCE"),
            },
            "chart": {
                "day_master_stem": self.day_master_stem,
                "day_master_element": self.day_master_element,
                "month_command_branch": self.month_command_branch,
                "pillars": [
                    {
                        "slot": item.slot,
                        "pillar": item.pillar,
                        "visible_ten_god": item.visible_ten_god,
                        "hidden": list(
                            zip(
                                item.hidden_stems,
                                item.hidden_ten_gods,
                                strict=True,
                            )
                        ),
                        "evidence_id": item.evidence_id,
                    }
                    for item in self.pillars
                ],
            },
            "day_master_support": self.day_master_support.model_dump(mode="json"),
            "professional_adjudication": _professional_adjudication_view(self),
            "natal_relations": [item.model_dump(mode="json") for item in self.natal_relations],
            "source_contexts": [item.model_dump(mode="json") for item in self.source_contexts],
            "mechanism_observations": [
                {
                    "pattern_ref": item.pattern_ref,
                    "label": item.label,
                    "structural_statement": item.structural_statement,
                    "role_summary": item.role_summary,
                    "blocker_codes": item.blocker_codes,
                    "evidence_id": item.evidence_id,
                }
                for item in self.mechanism_observations
            ],
            "timing": {
                "analysis_date": self.timing_analysis_date,
                "coordinates": [item.model_dump(mode="json") for item in self.timing_coordinates],
                "relations": [item.model_dump(mode="json") for item in self.timing_relations],
            },
            "fact_policy": (
                "Only the listed coordinates, relations, support roles, and evidence IDs "
                "may be used as chart facts."
            ),
        }

    @classmethod
    def issue(cls, **values: Any) -> MingliAgentCasePacket:
        identity = {
            "packet_version": MINGLI_AGENT_PACKET_VERSION,
            **values,
            "read_only": True,
        }
        for key in (
            "pillars",
            "natal_relations",
            "source_contexts",
            "mechanism_observations",
            "timing_coordinates",
            "timing_relations",
            "evidence_catalog",
        ):
            identity[key] = tuple(
                item.model_dump(mode="json") if isinstance(item, BaseModel) else item
                for item in identity[key]
            )
        if isinstance(identity["day_master_support"], BaseModel):
            identity["day_master_support"] = identity["day_master_support"].model_dump(mode="json")
        return cls(
            packet_ref=stable_ref("v60-mingli-agent-packet", identity),
            packet_hash=content_hash(identity),
            **identity,
        )


_BRANCH_ELEMENT = {
    "寅": "wood",
    "卯": "wood",
    "辰": "earth",
    "巳": "fire",
    "午": "fire",
    "未": "earth",
    "申": "metal",
    "酉": "metal",
    "戌": "earth",
    "亥": "water",
    "子": "water",
    "丑": "earth",
}
_GENERATES = {
    "wood": "fire",
    "fire": "earth",
    "earth": "metal",
    "metal": "water",
    "water": "wood",
}
_CONTROLS = {
    "wood": "earth",
    "earth": "water",
    "water": "fire",
    "fire": "metal",
    "metal": "wood",
}
_THREE_HARMONY_GROUPS = (
    ("申子辰", "water"),
    ("亥卯未", "wood"),
    ("寅午戌", "fire"),
    ("巳酉丑", "metal"),
)
_ELEMENT_LABEL = {
    "wood": "木",
    "fire": "火",
    "earth": "土",
    "metal": "金",
    "water": "水",
}


def _professional_adjudication_view(packet: MingliAgentCasePacket) -> dict[str, Any]:
    month_element = _BRANCH_ELEMENT[packet.month_command_branch]
    day_element = packet.day_master_element
    if month_element == day_element:
        seasonal_relation = "SAME_ELEMENT_SEASONAL_SUPPORT"
    elif _GENERATES[month_element] == day_element:
        seasonal_relation = "RESOURCE_SEASONAL_SUPPORT"
    elif _GENERATES[day_element] == month_element:
        seasonal_relation = "OUTPUT_SEASONAL_DRAIN"
    elif _CONTROLS[month_element] == day_element:
        seasonal_relation = "OFFICIAL_SEASONAL_PRESSURE"
    else:
        seasonal_relation = "WEALTH_SEASONAL_DRAIN"

    branch_coordinates: dict[str, list[dict[str, str]]] = {}
    for pillar in packet.pillars:
        branch_coordinates.setdefault(pillar.branch, []).append(
            {
                "slot": pillar.slot,
                "branch": pillar.branch,
                "evidence_id": pillar.evidence_id,
            }
        )
    structure_candidates = []
    present_branches = set(branch_coordinates)
    for members, result_element in _THREE_HARMONY_GROUPS:
        if not set(members).issubset(present_branches):
            continue
        member_coordinates = tuple(
            coordinate for member in members for coordinate in branch_coordinates[member]
        )
        structure_candidates.append(
            {
                "relation_type": "three_harmony_membership_candidate",
                "label": f"{members}三合{_ELEMENT_LABEL[result_element]}成员齐备候选",
                "members": tuple(members),
                "result_element": result_element,
                "member_coordinates": member_coordinates,
                "evidence_ids": tuple(
                    dict.fromkeys(coordinate["evidence_id"] for coordinate in member_coordinates)
                ),
                "membership_status": "CLASSICAL_MEMBER_SET_PRESENT",
                "effect_status": "REQUIRES_WHOLE_CHART_ADJUDICATION",
            }
        )

    occurrence_map: dict[str, list[str]] = {}
    for pillar in packet.pillars:
        occurrence_map.setdefault(pillar.visible_ten_god, []).append(
            f"{pillar.slot}干{pillar.stem}"
        )
        for hidden_stem, ten_god in zip(
            pillar.hidden_stems,
            pillar.hidden_ten_gods,
            strict=True,
        ):
            occurrence_map.setdefault(ten_god, []).append(f"{pillar.slot}支藏{hidden_stem}")
    natal_evidence_ids = tuple(
        item.evidence_id for item in packet.evidence_catalog if item.kind != "TIMING"
    )
    timing_evidence_ids = tuple(
        item.evidence_id for item in packet.evidence_catalog if item.kind == "TIMING"
    )
    mechanism_evidence_ids = {item.evidence_id for item in packet.mechanism_observations}
    chart_basis_evidence_ids = tuple(
        item for item in natal_evidence_ids if item not in mechanism_evidence_ids
    )
    return {
        "natal_evidence_ids": natal_evidence_ids,
        "timing_evidence_ids": timing_evidence_ids,
        "field_evidence_scope": {
            "natal_only_fields": (
                "first_look",
                "whole_chart_thesis",
                "hypotheses",
                "work_path",
                "life_image",
                "domains",
                "timing.natal_baseline",
            ),
            "natal_allowed": natal_evidence_ids,
            "primary_requires_chart_basis_from": chart_basis_evidence_ids,
            "natal_prose_forbidden": (
                "大运",
                "流年",
                "岁运",
                *(item.pillar for item in packet.timing_coordinates),
            ),
        },
        "seasonal_context": {
            "month_command_branch": packet.month_command_branch,
            "month_command_element": month_element,
            "relation_to_day_master": seasonal_relation,
            "counting_warning": "SEASON_ROOT_POSITION_AND_PATH_MUST_BE_WEIGHED_NOT_COUNTED",
        },
        "support_order": {
            "hidden_root_candidates": packet.day_master_support.same_element_hidden_support,
            "visible_peer_support": packet.day_master_support.visible_peer_support,
            "hidden_resource_support": packet.day_master_support.resource_support,
            "decision_warning": (
                "VISIBLE_PEERS_OR_HIDDEN_RESOURCE_CANNOT_BY_THEMSELVES_OVERRIDE_"
                "SEASON_AND_ROOT_STATUS"
            ),
        },
        "day_master_regime_method": day_master_regime_method_asset(
            seasonal_relation=seasonal_relation,
            root_candidates=packet.day_master_support.same_element_hidden_support,
            visible_peers=packet.day_master_support.visible_peer_support,
            hidden_resources=packet.day_master_support.resource_support,
        ),
        "ten_god_occurrences": tuple(
            {
                "ten_god": ten_god,
                "coordinates": tuple(coordinates),
            }
            for ten_god, coordinates in sorted(occurrence_map.items())
        ),
        "professional_structure_candidates": tuple(structure_candidates),
        "candidate_method_cards": {
            "authority": "CHECKS_REQUIRE_AGENT_RULING",
            "three_harmony": tuple(
                {
                    "candidate_label": item["label"],
                    "required_checks": (
                        "MEMBER_COMPLETION_TYPE",
                        "MONTH_COMMAND_SUPPORT_OR_RESISTANCE",
                        "RESULT_ELEMENT_STEM_VISIBILITY",
                        "DISRUPTION_OR_COMPETING_PATH",
                        "DAY_MASTER_AND_WHOLE_CHART_CAPACITY",
                    ),
                    "shortcut_forbidden": (
                        "MEMBERS_PRESENT_DOES_NOT_MEAN_EFFECT_OR_TRANSFORMATION"
                    ),
                }
                for item in structure_candidates
            ),
            "mechanisms": tuple(
                mechanism_method_card(
                    item,
                    include_distilled_guidance=True,
                    distilled_context=bound_method_context(
                        pattern_ref=item.pattern_ref,
                        ten_god_occurrences=occurrence_map,
                        root_candidates=(
                            packet.day_master_support.same_element_hidden_support
                        ),
                        visible_peers=packet.day_master_support.visible_peer_support,
                        hidden_resources=packet.day_master_support.resource_support,
                    ),
                )
                for item in packet.mechanism_observations
            ),
            "fallback_hypothesis": fallback_hypothesis_method_card(),
            "cross_card_discriminator": cross_card_discriminator(),
            "work_path_closure": {
                "closed_allowed_when": ("ALL_PRIMARY_BLOCKING_AND_CONDITIONING_CHECKS_SUPPORT"),
                "otherwise_allowed": ("CONDITIONAL", "UNCERTAIN", "BROKEN"),
            },
        },
        "domain_method_assets": domain_method_assets(
            gender=packet.gender,
            ten_god_occurrences=occurrence_map,
            spouse_palace={
                "slot": "day",
                "pillar": packet.pillars[2].pillar,
                "branch": packet.pillars[2].branch,
                "evidence_id": packet.pillars[2].evidence_id,
                "hidden_stems": packet.pillars[2].hidden_stems,
                "hidden_ten_gods": packet.pillars[2].hidden_ten_gods,
            },
        ),
        "required_decision_order": (
            "WEIGH_SEASON_ROOT_PEER_RESOURCE_DRAIN_WEALTH_AND_PRESSURE",
            "LOCK_NATAL_PRIMARY_AND_ALTERNATIVE_EXPLANATIONS",
            "COMPARE_PATTERN_SUCCESS_FAILURE_RESCUE_AND_TRANSFORMATION",
            "DERIVE_LIFE_DOMAINS_FROM_THE_NATAL_PRIMARY_ONLY",
            "APPLY_DAYUN_THEN_ANNUAL_WITHOUT_BACKFLOW_TO_NATAL",
            "ASK_ONE_REALITY_QUESTION_THAT_CAN_REVERSE_THE_PRIMARY_CHOICE",
        ),
    }


class AgentSupportSelection(BaseModel):
    """The model must acknowledge typed support facts without reclassifying them."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    root_status: Literal["NONE", "PRESENT"]
    root_coordinates: tuple[str, ...]
    peer_coordinates: tuple[str, ...]
    resource_coordinates: tuple[str, ...]


class AgentWorkPath(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    path_statement: str = Field(min_length=12, max_length=260)
    transformation_codes: tuple[
        Literal[
            "GENERATES",
            "CONTROLS",
            "SUPPORTS",
            "CONSTRAINS",
            "CHANNELS",
            "COMPETES",
        ],
        ...,
    ] = Field(min_length=1, max_length=4)
    closure: Literal["CLOSED", "CONDITIONAL", "BROKEN", "UNCERTAIN"]
    condition: str = Field(min_length=6, max_length=160)
    evidence_ids: tuple[str, ...] = Field(max_length=10)


class AgentDomainReading(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    headline: str = Field(min_length=4, max_length=48)
    conclusion: str = Field(min_length=16, max_length=260)
    causal_chain: tuple[NarrativeStep, ...] = Field(min_length=1, max_length=1)
    condition: str = Field(min_length=6, max_length=160)
    evidence_ids: tuple[str, ...] = Field(max_length=8)
    confidence: Literal["LOW", "MEDIUM"]


class AgentDomainReadings(BaseModel):
    """Fixed fields prevent a model from repeating one domain and omitting another."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    personality: AgentDomainReading
    career: AgentDomainReading
    wealth: AgentDomainReading
    relationship: AgentDomainReading
    family: AgentDomainReading

    @property
    def ordered(self) -> tuple[tuple[LifeDomain, AgentDomainReading], ...]:
        return (
            ("personality", self.personality),
            ("career", self.career),
            ("wealth", self.wealth),
            ("relationship", self.relationship),
            ("family", self.family),
        )


class AgentTimingLayerReading(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    coordinate_evidence_id: str = Field(min_length=4, max_length=4)
    relation_evidence_ids: tuple[str, ...] = Field(max_length=6)
    conclusion: str = Field(min_length=12, max_length=260)
    activation_chain: tuple[NarrativeStep, ...] = Field(min_length=1, max_length=1)
    evidence_ids: tuple[str, ...] = Field(min_length=1, max_length=8)
    confidence: Literal["LOW", "MEDIUM"]


class AgentTimingReading(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    natal_baseline: str = Field(min_length=12, max_length=180)
    natal_evidence_ids: tuple[str, ...] = Field(max_length=8)
    dayun: AgentTimingLayerReading
    annual: AgentTimingLayerReading
    verification_signals: tuple[str, ...] = Field(min_length=1, max_length=2)


class AgentLifeImage(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    title: str = Field(min_length=2, max_length=24)
    image: str = Field(min_length=8, max_length=140)
    explanation: str = Field(min_length=16, max_length=280)
    evidence_ids: tuple[str, ...] = Field(max_length=8)


class MingliAgentModelOutput(BaseModel):
    """One-call whole-chart verdict. It is interpretation, never a fact rewrite."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    first_look: str = Field(min_length=16, max_length=120)
    whole_chart_thesis: str = Field(min_length=24, max_length=320)
    day_master_state: Literal[
        "STRONG",
        "WEAK",
        "BALANCED",
        "FOLLOWING_TENDENCY",
        "SPECIALIZED_TENDENCY",
        "UNCERTAIN",
    ]
    support_selection: AgentSupportSelection
    day_master_rationale: str = Field(min_length=16, max_length=280)
    day_master_evidence_ids: tuple[str, ...] = Field(max_length=8)
    hypotheses: tuple[AgentHypothesis, ...] = Field(min_length=2, max_length=2)
    excluded_candidates: tuple[AgentExcludedCandidate, ...] = Field(max_length=8)
    hypothesis_decision: AgentHypothesisDecision
    work_path: AgentWorkPath
    life_image: AgentLifeImage
    domains: AgentDomainReadings
    timing: AgentTimingReading
    server_issue_keys: tuple[str, ...] = Field(default=(), max_length=12)

    @model_validator(mode="after")
    def professional_shape_is_valid(self) -> MingliAgentModelOutput:
        ids = tuple(item.hypothesis_id for item in self.hypotheses)
        if ids != ("H1", "H2"):
            raise ValueError("mingli_agent_hypotheses_not_unique")
        primary = tuple(item for item in self.hypotheses if item.role == "PRIMARY")
        if len(primary) != 1:
            raise ValueError("mingli_agent_primary_hypothesis_invalid")
        if self.hypothesis_decision.winner_id != primary[0].hypothesis_id:
            raise ValueError("mingli_agent_decision_primary_mismatch")
        return self

    def validate_evidence(self, allowed: frozenset[str]) -> None:
        cited: set[str] = set(self.day_master_evidence_ids)
        for item in self.hypotheses:
            cited.update(item.mechanism_evidence_ids)
            cited.update(item.evidence_ids)
            for ruling in item.method_rulings:
                cited.update(ruling.evidence_ids)
        for item in self.excluded_candidates:
            cited.update(item.evidence_ids)
        cited.update(self.work_path.evidence_ids)
        cited.update(self.life_image.evidence_ids)
        for _, item in self.domains.ordered:
            cited.update(item.evidence_ids)
        cited.update(self.timing.natal_evidence_ids)
        for item in (self.timing.dayun, self.timing.annual):
            cited.add(item.coordinate_evidence_id)
            cited.update(item.relation_evidence_ids)
            cited.update(item.evidence_ids)
        unknown = sorted(cited - allowed)
        if unknown:
            raise ValueError(f"mingli_agent_output_unknown_evidence:{','.join(unknown)}")


def mingli_agent_generation_key(
    *,
    requester_account_ref: str,
    reading_ref: str,
    reading_hash: str,
    packet_ref: str,
    packet_hash: str,
    agent_profile_ref: str,
    agent_profile_hash: str,
    provider_profile_ref: str,
    provider_profile_hash: str,
    prompt_ref: str,
    prompt_hash: str,
) -> str:
    return content_hash(
        {
            "requester_account_ref": requester_account_ref,
            "reading_ref": reading_ref,
            "reading_hash": reading_hash,
            "packet_ref": packet_ref,
            "packet_hash": packet_hash,
            "agent_profile_ref": agent_profile_ref,
            "agent_profile_hash": agent_profile_hash,
            "provider_profile_ref": provider_profile_ref,
            "provider_profile_hash": provider_profile_hash,
            "prompt_ref": prompt_ref,
            "prompt_hash": prompt_hash,
        }
    )


class MingliAgentReadingEnvelope(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    agent_reading_ref: str = Field(min_length=1)
    agent_reading_hash: str = Field(min_length=64, max_length=64)
    agent_reading_version: Literal["v60.mingli-agent-reading.003"]
    generation_key: str = Field(min_length=64, max_length=64)
    requester_account_ref: str = Field(min_length=1)
    case_ref: str = Field(min_length=1)
    chart_version_ref: str = Field(min_length=1)
    life_case_revision_ref: str = Field(min_length=1)
    reading_ref: str = Field(min_length=1)
    reading_hash: str = Field(min_length=64, max_length=64)
    packet_ref: str = Field(min_length=1)
    packet_hash: str = Field(min_length=64, max_length=64)
    agent_profile_ref: str = Field(min_length=1)
    agent_profile_hash: str = Field(min_length=64, max_length=64)
    provider_id: str = Field(min_length=1)
    model_ref: str = Field(min_length=1)
    model_digest: str = Field(min_length=64, max_length=64)
    provider_profile_ref: str = Field(min_length=1)
    provider_profile_hash: str = Field(min_length=64, max_length=64)
    prompt_ref: str = Field(min_length=1)
    prompt_hash: str = Field(min_length=64, max_length=64)
    provider_response_ref: str = Field(min_length=1)
    output: MingliAgentModelOutput
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    total_tokens: int = Field(ge=0)
    duration_ms: int = Field(ge=0)
    interpretation_status: Literal["AGENT_INTERPRETATION"]
    owner_review_status: Literal["NOT_REVIEWED"]
    canonical_fact_write_allowed: Literal[False]
    read_only: Literal[True]

    @model_validator(mode="after")
    def identity_is_valid(self) -> MingliAgentReadingEnvelope:
        expected_key = mingli_agent_generation_key(
            requester_account_ref=self.requester_account_ref,
            reading_ref=self.reading_ref,
            reading_hash=self.reading_hash,
            packet_ref=self.packet_ref,
            packet_hash=self.packet_hash,
            agent_profile_ref=self.agent_profile_ref,
            agent_profile_hash=self.agent_profile_hash,
            provider_profile_ref=self.provider_profile_ref,
            provider_profile_hash=self.provider_profile_hash,
            prompt_ref=self.prompt_ref,
            prompt_hash=self.prompt_hash,
        )
        if self.generation_key != expected_key:
            raise ValueError("mingli_agent_reading_generation_key_mismatch")
        identity = self.model_dump(
            mode="json",
            exclude={"agent_reading_ref", "agent_reading_hash"},
        )
        if self.agent_reading_hash != content_hash(identity):
            raise ValueError("mingli_agent_reading_hash_mismatch")
        if self.agent_reading_ref != stable_ref("v60-mingli-agent-reading", identity):
            raise ValueError("mingli_agent_reading_ref_mismatch")
        return self

    @classmethod
    def issue(cls, **values: Any) -> MingliAgentReadingEnvelope:
        identity = {
            "agent_reading_version": MINGLI_AGENT_READING_VERSION,
            **values,
            "interpretation_status": "AGENT_INTERPRETATION",
            "owner_review_status": "NOT_REVIEWED",
            "canonical_fact_write_allowed": False,
            "read_only": True,
        }
        if isinstance(identity["output"], BaseModel):
            identity["output"] = identity["output"].model_dump(mode="json")
        return cls(
            agent_reading_ref=stable_ref("v60-mingli-agent-reading", identity),
            agent_reading_hash=content_hash(identity),
            **identity,
        )
