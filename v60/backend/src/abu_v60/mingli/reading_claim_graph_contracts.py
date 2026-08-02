from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from abu_v60.provenance import content_hash, stable_ref

MINGLI_READING_CLAIM_GRAPH_VERSION = "v60.mingli-reading-claim-graph.009"

MingliReadingClaimLayer = Literal["PRINCIPLE", "IMAGE", "THEMES", "TIMING", "QUESTION"]
MingliReadingClaimStatus = Literal[
    "ESTABLISHED",
    "PROVISIONAL",
    "NEEDS_RECONCILIATION",
    "WITHHELD",
    "OPEN_QUESTION",
]
MingliReadingClaimConfidence = Literal["LOW", "MEDIUM", "HIGH"]
MingliReadingClaimAssessmentCode = Literal[
    "CLAIM_EVIDENCE_MISSING",
    "PRIMARY_HYPOTHESIS_CHART_BASIS_INCOMPLETE",
    "MECHANISM_CANDIDATE_REQUIRES_ADJUDICATION",
    "CONFIDENCE_EXCEEDS_PACKET",
    "DEPENDENCY_WITHHELD",
    "NATAL_CLAIM_CITES_TIMING_EVIDENCE",
    "NATAL_CLAIM_USES_SELECTED_TIMING",
    "TIMING_COORDINATE_EVIDENCE_MISSING",
    "TIMING_NATAL_BASIS_MISSING",
    "TIMING_RELATION_EVIDENCE_MISSING",
    "RELATION_MEMBERSHIP_PROMOTED_TO_EFFECT",
    "WORK_PATH_CLOSURE_EXCEEDS_PACKET",
    "HIGH_RISK_EVENT_ASSERTION",
    "ROOT_ASSERTION_CONFLICTS_WITH_PACKET",
    "NAMED_COORDINATE_CONFLICTS_WITH_PACKET",
    "TEN_GOD_MANIFESTATION_CONFLICTS_WITH_PACKET",
    "PEER_COUNT_CONFLICTS_WITH_PACKET",
    "UNSELECTED_TIMING_LAYER_ASSERTION",
    "UNLISTED_RELATION_COORDINATE_ASSERTION",
    "UNADMITTED_CLASSICAL_ASSERTION",
    "MODEL_FIELD_INVALID",
    "NON_READING_LANGUAGE",
    "LOW_INFORMATION_LANGUAGE",
    "TIMING_LAYER_PROSE_CONFLICT",
    "UNSUPPORTED_SOCIAL_RESOURCE_INFERENCE",
    "DOMAIN_PRIMARY_PATH_MISSING",
]
MingliReadingClaimRole = Literal[
    "SYNTHESIS",
    "PRIMARY",
    "ALTERNATIVE",
    "PROJECTION",
    "QUESTION",
]
MingliReadingClaimKind = Literal[
    "WHOLE_CHART_THESIS",
    "DAY_MASTER_STATE",
    "COMPETING_HYPOTHESIS",
    "WORK_PATH",
    "LIFE_IMAGE",
    "LIFE_DOMAIN",
    "TIMING_BASELINE",
    "TIMING_LAYER",
    "DISCRIMINATING_QUESTION",
]
MingliReadingClaimEdgeKind = Literal[
    "SUPPORTS",
    "COMPETES_WITH",
    "PROJECTS_TO",
    "TEMPORALLY_EXTENDS",
    "DISCRIMINATES",
]

CLAIM_SEMANTIC_KEY_ORDER = (
    "WHOLE_CHART",
    "DAY_MASTER",
    "HYPOTHESIS_H1",
    "HYPOTHESIS_H2",
    "WORK_PATH",
    "LIFE_IMAGE",
    "DOMAIN_PERSONALITY",
    "DOMAIN_CAREER",
    "DOMAIN_WEALTH",
    "DOMAIN_RELATIONSHIP",
    "DOMAIN_FAMILY",
    "TIMING_NATAL",
    "TIMING_DAYUN",
    "TIMING_ANNUAL",
    "DISCRIMINATING_QUESTION",
)


