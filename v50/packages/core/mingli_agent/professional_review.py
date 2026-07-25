from __future__ import annotations

import json
import re
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any, Iterable

from core.contracts.professional_review import (
    AssertionSourceSpan,
    MingliAssertion,
    PersistenceStatus,
    ProfessionalIntegrityIssue,
    ProfessionalRawSourceKind,
    ProfessionalReviewBundle,
    ProfessionalReviewOverlay,
    ProfessionalScopeBlock,
)
from core.engines.bazi import resolve_ten_god
from core.engines.bazi.knowledge import (
    BRANCH_ELEMENTS,
    CONTROLS,
    GENERATES,
    HALF_TRIPLE_HARMONY,
    HIDDEN_STEMS,
    PAIR_PUNISHMENT,
    SELF_PUNISHMENT,
    SIX_BREAK,
    SIX_CLASH,
    SIX_HARM,
    SIX_HARMONY,
    STEM_ELEMENTS,
    TRIPLE_HARMONY,
    TRIPLE_PUNISHMENT,
)
from core.mingli_agent.contracts import ChartWorldInstance, MingliCognitiveRecord


PROFESSIONAL_REVIEW_VERSION = "assertion_integrity_gate.v1"
_STEMS = "甲乙丙丁戊己庚辛壬癸"
_BRANCHES = "子丑寅卯辰巳午未申酉戌亥"
_ELEMENT_ZH = {
    "木": "wood",
    "火": "fire",
    "土": "earth",
    "金": "metal",
    "水": "water",
}
_TEN_GOD_ZH = {
    "bi_jian": "比肩",
    "jie_cai": "劫财",
    "shi_shen": "食神",
    "shang_guan": "伤官",
    "pian_cai": "偏财",
    "zheng_cai": "正财",
    "qi_sha": "七杀",
    "zheng_guan": "正官",
    "pian_yin": "偏印",
    "zheng_yin": "正印",
}
_TEN_GODS = "比肩|劫财|食神|伤官|偏财|正财|七杀|正官|偏印|正印"
_TEXT_FIELDS = {
    "first_look",
    "whole_chart_thesis",
    "observation",
    "why_it_matters",
    "name",
    "thesis",
    "rejection_reason",
    "success_conditions",
    "failure_conditions",
    "path_statement",
    "source",
    "transformations",
    "target",
    "body_function_relation",
    "candidate",
    "role",
    "why_useful",
    "when_harmful",
    "applicable_conditions",
    "invalidating_conditions",
    "claim",
    "rationale",
    "conditions",
    "falsifiers",
    "why_predicted",
    "disconfirming_answer",
    "question",
    "purpose",
    "options",
    "expected_updates",
    "unresolved_questions",
    "causal_chain",
    "stable_tendencies",
    "favorable_environments",
    "adverse_environments",
    "opportunity_conditions",
    "risk_conditions",
    "timing_note",
    "prior_directions",
    "unknowns",
}
_CONDITIONAL_FIELDS = {
    "success_conditions",
    "failure_conditions",
    "applicable_conditions",
    "invalidating_conditions",
    "conditions",
    "falsifiers",
    "disconfirming_answer",
    "expected_updates",
}
_NON_ASSERTIVE_MODALITIES = {
    "conditional",
    "counterfactual",
    "quoted",
    "interrogative",
    "negated",
}


def review_professional_record(
    *,
    record: MingliCognitiveRecord,
    world: ChartWorldInstance,
    persistence_status: PersistenceStatus = "persisted",
    reviewer: str = "assertion_integrity_gate",
    created_at: str | None = None,
) -> ProfessionalReviewBundle:
    """Review the immutable pre-projection cognition represented by a record."""

    payload = source_payload_from_record(record)
    return review_professional_payload(
        payload=payload,
        world=world,
        cognitive_record_ref=record.record_id,
        persistence_status=persistence_status,
        reviewer=reviewer,
        created_at=created_at,
        raw_source_kind="assertion_gate_original_chunks",
    )


