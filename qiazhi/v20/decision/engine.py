from __future__ import annotations

from v20.core.schemas import ChartFacts, CoreInference, TimeContext
from v20.decision.defeasible_model import build_defeasible_decision_model
from v20.decision.schema import (
    DecisionReport,
    MainlineDecision,
    PractitionerControl,
    RuleDecision,
    RuleHit,
)
from v20.features.schema import FeatureLayer
from v20.interaction.portrait_projection import build_portrait_projection
from v20.measurement.dimensions import dimension_payload
from v20.rules.engine import build_rule_runtime_report

DECISION_REPORT_VERSION = "v20.decision_report.v1"


def build_decision_report(
    facts: ChartFacts,
    core: CoreInference,
    feature_layer: FeatureLayer,
    time_context: TimeContext | None = None,
) -> dict[str, object]:
    hits = _build_hits(facts, core, feature_layer, time_context or TimeContext())
    rule_runtime_report = build_rule_runtime_report(feature_layer)
    defeasible_model = build_defeasible_decision_model(rule_runtime_report, feature_layer)
    legacy_decisions = _build_decisions(hits, facts, core)
    rulespec_decisions = _rulespec_decisions(defeasible_model)
    decisions = _merge_decisions(legacy_decisions, rulespec_decisions)
    mainlines = _merge_mainlines(_build_mainlines(legacy_decisions), _rulespec_mainlines(defeasible_model))
    controls = _practitioner_controls(decisions)
    report = DecisionReport(
        version=DECISION_REPORT_VERSION,
        status="ready" if decisions else "empty",
        hits=tuple(hits),
        decisions=tuple(decisions),
        mainlines=tuple(mainlines),
        practitioner_controls=tuple(controls),
    )
    payload = report.to_dict()
    payload["rule_runtime_source"] = "bazi_rule_spec_engine"
    payload["legacy_decision_bridge_status"] = "compatibility_only"
    payload["rule_runtime_report"] = rule_runtime_report
    payload["defeasible_decision_model"] = defeasible_model
    payload["portrait_projection"] = build_portrait_projection(feature_layer, defeasible_model, payload)
    return payload


