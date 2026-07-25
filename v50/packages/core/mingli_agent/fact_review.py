from __future__ import annotations

import re
from copy import deepcopy
from hashlib import sha256
from typing import Any

from core.mingli_agent.contracts import ChartWorldInstance, ProfessionalFactIssue


_BRANCHES = "子丑寅卯辰巳午未申酉戌亥"
_RELATION_TOKEN = "暗合|六合|三合|半合|相冲|冲|相合|合|相刑|刑|相害|害|相破|破"
_STEM_ELEMENTS = {
    "甲": "木",
    "乙": "木",
    "丙": "火",
    "丁": "火",
    "戊": "土",
    "己": "土",
    "庚": "金",
    "辛": "金",
    "壬": "水",
    "癸": "水",
}
_BRANCH_ELEMENTS = {
    "子": "水",
    "丑": "土",
    "寅": "木",
    "卯": "木",
    "辰": "土",
    "巳": "火",
    "午": "火",
    "未": "土",
    "申": "金",
    "酉": "金",
    "戌": "土",
    "亥": "水",
}
_ELEMENT_CONTROLS = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}
_ELEMENT_GENERATES = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
_STEM_POLARITY = {
    "甲": "阳",
    "乙": "阴",
    "丙": "阳",
    "丁": "阴",
    "戊": "阳",
    "己": "阴",
    "庚": "阳",
    "辛": "阴",
    "壬": "阳",
    "癸": "阴",
}
_BRANCH_HIDDEN_STEMS = {
    "子": "癸",
    "丑": "己癸辛",
    "寅": "甲丙戊",
    "卯": "乙",
    "辰": "戊乙癸",
    "巳": "丙戊庚",
    "午": "丁己",
    "未": "己丁乙",
    "申": "庚壬戊",
    "酉": "辛",
    "戌": "戊辛丁",
    "亥": "壬甲",
}
_NON_ASSERTIVE_PREFIXES = (
    "不是",
    "并非",
    "不构成",
    "不存在",
    "没有",
    "未见",
    "不能视为",
    "不等于",
    "若",
    "如果",
    "如",
    "例如",
    "比如",
    "假设",
    "除非",
)
_NATAL_FACT_MODALITIES = {"asserted_natal_fact", "derived_natal_claim"}


def classify_claim_modality(*, text: str, start: int = 0) -> str:
    """Classify the clause containing a claim for Phase-0 fact review.

    This intentionally stays narrow. It is not a general Chinese parser; it only
    separates immutable natal assertions from epistemically different speech acts.
    """

    clause_start = max(text.rfind(token, 0, start) for token in ("。", "；", ";", "，", ",", "\n")) + 1
    clause_ends = [
        position
        for token in ("。", "；", ";", "，", ",", "\n")
        if (position := text.find(token, start)) >= 0
    ]
    clause_end = min(clause_ends) if clause_ends else len(text)
    clause = text[clause_start:clause_end].strip()
    prefix = text[clause_start:start]

    if _inside_quote(text=text, start=start) or re.search(r"(?:原文|有人|命理师|用户|他说|她说|其称)[：:]?[‘'\"“]", clause):
        return "quoted_claim"
    if "？" in clause or "?" in clause or re.search(r"(?:是否|能否|会否|会不会|有没有|何时|为何|为什么|哪一个)", clause):
        return "question"
    if re.search(r"(?:若|如果|假如|假设|除非|倘若)", prefix + clause):
        return "counterfactual"
    if re.search(r"(?:流年|大运|岁运|运年|逢|遇)[^。；，,]{0,24}(?:冲|合|刑|害|破|引动|激活)", clause) or re.search(
        r"(?:冲|合|刑|害|破|引动|激活)[^。；，,]{0,16}(?:流年|大运|岁运|运年)",
        clause,
    ):
        return "timing_condition"
    if re.search(r"(?:可能|或许|也许|候选|假说|倾向于|可考虑|尚待验证|待确认)", prefix + clause):
        return "hypothesis"
    if re.search(r"(?:因此|所以|由此|可见|据此|推得|说明)", prefix):
        return "derived_natal_claim"
    return "asserted_natal_fact"


