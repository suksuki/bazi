from __future__ import annotations

from functools import lru_cache
from typing import Any

from v20.answer.measurement_policy import (
    applied_domains,
    domain_label,
    feature_domains_for_applied_domain,
    feature_label,
    feature_public_summary,
    measurement_stage,
)
from v20.features.schema import BaziFeature, FeatureLayer
from v20.interaction.question_ranker import QuestionRankingPolicy
from v20.knowledge.schema import KnowledgeRetrievalReport


FEATURE_DISCOVERY_VERSION = "v20.feature_discovery.v1"

INTERACTION_DOMAIN_KEYWORDS = (
    ("wealth", ("财", "钱", "收入", "财运", "wealth", "money", "income", "재물", "수입")),
    ("career", ("事业", "工作", "职业", "升职", "career", "work", "job", "직업", "일")),
    ("relationship", ("婚", "感情", "关系", "伴侣", "relationship", "marriage", "partner", "관계", "결혼")),
    ("health", ("健康", "身体", "平衡", "health", "body", "balance", "건강")),
    ("time", ("流年", "大运", "流月", "时间", "应期", "触发", "timing", "luck", "세운", "대운")),
    ("useful_god", ("用神", "喜忌", "扶抑", "useful", "favorable", "용신")),
    ("ten_god", ("十神", "藏干", "透出", "正官", "七杀", "食神", "ten god", "십성")),
    ("element", ("五行", "木", "火", "土", "金", "水", "element", "오행")),
    ("branch", ("冲", "合", "刑", "害", "地支", "branch", "clash", "충", "합")),
    ("strength", ("日主", "强弱", "身强", "身弱", "承载", "strength", "capacity", "강약")),
    ("pattern", ("格局", "格", "pattern", "structure", "격국")),
)


def build_feature_discovery_report(
    feature_layer: FeatureLayer,
    *,
    knowledge_report: KnowledgeRetrievalReport | dict[str, object] | None = None,
    portrait_projection: dict[str, object] | None = None,
    user_text: str = "",
    rule_candidate_ranking: dict[str, object] | None = None,
    llm_assist: dict[str, object] | None = None,
    knowledge_semantic_model: dict[str, object] | None = None,
    selected_question: object | dict[str, object] | None = None,
    limit: int = 12,
) -> dict[str, object]:
    knowledge_refs = _knowledge_refs(knowledge_report)
    portrait_axes = _portrait_axes(portrait_projection)
    rule_weights = _rule_domain_weights(rule_candidate_ranking or {})
    selected_domain = _selected_question_domain(selected_question)
    interaction_domains = _interaction_domains(user_text, llm_assist, selected_domain)
    training_signal = build_feature_discovery_training_signal(feature_layer)
    training_weights = {
        str(row.get("domain", "")): float(row.get("weight", 0.0))
        for row in training_signal.get("domain_priors", ())
        if isinstance(row, dict)
    }
    semantic_weights = _semantic_domain_weights(knowledge_semantic_model or {})

    feature_rows = _ranked_feature_rows(
        feature_layer.features,
        knowledge_refs=knowledge_refs,
        portrait_axes=portrait_axes,
        rule_weights=rule_weights,
        interaction_domains=interaction_domains,
        training_weights=training_weights,
        semantic_weights=semantic_weights,
    )
    domain_rows = _ranked_domain_rows(
        feature_rows,
        feature_layer.features,
        knowledge_refs=knowledge_refs,
        portrait_axes=portrait_axes,
        rule_weights=rule_weights,
        interaction_domains=interaction_domains,
        selected_domain=selected_domain,
        training_weights=training_weights,
        semantic_weights=semantic_weights,
    )
    question_policy = build_feature_discovery_question_policy({"domain_hypotheses": domain_rows})
    top_domains = [str(row["domain"]) for row in domain_rows[:5]]
    return {
        "version": FEATURE_DISCOVERY_VERSION,
        "status": "ready" if feature_rows else "empty",
        "mode": "feature_spine_knowledge_portrait_interaction_training_fusion",
        "ranked_features": feature_rows[:limit],
        "domain_hypotheses": domain_rows[:limit],
        "interaction_focus": {
            "user_text_present": bool(user_text.strip()),
            "selected_domain": selected_domain,
            "candidate_domains": interaction_domains,
            "top_domains": top_domains,
            "source": _interaction_source(user_text, llm_assist, selected_domain),
        },
        "training_signal": training_signal,
        "knowledge_semantic_signal": {
            "status": knowledge_semantic_model.get("status", "not_provided") if isinstance(knowledge_semantic_model, dict) else "not_provided",
            "domain_count": len(semantic_weights),
            "semantic_domains": tuple(sorted(semantic_weights)),
            "runtime_mutation": False,
        },
        "question_policy": question_policy.to_dict(),
        "next_actions": _next_actions(training_signal, domain_rows),
        "runtime_mutation": False,
        "guardrails": [
            "FEATURE_DISCOVERY_FUSES_SIGNALS_ONLY",
            "TRAINING_SIGNAL_IS_SHADOW_RANKING_PRIOR",
            "NO_CORE_FACT_MUTATION",
            "NO_RUNTIME_RULE_ACTIVATION",
            "NO_UNSUPPORTED_FORTUNE_VERDICT",
        ],
    }


