from __future__ import annotations

from collections import defaultdict
from typing import Any

from v20.answer.measurement_policy import domain_label, feature_domains_for_applied_domain, measurement_stage
from v20.features.schema import FeatureLayer
from v20.knowledge.loader import default_knowledge_units
from v20.knowledge.rule_extraction import build_rule_extraction_report
from v20.knowledge.schema import KnowledgeRef, KnowledgeRetrievalReport, KnowledgeUnit


KNOWLEDGE_SEMANTIC_MODEL_VERSION = "v20.knowledge_semantic_model.v1"

KNOWLEDGE_PORTRAIT_LABELS_ZH = {
    "v20.core.strength_boundary": "日主强弱证据边界",
    "v20.core.branch_relation_boundary": "地支关系边界",
    "v20.core.time_layer_boundary": "时间层触发边界",
    "v20.core.wealth_material_boundary": "财星材料边界",
    "v20.applied.career_projection_boundary": "事业结构投影",
    "v20.applied.relationship_projection_boundary": "关系结构投影",
    "v20.applied.health_projection_boundary": "健康边界投影",
    "v20.core.useful_god_gate": "用神证据门槛",
    "v20.core.useful_god_candidate_paths": "用神候选路径",
    "v20.core.ten_god_boundary": "十神来源层边界",
    "v20.core.element_distribution_boundary": "五行分布边界",
    "v20.core.pattern_review_boundary": "格局审查边界",
}


def build_knowledge_semantic_model(
    feature_layer: FeatureLayer | None = None,
    knowledge_report: KnowledgeRetrievalReport | dict[str, object] | None = None,
    *,
    user_text: str = "",
    extraction_limit_per_domain: int = 2,
) -> dict[str, object]:
    units = _selected_units(knowledge_report)
    active_domains = _active_domains(feature_layer, units, user_text)
    rule_index = _rule_extraction_index(active_domains, extraction_limit_per_domain)
    domains = []
    for domain in sorted(active_domains, key=lambda item: (measurement_stage(item), domain_label(item))):
        domain_units = [unit for unit in units if unit.domain == domain]
        if not domain_units:
            domain_units = _support_units_for_applied_domain(domain, units)
        hooks = tuple(dict.fromkeys(hook for unit in domain_units for hook in unit.feature_hooks))
        questions = tuple(dict.fromkeys(hook for unit in domain_units for hook in unit.question_hooks))
        extraction = rule_index.get(domain, {})
        atom_count = int(extraction.get("atom_count", 0)) if isinstance(extraction, dict) else 0
        derived_subrule_count = int(extraction.get("derived_subrule_count", 0)) if isinstance(extraction, dict) else 0
        domains.append(
            {
                "domain": domain,
                "label": domain_label(domain),
                "measurement_stage": measurement_stage(domain),
                "knowledge_ids": tuple(unit.knowledge_id for unit in domain_units),
                "knowledge_count": len(domain_units),
                "feature_hooks": hooks,
                "question_hooks": questions,
                "retrieval_tags": tuple(dict.fromkeys(tag for unit in domain_units for tag in unit.retrieval_tags)),
                "portrait_label_candidates": _portrait_label_candidates(domain, domain_units, hooks),
                "interaction_keywords": _interaction_keywords(domain, domain_units),
                "boundary_summary": _boundary_summary(domain_units),
                "rule_atom_count": atom_count,
                "derived_subrule_count": derived_subrule_count,
                "rule_extraction_status": extraction.get("status", "not_requested") if isinstance(extraction, dict) else "not_requested",
                "semantic_weight": _semantic_weight(len(domain_units), len(hooks), atom_count, derived_subrule_count),
                "runtime_mutation": False,
            }
        )
    interaction_domains = _domains_from_text(user_text, domains)
    return {
        "version": KNOWLEDGE_SEMANTIC_MODEL_VERSION,
        "status": "ready" if domains else "empty",
        "model_role": "knowledge_to_feature_rule_portrait_interaction_semantic_index",
        "source_authority": "reviewed_bazi_knowledge_base",
        "domain_models": domains,
        "interaction_index": {
            "user_text_present": bool(user_text.strip()),
            "matched_domains": interaction_domains,
            "routeable_question_hooks": tuple(
                dict.fromkeys(
                    hook
                    for row in domains
                    if row["domain"] in interaction_domains
                    for hook in row["question_hooks"]
                )
            ),
            "runtime_mutation": False,
        },
        "llm_lane": {
            "role": "structured_semantic_draft_only",
            "allowed_tasks": [
                "extract_rule_atoms_from_reviewed_knowledge",
                "draft_portrait_sub_axis_labels",
                "summarize_interaction_keywords",
                "suggest_missing_boundary_terms",
            ],
            "forbidden_tasks": [
                "create_chart_facts",
                "activate_rule_truth",
                "generate_fortune_verdict",
                "replace_reviewed_knowledge",
            ],
            "fallback": "deterministic_knowledge_semantic_model",
            "runtime_mutation": False,
        },
        "runtime_mutation": False,
        "guardrails": [
            "KNOWLEDGE_SEMANTIC_MODEL_IS_INDEX_ONLY",
            "REVIEWED_KNOWLEDGE_REMAINS_AUTHORITY",
            "LLM_DRAFTS_REQUIRE_VALIDATION",
            "NO_RUNTIME_RULE_ACTIVATION",
        ],
    }