def audit_professional_facts(
    *,
    text: str,
    world: ChartWorldInstance,
    claim_ref: str = "unscoped_claim",
) -> list[ProfessionalFactIssue]:
    """Annotate mechanically decidable Mingli fact conflicts without rewriting text."""

    issues = [
        *_element_cycle_issues(text=text, claim_ref=claim_ref),
        *_stem_identity_issues(text=text, claim_ref=claim_ref),
        *_branch_identity_issues(text=text, claim_ref=claim_ref),
        *_hidden_stem_issues(text=text, claim_ref=claim_ref),
        *_ten_god_issues(text=text, world=world, claim_ref=claim_ref),
        *_pillar_reference_issues(text=text, world=world, claim_ref=claim_ref),
    ]
    for message in _root_fact_conflicts(text=text, world=world):
        issues.append(
            _fact_issue(
                claim_ref=claim_ref,
                issue_type="root_strength_conflict",
                original_text=message,
                canonical_fact_ref="world:root_strength",
                modality="asserted_natal_fact",
            )
        )
    for message in _branch_relation_conflicts(text=text, world=world):
        unmodeled = message.startswith("地支关系未建模:")
        issues.append(
            _fact_issue(
                claim_ref=claim_ref,
                issue_type="branch_relation_unmodeled" if unmodeled else "branch_relation_conflict",
                original_text=message,
                canonical_fact_ref="world:branch_relations",
                modality="asserted_natal_fact",
                severity="warning" if unmodeled else "hard",
                disposition="annotate" if unmodeled else "suppress_from_projection",
            )
        )
    output: list[ProfessionalFactIssue] = []
    seen: set[str] = set()
    for issue in issues:
        if issue.issue_id not in seen:
            seen.add(issue.issue_id)
            output.append(issue)
    return output


def deterministic_fact_conflicts(*, text: str, world: ChartWorldInstance) -> list[str]:
    """Compatibility view over the structured professional fact auditor."""

    return _unique([
        issue.original_text
        for issue in audit_professional_facts(text=text, world=world)
    ])


def _element_cycle_issues(*, text: str, claim_ref: str) -> list[ProfessionalFactIssue]:
    output: list[ProfessionalFactIssue] = []
    pattern = r"([木火土金水])\s*(生|克制|克)\s*([木火土金水])"
    for match in re.finditer(pattern, text):
        if is_parallel_predicate_fragment(text=text, start=match.start(), end=match.end()):
            continue
        modality = classify_claim_modality(text=text, start=match.start())
        if modality not in _NATAL_FACT_MODALITIES:
            continue
        source, relation, target = match.group(1), match.group(2), match.group(3)
        canonical_target = _ELEMENT_GENERATES[source] if relation == "生" else _ELEMENT_CONTROLS[source]
        if target == canonical_target:
            continue
        canonical = f"{source}{'生' if relation == '生' else '克'}{canonical_target}"
        output.append(
            _fact_issue(
                claim_ref=claim_ref,
                issue_type="five_element_generation_direction" if relation == "生" else "five_element_control_direction",
                original_text=match.group(0),
                canonical_fact_ref=f"canonical:five_elements:{canonical}",
                modality=modality,
            )
        )
    return output


def is_parallel_predicate_fragment(*, text: str, start: int, end: int) -> bool:
    """Return true when a compact element substring crosses two predicates."""

    prefix = text[max(0, start - 10):start]
    suffix = text[end:end + 6]
    if prefix.endswith(("晦", "补", "暖", "助", "扶")):
        return True
    return prefix.endswith("受") and suffix.startswith(("耗", "泄", "制", "克", "生"))


