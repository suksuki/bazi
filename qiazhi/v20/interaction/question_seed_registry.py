from __future__ import annotations

from dataclasses import dataclass, replace

from v20.answer.measurement_policy import domain_label, feature_public_summary, measurement_stage
from v20.core.schemas import TimeContext
from v20.features.schema import BaziFeature, FeatureLayer
from v20.interaction.questions import QuestionCandidate
from v20.measurement.domain_alignment import align_question_candidate
from v20.measurement.dimensions import dimension_payload


SEED_REGISTRY_VERSION = "v20.question_seed_registry.v1"
SEED_QUESTION_STRATEGY = "seed_registry"


@dataclass(frozen=True)
class SeedQuestion:
    seed_key: str
    question_key: str
    domain: str
    intent: str
    role_targets: tuple[str, ...]
    required_signals: tuple[str, ...]
    template_zh: str
    score: float = 0.36

    def to_dict(self) -> dict[str, object]:
        return {
            "seed_key": self.seed_key,
            "question_key": self.question_key,
            "domain": self.domain,
            "intent": self.intent,
            "role_targets": self.role_targets,
            "required_signals": self.required_signals,
            "template_zh": self.template_zh,
            "score": self.score,
        }


SEED_QUESTIONS: tuple[SeedQuestion, ...] = (
    SeedQuestion(
        seed_key="seed.wealth.opportunity_pressure",
        question_key="q_income_factors",
        domain="wealth",
        intent="wealth_opportunity_pressure",
        role_targets=("guest", "user"),
        required_signals=("domain:wealth",),
        template_zh="{focus}明显时，财运机会、压力和承接力先看哪一段？",
    ),
    SeedQuestion(
        seed_key="seed.wealth.channel_capacity",
        question_key="q_income_stability",
        domain="wealth",
        intent="wealth_channel_capacity",
        role_targets=("user", "analyst"),
        required_signals=("domain:wealth", "feature_supported"),
        template_zh="{focus}参与时，财星通道和日主承接哪个更关键？",
        score=0.38,
    ),
    SeedQuestion(
        seed_key="seed.career.role_pressure",
        question_key="q_career_structure",
        domain="career",
        intent="career_role_pressure",
        role_targets=("guest", "user", "analyst"),
        required_signals=("domain:career",),
        template_zh="{focus}突出时，事业先看角色压力、表达还是缓冲？",
    ),
    SeedQuestion(
        seed_key="seed.relationship_interaction_boundary",
        question_key="q_relationship_structure",
        domain="relationship",
        intent="relationship_interaction_boundary",
        role_targets=("guest", "user"),
        required_signals=("domain:relationship",),
        template_zh="{focus}牵动时，关系里先看互动方式还是承接边界？",
    ),
    SeedQuestion(
        seed_key="seed.time.trigger_priority",
        question_key="q_time_relation_triggers",
        domain="time",
        intent="time_trigger_priority",
        role_targets=("user", "analyst", "admin"),
        required_signals=("time_context",),
        template_zh="{focus}出现时，大运、流年、流月哪个更先牵动主线？",
        score=0.39,
    ),
    SeedQuestion(
        seed_key="seed.strength.support_drain",
        question_key="q_strength_assessment",
        domain="strength",
        intent="strength_support_drain",
        role_targets=("guest", "user", "analyst"),
        required_signals=("domain:strength",),
        template_zh="{focus}成立时，日主先看支撑、泄耗还是承载？",
    ),
    SeedQuestion(
        seed_key="seed.useful_god.path_choice",
        question_key="q_useful_god_candidates",
        domain="useful_god",
        intent="useful_god_path_choice",
        role_targets=("user", "analyst"),
        required_signals=("domain:useful_god",),
        template_zh="{focus}清楚时，这个盘的用神和调节方向是什么？",
    ),
    SeedQuestion(
        seed_key="seed.branch_relation_priority",
        question_key="q_branch_relation_detail",
        domain="branch",
        intent="branch_relation_priority",
        role_targets=("user", "analyst"),
        required_signals=("domain:branch",),
        template_zh="{focus}被引动时，地支互动先分冲、合、刑、害哪条？",
    ),
    SeedQuestion(
        seed_key="seed.ten_god_visible_hidden",
        question_key="q_ten_god_focus",
        domain="ten_god",
        intent="ten_god_visible_hidden_priority",
        role_targets=("user", "analyst"),
        required_signals=("domain:ten_god",),
        template_zh="{focus}出现时，十神先看明透、藏干还是制化？",
        score=0.37,
    ),
    SeedQuestion(
        seed_key="seed.ten_god_hidden_stem",
        question_key="q_hidden_stem_role",
        domain="ten_god",
        intent="hidden_stem_role_review",
        role_targets=("analyst",),
        required_signals=("domain:ten_god",),
        template_zh="{focus}参与时，藏干里的十神线索需要先复核哪一层？",
    ),
    SeedQuestion(
        seed_key="seed.element_balance_pressure",
        question_key="q_element_balance",
        domain="element",
        intent="element_balance_pressure",
        role_targets=("guest", "user"),
        required_signals=("domain:element",),
        template_zh="{focus}明显时，五行先看偏旺、偏弱还是平衡压力？",
    ),
    SeedQuestion(
        seed_key="seed.element_support_pressure",
        question_key="q_element_support_pressure",
        domain="element",
        intent="element_support_pressure",
        role_targets=("user", "analyst"),
        required_signals=("domain:element",),
        template_zh="{focus}成势时，五行对日主是支撑更多还是压力更多？",
    ),
    SeedQuestion(
        seed_key="seed.pattern_structure_review",
        question_key="q_pattern_structure",
        domain="pattern",
        intent="pattern_structure_review",
        role_targets=("analyst", "admin"),
        required_signals=("domain:pattern",),
        template_zh="{focus}进入格局审查时，先看主轴清晰度还是做功连续性？",
        score=0.37,
    ),
    SeedQuestion(
        seed_key="seed.health_balance_boundary",
        question_key="q_health_balance_boundary",
        domain="health",
        intent="health_balance_boundary",
        role_targets=("guest", "user"),
        required_signals=("domain:health",),
        template_zh="{focus}提示健康平衡压力时，先看五行偏枯还是日主承载？",
    ),
    SeedQuestion(
        seed_key="seed.relationship_branch_tengod",
        question_key="q_relationship_structure",
        domain="relationship",
        intent="relationship_branch_tengod",
        role_targets=("user", "analyst"),
        required_signals=("domain:relationship",),
        template_zh="{focus}牵动关系时，先看十神角色还是地支互动？",
        score=0.37,
    ),
    SeedQuestion(
        seed_key="seed.career_output_authority_resource",
        question_key="q_career_structure",
        domain="career",
        intent="career_output_authority_resource",
        role_targets=("user", "analyst"),
        required_signals=("domain:career",),
        template_zh="{focus}影响事业时，食伤表达、官杀规则和印星缓冲谁更先？",
        score=0.38,
    ),
    SeedQuestion(
        seed_key="seed.wealth_competition_resource",
        question_key="q_income_factors",
        domain="wealth",
        intent="wealth_competition_resource",
        role_targets=("user", "analyst"),
        required_signals=("domain:wealth",),
        template_zh="{focus}进入财运判断时，先看财星机会、比劫竞争还是印星支撑？",
        score=0.37,
    ),
    SeedQuestion(
        seed_key="seed.time_natal_separation",
        question_key="q_time_vs_natal_relation",
        domain="branch",
        intent="time_natal_separation",
        role_targets=("user", "analyst", "admin"),
        required_signals=("domain:branch", "time_context"),
        template_zh="{focus}遇到时间层时，原局地支和岁运触发需要怎样分开看？",
        score=0.38,
    ),
    SeedQuestion(
        seed_key="seed.time_domain_trigger",
        question_key="q_time_layer_context",
        domain="time",
        intent="time_domain_trigger",
        role_targets=("guest", "user"),
        required_signals=("time_context",),
        template_zh="{focus}参与时，时间层先牵动事业、财运还是关系？",
        score=0.37,
    ),
    SeedQuestion(
        seed_key="seed.useful_god_evidence_gap",
        question_key="q_useful_god_evidence_gaps",
        domain="useful_god",
        intent="useful_god_evidence_gap",
        role_targets=("analyst",),
        required_signals=("domain:useful_god",),
        template_zh="{focus}进入用神候选时，证据、反证和取舍边界分别在哪里？",
        score=0.37,
    ),
)