def validate_knowledge_semantic_model(model: dict[str, object]) -> dict[str, object]:
    failures: list[str] = []
    if model.get("version") != KNOWLEDGE_SEMANTIC_MODEL_VERSION:
        failures.append("version_mismatch")
    if model.get("source_authority") != "reviewed_bazi_knowledge_base":
        failures.append("source_authority_must_be_reviewed_knowledge")
    if model.get("runtime_mutation") is not False:
        failures.append("runtime_mutation_must_be_false")
    for row in model.get("domain_models", ()):
        if not isinstance(row, dict):
            failures.append("malformed_domain_model")
            continue
        domain = str(row.get("domain", ""))
        if not row.get("knowledge_ids"):
            failures.append(f"missing_knowledge_ids:{domain}")
        if not row.get("feature_hooks"):
            failures.append(f"missing_feature_hooks:{domain}")
        if float(row.get("semantic_weight", 1.0)) > 0.08:
            failures.append(f"semantic_weight_too_high:{domain}")
    return {
        "version": "v20.knowledge_semantic_model_validation.v1",
        "status": "pass" if not failures else "fail",
        "ok": not failures,
        "domain_count": len([row for row in model.get("domain_models", ()) if isinstance(row, dict)]),
        "failures": failures,
        "runtime_mutation": False,
        "guardrails": [
            "VALIDATION_ONLY",
            "SEMANTIC_MODEL_IS_SHADOW_INDEX",
            "NO_RUNTIME_MUTATION",
        ],
    }


def _selected_units(report: KnowledgeRetrievalReport | dict[str, object] | None) -> tuple[KnowledgeUnit, ...]:
    all_units = default_knowledge_units()
    if report is None:
        return all_units
    ids = _knowledge_ids(report)
    if not ids:
        return all_units
    selected = tuple(unit for unit in all_units if unit.knowledge_id in ids)
    return selected or all_units


def _knowledge_ids(report: KnowledgeRetrievalReport | dict[str, object]) -> set[str]:
    if isinstance(report, KnowledgeRetrievalReport):
        return {ref.knowledge_id for ref in report.refs}
    refs = report.get("refs", ()) if isinstance(report, dict) else ()
    ids = set()
    for ref in refs:
        if isinstance(ref, KnowledgeRef):
            ids.add(ref.knowledge_id)
        elif isinstance(ref, dict) and ref.get("knowledge_id"):
            ids.add(str(ref["knowledge_id"]))
    return ids


def _active_domains(feature_layer: FeatureLayer | None, units: tuple[KnowledgeUnit, ...], user_text: str) -> set[str]:
    domains = {unit.domain for unit in units}
    if feature_layer is not None:
        domains.update(feature.domain for feature in feature_layer.features)
    domains.update(_static_domains_from_text(user_text))
    for domain in list(domains):
        domains.update(
            applied_domain
            for applied_domain in ("wealth", "career", "relationship", "health")
            if domain in feature_domains_for_applied_domain(applied_domain)
        )
    return {domain for domain in domains if domain}


def _support_units_for_applied_domain(domain: str, units: tuple[KnowledgeUnit, ...]) -> list[KnowledgeUnit]:
    source_domains = set(feature_domains_for_applied_domain(domain))
    return [unit for unit in units if unit.domain in source_domains]


def _rule_extraction_index(domains: set[str], limit: int) -> dict[str, dict[str, object]]:
    rows: dict[str, dict[str, object]] = {}
    for domain in sorted(domains):
        report = build_rule_extraction_report(domain, limit=limit)
        rows[domain] = {
            "status": report["status"],
            "candidate_count": report["candidate_count"],
            "atom_count": report["atom_count"],
            "derived_subrule_count": report["derived_subrule_count"],
        }
    return rows