def _stem_identity_issues(*, text: str, claim_ref: str) -> list[ProfessionalFactIssue]:
    output: list[ProfessionalFactIssue] = []
    pattern = rf"([{''.join(_STEM_ELEMENTS)}])(?:木|火|土|金|水)?\s*(?:为|是|属于|属)\s*(阴|阳)([木火土金水])"
    for match in re.finditer(pattern, text):
        modality = classify_claim_modality(text=text, start=match.start())
        if modality not in _NATAL_FACT_MODALITIES:
            continue
        stem, polarity, element = match.group(1), match.group(2), match.group(3)
        if polarity == _STEM_POLARITY[stem] and element == _STEM_ELEMENTS[stem]:
            continue
        output.append(
            _fact_issue(
                claim_ref=claim_ref,
                issue_type="stem_polarity_or_element_conflict",
                original_text=match.group(0),
                canonical_fact_ref=f"canonical:stem:{stem}:{_STEM_POLARITY[stem]}{_STEM_ELEMENTS[stem]}",
                modality=modality,
            )
        )
    return output


def _branch_identity_issues(*, text: str, claim_ref: str) -> list[ProfessionalFactIssue]:
    output: list[ProfessionalFactIssue] = []
    pattern = rf"([{_BRANCHES}])\s*(?:为|是|属于|属)\s*([木火土金水])"
    for match in re.finditer(pattern, text):
        modality = classify_claim_modality(text=text, start=match.start())
        if modality not in _NATAL_FACT_MODALITIES:
            continue
        branch, element = match.group(1), match.group(2)
        if element == _BRANCH_ELEMENTS[branch]:
            continue
        output.append(
            _fact_issue(
                claim_ref=claim_ref,
                issue_type="branch_element_conflict",
                original_text=match.group(0),
                canonical_fact_ref=f"canonical:branch:{branch}:{_BRANCH_ELEMENTS[branch]}",
                modality=modality,
            )
        )
    return output


def _hidden_stem_issues(*, text: str, claim_ref: str) -> list[ProfessionalFactIssue]:
    output: list[ProfessionalFactIssue] = []
    pattern = rf"([{_BRANCHES}])(?:中)?\s*藏(?:干)?(?:有|为|：|:)?\s*([{''.join(_STEM_ELEMENTS)}]+)"
    for match in re.finditer(pattern, text):
        modality = classify_claim_modality(text=text, start=match.start())
        if modality not in _NATAL_FACT_MODALITIES:
            continue
        branch, claimed = match.group(1), match.group(2)
        invalid = [stem for stem in claimed if stem not in _BRANCH_HIDDEN_STEMS[branch]]
        if not invalid:
            continue
        output.append(
            _fact_issue(
                claim_ref=claim_ref,
                issue_type="hidden_stem_conflict",
                original_text=match.group(0),
                canonical_fact_ref=f"canonical:hidden_stems:{branch}:{_BRANCH_HIDDEN_STEMS[branch]}",
                modality=modality,
            )
        )
    return output


def _ten_god_issues(*, text: str, world: ChartWorldInstance, claim_ref: str) -> list[ProfessionalFactIssue]:
    day_stem = world.pillars[2][0] if len(world.pillars) >= 3 and len(world.pillars[2]) >= 1 else ""
    if day_stem not in _STEM_ELEMENTS:
        return []
    ten_gods = "比肩|劫财|食神|伤官|偏财|正财|七杀|正官|偏印|正印"
    pattern = rf"([{''.join(_STEM_ELEMENTS)}])(?:木|火|土|金|水)?\s*(?:为|是|属于|对应|即)\s*({ten_gods})"
    output: list[ProfessionalFactIssue] = []
    for match in re.finditer(pattern, text):
        modality = classify_claim_modality(text=text, start=match.start())
        if modality not in _NATAL_FACT_MODALITIES:
            continue
        stem, claimed = match.group(1), match.group(2)
        canonical = _ten_god(day_stem=day_stem, other_stem=stem)
        if claimed == canonical:
            continue
        output.append(
            _fact_issue(
                claim_ref=claim_ref,
                issue_type="ten_god_mapping_conflict",
                original_text=match.group(0),
                canonical_fact_ref=f"canonical:ten_god:{day_stem}:{stem}:{canonical}",
                modality=modality,
            )
        )
    return output