def review_professional_payload(
    *,
    payload: dict[str, Any],
    world: ChartWorldInstance,
    cognitive_record_ref: str,
    persistence_status: PersistenceStatus = "persisted",
    reviewer: str = "assertion_integrity_gate",
    created_at: str | None = None,
    raw_source_kind: ProfessionalRawSourceKind = "model_payload",
) -> ProfessionalReviewBundle:
    """Apply deterministic tiers without repairing or rewriting source content."""

    raw_payload = deepcopy(payload)
    raw_hash = _canonical_hash(raw_payload)
    assertions = extract_mingli_assertions(
        payload=raw_payload,
        cognitive_record_ref=cognitive_record_ref,
    )
    issues: list[ProfessionalIntegrityIssue] = []
    for assertion in assertions:
        issues.extend(_tier0_contract_issues(assertion=assertion, world=world))
        issues.extend(_tier1_fact_issues(assertion=assertion, world=world))
        issues.extend(_tier2_ontology_issues(assertion=assertion, world=world))
        issues.extend(_tier3_structure_issues(assertion=assertion, world=world))
        issues.extend(_tier4_domain_issues(assertion=assertion))
    issues = _dedupe_issues(issues)

    core_issues = [
        item
        for item in issues
        if item.block_scope == "core" and item.disposition in {"hard_block", "manual_review"}
    ]
    domain_issues = [item for item in issues if item.block_scope == "domain"]
    suppressed = sorted({item.assertion_ref for item in issues})
    blocked = sorted({
        item.assertion_ref
        for item in issues
        if item.disposition in {"hard_block", "domain_block", "manual_review"}
    })
    release_status = (
        "blocked"
        if core_issues
        else "partially_blocked"
        if issues
        else "passed"
    )
    assertions_hash = _canonical_hash([item.model_dump(mode="json") for item in assertions])
    issue_hash = _canonical_hash([item.model_dump(mode="json") for item in issues])
    overlay_id = f"professional-review:{sha256(f'{cognitive_record_ref}|{assertions_hash}|{issue_hash}'.encode()).hexdigest()[:24]}"
    scope_blocks: list[ProfessionalScopeBlock] = []
    if core_issues:
        scope_blocks.append(ProfessionalScopeBlock(
            scope="core",
            scope_ref="whole_chart",
            reason_issue_refs=[item.issue_id for item in core_issues],
            downstream_domains_blocked=True,
        ))
    for domain in sorted({item.domain for item in domain_issues if item.domain}):
        scoped = [item for item in domain_issues if item.domain == domain]
        scope_blocks.append(ProfessionalScopeBlock(
            scope="domain",
            scope_ref=domain,
            reason_issue_refs=[item.issue_id for item in scoped],
        ))
    overlay = ProfessionalReviewOverlay(
        overlay_id=overlay_id,
        cognitive_record_ref=cognitive_record_ref,
        assertions_hash=assertions_hash,
        raw_output_hash=raw_hash,
        raw_source_kind=raw_source_kind,
        persistence_status=persistence_status,
        professional_release_status=release_status,
        reviewed_assertion_refs=[item.assertion_id for item in assertions],
        blocked_assertion_refs=blocked,
        suppressed_assertion_refs=suppressed,
        issues=issues,
        hard_error_count=sum(item.severity == "hard" for item in issues),
        major_error_count=sum(item.severity == "major" for item in issues),
        minor_error_count=sum(item.severity == "minor" for item in issues),
        scope_blocks=scope_blocks,
        downstream_domains_blocked=bool(core_issues),
        reviewer=reviewer,
        created_at=created_at or datetime.now(timezone.utc).isoformat(),
    )
    if raw_hash != _canonical_hash(payload):
        raise RuntimeError("professional_review_modified_raw_output")
    return ProfessionalReviewBundle(assertions=assertions, overlay=overlay)


def source_payload_from_record(record: MingliCognitiveRecord) -> dict[str, Any]:
    """Restore pre-projection values kept by AssertionGateDecision.original_text."""

    payload = record.cognition.model_dump(mode="json")
    for decision in record.assertion_gate.decisions:
        raw = decision.original_text
        if not raw:
            continue
        try:
            value: Any = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            value = raw
        _merge_source_value(
            payload,
            decision.field_path,
            value,
            assertion_ref=decision.assertion_ref,
            assertion_kind=decision.assertion_kind,
            evidence_refs=[
                *decision.accepted_evidence_refs,
                *decision.rejected_evidence_refs,
            ],
        )
        if (
            decision.assertion_kind == "hypothesis"
            and decision.disposition == "suppressed"
            and decision.field_path == "hypotheses.0"
        ):
            payload["selected_hypothesis_id"] = decision.assertion_ref
    return payload


def extract_mingli_assertions(
    *,
    payload: dict[str, Any],
    cognitive_record_ref: str,
) -> list[MingliAssertion]:
    selected_hypothesis_id = str(payload.get("selected_hypothesis_id") or "")
    output: list[MingliAssertion] = []

    def visit(value: Any, path: str, parent: dict[str, Any] | None, key: str) -> None:
        if isinstance(value, dict):
            for child_key, child in value.items():
                child_path = f"{path}.{child_key}" if path else child_key
                visit(child, child_path, value, child_key)
            return
        if isinstance(value, list):
            for index, child in enumerate(value):
                visit(child, f"{path}.{index}", parent, key)
            return
        if not isinstance(value, str) or not value.strip() or key not in _TEXT_FIELDS:
            return
        for start, end, text in _sentence_spans(value):
            modality = _assertion_modality(
                text=text,
                field_path=path,
                parent=parent,
                selected_hypothesis_id=selected_hypothesis_id,
            )
            assertion_type = _assertion_type(path)
            scope, domain = _assertion_scope(path=path, text=text)
            impact_scope = _impact_scope(
                field_path=path,
                parent=parent,
                selected_hypothesis_id=selected_hypothesis_id,
                domain=domain,
            )
            evidence, counter = _evidence_refs(parent=parent, payload=payload)
            attributes = _assertion_attributes(
                field_path=path,
                parent=parent,
                selected_hypothesis_id=selected_hypothesis_id,
                payload=payload,
            )
            assertion_id = "assertion:" + sha256(
                f"{cognitive_record_ref}|{path}|{start}|{end}|{text}".encode("utf-8")
            ).hexdigest()[:24]
            symbols = _symbol_refs(text)
            output.append(MingliAssertion(
                assertion_id=assertion_id,
                cognitive_record_ref=cognitive_record_ref,
                source_text=text,
                source_span=AssertionSourceSpan(field_path=path, start=start, end=end),
                source_hash=sha256(text.encode("utf-8")).hexdigest(),
                assertion_type=assertion_type,
                modality=modality,
                scope=scope,
                subject_refs=symbols[:1],
                predicate=_predicate(text),
                object_refs=symbols[1:],
                hypothesis_ref=str((parent or {}).get("hypothesis_id") or ""),
                evidence_refs=evidence,
                counter_evidence_refs=counter,
                epistemic_status=_epistemic_status(assertion_type, modality),
                impact_scope=impact_scope,
                domain=domain,
                attributes=attributes,
            ))

    visit(payload, "", None, "")
    return output