class MingliReadingClaim(BaseModel):
    """One deterministic assertion; method-bound synthesis may compose ruling copy."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    claim_ref: str = Field(min_length=1)
    source_agent_reading_ref: str = Field(min_length=1)
    semantic_key: str = Field(min_length=1, max_length=48)
    layer: MingliReadingClaimLayer
    kind: MingliReadingClaimKind
    role: MingliReadingClaimRole
    status: MingliReadingClaimStatus
    headline: str = Field(min_length=1, max_length=120)
    statement: str = Field(min_length=1, max_length=360)
    causal_chain: tuple[str, ...] = Field(max_length=4)
    condition: str | None = Field(default=None, max_length=180)
    evidence_ids: tuple[str, ...] = Field(max_length=12)
    mechanism_evidence_ids: tuple[str, ...] = Field(max_length=4)
    coordinate_evidence_id: str | None = Field(
        default=None,
        pattern=r"^E\d{3}$",
    )
    relation_evidence_ids: tuple[str, ...] = Field(max_length=6)
    confidence: MingliReadingClaimConfidence | None
    codes: tuple[str, ...] = Field(max_length=6)
    assessment_codes: tuple[MingliReadingClaimAssessmentCode, ...] = Field(max_length=15)

    @model_validator(mode="after")
    def identity_is_valid(self) -> MingliReadingClaim:
        if len(set(self.evidence_ids)) != len(self.evidence_ids):
            raise ValueError("mingli_reading_claim_evidence_not_unique")
        if any(not item.startswith("E") or len(item) != 4 for item in self.evidence_ids):
            raise ValueError("mingli_reading_claim_evidence_id_invalid")
        specialized_ids = {
            *self.mechanism_evidence_ids,
            *self.relation_evidence_ids,
            *((self.coordinate_evidence_id,) if self.coordinate_evidence_id is not None else ()),
        }
        if not specialized_ids.issubset(self.evidence_ids):
            raise ValueError("mingli_reading_claim_specialized_evidence_not_in_claim")
        identity = self.model_dump(mode="json", exclude={"claim_ref"})
        if self.claim_ref != stable_ref("v60-mingli-reading-claim", identity):
            raise ValueError("mingli_reading_claim_ref_mismatch")
        return self

    @classmethod
    def issue(cls, **values: Any) -> MingliReadingClaim:
        identity = dict(values)
        return cls(
            claim_ref=stable_ref("v60-mingli-reading-claim", identity),
            **identity,
        )


class MingliReadingClaimEdge(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    edge_ref: str = Field(min_length=1)
    relation: MingliReadingClaimEdgeKind
    source_claim_ref: str = Field(min_length=1)
    target_claim_ref: str = Field(min_length=1)

    @model_validator(mode="after")
    def identity_is_valid(self) -> MingliReadingClaimEdge:
        if self.source_claim_ref == self.target_claim_ref:
            raise ValueError("mingli_reading_claim_edge_self_reference")
        identity = self.model_dump(mode="json", exclude={"edge_ref"})
        if self.edge_ref != stable_ref("v60-mingli-reading-claim-edge", identity):
            raise ValueError("mingli_reading_claim_edge_ref_mismatch")
        return self

    @classmethod
    def issue(cls, **values: Any) -> MingliReadingClaimEdge:
        identity = dict(values)
        return cls(
            edge_ref=stable_ref("v60-mingli-reading-claim-edge", identity),
            **identity,
        )


class MingliReadingClaimGraph(BaseModel):
    """Deterministic cognitive projection shared by every product surface."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    graph_ref: str = Field(min_length=1)
    graph_hash: str = Field(min_length=64, max_length=64)
    graph_version: Literal["v60.mingli-reading-claim-graph.009"]
    case_ref: str = Field(min_length=1)
    chart_version_ref: str = Field(min_length=1)
    life_case_revision_ref: str = Field(min_length=1)
    reading_ref: str = Field(min_length=1)
    reading_hash: str = Field(min_length=64, max_length=64)
    agent_reading_ref: str = Field(min_length=1)
    agent_reading_hash: str = Field(min_length=64, max_length=64)
    packet_ref: str = Field(min_length=1)
    packet_hash: str = Field(min_length=64, max_length=64)
    agent_profile_ref: str = Field(min_length=1)
    agent_profile_hash: str = Field(min_length=64, max_length=64)
    model_ref: str = Field(min_length=1)
    model_digest: str = Field(min_length=64, max_length=64)
    reasoning_mode: Literal["BLIND_READING"]
    reasoning_mode_contract_ref: str = Field(min_length=1)
    reasoning_mode_contract_hash: str = Field(min_length=64, max_length=64)
    reconciliation_status: Literal["NOT_ADMITTED"]
    projection_authority: Literal["DETERMINISTIC_AGENT_READING"]
    qualification_status: Literal["OWNER_REVIEW_REQUIRED"]
    claims: tuple[MingliReadingClaim, ...] = Field(min_length=15, max_length=15)
    edges: tuple[MingliReadingClaimEdge, ...] = Field(min_length=1)
    owner_review_projection_allowed: Literal[True]
    public_projection_allowed: Literal[False]
    canonical_fact_write_allowed: Literal[False]
    read_only: Literal[True]

    @model_validator(mode="after")
    def identity_and_graph_are_valid(self) -> MingliReadingClaimGraph:
        if tuple(item.semantic_key for item in self.claims) != CLAIM_SEMANTIC_KEY_ORDER:
            raise ValueError("mingli_reading_claim_graph_semantic_order_invalid")
        claim_refs = tuple(item.claim_ref for item in self.claims)
        if len(set(claim_refs)) != len(claim_refs):
            raise ValueError("mingli_reading_claim_graph_claim_refs_not_unique")
        if any(item.source_agent_reading_ref != self.agent_reading_ref for item in self.claims):
            raise ValueError("mingli_reading_claim_graph_agent_lineage_mismatch")
        allowed = set(claim_refs)
        if any(
            edge.source_claim_ref not in allowed or edge.target_claim_ref not in allowed
            for edge in self.edges
        ):
            raise ValueError("mingli_reading_claim_graph_edge_endpoint_invalid")
        withheld = {item.claim_ref for item in self.claims if item.status == "WITHHELD"}
        if any(
            edge.source_claim_ref in withheld or edge.target_claim_ref in withheld
            for edge in self.edges
        ):
            raise ValueError("mingli_reading_claim_graph_withheld_edge_active")
        by_key = {item.semantic_key: item for item in self.claims}
        if (
            any(by_key[key].status == "WITHHELD" for key in ("HYPOTHESIS_H1", "WORK_PATH"))
            and by_key["WHOLE_CHART"].status != "WITHHELD"
            and (
                by_key["WHOLE_CHART"].status != "NEEDS_RECONCILIATION"
                or "DEPENDENCY_WITHHELD" not in by_key["WHOLE_CHART"].assessment_codes
            )
        ):
            raise ValueError("mingli_reading_claim_graph_dependency_status_not_propagated")
        if len({item.edge_ref for item in self.edges}) != len(self.edges):
            raise ValueError("mingli_reading_claim_graph_edge_refs_not_unique")
        identity = self.model_dump(
            mode="json",
            exclude={"graph_ref", "graph_hash"},
        )
        if self.graph_hash != content_hash(identity):
            raise ValueError("mingli_reading_claim_graph_hash_mismatch")
        if self.graph_ref != stable_ref("v60-mingli-reading-claim-graph", identity):
            raise ValueError("mingli_reading_claim_graph_ref_mismatch")
        return self

    @classmethod
    def issue(cls, **values: Any) -> MingliReadingClaimGraph:
        identity = {
            "graph_version": MINGLI_READING_CLAIM_GRAPH_VERSION,
            **values,
            "reasoning_mode": "BLIND_READING",
            "reconciliation_status": "NOT_ADMITTED",
            "projection_authority": "DETERMINISTIC_AGENT_READING",
            "qualification_status": "OWNER_REVIEW_REQUIRED",
            "owner_review_projection_allowed": True,
            "public_projection_allowed": False,
            "canonical_fact_write_allowed": False,
            "read_only": True,
        }
        for key in ("claims", "edges"):
            identity[key] = tuple(
                item.model_dump(mode="json") if isinstance(item, BaseModel) else item
                for item in identity[key]
            )
        return cls(
            graph_ref=stable_ref("v60-mingli-reading-claim-graph", identity),
            graph_hash=content_hash(identity),
            **identity,
        )