def build_feature_discovery_question_policy(report: dict[str, object]) -> QuestionRankingPolicy:
    weights: dict[str, float] = {}
    for row in report.get("domain_hypotheses", ()):
        if not isinstance(row, dict):
            continue
        domain = str(row.get("domain", ""))
        score = float(row.get("discovery_score", 0.0))
        if not domain or score < 0.42:
            continue
        weights[domain] = round(min(0.09, max(0.018, (score - 0.35) * 0.12)), 3)
    return QuestionRankingPolicy(
        policy_id="v20.question_ranking.feature_discovery_shadow",
        domain_weights=weights,
        max_adjustment=0.09,
        source="feature_discovery_fusion",
        status="active_shadow" if weights else "empty",
        guardrails=(
            "FEATURE_DISCOVERY_REORDERS_ONLY",
            "NO_NEW_QUESTION_GENERATION",
            "QUESTION_CANDIDATES_REMAIN_FEATURE_BACKED",
            "TRAINED_PRIORS_REQUIRE_PROMOTION_BEFORE_STRONGER_WEIGHT",
        ),
    )


def build_feature_discovery_training_signal(feature_layer: FeatureLayer) -> dict[str, object]:
    status = _read_corpus_artifact_status()
    artifacts = _cached_corpus_training_artifacts()
    feature_ids = {feature.feature_id for feature in feature_layer.features}
    feature_domains = {feature.domain for feature in feature_layer.features}
    rule_training = artifacts.get("rule_proposal_training", {}) if isinstance(artifacts, dict) else {}
    portrait_training = artifacts.get("portrait_axis_training", {}) if isinstance(artifacts, dict) else {}
    similarity = artifacts.get("similarity_manifest", {}) if isinstance(artifacts, dict) else {}
    domain_priors = _domain_priors_from_rule_training(rule_training, feature_ids, feature_domains)
    portrait_priors = _portrait_priors_from_training(portrait_training, feature_domains, feature_ids)
    return {
        "version": "v20.feature_discovery_training_signal.v1",
        "status": "ready" if artifacts.get("status") == "ready" else str(artifacts.get("status", "not_built")),
        "run_id": artifacts.get("run_id") or status.get("run_id", ""),
        "case_count": int(
            rule_training.get("case_count")
            or portrait_training.get("case_count")
            or similarity.get("case_count")
            or status.get("case_count")
            or status.get("completed")
            or 0
        ),
        "artifact_status": status.get("status", "not_built"),
        "similarity_status": similarity.get("status", "not_built") if isinstance(similarity, dict) else "not_built",
        "cluster_count": similarity.get("cluster_count", 0) if isinstance(similarity, dict) else 0,
        "domain_priors": domain_priors[:10],
        "portrait_priors": portrait_priors[:8],
        "training_tracks": [
            "feature_discovery_domain_prior",
            "portrait_axis_prior",
            "question_ranking_shadow_policy",
            "rule_candidate_selectivity_refinement",
        ],
        "runtime_mutation": False,
        "guardrails": [
            "CORPUS_TRAINING_PRIOR_ONLY",
            "NO_DESTINY_LABEL_TRAINING",
            "NO_DIRECT_RULE_ACTIVATION",
        ],
    }


