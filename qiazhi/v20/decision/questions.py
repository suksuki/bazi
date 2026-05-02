from __future__ import annotations

import hashlib
from dataclasses import replace
import re

from v20.answer.measurement_policy import (
    domain_label,
    feature_label,
    feature_public_summary,
    measurement_stage,
)
from v20.features.schema import FeatureLayer
from v20.interaction.question_ranker import QuestionRankingPolicy, rank_question_rows
from v20.interaction.questions import HOOK_DOMAIN_PREFERENCE, QUESTION_LABELS, QuestionCandidate
from v20.measurement.domain_alignment import align_question_candidate
from v20.measurement.dimensions import dimension_payload
from v20.core.schemas import TimeContext


QUESTION_KEY_BY_DOMAIN = {
    "strength": "q_strength_assessment",
    "wealth": "q_income_stability",
    "career": "q_career_structure",
    "ten_god": "q_ten_god_focus",
    "branch": "q_branch_relation_detail",
    "time": "q_time_layer_context",
    "element": "q_element_balance",
    "useful_god": "q_useful_god_candidates",
    "pattern": "q_pattern_structure",
    "relationship": "q_relationship_structure",
    "health": "q_health_balance_boundary",
}

FEATURE_MATERIAL_MAX = 2

_TECHNICAL_TERM_HINTS = (
    "证据",
    "evidence.",
    "decision.",
    "rulespec",
    "rule.",
    "应如何进入八字测算",
    "需复核",
    "条件成立",
    "材料",
    "反证",
    "边界",
    "纳入裁决",
    "先复核",
    "需要哪些证据",
    "Pattern review index",
    "Pattern",
    "review index",
    "ten-god",
    "ten god",
    "chart-specific",
    "focus is",
    "available",
)

CONTROL_DOMAIN = {
    "control.day_master_strength": "strength",
    "control.shang_guan_jian_guan": "career",
    "control.wealth_capacity": "wealth",
    "control.pattern_status": "pattern",
}


def _question_id(
    question_key: str,
    title: str,
    domain: str,
    source_feature_ids: tuple[str, ...],
    source_decision: dict[str, object] | None,
    extra_signature: str = "",
) -> str:
    source_key = str(source_decision.get("decision_key", "")) if isinstance(source_decision, dict) else ""
    source_rule = str(source_decision.get("rule_key", "")) if isinstance(source_decision, dict) else ""
    signature = "|".join(
        (
            question_key,
            domain,
            title,
            ";".join(source_feature_ids),
            source_key,
            source_rule,
            extra_signature,
        )
    )
    digest = hashlib.blake2s(signature.encode("utf-8"), digest_size=5).hexdigest()
    return f"{question_key}:{digest}"


def _decision_feature_materials(decision: dict[str, object], feature_layer: FeatureLayer) -> tuple[str, ...]:
    feature_ids = tuple(str(row) for row in decision.get("feature_ids", ()) if str(row))
    if not feature_ids:
        return ()
    materials: list[str] = []
    for feature in feature_layer.features:
        if feature.feature_id not in feature_ids:
            continue
        for ref in getattr(feature, "evidence_refs", ()):
            token = _clean_question_token(ref.title)
            if token and token not in materials:
                materials.append(token)
            if len(materials) >= FEATURE_MATERIAL_MAX:
                return tuple(materials)
        title = _clean_question_token(str(feature.title))
        if title and title not in materials:
            materials.append(title)
            if len(materials) >= FEATURE_MATERIAL_MAX:
                return tuple(materials)
    return tuple(materials)


def _append_focus_tail(title: str, materials: tuple[str, ...]) -> str:
    if not materials:
        return title
    suffix = "；".join(materials)
    if suffix in title:
        return title
    return f"{title}（重点看：{suffix}）"


def _attach_question_id(
    candidate: QuestionCandidate,
    source_decision: dict[str, object] | None = None,
) -> QuestionCandidate:
    return replace(
        candidate,
        question_id=_question_id(
            candidate.question_key,
            candidate.title,
            candidate.domain,
            candidate.source_feature_ids,
            source_decision,
        ),
    )

LATENT_SCENARIO_DOMAIN = {
    "latent.wealth_change": "wealth",
    "latent.career_transition": "career",
    "latent.relationship_shift": "relationship",
    "latent.relocation_environment": "time",
    "latent.stress_recovery": "health",
    "latent.action_result": "strength",
}


def recommend_decision_questions(
    decision_report: dict[str, object],
    feature_layer: FeatureLayer,
    *,
    time_context: TimeContext | None = None,
    practitioner_selections: tuple[dict[str, object], ...] = (),
    latent_event_answers: tuple[dict[str, object], ...] = (),
    limit: int = 12,
) -> tuple[QuestionCandidate, ...]:
    rows = []
    rows.extend(_mainline_questions(decision_report, feature_layer))
    rows.extend(_feature_hook_questions(decision_report, feature_layer))
    for decision in decision_report.get("decisions", ()):
        if not isinstance(decision, dict):
            continue
        domain = str(decision.get("domain", ""))
        key = QUESTION_KEY_BY_DOMAIN.get(domain)
        if not key:
            continue
        rows.extend(
            _decision_questions(
                decision=decision,
                feature_layer=feature_layer,
                domain=domain,
                include_variant=True,
            )
        )
        rows.extend(_secondary_questions(decision, feature_layer))
        rows.extend(_knowledge_rule_questions(decision, feature_layer))
    rows.extend(_time_context_questions(decision_report, feature_layer, time_context or TimeContext()))
    rows.extend(_practitioner_selection_questions(practitioner_selections, decision_report, feature_layer))
    rows.extend(_latent_event_questions(latent_event_answers, decision_report, feature_layer))
    if not rows:
        rows = [_fallback_question(feature_layer)]
    rows = _dedupe_questions(rows)
    ordered = tuple(
        rank_question_rows(
            tuple(rows),
            QuestionRankingPolicy(
                policy_id="v20.question_ranking.dynamic_decision",
                source="dynamic_rule_decisions",
                status="active",
                max_adjustment=0.12,
            ),
        )
    )
    ordered = _limit_question_diversity(ordered)
    if not ordered:
        ordered = (_fallback_question(feature_layer),)
    return ordered[:limit]


