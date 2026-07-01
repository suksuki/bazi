from __future__ import annotations

from pydantic import Field, model_validator

from v40.contracts.base import Polarity, Topic, V40Model
from v40.contracts.training import LocalOverlay, TrainingLabelEvent


class AnswerSignal(V40Model):
    version: str = "v40.answer_signal.v1"
    signal_id: str
    reading_id: str
    probe_id: str = ""
    topic: Topic = Topic.UNKNOWN
    question: str
    answer_text: str
    selected_option: str = ""
    interpreted_claim: str
    polarity: Polarity = Polarity.SUPPORT
    supports_target_ids: list[str] = Field(default_factory=list)
    weakens_target_ids: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    evidence_refs: list[str] = Field(default_factory=list)
    decision_authority: bool = False
    chart_fact_mutation_allowed: bool = False
    boundary: str = "answer_signal_captures_user_reality_without_verdict_or_chart_fact_authority"

    @model_validator(mode="after")
    def _answer_signal_boundary(self) -> "AnswerSignal":
        if not self.signal_id.strip():
            raise ValueError("AnswerSignal requires signal_id")
        if not self.reading_id.strip():
            raise ValueError("AnswerSignal requires reading_id")
        if not self.question.strip():
            raise ValueError("AnswerSignal requires question")
        if not self.answer_text.strip():
            raise ValueError("AnswerSignal requires answer_text")
        if not self.interpreted_claim.strip():
            raise ValueError("AnswerSignal requires interpreted_claim")
        if self.decision_authority:
            raise ValueError("AnswerSignal cannot have decision authority")
        if self.chart_fact_mutation_allowed:
            raise ValueError("AnswerSignal cannot mutate chart facts")
        return self


class HiddenAttributeUpdate(V40Model):
    version: str = "v40.hidden_attribute_update.v1"
    update_id: str
    reading_id: str
    probe_id: str = ""
    answer_signal_id: str
    topic: Topic = Topic.HIDDEN_ATTRIBUTE
    attribute_key: str
    value: str
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    evidence_refs: list[str] = Field(default_factory=list)
    local_only: bool = True
    chart_fact_mutation_allowed: bool = False
    boundary: str = "hidden_attribute_update_updates_current_reading_context_not_chart_facts"

    @model_validator(mode="after")
    def _hidden_attribute_boundary(self) -> "HiddenAttributeUpdate":
        if not self.update_id.strip():
            raise ValueError("HiddenAttributeUpdate requires update_id")
        if not self.answer_signal_id.strip():
            raise ValueError("HiddenAttributeUpdate requires answer_signal_id")
        if not self.attribute_key.strip():
            raise ValueError("HiddenAttributeUpdate requires attribute_key")
        if not self.value.strip():
            raise ValueError("HiddenAttributeUpdate requires value")
        if not self.local_only:
            raise ValueError("HiddenAttributeUpdate must be local_only before reviewed training")
        if self.chart_fact_mutation_allowed:
            raise ValueError("HiddenAttributeUpdate cannot mutate chart facts")
        return self


class ProbeAnswerResult(V40Model):
    version: str = "v40.probe_answer_result.v1"
    result_id: str
    reading_id: str
    answer_signal: AnswerSignal
    hidden_attribute_update: HiddenAttributeUpdate
    training_label: TrainingLabelEvent
    local_overlay: LocalOverlay
    refined_advice_points: list[str] = Field(default_factory=list)
    user_message: str
    changes_verdict: bool = False
    changes_chart_facts: bool = False
    writes_v40_production: bool = False
    writes_v30_state: bool = False
    boundary: str = "probe_answer_result_refines_current_reading_without_decision_or_fact_mutation"

    @model_validator(mode="after")
    def _probe_answer_result_boundary(self) -> "ProbeAnswerResult":
        if not self.result_id.strip():
            raise ValueError("ProbeAnswerResult requires result_id")
        if self.answer_signal.reading_id != self.reading_id:
            raise ValueError("ProbeAnswerResult requires matching answer_signal reading_id")
        if self.hidden_attribute_update.reading_id != self.reading_id:
            raise ValueError("ProbeAnswerResult requires matching hidden_attribute reading_id")
        if self.training_label.reading_id != self.reading_id:
            raise ValueError("ProbeAnswerResult requires matching training_label reading_id")
        if self.local_overlay.reading_id != self.reading_id:
            raise ValueError("ProbeAnswerResult requires matching overlay reading_id")
        if self.changes_verdict:
            raise ValueError("ProbeAnswerResult cannot directly change verdict")
        if self.changes_chart_facts:
            raise ValueError("ProbeAnswerResult cannot change chart facts")
        if self.writes_v40_production:
            raise ValueError("ProbeAnswerResult cannot write V40 production")
        if self.writes_v30_state:
            raise ValueError("ProbeAnswerResult cannot write V30 state")
        return self
