from __future__ import annotations

from dataclasses import replace

from v20.core.elements import element_distribution, strongest_elements, weakest_elements
from v20.core.schemas import ChartFacts, CoreInference, TimeContext
from v20.core.useful_god import derive_useful_god_candidates
from v20.features.boundaries import boundary_for
from v20.features.calibration import ConfidenceCalibrationPolicy, calibrate_features
from v20.features.confidence import bounded_confidence
from v20.features.discovery_engine import build_feature_discovery_model
from v20.features.hierarchy import cluster_features
from v20.features.schema import BaziFeature, BaziFeatureContext, EvidenceRef, FeatureLayer

FEATURE_LAYER_VERSION = "v20.feature_layer.v1"

WEALTH_LABELS = {"正财", "偏财"}
ELEMENT_LABELS_ZH = {
    "wood": "木",
    "fire": "火",
    "earth": "土",
    "metal": "金",
    "water": "水",
}
POSITION_LABELS_ZH = {
    "year": "年柱",
    "month": "月柱",
    "day": "日柱",
    "hour": "时柱",
    "luck": "大运",
    "flow_year": "流年",
    "flow_month": "流月",
}
RELATION_LABELS_ZH = {
    "clash": "冲",
    "harmony": "合",
    "harm": "害",
    "break": "破",
    "punishment": "刑",
    "three_harmony": "三合",
    "three_meeting": "三会",
}
TEN_GOD_KEYS = {
    "比肩": "bi_jian",
    "劫财": "jie_cai",
    "食神": "shi_shen",
    "伤官": "shang_guan",
    "偏财": "pian_cai",
    "正财": "zheng_cai",
    "七杀": "qi_sha",
    "正官": "zheng_guan",
    "偏印": "pian_yin",
    "正印": "zheng_yin",
}


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
    features.extend(_ten_god_focus_features(facts))
    features.extend(_useful_god_candidate_features(facts, inference))
    features.append(_element_balance_feature(facts))
    features.extend(_element_emphasis_features(facts))
    features.extend(_branch_features(facts))
    features.extend(_time_features(time_context or TimeContext()))
    features.extend(_wealth_features(facts))
    features.append(_pattern_index_feature(facts))
    features = _dedupe(features)
    features = list(calibrate_features(features, calibration_policy))
    features = _attach_feature_contexts(features, time_context or TimeContext())
    features.sort(key=lambda row: (row.confidence, row.feature_id), reverse=True)
    macro_features = cluster_features(features)
    feature_tuple = tuple(features)
    feature_contexts = tuple(row.context for row in feature_tuple if row.context is not None)
    return FeatureLayer(
        version=FEATURE_LAYER_VERSION,
        features=feature_tuple,
        feature_contexts=feature_contexts,
        macro_features=macro_features,
        discovery_trace=build_feature_discovery_model(facts, inference, time_context or TimeContext(), feature_tuple),
    )


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


def _useful_god_candidate_features(facts: ChartFacts, inference: CoreInference) -> list[BaziFeature]:
    candidates = derive_useful_god_candidates(facts, inference)
    if not candidates:
        return []
    refs = tuple(
        EvidenceRef(
            f"useful_god.{row.path_key}.{row.element}",
            "useful_god_candidate",
            f"{row.path_type}:{row.element}",
            "core",
        )
        for row in candidates[:6]
    )
    summary = ";".join(f"{row.path_key}:{row.element}:{row.status}" for row in candidates[:4])
    return [
        BaziFeature(
            feature_id="feature.useful_god.candidate_paths",
            title="Useful-god candidate paths are compiled",
            domain="useful_god",
            source_layers=("core", "element", "strength"),
            evidence_refs=refs,
            confidence=max(row.confidence for row in candidates),
            readiness="review_ready",
            boundary=boundary_for("useful_god"),
            question_hooks=("q_useful_god_candidates", "q_useful_god_evidence_gaps"),
            answer_hooks=("useful_god_candidate_paths",),
            calibration_state=summary,
        )
    ]


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


