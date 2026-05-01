from __future__ import annotations

from v20.core.schemas import ChartFacts, CoreInference, TimeContext
from v20.features.boundaries import boundary_for
from v20.features.calibration import ConfidenceCalibrationPolicy, calibrate_features
from v20.features.confidence import bounded_confidence
from v20.features.hierarchy import cluster_features
from v20.features.schema import BaziFeature, EvidenceRef, FeatureLayer

FEATURE_LAYER_VERSION = "v20.feature_layer.v1"

WEALTH_LABELS = {"正财", "偏财"}


def compile_features(
    facts: ChartFacts,
    inference: CoreInference,
    rule_paths: tuple[object, ...] = (),
    time_context: TimeContext | None = None,
    calibration_policy: ConfidenceCalibrationPolicy | None = None,
) -> FeatureLayer:
    features: list[BaziFeature] = [
        _strength_feature(inference),
        _useful_god_gate_feature(inference),
    ]
    features.extend(_ten_god_features(facts))
    features.extend(_branch_features(facts))
    features.extend(_time_features(time_context or TimeContext()))
    features.extend(_wealth_features(facts))
    features.append(_pattern_index_feature(facts))
    features = _dedupe(features)
    features = list(calibrate_features(features, calibration_policy))
    features.sort(key=lambda row: (row.confidence, row.feature_id), reverse=True)
    macro_features = cluster_features(features)
    return FeatureLayer(version=FEATURE_LAYER_VERSION, features=tuple(features), macro_features=macro_features)


def _strength_feature(inference: CoreInference) -> BaziFeature:
    title_by_state = {
        "supported_capacity": "Day-master capacity has support evidence",
        "capacity_needs_support": "Day-master capacity needs support review",
        "borderline_capacity": "Day-master capacity is near boundary",
    }
    return BaziFeature(
        feature_id=f"feature.strength.{inference.day_master_capacity}",
        title=title_by_state.get(inference.day_master_capacity, "Day-master capacity evidence"),
        domain="strength",
        source_layers=("core",),
        evidence_refs=(
            EvidenceRef("core.support_score", "core_signal", f"support={inference.support_score}", "core"),
            EvidenceRef("core.pressure_score", "core_signal", f"pressure={inference.pressure_score}", "core"),
        ),
        confidence=bounded_confidence(0.35, abs(inference.support_score - inference.pressure_score)),
        readiness="boundary_ready",
        boundary=boundary_for("strength"),
        question_hooks=("q_strength_assessment", "q_useful_god_candidates"),
        answer_hooks=("strength_assessment",),
    )


def _useful_god_gate_feature(inference: CoreInference) -> BaziFeature:
    return BaziFeature(
        feature_id="feature.useful_god.evidence_gate",
        title="Useful-god evidence gate requires review",
        domain="useful_god",
        source_layers=("core",),
        evidence_refs=(
            EvidenceRef("core.day_master_capacity", "core_signal", inference.day_master_capacity, "core"),
        ),
        confidence=0.42,
        readiness="review_ready",
        boundary=boundary_for("useful_god"),
        question_hooks=("q_useful_god_candidates",),
        answer_hooks=("useful_god_boundary",),
    )


def _ten_god_features(facts: ChartFacts) -> list[BaziFeature]:
    visible_labels = sorted({row.label for row in facts.visible_ten_gods if row.label})
    hidden_labels = sorted({row.label for row in facts.hidden_ten_gods if row.label})
    features = []
    if visible_labels:
        features.append(
            BaziFeature(
                feature_id="feature.ten_god.visible_relation",
                title="Visible ten-god relations are available",
                domain="ten_god",
                source_layers=("visible",),
                evidence_refs=tuple(EvidenceRef(f"visible.{label}", "ten_god", label, "visible") for label in visible_labels[:6]),
                confidence=bounded_confidence(0.3, len(visible_labels) * 0.06),
                readiness="ready",
                boundary=boundary_for("ten_god"),
                question_hooks=("q_ten_god_focus", "q_ten_god_metadata"),
                answer_hooks=("metadata_boundary",),
            )
        )
    if hidden_labels:
        features.append(
            BaziFeature(
                feature_id="feature.ten_god.hidden_relation",
                title="Hidden-stem ten-god relations are available",
                domain="ten_god",
                source_layers=("hidden",),
                evidence_refs=tuple(EvidenceRef(f"hidden.{label}", "ten_god", label, "hidden") for label in hidden_labels[:6]),
                confidence=bounded_confidence(0.26, len(hidden_labels) * 0.04),
                readiness="ready",
                boundary=boundary_for("ten_god"),
                question_hooks=("q_hidden_stem_role", "q_ten_god_metadata"),
                answer_hooks=("metadata_boundary",),
            )
        )
    return features


