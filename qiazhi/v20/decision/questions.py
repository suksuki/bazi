from __future__ import annotations

import hashlib
from dataclasses import replace
import re

from v20.answer.measurement_policy import (
    domain_label,
    measurement_stage,
)
from v20.features.schema import FeatureLayer
from v20.decision.question_config import (
    FEATURE_MATERIAL_MAX,
    QUESTION_KEY_BY_DOMAIN,
    QUESTION_KEY_RULE_PREFIX,
    QUESTION_STRATEGY,
    TECHNICAL_TERM_HINTS,
)
from v20.decision.question_builders import portrait_tag_questions, runtime_decision_fusion_questions
from v20.decision.question_decision_hits import decision_hit_questions
from v20.decision.question_feature_hooks import feature_context_material, feature_hook_questions
from v20.decision.question_interaction_refresh import latent_event_questions, practitioner_selection_questions
from v20.decision.question_mainline_time import mainline_questions, time_context_questions
from v20.decision.question_sources import QuestionCandidateManifest
from v20.interaction.question_ranker import question_ranking_policy_runtime, rank_question_rows
from v20.interaction.questions import HOOK_DOMAIN_PREFERENCE, QUESTION_LABELS, QuestionCandidate
from v20.interaction.question_seed_registry import build_seed_question_candidates
from v20.measurement.domain_alignment import align_question_candidate
from v20.measurement.dimensions import dimension_payload
from v20.core.schemas import TimeContext


def _question_id(
    question_key: str,
    title: str,
    domain: str,
    source_feature_ids: tuple[str, ...],
    source_decision: dict[str, object] | None,
    extra_signature: str = "",
    question_strategy: str = "",
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
            question_strategy,
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
    *,
    question_strategy: str = "",
) -> QuestionCandidate:
    decision_key = str(source_decision.get("decision_key", "")) if isinstance(source_decision, dict) else ""
    rule_key = str(source_decision.get("rule_key", "")) if isinstance(source_decision, dict) else ""
    status = str(source_decision.get("status", "")) if isinstance(source_decision, dict) else ""
    label = str(source_decision.get("label", "")) if isinstance(source_decision, dict) else ""
    return replace(
        candidate,
        question_id=_question_id(
            candidate.question_key,
            candidate.title,
            candidate.domain,
            candidate.source_feature_ids,
            source_decision,
            question_strategy=question_strategy,
        ),
        source_decision_key=decision_key,
        source_rule_key=rule_key,
        source_decision_status=status,
        source_decision_label=label,
        question_strategy=question_strategy,
    )