def professional_projection_payload(
    *,
    payload: dict[str, Any],
    bundle: ProfessionalReviewBundle,
) -> dict[str, Any]:
    """Suppress rejected assertion containers; never replace their semantics."""

    output = deepcopy(payload)
    suppressed_refs = set(bundle.overlay.suppressed_assertion_refs)
    container_paths = {
        matched
        for item in bundle.assertions
        if item.assertion_id in suppressed_refs
        if (matched := _matching_projection_container_path(output, item)) is not None
    }
    container_paths = sorted(
        container_paths,
        key=lambda path: [int(token) if token.isdigit() else token for token in path.split(".")],
        reverse=True,
    )
    for path in container_paths:
        _remove_projection_value(output, path)
    return output


def _tier0_contract_issues(
    *, assertion: MingliAssertion,
    world: ChartWorldInstance,
) -> list[ProfessionalIntegrityIssue]:
    allowed = set(world.allowed_evidence_refs)
    invalid = [
        ref
        for ref in [*assertion.evidence_refs, *assertion.counter_evidence_refs]
        if ref and ref not in allowed
    ]
    if not invalid:
        return []
    return [_issue(
        assertion=assertion,
        tier=0,
        issue_class="invalid_evidence_ref",
        severity="major",
        message=f"证据引用不属于当前正式世界：{', '.join(invalid)}",
        canonical_refs=[f"world:{world.world_id}:allowed_evidence_refs"],
    )]


