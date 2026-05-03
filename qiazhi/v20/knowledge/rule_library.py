from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any

from v20.knowledge.loader import default_knowledge_units
from v20.knowledge.rule_extraction import build_rule_extraction_report
from v20.knowledge.schema import KnowledgeUnit


@dataclass(frozen=True)
class KnowledgeRuleDefinition:
    rule_key: str
    title: str
    domain: str
    source_knowledge_id: str
    source_authority: str
    condition_atoms: tuple[dict[str, object], ...]
    portrait_outputs: tuple[dict[str, object], ...]
    question_outputs: tuple[dict[str, object], ...]
    answer_guidance: tuple[dict[str, object], ...]
    counterexamples: tuple[dict[str, object], ...]
    evidence_refs: tuple[str, ...]
    boundary: str
    bazi_alignment: dict[str, object]
    validation_state: str = "active_ready"
    activation_status: str = "active_iteration"
    runtime_allowed: bool = True
    guardrails: tuple[str, ...] = field(
        default=(
            "KNOWLEDGE_RULE_DEFINITION_FEEDS_ACTIVE_RUNTIME",
            "SYNTHETIC_VALIDATION_IS_ITERATION_SIGNAL",
            "PRACTITIONER_OR_DECISION_REVIEW_REWEIGHTS_RUNTIME",
            "TRACE_REQUIRED_FOR_USER_VISIBLE_RULE_USE",
        )
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_knowledge_rule_library(domain: str = "", *, limit: int = 0) -> dict[str, object]:
    units = _unit_index()
    extraction = build_rule_extraction_report(domain, limit=limit)
    definitions = tuple(
        _definition_from_candidate(candidate, units.get(str(candidate.get("source_knowledge_id", ""))))
        for candidate in extraction["candidates"]
        if isinstance(candidate, dict)
    )
    return {
        "version": "v20.knowledge_rule_library.v1",
        "status": "ready" if definitions else "empty",
        "domain": domain.strip(),
        "source_authority": "reviewed_bazi_knowledge_base",
        "definition_count": len(definitions),
        "atom_count": sum(len(row.condition_atoms) for row in definitions),
        "portrait_output_count": sum(len(row.portrait_outputs) for row in definitions),
        "question_output_count": sum(len(row.question_outputs) for row in definitions),
        "runtime_allowed_count": sum(1 for row in definitions if row.runtime_allowed),
        "coverage": _coverage(definitions),
        "definitions": [row.to_dict() for row in definitions],
        "upstream_extraction": {
            "version": extraction["version"],
            "candidate_count": extraction["candidate_count"],
            "derived_subrule_count": extraction["derived_subrule_count"],
            "corpus_role": extraction["corpus_role"],
            "llm_role": extraction["llm_role"],
        },
        "runtime_mutation": False,
        "guardrails": [
            "RULE_LIBRARY_IS_KNOWLEDGE_AUTHORED_ACTIVE_LAYER",
            "RULE_LIBRARY_ACTIVATES_TRACEABLE_RUNTIME_RULES",
            "CORPUS_AND_LLM_CAN_REFINE_BUT_NOT_AUTHOR_TRUTH",
        ],
    }


def validate_knowledge_rule_library(domain: str = "", *, limit: int = 0) -> dict[str, object]:
    library = build_knowledge_rule_library(domain, limit=limit)
    failures: list[str] = []
    if library["source_authority"] != "reviewed_bazi_knowledge_base":
        failures.append("source_authority_must_be_reviewed_knowledge_base")
    if library["status"] == "empty":
        failures.append("no_rule_definitions")
    if library["runtime_allowed_count"] != library["definition_count"]:
        failures.append("not_all_rules_runtime_allowed")
    for definition in library["definitions"]:
        if not isinstance(definition, dict):
            continue
        rule_key = str(definition.get("rule_key", ""))
        if not definition.get("condition_atoms"):
            failures.append(f"missing_condition_atoms:{rule_key}")
        if not definition.get("portrait_outputs"):
            failures.append(f"missing_portrait_outputs:{rule_key}")
        if not definition.get("question_outputs"):
            failures.append(f"missing_question_outputs:{rule_key}")
        if definition.get("source_authority") != "reviewed_bazi_knowledge_base":
            failures.append(f"source_authority_mismatch:{rule_key}")
        if definition.get("runtime_allowed") is not True:
            failures.append(f"runtime_blocked:{rule_key}")
        if definition.get("validation_state") != "active_ready":
            failures.append(f"unexpected_validation_state:{rule_key}")
        alignment = definition.get("bazi_alignment", {})
        if not isinstance(alignment, dict) or alignment.get("ok") is not True:
            failures.append(f"bazi_alignment_failed:{rule_key}")
    return {
        "version": "v20.knowledge_rule_library_validation.v1",
        "status": "pass" if not failures else "fail",
        "ok": not failures,
        "domain": domain.strip(),
        "definition_count": library["definition_count"],
        "atom_count": library["atom_count"],
        "portrait_output_count": library["portrait_output_count"],
        "question_output_count": library["question_output_count"],
        "failures": failures,
        "runtime_mutation": False,
        "guardrails": [
            "VALIDATION_ONLY",
            "RULE_LIBRARY_IS_ACTIVE_WITH_SYNTHETIC_ITERATION_SIGNAL",
            "NO_RUNTIME_MUTATION",
        ],
    }


def _definition_from_candidate(
    candidate: dict[str, object],
    unit: KnowledgeUnit | None,
) -> KnowledgeRuleDefinition:
    source_id = str(candidate.get("source_knowledge_id", ""))
    domain = str(candidate.get("domain", ""))
    rule_key = str(candidate.get("rule_id", "")) or f"v20.knowledge_rule.{_safe_id(source_id)}"
    return KnowledgeRuleDefinition(
        rule_key=rule_key,
        title=str(candidate.get("title", "")),
        domain=domain,
        source_knowledge_id=source_id,
        source_authority=str(candidate.get("source_authority", "reviewed_bazi_knowledge_base")),
        condition_atoms=_condition_atoms(candidate, unit),
        portrait_outputs=_portrait_outputs(candidate, unit),
        question_outputs=_question_outputs(candidate, unit),
        answer_guidance=_answer_guidance(candidate, unit),
        counterexamples=_counterexamples(unit),
        evidence_refs=tuple(str(row) for row in candidate.get("evidence_refs", ()) if row),
        boundary=str(candidate.get("boundary", "")),
        bazi_alignment=_alignment(candidate),
    )


def _condition_atoms(candidate: dict[str, object], unit: KnowledgeUnit | None) -> tuple[dict[str, object], ...]:
    atoms: list[dict[str, object]] = []
    if unit and unit.rule_atoms:
        atoms.extend(row.to_dict() | {"source": "knowledge_unit_structured_atom"} for row in unit.rule_atoms)
    for row in candidate.get("condition_atoms", ()):
        if isinstance(row, dict):
            atoms.append(dict(row) | {"source": "deterministic_rule_extraction"})
    return tuple(atoms)


def _portrait_outputs(candidate: dict[str, object], unit: KnowledgeUnit | None) -> tuple[dict[str, object], ...]:
    if unit and unit.portrait_mappings:
        return tuple(row.to_dict() | {"source": "knowledge_unit_structured_mapping"} for row in unit.portrait_mappings)
    domain = str(candidate.get("domain", ""))
    outputs = []
    for hook in candidate.get("emits_feature_hooks", ()):
        hook_text = str(hook)
        outputs.append(
            {
                "portrait_key": f"portrait.{domain}.{_safe_id(hook_text)}",
                "label": _domain_label(domain),
                "domain": domain,
                "description": str(candidate.get("summary", "")),
                "temperature": _domain_temperature(domain),
                "from_rule_atoms": [str(row.get("atom_id", "")) for row in candidate.get("condition_atoms", ()) if isinstance(row, dict)],
                "question_seeds": [_question_title(question, domain) for question in candidate.get("supports_question_hooks", ())],
                "source": "feature_hook_fallback_mapping",
                "guardrails": [
                    "FALLBACK_MAPPING_REQUIRES_REVIEW",
                    "NO_FIXED_FORTUNE_VERDICT",
                ],
            }
        )
    return tuple(outputs)


def _question_outputs(candidate: dict[str, object], unit: KnowledgeUnit | None) -> tuple[dict[str, object], ...]:
    if unit and unit.question_mappings:
        return tuple(row.to_dict() | {"source": "knowledge_unit_structured_mapping"} for row in unit.question_mappings)
    domain = str(candidate.get("domain", ""))
    return tuple(
        {
            "question_key": str(question),
            "title": _question_title(question, domain),
            "domain": domain,
            "trigger_rule_atoms": [
                str(row.get("atom_id", ""))
                for row in candidate.get("condition_atoms", ())
                if isinstance(row, dict) and row.get("evidence_role") in {"condition", "routing_effect"}
            ],
            "role": "recommended_question",
            "source": "question_hook_fallback_mapping",
            "guardrails": [
                "QUESTION_OUTPUT_REQUIRES_HUMAN_READABLE_REVIEW",
                "QUESTION_GUIDES_MEASUREMENT_NOT_VERDICT",
            ],
        }
        for question in candidate.get("supports_question_hooks", ())
    )


def _answer_guidance(candidate: dict[str, object], unit: KnowledgeUnit | None) -> tuple[dict[str, object], ...]:
    if unit and unit.answer_guidance:
        return tuple(row.to_dict() | {"source": "knowledge_unit_structured_guidance"} for row in unit.answer_guidance)
    domain = str(candidate.get("domain", ""))
    return (
        {
            "guidance_key": f"answer.{domain}.{_safe_id(str(candidate.get('source_knowledge_id', '')))}",
            "domain": domain,
            "reading_focus": _domain_answer_focus(domain),
            "allowed_phrases": [_domain_label(domain), "证据", "边界", "待复核"],
            "forbidden_phrases": ["一定", "必然", "固定吉凶", "具体时间点"],
            "boundary": str(candidate.get("boundary", "")),
            "source": "domain_fallback_guidance",
            "guardrails": [
                "ANSWER_GUIDANCE_IS_STYLE_AND_BOUNDARY_ONLY",
                "LLM_MUST_NOT_CREATE_NEW_CHART_FACTS",
            ],
        },
    )


def _counterexamples(unit: KnowledgeUnit | None) -> tuple[dict[str, object], ...]:
    if not unit:
        return ()
    return tuple(row.to_dict() | {"source": "knowledge_unit_counterexample"} for row in unit.counterexamples)


def _alignment(candidate: dict[str, object]) -> dict[str, object]:
    alignment = candidate.get("bazi_alignment", {})
    return dict(alignment) if isinstance(alignment, dict) else {"ok": False, "status": "missing_alignment"}


def _coverage(definitions: tuple[KnowledgeRuleDefinition, ...]) -> dict[str, object]:
    by_domain: dict[str, dict[str, int]] = {}
    for definition in definitions:
        row = by_domain.setdefault(
            definition.domain,
            {"definitions": 0, "atoms": 0, "portraits": 0, "questions": 0},
        )
        row["definitions"] += 1
        row["atoms"] += len(definition.condition_atoms)
        row["portraits"] += len(definition.portrait_outputs)
        row["questions"] += len(definition.question_outputs)
    return {
        "domain_count": len(by_domain),
        "domains": [
            {"domain": domain, **counts}
            for domain, counts in sorted(by_domain.items(), key=lambda item: item[0])
        ],
    }


def _unit_index() -> dict[str, KnowledgeUnit]:
    return {unit.knowledge_id: unit for unit in default_knowledge_units()}


def _domain_label(domain: str) -> str:
    labels = {
        "branch": "地支互动",
        "career": "事业结构",
        "element": "五行分布",
        "health": "身心平衡边界",
        "pattern": "格局复核",
        "relationship": "关系结构",
        "strength": "日主承载力",
        "ten_god": "十神角色",
        "time": "大运流年牵动",
        "useful_god": "用神候选路径",
        "wealth": "财星与收入结构",
    }
    return labels.get(domain, "命理主题")


def _domain_temperature(domain: str) -> str:
    if domain in {"time", "branch", "career", "wealth"}:
        return "hot"
    if domain in {"health", "relationship"}:
        return "cool"
    return "warm"


def _domain_answer_focus(domain: str) -> str:
    focuses = {
        "career": "先看事业角色、规则压力、表达方式和缓冲路径。",
        "wealth": "先看财星来源、承载力、通道和限制。",
        "strength": "先看扶助和压力，不急于定身强身弱。",
        "useful_god": "先列候选路径和证据缺口，不直接定喜忌。",
        "time": "先看大运流年牵动原局哪里，不做具体时间断语。",
    }
    return focuses.get(domain, f"先围绕{_domain_label(domain)}解释结构、证据和边界。")


def _question_title(question_key: object, domain: str) -> str:
    titles = {
        "q_branch_relation_detail": "地支互动会先影响哪一类事情？",
        "q_career_structure": "伤官见官是否被印星缓冲？",
        "q_element_balance": "五行偏向会让这个盘更需要哪种平衡？",
        "q_element_support_pressure": "五行支持和压力分别来自哪里？",
        "q_health_balance_boundary": "五行偏枯主要提示哪种平衡压力？",
        "q_hidden_stem_role": "藏干和明透分别承担什么结构作用？",
        "q_income_stability": "财星能不能用，要先看日主承载还是结构通道？",
        "q_pattern_structure": "格局和命格需要先复核哪条证据？",
        "q_relationship_structure": "关系结构里更明显的是互动、约束还是承接？",
        "q_strength_assessment": "这个八字日主偏强还是偏弱，适合先看什么？",
        "q_ten_god_focus": "十神里哪类角色最值得先看？",
        "q_ten_god_metadata": "十神来源层级会怎样影响判断？",
        "q_time_layer_context": "这一步大运流年最容易牵动哪条主线？",
        "q_time_relation_triggers": "流年大运会先牵动原局哪一块？",
        "q_useful_god_candidates": "哪些用神路径可以作为候选？",
        "q_useful_god_evidence_gaps": "用神判断现在还缺哪类证据？",
    }
    return titles.get(str(question_key), f"{_domain_label(domain)}需要先追问什么？")


def _safe_id(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_.-]+", "_", value)