def _dedupe_questions(rows: list[QuestionCandidate]) -> list[QuestionCandidate]:
    by_signature: dict[str, QuestionCandidate] = {}
    for row in rows:
        signature = _question_signature(row.question_key, row.title)
        current = by_signature.get(signature)
        if current is None or row.score > current.score:
            by_signature[signature] = row
    return list(by_signature.values())


def _limit_question_diversity(
    rows: tuple[QuestionCandidate, ...],
    *,
    per_domain_limit: int = 2,
    per_key_limit: int = 8,
) -> tuple[QuestionCandidate, ...]:
    kept: list[QuestionCandidate] = []
    domain_count: dict[str, int] = {}
    key_count: dict[str, int] = {}
    unique: set[str] = set()
    for row in rows:
        uid = row.question_id or row.question_key
        if uid in unique:
            continue
        if per_domain_limit and domain_count.get(row.domain, 0) >= per_domain_limit:
            continue
        if per_key_limit and key_count.get(row.question_key, 0) >= per_key_limit:
            continue
        kept.append(row)
        unique.add(uid)
        domain_count[row.domain] = domain_count.get(row.domain, 0) + 1
        key_count[row.question_key] = key_count.get(row.question_key, 0) + 1
    return tuple(kept)


def _feature_hook_questions(
    decision_report: dict[str, object],
    feature_layer: FeatureLayer,
    *,
    max_per_feature: int = 2,
    max_total: int = 18,
) -> list[QuestionCandidate]:
    rows: list[QuestionCandidate] = []
    if not feature_layer.features:
        return rows
    decisions = tuple(row for row in decision_report.get("decisions", ()) if isinstance(row, dict))
    decisions_by_domain: dict[str, list[dict[str, object]]] = {}
    for decision in decisions:
        domain = str(decision.get("domain", ""))
        if not domain:
            continue
        decisions_by_domain.setdefault(domain, []).append(decision)

    for feature in sorted(
        feature_layer.features,
        key=lambda row: (float(row.confidence or 0.0), len(getattr(row, "evidence_refs", ())), str(row.readiness)),
        reverse=True,
    ):
        if len(rows) >= max_total:
            break
        feature_id = str(getattr(feature, "feature_id", ""))
        feature_domain = str(getattr(feature, "domain", ""))
        source_decision = _source_decision_for_feature(feature_id, feature_domain, decisions_by_domain, decisions)
        hooks = tuple(str(row) for row in getattr(feature, "question_hooks", ()) if str(row))
        if not hooks:
            continue
        material = _feature_material_label(feature)
        for index, hook in enumerate(hooks[:max_per_feature]):
            if len(rows) >= max_total:
                break
            question_key = str(hook).strip()
            if not question_key:
                continue
            question_domain = HOOK_DOMAIN_PREFERENCE.get(question_key, feature_domain)
            if not question_domain:
                question_domain = feature_domain
            score = round(float(feature.confidence or 0.0) + 0.05 - index * 0.02, 3)
            if source_decision is not None:
                score = round(score + _base_question_score(source_decision) * 0.04, 3)
            title = _feature_hook_question_title(question_key, material, feature)
            aligned = _aligned(
                _attach_question_id(
                    QuestionCandidate(
                        question_key=question_key,
                        title=title,
                        domain=question_domain,
                        score=score,
                        source_feature_ids=(feature_id,) if feature_id else _feature_ids(source_decision or {}, feature_layer, question_domain),
                        boundary=_boundary(question_domain),
                        measurement_topic=domain_label(question_domain),
                        measurement_stage=measurement_stage(question_domain),
                        **dimension_payload(question_domain),
                    ),
                    source_decision=source_decision,
                )
            )
            if aligned:
                rows.append(aligned)
    return rows


def _source_decision_for_feature(
    feature_id: str,
    feature_domain: str,
    decisions_by_domain: dict[str, list[dict[str, object]]],
    all_decisions: tuple[dict[str, object], ...],
) -> dict[str, object] | None:
    if feature_id:
        for row in decisions_by_domain.get(feature_domain, ()):
            if feature_id in tuple(str(item) for item in row.get("feature_ids", ())):
                return row
        for row in all_decisions:
            if feature_id in tuple(str(item) for item in row.get("feature_ids", ())):
                return row
    rows = decisions_by_domain.get(feature_domain, ())
    if rows:
        return rows[0]
    return all_decisions[0] if all_decisions else None


def _feature_hook_question_title(question_key: str, material: str, feature: object) -> str:
    hook = str(question_key).strip()
    if not hook:
        return ""
    label = QUESTION_LABELS.get(hook, hook)
    stem = str(label).rstrip("？?")
    if material and material not in stem:
        return f"{material}，{stem}"
    feature_title = _clean_question_token(str(getattr(feature, "title", "")))
    if feature_title and feature_title not in stem:
        return f"{feature_title}，{stem}"
    return stem


def _feature_material_label(feature: object) -> str:
    raw = [
        feature_label(feature),
        feature_public_summary(feature),
        str(getattr(feature, "title", "")),
        str(getattr(feature, "boundary", "")),
    ]
    materials: list[str] = []
    for item in raw:
        token = _clean_question_token(item)
        if (
            token
            and _contains_chinese(token)
            and not re.search(r"\d", token)
            and token not in materials
        ):
            materials.append(token)
    if not materials:
        return ""
    return _clip_text(materials[0], 18)


def resolve_requested_question(
    questions: tuple[QuestionCandidate, ...],
    question_key: str,
    question_id: str,
    feature_layer: FeatureLayer,
) -> QuestionCandidate:
    if question_id:
        for question in questions:
            if question.question_id == question_id:
                return question
    if question_key:
        for question in questions:
            if question.question_key == question_key:
                return question
        explicit = _explicit_question(question_key, feature_layer)
        if explicit is not None:
            return explicit
    if questions:
        return questions[0]
    return _fallback_question(feature_layer)


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


def _is_rulespec_decision(decision: dict[str, object]) -> bool:
    decision_key = str(decision.get("decision_key", ""))
    rule_key = str(decision.get("rule_key", ""))
    return (
        decision_key.startswith("decision.rulespec.")
        or ".rulespec." in decision_key
        or rule_key.startswith("rule.l")
    )


def _rulespec_rules_text(decision: dict[str, object]) -> str:
    for seed in decision.get("question_seeds", ()):
        candidate = _clean_question_token(str(seed))
        if candidate:
            return candidate
    label = str(decision.get("label", "")).strip()
    if label:
        return _clean_question_token(label)
    return ""