def _pillar_reference_issues(*, text: str, world: ChartWorldInstance, claim_ref: str) -> list[ProfessionalFactIssue]:
    labels = {"年柱": 0, "月柱": 1, "日柱": 2, "时柱": 3}
    pattern = rf"(年柱|月柱|日柱|时柱)\s*(?:为|是|：|:)?\s*([{''.join(_STEM_ELEMENTS)}][{_BRANCHES}])"
    output: list[ProfessionalFactIssue] = []
    for match in re.finditer(pattern, text):
        modality = classify_claim_modality(text=text, start=match.start())
        if modality not in _NATAL_FACT_MODALITIES:
            continue
        label, claimed = match.group(1), match.group(2)
        index = labels[label]
        canonical = world.pillars[index] if len(world.pillars) > index else "missing"
        if claimed == canonical:
            continue
        output.append(
            _fact_issue(
                claim_ref=claim_ref,
                issue_type="pillar_reference_conflict",
                original_text=match.group(0),
                canonical_fact_ref=f"world:pillar:{label}:{canonical}",
                modality=modality,
            )
        )
    return output


def _ten_god(*, day_stem: str, other_stem: str) -> str:
    day_element = _STEM_ELEMENTS[day_stem]
    other_element = _STEM_ELEMENTS[other_stem]
    same_polarity = _STEM_POLARITY[day_stem] == _STEM_POLARITY[other_stem]
    if other_element == day_element:
        return "比肩" if same_polarity else "劫财"
    if _ELEMENT_GENERATES[day_element] == other_element:
        return "食神" if same_polarity else "伤官"
    if _ELEMENT_CONTROLS[day_element] == other_element:
        return "偏财" if same_polarity else "正财"
    if _ELEMENT_CONTROLS[other_element] == day_element:
        return "七杀" if same_polarity else "正官"
    return "偏印" if same_polarity else "正印"


def _fact_issue(
    *,
    claim_ref: str,
    issue_type: str,
    original_text: str,
    canonical_fact_ref: str,
    modality: str,
    severity: str = "hard",
    disposition: str = "suppress_from_projection",
) -> ProfessionalFactIssue:
    digest = sha256(
        f"{claim_ref}|{issue_type}|{original_text}|{canonical_fact_ref}|{modality}".encode("utf-8")
    ).hexdigest()[:16]
    return ProfessionalFactIssue(
        issue_id=f"pfi:{digest}",
        claim_ref=claim_ref,
        issue_type=issue_type,
        original_text=original_text,
        canonical_fact_ref=canonical_fact_ref,
        modality=modality,
        severity=severity,
        disposition=disposition,
    )


def repair_locked_fact_assertions(
    *,
    payload: dict[str, Any],
    world: ChartWorldInstance,
) -> tuple[dict[str, Any], list[str]]:
    """Repair wording governed by locked facts without choosing a Mingli hypothesis."""

    output = deepcopy(payload)
    repairs: list[str] = []

    def repair_value(value: Any) -> Any:
        if isinstance(value, str):
            repaired = _repair_locked_fact_text(text=value, world=world)
            if repaired != value:
                repairs.append(f"{value} -> {repaired}")
            return repaired
        if isinstance(value, list):
            return [repair_value(item) for item in value]
        return value

    def repair_fields(item: dict[str, Any], fields: tuple[str, ...]) -> None:
        for field in fields:
            if field in item:
                item[field] = repair_value(item[field])

    repair_fields(output, ("preview_line", "first_look", "whole_chart_thesis"))
    for item in output.get("salient_phenomena", []):
        repair_fields(item, ("observation", "why_it_matters"))
    selected_id = output.get("selected_hypothesis_id")
    for item in output.get("hypotheses", []):
        if item.get("hypothesis_id") == selected_id:
            repair_fields(item, ("name", "thesis"))
    repair_fields(
        output.get("work_path") or {},
        ("path_statement", "source", "transformations", "target", "body_function_relation"),
    )
    for item in output.get("useful_god_reasoning", []):
        repair_fields(item, ("candidate", "role", "why_useful"))
    for item in output.get("portrait", []):
        repair_fields(item, ("claim", "rationale"))
    for item in output.get("prior_predictions", []):
        repair_fields(item, ("claim", "why_predicted"))
    for domain_name in ("career", "wealth"):
        domain = output.get(domain_name) or {}
        repair_fields(domain, ("causal_chain", "stable_tendencies", "prior_directions"))
        for item in domain.get("assertions", []):
            repair_fields(item, ("claim", "rationale"))
    if "causal_chain" in output:
        repair_fields(output, ("causal_chain", "stable_tendencies", "prior_directions"))
        for item in output.get("assertions", []):
            repair_fields(item, ("claim", "rationale"))
    dual = output.get("dual_lens") or {}
    for item in dual.get("palace_observations", []):
        repair_fields(item, ("claim", "why_it_matters"))
    repair_fields(dual, ("agreements", "disagreements"))
    return output, _unique(repairs)


