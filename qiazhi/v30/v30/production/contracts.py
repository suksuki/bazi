from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import Field, model_validator

from v30.contracts import RoleKey, V30Model


PRODUCTION_SIDECAR_VERSION = "v30.production_sidecar.v1"
SIGNAL_REGISTRY_VERSION = "v30.signal_registry.v1"
BAZI_SIGNAL_VERSION = "v30.bazi_signal.v1"
SIGNAL_USAGE_AUDIT_VERSION = "v30.signal_usage_audit.v1"
MODULE_AUDIT_ENTRY_VERSION = "v30.module_audit_entry.v1"
PRODUCTION_AUDIT_SUMMARY_VERSION = "v30.production_audit_summary.v1"


class SignalSourceType(str, Enum):
    FEATURE_EVIDENCE = "feature_evidence"
    MATCHED_RULE = "matched_rule"
    DIAGNOSIS_FEATURE = "diagnosis_feature"
    DIAGNOSIS_PATH = "diagnosis_path"
    DIAGNOSIS_PORTRAIT = "diagnosis_portrait"
    DIAGNOSIS_CLAIM = "diagnosis_claim"
    RANKED_DECISION = "ranked_decision"
    MACRO_DIMENSION = "macro_dimension"
    STAGE_POINT = "stage_point"
    PRACTITIONER_SELECTION = "practitioner_selection"
    LEARNING_OVERLAY = "learning_overlay"
    ZIWEI_SIGNAL = "ziwei_signal"


class SourceModule(str, Enum):
    FEATURE_COMPILER = "feature_compiler"
    KNOWLEDGE_MACRO = "knowledge_macro"
    RANKED_DECISION = "ranked_decision"
    RULE_MATCHER = "rule_matcher"
    DIAGNOSIS_FEATURE_ENGINE = "diagnosis_feature_engine"
    DIAGNOSIS_PATH_ENGINE = "diagnosis_path_engine"
    DIAGNOSIS_PORTRAIT_ENGINE = "diagnosis_portrait_engine"
    DIAGNOSIS_CLAIM_GENERATOR = "diagnosis_claim_generator"
    STAGE_POINT = "stage_point"
    PRACTITIONER_INTERACTION = "practitioner_interaction"
    LEARNING_OVERLAY = "learning_overlay"
    ZIWEI_DOMAIN_LENS = "ziwei_domain_lens"


class SignalPolarity(str, Enum):
    SUPPORT = "support"
    OPPOSE = "oppose"
    MIXED = "mixed"
    NEUTRAL = "neutral"


class AssertionLevelHint(str, Enum):
    CONFIRMED = "confirmed"
    SUPPORTED = "supported"
    MIXED = "mixed"
    WEAK_CANDIDATE = "weak_candidate"
    BLOCKED = "blocked"


class ModuleOutputStatus(str, Enum):
    OUTPUT_BOUND = "output_bound"
    RUNTIME_USED = "runtime_used"
    CANDIDATE = "candidate"
    TRAIN_ONLY = "train_only"
    TEST_ONLY = "test_only"
    DEBUG_ONLY = "debug_only"
    ORPHAN = "orphan"
    PARTIAL_ORPHAN = "partial_orphan"


class BaziTopic(str, Enum):
    CHART = "chart"
    STRUCTURE = "structure"
    USEFUL_GOD = "useful_god"
    TIMING = "timing"
    WEALTH = "wealth"
    CAREER = "career"
    RELATIONSHIP = "relationship"
    HEALTH = "health"
    HIDDEN_FACTOR = "hidden_factor"
    FEATURE = "feature"
    RULE = "rule"
    PATH = "path"
    PORTRAIT = "portrait"
    MACRO = "macro"
    ADVICE = "advice"
    QUESTION = "question"
    MOBILITY = "mobility"
    PROPERTY = "property"
    SOCIAL = "social"
    UNKNOWN = "unknown"


class BaziDomain(str, Enum):
    OVERVIEW = "overview"
    CHART = "chart"
    STRUCTURE = "structure"
    USEFUL_GOD = "useful_god"
    TIMING = "timing"
    WEALTH = "wealth"
    CAREER = "career"
    RELATIONSHIP = "relationship"
    HEALTH = "health"
    HIDDEN_FACTOR = "hidden_factor"
    ELEMENT = "element"
    TEN_GOD = "ten_god"
    FAMILY = "family"
    RISK = "risk"
    LEARNING = "learning"
    LOCATION = "location"
    MOBILITY = "mobility"
    PROPERTY = "property"
    SOCIAL = "social"
    UNKNOWN = "unknown"


class BaziSignal(V30Model):
    version: str = BAZI_SIGNAL_VERSION
    signal_id: str
    source_module: SourceModule
    source_type: SignalSourceType
    source_ref: str = ""
    topic: BaziTopic = BaziTopic.UNKNOWN
    domain: BaziDomain = BaziDomain.UNKNOWN
    role_visibility: list[RoleKey] = Field(default_factory=lambda: ["user", "practitioner", "admin"])
    claim: str
    claim_key: str = ""
    polarity: SignalPolarity = SignalPolarity.NEUTRAL
    strength: float = Field(default=0.0, ge=0.0, le=1.0)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    assertion_level_hint: AssertionLevelHint = AssertionLevelHint.WEAK_CANDIDATE
    evidence_refs: list[str] = Field(default_factory=list)
    counter_evidence_refs: list[str] = Field(default_factory=list)
    branch_group_id: str = ""
    conflict_group_id: str = ""
    training_targets: list[str] = Field(default_factory=list)
    boundary: str = ""
    raw_ref: str = ""

    @model_validator(mode="after")
    def _signal_has_required_material(self) -> "BaziSignal":
        if not self.signal_id.strip():
            raise ValueError("BaziSignal requires signal_id")
        if not self.claim.strip():
            raise ValueError("BaziSignal requires claim")
        if not self.role_visibility:
            raise ValueError("BaziSignal requires role_visibility")
        return self