def _rulespec_domain_template(domain: str) -> str:
    if domain == "strength":
        return "日主强弱这条主线先看承载、泄耗和财印关系。"
    if domain == "wealth":
        return "财运主线先看承载、机会与财星通道。"
    if domain == "career":
        return "事业主线先看官星、伤官、印星谁更先起效？"
    if domain == "ten_god":
        return "十神主线先看明透与藏干的先后。"
    if domain == "useful_god":
        return "用神方向先看扶身、泄秀还是财星通道？"
    if domain == "pattern":
        return "格局主线先复核哪一段关键条件？"
    if domain == "branch":
        return "地支互动主线先看冲合刑害哪个先牵起？"
    if domain == "time":
        return "时间层先看哪条关系先牵动？"
    if domain == "relationship":
        return "关系主线先看互动、承接还是约束？"
    if domain == "health":
        return "健康主线先看五行偏枯的承压点。"
    if domain == "element":
        return "五行主线先看偏枯与平衡压力。"
    return "先从这条主线的结构证据入手。"


def _rulespec_mainline_template(domain: str) -> str:
    if domain == "strength":
        return "日主强弱先看承载与泄耗？"
    if domain == "wealth":
        return "财运主线先看承接后看机会与通道？"
    if domain == "career":
        return "事业先看官星、伤官与印星谁主导？"
    if domain == "ten_god":
        return "十神结构先看明透或藏干？"
    if domain == "pattern":
        return "格局先复核哪些关键条件？"
    if domain == "branch":
        return "先看地支冲合刑害中的主要作用？"
    if domain == "time":
        return "先看大运流年是先触发哪条关系？"
    if domain == "useful_god":
        return "先看用神扶身、泄秀还是财星通道？"
    if domain == "relationship":
        return "关系先看互动、承接还是约束？"
    if domain == "health":
        return "健康先看五行平衡边界吗？"
    if domain == "element":
        return "五行先看偏向与压力？"
    return "这条主线先从哪些结构切入？"


def _question_title(decision: dict[str, object], feature_layer: FeatureLayer) -> str:
    label = str(decision.get("label", "命理结构"))
    domain = str(decision.get("domain", ""))
    rule_key = str(decision.get("rule_key", ""))
    base = ""
    if rule_key == "rule.strength.capacity":
        status = str(decision.get("status", ""))
        if status == "needs_support":
            base = "日主需要扶身时，先看印星、比劫还是通关？"
        elif status == "borderline":
            base = "日主强弱接近分界时，先比较哪类证据？"
        elif status == "supported":
            base = "日主有支撑后，适合先看泄秀、财星还是官杀？"
        else:
            base = "这个八字日主偏强还是偏弱，适合先看什么？"
    elif rule_key == "rule.wealth.material":
        base = "财运主要从哪些位置和十神线索看？"
    elif rule_key == "rule.wealth.capacity_gate":
        base = "财星可见时，日主能不能承接？"
    elif rule_key == "rule.wealth.peer_competition":
        base = "财运上先看机会，还是先看比劫竞争和承载力？"
    elif rule_key == "rule.career.resource_buffer":
        base = "事业压力中，印星能不能形成缓冲？"
    elif rule_key == "rule.ten_god.source_layers":
        base = "明透和藏干里，哪些十神最值得先看？"
    elif rule_key == "rule.element.distribution":
        base = "五行偏向会让这个盘更需要哪种平衡？"
    elif rule_key == "rule.useful_god.candidate_gate":
        base = ""
        if "扶身" in label:
            base = "用神方向要先扶身，还是另有通关路径？"
        elif "泄秀" in label:
            base = "用神方向适合先看泄秀还是财星通道？"
        elif "财星通道" in label:
            base = "用神方向能不能走财星通道？"
        elif "官杀约束" in label:
            base = "用神方向要不要先看官杀约束？"
        elif "扶泄裁决" in label:
            base = "用神方向先扶身还是先泄秀？"
        else:
            base = "这个盘下一步适合先找哪类用神方向？"
    elif rule_key == "rule.pattern.review_gate":
        if "墓库藏气" in label:
            base = "格局判断要先复核哪一处墓库藏气？"
        else:
            base = "格局复核时先看月令、透干还是十神组合？"
    elif rule_key == "rule.ten_god.shang_guan_jian_guan":
        status = str(decision.get("status", ""))
        if status == "weakened_by_resource":
            base = "伤官见官是否被印星缓冲？"
        else:
            base = "伤官见官会怎样影响事业表达和规则？"
    elif rule_key == "rule.ten_god.guan_sha_mixed":
        base = "事业压力来自规则、竞争，还是角色混杂？"
    elif rule_key == "rule.ten_god.output_to_wealth":
        base = "食伤输出能不能形成财运通道？"
    elif rule_key == "rule.wealth.output_wealth_capacity_chain":
        if "承载关" in label:
            base = "食伤生财时，日主承接够不够？"
        elif "承载需裁决" in label:
            base = "食伤生财要先看承载还是通道？"
        else:
            base = "食伤生财能否形成稳定财星通道？"
    elif rule_key == "rule.career.output_authority_resource_chain":
        base = "事业上官星、伤官和印星谁是主导？"
    elif rule_key == "rule.branch.relations":
        base = "地支冲合刑害会先影响哪一类事情？"
    elif rule_key == "rule.relationship.interaction_projection":
        base = "关系结构里更明显的是互动、约束还是承接？"
    elif rule_key == "rule.health.balance_boundary":
        base = "五行偏枯主要提示哪种平衡压力？"
    elif rule_key == "rule.time.trigger":
        base = "流年大运会先牵动事业、财运还是关系？"
    elif domain == "strength":
        base = "先看日主强弱与承载力吗？"
    elif domain == "wealth":
        base = "财运主要从哪些命局线索看？"
    elif domain == "career":
        base = f"{label}是否会成为事业主线？"
    elif domain == "branch":
        base = "地支冲合刑害会先影响哪一类事情？"
    elif domain == "time":
        base = "流年大运会先牵动哪一类事情？"

    if rule_key == "rule.useful_god.candidate_gate":
        return base or "用神方向要先看扶身、泄秀还是财星通道？"

    if not base:
        if _is_rulespec_decision(decision):
            base = _rulespec_rules_text(decision)
            if base:
                base = _inject_decision_focus(base, decision, feature_layer)
            else:
                base = _rulespec_domain_template(domain)
        else:
            if domain:
                base = f"{domain_label(domain)}的结构要先在哪个入口读？"
            else:
                base = f"{label}应如何进入八字测算？"
    if "规则" in str(base):
        if domain == "useful_god":
            base = "用神方向先看扶身、泄秀还是财星？"
        elif domain == "pattern":
            base = "格局复核先看月令、透干、十神组合？"
        elif domain == "strength":
            base = "先看日主强弱与承载力吗？"
        elif domain == "wealth":
            base = "财运先看材料来源、承接与通道。"
        elif domain == "career":
            base = "事业主线先看官星、伤官与印星谁更关键？"
        elif domain == "ten_god":
            base = "先看十神来源与明藏关系。"
        elif domain == "branch":
            base = "地支冲合刑害谁更先起效？"
        else:
            base = f"{label}该如何进入测算？"
    seed = _decision_question_seed(decision)
    if seed and seed == base:
        return base
    return _inject_decision_focus(base, decision, feature_layer)