def _repair_locked_fact_text(*, text: str, world: ChartWorldInstance) -> str:
    repaired = text
    root_fact = next((fact for fact in world.facts if fact.category == "root_strength"), None)
    if root_fact and bool(root_fact.payload.get("has_root")):
        day_stem = str(root_fact.payload.get("day_stem") or "")
        day_element = str(root_fact.payload.get("day_element") or _STEM_ELEMENTS.get(day_stem, ""))
        named_day_master = re.escape(f"{day_stem}{day_element}") if day_stem and day_element else r"(?!)"
        subject = rf"(日主(?:{named_day_master})?|命主)"
        repaired = re.sub(
            rf"{subject}(?:完全|极度)?(?:无根|根气全无|没有(?:任何)?根气)",
            lambda match: f"{match.group(1)}根气受损、支撑有限",
            repaired,
        )

    chart_branches = {pillar[1] for pillar in world.pillars if len(pillar) >= 2}
    allowed = _allowed_branch_relations(world)
    for branch_a, branch_b, label, _ in [
        *_relation_claims_after_pair(repaired),
        *_relation_claims_between_pair(repaired),
    ]:
        relation = _relation_kind(label)
        pair = frozenset((branch_a, branch_b))
        if branch_a in chart_branches and branch_b in chart_branches:
            opposite = "harmony" if relation == "clash" else "clash" if relation == "harmony" else ""
            if pair not in allowed.get(relation, set()) and opposite and pair in allowed.get(opposite, set()):
                correct_label = "相合" if opposite == "harmony" else "相冲"
                compact = re.compile(rf"{re.escape(branch_a)}{re.escape(branch_b)}{re.escape(label)}")
                repaired = compact.sub(f"{branch_a}{branch_b}{correct_label}", repaired)
                decorated = re.compile(
                    rf"({re.escape(branch_a)}(?:木|火|土|金|水)?)[^。；，,{_BRANCHES}]{{0,4}}?"
                    rf"{re.escape(label)}[^。；，,{_BRANCHES}]{{0,4}}?"
                    rf"({re.escape(branch_b)}(?:木|火|土|金|水)?)"
                )
                repaired = decorated.sub(lambda match: f"{match.group(1)}与{match.group(2)}{correct_label}", repaired)
            elif pair not in allowed.get(relation, set()) and relation in {"clash", "harmony"}:
                element_a = _BRANCH_ELEMENTS[branch_a]
                element_b = _BRANCH_ELEMENTS[branch_b]
                if _ELEMENT_CONTROLS[element_a] == element_b:
                    neutral = f"{branch_a}{element_a}克制{branch_b}{element_b}"
                elif _ELEMENT_CONTROLS[element_b] == element_a:
                    neutral = f"{branch_b}{element_b}克制{branch_a}{element_a}"
                else:
                    neutral = f"{branch_a}、{branch_b}同现"
                compact = re.compile(rf"{re.escape(branch_a)}{re.escape(branch_b)}{re.escape(label)}")
                repaired = compact.sub(neutral, repaired)
                decorated = re.compile(
                    rf"({re.escape(branch_a)}(?:木|火|土|金|水)?)[^。；，,{_BRANCHES}]{{0,4}}?"
                    rf"{re.escape(label)}[^。；，,{_BRANCHES}]{{0,4}}?"
                    rf"({re.escape(branch_b)}(?:木|火|土|金|水)?)"
                )
                repaired = decorated.sub(neutral, repaired)
            continue
        token = re.escape(f"{branch_a}{branch_b}{label}")
        variant_pattern = rf"(?:且|并)?存在[‘“]?{token}[’”]?(?:的)?变体逻辑（此处为([^）]+)）"
        repaired = re.sub(variant_pattern, lambda match: f"；可观察到{match.group(1)}", repaired)
    return repaired