def question_seed_registry_manifest() -> dict[str, object]:
    return {
        "version": SEED_REGISTRY_VERSION,
        "seed_count": len(SEED_QUESTIONS),
        "seeds": [row.to_dict() for row in SEED_QUESTIONS],
        "runtime_mutation": False,
        "guardrails": [
            "SEED_QUESTIONS_ARE_CANDIDATES_ONLY",
            "SEED_QUESTIONS_REQUIRE_BAZI_SIGNAL_MATCH",
            "SEED_QUESTIONS_DO_NOT_OVERRIDE_MAINLINE_RANKING",
            "NO_RAW_WEB_TEXT_IN_SEED_REGISTRY",
        ],
    }


def build_seed_question_candidates(
    decision_report: dict[str, object],
    feature_layer: FeatureLayer,
    *,
    time_context: TimeContext | None = None,
    limit: int = 6,
) -> tuple[QuestionCandidate, ...]:
    context = time_context or TimeContext()
    rows: list[QuestionCandidate] = []
    active_domains = _active_domains(decision_report, feature_layer, context)
    for seed in SEED_QUESTIONS:
        if not _seed_matches(seed, active_domains, context):
            continue
        features = _domain_features(feature_layer, seed.domain)
        if not features:
            continue
        focus = _focus_label(seed.domain, features, decision_report)
        title = seed.template_zh.format(focus=focus)
        candidate = QuestionCandidate(
            question_key=seed.question_key,
            title=title,
            domain=seed.domain,
            score=round(seed.score + _domain_strength(seed.domain, features, decision_report), 3),
            source_feature_ids=tuple(feature.feature_id for feature in features[:3]),
            boundary=_seed_boundary(seed.domain),
            measurement_topic=domain_label(seed.domain),
            measurement_stage=measurement_stage(seed.domain),
            **dimension_payload(seed.domain),
            role="seed_question_registry",
            source_decision_key=seed.seed_key,
            source_decision_status="candidate",
            source_decision_label=seed.intent,
            question_strategy=SEED_QUESTION_STRATEGY,
        )
        aligned = _aligned(candidate)
        if aligned is not None:
            rows.append(aligned)
    return tuple(sorted(rows, key=lambda row: row.score, reverse=True)[:limit])


