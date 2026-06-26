from __future__ import annotations

from typing import Any, Literal

from pydantic import Field, model_validator

from v30.contracts import RoleKey, V30Model


DIAGNOSIS_CONTRACT_VERSION = "v30.real_bazi_diagnosis.contracts.v1"

DiagnosisMode = Literal[
    "overview",
    "career",
    "wealth",
    "relationship",
    "health",
    "timing",
    "hidden_factor_calibration",
    "practitioner_diagnostic",
]
DiagnosisDomain = Literal[
    "overview",
    "career",
    "wealth",
    "relationship",
    "health",
    "timing",
    "structure",
    "useful_god",
    "hidden_factor",
]
DiagnosisClaimLevel = Literal["fact", "feature", "path", "portrait", "domain", "timing", "question"]
DiagnosisConfidenceBand = Literal["low", "medium", "high"]
DiagnosisGraphNodeKind = Literal[
    "chart_fact",
    "feature",
    "matched_rule",
    "portrait",
    "path",
    "ranked_decision",
    "claim",
    "timing_activation",
    "feedback",
]
DiagnosisGraphEdgeKind = Literal["supports", "weakens", "activates", "blocks", "requires", "explains", "asks_followup"]


class DiagnosisContext(V30Model):
    version: str = DIAGNOSIS_CONTRACT_VERSION
    context_id: str
    reading_id: str
    chart_context_id: str
    role_key: RoleKey
    diagnosis_mode: DiagnosisMode = "overview"
    active_domains: list[DiagnosisDomain] = Field(default_factory=list)
    immutable_chart_fact_ids: list[str] = Field(default_factory=list)
    active_time_layers: dict[str, Any] = Field(default_factory=dict)
    strongest_evidence_families: list[str] = Field(default_factory=list)
    counter_evidence_families: list[str] = Field(default_factory=list)
    blocked_claim_types: list[str] = Field(default_factory=list)
    selected_question_id: str | None = None
    evidence_ids: list[str] = Field(default_factory=list)
    policy_versions: dict[str, str] = Field(default_factory=dict)
    runtime_write_allowed: bool = False
    chart_fact_mutation_allowed: bool = False
    boundary: str = "diagnosis_context_is_read_only_runtime_projection_not_chart_fact_source"

    @model_validator(mode="after")
    def _read_only_context(self) -> "DiagnosisContext":
        if self.runtime_write_allowed:
            raise ValueError("DiagnosisContext cannot allow runtime writes")
        if self.chart_fact_mutation_allowed:
            raise ValueError("DiagnosisContext cannot allow chart fact mutation")
        return self


class MatchedRule(V30Model):
    version: str = DIAGNOSIS_CONTRACT_VERSION
    rule_match_id: str
    rule_id: str
    source_family_ids: list[str] = Field(default_factory=list)
    domain_targets: list[DiagnosisDomain] = Field(default_factory=list)
    match_strength: float = Field(ge=0.0, le=1.0)
    required_context_hit: list[str] = Field(default_factory=list)
    counter_context_hit: list[str] = Field(default_factory=list)
    missing_context: list[str] = Field(default_factory=list)
    claim_templates: list[str] = Field(default_factory=list)
    blocked_claims: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    path_ids: list[str] = Field(default_factory=list)
    can_generate_claim: bool = True
    requires_user_calibration: bool = False
    chart_fact_mutation_requested: bool = False
    boundary: str = "matched_rule_is_evidence_match_not_public_verdict"

    @model_validator(mode="after")
    def _validate_rule_match(self) -> "MatchedRule":
        if self.chart_fact_mutation_requested:
            raise ValueError("MatchedRule cannot request chart fact mutation")
        if not self.evidence_ids:
            raise ValueError("MatchedRule requires at least one evidence id")
        if self.match_strength <= 0 and self.can_generate_claim:
            raise ValueError("MatchedRule with zero strength cannot generate claims")
        return self