def assertive_claim_text(payload: dict[str, Any]) -> str:
    """Collect claims while excluding alternatives, conditions and Probe questions."""

    values: list[str] = []

    def add(value: Any) -> None:
        if isinstance(value, str) and value.strip():
            values.append(value)
        elif isinstance(value, list):
            for item in value:
                add(item)

    add(payload.get("preview_line"))
    add(payload.get("first_look"))
    add(payload.get("whole_chart_thesis"))
    for item in payload.get("salient_phenomena", []):
        add(item.get("observation"))
        add(item.get("why_it_matters"))
    selected_id = payload.get("selected_hypothesis_id")
    selected = next((item for item in payload.get("hypotheses", []) if item.get("hypothesis_id") == selected_id), None)
    if selected:
        add(selected.get("name"))
        add(selected.get("thesis"))
    work = payload.get("work_path") or {}
    for key in ("path_statement", "source", "transformations", "target", "body_function_relation"):
        add(work.get(key))
    for item in payload.get("useful_god_reasoning", []):
        add(item.get("candidate"))
        add(item.get("role"))
        add(item.get("why_useful"))
    for item in payload.get("portrait", []):
        add(item.get("claim"))
        add(item.get("rationale"))
    for item in payload.get("prior_predictions", []):
        add(item.get("claim"))
        add(item.get("why_predicted"))
    domains = [payload] if "causal_chain" in payload else [payload.get(name) or {} for name in ("career", "wealth")]
    for domain in domains:
        for key in ("causal_chain", "stable_tendencies", "prior_directions"):
            add(domain.get(key))
        for item in domain.get("assertions", []):
            add(item.get("claim"))
            add(item.get("rationale"))
    dual = payload.get("dual_lens") or payload
    for item in dual.get("palace_observations", []):
        add(item.get("claim"))
        add(item.get("why_it_matters"))
    add(dual.get("agreements"))
    add(dual.get("disagreements"))
    return "\n".join(values)


def _root_fact_conflicts(*, text: str, world: ChartWorldInstance) -> list[str]:
    root_fact = next((fact for fact in world.facts if fact.category == "root_strength"), None)
    if root_fact is None or "has_root" not in root_fact.payload:
        return []
    has_root = bool(root_fact.payload["has_root"])
    day_stem = str(root_fact.payload.get("day_stem") or "")
    day_element = str(root_fact.payload.get("day_element") or _STEM_ELEMENTS.get(day_stem, ""))
    root_branches = [str(item.get("branch") or "") for item in root_fact.payload.get("root_sources", [])]
    # A bare stem is not a safe subject: another pillar can expose the same stem.
    named_day_master = re.escape(f"{day_stem}{day_element}") if day_stem and day_element else r"(?!)"
    subject = rf"(?:日主|命主|{named_day_master})"
    unrooted = any(
        _has_asserted_match(text, pattern)
        for pattern in (
            rf"{subject}[^。；，,]{{0,12}}(?:完全|极度)?(?:无根|根气全无|没有(?:任何)?根气)",
        )
    )
    rooted_patterns = [
        rf"{subject}[^。；，,]{{0,12}}(?:(?<!无)强根|通根|坐根|(?<!没)有根|根气充足)",
        *[
            rf"(?:日支|月支|年支|时支)?{re.escape(branch)}(?:木|火|土|金|水)?[^。；，,]{{0,8}}(?:(?<!无)强根|为根|根气)"
            for branch in root_branches
            if branch
        ],
    ]
    rooted = any(_has_asserted_match(text, pattern) for pattern in rooted_patterns)
    errors: list[str] = []
    if unrooted and rooted:
        errors.append("根气表述自相矛盾:同一段同时断言有根与无根")
    if has_root and unrooted:
        errors.append("根气事实冲突:账本存在同类藏干根，不能断言地支无根")
    if not has_root and rooted:
        errors.append("根气事实冲突:账本未发现同类藏干根，不能断言已经通根或有强根")
    return errors