def _build_hits(
    facts: ChartFacts,
    core: CoreInference,
    feature_layer: FeatureLayer,
    time_context: TimeContext,
) -> list[RuleHit]:
    labels = _all_ten_gods(facts)
    feature_ids_by_domain = _feature_ids_by_domain(feature_layer)
    hits = [
        RuleHit(
            rule_key="rule.strength.capacity",
            label="日主承载力",
            domain="strength",
            status=core.day_master_capacity,
            score=_strength_score(core),
            evidence=_strength_evidence(facts, core),
            feature_ids=feature_ids_by_domain.get("strength", ()),
        )
    ]
    wealth_labels = _labels_present(labels, {"正财", "偏财"})
    visible_wealth_labels = _labels_present(facts.visible_ten_gods, {"正财", "偏财"})
    hidden_wealth_labels = _labels_present(facts.hidden_ten_gods, {"正财", "偏财"})
    peer_labels = _labels_present(labels, {"比肩", "劫财"})
    resource_labels = _labels_present(labels, {"正印", "偏印"})
    authority_labels = _labels_present(labels, {"正官", "七杀"})
    output_labels = _labels_present(labels, {"食神", "伤官"})
    element_features = [feature for feature in feature_layer.features if feature.domain == "element"]
    useful_god_features = [feature for feature in feature_layer.features if feature.domain == "useful_god"]
    pattern_features = [feature for feature in feature_layer.features if feature.domain == "pattern"]
    ten_god_features = [feature for feature in feature_layer.features if feature.domain == "ten_god"]
    if ten_god_features:
        hits.append(
            RuleHit(
                rule_key="rule.ten_god.source_layers",
                label="十神来源层",
                domain="ten_god",
                status="hit",
                score=max(feature.confidence for feature in ten_god_features[:4]),
                evidence=_feature_evidence(ten_god_features),
                feature_ids=feature_ids_by_domain.get("ten_god", ()),
            )
        )
    if element_features:
        hits.append(
            RuleHit(
                rule_key="rule.element.distribution",
                label="五行分布",
                domain="element",
                status="candidate",
                score=max(feature.confidence for feature in element_features[:4]),
                evidence=_feature_evidence(element_features),
                feature_ids=feature_ids_by_domain.get("element", ()),
            )
        )
    if useful_god_features:
        hits.append(
            RuleHit(
                rule_key="rule.useful_god.candidate_gate",
                label="用神候选门槛",
                domain="useful_god",
                status="candidate",
                score=max(feature.confidence for feature in useful_god_features[:3]),
                evidence=_feature_evidence(useful_god_features),
                feature_ids=feature_ids_by_domain.get("useful_god", ()),
            )
        )
    if pattern_features:
        hits.append(
            RuleHit(
                rule_key="rule.pattern.review_gate",
                label="格局复核门槛",
                domain="pattern",
                status="candidate",
                score=max(feature.confidence for feature in pattern_features[:3]),
                evidence=_feature_evidence(pattern_features),
                feature_ids=feature_ids_by_domain.get("pattern", ()),
            )
        )
    hits.append(
        RuleHit(
            rule_key="rule.wealth.material",
            label="财星材料",
            domain="wealth",
            status=_wealth_material_status(visible_wealth_labels, hidden_wealth_labels),
            score=_wealth_material_score(visible_wealth_labels, hidden_wealth_labels),
            evidence=tuple(f"{row.label}@{_position_label(row.pillar)}{_layer_label(row.layer)}" for row in wealth_labels[:6])
            or ("原局明透与藏干未直接见财星",),
            missing_evidence=_wealth_missing_evidence(visible_wealth_labels, hidden_wealth_labels),
            feature_ids=feature_ids_by_domain.get("wealth", ()),
        )
    )
    if visible_wealth_labels and peer_labels:
        hits.append(
            RuleHit(
                rule_key="rule.wealth.peer_competition",
                label="财星与比劫并见",
                domain="wealth",
                status="candidate",
                score=0.67,
                evidence=tuple(
                    f"{row.label}@{_position_label(row.pillar)}{_layer_label(row.layer)}"
                    for row in [*visible_wealth_labels[:3], *peer_labels[:3]]
                ),
                missing_evidence=("需继续裁决财星承载力和通道",),
                feature_ids=_merge_feature_ids(feature_ids_by_domain, ("wealth", "ten_god", "strength")),
            )
        )
    if resource_labels and (authority_labels or output_labels):
        hits.append(
            RuleHit(
                rule_key="rule.career.resource_buffer",
                label="印星缓冲路径候选",
                domain="career",
                status="buffer_candidate",
                score=0.64,
                evidence=tuple(
                    f"{row.label}@{_position_label(row.pillar)}{_layer_label(row.layer)}"
                    for row in [*resource_labels[:3], *authority_labels[:2], *output_labels[:2]]
                ),
                missing_evidence=("需继续裁决印星是否形成缓冲路径",),
                feature_ids=_merge_feature_ids(feature_ids_by_domain, ("ten_god", "career", "strength", "pattern")),
            )
        )
    hits.append(_ten_god_pair_hit(
        labels,
        feature_ids_by_domain,
        rule_key="rule.ten_god.shang_guan_jian_guan",
        label="伤官见官",
        domain="career",
        left="伤官",
        right="正官",
    ))
    hits.append(_ten_god_pair_hit(
        labels,
        feature_ids_by_domain,
        rule_key="rule.ten_god.guan_sha_mixed",
        label="官杀混杂",
        domain="career",
        left="正官",
        right="七杀",
    ))
    output_wealth_labels = tuple(
        row for row in labels
        if getattr(row, "label", "") not in {"正财", "偏财"} or getattr(row, "layer", "") == "visible"
    )
    hits.append(_ten_god_pair_hit(
        output_wealth_labels,
        feature_ids_by_domain,
        rule_key="rule.ten_god.output_to_wealth",
        label="食伤生财",
        domain="wealth",
        left=("食神", "伤官"),
        right=("正财", "偏财"),
    ))
    if output_labels and visible_wealth_labels:
        hits.append(
            RuleHit(
                rule_key="rule.wealth.output_wealth_capacity_chain",
                label="食伤生财承载链",
                domain="wealth",
                status="chain_candidate",
                score=0.685 if core.day_master_capacity != "supported_capacity" else 0.655,
                evidence=tuple(
                    [
                        *(_ten_god_public_row(row) for row in output_labels[:2]),
                        *(_ten_god_public_row(row) for row in visible_wealth_labels[:2]),
                        _strength_label(core.day_master_capacity),
                    ]
                ),
                missing_evidence=("需继续裁决输出、财星和日主承载是否成链",),
                feature_ids=_merge_feature_ids(feature_ids_by_domain, ("wealth", "ten_god", "strength", "useful_god")),
            )
        )
    if output_labels and authority_labels and resource_labels:
        hits.append(
            RuleHit(
                rule_key="rule.career.output_authority_resource_chain",
                label="官伤印三方链",
                domain="career",
                status="chain_candidate",
                score=0.675,
                evidence=tuple(
                    [
                        *(_ten_god_public_row(row) for row in output_labels[:2]),
                        *(_ten_god_public_row(row) for row in authority_labels[:2]),
                        *(_ten_god_public_row(row) for row in resource_labels[:2]),
                    ]
                ),
                missing_evidence=("需继续裁决表达、规则压力和印星缓冲谁主导",),
                feature_ids=_merge_feature_ids(feature_ids_by_domain, ("career", "ten_god", "strength", "pattern")),
            )
        )
    hits.append(
        RuleHit(
            rule_key="rule.branch.relations",
            label="地支互动",
            domain="branch",
            status="hit" if facts.relation_hits else "quiet",
            score=min(0.86, 0.42 + len(facts.relation_hits) * 0.08) if facts.relation_hits else 0.28,
            evidence=tuple(_relation_label(row) for row in facts.relation_hits[:6]) or ("原局地支关系相对安静",),
            feature_ids=feature_ids_by_domain.get("branch", ()),
        )
    )
    if facts.relation_hits:
        hits.append(
            RuleHit(
                rule_key="rule.relationship.interaction_projection",
                label="关系互动投影",
                domain="relationship",
                status="candidate",
                score=min(0.74, 0.45 + len(facts.relation_hits) * 0.05),
                evidence=tuple(_relation_label(row) for row in facts.relation_hits[:4]),
                feature_ids=_merge_feature_ids(
                    feature_ids_by_domain,
                    ("branch", "ten_god", "strength"),
                ),
            )
        )
    element_pressure_features = [
        feature
        for feature in element_features
        if str(getattr(feature, "feature_id", "")).startswith(("feature.element.prominent.", "feature.element.weak."))
    ]
    if element_pressure_features:
        hits.append(
            RuleHit(
                rule_key="rule.health.balance_boundary",
                label="五行平衡边界",
                domain="health",
                status="safety_boundary",
                score=min(0.72, 0.46 + len(element_pressure_features) * 0.05),
                evidence=_feature_evidence(element_pressure_features),
                feature_ids=_merge_feature_ids(
                    feature_ids_by_domain,
                    ("element", "strength", "branch", "pattern"),
                ),
            )
        )
    if time_context.status == "ready":
        hits.append(
            RuleHit(
                rule_key="rule.time.trigger",
                label="时间层触发",
                domain="time",
                status="hit",
                score=min(0.86, 0.44 + len(time_context.relation_hits) * 0.08 + len(time_context.layers) * 0.06),
                evidence=tuple(
                    [f"{row.pillar.display}={row.ten_god.label}" for row in time_context.layers[:4]]
                    + [_relation_label(row) for row in time_context.relation_hits[:4]]
                ),
                feature_ids=feature_ids_by_domain.get("time", ()),
            )
        )
    if "wealth" in {row.domain for row in hits} and core.day_master_capacity != "supported_capacity" and visible_wealth_labels:
        hits.append(
            RuleHit(
                rule_key="rule.wealth.capacity_gate",
                label="财星承载门槛",
                domain="wealth",
                status="candidate",
                score=0.63,
                evidence=("财星可见", f"日主承载状态 {core.day_master_capacity}"),
                missing_evidence=("需继续裁决财星是否可用",),
                feature_ids=tuple(dict.fromkeys((*feature_ids_by_domain.get("wealth", ()), *feature_ids_by_domain.get("strength", ())))),
            )
        )
    return hits