def _contains_chinese(value: str) -> bool:
    return any("\u4e00" <= char <= "\u9fff" for char in str(value))


def _clean_question_token(raw: str) -> str:
    text = str(raw or "").strip()
    if not text:
        return ""
    if not _contains_chinese(text):
        return ""
    if any(token in text for token in _TECHNICAL_TERM_HINTS):
        return ""
    if "规则" in text:
        return ""
    text = text.replace("应如何进入八字测算", "先看哪些命理线索")
    text = text.replace("条件成立", "")
    text = text.replace("需复核", "先复核")
    text = text.replace("材料更关键", "关键条件")
    text = text.replace("  ", " ").strip()
    return text.strip(" ，，。；;：:")


def _decision_questions(
    *,
    decision: dict[str, object],
    feature_layer: FeatureLayer,
    domain: str,
    include_variant: bool,
) -> list[QuestionCandidate]:
    key = QUESTION_KEY_BY_DOMAIN.get(domain, "")
    if not key:
        return []
    rule_key = str(decision.get("rule_key", ""))
    if re.match(r"^rule\.l\d+\.", rule_key):
        return []
    base_score = _base_question_score(decision)
    base_title = _question_title(decision, feature_layer)
    rows = [_make_question_row(
        question_key=key,
        title=base_title,
        domain=domain,
        score=base_score,
        decision=decision,
        feature_layer=feature_layer,
    )]
    if include_variant:
        variant_title = _materialized_question_title(decision, domain, feature_layer)
        if variant_title and variant_title != base_title:
            rows.append(_make_question_row(
                question_key=key,
                title=variant_title,
                domain=domain,
                score=round(base_score - 0.03, 3),
                decision=decision,
                feature_layer=feature_layer,
            ))
    return [row for row in rows if row is not None]


def _base_question_score(decision: dict[str, object]) -> float:
    return round(
        float(decision.get("score", 0.0))
        + _role_boost(str(decision.get("role", "")))
        + _rulespec_question_adjustment(decision)
        + _state_boost(str(decision.get("status", ""))),
        3,
    )


def _materialized_question_title(
    decision: dict[str, object],
    domain: str,
    feature_layer: FeatureLayer,
) -> str:
    digest = _inject_decision_focus(_feature_digest(decision, feature_layer), decision, feature_layer, prefer_front=True)
    if not digest:
        return ""
    if domain == "strength":
        return f"{digest}更突出时，先看日主承载与泄耗主次。"
    if domain == "wealth":
        return f"{digest}明显时，财运先看机会、承载与通道关系。"
    if domain == "career":
        return f"{digest}更明显时，事业先分官星、伤官、印星先后。"
    if domain == "ten_god":
        return f"{digest}比较突出时，先看十神是“明透”还是“藏干”线。"
    if domain == "element":
        return f"{digest}偏向明显时，五行平衡先看哪边压力更大？"
    if domain == "branch":
        return f"{digest}先触发时，地支互动优先看冲合刑害哪个更先。"
    if domain == "useful_god":
        return f"{digest}更突出时，用神方向先看扶身、泄秀还是财星？"
    if domain == "pattern":
        return f"{digest}明显时，格局先复核哪段关键条件？"
    if domain == "relationship":
        return f"{digest}凸显时，关系里先看互动、承接还是约束？"
    if domain == "health":
        return f"{digest}较明显时，先看健康偏枯和平衡压力。"
    if domain == "time":
        return _append_focus_tail(f"{digest}参与时，先看时间层牵动的事业、财运或关系。", _decision_feature_materials(decision, feature_layer))
    return _append_focus_tail(f"{digest}明显时，先从这个结构切入。", _decision_feature_materials(decision, feature_layer))


def _make_question_row(
    *,
    question_key: str,
    title: str,
    domain: str,
    score: float,
    decision: dict[str, object],
    feature_layer: FeatureLayer,
) -> QuestionCandidate:
    candidate = _make_decision_question(
        question_key=question_key,
        title=title,
        domain=domain,
        score=score,
        feature_layer=feature_layer,
        source_decision=decision,
    )
    return _aligned(candidate)


def _feature_digest(decision: dict[str, object], feature_layer: FeatureLayer) -> str:
    material = _decision_focus_snippet(decision, feature_layer, max_count=2, min_count=2)
    if not material:
        return ""
    return "、".join(dict.fromkeys(material))


def _decision_focus_snippet(
    decision: dict[str, object],
    feature_layer: FeatureLayer,
    max_count: int = 2,
    min_count: int = 1,
) -> list[str]:
    material: list[str] = []
    for row in decision.get("support", ()):
        token = _normalize_marker_token(str(row))
        token = _clean_question_token(token)
        if (
            token
            and "规则" not in token
            and "材料" not in token
            and not re.search(r"\d", token)
            and token not in material
        ):
            material.append(token)
        if len(material) >= max_count:
            break
    if len(material) < min_count:
        feature_ids = tuple(str(row) for row in decision.get("feature_ids", ()) if str(row))
        for feature_id in feature_ids:
            for extra in _feature_keywords_by_id(feature_id, feature_layer):
                candidate = _clean_question_token(extra)
                if candidate and candidate not in material:
                    material.append(candidate)
            if len(material) >= max_count:
                break
    if len(material) < min_count:
        for tag in decision.get("portrait_tags", ()):
            token = _normalize_marker_token(str(tag))
            token = _clean_question_token(token)
            if token and token not in material:
                material.append(token)
            if len(material) >= max_count:
                break
    return material[:max_count]