class DiagnosisFeature(V30Model):
    version: str = DIAGNOSIS_CONTRACT_VERSION
    feature_id: str
    family: str
    domain: DiagnosisDomain
    statement: str
    evidence_ids: list[str] = Field(default_factory=list)
    confidence_band: DiagnosisConfidenceBand = "medium"
    supports_claim_types: list[DiagnosisClaimLevel] = Field(default_factory=list)
    counter_notes: list[str] = Field(default_factory=list)
    boundary: str = "diagnosis_feature_projects_feature_evidence_without_new_fact"

    @model_validator(mode="after")
    def _feature_has_trace(self) -> "DiagnosisFeature":
        if not self.evidence_ids:
            raise ValueError("DiagnosisFeature requires evidence ids")
        if not self.statement.strip():
            raise ValueError("DiagnosisFeature requires a statement")
        return self


class DiagnosisPath(V30Model):
    version: str = DIAGNOSIS_CONTRACT_VERSION
    path_id: str
    family_chain: list[str] = Field(default_factory=list)
    mechanism: str
    domain_targets: list[DiagnosisDomain] = Field(default_factory=list)
    diagnosis_statement: str
    risk_statement: str = ""
    timing_trigger: dict[str, Any] = Field(default_factory=dict)
    score: float = Field(ge=0.0, le=1.0)
    evidence_ids: list[str] = Field(default_factory=list)
    counter_evidence_ids: list[str] = Field(default_factory=list)
    blocked_overclaim: list[str] = Field(default_factory=list)
    boundary: str = "diagnosis_path_translates_dynamic_path_without_final_event_prediction"

    @model_validator(mode="after")
    def _path_has_bazi_content(self) -> "DiagnosisPath":
        if len(self.family_chain) < 2:
            raise ValueError("DiagnosisPath requires a family chain with at least two nodes")
        if not self.diagnosis_statement.strip():
            raise ValueError("DiagnosisPath requires a diagnosis statement")
        if not self.evidence_ids:
            raise ValueError("DiagnosisPath requires evidence ids")
        return self


class DiagnosisPortrait(V30Model):
    version: str = DIAGNOSIS_CONTRACT_VERSION
    portrait_id: str
    dimension: str
    domain: DiagnosisDomain = "overview"
    statement: str
    evidence_ids: list[str] = Field(default_factory=list)
    path_ids: list[str] = Field(default_factory=list)
    confidence_band: DiagnosisConfidenceBand = "medium"
    counter_notes: list[str] = Field(default_factory=list)
    boundary: str = "diagnosis_portrait_is_derived_projection_not_personality_fact"

    @model_validator(mode="after")
    def _portrait_is_traceable(self) -> "DiagnosisPortrait":
        if not self.statement.strip():
            raise ValueError("DiagnosisPortrait requires a statement")
        if not self.evidence_ids and not self.path_ids:
            raise ValueError("DiagnosisPortrait requires evidence ids or path ids")
        return self


class DiagnosisClaim(V30Model):
    version: str = DIAGNOSIS_CONTRACT_VERSION
    claim_id: str
    claim_level: DiagnosisClaimLevel
    domain: DiagnosisDomain
    claim_text: str
    confidence_band: DiagnosisConfidenceBand = "medium"
    evidence_ids: list[str] = Field(default_factory=list)
    rule_ids: list[str] = Field(default_factory=list)
    path_ids: list[str] = Field(default_factory=list)
    portrait_ids: list[str] = Field(default_factory=list)
    blocked_overclaim: list[str] = Field(default_factory=list)
    needs_user_calibration: bool = False
    llm_generated: bool = False
    chart_fact_mutation_allowed: bool = False
    fixed_event_prediction: bool = False
    boundary: str = "diagnosis_claim_is_traceable_bounded_bazi_judgment"

    @model_validator(mode="after")
    def _claim_has_trace_and_boundary(self) -> "DiagnosisClaim":
        if not self.claim_text.strip():
            raise ValueError("DiagnosisClaim requires claim text")
        if not (self.evidence_ids or self.rule_ids or self.path_ids or self.portrait_ids):
            raise ValueError("DiagnosisClaim requires evidence, rule, path, or portrait trace")
        if self.llm_generated:
            raise ValueError("DiagnosisClaim cannot be LLM-generated")
        if self.chart_fact_mutation_allowed:
            raise ValueError("DiagnosisClaim cannot allow chart fact mutation")
        if self.fixed_event_prediction:
            raise ValueError("DiagnosisClaim cannot be a fixed event prediction")
        return self