def _build_decisions(hits: list[RuleHit], facts: ChartFacts, core: CoreInference) -> list[RuleDecision]:
    decisions = []
    by_key = {hit.rule_key: hit for hit in hits}
    for hit in hits:
        if hit.rule_key == "rule.strength.capacity":
            decisions.append(
                RuleDecision(
                    decision_key="decision.strength.capacity",
                    rule_key=hit.rule_key,
                    label=_strength_label(core.day_master_capacity),
                    domain="strength",
                    status=_strength_status(core.day_master_capacity),
                    role="foundation",
                    score=hit.score,
                    support=hit.evidence,
                    **dimension_payload("strength"),
                    feature_ids=hit.feature_ids,
                    portrait_tags=(_strength_portrait_tag(core.day_master_capacity),),
                    question_seeds=(_strength_question(core.day_master_capacity),),
                    practitioner_control_keys=("control.day_master_strength",),
                )
            )
        elif hit.rule_key == "rule.wealth.material" and hit.status == "hit":
            decisions.append(_decision_from_hit(
                hit,
                label="财星线索可见",
                status="candidate",
                role="domain_material",
                portrait_tags=("财星线索可见", "财运要看来源与承受力"),
                question_seeds=("财运主要从哪些位置和十神线索看？",),
            ))
        elif hit.rule_key == "rule.wealth.material" and hit.status == "hidden_only":
            decisions.append(_decision_from_hit(
                hit,
                label="财星藏于地支需先辨明暗",
                status="hidden_material_review",
                role="domain_boundary",
                portrait_tags=("财星藏干只作潜在线索",),
                question_seeds=("藏干里的财星，要先看能不能透出或被引动吗？",),
            ))
        elif hit.rule_key == "rule.wealth.capacity_gate":
            decisions.append(_decision_from_hit(
                hit,
                label=_wealth_capacity_label(core.day_master_capacity),
                status="candidate_review",
                role="mainline_candidate",
                portrait_tags=(_wealth_capacity_portrait_tag(core.day_master_capacity),),
                question_seeds=("财星可见时，先看日主能不能承接吗？",),
                practitioner_control_keys=("control.wealth_capacity",),
            ))
        elif hit.rule_key == "rule.wealth.peer_competition":
            decisions.append(_decision_from_hit(
                hit,
                label="财星与比劫需要一起裁决",
                status="candidate_review",
                role="mainline_candidate",
                portrait_tags=("财运需看竞争与承载",),
                question_seeds=("财运上先看机会，还是先看比劫竞争和承载力？",),
                practitioner_control_keys=("control.wealth_capacity",),
            ))
        elif hit.rule_key == "rule.career.resource_buffer":
            decisions.append(_decision_from_hit(
                hit,
                label="印星缓冲事业压力候选",
                status="candidate_review",
                role="mainline_candidate",
                portrait_tags=("事业压力可看印星缓冲", "印星学习与规则适应路径"),
                question_seeds=("事业压力中，印星是在缓冲、学习路径，还是只是候选线索？",),
                practitioner_control_keys=("control.shang_guan_jian_guan",),
            ))
        elif hit.rule_key == "rule.ten_god.source_layers":
            decisions.append(_decision_from_hit(
                hit,
                label="明透和藏干要分开看",
                status="ready",
                role="foundation_context",
                portrait_tags=("明透藏干要分开看",),
                question_seeds=("明透和藏干里，哪些十神最值得先看？",),
            ))
        elif hit.rule_key == "rule.element.distribution":
            decisions.append(_decision_from_hit(
                hit,
                label="五行分布参与扶抑判断",
                status="candidate",
                role="foundation_context",
                portrait_tags=("五行偏向影响整体平衡",),
                question_seeds=("五行偏向会让这个盘更需要哪种平衡？",),
            ))
        elif hit.rule_key == "rule.useful_god.candidate_gate":
            decisions.append(_decision_from_hit(
                hit,
                label=_useful_god_label(hit.evidence),
                status="review_required",
                role="mainline_candidate",
                portrait_tags=(_useful_god_portrait_tag(hit.evidence),),
                question_seeds=(_useful_god_question(hit.evidence),),
            ))
        elif hit.rule_key == "rule.pattern.review_gate":
            decisions.append(_decision_from_hit(
                hit,
                label=_pattern_label(hit.evidence),
                status="review_required",
                role="mainline_candidate",
                portrait_tags=(_pattern_portrait_tag(hit.evidence),),
                question_seeds=(_pattern_question(hit.evidence),),
                practitioner_control_keys=("control.pattern_status",),
            ))
        elif hit.rule_key == "rule.ten_god.shang_guan_jian_guan" and hit.status != "no_hit":
            weakening = _resource_weakening(facts)
            decisions.append(_decision_from_hit(
                hit,
                label="伤官见官见印缓冲" if weakening else "伤官见官候选",
                status="weakened_by_resource" if weakening else "candidate",
                role="mainline_candidate",
                weakening=weakening,
                portrait_tags=(
                    "表达冲规则但见印星缓冲" if weakening else "表达力与规则压力并见",
                    "事业需看官伤印三方裁决",
                ),
                question_seeds=("伤官见官是否被印星缓冲？",),
                practitioner_control_keys=("control.shang_guan_jian_guan",),
            ))
        elif hit.rule_key == "rule.ten_god.guan_sha_mixed" and hit.status != "no_hit":
            decisions.append(_decision_from_hit(
                hit,
                label="官杀混杂需分清压力来源",
                status="candidate",
                role="mainline_candidate",
                portrait_tags=("事业压力来源需要分清", "事业压力与规则系统并见"),
                question_seeds=("事业压力来自规则、竞争，还是角色混杂？",),
                practitioner_control_keys=("control.pattern_status",),
            ))
        elif hit.rule_key == "rule.ten_god.output_to_wealth" and hit.status != "no_hit":
            decisions.append(_decision_from_hit(
                hit,
                label="食伤生财通道候选",
                status="candidate",
                role="supporting_path",
                portrait_tags=("才华输出有转财线索", "财运需看输出能否形成通道"),
                question_seeds=("才华输出能不能转成财运机会？",),
            ))
        elif hit.rule_key == "rule.wealth.output_wealth_capacity_chain":
            decisions.append(_decision_from_hit(
                hit,
                label=_output_wealth_capacity_label(core.day_master_capacity),
                status="chain_review",
                role="mainline_candidate",
                portrait_tags=(_output_wealth_capacity_portrait_tag(core.day_master_capacity),),
                question_seeds=(_output_wealth_capacity_question(core.day_master_capacity),),
                practitioner_control_keys=("control.wealth_capacity",),
            ))
        elif hit.rule_key == "rule.career.output_authority_resource_chain":
            decisions.append(_decision_from_hit(
                hit,
                label="官伤印三方需要合参",
                status="chain_review",
                role="mainline_candidate",
                portrait_tags=("事业需裁决官伤印主次",),
                question_seeds=("事业上官星、伤官和印星谁是主导？",),
                practitioner_control_keys=("control.shang_guan_jian_guan", "control.pattern_status"),
            ))
        elif hit.rule_key == "rule.branch.relations" and hit.status == "hit":
            decisions.append(_decision_from_hit(
                hit,
                label="地支互动需要分层",
                status="candidate",
                role="structure_context",
                portrait_tags=("地支互动会牵动主线",),
                question_seeds=("地支冲合刑害会先影响哪一类事情？",),
            ))
        elif hit.rule_key == "rule.relationship.interaction_projection":
            decisions.append(_decision_from_hit(
                hit,
                label="关系先看互动与承接",
                status="candidate",
                role="applied_projection",
                portrait_tags=("关系先看互动与承接",),
                question_seeds=("关系结构里更明显的是互动、约束还是承接？",),
            ))
        elif hit.rule_key == "rule.health.balance_boundary":
            decisions.append(_decision_from_hit(
                hit,
                label="五行平衡只作命理边界",
                status="safety_boundary",
                role="applied_boundary",
                portrait_tags=("五行平衡与压力边界",),
                question_seeds=("五行偏枯主要提示哪种平衡压力？",),
            ))
        elif hit.rule_key == "rule.time.trigger":
            decisions.append(_decision_from_hit(
                hit,
                label="大运流年正在参与判断",
                status="candidate",
                role="time_context",
                portrait_tags=("大运流年要回到原局看",),
                question_seeds=("流年大运会先牵动事业、财运还是关系？",),
            ))
    if by_key.get("rule.wealth.material", RuleHit("", "", "", "", 0, ())).status == "not_visible":
        hit = by_key["rule.wealth.material"]
        decisions.append(_decision_from_hit(
                hit,
                label="财星线索不明显",
            status="evidence_gap",
            role="domain_boundary",
            portrait_tags=("财运需从间接线索看",),
            question_seeds=("财星不明显时，财运该从哪条线索切入？",),
        ))
    return sorted(decisions, key=lambda row: (row.role == "mainline_candidate", row.score), reverse=True)


