from __future__ import annotations

from collections import Counter
from enum import Enum

from pydantic import Field, model_validator

from v40.contracts.base import AssertionLevel, Polarity, RoleKey, Topic, V40Model
from v40.contracts.signal import RuntimeSignal, SignalSource


class MingliAssetType(str, Enum):
    FACT_RULE = "fact_rule"
    FEATURE_RULE = "feature_rule"
    DIAGNOSIS_RULE = "diagnosis_rule"
    PATH_RULE = "path_rule"
    PORTRAIT_RULE = "portrait_rule"
    KNOWLEDGE_CARD = "knowledge_card"
    PROBE_TEMPLATE = "probe_template"
    DOMAIN_ADAPTER_SEED = "domain_adapter_seed"
    HIDDEN_FACTOR_SEED = "hidden_factor_seed"
    ZIWEI_LENS_SEED = "ziwei_lens_seed"


class MingliAssetTargetType(str, Enum):
    RUNTIME_SIGNAL = "runtime_signal"
    KNOWLEDGE_CARD = "knowledge_card"
    PROBE_TEMPLATE = "probe_template"
    DECISION_CANDIDATE_SEED = "decision_candidate_seed"
    ADVICE_SEED = "advice_seed"
    TRAINING_RULE = "training_rule"


class MingliAssetMigrationStatus(str, Enum):
    DRAFT = "draft"
    SIDECAR = "sidecar"
    EVALUATING = "evaluating"
    ENABLED = "enabled"
    DISABLED = "disabled"
    REJECTED = "rejected"


class MigratedMingliAsset(V40Model):
    version: str = "v40.migrated_mingli_asset.v1"
    asset_id: str
    source_v30_module: str
    source_ref: str = ""
    asset_type: MingliAssetType
    target_v40_type: MingliAssetTargetType = MingliAssetTargetType.RUNTIME_SIGNAL
    topic: Topic = Topic.OVERVIEW
    domain: str = ""
    claim_key: str = ""
    claim: str
    evidence_refs: list[str] = Field(default_factory=list)
    counter_evidence_refs: list[str] = Field(default_factory=list)
    evidence_policy: str = "requires_chart_or_rule_evidence"
    default_confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    strength: float = Field(default=0.5, ge=0.0, le=1.0)
    polarity: Polarity = Polarity.NEUTRAL
    assertion_hint: AssertionLevel = AssertionLevel.WEAK_CANDIDATE
    max_assertion_level: AssertionLevel = AssertionLevel.SUPPORTED
    forbidden_user_claims: list[str] = Field(default_factory=list)
    allowed_roles: list[RoleKey] = Field(default_factory=lambda: ["practitioner", "admin", "lab"])
    user_visible: bool = False
    required_tests: list[str] = Field(default_factory=list)
    migration_status: MingliAssetMigrationStatus = MingliAssetMigrationStatus.DRAFT
    raw_v30_runtime_path: str = ""
    raw_v30_database_ref: str = ""
    raw_v30_redis_key: str = ""
    boundary: str = "migrated_mingli_asset_is_plain_json_asset_not_v30_runtime_import"

    @model_validator(mode="after")
    def _asset_boundary(self) -> "MigratedMingliAsset":
        if not self.asset_id.strip():
            raise ValueError("MigratedMingliAsset requires asset_id")
        if not self.source_v30_module.strip():
            raise ValueError("MigratedMingliAsset requires source_v30_module")
        if not self.claim.strip():
            raise ValueError("MigratedMingliAsset requires claim")
        if self.raw_v30_runtime_path or self.raw_v30_database_ref or self.raw_v30_redis_key:
            raise ValueError("MigratedMingliAsset cannot carry raw V30 runtime, DB, or Redis refs")
        if self.target_v40_type == MingliAssetTargetType.RUNTIME_SIGNAL and not self.evidence_refs:
            raise ValueError("RuntimeSignal migrated assets require evidence_refs")
        if self.migration_status == MingliAssetMigrationStatus.ENABLED and not self.required_tests:
            raise ValueError("Enabled migrated assets require required_tests")
        if not self.allowed_roles:
            raise ValueError("MigratedMingliAsset requires allowed_roles")
        return self


class MingliAssetMigrationGateResult(V40Model):
    version: str = "v40.mingli_asset_migration_gate_result.v1"
    gate_id: str
    reading_id: str
    asset_count: int = Field(default=0, ge=0)
    signal_count: int = Field(default=0, ge=0)
    accepted_asset_ids: list[str] = Field(default_factory=list)
    blocked_asset_ids: list[str] = Field(default_factory=list)
    status_counts: dict[str, int] = Field(default_factory=dict)
    target_counts: dict[str, int] = Field(default_factory=dict)
    blocked_reasons: dict[str, list[str]] = Field(default_factory=dict)
    signals: list[RuntimeSignal] = Field(default_factory=list)
    writes_v30_state: bool = False
    writes_v40_production: bool = False
    boundary: str = "mingli_asset_migration_gate_converts_assets_to_sidecar_signals_without_production_write"

    @model_validator(mode="after")
    def _gate_boundary(self) -> "MingliAssetMigrationGateResult":
        if not self.gate_id.strip():
            raise ValueError("MingliAssetMigrationGateResult requires gate_id")
        if not self.reading_id.strip():
            raise ValueError("MingliAssetMigrationGateResult requires reading_id")
        if self.asset_count != len(self.accepted_asset_ids) + len(self.blocked_asset_ids):
            raise ValueError("MingliAssetMigrationGateResult asset counts must match accepted and blocked ids")
        if self.signal_count != len(self.signals):
            raise ValueError("MingliAssetMigrationGateResult signal_count must match signals")
        if self.writes_v30_state:
            raise ValueError("MingliAssetMigrationGateResult cannot write V30 state")
        if self.writes_v40_production:
            raise ValueError("MingliAssetMigrationGateResult cannot write V40 production")
        return self