def _ten_god_focus_features(facts: ChartFacts) -> list[BaziFeature]:
    grouped: dict[str, list[object]] = {}
    for row in [*facts.visible_ten_gods, *facts.hidden_ten_gods]:
        if row.label:
            grouped.setdefault(row.label, []).append(row)
    features = []
    for label, rows in sorted(grouped.items(), key=lambda item: (sum(row.weight for row in item[1]), item[0]), reverse=True):
        total_weight = round(sum(row.weight for row in rows), 3)
        visible_count = sum(1 for row in rows if row.layer == "visible")
        if total_weight < 1.45 and visible_count == 0:
            continue
        key = TEN_GOD_KEYS.get(label, label)
        evidence_refs = tuple(
            EvidenceRef(
                f"ten_god.focus.{key}.{row.layer}.{row.pillar}",
                "ten_god_focus",
                f"{label}@{POSITION_LABELS_ZH.get(row.pillar, row.pillar)}",
                row.layer,
            )
            for row in rows[:8]
        )
        hooks = ["q_ten_god_focus", "q_hidden_stem_role"]
        if label in {"正财", "偏财"}:
            hooks.insert(0, "q_income_factors")
        if label in {"正官", "七杀"}:
            hooks.insert(0, "q_career_structure")
        features.append(
            BaziFeature(
                feature_id=f"feature.ten_god.focus.{key}",
                title=f"{label} ten-god focus is chart-specific",
                domain="ten_god",
                source_layers=tuple(sorted({row.layer for row in rows})),
                evidence_refs=evidence_refs,
                confidence=bounded_confidence(0.33, min(0.24, total_weight * 0.045 + visible_count * 0.045)),
                readiness="ready",
                boundary=boundary_for("ten_god"),
                question_hooks=tuple(dict.fromkeys(hooks)),
                answer_hooks=("metadata_boundary",),
                calibration_state=f"label={label};weight={total_weight};visible={visible_count};count={len(rows)}",
            )
        )
    return features[:4]


def _element_balance_feature(facts: ChartFacts) -> BaziFeature:
    distribution = element_distribution(facts)
    strongest = strongest_elements(distribution)
    weakest = weakest_elements(distribution)
    refs = tuple(
        EvidenceRef(
            f"element.{element}",
            "element_distribution",
            f"{element}={distribution[element]}",
            "core",
        )
        for element in distribution
    )
    spread = max(distribution.values()) - min(distribution.values()) if distribution else 0.0
    return BaziFeature(
        feature_id="feature.element.balance_distribution",
        title="Five-element distribution is available",
        domain="element",
        source_layers=("core", "hidden"),
        evidence_refs=refs,
        confidence=bounded_confidence(0.32, min(0.22, spread * 0.04)),
        readiness="boundary_ready",
        boundary=boundary_for("element"),
        question_hooks=("q_element_balance", "q_element_support_pressure"),
        answer_hooks=("element_balance",),
        calibration_state=f"strongest={','.join(strongest)};weakest={','.join(weakest)}",
    )