class DiagnosisGraphNode(V30Model):
    node_id: str
    node_kind: DiagnosisGraphNodeKind
    ref_id: str
    domain: DiagnosisDomain = "overview"
    weight: float = Field(ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class DiagnosisGraphEdge(V30Model):
    edge_id: str
    source_node_id: str
    target_node_id: str
    edge_kind: DiagnosisGraphEdgeKind
    weight: float = Field(ge=0.0, le=1.0)
    evidence_ids: list[str] = Field(default_factory=list)


class DiagnosisGraph(V30Model):
    version: str = DIAGNOSIS_CONTRACT_VERSION
    graph_id: str
    reading_id: str
    nodes: list[DiagnosisGraphNode] = Field(default_factory=list)
    edges: list[DiagnosisGraphEdge] = Field(default_factory=list)
    top_claim_ids: list[str] = Field(default_factory=list)
    top_path_ids: list[str] = Field(default_factory=list)
    boundary: str = "diagnosis_graph_routes_evidence_to_claims_without_mutating_facts"

    @model_validator(mode="after")
    def _graph_refs_exist(self) -> "DiagnosisGraph":
        node_ids = {node.node_id for node in self.nodes}
        for edge in self.edges:
            if edge.source_node_id not in node_ids or edge.target_node_id not in node_ids:
                raise ValueError("DiagnosisGraph edge references missing node")
        return self


class DiagnosisRouteDecision(V30Model):
    version: str = DIAGNOSIS_CONTRACT_VERSION
    route_id: str
    reading_id: str
    role_key: RoleKey
    diagnosis_mode: DiagnosisMode
    selected_domain: DiagnosisDomain = "overview"
    selected_claim_ids: list[str] = Field(default_factory=list)
    selected_path_ids: list[str] = Field(default_factory=list)
    selected_portrait_ids: list[str] = Field(default_factory=list)
    followup_required: bool = False
    followup_reason: str = ""
    expression_density: str = "standard"
    safeguards: list[str] = Field(default_factory=list)
    training_routes: list[str] = Field(default_factory=list)
    central_brain_generated_facts: bool = False
    boundary: str = "diagnosis_route_decision_selects_claims_not_facts"

    @model_validator(mode="after")
    def _router_is_coordinator(self) -> "DiagnosisRouteDecision":
        if self.central_brain_generated_facts:
            raise ValueError("DiagnosisRouteDecision cannot generate facts")
        if not (self.selected_claim_ids or self.followup_required):
            raise ValueError("DiagnosisRouteDecision must select claims or require follow-up")
        return self


class RealBaziDiagnosis(V30Model):
    version: str = DIAGNOSIS_CONTRACT_VERSION
    diagnosis_id: str
    reading_id: str
    context: DiagnosisContext
    matched_rules: list[MatchedRule] = Field(default_factory=list)
    features: list[DiagnosisFeature] = Field(default_factory=list)
    paths: list[DiagnosisPath] = Field(default_factory=list)
    portraits: list[DiagnosisPortrait] = Field(default_factory=list)
    claims: list[DiagnosisClaim] = Field(default_factory=list)
    graph: DiagnosisGraph
    route_decision: DiagnosisRouteDecision
    storage_policy: dict[str, Any] = Field(default_factory=dict)
    boundary: str = "real_bazi_diagnosis_is_traceable_module_output_not_llm_or_chart_fact_source"

    @model_validator(mode="after")
    def _diagnosis_is_coherent(self) -> "RealBaziDiagnosis":
        if self.context.reading_id != self.reading_id:
            raise ValueError("RealBaziDiagnosis reading id must match context")
        if self.graph.reading_id != self.reading_id:
            raise ValueError("RealBaziDiagnosis reading id must match graph")
        if self.route_decision.reading_id != self.reading_id:
            raise ValueError("RealBaziDiagnosis reading id must match route decision")
        claim_ids = {claim.claim_id for claim in self.claims}
        for claim_id in self.route_decision.selected_claim_ids:
            if claim_id not in claim_ids:
                raise ValueError("Route decision selected missing claim")
        return self
