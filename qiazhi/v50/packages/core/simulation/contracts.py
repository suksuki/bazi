from __future__ import annotations

from enum import Enum

from pydantic import Field, model_validator

from core.contracts.base import V50Model, require_non_empty, require_refs
from core.graph.contracts import NodeImportanceMetric


class PerturbationType(str, Enum):
    REMOVE_NODE = "remove_node"
    WEAKEN_NODE = "weaken_node"
    ADD_LUCK_CYCLE = "add_luck_cycle"
    ADD_ANNUAL_CYCLE = "add_annual_cycle"
    ADD_TWIN_EVIDENCE = "add_twin_evidence"
    ADD_ZIWEI_ACTIVATION = "add_ziwei_activation"


class MingliState(V50Model):
    version: str = "v50.mingli_state.v1"
    state_id: str
    reading_id: str
    graph_id: str
    analysis_id: str
    policy_version: str
    node_metrics: list[NodeImportanceMetric] = Field(default_factory=list)
    active_flows: list[str] = Field(default_factory=list)
    mechanism_scores: dict[str, float] = Field(default_factory=dict)
    creates_judgment: bool = False
    calls_brain: bool = False
    calls_llm: bool = False
    evidence_refs: list[str] = Field(default_factory=list)
    boundary: str = "mingli_state_is_simulation_evidence_not_verdict"

    @model_validator(mode="after")
    def _boundary(self) -> "MingliState":
        require_non_empty(self.state_id, "state_id")
        require_non_empty(self.reading_id, "reading_id")
        require_non_empty(self.graph_id, "graph_id")
        require_non_empty(self.analysis_id, "analysis_id")
        require_refs(self.evidence_refs, "evidence_refs")
        if self.creates_judgment:
            raise ValueError("MingliState cannot create judgment")
        if self.calls_brain:
            raise ValueError("MingliState cannot call Brain")
        if self.calls_llm:
            raise ValueError("MingliState cannot call LLM")
        return self


class AblationResult(V50Model):
    version: str = "v50.ablation_result.v1"
    ablation_id: str
    reading_id: str
    state_id: str
    perturbation_type: PerturbationType = PerturbationType.REMOVE_NODE
    target_node_id: str
    target_label: str
    target_position: str = ""
    state_delta: float = Field(default=0.0, ge=0.0, le=1.0)
    affected_flows: list[str] = Field(default_factory=list)
    mechanism_score_delta: dict[str, float] = Field(default_factory=dict)
    explanation_codes: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    boundary: str = "ablation_result_is_counterfactual_evidence_not_verdict"

    @model_validator(mode="after")
    def _boundary(self) -> "AblationResult":
        require_non_empty(self.ablation_id, "ablation_id")
        require_non_empty(self.reading_id, "reading_id")
        require_non_empty(self.state_id, "state_id")
        require_non_empty(self.target_node_id, "target_node_id")
        require_refs(self.evidence_refs, "evidence_refs")
        return self


class SimulationReport(V50Model):
    version: str = "v50.simulation_report.v1"
    report_id: str
    reading_id: str
    state_id: str
    ablation_results: list[AblationResult] = Field(default_factory=list)
    ranked_critical_node_ids: list[str] = Field(default_factory=list)
    creates_judgment: bool = False
    calls_brain: bool = False
    calls_llm: bool = False
    boundary: str = "simulation_report_outputs_mechanism_ready_evidence_not_verdict"

    @model_validator(mode="after")
    def _boundary(self) -> "SimulationReport":
        require_non_empty(self.report_id, "report_id")
        require_non_empty(self.reading_id, "reading_id")
        require_non_empty(self.state_id, "state_id")
        if self.creates_judgment:
            raise ValueError("SimulationReport cannot create judgment")
        if self.calls_brain:
            raise ValueError("SimulationReport cannot call Brain")
        if self.calls_llm:
            raise ValueError("SimulationReport cannot call LLM")
        return self