def recommend_decision_questions(
    decision_report: dict[str, object],
    feature_layer: FeatureLayer,
    *,
    runtime_decision_fusion: dict[str, object] | None = None,
    time_context: TimeContext | None = None,
    practitioner_selections: tuple[dict[str, object], ...] = (),
    latent_event_answers: tuple[dict[str, object], ...] = (),
    limit: int = 12,
) -> tuple[QuestionCandidate, ...]:
    rows = []
    manifest = QuestionCandidateManifest()
    rows.extend(manifest.extend(
        "runtime_fusion",
        runtime_decision_fusion_questions(
            runtime_decision_fusion or {},
            feature_layer,
            make_question=_make_decision_question,
            align_question=_aligned,
            explicit_title=lambda explicit_key: _explicit_question_title(explicit_key, feature_layer),
        )
    ))
    rows.extend(manifest.extend(
        "mainline",
        mainline_questions(
            decision_report,
            feature_layer,
            make_question=_make_decision_question,
            align_question=_aligned,
            question_title=_question_title,
            state_boost=_state_boost,
        )
    ))
    rows.extend(manifest.extend(
        "portrait_axis",
        portrait_tag_questions(
            decision_report,
            feature_layer,
            make_question=_make_decision_question,
            align_question=_aligned,
        )
    ))
    rows.extend(manifest.extend(
        "decision_hit",
        decision_hit_questions(
            decision_report,
            feature_layer,
            make_question=_make_decision_question,
            align_question=_aligned,
            clean_token=_clean_question_token,
            normalize_token=_normalize_marker_token,
        )
    ))
    rows.extend(manifest.extend(
        "feature_hook",
        feature_hook_questions(
            decision_report,
            feature_layer,
            attach_question=lambda candidate, source_decision, strategy: _attach_question_id(
                candidate,
                source_decision=source_decision,
                question_strategy=strategy,
            ),
            align_question=_aligned,
            base_score=_base_question_score,
            feature_ids=_feature_ids,
            boundary=_boundary,
            clean_token=_clean_question_token,
            contains_chinese=_contains_chinese,
            clip_text=_clip_text,
        )
    ))
    decision_loop_rows: list[QuestionCandidate] = []
    for decision in decision_report.get("decisions", ()):
        if not isinstance(decision, dict):
            continue
        domain = str(decision.get("domain", ""))
        key = QUESTION_KEY_BY_DOMAIN.get(domain)
        if not key:
            continue
        decision_loop_rows.extend(
            _decision_questions(
                decision=decision,
                feature_layer=feature_layer,
                domain=domain,
                include_variant=True,
            )
        )
        decision_loop_rows.extend(_secondary_questions(decision, feature_layer))
        decision_loop_rows.extend(_knowledge_rule_questions(decision, feature_layer))
    rows.extend(manifest.extend("decision_loop", decision_loop_rows))
    rows.extend(manifest.extend(
        "time_context",
        time_context_questions(
            decision_report,
            feature_layer,
            time_context or TimeContext(),
            make_question=_make_decision_question,
            align_question=_aligned,
        )
    ))
    rows.extend(
        manifest.extend(
            "seed_registry",
            list(build_seed_question_candidates(decision_report, feature_layer, time_context=time_context or TimeContext())),
        )
    )
    rows.extend(manifest.extend(
        "practitioner_refresh",
        practitioner_selection_questions(
            practitioner_selections,
            decision_report,
            feature_layer,
            make_question=_make_interaction_question,
            align_question=_aligned,
        )
    ))
    rows.extend(manifest.extend(
        "latent_event",
        latent_event_questions(
            latent_event_answers,
            decision_report,
            feature_layer,
            make_question=_make_interaction_question,
            align_question=_aligned,
        )
    ))
    if not rows:
        rows = manifest.extend("fallback", [_fallback_question(feature_layer)])
    rows = _dedupe_questions(rows)
    ordered = tuple(
        rank_question_rows(
            tuple(rows),
            question_ranking_policy_runtime(),
        )
    )
    ordered = _limit_question_diversity(ordered)
    if not ordered:
        ordered = (_fallback_question(feature_layer),)
    return ordered[:limit]


def _dedupe_questions(rows: list[QuestionCandidate]) -> list[QuestionCandidate]:
    by_signature: dict[str, QuestionCandidate] = {}
    for row in rows:
        signature = _question_signature_for_diversity(row)
        current = by_signature.get(signature)
        if current is None or row.score > current.score:
            by_signature[signature] = row
    return list(by_signature.values())


def _limit_question_diversity(
    rows: tuple[QuestionCandidate, ...],
    *,
    per_domain_limit: int = 2,
    per_domain_strategy_limit: int = 1,
    per_key_limit: int = 1,
) -> tuple[QuestionCandidate, ...]:
    kept: list[QuestionCandidate] = []
    domain_count: dict[str, int] = {}
    key_count: dict[str, int] = {}
    domain_strategy_count: dict[str, dict[str, int]] = {}
    signature_seen: set[str] = set()
    for row in rows:
        key = row.question_key
        strategy = str(row.question_strategy or "").strip()
        signature = _question_signature_for_diversity(row)
        if signature in signature_seen:
            continue
        domain_strategy = domain_strategy_count.setdefault(row.domain, {})
        strategy_limit = 2 if strategy == QUESTION_STRATEGY["time_context"] else per_domain_strategy_limit
        if strategy_limit and domain_strategy.get(strategy, 0) >= strategy_limit:
            continue
        if per_domain_limit and domain_count.get(row.domain, 0) >= per_domain_limit:
            continue
        if per_key_limit and key_count.get(key, 0) >= per_key_limit:
            continue

        kept.append(row)
        signature_seen.add(signature)
        domain_count[row.domain] = domain_count.get(row.domain, 0) + 1
        key_count[key] = key_count.get(key, 0) + 1
        domain_strategy[strategy] = domain_strategy.get(strategy, 0) + 1
    return tuple(kept)


