from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from v30.diagnosis.contracts import (
    DiagnosisClaim,
    DiagnosisDomain,
    DiagnosisFeature,
    DiagnosisPath,
    DiagnosisPortrait,
    MatchedRule,
)


CLAIM_GENERATOR_VERSION = "v30.real_bazi_diagnosis.claim_generator.v1"

DOMAIN_ORDER: list[DiagnosisDomain] = [
    "overview",
    "structure",
    "useful_god",
    "timing",
    "wealth",
    "career",
    "relationship",
    "health",
    "hidden_factor",
]


def generate_diagnosis_claims(
    *,
    matched_rules: Sequence[MatchedRule],
    features: Sequence[DiagnosisFeature],
    paths: Sequence[DiagnosisPath],
    portraits: Sequence[DiagnosisPortrait],
    active_domains: Sequence[DiagnosisDomain] | None = None,
    limit: int | None = None,
) -> list[DiagnosisClaim]:
    domains = list(active_domains or DOMAIN_ORDER)
    claims: list[DiagnosisClaim] = []
    claims.extend(_fact_and_feature_claims(features))
    claims.extend(_path_claims(paths))
    claims.extend(_portrait_claims(portraits))
    claims.extend(_domain_claims(domains, matched_rules, features, paths, portraits))
    claims.extend(_timing_claims(features, paths, matched_rules))
    claims.extend(_question_claims(matched_rules, features, portraits))
    claims = _dedupe_claims(claims)
    claims.sort(key=lambda row: (_domain_rank(row.domain), _claim_level_rank(row.claim_level), _confidence_rank(row.confidence_band), row.claim_id))
    if limit is not None:
        return claims[:limit]
    return claims


def summarize_diagnosis_claims(claims: Sequence[DiagnosisClaim]) -> dict[str, Any]:
    by_domain: dict[str, int] = {}
    by_level: dict[str, int] = {}
    by_confidence: dict[str, int] = {}
    for claim in claims:
        by_domain[claim.domain] = by_domain.get(claim.domain, 0) + 1
        by_level[claim.claim_level] = by_level.get(claim.claim_level, 0) + 1
        by_confidence[claim.confidence_band] = by_confidence.get(claim.confidence_band, 0) + 1
    return {
        "version": CLAIM_GENERATOR_VERSION,
        "claim_count": len(claims),
        "domain_counts": dict(sorted(by_domain.items())),
        "level_counts": dict(sorted(by_level.items())),
        "confidence_counts": dict(sorted(by_confidence.items())),
        "needs_calibration_count": sum(1 for claim in claims if claim.needs_user_calibration),
        "blocked_overclaim_count": sum(len(claim.blocked_overclaim) for claim in claims),
        "top_claim_ids": [claim.claim_id for claim in list(claims)[:10]],
        "boundary": "diagnosis_claim_summary_is_traceable_bounded_bazi_judgment_not_llm_output",
    }


def _fact_and_feature_claims(features: Sequence[DiagnosisFeature]) -> list[DiagnosisClaim]:
    claims: list[DiagnosisClaim] = []
    for feature in features:
        if feature.domain == "overview" and "不可改写" in feature.statement:
            claims.append(
                DiagnosisClaim(
                    claim_id=f"rbd.claim.fact:{_safe_id(feature.feature_id)}",
                    claim_level="fact",
                    domain="overview",
                    claim_text=feature.statement,
                    confidence_band=feature.confidence_band,
                    evidence_ids=feature.evidence_ids,
                    blocked_overclaim=_blocked_from_notes(feature.counter_notes),
                )
            )
            continue
        if feature.domain in {"structure", "useful_god", "hidden_factor"} and _is_high_signal(feature):
            claims.append(
                DiagnosisClaim(
                    claim_id=f"rbd.claim.feature:{_safe_id(feature.feature_id)}",
                    claim_level="feature",
                    domain=feature.domain,
                    claim_text=_feature_claim_text(feature),
                    confidence_band=feature.confidence_band,
                    evidence_ids=feature.evidence_ids,
                    blocked_overclaim=_blocked_from_notes(feature.counter_notes),
                    needs_user_calibration=feature.domain in {"useful_god", "hidden_factor"} or _needs_calibration_from_notes(feature.counter_notes),
                )
            )
    return claims