def _decision_from_hit(
    hit: RuleHit,
    *,
    label: str,
    status: str,
    role: str,
    portrait_tags: tuple[str, ...],
    question_seeds: tuple[str, ...],
    weakening: tuple[str, ...] = (),
    practitioner_control_keys: tuple[str, ...] = (),
) -> RuleDecision:
    return RuleDecision(
        decision_key=hit.rule_key.replace("rule.", "decision."),
        rule_key=hit.rule_key,
        label=label,
        domain=hit.domain,
        status=status,
        role=role,
        score=hit.score,
        support=hit.evidence,
        **dimension_payload(hit.domain),
        weakening=weakening,
        feature_ids=hit.feature_ids,
        portrait_tags=portrait_tags,
        question_seeds=question_seeds,
        practitioner_control_keys=practitioner_control_keys,
    )


def _rulespec_decisions(defeasible_model: dict[str, object]) -> list[RuleDecision]:
    rows: list[RuleDecision] = []
    for candidate in defeasible_model.get("rule_decision_candidates", ()):
        if not isinstance(candidate, dict):
            continue
        rows.append(
            RuleDecision(
                decision_key=str(candidate.get("decision_key", "")),
                rule_key=str(candidate.get("rule_key", "")),
                label=str(candidate.get("label", "")),
                domain=str(candidate.get("domain", "")),
                status=str(candidate.get("status", "")),
                role=str(candidate.get("role", "")),
                score=float(candidate.get("score", 0.0) or 0.0),
                support=tuple(str(row) for row in candidate.get("support", ()) if str(row)),
                dimension_key=str(candidate.get("dimension_key", "")),
                dimension_layer=str(candidate.get("dimension_layer", "")),
                dimension_label=str(candidate.get("dimension_label", "")),
                weakening=tuple(str(row) for row in candidate.get("weakening", ()) if str(row)),
                feature_ids=tuple(str(row) for row in candidate.get("feature_ids", ()) if str(row)),
                portrait_tags=tuple(str(row) for row in candidate.get("portrait_tags", ()) if str(row)),
                question_seeds=tuple(str(row) for row in candidate.get("question_seeds", ()) if str(row)),
                practitioner_control_keys=tuple(
                    str(row) for row in candidate.get("practitioner_control_keys", ()) if str(row)
                ),
                guardrails=(
                    "DECISION_FROM_RULESPEC_DEFEASIBLE_MODEL",
                    "DECISION_IS_EVIDENCE_BOUNDED",
                    "LLM_MAY_EXPLAIN_NOT_DECIDE",
                ),
            )
        )
    return rows


