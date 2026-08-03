from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

REGIME_WEAK_VS_FOLLOW_METHOD_REF = "REGIME_WEAK_VS_FOLLOW_TREND_001"
MINGLI_AGENT_REGIME_DECISION_VERSION = "v60.mingli-agent-regime-decision.002"

RegimeClassification = Literal[
    "NON_WEAK_OUTSIDE_SCOPE",
    "ORDINARY_WEAK",
    "FALSE_FOLLOW_COMPETITION",
    "FOLLOW_TREND",
    "UNRESOLVED",
]
RegimeFactStatus = Literal["PRESENT", "ABSENT", "UNRESOLVED"]
RegimeChainStatus = Literal["CLOSED", "OPEN", "UNRESOLVED"]
RegimeCompetitionKind = Literal[
    "VISIBLE_PEER",
    "HIDDEN_RESOURCE",
    "COMBINATION_UNRESOLVED",
]


class AgentRegimeDecision(BaseModel):
    """Typed weak-vs-follow audit; it does not force every rooted chart to be weak."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    method_asset_ref: Literal["REGIME_WEAK_VS_FOLLOW_TREND_001"]
    classification: RegimeClassification
    effective_root_status: RegimeFactStatus = Field(
        description=(
            "整盘裁决后的有效根状态；它不是根候选清单是否为空。"
            "有候选但尚未裁定时必须为 UNRESOLVED。"
        )
    )
    effective_root_coordinates: tuple[str, ...] = Field(
        max_length=8,
        description="仅在 effective_root_status=PRESENT 时填写已裁定的根候选坐标。",
    )
    rooted_visible_support_status: RegimeFactStatus = Field(
        description=(
            "有效根与明干同类共同形成的有根明透支持；"
            "visible_peer_support 为空时必须为 ABSENT，且不得改写有效根状态。"
        )
    )
    dominant_chain_status: RegimeChainStatus
    competition_kinds: tuple[RegimeCompetitionKind, ...] = Field(
        max_length=3,
        description="按明干同类、藏印与未决组合的实际存在逐项归槽。",
    )
    evidence_ids: tuple[str, ...] = Field(min_length=1, max_length=10)

    @model_validator(mode="after")
    def typed_lists_are_consistent(self) -> AgentRegimeDecision:
        if len(self.effective_root_coordinates) != len(
            set(self.effective_root_coordinates)
        ):
            raise ValueError("mingli_agent_regime_root_coordinates_not_unique")
        if self.effective_root_status != "PRESENT" and self.effective_root_coordinates:
            raise ValueError("mingli_agent_regime_nonpresent_root_has_coordinates")
        if len(self.competition_kinds) != len(set(self.competition_kinds)):
            raise ValueError("mingli_agent_regime_competition_kinds_not_unique")
        if len(self.evidence_ids) != len(set(self.evidence_ids)):
            raise ValueError("mingli_agent_regime_evidence_not_unique")
        return self
