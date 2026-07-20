from __future__ import annotations

from enum import Enum

from pydantic import Field, model_validator

from core.contracts.base import V50Model, require_non_empty, require_refs


class MingliGraphNodeType(str, Enum):
    STEM = "stem"
    BRANCH = "branch"
    HIDDEN_STEM = "hidden_stem"
    LUCK = "luck"
    YEAR = "year"
    ZIWEI_PALACE = "ziwei_palace"
    ZIWEI_STAR = "ziwei_star"
    TWIN_EVIDENCE = "twin_evidence"


class MingliGraphEdgeType(str, Enum):
    GENERATES = "generates"
    CONTROLS = "controls"
    SAME_ELEMENT_SUPPORT = "same_element_support"
    STORES = "stores"
    ROOTS = "roots"
    FORMS_HALF_COMBINATION = "forms_half_combination"
    FORMS_TRIPLE_COMBINATION = "forms_triple_combination"
    CLASHES = "clashes"
    HARMONIZES = "harmonizes"
    ACTIVATES = "activates"
    BRIDGES = "bridges"
    POSITION_LINK = "position_link"


class MingliStateLayer(str, Enum):
    NATAL = "natal_state"
    LUCK = "luck_state"
    YEAR = "year_state"
    MONTH = "month_state"


class NodeRoleType(str, Enum):
    ENVIRONMENT_NODE = "environment_node"
    BRIDGE_NODE = "bridge_node"
    CONVERTER_NODE = "converter_node"
    ENGINE_NODE = "engine_node"
    ANCHOR_NODE = "anchor_node"
    BUFFER_NODE = "buffer_node"
    SINGLE_FAILURE_NODE = "single_failure_node"
    ACTIVATION_NODE = "activation_node"


class MingliGraphNode(V50Model):
    version: str = "v50.mingli_graph_node.v1"
    node_id: str
    reading_id: str
    label: str
    node_type: MingliGraphNodeType
    position: str = ""
    element: str = ""
    yin_yang: str = ""
    ten_god: str = ""
    attributes: dict[str, object] = Field(default_factory=dict)
    material_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    boundary: str = "graph_node_is_computational_evidence_not_judgment"

    @model_validator(mode="after")
    def _boundary(self) -> "MingliGraphNode":
        require_non_empty(self.node_id, "node_id")
        require_non_empty(self.reading_id, "reading_id")
        require_non_empty(self.label, "label")
        require_refs(self.material_refs, "material_refs")
        require_refs(self.evidence_refs, "evidence_refs")
        return self


class MingliGraphEdge(V50Model):
    version: str = "v50.mingli_graph_edge.v1"
    edge_id: str
    reading_id: str
    from_node_id: str
    to_node_id: str
    edge_type: MingliGraphEdgeType
    strength: float = Field(default=0.0, ge=0.0, le=1.0)
    relation_label: str = ""
    attributes: dict[str, object] = Field(default_factory=dict)
    material_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    boundary: str = "graph_edge_is_computational_relation_not_judgment"

    @model_validator(mode="after")
    def _boundary(self) -> "MingliGraphEdge":
        require_non_empty(self.edge_id, "edge_id")
        require_non_empty(self.reading_id, "reading_id")
        require_non_empty(self.from_node_id, "from_node_id")
        require_non_empty(self.to_node_id, "to_node_id")
        require_refs(self.material_refs, "material_refs")
        require_refs(self.evidence_refs, "evidence_refs")
        return self


class MingliGraph(V50Model):
    version: str = "v50.mingli_graph.v1"
    graph_id: str
    reading_id: str
    nodes: list[MingliGraphNode] = Field(default_factory=list)
    edges: list[MingliGraphEdge] = Field(default_factory=list)
    source_store_id: str
    creates_judgment: bool = False
    calls_brain: bool = False
    calls_llm: bool = False
    boundary: str = "mingli_graph_models_structure_without_judgment"

    @model_validator(mode="after")
    def _boundary(self) -> "MingliGraph":
        require_non_empty(self.graph_id, "graph_id")
        require_non_empty(self.reading_id, "reading_id")
        require_non_empty(self.source_store_id, "source_store_id")
        if self.creates_judgment:
            raise ValueError("MingliGraph cannot create judgment")
        if self.calls_brain:
            raise ValueError("MingliGraph cannot call Brain")
        if self.calls_llm:
            raise ValueError("MingliGraph cannot call LLM")
        return self