def _inject_decision_focus(
    title: str,
    decision: dict[str, object],
    feature_layer: FeatureLayer,
    prefer_front: bool = False,
) -> str:
    seed = _decision_question_seed(decision)
    focus = _decision_focus_snippet(decision, feature_layer, max_count=1)
    if seed and title and str(seed) == str(title):
        if not focus or seed in focus:
            return title
    if not title:
        return seed or title
    if not focus and not seed:
        return title
    parts = []
    if focus:
        parts.append(str(focus[0]))
    if seed and seed != focus:
        parts.append(seed)
    if not parts:
        return title
    marker = "；".join(dict.fromkeys(parts))
    if marker in title:
        return title
    if prefer_front:
        return f"{marker}，{title}"
    return f"{title}（{marker}）"


def _decision_question_seed(decision: dict[str, object]) -> str:
    if _is_rulespec_decision(decision):
        result = _rulespec_rules_text(decision)
        if result and "规则" not in result:
            return result
    raw_seeds = tuple(str(row) for row in decision.get("question_seeds", ()) if str(row).strip())
    if raw_seeds:
        for raw_seed in raw_seeds:
            seed = _clean_question_token(raw_seed)
            if seed:
                return seed
    if str(decision.get("label", "")).strip():
        return _clean_question_token(str(decision.get("label", "")))
    return ""


def _question_signature(question_key: str, title: str) -> str:
    compact_title = _compact_text(title)
    if len(compact_title) > 40:
        compact_title = compact_title[:40]
    return f"{question_key}:{compact_title}"


def _clip_text(value: str, limit: int) -> str:
    text = str(value or "").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def _compact_text(value: str) -> str:
    text = str(value or "").strip()
    for token in ("，", "？", "?", ":", "：", "。", "，", "！", "!", "；", ";", "（", "）", "(", ")", '"', "'","“","”"):
        text = text.replace(token, "")
    return text


def _normalize_marker_token(raw: str) -> str:
    raw = raw.strip()
    if not raw:
        return ""
    if "@" in raw:
        raw = raw.split("@", 1)[0].strip()
    return raw.strip("[]{}()，,:；;。")


def _feature_keywords_by_id(feature_id: str, feature_layer: FeatureLayer) -> list[str]:
    if not feature_id:
        return []
    for feature in feature_layer.features:
        if feature.feature_id != feature_id:
            continue
        title = str(feature.title).strip()
        if title:
            return [token for token in (title.split("｜", 1)[0], title.split("|", 1)[0]) if token]
        summary = str(feature.boundary or "").strip()
        if summary:
            return [_normalize_marker_token(summary)]
        return []
    return []


def _mainline_questions(decision_report: dict[str, object], feature_layer: FeatureLayer) -> list[QuestionCandidate]:
    rows: list[QuestionCandidate] = []
    mainlines = [row for row in decision_report.get("mainlines", ()) if isinstance(row, dict)]
    decision_by_key = {
        str(row.get("decision_key", "")): row
        for row in decision_report.get("decisions", ())
        if isinstance(row, dict)
    }
    used_domains: set[str] = set()
    for index, mainline in enumerate(mainlines[:4]):
        domain = str(mainline.get("domain", ""))
        key = QUESTION_KEY_BY_DOMAIN.get(domain)
        if not key:
            continue
        source_decision_keys = tuple(str(row) for row in mainline.get("source_decision_keys", ()) if str(row))
        source_decisions = tuple(
            decision_by_key[row_key]
            for row_key in source_decision_keys
            if row_key in decision_by_key
        )
        is_rulespec = _is_rulespec_mainline(mainline)
        if is_rulespec and domain in used_domains:
            continue
        if is_rulespec and not _mainline_needs_rulespec_prompt(mainline, decision_by_key.values()):
            continue
        title = _mainline_title(mainline, source_decisions, feature_layer)
        score = float(mainline.get("score", 0.0))
        status = str(mainline.get("status", ""))
        title = _decorate_mainline_title(title, str(mainline.get("title", "")), status)
        rows.append(_attach_question_id(
            QuestionCandidate(
            question_key=key,
            title=title,
            domain=domain,
            score=round(score + 0.09 - index * 0.01 + _state_boost(status), 3),
            source_feature_ids=_feature_ids(source_decisions[0] if source_decisions else mainline, feature_layer, domain),
            boundary=_boundary(domain),
            measurement_topic=domain_label(domain),
            measurement_stage=measurement_stage(domain),
            **dimension_payload(domain),
            ),
            source_decision=source_decisions[0] if source_decisions else mainline,
        ))
        used_domains.add(domain)
    return [row for row in (_aligned(row) for row in rows) if row is not None]


def _is_rulespec_mainline(mainline: dict[str, object]) -> bool:
    if str(mainline.get("role", "")) == "primary_rulespec_bazi_mainline":
        return True
    return any(
        str(source).startswith("decision.rulespec.")
        for source in tuple(mainline.get("source_decision_keys", ()))
    )


def _mainline_needs_rulespec_prompt(
    mainline: dict[str, object],
    decisions: tuple[object, ...] | list[object] | dict_values[object],
) -> bool:
    domain = str(mainline.get("domain", ""))
    if not domain:
        return True
    for row in decisions:
        if not isinstance(row, dict):
            continue
        if str(row.get("domain", "")) != domain:
            continue
        key = str(row.get("decision_key", "") or row.get("rule_key", ""))
        if key.startswith("decision.rulespec."):
            continue
        if str(row.get("role", "")) == "rulespec_context":
            continue
        return False
    return True


def _mainline_title(
    mainline: dict[str, object],
    source_decisions: tuple[dict[str, object], ...],
    feature_layer: FeatureLayer,
) -> str:
    seed = str(mainline.get("question_seed", "")).strip()
    if _is_rulespec_mainline(mainline) and source_decisions:
        for source in source_decisions:
            candidate = _question_title(source, feature_layer)
            if candidate:
                return candidate
    if seed and _is_mainline_seed_ok(seed):
        return f"{seed}"
    if _is_rulespec_mainline(mainline):
        return _rulespec_mainline_template(str(mainline.get("domain", "")))
    title = str(mainline.get("title", "")).strip()
    if title:
        return f"{title}如何进入本次测算？"
    return "这个主线现在应从哪条证据先入手？"