def _path_claims(paths: Sequence[DiagnosisPath]) -> list[DiagnosisClaim]:
    claims: list[DiagnosisClaim] = []
    for path in paths:
        if path.score < 0.55:
            continue
        primary_domain = _primary_path_domain(path)
        claims.append(
            DiagnosisClaim(
                claim_id=f"rbd.claim.path:{_safe_id(path.path_id)}",
                claim_level="path",
                domain=primary_domain,
                claim_text=_path_claim_text(path, primary_domain),
                confidence_band=_confidence_band(path.score),
                evidence_ids=path.evidence_ids,
                path_ids=[path.path_id],
                blocked_overclaim=path.blocked_overclaim,
                needs_user_calibration=bool(path.counter_evidence_ids),
            )
        )
        if primary_domain != "health" and "health" in path.domain_targets:
            claims.append(
                DiagnosisClaim(
                    claim_id=f"rbd.claim.path.health:{_safe_id(path.path_id)}",
                    claim_level="path",
                    domain="health",
                    claim_text=_path_claim_text(path, "health"),
                    confidence_band=_confidence_band(path.score),
                    evidence_ids=path.evidence_ids,
                    path_ids=[path.path_id],
                    blocked_overclaim=_merge_ids(path.blocked_overclaim, ["medical_diagnosis", "disease_prediction"]),
                    needs_user_calibration=bool(path.counter_evidence_ids),
                )
            )
    return claims


def _portrait_claims(portraits: Sequence[DiagnosisPortrait]) -> list[DiagnosisClaim]:
    claims: list[DiagnosisClaim] = []
    for portrait in portraits:
        if portrait.domain == "overview":
            continue
        if portrait.confidence_band == "low":
            continue
        if not _portrait_is_actionable(portrait):
            continue
        claims.append(
            DiagnosisClaim(
                claim_id=f"rbd.claim.portrait:{_safe_id(portrait.portrait_id)}",
                claim_level="portrait",
                domain=portrait.domain,
                claim_text=_portrait_claim_text(portrait),
                confidence_band=portrait.confidence_band,
                evidence_ids=portrait.evidence_ids,
                path_ids=portrait.path_ids,
                portrait_ids=[portrait.portrait_id],
                blocked_overclaim=_blocked_from_notes(portrait.counter_notes),
                needs_user_calibration=portrait.domain == "hidden_factor" or _needs_calibration_from_notes(portrait.counter_notes),
            )
        )
    return claims


def _domain_claims(
    domains: Sequence[DiagnosisDomain],
    matched_rules: Sequence[MatchedRule],
    features: Sequence[DiagnosisFeature],
    paths: Sequence[DiagnosisPath],
    portraits: Sequence[DiagnosisPortrait],
) -> list[DiagnosisClaim]:
    claims: list[DiagnosisClaim] = []
    for domain in domains:
        if domain not in {"structure", "useful_god", "wealth", "career", "relationship", "health", "hidden_factor"}:
            continue
        domain_paths = _top_paths(paths, domain)
        domain_portraits = _top_portraits(portraits, domain)
        domain_rules = _top_rules(matched_rules, domain)
        domain_features = _top_features(features, domain)
        if not (domain_paths or domain_portraits or domain_rules or domain_features):
            continue
        claims.append(
            DiagnosisClaim(
                claim_id=f"rbd.claim.domain:{domain}",
                claim_level="domain",
                domain=domain,
                claim_text=_domain_claim_text(domain, domain_paths, domain_portraits, domain_features),
                confidence_band=_aggregate_confidence(domain_paths, domain_portraits, domain_rules, domain_features),
                evidence_ids=_merge_ids(
                    [item for feature in domain_features for item in feature.evidence_ids],
                    [item for path in domain_paths for item in path.evidence_ids],
                    [item for portrait in domain_portraits for item in portrait.evidence_ids],
                    [item for rule in domain_rules for item in rule.evidence_ids],
                ),
                rule_ids=[rule.rule_id for rule in domain_rules[:5]],
                path_ids=[path.path_id for path in domain_paths[:5]],
                portrait_ids=[portrait.portrait_id for portrait in domain_portraits[:5]],
                blocked_overclaim=_merge_ids(
                    [item for path in domain_paths for item in path.blocked_overclaim],
                    [item.removeprefix("blocks:") for feature in domain_features for item in feature.counter_notes if item.startswith("blocks:")],
                    [item for rule in domain_rules for item in rule.blocked_claims],
                ),
                needs_user_calibration=_domain_needs_calibration(domain, domain_rules, domain_features, domain_portraits, domain_paths),
            )
        )
    return claims