def _tier1_fact_issues(
    *, assertion: MingliAssertion,
    world: ChartWorldInstance,
) -> list[ProfessionalIntegrityIssue]:
    if assertion.modality in _NON_ASSERTIVE_MODALITIES:
        return []
    text = assertion.source_text
    issues: list[ProfessionalIntegrityIssue] = []

    relation_pattern = rf"([{_STEMS}])(?:[木火土金水])?[^。；;，,]{{0,8}}?(生助|生扶|生|克制|制约|克)[^。；;，,]{{0,8}}?([{_STEMS}])(?:[木火土金水])?"
    for match in re.finditer(relation_pattern, text):
        if text[max(0, match.start() - 1):match.start()] in {"晦", "泄"}:
            continue
        source, verb, target = match.group(1), match.group(2), match.group(3)
        source_element = STEM_ELEMENTS[source]
        target_element = STEM_ELEMENTS[target]
        expected = GENERATES[source_element] if verb.startswith("生") else CONTROLS[source_element]
        if target_element != expected:
            issues.append(_issue(
                assertion=assertion,
                tier=1,
                issue_class=(
                    "five_element_relation_error"
                    if verb.startswith("生")
                    else "five_element_control_error"
                ),
                severity="hard",
                message=f"{source}{verb}{target}与正式五行方向冲突。",
                canonical_refs=[f"canonical:five_elements:{source_element}:{verb}:{expected}"],
            ))

    implied_day_pattern = rf"([{_STEMS}])(?:[木火土金水])?[^。；;，,]{{0,5}}?(生助|生扶)(?=、|，|。|；|;|$)"
    day_stem = world.pillars[2][0] if len(world.pillars) >= 3 else ""
    if day_stem in STEM_ELEMENTS and re.search(r"(?:日主|命主)", text):
        for match in re.finditer(implied_day_pattern, text):
            source, verb = match.group(1), match.group(2)
            if GENERATES[STEM_ELEMENTS[source]] != STEM_ELEMENTS[day_stem]:
                issues.append(_issue(
                    assertion=assertion,
                    tier=1,
                    issue_class="five_element_relation_error",
                    severity="hard",
                    message=f"句中{source}{verb}指向日主{day_stem}，与正式五行方向冲突。",
                    canonical_refs=[f"canonical:five_elements:{STEM_ELEMENTS[source]}:generates"],
                ))

    element_pattern = r"([木火土金水])\s*(生助|生扶|生|克制|制约|克)\s*([木火土金水])"
    for match in re.finditer(element_pattern, text):
        if text[max(0, match.start() - 1):match.start()] in {"晦", "泄", "补", "暖"}:
            continue
        source_zh, verb, target_zh = match.group(1), match.group(2), match.group(3)
        source = _ELEMENT_ZH[source_zh]
        target = _ELEMENT_ZH[target_zh]
        expected = GENERATES[source] if verb.startswith("生") else CONTROLS[source]
        if target != expected:
            issues.append(_issue(
                assertion=assertion,
                tier=1,
                issue_class="five_element_relation_error",
                severity="hard",
                message=f"{source_zh}{verb}{target_zh}与正式五行方向冲突。",
                canonical_refs=[f"canonical:five_elements:{source}:{verb}:{expected}"],
            ))

    if day_stem in STEM_ELEMENTS:
        stem_ten_god_pattern = rf"([{_STEMS}])(?:[木火土金水])?[^。；;，,]{{0,5}}?(?:为|是|属于|对应|即)[^。；;，,]{{0,3}}?({_TEN_GODS})"
        for match in re.finditer(stem_ten_god_pattern, text):
            stem, claimed = match.group(1), match.group(2)
            expected = _TEN_GOD_ZH[resolve_ten_god(day_stem=day_stem, other_stem=stem)]
            if claimed != expected:
                issues.append(_issue(
                    assertion=assertion,
                    tier=1,
                    issue_class="ten_god_mapping_error",
                    severity="hard",
                    message=f"{stem}相对{day_stem}日主应为{expected}，不是{claimed}。",
                    canonical_refs=[f"canonical:ten_god:{day_stem}:{stem}:{expected}"],
                ))
        branch_role_pattern = rf"([{_BRANCHES}])(?:[木火土金水])?\s*[（(]({_TEN_GODS})[）)]"
        for match in re.finditer(branch_role_pattern, text):
            branch, claimed = match.group(1), match.group(2)
            principal = HIDDEN_STEMS[branch][0]
            expected = _TEN_GOD_ZH[resolve_ten_god(day_stem=day_stem, other_stem=principal)]
            if claimed != expected:
                issues.append(_issue(
                    assertion=assertion,
                    tier=1,
                    issue_class="ten_god_mapping_error",
                    severity="hard",
                    message=f"{branch}主气{principal}相对{day_stem}日主应为{expected}，不是{claimed}。",
                    canonical_refs=[f"canonical:ten_god:{day_stem}:{principal}:{expected}"],
                ))

        root_pattern = rf"([{_BRANCHES}])(?:[木火土金水])?[^。；;，,]{{0,10}}?(?:扎根|通根|坐根|为根)"
        for match in re.finditer(root_pattern, text):
            branch = match.group(1)
            day_element = STEM_ELEMENTS[day_stem]
            if not any(STEM_ELEMENTS[stem] == day_element for stem in HIDDEN_STEMS[branch]):
                issues.append(_issue(
                    assertion=assertion,
                    tier=1,
                    issue_class="rooting_fact_error",
                    severity="hard",
                    message=f"{branch}藏干不含{day_element}，不能作为{day_stem}日主之根。",
                    canonical_refs=[f"canonical:hidden_stems:{branch}"],
                ))

    sitting_pattern = rf"([{_STEMS}])(?:[木火土金水])?[^。；;]{{0,24}}?坐([{_BRANCHES}])(?:[木火土金水])?[^。；;，,]{{0,8}}?(?:受|被)(?:其)?克"
    for match in re.finditer(sitting_pattern, text):
        stem, branch = match.group(1), match.group(2)
        if CONTROLS.get(BRANCH_ELEMENTS[branch]) != STEM_ELEMENTS[stem]:
            issues.append(_issue(
                assertion=assertion,
                tier=1,
                issue_class="five_element_control_direction_error",
                severity="hard",
                message=f"{branch}并不克{stem}，受克方向与正式五行关系冲突。",
                canonical_refs=[f"canonical:five_elements:{BRANCH_ELEMENTS[branch]}:controls"],
            ))
    return issues