def _branch_relation_conflicts(*, text: str, world: ChartWorldInstance) -> list[str]:
    chart_branches = {pillar[1] for pillar in world.pillars if len(pillar) >= 2}
    allowed = _allowed_branch_relations(world)
    claims = [
        *_relation_claims_after_pair(text),
        *_relation_claims_between_pair(text),
    ]
    errors: list[str] = []
    seen: set[tuple[str, str, str]] = set()
    for branch_a, branch_b, label, start in claims:
        key = tuple(sorted((branch_a, branch_b))) + (label,)
        if (
            key in seen
            or _is_non_assertive(text=text, start=start)
            or _relation_has_recent_timing_scope(
                text=text,
                start=start,
                branch_a=branch_a,
                branch_b=branch_b,
            )
        ):
            continue
        seen.add(key)
        relation = _relation_kind(label)
        if branch_a not in chart_branches or branch_b not in chart_branches:
            errors.append(f"地支关系冲突:盘中不存在{branch_a}{branch_b}{label}所需地支")
            continue
        if frozenset((branch_a, branch_b)) not in allowed.get(relation, set()):
            if relation in {"clash", "harmony"}:
                errors.append(f"地支关系冲突:确定性关系表不支持{branch_a}{branch_b}{label}")
            else:
                errors.append(f"地支关系未建模:当前世界账本尚未覆盖{branch_a}{branch_b}{label}")
    return errors


def _relation_has_recent_timing_scope(*, text: str, start: int, branch_a: str, branch_b: str) -> bool:
    """Recover timing scope split into an adjacent claim/rationale field."""

    context = text[max(0, start - 280):start]
    if not re.search(r"(?:流年|大运|岁运|运年|逢|遇)", context):
        return False
    return bool(
        re.search(rf"(?:{re.escape(branch_a)}|{re.escape(branch_b)})(?:年|运)", context)
        or re.search(
            rf"(?:逢|遇)[^。；;]{{0,48}}(?:{re.escape(branch_a)}|{re.escape(branch_b)})",
            context,
        )
    )


def _allowed_branch_relations(world: ChartWorldInstance) -> dict[str, set[frozenset[str]]]:
    output: dict[str, set[frozenset[str]]] = {
        "clash": set(),
        "harmony": set(),
        "triple": set(),
        "half": set(),
        "punishment": set(),
        "harm": set(),
        "break": set(),
        "dark_harmony": set(),
    }
    for fact in world.facts:
        if fact.category == "branch_relations":
            for row in fact.payload.get("relations", []):
                relation = {"clash": "clash", "harmony": "harmony"}.get(str(row.get("type") or ""))
                branch_a = str(row.get("branch_a") or "")
                branch_b = str(row.get("branch_b") or "")
                if relation and branch_a and branch_b:
                    output[relation].add(frozenset((branch_a, branch_b)))
        if fact.category != "graph_relation":
            continue
        relation = {
            "clashes": "clash",
            "harmonizes": "harmony",
            "forms_triple_combination": "triple",
            "forms_half_combination": "half",
        }.get(str(fact.payload.get("relation") or ""))
        branch_a = str(fact.payload.get("from") or "")
        branch_b = str(fact.payload.get("to") or "")
        if relation and branch_a in _BRANCHES and branch_b in _BRANCHES:
            output[relation].add(frozenset((branch_a, branch_b)))
    return output


def _relation_claims_after_pair(text: str) -> list[tuple[str, str, str, int]]:
    branch = rf"([{_BRANCHES}])(?:木|火|土|金|水)?"
    patterns = (
        # Compact professional notation: 辰戌冲、午申暗合、卯未半合。
        rf"{branch}[、/]?{branch}(?:无礼之|恃势之|无恩之)?(?:发生|形成|构成|呈现|存在)?({_RELATION_TOKEN})",
        # Natural language: 年支申金与日支寅木发生冲克。
        rf"{branch}[^。；，,{_BRANCHES}]{{0,12}}?(?:与|和|同){branch}[^。；，,{_BRANCHES}]{{0,8}}?(?:发生|形成|构成|呈现|存在|出现)?({_RELATION_TOKEN})",
    )
    output: list[tuple[str, str, str, int]] = []
    for pattern in patterns:
        output.extend(
            (match.group(1), match.group(2), match.group(3), match.start())
            for match in re.finditer(pattern, text)
        )
    return output