class MingliPath(V50Model):
    version: str = "v50.mingli_path.v1"
    path_id: str
    reading_id: str
    graph_id: str
    state_layer: MingliStateLayer = MingliStateLayer.NATAL
    node_ids: list[str] = Field(default_factory=list)
    edge_ids: list[str] = Field(default_factory=list)
    relation_types: list[str] = Field(default_factory=list)
    source_strength: float = Field(default=0.0, ge=0.0, le=1.0)
    edge_strength: float = Field(default=0.0, ge=0.0, le=1.0)
    season_bias: float = Field(default=0.0, ge=0.0, le=1.0)
    root_support: float = Field(default=0.0, ge=0.0, le=1.0)
    converter_capacity: float = Field(default=0.0, ge=0.0, le=1.0)
    bridge_stability: float = Field(default=0.0, ge=0.0, le=1.0)
    target_receptivity: float = Field(default=0.0, ge=0.0, le=1.0)
    path_score: float = Field(default=0.0, ge=0.0, le=1.0)
    mechanism_hints: list[str] = Field(default_factory=list)
    graph_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    boundary: str = "mingli_path_is_explored_computational_evidence_not_verdict"

    @model_validator(mode="after")
    def _boundary(self) -> "MingliPath":
        require_non_empty(self.path_id, "path_id")
        require_non_empty(self.reading_id, "reading_id")
        require_non_empty(self.graph_id, "graph_id")
        if len(self.node_ids) < 2:
            raise ValueError("MingliPath requires at least two nodes")
        require_refs(self.edge_ids, "edge_ids")
        require_refs(self.graph_refs, "graph_refs")
        require_refs(self.evidence_refs, "evidence_refs")
        return self


class PathExplorationResult(V50Model):
    version: str = "v50.path_exploration_result.v1"
    exploration_id: str
    reading_id: str
    graph_id: str
    state_layer: MingliStateLayer = MingliStateLayer.NATAL
    paths: list[MingliPath] = Field(default_factory=list)
    ranked_path_ids: list[str] = Field(default_factory=list)
    node_path_contribution: dict[str, float] = Field(default_factory=dict)
    creates_judgment: bool = False
    calls_brain: bool = False
    calls_llm: bool = False
    boundary: str = "path_exploration_finds_routes_without_judgment"

    @model_validator(mode="after")
    def _boundary(self) -> "PathExplorationResult":
        require_non_empty(self.exploration_id, "exploration_id")
        require_non_empty(self.reading_id, "reading_id")
        require_non_empty(self.graph_id, "graph_id")
        if self.creates_judgment:
            raise ValueError("PathExplorationResult cannot create judgment")
        if self.calls_brain:
            raise ValueError("PathExplorationResult cannot call Brain")
        if self.calls_llm:
            raise ValueError("PathExplorationResult cannot call LLM")
        return self


class NodeRoleAssignment(V50Model):
    version: str = "v50.node_role_assignment.v1"
    assignment_id: str
    reading_id: str
    graph_id: str
    node_id: str
    label: str
    position: str = ""
    role: NodeRoleType
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    reason_codes: list[str] = Field(default_factory=list)
    path_refs: list[str] = Field(default_factory=list)
    graph_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    boundary: str = "node_role_is_structural_classification_not_verdict"

    @model_validator(mode="after")
    def _boundary(self) -> "NodeRoleAssignment":
        require_non_empty(self.assignment_id, "assignment_id")
        require_non_empty(self.reading_id, "reading_id")
        require_non_empty(self.graph_id, "graph_id")
        require_non_empty(self.node_id, "node_id")
        require_refs(self.graph_refs, "graph_refs")
        require_refs(self.evidence_refs, "evidence_refs")
        return self