class SignalRegistry(V30Model):
    version: str = SIGNAL_REGISTRY_VERSION
    registry_id: str
    reading_id: str
    signals: list[BaziSignal] = Field(default_factory=list)
    validation_issues: list[dict[str, Any]] = Field(default_factory=list)
    boundary: str = "signal_registry_registers_runtime_outputs_without_replacing_decision_engine"

    def register(self, signal: BaziSignal) -> "SignalRegistry":
        existing = {row.signal_id for row in self.signals}
        if signal.signal_id in existing:
            return self
        return self.model_copy(update={"signals": [*self.signals, signal]})

    def register_many(self, signals: list[BaziSignal]) -> "SignalRegistry":
        registry = self
        for signal in signals:
            registry = registry.register(signal)
        return registry.model_copy(update={"validation_issues": validate_signal_rows(registry.signals)})

    def by_source_type(self, source_type: SignalSourceType) -> list[BaziSignal]:
        return [row for row in self.signals if row.source_type == source_type]

    def by_topic(self, topic: BaziTopic) -> list[BaziSignal]:
        return [row for row in self.signals if row.topic == topic]

    def by_domain(self, domain: BaziDomain) -> list[BaziSignal]:
        return [row for row in self.signals if row.domain == domain]

    def by_claim_key(self, claim_key: str) -> list[BaziSignal]:
        return [row for row in self.signals if row.claim_key == claim_key]

    def by_role(self, role_key: RoleKey) -> list[BaziSignal]:
        return [row for row in self.signals if role_key in row.role_visibility]


class SignalUsageAudit(V30Model):
    version: str = SIGNAL_USAGE_AUDIT_VERSION
    signal_id: str
    consumed_by_decision: bool = False
    consumed_by_verdict: bool = False
    consumed_by_advice: bool = False
    consumed_by_ui: bool = False
    consumed_by_training: bool = False
    indirect_consumers: list[str] = Field(default_factory=list)
    output_bound: bool = False
    status: ModuleOutputStatus = ModuleOutputStatus.CANDIDATE
    notes: list[str] = Field(default_factory=list)


class ModuleAuditEntry(V30Model):
    version: str = MODULE_AUDIT_ENTRY_VERSION
    module_name: SourceModule
    source_types: list[SignalSourceType] = Field(default_factory=list)
    produced_count: int = Field(default=0, ge=0)
    signal_count: int = Field(default=0, ge=0)
    consumed_by_decision_count: int = Field(default=0, ge=0)
    consumed_by_verdict_count: int = Field(default=0, ge=0)
    consumed_by_advice_count: int = Field(default=0, ge=0)
    consumed_by_ui_count: int = Field(default=0, ge=0)
    consumed_by_training_count: int = Field(default=0, ge=0)
    output_bound_count: int = Field(default=0, ge=0)
    status: ModuleOutputStatus = ModuleOutputStatus.CANDIDATE
    example_signal_ids: list[str] = Field(default_factory=list)
    missing_fields: list[str] = Field(default_factory=list)
    recommended_action: str = ""


class ProductionAuditSummary(V30Model):
    version: str = PRODUCTION_AUDIT_SUMMARY_VERSION
    reading_id: str
    signal_count: int = Field(default=0, ge=0)
    module_count: int = Field(default=0, ge=0)
    output_bound_signal_count: int = Field(default=0, ge=0)
    decision_consumed_signal_count: int = Field(default=0, ge=0)
    verdict_consumed_signal_count: int = Field(default=0, ge=0)
    advice_consumed_signal_count: int = Field(default=0, ge=0)
    ui_consumed_signal_count: int = Field(default=0, ge=0)
    training_consumed_signal_count: int = Field(default=0, ge=0)
    status_counts: dict[str, int] = Field(default_factory=dict)
    validation_issue_count: int = Field(default=0, ge=0)
    top_output_bound_modules: list[str] = Field(default_factory=list)
    candidate_module_count: int = Field(default=0, ge=0)
    orphan_module_count: int = Field(default=0, ge=0)
    boundary: str = "production_audit_summary_observes_output_responsibility_without_runtime_mutation"


class ProductionSidecar(V30Model):
    version: str = PRODUCTION_SIDECAR_VERSION
    reading_id: str
    registry: SignalRegistry
    usage_audit: list[SignalUsageAudit] = Field(default_factory=list)
    module_audit: list[ModuleAuditEntry] = Field(default_factory=list)
    summary: ProductionAuditSummary
    decision_engine_mutated: bool = False
    verdict_mutated: bool = False
    final_synthesis_mutated: bool = False
    llm_decision_authority: bool = False
    boundary: str = "production_sidecar_is_parallel_audit_not_decision_runtime"


def validate_signal_rows(signals: list[BaziSignal]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    seen: set[str] = set()
    for signal in signals:
        missing: list[str] = []
        if signal.signal_id in seen:
            issues.append({"signal_id": signal.signal_id, "issue": "duplicate_signal_id"})
            continue
        seen.add(signal.signal_id)
        if not signal.source_ref:
            missing.append("source_ref")
        if not signal.claim_key:
            missing.append("claim_key")
        if signal.assertion_level_hint in {AssertionLevelHint.CONFIRMED, AssertionLevelHint.SUPPORTED} and not signal.evidence_refs:
            missing.append("evidence_refs")
        if not signal.boundary:
            missing.append("boundary")
        if missing:
            issues.append(
                {
                    "signal_id": signal.signal_id,
                    "issue": "missing_fields",
                    "missing_fields": missing,
                }
            )
    return issues