def _is_mainline_seed_ok(seed: str) -> bool:
    return bool(seed) and "规则" not in seed and "明确成立" not in seed and "候选" not in seed


def _decorate_mainline_title(title: str, label: str, status: str) -> str:
    if not title:
        return title
    if status in {"chain_review", "requires_review"}:
        return f"{title}先做哪一步复核？"
    if status in {"countered", "blocked"}:
        return f"{title}有没有先级更高的牵引问题？"
    if not label:
        return title
    return title


def _time_context_questions(
    decision_report: dict[str, object],
    feature_layer: FeatureLayer,
    time_context: TimeContext,
) -> list[QuestionCandidate]:
    rows: list[QuestionCandidate] = []
    if not isinstance(time_context, TimeContext):
        return rows
    if not time_context.layers:
        return rows
    layer_descriptions = [
        f"{row.layer_key}:{row.pillar.display} ({row.ten_god.label})"
        for row in time_context.layers
        if row is not None
    ]
    relation_count = len(time_context.relation_hits)
    base = 0.86 + min(0.09, len(time_context.layers) * 0.03 + relation_count * 0.015)

    rows.append(_make_decision_question(
        "q_time_layer_context",
        f"{layer_descriptions[0]}是否先牵动事业、财运、关系中的哪条线？",
        "time",
        round(base, 3),
        feature_layer,
        source_decision=_time_context_decision(decision_report),
    ))

    if relation_count:
        trigger = _time_trigger_hint(time_context)
        rows.append(_make_decision_question(
            "q_time_relation_triggers",
            f"{trigger}是否优先先触发了哪种交互？",
            "time",
            round(base - 0.07, 3),
            feature_layer,
            source_decision=_time_context_decision(decision_report),
        ))
    else:
        rows.append(_make_decision_question(
            "q_time_relation_triggers",
            "大运流年更容易先触发哪类关系交互？",
            "time",
            round(base - 0.07, 3),
            feature_layer,
            source_decision=_time_context_decision(decision_report),
        ))
    rows.append(_make_decision_question(
        "q_branch_relation_detail",
        "地支牵动里哪些关系互动更值得先拆？",
        "branch",
        round(base - 0.09, 3),
        feature_layer,
        source_decision=_time_context_decision(decision_report),
    ))
    return [
        row
        for row in (_aligned(row) for row in rows)
        if row is not None
    ]


def _time_context_decision(decision_report: dict[str, object]) -> dict[str, object]:
    time_decisions = [
        row for row in decision_report.get("decisions", ())
        if isinstance(row, dict) and str(row.get("domain", "")) == "time"
    ]
    if time_decisions:
        return time_decisions[0]
    return {"feature_ids": (), "score": 0.66, "status": "candidate", "decision_key": "decision.time.synthetic"}


def _time_trigger_hint(time_context: TimeContext) -> str:
    if not time_context.relation_hits:
        return "时运层位置信息"
    first = list(time_context.relation_hits)[0]
    relation = str(first.relation_type or "关系变化")
    if "冲" in relation:
        return "地支冲合"
    if "合" in relation:
        return "合化"
    if "刑" in relation:
        return "刑害"
    if "害" in relation:
        return "三刑"
    return "关系变化"


def _make_decision_question(
    question_key: str,
    title: str,
    domain: str,
    score: float,
    feature_layer: FeatureLayer,
    source_decision: dict[str, object] | None,
) -> QuestionCandidate:
    candidate = QuestionCandidate(
        question_key=question_key,
        title=title,
        domain=domain,
        score=round(score, 3),
        source_feature_ids=_feature_ids(source_decision or {}, feature_layer, domain),
        boundary=_boundary(domain),
        measurement_topic=domain_label(domain),
        measurement_stage=measurement_stage(domain),
        **dimension_payload(domain),
    )
    return _attach_question_id(candidate, source_decision=source_decision)


def _feature_ids(decision: dict[str, object], feature_layer: FeatureLayer, domain: str) -> tuple[str, ...]:
    ids = tuple(str(row) for row in decision.get("feature_ids", ()) if str(row))
    if ids:
        return ids
    fallback = tuple(feature.feature_id for feature in feature_layer.features if feature.domain == domain)
    if fallback:
        return fallback[:4]
    return tuple(feature.feature_id for feature in feature_layer.features[:3])


def _boundary(domain: str) -> str:
    if domain == "wealth":
        return "只解释财星来源、承载力和结构路径，不直接判断收益结果。"
    if domain == "career":
        return "只解释十神角色、格局候选和事业结构，不直接判断职位升降。"
    if domain == "relationship":
        return "只解释十神来源、地支互动和承接边界，不直接判断关系事件。"
    if domain == "health":
        return "只解释五行平衡和结构压力边界，不输出诊断或处理建议。"
    if domain == "time":
        return "时间层只作为触发背景，不输出无证据支撑的具体时间点。"
    return f"只解释{domain_label(domain)}的结构证据和裁决边界，不输出固定吉凶。"


def _role_boost(role: str) -> float:
    if role == "mainline_candidate":
        return 0.12
    if role == "foundation":
        return 0.07
    if role == "time_context":
        return 0.05
    return 0.0


def _rulespec_question_adjustment(decision: dict[str, object]) -> float:
    if _is_rulespec_decision(decision):
        return -0.55
    return 0.0


def _state_boost(state: str) -> float:
    if state in {"volatile", "chain_review", "mixed", "requires_review"}:
        return 0.24
    if state in {"countered", "blocked", "out_of_scope"}:
        return -0.15
    if state in {"weak_candidate", "supported"}:
        return 0.08
    return 0.0


def _fallback_question(feature_layer: FeatureLayer) -> QuestionCandidate:
    ids = tuple(feature.feature_id for feature in feature_layer.features[:4])
    return _attach_question_id(
        QuestionCandidate(
            question_key="q_structure_overview",
            title="这个八字先抓哪条结构主线？",
            domain="branch",
            score=0.3,
            source_feature_ids=ids,
            boundary="只做结构主线梳理，不输出固定吉凶。",
            measurement_topic=domain_label("branch"),
            measurement_stage=measurement_stage("branch"),
            **dimension_payload("branch"),
        ),
        source_decision={"decision_key": "fallback.structure_overview"},
    )


