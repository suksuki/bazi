from __future__ import annotations

from v20.core.elements import element_distribution, strongest_elements, weakest_elements
from v20.core.schemas import ChartFacts, CoreInference, TimeContext
from v20.core.useful_god import derive_useful_god_candidates
from v20.features.boundaries import boundary_for
from v20.features.calibration import ConfidenceCalibrationPolicy, calibrate_features
from v20.features.confidence import bounded_confidence
from v20.features.hierarchy import cluster_features
from v20.features.schema import BaziFeature, EvidenceRef, FeatureLayer

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