def validate_feature_discovery_report(report: dict[str, object]) -> dict[str, object]:
    failures: list[str] = []
    if report.get("version") != FEATURE_DISCOVERY_VERSION:
        failures.append("version_mismatch")
    if report.get("runtime_mutation") is not False:
        failures.append("runtime_mutation_must_be_false")
    for row in report.get("ranked_features", ()):
        if not isinstance(row, dict):
            failures.append("malformed_ranked_feature")
            continue
        score = float(row.get("discovery_score", -1))
        if score < 0 or score > 1:
            failures.append(f"feature_score_out_of_range:{row.get('feature_id', '')}")
        if "direct_verdict" in row.get("sources", ()):
            failures.append(f"forbidden_source:{row.get('feature_id', '')}")
    policy = report.get("question_policy", {})
    if not isinstance(policy, dict):
        failures.append("missing_question_policy")
    else:
        if float(policy.get("max_adjustment", 1.0)) > 0.09:
            failures.append("question_policy_adjustment_too_high")
        if policy.get("source") != "feature_discovery_fusion":
            failures.append("question_policy_source_mismatch")
    training = report.get("training_signal", {})
    if isinstance(training, dict) and training.get("runtime_mutation") is not False:
        failures.append("training_signal_runtime_mutation")
    return {
        "version": "v20.feature_discovery_validation.v1",
        "status": "pass" if not failures else "fail",
        "ok": not failures,
        "feature_count": len([row for row in report.get("ranked_features", ()) if isinstance(row, dict)]),
        "domain_count": len([row for row in report.get("domain_hypotheses", ()) if isinstance(row, dict)]),
        "failures": failures,
        "runtime_mutation": False,
        "guardrails": [
            "VALIDATION_ONLY",
            "FEATURE_DISCOVERY_REMAINS_SHADOW_RANKING",
            "NO_RUNTIME_MUTATION",
        ],
    }


def _ranked_feature_rows(
    features: tuple[BaziFeature, ...],
    *,
    knowledge_refs: list[dict[str, object]],
    portrait_axes: list[dict[str, object]],
    rule_weights: dict[str, float],
    interaction_domains: tuple[str, ...],
    training_weights: dict[str, float],
    semantic_weights: dict[str, float],
) -> list[dict[str, object]]:
    rows = []
    for feature in features:
        knowledge_count = _knowledge_count_for_domain(knowledge_refs, feature.domain)
        portrait_axis = _portrait_axis_for_domain(portrait_axes, feature.domain)
        related_interactions = _related_interaction_domains(feature.domain, interaction_domains)
        direct_interaction = feature.domain in interaction_domains
        interaction_weight = 0.0
        if direct_interaction:
            interaction_weight = 0.14
        elif related_interactions:
            interaction_weight = 0.09
        rule_weight = _rule_weight_for_feature(feature.domain, rule_weights)
        training_weight = _training_weight_for_feature(feature.domain, training_weights)
        semantic_weight = _semantic_weight_for_feature(feature.domain, semantic_weights)
        specificity_weight = _specificity_weight_for_feature(feature)
        evidence_weight = min(0.1, len(feature.evidence_refs) * 0.018)
        knowledge_weight = min(0.1, knowledge_count * 0.022)
        portrait_weight = 0.0
        if portrait_axis:
            portrait_weight = min(0.08, 0.026 + float(portrait_axis.get("peak_confidence", 0.0)) * 0.045)
        readiness_weight = 0.02 if feature.readiness == "ready" else 0.0
        score = _bounded_score(
            feature.confidence * 0.52
            + evidence_weight
            + knowledge_weight
            + portrait_weight
            + rule_weight
            + interaction_weight
            + training_weight
            + semantic_weight
            + specificity_weight
            + readiness_weight
        )
        sources = ["feature_spine"]
        if knowledge_count:
            sources.append("reviewed_knowledge")
        if portrait_axis:
            sources.append("portrait_projection")
        if rule_weight:
            sources.append("shadow_rule_candidates")
        if interaction_weight:
            sources.append("interaction_focus")
        if training_weight:
            sources.append("corpus_training_prior")
        if semantic_weight:
            sources.append("knowledge_semantic_model")
        if specificity_weight:
            sources.append("chart_specific_salience")
        rows.append(
            {
                "feature_id": feature.feature_id,
                "title": feature_label(feature),
                "domain": feature.domain,
                "domain_label": domain_label(feature.domain),
                "measurement_stage": measurement_stage(feature.domain),
                "discovery_score": score,
                "confidence": feature.confidence,
                "readiness": feature.readiness,
                "evidence_count": len(feature.evidence_refs),
                "knowledge_ref_count": knowledge_count,
                "portrait_axis_score": round(float(portrait_axis.get("peak_confidence", 0.0)), 3) if portrait_axis else 0.0,
                "rule_candidate_weight": round(rule_weight, 3),
                "interaction_weight": round(interaction_weight, 3),
                "training_weight": round(training_weight, 3),
                "semantic_weight": round(semantic_weight, 3),
                "specificity_weight": round(specificity_weight, 3),
                "related_interaction_domains": related_interactions,
                "sources": sources,
                "summary": feature_public_summary(feature) or feature.boundary,
                "reason": _feature_reason(feature, knowledge_count, direct_interaction, related_interactions, training_weight),
                "boundary": feature.boundary,
                "runtime_mutation": False,
            }
        )
    return sorted(rows, key=lambda row: (float(row["discovery_score"]), str(row["feature_id"])), reverse=True)