def _branch_features(facts: ChartFacts) -> list[BaziFeature]:
    if not facts.relation_hits:
        return [
            BaziFeature(
                feature_id="feature.branch.relation_quiet",
                title="Branch relations are relatively quiet",
                domain="branch",
                source_layers=("natal",),
                evidence_refs=(EvidenceRef("branch.no_relation_hit", "branch_relation", "no major branch relation hit", "core"),),
                confidence=0.34,
                readiness="boundary_ready",
                boundary=boundary_for("branch"),
                question_hooks=("q_structure_overview",),
                answer_hooks=("structure_overview",),
            )
        ]
    refs = tuple(
        EvidenceRef(
            f"branch.{row.relation_type}.{'.'.join(row.branches)}",
            "branch_relation",
            row.relation_type,
            row.layer,
        )
        for row in facts.relation_hits[:6]
    )
    return [
        BaziFeature(
            feature_id="feature.branch.visible_relation",
            title="Visible branch relation requires layer review",
            domain="branch",
            source_layers=("natal",),
            evidence_refs=refs,
            confidence=bounded_confidence(0.36, len(refs) * 0.05),
            readiness="ready",
            boundary=boundary_for("branch"),
            question_hooks=("q_branch_relation_detail", "q_time_vs_natal_relation"),
            answer_hooks=("branch_relation",),
        )
    ]


def _time_features(time_context: TimeContext) -> list[BaziFeature]:
    if time_context.status != "ready" or not time_context.layers:
        return []
    refs: list[EvidenceRef] = []
    for layer in time_context.layers:
        refs.append(EvidenceRef(f"time.{layer.layer_key}.{layer.pillar.display}", "time_pillar", layer.pillar.display, "time"))
        refs.append(EvidenceRef(f"time.ten_god.{layer.layer_key}.{layer.ten_god.label}", "ten_god", layer.ten_god.label, "time"))
    for hit in time_context.relation_hits[:6]:
        refs.append(EvidenceRef(f"time.relation.{hit.relation_type}.{'.'.join(hit.positions)}", "branch_relation", hit.relation_type, "time"))
    return [
        BaziFeature(
            feature_id="feature.time.explicit_context",
            title="Explicit time layer is available",
            domain="time",
            source_layers=("time",),
            evidence_refs=tuple(refs[:10]),
            confidence=bounded_confidence(0.34, len(refs) * 0.035),
            readiness="review_ready",
            boundary=boundary_for("time"),
            question_hooks=("q_time_layer_context", "q_time_relation_triggers"),
            answer_hooks=("timing_context",),
        )
    ]


def _wealth_features(facts: ChartFacts) -> list[BaziFeature]:
    labels = [row for row in [*facts.visible_ten_gods, *facts.hidden_ten_gods] if row.label in WEALTH_LABELS]
    if not labels:
        return [
            BaziFeature(
                feature_id="feature.wealth.material_not_visible",
                title="Wealth material is not directly visible",
                domain="wealth",
                source_layers=("visible", "hidden"),
                evidence_refs=(EvidenceRef("wealth.no_material", "ten_god", "no wealth ten-god material found", "core"),),
                confidence=0.31,
                readiness="boundary_ready",
                boundary=boundary_for("wealth"),
                question_hooks=("q_income_stability",),
                answer_hooks=("income_structure",),
            )
        ]
    return [
        BaziFeature(
            feature_id="feature.wealth.material_available",
            title="Wealth material is structurally available",
            domain="wealth",
            source_layers=tuple(sorted({row.layer for row in labels})),
            evidence_refs=tuple(EvidenceRef(f"wealth.{row.layer}.{row.pillar}", "ten_god", row.label, row.layer) for row in labels[:6]),
            confidence=bounded_confidence(0.34, len(labels) * 0.04),
            readiness="ready",
            boundary=boundary_for("wealth"),
            question_hooks=("q_income_stability", "q_income_factors"),
            answer_hooks=("income_structure",),
        )
    ]


def _pattern_index_feature(facts: ChartFacts) -> BaziFeature:
    refs = tuple(EvidenceRef(f"vault.{position}", "vault", position, "core") for position in facts.vault_branches)
    return BaziFeature(
        feature_id="feature.pattern.review_index",
        title="Pattern review index is available",
        domain="pattern",
        source_layers=("core",),
        evidence_refs=refs or (EvidenceRef("pattern.index", "core_signal", "general structure index", "core"),),
        confidence=0.28 if not refs else 0.38,
        readiness="review_ready",
        boundary=boundary_for("pattern"),
        question_hooks=("q_pattern_structure",),
        answer_hooks=("pattern_structure",),
    )


def _dedupe(features: list[BaziFeature]) -> list[BaziFeature]:
    out: dict[str, BaziFeature] = {}
    for feature in features:
        current = out.get(feature.feature_id)
        if current is None or feature.confidence > current.confidence:
            out[feature.feature_id] = feature
    return list(out.values())