def _tier2_ontology_issues(
    *, assertion: MingliAssertion,
    world: ChartWorldInstance,
) -> list[ProfessionalIntegrityIssue]:
    if assertion.modality in _NON_ASSERTIVE_MODALITIES:
        return []
    text = assertion.source_text
    issues: list[ProfessionalIntegrityIssue] = []
    relation_pattern = rf"([{_BRANCHES}])(?:[木火土金水])?[^。；;，,]{{0,5}}?([{_BRANCHES}])(?:[木火土金水])?[^。；;，,]{{0,5}}?(半合|六合|相合|合|相冲|冲|相刑|刑|相害|害|相破|破)([木火土金水])?(?:局)?"
    seen: set[tuple[str, str, str]] = set()
    for match in re.finditer(relation_pattern, text):
        branch_a, branch_b, label, element_zh = match.groups()
        key = tuple(sorted((branch_a, branch_b))) + (label,)
        if key in seen:
            continue
        seen.add(key)
        pair = frozenset((branch_a, branch_b))
        valid, expected_element = _relation_is_valid(pair=pair, label=label)
        if not valid:
            issues.append(_issue(
                assertion=assertion,
                tier=2,
                issue_class="invalid_branch_relation",
                severity="hard",
                message=f"正式关系本体不支持{branch_a}{branch_b}{label}。",
                canonical_refs=["canonical:branch_relation_ontology"],
            ))
        elif element_zh and expected_element and _ELEMENT_ZH[element_zh] != expected_element:
            issues.append(_issue(
                assertion=assertion,
                tier=2,
                issue_class="branch_relation_element_error",
                severity="hard",
                message=f"{branch_a}{branch_b}{label}的五行归属不是{element_zh}。",
                canonical_refs=[f"canonical:branch_relation_element:{expected_element}"],
            ))

    if re.search(r"(?:两丑一酉|酉金与两丑).{0,20}(?:强金局|彻底转化|同化|完全化)", text):
        issues.append(_issue(
            assertion=assertion,
            tier=2,
            issue_class="half_combination_overpromoted_to_transformation",
            severity="hard",
            message="两个酉丑半合关系不能自动晋升为完整三合化局。",
            canonical_refs=["canonical:half_triple_harmony:酉丑"],
        ))

    if re.search(r"双财生杀\s*[（(]食伤[）)]", text):
        issues.append(_issue(
            assertion=assertion,
            tier=2,
            issue_class="ontology_mechanism_role_conflict",
            severity="hard",
            message="财、杀与食伤是不同十神角色，不能用括号混写为同一机制。",
            canonical_refs=["canonical:ten_god:role_ontology"],
        ))

    if "岁运并临" in text and assertion.scope == "natal":
        issues.append(_issue(
            assertion=assertion,
            tier=2,
            issue_class="natal_timing_scope_conflict",
            severity="hard",
            message="原局柱间关系不能命名为岁运并临。",
            canonical_refs=["canonical:scope:natal_vs_timing"],
        ))
    return issues


def _tier3_structure_issues(
    *, assertion: MingliAssertion,
    world: ChartWorldInstance,
) -> list[ProfessionalIntegrityIssue]:
    if assertion.modality in _NON_ASSERTIVE_MODALITIES:
        return []
    text = assertion.source_text
    issues: list[ProfessionalIntegrityIssue] = []
    if assertion.assertion_type == "work_path_claim" and assertion.source_span.field_path.endswith("path_statement"):
        source = assertion.attributes.get("source") or []
        target = assertion.attributes.get("target") or []
        if not source or not target:
            issues.append(_issue(
                assertion=assertion,
                tier=3,
                issue_class="work_path_incomplete",
                severity="major",
                message="做功路径缺少明确源端或目标端。",
                canonical_refs=["contract:work_path:source_transform_target"],
            ))
        if re.search(r"辛金[^。；;]{0,30}(?:->|→)[^。；;]{0,30}丑土[^。；;]{0,12}得生", text):
            issues.append(_issue(
                assertion=assertion,
                tier=3,
                issue_class="work_path_transition_direction_error",
                severity="hard",
                message="路径把辛金到丑土标为得生，方向与土生金相反。",
                canonical_refs=["canonical:five_elements:earth:generates:metal"],
            ))
        if re.search(r"疏泄旺土[^。；;]{0,16}(?:并|同时)生助戊土", text):
            issues.append(_issue(
                assertion=assertion,
                tier=3,
                issue_class="work_path_internal_contradiction",
                severity="hard",
                message="同一步同时声称疏泄旺土并生助旺土，机制方向自相矛盾。",
                canonical_refs=["contract:work_path:internal_consistency"],
            ))

        if (
            "制杀" in text
            and not _world_has_officer_or_killing(world)
            and not _text_names_hidden_officer_or_killing(text=text, world=world)
        ):
            issues.append(_issue(
                assertion=assertion,
                tier=3,
                issue_class="mechanism_required_role_missing",
                severity="hard",
                message="原局正式节点中未建立官杀，做功路径不能直接使用制杀机制。",
                canonical_refs=["canonical:ten_god:visible_or_hidden_officer_killing"],
            ))

    if (
        assertion.assertion_type == "structural_hypothesis"
        and assertion.source_span.field_path.endswith(".thesis")
        and assertion.attributes.get("selected")
        and assertion.attributes.get("confidence") == "high"
        and not assertion.attributes.get("success_conditions")
        and not assertion.attributes.get("work_path_success_conditions")
    ):
        issues.append(_issue(
            assertion=assertion,
            tier=3,
            issue_class="high_confidence_hypothesis_without_success_conditions",
            severity="major",
            message="高置信主假设没有明确成立条件，不能作为正式整盘结论发布。",
            canonical_refs=["contract:hypothesis:success_conditions"],
        ))

    if re.search(r"(?:冲|刑|害|破)[^。；;]{0,18}(?:彻底|完全)(?:破坏|摧毁|拔除|消失)", text):
        issues.append(_issue(
            assertion=assertion,
            tier=3,
            issue_class="relation_effect_overclaim_without_activation",
            severity="major",
            message="关系存在不能在缺少激活与条件证明时直接升级为彻底破坏。",
            canonical_refs=["contract:relation:existence_vs_activation"],
        ))
    return issues