def _timing_claims(
    features: Sequence[DiagnosisFeature],
    paths: Sequence[DiagnosisPath],
    matched_rules: Sequence[MatchedRule],
) -> list[DiagnosisClaim]:
    timing_features = [feature for feature in features if feature.domain == "timing"]
    timed_paths = [path for path in paths if any(str(value) for value in path.timing_trigger.values())]
    if not timing_features and not timed_paths:
        return []
    blocked = _merge_ids(
        [item for rule in matched_rules if "timing" in rule.domain_targets for item in rule.blocked_claims],
        [item for path in timed_paths for item in path.blocked_overclaim],
    )
    text = _timing_text(timing_features, timed_paths)
    return [
        DiagnosisClaim(
            claim_id="rbd.claim.timing:active_time_layer",
            claim_level="timing",
            domain="timing",
            claim_text=text,
            confidence_band="high" if timed_paths else "medium",
            evidence_ids=_merge_ids(
                [item for feature in timing_features for item in feature.evidence_ids],
                [item for path in timed_paths[:4] for item in path.evidence_ids],
            ),
            path_ids=[path.path_id for path in timed_paths[:5]],
            blocked_overclaim=blocked or ["fixed_event_prediction", "special_year_claim"],
            needs_user_calibration=False,
        )
    ]


def _question_claims(
    matched_rules: Sequence[MatchedRule],
    features: Sequence[DiagnosisFeature],
    portraits: Sequence[DiagnosisPortrait],
) -> list[DiagnosisClaim]:
    calibration_rules = [rule for rule in matched_rules if rule.requires_user_calibration]
    calibration_features = [feature for feature in features if feature.domain in {"hidden_factor", "useful_god"}]
    calibration_portraits = [portrait for portrait in portraits if portrait.domain in {"hidden_factor", "useful_god"}]
    if not (calibration_rules or calibration_features or calibration_portraits):
        return []
    return [
        DiagnosisClaim(
            claim_id="rbd.claim.question:calibration_next",
            claim_level="question",
            domain="hidden_factor" if any(item.domain == "hidden_factor" for item in [*calibration_features, *calibration_portraits]) else "useful_god",
            claim_text="下一轮问答应优先校准藏干背景线索、反复年份/状态和用神候选承接点；这些反馈只调整路径权重和断语边界，不改四柱、大运或流年事实。",
            confidence_band="medium",
            evidence_ids=_merge_ids(
                [item for rule in calibration_rules for item in rule.evidence_ids],
                [item for feature in calibration_features for item in feature.evidence_ids],
                [item for portrait in calibration_portraits for item in portrait.evidence_ids],
            ),
            rule_ids=[rule.rule_id for rule in calibration_rules[:6]],
            portrait_ids=[portrait.portrait_id for portrait in calibration_portraits[:6]],
            blocked_overclaim=["chart_fact_mutation", "deterministic_hidden_factor_claim", "fixed_useful_god_verdict"],
            needs_user_calibration=True,
        )
    ]


def _feature_claim_text(feature: DiagnosisFeature) -> str:
    if feature.domain == "structure":
        return f"结构特征可直接进入判断：{feature.statement}"
    if feature.domain == "useful_god":
        return f"用神取向落在承接路径上：{feature.statement}"
    if feature.domain == "hidden_factor":
        return f"背景校准线索集中在：{feature.statement}"
    return feature.statement


def _path_claim_text(path: DiagnosisPath, domain: DiagnosisDomain) -> str:
    if domain == "wealth":
        return f"财运主路径是{path.diagnosis_statement} 财星表现依赖输出、职责和资源承接。"
    if domain == "career":
        return f"事业判断的核心路径是{path.diagnosis_statement} 重点看责任、规则、资质、平台或输出如何承接压力。"
    if domain == "relationship":
        return f"关系沿结构互动展开：{path.diagnosis_statement} 主要看互动模式、压力来源和边界感。"
    if domain == "health":
        return f"身心节律受五行偏性和冲突压力牵动：{path.diagnosis_statement} 调整重点在作息、负荷和寒热燥湿。"
    if domain == "useful_god":
        return f"用神沿承接路径判断：{path.diagnosis_statement} 优先看能通关、调候、承压的五行十神。"
    return path.diagnosis_statement