def _merge_decisions(legacy: list[RuleDecision], rulespec: list[RuleDecision]) -> list[RuleDecision]:
    seen = {row.decision_key for row in legacy}
    additions = [row for row in rulespec if row.decision_key not in seen]
    additions.sort(key=lambda row: (row.role == "mainline_candidate", row.score), reverse=True)
    return [*legacy, *additions[:28]]


def _rulespec_mainlines(defeasible_model: dict[str, object]) -> list[MainlineDecision]:
    rows: list[MainlineDecision] = []
    for candidate in defeasible_model.get("mainline_candidates", ()):
        if not isinstance(candidate, dict):
            continue
        domain = str(candidate.get("domain", ""))
        rows.append(
            MainlineDecision(
                mainline_key=str(candidate.get("mainline_key", "")),
                title=str(candidate.get("title", "")),
                domain=domain,
                status=str(candidate.get("status", "")),
                score=float(candidate.get("score", 0.0) or 0.0),
                priority=int(candidate.get("priority", 0) or 0),
                summary=str(candidate.get("summary", "")),
                source_decision_keys=tuple(
                    str(rule_id).replace("rule.", "decision.rulespec.")
                    for rule_id in candidate.get("source_rule_ids", ())
                    if str(rule_id)
                ),
                support=tuple(str(row) for row in candidate.get("support", ()) if str(row)),
                question_seed=str(candidate.get("question_seed", "")),
                role="primary_rulespec_bazi_mainline",
                guardrails=(
                    "MAINLINE_IS_AGGREGATED_FROM_DEFEASIBLE_RULESPEC_DECISIONS",
                    "NO_NEW_FACTS_FROM_MAINLINE",
                    "MAINLINE_DRIVES_PORTRAIT_QUESTIONS_AND_ANSWER_ORDER",
                ),
            )
        )
    return rows


def _merge_mainlines(legacy: list[MainlineDecision], rulespec: list[MainlineDecision]) -> list[MainlineDecision]:
    by_key = {row.mainline_key: row for row in [*rulespec, *legacy]}
    return sorted(by_key.values(), key=lambda row: (row.priority, row.score), reverse=True)[:8]


def _build_mainlines(decisions: list[RuleDecision]) -> list[MainlineDecision]:
    by_key = {decision.decision_key: decision for decision in decisions}
    rows: list[MainlineDecision] = []
    rows.extend(_wealth_mainlines(by_key))
    rows.extend(_career_mainlines(by_key))
    rows.extend(_foundation_mainlines(by_key))
    rows.extend(_structure_mainlines(by_key))
    return sorted(rows, key=lambda row: (row.priority, row.score), reverse=True)[:6]


def _wealth_mainlines(by_key: dict[str, RuleDecision]) -> list[MainlineDecision]:
    chain = by_key.get("decision.wealth.output_wealth_capacity_chain")
    material = by_key.get("decision.wealth.material")
    capacity = by_key.get("decision.wealth.capacity_gate")
    peer = by_key.get("decision.wealth.peer_competition")
    if chain:
        linked = tuple(
            decision.decision_key
            for decision in (chain, capacity, peer, material)
            if decision is not None
        )
        return [
            MainlineDecision(
                mainline_key="mainline.wealth.output_capacity",
                title=chain.label,
                domain="wealth",
                status=chain.status,
                score=round(max(decision.score for decision in (chain, capacity or chain, peer or chain)), 3),
                priority=95,
                summary=_mainline_summary(chain, (capacity, peer, material)),
                source_decision_keys=linked,
                support=chain.support[:5],
                question_seed=chain.question_seeds[0] if chain.question_seeds else "食伤生财路径先复核哪一段？",
            )
        ]
    if material and material.status not in {"hidden_material_review", "evidence_gap"}:
        return [
            MainlineDecision(
                mainline_key="mainline.wealth.material",
                title=material.label,
                domain="wealth",
                status=material.status,
                score=material.score,
                priority=70,
                summary=_mainline_summary(material, (capacity, peer)),
                source_decision_keys=tuple(decision.decision_key for decision in (material, capacity, peer) if decision is not None),
                support=material.support[:4],
                question_seed=material.question_seeds[0] if material.question_seeds else "财运主要从哪些位置和十神线索看？",
            )
        ]
    return []


def _career_mainlines(by_key: dict[str, RuleDecision]) -> list[MainlineDecision]:
    chain = by_key.get("decision.career.output_authority_resource_chain")
    shang_guan = by_key.get("decision.ten_god.shang_guan_jian_guan")
    mixed = by_key.get("decision.ten_god.guan_sha_mixed")
    buffer = by_key.get("decision.career.resource_buffer")
    if chain:
        linked = tuple(
            decision.decision_key
            for decision in (chain, shang_guan, mixed, buffer)
            if decision is not None
        )
        return [
            MainlineDecision(
                mainline_key="mainline.career.guan_shang_yin",
                title=chain.label,
                domain="career",
                status=chain.status,
                score=round(max(decision.score for decision in (chain, shang_guan or chain, buffer or chain)), 3),
                priority=94,
                summary=_mainline_summary(chain, (shang_guan, mixed, buffer)),
                source_decision_keys=linked,
                support=chain.support[:5],
                question_seed=chain.question_seeds[0] if chain.question_seeds else "事业上官星、伤官和印星谁是主导？",
            )
        ]
    if shang_guan or buffer:
        primary = shang_guan or buffer
        assert primary is not None
        return [
            MainlineDecision(
                mainline_key="mainline.career.structure",
                title=primary.label,
                domain="career",
                status=primary.status,
                score=primary.score,
                priority=82,
                summary=_mainline_summary(primary, (mixed, buffer)),
                source_decision_keys=tuple(decision.decision_key for decision in (primary, mixed, buffer) if decision is not None),
                support=primary.support[:4],
                question_seed=primary.question_seeds[0] if primary.question_seeds else "事业结构先复核哪条线？",
            )
        ]
    return []