def _element_emphasis_features(facts: ChartFacts) -> list[BaziFeature]:
    distribution = element_distribution(facts)
    if not distribution:
        return []
    peak = max(distribution.values())
    floor = min(distribution.values())
    spread = round(peak - floor, 3)
    if spread < 1.2:
        return []
    features: list[BaziFeature] = []
    for element in strongest_elements(distribution):
        label = ELEMENT_LABELS_ZH.get(element, element)
        features.append(
            BaziFeature(
                feature_id=f"feature.element.prominent.{element}",
                title=f"{label} element is structurally prominent",
                domain="element",
                source_layers=("core", "hidden"),
                evidence_refs=(
                    EvidenceRef(f"element.prominent.{element}", "element_emphasis", f"{label}偏显={distribution[element]}", "core"),
                    EvidenceRef("element.spread", "element_distribution", f"spread={spread}", "core"),
                ),
                confidence=bounded_confidence(0.34, min(0.25, spread * 0.055)),
                readiness="boundary_ready",
                boundary=boundary_for("element"),
                question_hooks=("q_element_balance", "q_element_support_pressure"),
                answer_hooks=("element_balance",),
                calibration_state=f"element={element};state=prominent;value={distribution[element]};spread={spread}",
            )
        )
    for element in weakest_elements(distribution):
        label = ELEMENT_LABELS_ZH.get(element, element)
        features.append(
            BaziFeature(
                feature_id=f"feature.element.weak.{element}",
                title=f"{label} element is structurally thin",
                domain="element",
                source_layers=("core", "hidden"),
                evidence_refs=(
                    EvidenceRef(f"element.weak.{element}", "element_emphasis", f"{label}偏弱={distribution[element]}", "core"),
                    EvidenceRef("element.spread", "element_distribution", f"spread={spread}", "core"),
                ),
                confidence=bounded_confidence(0.31, min(0.22, spread * 0.045)),
                readiness="boundary_ready",
                boundary=boundary_for("element"),
                question_hooks=("q_element_support_pressure", "q_element_balance"),
                answer_hooks=("element_balance",),
                calibration_state=f"element={element};state=weak;value={distribution[element]};spread={spread}",
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
            _relation_title(row),
            row.layer,
        )
        for row in facts.relation_hits[:6]
    )
    features = [
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
    by_type: dict[str, list[object]] = {}
    for hit in facts.relation_hits:
        by_type.setdefault(hit.relation_type, []).append(hit)
    for relation_type, hits in sorted(by_type.items(), key=lambda item: (len(item[1]), item[0]), reverse=True):
        refs = tuple(
            EvidenceRef(
                f"branch.{relation_type}.{'.'.join(row.branches)}.{index}",
                "branch_relation_focus",
                _relation_title(row),
                row.layer,
            )
            for index, row in enumerate(hits[:4])
        )
        features.append(
            BaziFeature(
                feature_id=f"feature.branch.relation_type.{relation_type}",
                title=f"Branch {relation_type} relation is chart-specific",
                domain="branch",
                source_layers=("natal",),
                evidence_refs=refs,
                confidence=bounded_confidence(0.34, len(refs) * 0.055),
                readiness="ready",
                boundary=boundary_for("branch"),
                question_hooks=("q_branch_relation_detail", "q_structure_overview"),
                answer_hooks=("branch_relation",),
                calibration_state=f"relation_type={relation_type};count={len(hits)}",
            )
        )
    return features


def _time_features(time_context: TimeContext) -> list[BaziFeature]:
    if time_context.status != "ready" or not time_context.layers:
        return []
    refs: list[EvidenceRef] = []
    for layer in time_context.layers:
        refs.append(EvidenceRef(f"time.{layer.layer_key}.{layer.pillar.display}", "time_pillar", layer.pillar.display, "time"))
        refs.append(EvidenceRef(f"time.ten_god.{layer.layer_key}.{layer.ten_god.label}", "ten_god", layer.ten_god.label, "time"))
    for hit in time_context.relation_hits[:6]:
        refs.append(
            EvidenceRef(
                f"time.relation.{hit.relation_type}.{'.'.join(hit.positions)}",
                "branch_relation",
                _relation_title(hit),
                "time",
            )
        )
    features = [
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
    if time_context.relation_hits:
        by_type: dict[str, list[object]] = {}
        for hit in time_context.relation_hits:
            by_type.setdefault(hit.relation_type, []).append(hit)
        for relation_type, hits in sorted(by_type.items(), key=lambda item: (len(item[1]), item[0]), reverse=True):
            features.append(
                BaziFeature(
                    feature_id=f"feature.time.relation_type.{relation_type}",
                    title=f"Time-layer {relation_type} trigger is available",
                    domain="time",
                    source_layers=("time",),
                    evidence_refs=tuple(
                        EvidenceRef(
                            f"time.relation.focus.{relation_type}.{index}",
                            "time_relation_focus",
                            _relation_title(hit),
                            "time",
                        )
                        for index, hit in enumerate(hits[:4])
                    ),
                    confidence=bounded_confidence(0.34, len(hits[:4]) * 0.06),
                    readiness="review_ready",
                    boundary=boundary_for("time"),
                    question_hooks=("q_time_relation_triggers", "q_time_layer_context"),
                    answer_hooks=("timing_context",),
                    calibration_state=f"relation_type={relation_type};count={len(hits)}",
                )
            )
    for layer in time_context.layers[:3]:
        label = layer.ten_god.label
        key = TEN_GOD_KEYS.get(label, label)
        features.append(
            BaziFeature(
                feature_id=f"feature.time.ten_god.{layer.layer_key}.{key}",
                title=f"Time-layer {label} material is available",
                domain="time",
                source_layers=("time",),
                evidence_refs=(
                    EvidenceRef(f"time.ten_god.focus.{layer.layer_key}", "time_ten_god_focus", f"{layer.pillar.display}={label}", "time"),
                ),
                confidence=0.41,
                readiness="review_ready",
                boundary=boundary_for("time"),
                question_hooks=("q_time_layer_context", "q_time_relation_triggers"),
                answer_hooks=("timing_context",),
                calibration_state=f"layer={layer.layer_key};ten_god={label};pillar={layer.pillar.display}",
            )
        )
    return features


def _wealth_features(facts: ChartFacts) -> list[BaziFeature]:
    visible_labels = [row for row in facts.visible_ten_gods if row.label in WEALTH_LABELS]
    hidden_labels = [row for row in facts.hidden_ten_gods if row.label in WEALTH_LABELS]
    labels = [*visible_labels, *hidden_labels]
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
    if not visible_labels:
        hidden_weight = round(sum(row.weight for row in hidden_labels), 3)
        return [
            BaziFeature(
                feature_id="feature.wealth.hidden_material",
                title="Wealth material is hidden-stem only",
                domain="wealth",
                source_layers=("hidden",),
                evidence_refs=tuple(
                    EvidenceRef(f"wealth.hidden.{row.pillar}.{index}", "ten_god", row.label, row.layer)
                    for index, row in enumerate(hidden_labels[:6])
                ),
                confidence=bounded_confidence(0.27, min(0.18, hidden_weight * 0.035)),
                readiness="boundary_ready",
                boundary=boundary_for("wealth"),
                question_hooks=("q_income_factors", "q_hidden_stem_role"),
                answer_hooks=("income_structure",),
                calibration_state=f"visibility=hidden_only;weight={hidden_weight};count={len(hidden_labels)}",
            )
        ]
    return [
        BaziFeature(
            feature_id="feature.wealth.visible_material",
            title="Wealth material is structurally available",
            domain="wealth",
            source_layers=tuple(sorted({row.layer for row in labels})),
            evidence_refs=tuple(
                EvidenceRef(f"wealth.{row.layer}.{row.pillar}.{index}", "ten_god", row.label, row.layer)
                for index, row in enumerate(labels[:6])
            ),
            confidence=bounded_confidence(0.38, len(visible_labels) * 0.07 + len(hidden_labels) * 0.025),
            readiness="ready",
            boundary=boundary_for("wealth"),
            question_hooks=("q_income_stability", "q_income_factors"),
            answer_hooks=("income_structure",),
            calibration_state=f"visibility=visible;visible={len(visible_labels)};hidden={len(hidden_labels)}",
        )
    ]


def _pattern_index_feature(facts: ChartFacts) -> BaziFeature:
    refs = tuple(
        EvidenceRef(
            f"vault.{position}",
            "vault",
            f"{POSITION_LABELS_ZH.get(position, position)}墓库藏气需要格局复核",
            "core",
        )
        for position in facts.vault_branches
    )
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


def _attach_feature_contexts(features: list[BaziFeature], time_context: TimeContext) -> list[BaziFeature]:
    return [
        replace(feature, context=_feature_context(feature, time_context))
        for feature in features
    ]


def _feature_context(feature: BaziFeature, time_context: TimeContext) -> BaziFeatureContext:
    decision_state = _context_decision_state(feature)
    feature_type = _feature_type(feature)
    source_rule_ids = _source_rules_for_feature(feature)
    evidence_atoms = tuple(ref.ref_id for ref in feature.evidence_refs if ref.ref_id)
    projection_hooks = _projection_hooks(feature)
    question_hooks = tuple(dict.fromkeys((*feature.question_hooks, *_context_question_hooks(feature))))
    boundary_flags = _boundary_flags(feature)
    time_scope = "time_layer" if feature.domain == "time" or time_context.status == "ready" and feature.domain in {"wealth", "career", "relationship"} else "natal"
    activation_sources = _activation_sources(feature, time_context)
    return BaziFeatureContext(
        context_id=f"context.{feature.feature_id}",
        feature_id=feature.feature_id,
        feature_type=feature_type,
        domain=feature.domain,
        mechanism=_context_mechanism(feature),
        source_rule_ids=source_rule_ids,
        evidence_atoms=evidence_atoms,
        counter_evidence_atoms=_counter_evidence_atoms(feature),
        strength_score=round(float(feature.confidence or 0.0), 3),
        confidence_score=round(float(feature.confidence or 0.0), 3),
        decision_state=decision_state,
        readiness=feature.readiness,
        blockers=_blockers(feature),
        amplifiers=_amplifiers(feature, time_context),
        affected_domains=_affected_domains(feature),
        time_scope=time_scope,
        activation_sources=activation_sources,
        projection_hooks=projection_hooks,
        question_hooks=question_hooks,
        answer_hooks=feature.answer_hooks,
        boundary_flags=boundary_flags,
        trace_nodes=tuple(f"trace.feature_context.{feature.domain}.{index}" for index, _ref in enumerate(feature.evidence_refs[:3])),
    )


def _context_decision_state(feature: BaziFeature) -> str:
    if feature.readiness == "ready":
        return "confirmed"
    if feature.readiness == "boundary_ready":
        return "candidate"
    if feature.feature_id.endswith("material_not_visible"):
        return "countered"
    if feature.domain in {"useful_god", "pattern", "time"}:
        return "weak_candidate"
    return "candidate"


def _feature_type(feature: BaziFeature) -> str:
    feature_id = feature.feature_id
    if feature.domain == "time":
        return "activation"
    if "weak." in feature_id or feature_id.endswith("material_not_visible"):
        return "constraint"
    if "prominent." in feature_id or "visible" in feature_id or "hidden" in feature_id:
        return "material"
    if feature.domain in {"strength", "useful_god"}:
        return "capacity"
    if feature.domain in {"branch", "pattern"}:
        return "mechanism"
    if feature.domain == "wealth":
        return "projection"
    return "mechanism"


def _context_mechanism(feature: BaziFeature) -> str:
    if feature.domain == "strength":
        return "day_master_capacity_and_load"
    if feature.domain == "wealth":
        if feature.feature_id.endswith("visible_material"):
            return "wealth_material_visible_then_capacity_gate"
        if feature.feature_id.endswith("hidden_material"):
            return "wealth_material_hidden_then_activation_gate"
        return "wealth_material_gap_then_alternative_path_review"
    if feature.domain == "ten_god":
        return "ten_god_visibility_and_role_distribution"
    if feature.domain == "element":
        return "element_distribution_pressure_and_balance"
    if feature.domain == "branch":
        return "branch_relation_trigger_and_interaction"
    if feature.domain == "time":
        return "luck_flow_activation_against_natal_chart"
    if feature.domain == "useful_god":
        return "useful_god_candidate_path_selection"
    if feature.domain == "pattern":
        return "pattern_axis_review_and_work_chain"
    return f"{feature.domain}_structural_context"


def _source_rules_for_feature(feature: BaziFeature) -> tuple[str, ...]:
    feature_id = feature.feature_id
    if feature_id.startswith("feature.strength."):
        return ("rule.strength.capacity",)
    if feature_id.startswith("feature.wealth."):
        return ("rule.wealth.material", "rule.wealth.capacity_gate")
    if feature_id.startswith("feature.ten_god."):
        return ("rule.ten_god.source_layers",)
    if feature_id.startswith("feature.element."):
        return ("rule.element.distribution", "rule.health.balance_boundary")
    if feature_id.startswith("feature.branch."):
        return ("rule.branch.relations", "rule.relationship.interaction_projection")
    if feature_id.startswith("feature.time."):
        return ("rule.time.trigger",)
    if feature_id.startswith("feature.useful_god."):
        return ("rule.useful_god.candidate_gate",)
    if feature_id.startswith("feature.pattern."):
        return ("rule.pattern.review_gate",)
    return (f"rule.{feature.domain}.structural_context",)


def _projection_hooks(feature: BaziFeature) -> tuple[str, ...]:
    hooks = {
        "strength": ("capacity_profile", "useful_god_direction", "answer_load_order"),
        "wealth": ("wealth_opportunity", "wealth_capacity", "wealth_volatility"),
        "career": ("career_role", "career_pressure", "career_expression"),
        "relationship": ("relationship_interaction", "relationship_boundary"),
        "health": ("wellbeing_pressure", "balance_boundary"),
        "ten_god": ("role_visibility", "role_interaction"),
        "element": ("element_pressure", "element_balance"),
        "branch": ("branch_trigger", "interaction_sequence"),
        "time": ("timing_trigger", "luck_flow_sequence"),
        "useful_god": ("support_release_choice", "adjustment_path"),
        "pattern": ("pattern_order", "mechanism_continuity"),
    }
    return hooks.get(feature.domain, (f"{feature.domain}_projection",))


def _context_question_hooks(feature: BaziFeature) -> tuple[str, ...]:
    if feature.domain == "wealth":
        return ("q_income_stability", "q_income_factors")
    if feature.domain == "career":
        return ("q_career_structure",)
    if feature.domain == "relationship":
        return ("q_relationship_structure",)
    if feature.domain == "health":
        return ("q_health_balance_boundary",)
    return ()


def _boundary_flags(feature: BaziFeature) -> tuple[str, ...]:
    flags = ["structural_decision_only"]
    if feature.domain in {"health", "time"}:
        flags.append("high_risk_topic_boundary")
    if feature.feature_id.endswith("material_not_visible"):
        flags.append("alternative_path_required")
    if "review" in feature.readiness:
        flags.append("low_confidence_but_directional")
    return tuple(flags)


def _counter_evidence_atoms(feature: BaziFeature) -> tuple[str, ...]:
    if feature.feature_id.endswith("material_not_visible"):
        return ("counter.wealth.no_visible_or_hidden_material",)
    if feature.feature_id.startswith("feature.element.weak."):
        return ("counter.element.weak_side_pressure",)
    if feature.readiness == "review_ready":
        return (f"counter.{feature.domain}.requires_cross_check",)
    return ()


def _blockers(feature: BaziFeature) -> tuple[str, ...]:
    if feature.feature_id.endswith("material_not_visible"):
        return ("wealth_material_absent",)
    if feature.feature_id == "feature.useful_god.evidence_gate":
        return ("useful_god_requires_capacity_path",)
    if feature.feature_id == "feature.pattern.review_index":
        return ("pattern_requires_main_axis_review",)
    return ()


def _amplifiers(feature: BaziFeature, time_context: TimeContext) -> tuple[str, ...]:
    rows: list[str] = []
    if feature.confidence >= 0.55:
        rows.append("high_feature_confidence")
    if time_context.status == "ready" and feature.domain in {"time", "wealth", "career", "relationship", "branch"}:
        rows.append("explicit_luck_flow_context")
    if len(feature.evidence_refs) >= 4:
        rows.append("multi_evidence_support")
    return tuple(rows)


def _affected_domains(feature: BaziFeature) -> tuple[str, ...]:
    mapping = {
        "strength": ("strength", "wealth", "career", "useful_god"),
        "ten_god": ("ten_god", "wealth", "career", "relationship"),
        "element": ("element", "health", "strength"),
        "branch": ("branch", "relationship", "time", "wealth", "career"),
        "time": ("time", "wealth", "career", "relationship"),
        "wealth": ("wealth",),
        "useful_god": ("useful_god", "strength", "wealth", "career"),
        "pattern": ("pattern", "career", "wealth"),
    }
    return mapping.get(feature.domain, (feature.domain,))


def _activation_sources(feature: BaziFeature, time_context: TimeContext) -> tuple[str, ...]:
    sources: list[str] = []
    if feature.domain == "time" and time_context.status == "ready":
        sources.extend(f"time.{row.layer_key}.{row.pillar.display}" for row in time_context.layers[:3])
    if time_context.status == "ready" and feature.domain in {"wealth", "career", "relationship", "branch"}:
        sources.append("time.explicit_context")
    return tuple(sources)


def _relation_title(hit) -> str:
    relation = RELATION_LABELS_ZH.get(hit.relation_type, hit.relation_type)
    rows = [
        f"{POSITION_LABELS_ZH.get(position, position)}{branch}"
        for position, branch in zip(hit.positions, hit.branches)
    ]
    if hit.relation_type in {"three_harmony", "three_meeting"}:
        element = ELEMENT_LABELS_ZH.get(hit.element, "")
        suffix = f"{relation}{element}" if element else relation
        return "、".join(rows) + suffix
    if len(rows) >= 2:
        return f"{rows[0]}与{rows[1]}{relation}"
    return "".join(rows) + relation