def _aligned(candidate: QuestionCandidate) -> QuestionCandidate | None:
    alignment = align_question_candidate(
        question_key=candidate.question_key,
        domain=candidate.domain,
        title=candidate.title,
        source_feature_ids=candidate.source_feature_ids,
        boundary=candidate.boundary,
    )
    if not alignment.ok:
        return None
    return replace(
        candidate,
        alignment_status=alignment.status,
        bazi_focus=alignment.focus,
        alignment_score=alignment.score,
    )


def _seed_matches(seed: SeedQuestion, active_domains: set[str], time_context: TimeContext) -> bool:
    for signal in seed.required_signals:
        if signal.startswith("domain:") and signal.split(":", 1)[1] not in active_domains:
            return False
        if signal == "time_context" and not _has_time_context(time_context):
            return False
        if signal == "feature_supported" and seed.domain not in active_domains:
            return False
    return True


def _active_domains(decision_report: dict[str, object], feature_layer: FeatureLayer, time_context: TimeContext) -> set[str]:
    domains = {str(feature.domain) for feature in feature_layer.features if str(feature.domain)}
    domains.update(str(row.get("domain", "")) for row in decision_report.get("decisions", ()) if isinstance(row, dict))
    domains.update(str(row.get("domain", "")) for row in decision_report.get("mainlines", ()) if isinstance(row, dict))
    if _has_time_context(time_context):
        domains.add("time")
    return {domain for domain in domains if domain}


def _domain_features(feature_layer: FeatureLayer, domain: str) -> tuple[BaziFeature, ...]:
    direct = tuple(feature for feature in feature_layer.features if feature.domain == domain)
    if direct:
        return direct
    if domain == "career":
        return tuple(feature for feature in feature_layer.features if feature.domain in {"ten_god", "pattern", "strength", "branch"})
    if domain == "relationship":
        return tuple(feature for feature in feature_layer.features if feature.domain in {"ten_god", "branch"})
    if domain == "health":
        return tuple(feature for feature in feature_layer.features if feature.domain in {"element", "strength"})
    return ()


def _focus_label(domain: str, features: tuple[BaziFeature, ...], decision_report: dict[str, object]) -> str:
    for row in decision_report.get("decisions", ()):
        if isinstance(row, dict) and str(row.get("domain", "")) == domain:
            label = str(row.get("label", "")).strip()
            if label:
                return label
    for feature in features:
        summary = feature_public_summary(feature)
        if summary:
            return summary
        if feature.title:
            return feature.title
    return domain_label(domain)


def _domain_strength(domain: str, features: tuple[BaziFeature, ...], decision_report: dict[str, object]) -> float:
    feature_score = max((float(feature.confidence or 0.0) for feature in features), default=0.0) * 0.12
    decision_score = 0.0
    for row in decision_report.get("decisions", ()):
        if isinstance(row, dict) and str(row.get("domain", "")) == domain:
            decision_score = max(decision_score, float(row.get("score", 0.0)) * 0.08)
    return min(0.18, feature_score + decision_score)


def _has_time_context(time_context: TimeContext) -> bool:
    return bool(time_context.layers or time_context.relation_hits or time_context.status == "provided")


def _seed_boundary(domain: str) -> str:
    if domain == "wealth":
        return "只作为财星结构、承接力和路径问题候选，不直接判断收益结果。"
    if domain == "career":
        return "只作为事业结构问题候选，不直接判断职位升降。"
    if domain == "relationship":
        return "只作为关系结构问题候选，不直接判断关系事件。"
    if domain == "time":
        return "只作为时间层触发问题候选，不直接判断具体事件。"
    return "只作为八字结构问题候选，不直接生成结论。"