def _tier4_domain_issues(*, assertion: MingliAssertion) -> list[ProfessionalIntegrityIssue]:
    if assertion.scope != "natal" or assertion.modality in _NON_ASSERTIVE_MODALITIES:
        return []
    path = assertion.source_span.field_path
    if any(token in path for token in ("next_probe", "unresolved_questions", "rejection_reason")):
        return []
    if not re.search(r"(?:健康|疾病|心血管|眼目|精神焦虑|精神崩溃|抑郁|失眠)", assertion.source_text):
        return []
    return [_issue(
        assertion=assertion,
        tier=4,
        issue_class="unopened_health_domain_projection",
        severity="major",
        message="整盘基线不能把未经现实证据审查的健康映射发布为正式结论。",
        canonical_refs=["contract:domain:health:closed"],
        force_scope="domain",
        domain="health",
    )]


def _issue(
    *,
    assertion: MingliAssertion,
    tier: int,
    issue_class: str,
    severity: str,
    message: str,
    canonical_refs: Iterable[str],
    force_scope: str = "",
    domain: str = "",
) -> ProfessionalIntegrityIssue:
    scope = force_scope or assertion.impact_scope
    disposition = (
        "hard_block"
        if scope == "core"
        else "domain_block"
        if scope == "domain"
        else "suppress"
    )
    digest = sha256(
        f"{assertion.assertion_id}|{tier}|{issue_class}|{message}".encode("utf-8")
    ).hexdigest()[:20]
    return ProfessionalIntegrityIssue(
        issue_id=f"professional-issue:{digest}",
        assertion_ref=assertion.assertion_id,
        tier=tier,
        issue_class=issue_class,
        severity=severity,
        disposition=disposition,
        block_scope=scope,
        domain=domain or assertion.domain,
        message=message,
        canonical_refs=list(canonical_refs),
    )


def _relation_is_valid(*, pair: frozenset[str], label: str) -> tuple[bool, str]:
    if "半合" in label:
        row = HALF_TRIPLE_HARMONY.get(pair)
        return row is not None, row[1] if row else ""
    if "冲" in label:
        return pair in SIX_CLASH, ""
    if label in {"六合", "相合", "合"}:
        return pair in SIX_HARMONY, ""
    if "害" in label:
        return pair in SIX_HARM, ""
    if "破" in label:
        return pair in SIX_BREAK, ""
    if "刑" in label:
        valid = pair in PAIR_PUNISHMENT or (
            len(pair) == 1 and next(iter(pair), "") in SELF_PUNISHMENT
        ) or any(pair.issubset(group) for group in TRIPLE_PUNISHMENT)
        return valid, ""
    return False, ""


def _world_has_officer_or_killing(world: ChartWorldInstance) -> bool:
    day_stem = world.pillars[2][0] if len(world.pillars) >= 3 else ""
    if day_stem not in STEM_ELEMENTS:
        return False
    # A mechanism may not promote a hidden possibility into an established
    # pressure node without naming and evidencing that hidden-stem mechanism.
    stems = [pillar[0] for pillar in world.pillars if len(pillar) >= 2]
    return any(resolve_ten_god(day_stem=day_stem, other_stem=stem) in {"qi_sha", "zheng_guan"} for stem in stems)


def _text_names_hidden_officer_or_killing(
    *,
    text: str,
    world: ChartWorldInstance,
) -> bool:
    day_stem = world.pillars[2][0] if len(world.pillars) >= 3 else ""
    if day_stem not in STEM_ELEMENTS:
        return False
    for pillar in world.pillars:
        if len(pillar) < 2:
            continue
        branch = pillar[1]
        for stem in HIDDEN_STEMS[branch]:
            role = resolve_ten_god(day_stem=day_stem, other_stem=stem)
            if role not in {"qi_sha", "zheng_guan"}:
                continue
            role_zh = _TEN_GOD_ZH[role]
            explicit_patterns = (
                f"{branch}中{stem}",
                f"{branch}藏{stem}",
                f"{stem}藏于{branch}",
                f"{stem}{role_zh}",
            )
            if any(pattern in text for pattern in explicit_patterns):
                return True
    return False


