from __future__ import annotations

from v20.core.schemas import ChartFacts, CoreInference, TimeContext
from v20.decision.schema import (
    DecisionReport,
    DynamicPortrait,
    DynamicPortraitTag,
    PractitionerControl,
    RuleDecision,
    RuleHit,
)
from v20.features.schema import FeatureLayer

DECISION_REPORT_VERSION = "v20.decision_report.v1"
DYNAMIC_PORTRAIT_VERSION = "v20.dynamic_portrait.v1"


def build_decision_report(
    facts: ChartFacts,
    core: CoreInference,
    feature_layer: FeatureLayer,
    time_context: TimeContext | None = None,
) -> dict[str, object]:
    hits = _build_hits(facts, core, feature_layer, time_context or TimeContext())
    decisions = _build_decisions(hits, facts, core)
    controls = _practitioner_controls(decisions)
    portrait = _dynamic_portrait(decisions)
    report = DecisionReport(
        version=DECISION_REPORT_VERSION,
        status="ready" if decisions else "empty",
        hits=tuple(hits),
        decisions=tuple(decisions),
        dynamic_portrait=portrait,
        practitioner_controls=tuple(controls),
    )
    return report.to_dict()


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
            evidence=(f"扶助分 {core.support_score}", f"压力分 {core.pressure_score}"),
            feature_ids=feature_ids_by_domain.get("strength", ()),
        )
    ]
    wealth_labels = _labels_present(labels, {"正财", "偏财"})
    element_features = [feature for feature in feature_layer.features if feature.domain == "element"]
    useful_god_features = [feature for feature in feature_layer.features if feature.domain == "useful_god"]
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
    hits.append(
        RuleHit(
            rule_key="rule.wealth.material",
            label="财星材料",
            domain="wealth",
            status="hit" if wealth_labels else "not_visible",
            score=0.68 if wealth_labels else 0.32,
            evidence=tuple(f"{row.label}@{_position_label(row.pillar)}{_layer_label(row.layer)}" for row in wealth_labels[:6])
            or ("原局明透与藏干未直接见财星",),
            missing_evidence=() if wealth_labels else ("财星入口需要从十神链条和大运流年旁路复核",),
            feature_ids=feature_ids_by_domain.get("wealth", ()),
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
    hits.append(_ten_god_pair_hit(
        labels,
        feature_ids_by_domain,
        rule_key="rule.ten_god.output_to_wealth",
        label="食伤生财",
        domain="wealth",
        left=("食神", "伤官"),
        right=("正财", "偏财"),
    ))
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
    if "wealth" in {row.domain for row in hits} and core.day_master_capacity != "supported_capacity" and wealth_labels:
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
                    feature_ids=hit.feature_ids,
                    portrait_tags=(_strength_label(core.day_master_capacity),),
                    question_seeds=("先看日主承载力，再决定财官食伤能不能展开。",),
                    practitioner_control_keys=("control.day_master_strength",),
                )
            )
        elif hit.rule_key == "rule.wealth.material" and hit.status == "hit":
            decisions.append(_decision_from_hit(
                hit,
                label="财星入口可见",
                status="candidate",
                role="domain_material",
                portrait_tags=("财星入口可见", "财运主题需要看来源层与承载力"),
                question_seeds=("这个盘财星从哪里来，日主能不能承接？",),
            ))
        elif hit.rule_key == "rule.wealth.capacity_gate":
            decisions.append(_decision_from_hit(
                hit,
                label="财星要先过承载门槛",
                status="candidate_review",
                role="mainline_candidate",
                portrait_tags=("财星承载待裁决",),
                question_seeds=("财星能不能用，要先看日主承载还是结构通道？",),
                practitioner_control_keys=("control.wealth_capacity",),
            ))
        elif hit.rule_key == "rule.ten_god.source_layers":
            decisions.append(_decision_from_hit(
                hit,
                label="十神显隐要分层读取",
                status="ready",
                role="foundation_context",
                portrait_tags=("十神来源层需要分清",),
                question_seeds=("藏干和明透分别承担什么结构作用？",),
            ))
        elif hit.rule_key == "rule.element.distribution":
            decisions.append(_decision_from_hit(
                hit,
                label="五行分布参与扶抑判断",
                status="candidate",
                role="foundation_context",
                portrait_tags=("五行分布影响结构平衡",),
                question_seeds=("五行偏向会怎样影响日主承载和用神候选？",),
            ))
        elif hit.rule_key == "rule.useful_god.candidate_gate":
            decisions.append(_decision_from_hit(
                hit,
                label="用神只能作为候选路径",
                status="review_required",
                role="mainline_candidate",
                portrait_tags=("用神路径需要动态裁决",),
                question_seeds=("哪些用神路径可以先作为候选，而不是直接定喜忌？",),
            ))
        elif hit.rule_key == "rule.ten_god.shang_guan_jian_guan" and hit.status != "no_hit":
            weakening = _resource_weakening(facts)
            decisions.append(_decision_from_hit(
                hit,
                label="伤官见官候选",
                status="weakened_by_resource" if weakening else "candidate",
                role="mainline_candidate",
                weakening=weakening,
                portrait_tags=("表达与规则压力并见", "事业关系需看官伤互动"),
                question_seeds=("这个盘伤官见官是否成立，有没有印星化解？",),
                practitioner_control_keys=("control.shang_guan_jian_guan",),
            ))
        elif hit.rule_key == "rule.ten_god.guan_sha_mixed" and hit.status != "no_hit":
            decisions.append(_decision_from_hit(
                hit,
                label="官杀并见候选",
                status="candidate",
                role="mainline_candidate",
                portrait_tags=("官杀角色需要分清", "事业压力与规则系统并见"),
                question_seeds=("官杀并见时，事业压力和角色边界怎么分？",),
                practitioner_control_keys=("control.pattern_status",),
            ))
        elif hit.rule_key == "rule.ten_god.output_to_wealth" and hit.status != "no_hit":
            decisions.append(_decision_from_hit(
                hit,
                label="食伤生财候选",
                status="candidate",
                role="supporting_path",
                portrait_tags=("输出生财路径候选",),
                question_seeds=("食伤能不能形成生财路径？",),
            ))
        elif hit.rule_key == "rule.branch.relations" and hit.status == "hit":
            decisions.append(_decision_from_hit(
                hit,
                label="地支互动需要分层",
                status="candidate",
                role="structure_context",
                portrait_tags=("地支互动牵动结构",),
                question_seeds=("这些冲合刑害会牵动哪条命理主线？",),
            ))
        elif hit.rule_key == "rule.time.trigger":
            decisions.append(_decision_from_hit(
                hit,
                label="时间层触发候选",
                status="candidate",
                role="time_context",
                portrait_tags=("大运流年触发需要回到原局",),
                question_seeds=("时间层进入后，先触发哪条原局结构？",),
            ))
    if by_key.get("rule.wealth.material", RuleHit("", "", "", "", 0, ())).status == "not_visible":
        hit = by_key["rule.wealth.material"]
        decisions.append(_decision_from_hit(
            hit,
            label="财星入口不明显",
            status="evidence_gap",
            role="domain_boundary",
            portrait_tags=("财运主题需要旁路复核",),
            question_seeds=("财星不显时，财运主题应从哪里切入？",),
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
        weakening=weakening,
        feature_ids=hit.feature_ids,
        portrait_tags=portrait_tags,
        question_seeds=question_seeds,
        practitioner_control_keys=practitioner_control_keys,
    )


def _dynamic_portrait(decisions: list[RuleDecision]) -> DynamicPortrait:
    tags = []
    for index, decision in enumerate(decisions[:8]):
        if not decision.portrait_tags:
            continue
        label = decision.portrait_tags[0]
        tags.append(
            DynamicPortraitTag(
                tag_key=f"portrait.dynamic.{index:02d}.{decision.decision_key.rsplit('.', 1)[-1]}",
                label=label,
                domain=decision.domain,
                summary=_portrait_summary(decision),
                score=decision.score,
                source_decision_keys=(decision.decision_key,),
                question_seeds=decision.question_seeds,
            )
        )
    return DynamicPortrait(
        version=DYNAMIC_PORTRAIT_VERSION,
        status="ready" if tags else "empty",
        tags=tuple(tags),
    )


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
        for row in [*left_rows[:3], *right_rows[:3]]
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


def _resource_weakening(facts: ChartFacts) -> tuple[str, ...]:
    resources = _labels_present(_all_ten_gods(facts), {"正印", "偏印"})
    if not resources:
        return ()
    return tuple(f"{row.label}@{_position_label(row.pillar)}可作缓冲" for row in resources[:3])


def _feature_evidence(features: list[object]) -> tuple[str, ...]:
    rows: list[str] = []
    for feature in features[:4]:
        for ref in getattr(feature, "evidence_refs", ())[:2]:
            detail = getattr(ref, "title", "")
            if detail:
                rows.append(str(detail))
    if rows:
        return tuple(dict.fromkeys(rows))[:6]
    return tuple(str(getattr(feature, "title", "命理特征")) for feature in features[:3])


def _strength_score(core: CoreInference) -> float:
    return round(min(0.88, 0.42 + abs(core.support_score - core.pressure_score)), 3)


def _strength_label(capacity: str) -> str:
    return {
        "supported_capacity": "日主有扶助证据",
        "capacity_needs_support": "日主偏需扶助",
        "borderline_capacity": "日主承载接近边界",
    }.get(capacity, "日主承载待复核")


def _strength_status(capacity: str) -> str:
    return {
        "supported_capacity": "supported",
        "capacity_needs_support": "needs_support",
        "borderline_capacity": "borderline",
    }.get(capacity, "review")


def _portrait_summary(decision: RuleDecision) -> str:
    support = "、".join(decision.support[:3])
    weakening = "；削弱：" + "、".join(decision.weakening[:2]) if decision.weakening else ""
    return f"{decision.label}：{support}{weakening}。"


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