def _portrait_claim_text(portrait: DiagnosisPortrait) -> str:
    if portrait.domain == "wealth":
        return f"财富画像：{portrait.statement}"
    if portrait.domain == "career":
        return f"事业画像：{portrait.statement}"
    if portrait.domain == "relationship":
        return f"关系画像：{portrait.statement}"
    if portrait.domain == "health":
        return f"身心节律画像：{portrait.statement}"
    if portrait.domain == "hidden_factor":
        return f"背景校准画像：{portrait.statement}"
    if portrait.domain == "useful_god":
        return f"用神画像：{portrait.statement}"
    return portrait.statement


def _domain_claim_text(
    domain: DiagnosisDomain,
    paths: Sequence[DiagnosisPath],
    portraits: Sequence[DiagnosisPortrait],
    features: Sequence[DiagnosisFeature],
) -> str:
    path = paths[0] if paths else None
    portrait = portraits[0] if portraits else None
    feature = features[0] if features else None
    if domain == "wealth":
        if path:
            return f"财运沿{path.mechanism}展开，财星要通过输出、职责或资源承接后才容易成事；适合从资源转化、方案输出、平台授权和分配结构上看收益。"
        return f"财运判断以{portrait.statement if portrait else feature.statement}为入口，先看财星如何被结构承接，再看时运触发。"
    if domain == "career":
        if path:
            return f"事业落在{path.mechanism}，压力会推动资质、规则、平台和可交付能力的形成；职位变化要看职责是否被印星、输出和资源承接。"
        return f"事业判断以{portrait.statement if portrait else feature.statement}为入口，先看官杀、印星和输出之间的承接。"
    if domain == "relationship":
        if path:
            return f"关系受{path.mechanism}牵动，互动压力会集中在责任、资源分配和边界感上；官杀、财星和地支互动决定关系推进节奏。"
        return f"关系判断以{portrait.statement if portrait else feature.statement}为入口，先看十神标记与地支互动。"
    if domain == "health":
        if path:
            return f"身心节律受{path.mechanism}影响，容易在压力触发时表现为作息、寒热燥湿和冲刑压力的波动；调理重点放在节律和负荷管理。"
        return f"健康判断以{portrait.statement if portrait else feature.statement}为边界，只表达生活节律与五行偏性。"
    if domain == "useful_god":
        if path:
            return f"用神取向先看{path.mechanism}中能通关、调候、承压或回生日主的五行十神，再按大运流年验证取舍。"
        return f"用神判断以{feature.statement if feature else portrait.statement}为候选门控，需要继续看路径和反证。"
    if domain == "hidden_factor":
        return "背景校准已有藏干和问答入口，可用于解释反复状态或特殊年份的放大机制，但不能改写命局事实。"
    if domain == "structure":
        if path:
            return f"命局结构以{path.mechanism}为核心路径，月令、十神、地支关系和制化承接需要合并判断。"
        return f"结构判断以{feature.statement if feature else portrait.statement}为入口，保持证据链表达。"
    return portrait.statement if portrait else feature.statement if feature else "该领域已有可追踪诊断证据。"


def _timing_text(features: Sequence[DiagnosisFeature], paths: Sequence[DiagnosisPath]) -> str:
    path = paths[0] if paths else None
    layer_text = ""
    if path:
        trigger = path.timing_trigger
        parts = [str(trigger.get(key) or "") for key in ("luck_pillar", "flow_year_pillar", "flow_month_pillar")]
        parts = [item for item in parts if item]
        if parts:
            layer_text = f"当前时运层为{'、'.join(parts)}，"
    if path:
        return f"{layer_text}时运只作为触发层使用：它会放大{path.mechanism}这类结构路径，但不能单独生成具体年份事件。"
    return f"{features[0].statement} 时运层可参与触发判断，但必须回到原局结构和路径证据。"


def _primary_path_domain(path: DiagnosisPath) -> DiagnosisDomain:
    for domain in ("wealth", "career", "relationship", "health", "useful_god", "structure"):
        if domain in path.domain_targets:
            return domain  # type: ignore[return-value]
    return path.domain_targets[0] if path.domain_targets else "structure"


def _is_high_signal(feature: DiagnosisFeature) -> bool:
    return feature.confidence_band in {"high", "medium"} and feature.domain in {"structure", "useful_god", "hidden_factor"}


def _portrait_is_actionable(portrait: DiagnosisPortrait) -> bool:
    return any(token in portrait.statement for token in ("画像", "财", "事业", "关系", "身心", "结构", "用神", "隐藏", "路径"))


def _top_paths(paths: Sequence[DiagnosisPath], domain: DiagnosisDomain) -> list[DiagnosisPath]:
    rows = [path for path in paths if domain in path.domain_targets]
    rows.sort(key=lambda row: (-row.score, row.path_id))
    return rows[:4]