def _merge_source_value(
    payload: dict[str, Any],
    path: str,
    value: Any,
    *,
    assertion_ref: str,
    assertion_kind: str,
    evidence_refs: list[str],
) -> None:
    tokens = path.split(".") if path else []
    if not tokens:
        return
    current: Any = payload
    for token in tokens[:-1]:
        if token.isdigit():
            index = int(token)
            if not isinstance(current, list) or index >= len(current):
                return
            current = current[index]
        else:
            current = current.get(token)
        if current is None:
            return
    last = tokens[-1]
    if last.isdigit():
        if not isinstance(current, list):
            return
        id_key = {
            "hypothesis": "hypothesis_id",
            "salient_phenomenon": "phenomenon_id",
            "portrait_assertion": "assertion_id",
            "prior_prediction": "prediction_id",
        }.get(assertion_kind, "")
        existing = next(
            (
                item
                for item in current
                if id_key and isinstance(item, dict) and str(item.get(id_key) or "") == assertion_ref
            ),
            None,
        )
        if existing is None:
            index = int(last)
            existing = current[index] if index < len(current) else None
        if isinstance(existing, dict) and isinstance(value, dict):
            existing.update(value)
            if id_key:
                existing[id_key] = assertion_ref
            if assertion_kind == "hypothesis":
                existing.setdefault("status", "primary" if int(last) == 0 else "alternative")
                existing.setdefault("confidence", "medium")
                existing.setdefault("success_conditions", [])
                existing.setdefault("failure_conditions", [])
                existing.setdefault("supporting_evidence_refs", evidence_refs)
            existing.setdefault("evidence_refs", evidence_refs)
            return
        if isinstance(value, dict):
            restored = dict(value)
            if id_key:
                restored[id_key] = assertion_ref
            if assertion_kind == "hypothesis":
                restored.update({
                    "status": "primary" if int(last) == 0 else "alternative",
                    "confidence": "medium",
                    "success_conditions": [],
                    "failure_conditions": [],
                    "supporting_evidence_refs": evidence_refs,
                })
            restored.setdefault("evidence_refs", evidence_refs)
            current.append(restored)
        return
    existing = current.get(last)
    if isinstance(existing, dict) and isinstance(value, dict):
        value = {**existing, **value}
    current[last] = value


def _sentence_spans(text: str) -> list[tuple[int, int, str]]:
    output: list[tuple[int, int, str]] = []
    for match in re.finditer(r"[^。；;\n]+(?:[。；;]|$)", text):
        stripped = match.group(0).strip()
        stripped = stripped.rstrip("。；;").strip()
        if not stripped:
            continue
        relative = match.group(0).find(stripped)
        start = match.start() + relative
        output.append((start, start + len(stripped), stripped))
    return output or [(0, len(text), text)]


def _assertion_modality(
    *,
    text: str,
    field_path: str,
    parent: dict[str, Any] | None,
    selected_hypothesis_id: str,
) -> str:
    key = field_path.split(".")[-1]
    if key.isdigit() and len(field_path.split(".")) > 1:
        key = field_path.split(".")[-2]
    if key in _CONDITIONAL_FIELDS or re.search(r"^(?:若|如果|假如|假设|除非|倘若|一旦)", text):
        return "conditional"
    if "?" in text or "？" in text or key in {"question", "unresolved_questions"}:
        return "interrogative"
    if re.search(r"(?:并非|不是|不构成|不存在|不能视为|不等于)", text[:18]):
        return "negated"
    if re.search(r"(?:原文|用户|命理师|有人(?:说)?|其称)[：:]?[‘'\"“]", text):
        return "quoted"
    if isinstance(parent, dict) and parent.get("hypothesis_id"):
        hypothesis_id = str(parent.get("hypothesis_id") or "")
        if hypothesis_id != selected_hypothesis_id or parent.get("status") != "primary":
            return "candidate"
    if re.search(r"(?:可能|或许|也许|候选|假说|尚待|待确认)", text):
        return "candidate"
    return "asserted"


def _assertion_type(path: str) -> str:
    if path.startswith("work_path"):
        return "work_path_claim"
    if path.startswith("hypotheses"):
        return "structural_hypothesis"
    if path.startswith("salient_phenomena"):
        return "derived_relation"
    if path.startswith("useful_god_reasoning"):
        return "functional_role_claim"
    if path.startswith("portrait"):
        return "portrait_claim"
    if path.startswith("prior_predictions"):
        return "prediction"
    if path.startswith(("career", "wealth")):
        return "domain_claim"
    if "question" in path or "probe" in path or "unresolved" in path:
        return "question"
    if path in {"first_look", "whole_chart_thesis"}:
        return "mechanism_claim"
    return "mechanism_claim"


def _assertion_scope(*, path: str, text: str) -> tuple[str, str]:
    if path.startswith("career"):
        return "domain", "career"
    if path.startswith("wealth"):
        return "domain", "wealth"
    if re.search(r"(?:大运|运中|行运)", text):
        return "luck_cycle", ""
    if re.search(r"(?:流年|年份|年运)", text):
        return "annual", ""
    if re.search(r"(?:流月|月份|月运)", text):
        return "monthly", ""
    return "natal", ""


def _impact_scope(
    *,
    field_path: str,
    parent: dict[str, Any] | None,
    selected_hypothesis_id: str,
    domain: str,
) -> str:
    if domain:
        return "domain"
    if field_path in {"first_look", "whole_chart_thesis"} or field_path.startswith("work_path"):
        return "core"
    if field_path.startswith("salient_phenomena") or field_path.startswith("useful_god_reasoning"):
        return "core"
    if field_path.startswith("hypotheses") and isinstance(parent, dict):
        if str(parent.get("hypothesis_id") or "") == selected_hypothesis_id:
            return "core"
    return "assertion"