def _foundation_mainlines(by_key: dict[str, RuleDecision]) -> list[MainlineDecision]:
    strength = by_key.get("decision.strength.capacity")
    useful = by_key.get("decision.useful_god.candidate_gate")
    pattern = by_key.get("decision.pattern.review_gate")
    rows: list[MainlineDecision] = []
    if strength:
        rows.append(
            MainlineDecision(
                mainline_key="mainline.foundation.capacity",
                title=strength.label,
                domain="strength",
                status=strength.status,
                score=strength.score,
                priority=88,
                summary=_mainline_summary(strength, (useful, pattern)),
                source_decision_keys=tuple(decision.decision_key for decision in (strength, useful, pattern) if decision is not None),
                support=strength.support[:5],
                question_seed=strength.question_seeds[0] if strength.question_seeds else "日主强弱先复核哪类证据？",
            )
        )
    if useful:
        rows.append(
            MainlineDecision(
                mainline_key="mainline.useful_god.path",
                title=useful.label,
                domain="useful_god",
                status=useful.status,
                score=useful.score,
                priority=78,
                summary=_mainline_summary(useful, (strength, pattern)),
                source_decision_keys=tuple(decision.decision_key for decision in (useful, strength, pattern) if decision is not None),
                support=useful.support[:4],
                question_seed=useful.question_seeds[0] if useful.question_seeds else "用神方向先复核哪条路径？",
            )
        )
    return rows


def _structure_mainlines(by_key: dict[str, RuleDecision]) -> list[MainlineDecision]:
    branch = by_key.get("decision.branch.relations")
    time = by_key.get("decision.time.trigger")
    if time:
        return [
            MainlineDecision(
                mainline_key="mainline.time.trigger",
                title=time.label,
                domain="time",
                status=time.status,
                score=time.score,
                priority=84,
                summary=_mainline_summary(time, (branch,)),
                source_decision_keys=tuple(decision.decision_key for decision in (time, branch) if decision is not None),
                support=time.support[:5],
                question_seed=time.question_seeds[0] if time.question_seeds else "大运流年先牵动哪条主线？",
            )
        ]
    if branch:
        return [
            MainlineDecision(
                mainline_key="mainline.structure.branch",
                title=branch.label,
                domain="branch",
                status=branch.status,
                score=branch.score,
                priority=68,
                summary=_mainline_summary(branch, ()),
                source_decision_keys=(branch.decision_key,),
                support=branch.support[:4],
                question_seed=branch.question_seeds[0] if branch.question_seeds else "地支互动会先影响哪一类事情？",
            )
        ]
    return []


def _mainline_summary(primary: RuleDecision, related: tuple[RuleDecision | None, ...]) -> str:
    related_labels = [decision.label for decision in related if decision is not None]
    support = "、".join(_public_evidence_text(row) for row in primary.support[:3])
    if related_labels:
        return f"当前主线入口，联动{'、'.join(related_labels[:3])}；证据：{support}。"
    return f"当前主线入口；证据：{support}。"


def _practitioner_controls(decisions: list[RuleDecision]) -> list[PractitionerControl]:
    keys = {key for decision in decisions for key in decision.practitioner_control_keys}
    controls = []
    if "control.day_master_strength" in keys:
        controls.append(PractitionerControl(
            control_key="control.day_master_strength",
            label="日主强弱裁决",
            options=("偏强", "中和偏强", "中和", "中和偏弱", "偏弱", "待复核"),
            default="待复核",
            source_decision_keys=tuple(decision.decision_key for decision in decisions if "control.day_master_strength" in decision.practitioner_control_keys),
        ))
    if "control.shang_guan_jian_guan" in keys:
        controls.append(PractitionerControl(
            control_key="control.shang_guan_jian_guan",
            label="伤官见官裁决",
            options=("成立", "候选", "被印化", "被财通关", "不成立", "待复核"),
            default="候选",
            source_decision_keys=tuple(decision.decision_key for decision in decisions if "control.shang_guan_jian_guan" in decision.practitioner_control_keys),
        ))
    if "control.wealth_capacity" in keys:
        controls.append(PractitionerControl(
            control_key="control.wealth_capacity",
            label="财星承载裁决",
            options=("可承接", "需扶身", "走通关", "看大运", "证据不足"),
            default="证据不足",
            source_decision_keys=tuple(decision.decision_key for decision in decisions if "control.wealth_capacity" in decision.practitioner_control_keys),
        ))
    if "control.pattern_status" in keys:
        controls.append(PractitionerControl(
            control_key="control.pattern_status",
            label="格局/命格裁决",
            options=("成格", "破格", "候选", "不取格", "待复核"),
            default="待复核",
            source_decision_keys=tuple(decision.decision_key for decision in decisions if "control.pattern_status" in decision.practitioner_control_keys),
        ))
    return controls


def _all_ten_gods(facts: ChartFacts) -> tuple[object, ...]:
    return (*facts.visible_ten_gods, *facts.hidden_ten_gods)


def _labels_present(rows: tuple[object, ...], labels: set[str]) -> list[object]:
    return [row for row in rows if getattr(row, "label", "") in labels]


def _wealth_material_status(visible_rows: list[object], hidden_rows: list[object]) -> str:
    if visible_rows:
        return "hit"
    if hidden_rows:
        return "hidden_only"
    return "not_visible"


def _wealth_material_score(visible_rows: list[object], hidden_rows: list[object]) -> float:
    if visible_rows:
        return round(min(0.78, 0.58 + len(visible_rows[:3]) * 0.055 + _weighted_sum(hidden_rows[:4]) * 0.025), 3)
    if hidden_rows:
        return round(min(0.52, 0.34 + _weighted_sum(hidden_rows[:5]) * 0.045), 3)
    return 0.24


def _wealth_missing_evidence(visible_rows: list[object], hidden_rows: list[object]) -> tuple[str, ...]:
    if visible_rows:
        return ()
    if hidden_rows:
        return ("财星只在藏干，不直接作为财运主线，需看透出、引动或成链证据",)
    return ("财星入口需要从十神关系和大运流年旁路复核",)


def _weighted_sum(rows: list[object]) -> float:
    return round(sum(float(getattr(row, "weight", 1.0)) for row in rows), 3)