def _relation_claims_between_pair(text: str) -> list[tuple[str, str, str, int]]:
    # Do not start in the middle of compact notation such as 辰戌冲 or 午未合。
    pattern = rf"(?<![{_BRANCHES}])([{_BRANCHES}])(?:木|火|土|金|水)?[^。；，,{_BRANCHES}]{{0,4}}?({_RELATION_TOKEN})[^。；，,{_BRANCHES}]{{0,4}}?([{_BRANCHES}])(?:木|火|土|金|水)?"
    return [(match.group(1), match.group(3), match.group(2), match.start()) for match in re.finditer(pattern, text)]


def _relation_kind(label: str) -> str:
    if "暗合" in label:
        return "dark_harmony"
    if "三合" in label:
        return "triple"
    if "半合" in label:
        return "half"
    if "冲" in label:
        return "clash"
    if "合" in label:
        return "harmony"
    if "刑" in label:
        return "punishment"
    if "害" in label:
        return "harm"
    return "break"


def _has_asserted_match(text: str, pattern: str) -> bool:
    return any(
        not _is_non_assertive(text=text, start=match.start())
        and not re.search(r"(?:并非|不是|不等于|不能视为|不构成|未见)(?:完全|极度)?(?:无根|根气全无)", match.group())
        for match in re.finditer(pattern, text)
    )


def _is_non_assertive(*, text: str, start: int) -> bool:
    clause_start = max(text.rfind(token, 0, start) for token in ("。", "；", ";", "，", ",", "\n")) + 1
    prefix = text[clause_start:start]
    clause_ends = [position for token in ("。", "；", ";", "，", ",", "\n") if (position := text.find(token, start)) >= 0]
    clause_end = min(clause_ends) if clause_ends else len(text)
    clause = text[clause_start:clause_end]
    if any(token in prefix for token in _NON_ASSERTIVE_PREFIXES):
        return True
    # A natal fact checker cannot judge a relation introduced only as a future,
    # luck-cycle, or counterfactual condition. Those claims belong to timing or
    # epistemic review, not to the immutable chart-relation ledger.
    if classify_claim_modality(text=text, start=start) not in _NATAL_FACT_MODALITIES:
        return True
    # JSON-backed claims often contain a timing condition before a Chinese comma,
    # followed by the concrete relation in the next clause.  Keep that relation
    # inside the timing modality instead of reclassifying the tail as a natal fact.
    sentence_start = max(text.rfind(token, 0, start) for token in ("。", "；", ";", "\n")) + 1
    sentence_prefix = text[sentence_start:start]
    if re.search(
        r"(?:若|如果|假如|假设|除非|倘若|流年|大运|岁运|运年|逢|遇)[^。；;\n]{0,96}$",
        sentence_prefix,
    ):
        return True
    return bool(
        re.search(r"(?:流年|大运|岁运|运年|逢|遇|例如|比如|如)[^。；，,]{0,18}(?:冲|合|刑|害|破)", clause)
        or re.search(r"(?:冲|合|刑|害|破)[^。；，,]{0,12}(?:流年|大运|岁运|可能|条件|假设)", clause)
    )


def _inside_quote(*, text: str, start: int) -> bool:
    left_double = max(text.rfind("“", 0, start + 1), text.rfind('"', 0, start + 1))
    right_double = min(
        [position for token in ("”", '"') if (position := text.find(token, start)) >= 0],
        default=-1,
    )
    left_single = max(text.rfind("‘", 0, start + 1), text.rfind("'", 0, start + 1))
    right_single = min(
        [position for token in ("’", "'") if (position := text.find(token, start)) >= 0],
        default=-1,
    )
    return (left_double >= 0 and right_double >= start) or (left_single >= 0 and right_single >= start)


def _unique(values: list[str]) -> list[str]:
    output: list[str] = []
    for value in values:
        if value not in output:
            output.append(value)
    return output