def _secondary_questions(decision: dict[str, object], feature_layer: FeatureLayer) -> list[QuestionCandidate]:
    domain = str(decision.get("domain", ""))
    role = str(decision.get("role", ""))
    rows: list[QuestionCandidate] = []
    if domain == "time":
        title = _inject_decision_focus("这一步大运流年最容易牵动哪条主线？", decision, feature_layer)
        rows.append(_make_question(
            "q_time_relation_triggers",
            title,
            "time",
            float(decision.get("score", 0.0)) - 0.02,
            decision,
            feature_layer,
        ))
    if domain == "wealth":
        title = _inject_decision_focus("财运的机会和限制分别在哪里？", decision, feature_layer)
        rows.append(_make_question(
            "q_income_factors",
            title,
            "wealth",
            float(decision.get("score", 0.0)) - 0.02,
            decision,
            feature_layer,
        ))
    if domain == "element":
        title = _inject_decision_focus("五行偏向会带来什么优势和压力？", decision, feature_layer)
        rows.append(_make_question(
            "q_element_support_pressure",
            title,
            "element",
            float(decision.get("score", 0.0)) - 0.02,
            decision,
            feature_layer,
        ))
    if domain == "ten_god" or ".ten_god." in str(decision.get("rule_key", "")):
        title = _inject_decision_focus("藏干里有哪些容易被忽略的命理线索？", decision, feature_layer)
        rows.append(_make_question(
            "q_hidden_stem_role",
            title,
            "ten_god",
            float(decision.get("score", 0.0)) - (0.01 if role == "foundation_context" else 0.02),
            decision,
            feature_layer,
        ))
    return [row for row in (_aligned(item) for item in rows) if row is not None]


def _knowledge_rule_questions(decision: dict[str, object], feature_layer: FeatureLayer) -> list[QuestionCandidate]:
    rows: list[QuestionCandidate] = []
    rule_key = str(decision.get("rule_key", ""))
    if re.match(r"^rule\.l\d+\.", rule_key):
        return rows
    if str(decision.get("decision_key", "")).startswith("decision.rulespec."):
        return rows
    domain = str(decision.get("domain", ""))
    for ref_index, ref in enumerate(decision.get("knowledge_rule_refs", ())[:2]):
        if not isinstance(ref, dict):
            continue
        for output in ref.get("question_outputs", ())[:2]:
            if not isinstance(output, dict):
                continue
            question_key = str(output.get("question_key", ""))
            title = _normalize_knowledge_question_title(str(output.get("title", "")), domain)
            output_domain = str(output.get("domain", "")) or domain
            if not question_key or not title:
                continue
            candidate = _attach_question_id(
                QuestionCandidate(
                question_key=question_key,
                title=title,
                domain=output_domain,
                score=round(float(decision.get("score", 0.0)) - 0.08 - ref_index * 0.01, 3),
                source_feature_ids=_feature_ids(decision, feature_layer, output_domain),
                boundary=_boundary(output_domain),
                measurement_topic=domain_label(output_domain),
                measurement_stage=measurement_stage(output_domain),
                **dimension_payload(output_domain),
                ),
                source_decision=decision,
            )
            aligned = _aligned(candidate)
            if aligned:
                rows.append(aligned)
    return rows


def _normalize_knowledge_question_title(title: str, domain: str) -> str:
    text = title.strip()
    if not text:
        return ""
    text = _clean_question_token(text)
    if "规则" in text:
        return ""
    if any(token in text for token in ("feature", "hook", "metadata", "应如何进入")):
        return ""
    if "技术" in text or "材料" in text:
        return ""
    if domain == "wealth" and "财" not in text and "收入" not in text:
        return ""
    if domain == "career" and not any(token in text for token in ("事业", "规则", "压力", "表达", "印星", "官杀")):
        return ""
    if domain == "branch" and "冲合刑害" not in text:
        return "地支冲合刑害会先影响哪一类事情？"
    return text


def _practitioner_selection_questions(
    selections: tuple[dict[str, object], ...],
    decision_report: dict[str, object],
    feature_layer: FeatureLayer,
) -> list[QuestionCandidate]:
    rows = []
    decisions = [row for row in decision_report.get("decisions", ()) if isinstance(row, dict)]
    for index, selection in enumerate(selections[:4]):
        control_key = str(selection.get("control_key", ""))
        option = str(selection.get("option", ""))
        domain = CONTROL_DOMAIN.get(control_key, "branch")
        question_key, title = _practitioner_question(control_key, option)
        source_decision_keys = tuple(str(row) for row in selection.get("source_decision_keys", ()) if str(row))
        source_decision = _source_decision_for_selection(decisions, source_decision_keys, domain)
        candidate = _attach_question_id(
            QuestionCandidate(
            question_key=question_key,
            title=title,
            domain=domain,
            score=round(1.2 - index * 0.03, 3),
            source_feature_ids=_feature_ids(source_decision or {}, feature_layer, domain),
            boundary=_boundary(domain),
            measurement_topic=domain_label(domain),
            measurement_stage=measurement_stage(domain),
            **dimension_payload(domain),
            ),
            source_decision=source_decision,
        )
        aligned = _aligned(candidate)
        if aligned:
            rows.append(aligned)
    return rows


def _latent_event_questions(
    answers: tuple[dict[str, object], ...],
    decision_report: dict[str, object],
    feature_layer: FeatureLayer,
) -> list[QuestionCandidate]:
    rows = []
    decisions = [row for row in decision_report.get("decisions", ()) if isinstance(row, dict)]
    for index, answer in enumerate(answers[:4]):
        scenario_id = str(answer.get("scenario_id", ""))
        domain = LATENT_SCENARIO_DOMAIN.get(scenario_id, "")
        if not domain:
            continue
        question_key, title = _latent_event_question(scenario_id, str(answer.get("result_option", "")))
        source_decision = _source_decision_for_selection(decisions, tuple(), domain)
        candidate = _attach_question_id(
            QuestionCandidate(
            question_key=question_key,
            title=title,
            domain=domain,
            score=round(1.12 - index * 0.03, 3),
            source_feature_ids=_feature_ids(source_decision or {}, feature_layer, domain),
            boundary=_boundary(domain),
            measurement_topic=domain_label(domain),
            measurement_stage=measurement_stage(domain),
            **dimension_payload(domain),
            ),
            source_decision=source_decision,
        )
        aligned = _aligned(candidate)
        if aligned:
            rows.append(aligned)
    return rows