def _top_portraits(portraits: Sequence[DiagnosisPortrait], domain: DiagnosisDomain) -> list[DiagnosisPortrait]:
    rows = [portrait for portrait in portraits if portrait.domain == domain]
    rows.sort(key=lambda row: (_confidence_rank(row.confidence_band), row.portrait_id))
    return rows[:4]


def _top_rules(rules: Sequence[MatchedRule], domain: DiagnosisDomain) -> list[MatchedRule]:
    rows = [rule for rule in rules if domain in rule.domain_targets and rule.can_generate_claim]
    rows.sort(key=lambda row: (-row.match_strength, row.rule_id))
    return rows[:4]


def _top_features(features: Sequence[DiagnosisFeature], domain: DiagnosisDomain) -> list[DiagnosisFeature]:
    rows = [feature for feature in features if feature.domain == domain]
    rows.sort(key=lambda row: (_confidence_rank(row.confidence_band), row.feature_id))
    return rows[:4]


def _aggregate_confidence(
    paths: Sequence[DiagnosisPath],
    portraits: Sequence[DiagnosisPortrait],
    rules: Sequence[MatchedRule],
    features: Sequence[DiagnosisFeature],
) -> str:
    score = 0.0
    if paths:
        score += max(path.score for path in paths) * 0.38
    if rules:
        score += max(rule.match_strength for rule in rules) * 0.28
    if portraits:
        score += _band_score(portraits[0].confidence_band) * 0.2
    if features:
        score += _band_score(features[0].confidence_band) * 0.14
    if score >= 0.72:
        return "high"
    if score >= 0.48:
        return "medium"
    return "low"


def _domain_needs_calibration(
    domain: DiagnosisDomain,
    rules: Sequence[MatchedRule],
    features: Sequence[DiagnosisFeature],
    portraits: Sequence[DiagnosisPortrait],
    paths: Sequence[DiagnosisPath],
) -> bool:
    if domain in {"hidden_factor", "useful_god"}:
        return True
    if any(rule.requires_user_calibration or rule.missing_context for rule in rules):
        return True
    if any(path.counter_evidence_ids for path in paths):
        return True
    notes = [*[_note for feature in features for _note in feature.counter_notes], *[_note for portrait in portraits for _note in portrait.counter_notes]]
    return _needs_calibration_from_notes(notes)


def _blocked_from_notes(notes: Sequence[str]) -> list[str]:
    blocked: list[str] = []
    for note in notes:
        if note.startswith("blocks:"):
            blocked.append(note.removeprefix("blocks:"))
        elif note in {"medical_diagnosis", "disease_prediction", "fixed_event_prediction", "chart_fact_mutation", "fixed_useful_god_verdict", "deterministic_hidden_factor_claim"}:
            blocked.append(note)
    return _merge_ids(blocked)


def _needs_calibration_from_notes(notes: Sequence[str]) -> bool:
    return any("calibration" in note or "requires_user" in note or "hidden" in note for note in notes)


def _confidence_band(value: float) -> str:
    if value >= 0.75:
        return "high"
    if value >= 0.55:
        return "medium"
    return "low"


def _band_score(value: str) -> float:
    return {"high": 1.0, "medium": 0.66, "low": 0.33}.get(value, 0.0)


def _confidence_rank(value: str) -> int:
    return {"high": 0, "medium": 1, "low": 2}.get(value, 3)


def _claim_level_rank(value: str) -> int:
    order = ["fact", "feature", "path", "portrait", "domain", "timing", "question"]
    return order.index(value) if value in order else 99


def _domain_rank(domain: DiagnosisDomain) -> int:
    return DOMAIN_ORDER.index(domain) if domain in DOMAIN_ORDER else 99


def _merge_ids(*groups: Sequence[str]) -> list[str]:
    out: list[str] = []
    for group in groups:
        for item in group:
            if item and item not in out:
                out.append(item)
    return out


def _safe_id(value: str) -> str:
    return value.replace(":", ".").replace("/", ".")


def _dedupe_claims(claims: Sequence[DiagnosisClaim]) -> list[DiagnosisClaim]:
    seen: set[tuple[str, str, str]] = set()
    out: list[DiagnosisClaim] = []
    for claim in claims:
        key = (claim.domain, claim.claim_level, claim.claim_text)
        if key in seen:
            continue
        seen.add(key)
        out.append(claim)
    return out