def _ranked_domain_rows(
    feature_rows: list[dict[str, object]],
    features: tuple[BaziFeature, ...],
    *,
    knowledge_refs: list[dict[str, object]],
    portrait_axes: list[dict[str, object]],
    rule_weights: dict[str, float],
    interaction_domains: tuple[str, ...],
    selected_domain: str,
    training_weights: dict[str, float],
    semantic_weights: dict[str, float],
) -> list[dict[str, object]]:
    domains = set(interaction_domains)
    if selected_domain:
        domains.add(selected_domain)
    domains.update(row["domain"] for row in feature_rows)
    domains.update(str(ref.get("domain", "")) for ref in knowledge_refs if ref.get("domain"))
    domains.update(str(axis.get("domain", "")) for axis in portrait_axes if axis.get("domain"))
    domains.update(rule_weights)
    domains.update(semantic_weights)
    for domain in applied_domains():
        if any(feature.domain in feature_domains_for_applied_domain(domain) for feature in features):
            domains.add(domain)

    rows = []
    for domain in sorted(domains):
        direct_features = [row for row in feature_rows if row["domain"] == domain]
        source_domains = feature_domains_for_applied_domain(domain)
        related_features = [
            row for row in feature_rows
            if row["domain"] in source_domains and row["domain"] != domain
        ]
        source_feature_rows = direct_features or related_features
        peak_feature_score = max((float(row["discovery_score"]) for row in source_feature_rows), default=0.0)
        if not direct_features and related_features:
            peak_feature_score *= 0.92
        knowledge_count = _knowledge_count_for_domain(knowledge_refs, domain)
        if not knowledge_count and not direct_features:
            knowledge_count = sum(_knowledge_count_for_domain(knowledge_refs, source) for source in source_domains)
        portrait_axis = _portrait_axis_for_domain(portrait_axes, domain)
        portrait_count = 1 if portrait_axis else 0
        if not portrait_count and not direct_features:
            portrait_count = sum(1 for axis in portrait_axes if axis.get("domain") in source_domains)
        interaction_weight = 0.18 if domain in interaction_domains else 0.0
        if not interaction_weight and any(source in interaction_domains for source in source_domains):
            interaction_weight = 0.1
        selected_weight = 0.04 if selected_domain and selected_domain == domain else 0.0
        rule_weight = rule_weights.get(domain, 0.0)
        if not rule_weight and not direct_features:
            rule_weight = max((rule_weights.get(source, 0.0) for source in source_domains), default=0.0) * 0.6
        training_weight = training_weights.get(domain, 0.0)
        if not training_weight and not direct_features:
            training_weight = max((training_weights.get(source, 0.0) for source in source_domains), default=0.0) * 0.7
        semantic_weight = semantic_weights.get(domain, 0.0)
        if not semantic_weight and not direct_features:
            semantic_weight = max((semantic_weights.get(source, 0.0) for source in source_domains), default=0.0) * 0.7
        score = _bounded_score(
            peak_feature_score * 0.58
            + min(0.13, knowledge_count * 0.024)
            + min(0.1, portrait_count * 0.034)
            + min(0.07, rule_weight)
            + min(0.055, training_weight)
            + min(0.06, semantic_weight)
            + interaction_weight
            + selected_weight
        )
        rows.append(
            {
                "domain": domain,
                "label": domain_label(domain),
                "measurement_stage": measurement_stage(domain),
                "discovery_score": score,
                "feature_count": len(direct_features),
                "related_feature_count": len(related_features) if not direct_features else 0,
                "knowledge_ref_count": knowledge_count,
                "portrait_axis_count": portrait_count,
                "rule_candidate_weight": round(rule_weight, 3),
                "training_weight": round(training_weight, 3),
                "semantic_weight": round(semantic_weight, 3),
                "interaction_match": domain in interaction_domains,
                "source_feature_ids": [str(row["feature_id"]) for row in source_feature_rows[:8]],
                "status": "active_focus" if domain in interaction_domains or domain == selected_domain else "candidate",
                "runtime_mutation": False,
            }
        )
    return sorted(rows, key=lambda row: (float(row["discovery_score"]), str(row["domain"])), reverse=True)