def _question_priority_sort_key(row: QuestionCandidate) -> tuple[int, int, int, int, float, float, int, int]:
    rule_ok = 0 if row.source_rule_key else 1
    rule_prefix_match = _question_rule_prefix_priority(row.question_key, str(row.source_rule_key or ""))
    role_boost = 1 if row.role == "practitioner_refresh" else 0
    strategy_boost = 0
    if row.question_strategy == QUESTION_STRATEGY["time_context"]:
        strategy_boost = 3
    elif row.question_strategy == QUESTION_STRATEGY["mainline_candidate"]:
        strategy_boost = 2
    elif row.question_strategy == QUESTION_STRATEGY["decision_hit"]:
        strategy_boost = 2
    elif row.question_strategy == QUESTION_STRATEGY["practitioner_refresh"]:
        strategy_boost = 4
    return (
        -rule_ok,
        role_boost,
        strategy_boost,
        rule_prefix_match,
        _status_priority(str(row.source_decision_status)),
        float(row.score or 0.0),
        float(row.alignment_score or 0.0),
        len(row.source_feature_ids or ()),
        -len(row.measurement_topic or ""),
    )


def _question_signature_for_diversity(question: QuestionCandidate) -> str:
    strategy = str(question.question_strategy or "").strip()
    return "|".join(
        (
            question.question_key,
            question.domain,
            strategy,
            question.source_rule_key,
            question.source_decision_key,
            question.source_decision_status,
            str(hash(tuple(question.source_feature_ids[:2]))),
            _question_text_signature(question.title),
        )
    )


def _question_text_signature(value: str, max_len: int = 36) -> str:
    text = _compact_text(str(value or "").strip())
    if not text:
        return ""
    return text[:max_len]


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
        keyed = [question for question in questions if question.question_key == question_key]
        if keyed:
            return _best_question_for_key(question_key, keyed)
        explicit = _explicit_question(question_key, feature_layer)
        if explicit is not None:
            return explicit
    if questions:
        return questions[0]
    return _fallback_question(feature_layer)


def _best_question_for_key(question_key: str, candidates: list[QuestionCandidate]) -> QuestionCandidate:
    return _highest_priority_question(candidates)


def _status_priority(status: str) -> int:
    if status in {"confirmed", "supported", "supported_capacity"}:
        return 3
    if status in {"chain_review", "requires_review", "review_required", "mixed", "volatile", "candidate", "weak_candidate"}:
        return 2
    if status in {"candidate_review"}:
        return 1
    return 0