def _ten_god_pair_hit(
    labels: tuple[object, ...],
    feature_ids_by_domain: dict[str, tuple[str, ...]],
    *,
    rule_key: str,
    label: str,
    domain: str,
    left: str | tuple[str, ...],
    right: str | tuple[str, ...],
) -> RuleHit:
    left_labels = {left} if isinstance(left, str) else set(left)
    right_labels = {right} if isinstance(right, str) else set(right)
    left_rows = _labels_present(labels, left_labels)
    right_rows = _labels_present(labels, right_labels)
    evidence = tuple(
        f"{row.label}@{_position_label(row.pillar)}{_layer_label(row.layer)}"
        for row in [*left_rows[:2], *right_rows[:2]]
    )
    status = "hit" if left_rows and right_rows else "no_hit"
    score = 0.66 if status == "hit" else 0.0
    if any(row.layer == "visible" for row in left_rows) and any(row.layer == "visible" for row in right_rows):
        score += 0.08
    return RuleHit(
        rule_key=rule_key,
        label=label,
        domain=domain,
        status=status,
        score=round(min(0.88, score), 3),
        evidence=evidence,
        missing_evidence=() if status == "hit" else (f"未同时见{label}所需十神",),
        feature_ids=tuple(dict.fromkeys((*feature_ids_by_domain.get("ten_god", ()), *feature_ids_by_domain.get(domain, ())))),
    )


def _feature_ids_by_domain(feature_layer: FeatureLayer) -> dict[str, tuple[str, ...]]:
    rows: dict[str, list[str]] = {}
    for feature in feature_layer.features:
        rows.setdefault(feature.domain, []).append(feature.feature_id)
    return {domain: tuple(values) for domain, values in rows.items()}


def _merge_feature_ids(rows: dict[str, tuple[str, ...]], domains: tuple[str, ...]) -> tuple[str, ...]:
    values: list[str] = []
    for domain in domains:
        values.extend(rows.get(domain, ()))
    return tuple(dict.fromkeys(values))


def _resource_weakening(facts: ChartFacts) -> tuple[str, ...]:
    resources = _labels_present(_all_ten_gods(facts), {"正印", "偏印"})
    if not resources:
        return ()
    return tuple(f"{row.label}@{_position_label(row.pillar)}可作缓冲" for row in resources[:3])


def _strength_evidence(facts: ChartFacts, core: CoreInference) -> tuple[str, ...]:
    labels = _all_ten_gods(facts)
    support_rows = _labels_present(labels, {"比肩", "劫财", "正印", "偏印"})
    pressure_rows = _labels_present(labels, {"食神", "伤官", "正财", "偏财", "正官", "七杀"})
    evidence = [
        f"扶助分 {core.support_score}",
        f"压力分 {core.pressure_score}",
    ]
    if support_rows:
        evidence.append("扶身材料：" + "、".join(_ten_god_public_row(row) for row in support_rows[:4]))
    else:
        evidence.append("扶身材料不明显")
    if pressure_rows:
        evidence.append("泄耗克制材料：" + "、".join(_ten_god_public_row(row) for row in pressure_rows[:4]))
    else:
        evidence.append("泄耗克制材料不明显")
    if facts.relation_hits:
        evidence.append("地支互动需要纳入强弱复核")
    return tuple(evidence)


def _ten_god_public_row(row: object) -> str:
    return f"{getattr(row, 'label', '')}@{_position_label(getattr(row, 'pillar', ''))}{_layer_label(getattr(row, 'layer', ''))}"


def _feature_evidence(features: list[object]) -> tuple[str, ...]:
    rows: list[str] = []
    for feature in features[:4]:
        for ref in getattr(feature, "evidence_refs", ())[:2]:
            detail = getattr(ref, "title", "")
            if detail:
                rows.append(_public_evidence_text(str(detail)))
    if rows:
        return tuple(dict.fromkeys(rows))[:6]
    return tuple(_public_evidence_text(str(getattr(feature, "title", "命理特征"))) for feature in features[:3])


def _strength_score(core: CoreInference) -> float:
    return round(min(0.88, 0.42 + abs(core.support_score - core.pressure_score)), 3)


def _strength_label(capacity: str) -> str:
    return {
        "supported_capacity": "日主有根气与生扶支撑",
        "capacity_needs_support": "日主偏弱需扶身复核",
        "borderline_capacity": "日主强弱接近分界需裁决",
    }.get(capacity, "日主强弱待复核")


def _strength_portrait_tag(capacity: str) -> str:
    return {
        "supported_capacity": "日主有支撑可承接",
        "capacity_needs_support": "日主需先看扶身",
        "borderline_capacity": "日主强弱需先裁决",
    }.get(capacity, "日主强弱待复核")


def _strength_question(capacity: str) -> str:
    return {
        "supported_capacity": "日主有支撑后，适合先看泄秀、财星还是官杀？",
        "capacity_needs_support": "日主需要扶身时，先看印星、比劫还是通关？",
        "borderline_capacity": "日主强弱接近分界时，先比较哪类证据？",
    }.get(capacity, "这个八字日主偏强还是偏弱，适合先看什么？")


def _strength_status(capacity: str) -> str:
    return {
        "supported_capacity": "supported",
        "capacity_needs_support": "needs_support",
        "borderline_capacity": "borderline",
    }.get(capacity, "review")


def _wealth_capacity_label(capacity: str) -> str:
    return {
        "capacity_needs_support": "财星可见但日主承接需扶助",
        "borderline_capacity": "财星承载接近分界",
        "supported_capacity": "财星承载可进入复核",
    }.get(capacity, "财星承载需要复核")


def _wealth_capacity_portrait_tag(capacity: str) -> str:
    return {
        "capacity_needs_support": "财运要先看扶身与承接",
        "borderline_capacity": "财运承接力接近边界",
        "supported_capacity": "财运可进入机会与通道复核",
    }.get(capacity, "财运要先看承受力")


def _output_wealth_capacity_label(capacity: str) -> str:
    return {
        "capacity_needs_support": "食伤生财需先过承载关",
        "borderline_capacity": "食伤生财承载需裁决",
        "supported_capacity": "食伤生财可进入通道复核",
    }.get(capacity, "食伤生财路径需要复核")