def _domain_priors_from_rule_training(
    rule_training: dict[str, object],
    feature_ids: set[str],
    feature_domains: set[str],
) -> list[dict[str, object]]:
    proposals = rule_training.get("proposals", ()) if isinstance(rule_training, dict) else ()
    rows = []
    for proposal in proposals:
        if not isinstance(proposal, dict):
            continue
        emits = tuple(str(row) for row in proposal.get("emits_feature_hooks", ()) if str(row))
        matched_hooks = tuple(hook for hook in emits if _hook_matches_feature_ids(hook, feature_ids))
        domain = str(proposal.get("domain", ""))
        if not matched_hooks and domain not in feature_domains and domain not in applied_domains():
            continue
        matched_ratio = len(matched_hooks) / max(1, len(emits))
        selectivity = float(proposal.get("selectivity_score", 0.0))
        support_ratio = float(proposal.get("support_ratio", 0.0))
        weight = round(min(0.055, 0.014 + matched_ratio * 0.026 + selectivity * 0.035), 3)
        rows.append(
            {
                "domain": domain,
                "label": domain_label(domain),
                "proposal_id": proposal.get("proposal_id", ""),
                "matched_hook_count": len(matched_hooks),
                "matched_hooks": matched_hooks,
                "support_count": int(proposal.get("support_count", 0)),
                "support_ratio": round(support_ratio, 6),
                "selectivity_score": round(selectivity, 4),
                "weight": weight,
                "support_quality": proposal.get("support_quality", ""),
                "next_training_action": proposal.get("next_training_action", ""),
                "runtime_allowed": False,
            }
        )
    return sorted(rows, key=lambda row: (float(row["weight"]), str(row["domain"])), reverse=True)


def _portrait_priors_from_training(
    portrait_training: dict[str, object],
    feature_domains: set[str],
    feature_ids: set[str],
) -> list[dict[str, object]]:
    models = portrait_training.get("axis_models", ()) if isinstance(portrait_training, dict) else ()
    rows = []
    for model in models:
        if not isinstance(model, dict):
            continue
        axis = str(model.get("axis", ""))
        if axis not in feature_domains:
            continue
        top_feature_ids = []
        for item in model.get("top_feature_ids", ())[:6]:
            if isinstance(item, dict) and str(item.get("value", "")) in feature_ids:
                top_feature_ids.append(item)
        rows.append(
            {
                "axis": axis,
                "label": domain_label(axis),
                "case_count": int(model.get("count", 0)),
                "global_ratio": round(float(model.get("global_ratio", 0.0)), 6),
                "diagnostic": model.get("diagnostic", ""),
                "matched_top_feature_count": len(top_feature_ids),
                "matched_top_features": top_feature_ids[:4],
                "runtime_mutation": False,
            }
        )
    return sorted(rows, key=lambda row: (row["matched_top_feature_count"], row["global_ratio"]), reverse=True)