def _highest_priority_question(candidates: list[QuestionCandidate]) -> QuestionCandidate:
    return sorted(candidates, key=_question_priority_sort_key, reverse=True)[0]


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
        return "这个盘的用神和调节方向是什么？"
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
            base = "这个盘的用神为什么偏向扶助日主？"
        elif "泄秀" in label:
            base = "这个盘的用神为什么偏向疏导泄秀？"
        elif "财星通道" in label:
            base = "这个盘的用神能不能落到财星通道？"
        elif "官杀约束" in label:
            base = "这个盘取用时官杀约束要放到什么位置？"
        elif "扶泄裁决" in label:
            base = "这个盘的用神和调节方向到底是什么？"
        else:
            base = "这个盘的用神和调节方向是什么？"
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
        return base or "这个盘的用神和调节方向是什么？"

    if rule_key == "rule.strength.capacity":
        return base

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
            base = "这个盘的用神和调节方向是什么？"
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
    if any(token in text for token in TECHNICAL_TERM_HINTS):
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
        question_strategy=QUESTION_STRATEGY["mainline_candidate"],
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
                question_strategy=QUESTION_STRATEGY["mainline_candidate"],
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
        return f"{digest}更突出时，这个盘的用神和调节方向是什么？"
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
    question_strategy: str,
) -> QuestionCandidate:
    candidate = _make_decision_question(
        question_key=question_key,
        title=title,
        domain=domain,
        score=score,
        feature_layer=feature_layer,
        source_decision=decision,
        question_strategy=question_strategy,
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


def _question_signature_with_id(question_key: str, title: str, question_id: str) -> str:
    compact_title = _compact_text(title)
    if len(compact_title) > 40:
        compact_title = compact_title[:40]
    normalized_id = str(question_id or "").strip()
    if normalized_id:
        normalized_id = normalized_id.split(":", 1)[0]
        return f"{question_key}:{compact_title}:{normalized_id}"
    return f"{question_key}:{compact_title}"


def _question_signature(question_key: str, title: str, question_id: str = "") -> str:
    return _question_signature_with_id(question_key, title, question_id)


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


def _question_rule_prefix_priority(question_key: str, rule_key: str) -> int:
    prefix = QUESTION_KEY_RULE_PREFIX.get(question_key, "")
    if not prefix:
        return 0
    return 1 if str(rule_key).startswith(prefix) else 0


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
        material = feature_context_material(feature)
        if material:
            return [material]
        summary = str(feature.boundary or "").strip()
        if summary:
            return [_normalize_marker_token(summary)]
        return []
    return []


def _make_decision_question(
    question_key: str,
    title: str,
    domain: str,
    score: float,
    feature_layer: FeatureLayer,
    source_decision: dict[str, object] | None,
    question_strategy: str = "",
) -> QuestionCandidate:
    strategy = question_strategy or QUESTION_STRATEGY["default"]
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
    return _attach_question_id(candidate, source_decision=source_decision, question_strategy=strategy)


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
        question_strategy=QUESTION_STRATEGY["fallback"],
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
            question_strategy=QUESTION_STRATEGY["secondary"],
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
            question_strategy=QUESTION_STRATEGY["secondary"],
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
            question_strategy=QUESTION_STRATEGY["secondary"],
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
            question_strategy=QUESTION_STRATEGY["secondary"],
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
                question_strategy=QUESTION_STRATEGY["knowledge_output"],
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


def _make_interaction_question(
    question_key: str,
    title: str,
    domain: str,
    score: float,
    feature_layer: FeatureLayer,
    source_decision: dict[str, object] | None,
    question_strategy: str,
    role: str,
) -> QuestionCandidate:
    candidate = QuestionCandidate(
        question_key=question_key,
        title=title,
        domain=domain,
        score=round(score, 3),
        role=role,
        source_feature_ids=_feature_ids(source_decision or {}, feature_layer, domain),
        boundary=_boundary(domain),
        measurement_topic=domain_label(domain),
        measurement_stage=measurement_stage(domain),
        **dimension_payload(domain),
    )
    return _attach_question_id(candidate, source_decision=source_decision, question_strategy=question_strategy)


def _make_question(
    question_key: str,
    title: str,
    domain: str,
    score: float,
    decision: dict[str, object],
    feature_layer: FeatureLayer,
    question_strategy: str = "",
) -> QuestionCandidate:
    strategy = question_strategy or QUESTION_STRATEGY["default"]
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
    return _attach_question_id(candidate, source_decision=decision, question_strategy=strategy)


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
        question_strategy=QUESTION_STRATEGY["decision_mainline"],
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
            return "这个盘的用神为什么偏向扶助日主？"
        if "output_release" in state:
            return "这个盘的用神为什么偏向疏导泄秀？"
        if "support_vs_release_review" in state:
            return "这个盘的用神和调节方向到底是什么？"
    return QUESTION_LABELS[question_key]


def _domain_feature_ids(feature_layer: FeatureLayer, domain: str) -> tuple[str, ...]:
    direct = tuple(feature.feature_id for feature in feature_layer.features if feature.domain == domain)
    if direct:
        return direct[:6]
    return tuple(feature.feature_id for feature in feature_layer.features[:4])