def _output_wealth_capacity_portrait_tag(capacity: str) -> str:
    return {
        "capacity_needs_support": "食伤生财要先看日主承接",
        "borderline_capacity": "食伤生财承载接近分界",
        "supported_capacity": "食伤生财可看通道闭合",
    }.get(capacity, "食伤生财路径需复核")


def _output_wealth_capacity_question(capacity: str) -> str:
    return {
        "capacity_needs_support": "食伤生财时，日主承接够不够？",
        "borderline_capacity": "食伤生财要先看承载还是通道？",
        "supported_capacity": "食伤生财能否形成稳定财星通道？",
    }.get(capacity, "食伤生财路径先复核哪一段？")


def _useful_god_label(evidence: tuple[str, ...]) -> str:
    text = " ".join(evidence)
    if "support:" in text or "扶身候选" in text:
        return "用神候选先看扶身路径"
    if "release:" in text or "泄秀候选" in text:
        return "用神候选先看泄秀路径"
    if "channel:" in text or "通道候选" in text:
        return "用神候选包含财星通道"
    if "constraint:" in text or "约束候选" in text:
        return "用神候选需看官杀约束"
    if "arbitration:" in text or "用神参考" in text:
        return "用神方向需先做扶泄裁决"
    return "用神方向需要结合全局复核"


def _useful_god_portrait_tag(evidence: tuple[str, ...]) -> str:
    text = " ".join(evidence)
    if "support:" in text or "扶身候选" in text:
        return "用神方向先看扶身"
    if "release:" in text or "泄秀候选" in text:
        return "用神方向先看泄秀"
    if "channel:" in text or "通道候选" in text:
        return "用神方向包含财星通道"
    if "constraint:" in text or "约束候选" in text:
        return "用神方向需看官杀约束"
    if "arbitration:" in text or "用神参考" in text:
        return "用神方向需扶泄裁决"
    return "用神方向还需结合全局"


def _useful_god_question(evidence: tuple[str, ...]) -> str:
    text = " ".join(evidence)
    if "support:" in text or "扶身候选" in text:
        return "这个盘用神方向要先扶身，还是另有通关路径？"
    if "release:" in text or "泄秀候选" in text:
        return "这个盘用神方向适合先看泄秀还是财星通道？"
    if "channel:" in text or "通道候选" in text:
        return "这个盘用神方向能不能走财星通道？"
    if "constraint:" in text or "约束候选" in text:
        return "这个盘用神方向要不要先看官杀约束？"
    if "arbitration:" in text or "用神参考" in text:
        return "这个盘用神方向先扶身还是先泄秀？"
    return "这个盘下一步适合先找哪类用神方向？"


def _pattern_label(evidence: tuple[str, ...]) -> str:
    text = " ".join(evidence)
    if "墓库" in text or "藏气" in text:
        return "格局需先看墓库藏气"
    return "格局先从月令和十神复核"


def _pattern_portrait_tag(evidence: tuple[str, ...]) -> str:
    text = " ".join(evidence)
    if "墓库" in text or "藏气" in text:
        return "格局要先复核墓库藏气"
    return "格局需要回到月令十神"


def _pattern_question(evidence: tuple[str, ...]) -> str:
    text = " ".join(evidence)
    if "墓库" in text or "藏气" in text:
        return "格局判断要先复核哪一处墓库藏气？"
    return "格局判断要先看月令、透干还是十神组合？"


def _public_evidence_text(value: str) -> str:
    text = str(value or "")
    element = {
        "wood": "木",
        "fire": "火",
        "earth": "土",
        "metal": "金",
        "water": "水",
    }
    if text.startswith("arbitration:"):
        key = text.split(":", 1)[1]
        return f"{element.get(key, key)}方向可作为用神参考"
    if text.startswith("support:"):
        key = text.split(":", 1)[1]
        return f"{element.get(key, key)}方向可作为扶身候选"
    if text.startswith("release:"):
        key = text.split(":", 1)[1]
        return f"{element.get(key, key)}方向可作为泄秀候选"
    if text.startswith("channel:"):
        key = text.split(":", 1)[1]
        return f"{element.get(key, key)}方向可作为通道候选"
    if text.startswith("constraint:"):
        key = text.split(":", 1)[1]
        return f"{element.get(key, key)}方向可作为约束候选"
    if text.startswith("evidence_gap:"):
        key = text.split(":", 1)[1]
        return f"{element.get(key, key)}方向属于证据缺口复核"
    if text in {"supported_capacity", "capacity_needs_support", "borderline_capacity"}:
        return _strength_label(text)
    return (
        text.replace("日主承载状态 borderline_capacity", "日主强弱接近分界需裁决")
        .replace("日主承载状态 capacity_needs_support", "日主偏弱需扶身复核")
        .replace("日主承载状态 supported_capacity", "日主有根气与生扶支撑")
    )


def _position_label(value: str) -> str:
    return {
        "year": "年柱",
        "month": "月柱",
        "day": "日柱",
        "hour": "时柱",
        "luck": "大运",
        "flow_year": "流年",
        "flow_month": "流月",
    }.get(value, value)


def _layer_label(value: str) -> str:
    return {"visible": "明透", "hidden": "藏干", "time": "时间层"}.get(value, value)


def _relation_label(hit: object) -> str:
    relation = {
        "clash": "冲",
        "harmony": "合",
        "harm": "害",
        "break": "破",
        "punishment": "刑",
        "three_harmony": "三合",
        "three_meeting": "三会",
    }.get(getattr(hit, "relation_type", ""), getattr(hit, "relation_type", ""))
    positions = tuple(getattr(hit, "positions", ()))
    branches = tuple(getattr(hit, "branches", ()))
    rows = [f"{_position_label(pos)}{branch}" for pos, branch in zip(positions, branches)]
    if len(rows) >= 2:
        return f"{rows[0]}与{rows[1]}{relation}"
    return "".join(rows) + relation