def _knowledge_refs(report: KnowledgeRetrievalReport | dict[str, object] | None) -> list[dict[str, object]]:
    if report is None:
        return []
    if isinstance(report, KnowledgeRetrievalReport):
        return [row.to_dict() for row in report.refs]
    refs = report.get("refs", ()) if isinstance(report, dict) else ()
    return [row for row in refs if isinstance(row, dict)]


def _portrait_axes(portrait: dict[str, object] | None) -> list[dict[str, object]]:
    axes = portrait.get("axes", ()) if isinstance(portrait, dict) else ()
    return [row for row in axes if isinstance(row, dict)]


def _rule_domain_weights(report: dict[str, object]) -> dict[str, float]:
    weights: dict[str, float] = {}
    policy = report.get("policy", {})
    if isinstance(policy, dict):
        for domain, weight in (policy.get("domain_weights", {}) or {}).items():
            weights[str(domain)] = float(weight)
    for row in report.get("domain_signals", ()):
        if isinstance(row, dict):
            weights[str(row.get("domain", ""))] = max(
                weights.get(str(row.get("domain", "")), 0.0),
                float(row.get("ranking_weight", 0.0)),
            )
    return {domain: weight for domain, weight in weights.items() if domain}


def _interaction_domains(user_text: str, llm_assist: dict[str, object] | None, selected_domain: str) -> tuple[str, ...]:
    domains = list(_domains_from_text(user_text))
    if selected_domain:
        domains.append(selected_domain)
    if llm_assist:
        domains.extend(_domains_from_llm_assist(llm_assist))
    return tuple(dict.fromkeys(domain for domain in domains if domain))


def _domains_from_text(text: str) -> tuple[str, ...]:
    lower = text.lower()
    found = [
        domain
        for domain, keywords in INTERACTION_DOMAIN_KEYWORDS
        if any(keyword in lower for keyword in keywords)
    ]
    return tuple(dict.fromkeys(found))


def _domains_from_llm_assist(llm_assist: dict[str, object]) -> tuple[str, ...]:
    rows: list[str] = []
    intent = llm_assist.get("intent", {})
    if isinstance(intent, dict):
        result = intent.get("result", {})
        if isinstance(result, dict):
            rows.extend(str(domain) for domain in result.get("feature_domains", ()) if str(domain))
    proposals = llm_assist.get("feature_candidate_proposals", {})
    if isinstance(proposals, dict):
        for row in proposals.get("candidates", ()):
            if isinstance(row, dict) and row.get("domain"):
                rows.append(str(row["domain"]))
    return tuple(dict.fromkeys(rows))


def _selected_question_domain(selected_question: object | dict[str, object] | None) -> str:
    if selected_question is None:
        return ""
    if isinstance(selected_question, dict):
        return str(selected_question.get("domain", ""))
    return str(getattr(selected_question, "domain", ""))


def _interaction_source(user_text: str, llm_assist: dict[str, object] | None, selected_domain: str) -> tuple[str, ...]:
    sources = []
    if user_text.strip():
        sources.append("user_text_keyword_router")
    if selected_domain:
        sources.append("selected_question")
    if llm_assist and llm_assist.get("status") == "ready":
        sources.append("bounded_llm_assist")
    return tuple(sources)


def _knowledge_count_for_domain(refs: list[dict[str, object]], domain: str) -> int:
    return sum(1 for ref in refs if ref.get("domain") == domain and ref.get("reviewed", True))


def _portrait_axis_for_domain(axes: list[dict[str, object]], domain: str) -> dict[str, object]:
    for axis in axes:
        if axis.get("domain") == domain:
            return axis
    return {}


def _related_interaction_domains(feature_domain: str, interaction_domains: tuple[str, ...]) -> tuple[str, ...]:
    rows = [
        domain
        for domain in interaction_domains
        if feature_domain in feature_domains_for_applied_domain(domain) and feature_domain != domain
    ]
    return tuple(dict.fromkeys(rows))