def _evidence_refs(
    *,
    parent: dict[str, Any] | None,
    payload: dict[str, Any],
) -> tuple[list[str], list[str]]:
    source = parent or payload
    evidence = source.get("evidence_refs") or source.get("supporting_evidence_refs") or []
    counter = source.get("counter_evidence_refs") or []
    if not isinstance(evidence, list):
        evidence = []
    if not isinstance(counter, list):
        counter = []
    return [str(item) for item in evidence], [str(item) for item in counter]


def _assertion_attributes(
    *,
    field_path: str,
    parent: dict[str, Any] | None,
    selected_hypothesis_id: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    if not isinstance(parent, dict):
        return {}
    if field_path.startswith("work_path"):
        return {
            key: deepcopy(parent.get(key))
            for key in ("source", "transformations", "target", "closure", "success_conditions", "failure_conditions")
        }
    if field_path.startswith("hypotheses"):
        return {
            "selected": str(parent.get("hypothesis_id") or "") == selected_hypothesis_id,
            "status": parent.get("status"),
            "confidence": parent.get("confidence"),
            "success_conditions": deepcopy(parent.get("success_conditions") or []),
            "failure_conditions": deepcopy(parent.get("failure_conditions") or []),
            "work_path_success_conditions": deepcopy(
                (payload.get("work_path") or {}).get("success_conditions") or []
            ),
        }
    return {}


def _epistemic_status(assertion_type: str, modality: str) -> str:
    if assertion_type == "chart_fact":
        return "fact"
    if modality in {"candidate", "conditional", "counterfactual"}:
        return "hypothesis"
    if modality == "interrogative":
        return "unresolved"
    if assertion_type == "derived_relation":
        return "derived"
    return "interpretation"


def _symbol_refs(text: str) -> list[str]:
    output: list[str] = []
    for stem in re.findall(rf"[{_STEMS}]", text):
        ref = f"symbol:stem:{stem}"
        if ref not in output:
            output.append(ref)
    for branch in re.findall(rf"[{_BRANCHES}]", text):
        ref = f"symbol:branch:{branch}"
        if ref not in output:
            output.append(ref)
    return output


def _predicate(text: str) -> str:
    match = re.search(r"(半合|三合|六合|相冲|相刑|相害|相破|生助|生扶|生|克制|制约|克|通根|透干|制杀|生财)", text)
    return match.group(1) if match else "interprets"


def _suppressible_container_path(path: str) -> str:
    tokens = path.split(".")
    for index, token in enumerate(tokens):
        if token.isdigit():
            return ".".join(tokens[: index + 1])
    return path


def _matching_projection_container_path(
    payload: dict[str, Any],
    assertion: MingliAssertion,
) -> str | None:
    requested = _suppressible_container_path(assertion.source_span.field_path)
    current = _value_at_path(payload, requested)
    if current is not None and assertion.source_text in _text_content(current):
        return requested
    tokens = assertion.source_span.field_path.split(".")
    numeric = next((index for index, token in enumerate(tokens) if token.isdigit()), None)
    if numeric is None:
        return None
    collection_path = ".".join(tokens[:numeric])
    collection = _value_at_path(payload, collection_path)
    if not isinstance(collection, list):
        return None
    for index, item in enumerate(collection):
        if assertion.source_text in _text_content(item):
            return f"{collection_path}.{index}"
    return None


def _value_at_path(payload: dict[str, Any], path: str) -> Any:
    current: Any = payload
    for token in path.split(".") if path else []:
        if token.isdigit():
            index = int(token)
            if not isinstance(current, list) or index >= len(current):
                return None
            current = current[index]
        elif isinstance(current, dict):
            current = current.get(token)
        else:
            return None
    return current


def _text_content(value: Any) -> str:
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, sort_keys=True) if value is not None else ""


def _remove_projection_value(payload: dict[str, Any], path: str) -> None:
    tokens = path.split(".")
    current: Any = payload
    for token in tokens[:-1]:
        current = current[int(token)] if token.isdigit() else current.get(token)
        if current is None:
            return
    last = tokens[-1]
    if last.isdigit() and isinstance(current, list):
        index = int(last)
        if 0 <= index < len(current):
            current.pop(index)
    elif isinstance(current, dict):
        current.pop(last, None)


def _canonical_hash(value: Any) -> str:
    return sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _dedupe_issues(issues: list[ProfessionalIntegrityIssue]) -> list[ProfessionalIntegrityIssue]:
    output: list[ProfessionalIntegrityIssue] = []
    seen: set[tuple[str, str]] = set()
    for issue in issues:
        key = (issue.assertion_ref, issue.issue_class)
        if key not in seen:
            seen.add(key)
            output.append(issue)
    return output


__all__ = [
    "PROFESSIONAL_REVIEW_VERSION",
    "extract_mingli_assertions",
    "professional_projection_payload",
    "review_professional_payload",
    "review_professional_record",
    "source_payload_from_record",
]