def _portrait_label_candidates(domain: str, units: list[KnowledgeUnit], hooks: tuple[str, ...]) -> tuple[dict[str, object], ...]:
    rows = []
    if not units:
        rows.append(_portrait_candidate(domain, f"{domain_label(domain)}结构轴", hooks))
        return tuple(rows)
    for index, unit in enumerate(units[:4]):
        rows.append(
            _portrait_candidate(
                domain,
                _label_from_unit(unit),
                unit.feature_hooks or hooks,
                source_knowledge_id=unit.knowledge_id,
                index=index,
            )
        )
    return tuple(rows)


def _portrait_candidate(
    domain: str,
    label: str,
    hooks: tuple[str, ...],
    *,
    source_knowledge_id: str = "",
    index: int = 0,
) -> dict[str, object]:
    return {
        "candidate_id": f"v20.portrait_label.{domain}.{index:02d}",
        "label": label,
        "domain": domain,
        "source_knowledge_id": source_knowledge_id,
        "feature_hooks": hooks,
        "status": "shadow_label_candidate",
        "runtime_allowed": False,
        "guardrails": [
            "PORTRAIT_LABEL_CANDIDATE_ONLY",
            "NO_PERSONALITY_VERDICT",
            "CALIBRATION_REQUIRED_BEFORE_PROMOTION",
        ],
    }


def _interaction_keywords(domain: str, units: list[KnowledgeUnit]) -> tuple[str, ...]:
    words = {domain_label(domain), domain}
    for unit in units:
        words.update(unit.retrieval_tags)
        words.update(_keywords_from_text(unit.title))
        words.update(_keywords_from_text(unit.summary))
    return tuple(sorted(word for word in words if word))


def _boundary_summary(units: list[KnowledgeUnit]) -> str:
    boundaries = [unit.boundary for unit in units if unit.boundary]
    if not boundaries:
        return "该知识域只进入结构解释、证据边界和候选路径，不直接生成断语。"
    return "；".join(boundaries[:2])


def _semantic_weight(knowledge_count: int, hook_count: int, atom_count: int, derived_subrule_count: int) -> float:
    return round(min(0.08, knowledge_count * 0.012 + hook_count * 0.01 + atom_count * 0.002 + derived_subrule_count * 0.004), 3)


def _domains_from_text(user_text: str, domain_models: list[dict[str, object]]) -> tuple[str, ...]:
    static = set(_static_domains_from_text(user_text))
    text = user_text.lower()
    by_domain: dict[str, set[str]] = defaultdict(set)
    for row in domain_models:
        domain = str(row.get("domain", ""))
        for keyword in row.get("interaction_keywords", ()):
            if keyword and str(keyword).lower() in text:
                by_domain[domain].add(str(keyword))
    return tuple(dict.fromkeys([*static, *by_domain.keys()]))


def _static_domains_from_text(user_text: str) -> tuple[str, ...]:
    text = user_text.lower()
    mapping = (
        ("wealth", ("财", "钱", "收入", "wealth", "money")),
        ("career", ("事业", "工作", "职业", "career", "job")),
        ("relationship", ("关系", "感情", "婚", "relationship", "partner")),
        ("health", ("健康", "身体", "health")),
        ("time", ("流年", "大运", "时间", "timing", "luck")),
        ("useful_god", ("用神", "喜忌", "useful")),
        ("ten_god", ("十神", "藏干", "透出", "ten god")),
        ("element", ("五行", "element")),
        ("branch", ("地支", "冲", "合", "刑", "害", "branch")),
        ("strength", ("日主", "强弱", "身强", "身弱", "strength")),
        ("pattern", ("格局", "pattern")),
    )
    return tuple(domain for domain, keywords in mapping if any(keyword in text for keyword in keywords))


def _label_from_unit(unit: KnowledgeUnit) -> str:
    if unit.knowledge_id in KNOWLEDGE_PORTRAIT_LABELS_ZH:
        return KNOWLEDGE_PORTRAIT_LABELS_ZH[unit.knowledge_id]
    title = unit.title.replace(" boundary", "").replace("Boundary", "").replace(" projection", "")
    if title:
        return title
    return f"{domain_label(unit.domain)}结构轴"


def _keywords_from_text(text: str) -> set[str]:
    cleaned = text.replace("-", " ").replace("/", " ")
    words = {part.strip(".,;:()[]{}").lower() for part in cleaned.split()}
    return {word for word in words if 2 <= len(word) <= 24}