def _rule_weight_for_feature(domain: str, rule_weights: dict[str, float]) -> float:
    direct = rule_weights.get(domain, 0.0)
    related = max(
        (
            weight * 0.6
            for applied_domain, weight in rule_weights.items()
            if domain in feature_domains_for_applied_domain(applied_domain)
        ),
        default=0.0,
    )
    return min(0.065, max(direct, related))


def _training_weight_for_feature(domain: str, training_weights: dict[str, float]) -> float:
    direct = training_weights.get(domain, 0.0)
    related = max(
        (
            weight * 0.7
            for applied_domain, weight in training_weights.items()
            if domain in feature_domains_for_applied_domain(applied_domain)
        ),
        default=0.0,
    )
    return min(0.055, max(direct, related))


def _semantic_domain_weights(model: dict[str, object]) -> dict[str, float]:
    rows = {}
    for row in model.get("domain_models", ()) if isinstance(model, dict) else ():
        if isinstance(row, dict) and row.get("domain"):
            rows[str(row["domain"])] = min(0.08, float(row.get("semantic_weight", 0.0)))
    return rows


def _semantic_weight_for_feature(domain: str, semantic_weights: dict[str, float]) -> float:
    direct = semantic_weights.get(domain, 0.0)
    related = max(
        (
            weight * 0.65
            for applied_domain, weight in semantic_weights.items()
            if domain in feature_domains_for_applied_domain(applied_domain)
        ),
        default=0.0,
    )
    return min(0.06, max(direct, related))


def _specificity_weight_for_feature(feature: BaziFeature) -> float:
    if feature.feature_id.startswith(
        (
            "feature.ten_god.focus.",
            "feature.element.prominent.",
            "feature.element.weak.",
            "feature.branch.relation_type.",
            "feature.time.relation_type.",
            "feature.time.ten_god.",
        )
    ):
        return min(0.07, 0.025 + len(feature.evidence_refs) * 0.012)
    if feature.feature_id in {"feature.wealth.material_available", "feature.wealth.material_not_visible"}:
        return min(0.045, 0.018 + len(feature.evidence_refs) * 0.006)
    return 0.0


def _feature_reason(
    feature: BaziFeature,
    knowledge_count: int,
    direct_interaction: bool,
    related_interactions: tuple[str, ...],
    training_weight: float,
) -> str:
    rows = [f"以“{domain_label(feature.domain)}”特征为入口"]
    if knowledge_count:
        rows.append(f"接入 {knowledge_count} 条已审知识边界")
    if direct_interaction:
        rows.append("命中本轮用户关注方向")
    elif related_interactions:
        rows.append("支撑用户关注的应用领域")
    if training_weight:
        rows.append("已读取 518K 语料训练先验")
    return "，".join(rows) + "。"


def _hook_matches_feature_ids(hook: str, feature_ids: set[str]) -> bool:
    return any(feature_id.startswith(hook) for feature_id in feature_ids)


def _next_actions(training_signal: dict[str, object], domain_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    actions = [
        {
            "action_key": "ask_top_feature_backed_question",
            "label": "优先追问排名最高的特征域",
            "target_domains": [str(row.get("domain", "")) for row in domain_rows[:3]],
            "runtime_mutation": False,
        }
    ]
    if training_signal.get("status") == "ready":
        actions.append(
            {
                "action_key": "train_shadow_ranker_from_corpus_priors",
                "label": "用 518K 训练先验继续校准问题排序",
                "target_artifacts": ["portrait_axis_training", "rule_proposal_training", "similarity_manifest"],
                "runtime_mutation": False,
            }
        )
    actions.append(
        {
            "action_key": "llm_rule_and_portrait_draft_review",
            "label": "让 LLM 只做知识规则和画像标签草案，交给验证器裁决",
            "runtime_mutation": False,
        }
    )
    return actions


def _bounded_score(value: float) -> float:
    return round(min(0.99, max(0.0, value)), 3)


@lru_cache(maxsize=1)
def _cached_corpus_training_artifacts() -> dict[str, object]:
    from v20.corpus.artifacts import read_corpus_training_artifacts

    return read_corpus_training_artifacts()


def _read_corpus_artifact_status() -> dict[str, object]:
    from v20.corpus.artifacts import read_corpus_artifact_status

    return read_corpus_artifact_status()