def _latent_event_question(scenario_id: str, result_option: str) -> tuple[str, str]:
    if scenario_id == "latent.wealth_change":
        if result_option in {"income_down", "resource_pressure"}:
            return "q_income_stability", "财务压力出现时，命局里先看承载力还是外部牵动？"
        return "q_income_factors", "财务变化明显时，命局里哪些线索最容易被放大？"
    if scenario_id == "latent.career_transition":
        return "q_career_structure", "职业变化明显时，事业主线先看规则、平台还是表达？"
    if scenario_id == "latent.relationship_shift":
        return "q_relationship_structure", "关系变化明显时，命局里先看互动、约束还是承接？"
    if scenario_id == "latent.relocation_environment":
        return "q_time_layer_context", "环境变化明显时，大运流年会先牵动哪条结构线？"
    if scenario_id == "latent.stress_recovery":
        return "q_health_balance_boundary", "压力恢复节奏明显时，命局里先看哪类平衡边界？"
    if scenario_id == "latent.action_result":
        return "q_strength_assessment", "行动结果节奏明显时，先看日主承载还是资源支持？"
    return "q_structure_overview", "结合人生节点后，这个八字先复核哪条主线？"


def _source_decision_for_selection(
    decisions: list[dict[str, object]],
    source_decision_keys: tuple[str, ...],
    domain: str,
) -> dict[str, object] | None:
    for decision in decisions:
        if source_decision_keys and str(decision.get("decision_key", "")) in source_decision_keys:
            return decision
    for decision in decisions:
        if str(decision.get("domain", "")) == domain:
            return decision
    return None


def _practitioner_question(control_key: str, option: str) -> tuple[str, str]:
    if control_key == "control.day_master_strength":
        return "q_strength_assessment", f"命理师判为「{option}」后，下一步先看扶助还是泄耗？"
    if control_key == "control.shang_guan_jian_guan":
        if option == "成立":
            return "q_career_structure", "伤官见官已判成立，先看冲突来源还是化解路径？"
        if option == "被印化":
            return "q_career_structure", "印星能否化解表达冲规则？"
        if option == "被财通关":
            return "q_income_factors", "财星能不能把表达和规则通起来？"
        if option == "不成立":
            return "q_career_structure", "不取伤官见官后，事业主线改看哪里？"
        return "q_career_structure", f"伤官见官判为「{option}」后，事业先复核哪条线？"
    if control_key == "control.wealth_capacity":
        if option == "需扶身":
            return "q_income_stability", "财运要先扶身，还是先看财星来源？"
        if option == "走通关":
            return "q_useful_god_candidates", "财运通关路径应该先看哪一类用神？"
        if option == "看大运":
            return "q_time_layer_context", "财运要不要先看大运流年是否接力？"
        return "q_income_factors", f"财星承载判为「{option}」后，机会和限制在哪里？"
    if control_key == "control.pattern_status":
        if option in {"成格", "破格"}:
            return "q_pattern_structure", f"格局判为「{option}」后，最关键的成败点是什么？"
        return "q_pattern_structure", f"格局仍是「{option}」时，先复核哪几个条件？"
    return "q_structure_overview", "命理师裁决后，下一步先复核哪条结构主线？"


def _make_question(
    question_key: str,
    title: str,
    domain: str,
    score: float,
    decision: dict[str, object],
    feature_layer: FeatureLayer,
) -> QuestionCandidate:
    title = _inject_decision_focus(title, decision, feature_layer)
    candidate = QuestionCandidate(
        question_key=question_key,
        title=title,
        domain=domain,
        score=round(score, 3),
        source_feature_ids=_feature_ids(decision, feature_layer, domain),
        boundary=_boundary(domain),
        measurement_topic=domain_label(domain),
        measurement_stage=measurement_stage(domain),
        **dimension_payload(domain),
    )
    return _attach_question_id(candidate, source_decision=decision)


def _explicit_question(question_key: str, feature_layer: FeatureLayer) -> QuestionCandidate | None:
    if question_key not in QUESTION_LABELS:
        return None
    domain = HOOK_DOMAIN_PREFERENCE.get(question_key, "branch")
    feature_ids = _domain_feature_ids(feature_layer, domain)
    title = _explicit_question_title(question_key, feature_layer)
    candidate = _attach_question_id(
        QuestionCandidate(
        question_key=question_key,
        title=title,
        domain=domain,
        score=0.5,
        source_feature_ids=feature_ids,
        boundary=_boundary(domain),
        measurement_topic=domain_label(domain),
        measurement_stage=measurement_stage(domain),
        **dimension_payload(domain),
        ),
        source_decision={"question_key": question_key},
    )
    return _aligned(candidate)


def _explicit_question_title(question_key: str, feature_layer: FeatureLayer) -> str:
    if question_key == "q_strength_assessment":
        ids = {feature.feature_id for feature in feature_layer.features}
        if "feature.strength.capacity_needs_support" in ids:
            return "日主需要扶身时，先看印星、比劫还是通关？"
        if "feature.strength.borderline_capacity" in ids:
            return "日主强弱接近分界时，先比较哪类证据？"
        if "feature.strength.supported_capacity" in ids:
            return "日主有支撑后，适合先看泄秀、财星还是官杀？"
    if question_key == "q_useful_god_candidates":
        candidate = next((feature for feature in feature_layer.features if feature.feature_id == "feature.useful_god.candidate_paths"), None)
        state = str(getattr(candidate, "calibration_state", "")) if candidate else ""
        if "resource_support" in state or "peer_stabilizer" in state:
            return "用神方向要先扶身，还是另有通关路径？"
        if "output_release" in state:
            return "用神方向适合先看泄秀还是财星通道？"
        if "support_vs_release_review" in state:
            return "用神方向先扶身还是先泄秀？"
    return QUESTION_LABELS[question_key]


def _domain_feature_ids(feature_layer: FeatureLayer, domain: str) -> tuple[str, ...]:
    direct = tuple(feature.feature_id for feature in feature_layer.features if feature.domain == domain)
    if direct:
        return direct[:6]
    return tuple(feature.feature_id for feature in feature_layer.features[:4])