class NodeRoleClassificationResult(V50Model):
    version: str = "v50.node_role_classification_result.v1"
    classification_id: str
    reading_id: str
    graph_id: str
    state_layer: MingliStateLayer = MingliStateLayer.NATAL
    assignments: list[NodeRoleAssignment] = Field(default_factory=list)
    roles_by_node_id: dict[str, list[NodeRoleType]] = Field(default_factory=dict)
    creates_judgment: bool = False
    calls_brain: bool = False
    calls_llm: bool = False
    boundary: str = "node_role_classification_prepares_simulation_evidence_without_verdict"

    @model_validator(mode="after")
    def _boundary(self) -> "NodeRoleClassificationResult":
        require_non_empty(self.classification_id, "classification_id")
        require_non_empty(self.reading_id, "reading_id")
        require_non_empty(self.graph_id, "graph_id")
        if self.creates_judgment:
            raise ValueError("NodeRoleClassificationResult cannot create judgment")
        if self.calls_brain:
            raise ValueError("NodeRoleClassificationResult cannot call Brain")
        if self.calls_llm:
            raise ValueError("NodeRoleClassificationResult cannot call LLM")
        return self


class NodeImportanceMetric(V50Model):
    version: str = "v50.node_importance_metric.v1"
    metric_id: str
    reading_id: str
    graph_id: str
    node_id: str
    label: str
    position: str = ""
    policy_version: str = "node_importance_policy_v2"
    season_score: float = Field(default=0.0, ge=0.0, le=1.0)
    centrality_score: float = Field(default=0.0, ge=0.0, le=1.0)
    bridge_score: float = Field(default=0.0, ge=0.0, le=1.0)
    criticality_score: float = Field(default=0.0, ge=0.0, le=1.0)
    flow_contribution: float = Field(default=0.0, ge=0.0, le=1.0)
    perturbation_sensitivity: float = Field(default=0.0, ge=0.0, le=1.0)
    redundancy_score: float = Field(default=0.0, ge=0.0, le=1.0)
    final_importance: float = Field(default=0.0, ge=0.0, le=1.0)
    explanation_codes: list[str] = Field(default_factory=list)
    graph_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    boundary: str = "node_importance_is_policy_versioned_computational_evidence"

    @model_validator(mode="after")
    def _boundary(self) -> "NodeImportanceMetric":
        require_non_empty(self.metric_id, "metric_id")
        require_non_empty(self.reading_id, "reading_id")
        require_non_empty(self.graph_id, "graph_id")
        require_non_empty(self.node_id, "node_id")
        require_refs(self.graph_refs, "graph_refs")
        require_refs(self.evidence_refs, "evidence_refs")
        return self


class GraphAnalysisResult(V50Model):
    version: str = "v50.graph_analysis_result.v1"
    analysis_id: str
    reading_id: str
    graph_id: str
    policy_version: str = "node_importance_policy_v2"
    node_metrics: list[NodeImportanceMetric] = Field(default_factory=list)
    ranked_node_ids: list[str] = Field(default_factory=list)
    creates_judgment: bool = False
    calls_brain: bool = False
    calls_llm: bool = False
    boundary: str = "graph_analysis_outputs_simulation_ready_evidence_not_verdict"

    @model_validator(mode="after")
    def _boundary(self) -> "GraphAnalysisResult":
        require_non_empty(self.analysis_id, "analysis_id")
        require_non_empty(self.reading_id, "reading_id")
        require_non_empty(self.graph_id, "graph_id")
        if self.creates_judgment:
            raise ValueError("GraphAnalysisResult cannot create judgment")
        if self.calls_brain:
            raise ValueError("GraphAnalysisResult cannot call Brain")
        if self.calls_llm:
            raise ValueError("GraphAnalysisResult cannot call LLM")
        return self