RUNNABLE_STATUSES = {
    MingliAssetMigrationStatus.SIDECAR,
    MingliAssetMigrationStatus.EVALUATING,
    MingliAssetMigrationStatus.ENABLED,
}

ASSERTION_RANK = {
    AssertionLevel.BLOCKED: 0,
    AssertionLevel.WEAK_CANDIDATE: 1,
    AssertionLevel.MIXED: 2,
    AssertionLevel.SUPPORTED: 3,
    AssertionLevel.CONFIRMED: 4,
}


def build_mingli_asset_migration_gate(
    *,
    gate_id: str,
    reading_id: str,
    assets: list[MigratedMingliAsset],
) -> MingliAssetMigrationGateResult:
    accepted_ids: list[str] = []
    blocked_ids: list[str] = []
    blocked_reasons: dict[str, list[str]] = {}
    signals: list[RuntimeSignal] = []
    for asset in assets:
        reasons = _asset_blocking_reasons(asset)
        if reasons:
            blocked_ids.append(asset.asset_id)
            blocked_reasons[asset.asset_id] = reasons
            continue
        accepted_ids.append(asset.asset_id)
        if asset.target_v40_type == MingliAssetTargetType.RUNTIME_SIGNAL:
            signals.append(_asset_to_signal(asset=asset, reading_id=reading_id))
    return MingliAssetMigrationGateResult(
        gate_id=gate_id,
        reading_id=reading_id,
        asset_count=len(assets),
        signal_count=len(signals),
        accepted_asset_ids=accepted_ids,
        blocked_asset_ids=blocked_ids,
        status_counts=dict(sorted(Counter(asset.migration_status.value for asset in assets).items())),
        target_counts=dict(sorted(Counter(asset.target_v40_type.value for asset in assets).items())),
        blocked_reasons=blocked_reasons,
        signals=signals,
    )


def adapt_mingli_assets_to_runtime_signals(
    *,
    reading_id: str,
    assets: list[MigratedMingliAsset],
) -> list[RuntimeSignal]:
    return build_mingli_asset_migration_gate(
        gate_id=f"mingli-asset-gate:{reading_id}",
        reading_id=reading_id,
        assets=assets,
    ).signals


def _asset_blocking_reasons(asset: MigratedMingliAsset) -> list[str]:
    reasons: list[str] = []
    if asset.migration_status not in RUNNABLE_STATUSES:
        reasons.append(f"migration_status_{asset.migration_status.value}_not_runnable")
    if asset.target_v40_type != MingliAssetTargetType.RUNTIME_SIGNAL:
        reasons.append(f"target_{asset.target_v40_type.value}_not_runtime_signal_v1")
    if not asset.evidence_refs:
        reasons.append("missing_evidence_refs")
    if asset.assertion_hint == AssertionLevel.CONFIRMED and asset.max_assertion_level != AssertionLevel.CONFIRMED:
        reasons.append("assertion_hint_above_max_assertion_level")
    return reasons


def _asset_to_signal(*, asset: MigratedMingliAsset, reading_id: str) -> RuntimeSignal:
    return RuntimeSignal(
        signal_id=f"migrated:{reading_id}:{asset.asset_id}",
        reading_id=reading_id,
        source=SignalSource.BAZI_ENGINE,
        source_ref=f"v30_asset:{asset.source_v30_module}:{asset.source_ref or asset.asset_id}",
        topic=asset.topic,
        claim=asset.claim,
        claim_key=asset.claim_key or asset.asset_id,
        polarity=asset.polarity,
        strength=asset.strength,
        confidence=asset.default_confidence,
        assertion_hint=_bounded_assertion(asset.assertion_hint, asset.max_assertion_level),
        evidence_refs=asset.evidence_refs,
        counter_evidence_refs=asset.counter_evidence_refs,
        role_visibility=_role_visibility(asset),
        trainable_targets=_trainable_targets(asset),
    )


def _bounded_assertion(assertion: AssertionLevel, maximum: AssertionLevel) -> AssertionLevel:
    if ASSERTION_RANK[assertion] <= ASSERTION_RANK[maximum]:
        return assertion
    return maximum


def _role_visibility(asset: MigratedMingliAsset) -> list[RoleKey]:
    roles = list(dict.fromkeys(asset.allowed_roles))
    if asset.user_visible:
        return roles
    return [role for role in roles if role not in {"guest", "user"}] or ["practitioner", "admin", "lab"]


def _trainable_targets(asset: MigratedMingliAsset) -> list[str]:
    targets = [
        f"asset_weight.{asset.asset_type.value}",
        f"source_weight.{asset.source_v30_module}",
    ]
    if asset.claim_key:
        targets.append(f"claim_score.{asset.claim_key}")
    if asset.domain:
        targets.append(f"domain_adapter.{asset.domain}")
    return targets
