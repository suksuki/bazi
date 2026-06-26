from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from v30.diagnosis.contracts import DiagnosisDomain, DiagnosisPath, DiagnosisPortrait, MatchedRule


PORTRAIT_ENGINE_VERSION = "v30.real_bazi_diagnosis.portrait_engine.v1"

DIMENSION_DOMAIN_HINTS: dict[str, DiagnosisDomain] = {
    "career": "career",
    "authority": "career",
    "wealth": "wealth",
    "finance": "wealth",
    "romance": "relationship",
    "relationship": "relationship",
    "health": "health",
    "hidden": "hidden_factor",
    "useful_god": "useful_god",
    "structure": "structure",
    "element": "structure",
    "seasonal": "structure",
    "calculation": "overview",
    "training": "overview",
}


def extract_diagnosis_portraits(
    *,
    matched_rules: Sequence[MatchedRule],
    diagnosis_paths: Sequence[DiagnosisPath],
    krp_units: Sequence[Mapping[str, Any]] | None = None,
    limit: int | None = None,
) -> list[DiagnosisPortrait]:
    portraits: list[DiagnosisPortrait] = []
    portraits.extend(_portraits_from_rules(matched_rules, krp_units or []))
    portraits.extend(_portraits_from_paths(diagnosis_paths))
    portraits = _dedupe_portraits(portraits)
    portraits.sort(key=lambda row: (_domain_rank(row.domain), _confidence_rank(row.confidence_band), row.portrait_id))
    if limit is not None:
        return portraits[:limit]
    return portraits


def summarize_diagnosis_portraits(portraits: Sequence[DiagnosisPortrait]) -> dict[str, Any]:
    by_domain: dict[str, int] = {}
    by_dimension: dict[str, int] = {}
    by_confidence: dict[str, int] = {}
    for portrait in portraits:
        by_domain[portrait.domain] = by_domain.get(portrait.domain, 0) + 1
        by_dimension[portrait.dimension] = by_dimension.get(portrait.dimension, 0) + 1
        by_confidence[portrait.confidence_band] = by_confidence.get(portrait.confidence_band, 0) + 1
    return {
        "version": PORTRAIT_ENGINE_VERSION,
        "portrait_count": len(portraits),
        "domain_counts": dict(sorted(by_domain.items())),
        "dimension_counts": dict(sorted(by_dimension.items())),
        "confidence_counts": dict(sorted(by_confidence.items())),
        "top_portrait_ids": [row.portrait_id for row in list(portraits)[:8]],
        "boundary": "diagnosis_portrait_summary_is_derived_from_rules_and_paths_not_personality_fact",
    }


def _portraits_from_rules(
    matched_rules: Sequence[MatchedRule],
    krp_units: Sequence[Mapping[str, Any]],
) -> list[DiagnosisPortrait]:
    unit_index = {str(unit.get("unit_id") or ""): unit for unit in krp_units}
    rows: list[DiagnosisPortrait] = []
    for rule in matched_rules:
        unit = unit_index.get(rule.rule_id, {})
        dimensions = _string_list(unit.get("portrait_dimensions")) or [_fallback_dimension(rule)]
        for dimension in dimensions:
            domain = _dimension_domain(dimension, rule.domain_targets)
            rows.append(
                DiagnosisPortrait(
                    portrait_id=f"rbd.portrait.rule:{_safe_id(rule.rule_id)}:{_safe_id(dimension)}",
                    dimension=dimension,
                    domain=domain,
                    statement=_rule_statement(rule, dimension, unit),
                    evidence_ids=rule.evidence_ids,
                    path_ids=rule.path_ids[:6],
                    confidence_band=_confidence_band(rule.match_strength),
                    counter_notes=_counter_notes(rule),
                )
            )
    return rows


def _portraits_from_paths(paths: Sequence[DiagnosisPath]) -> list[DiagnosisPortrait]:
    rows: list[DiagnosisPortrait] = []
    for path in paths:
        for domain in _portrait_domains_for_path(path):
            dimension = _path_dimension(path, domain)
            rows.append(
                DiagnosisPortrait(
                    portrait_id=f"rbd.portrait.path:{_safe_id(path.path_id)}:{domain}",
                    dimension=dimension,
                    domain=domain,
                    statement=_path_statement(path, domain),
                    evidence_ids=path.evidence_ids,
                    path_ids=[path.path_id],
                    confidence_band=_confidence_band(path.score),
                    counter_notes=[path.risk_statement, *path.blocked_overclaim[:5]],
                )
            )
    return rows


def _rule_statement(rule: MatchedRule, dimension: str, unit: Mapping[str, Any]) -> str:
    guidance = _string_list(unit.get("answer_guidance"))
    title = str(unit.get("title") or "")
    if dimension == "calculation_foundation":
        return "此命局画像必须先锁定四柱、日主和确定性事实，后续画像只做解释投影，不改排盘来源。"
    if dimension == "calculation_basis_trace":
        return "此命局适合先列明排盘依据，再进入结构、十神和领域路径，避免凭空输出断语。"
    if "career" in dimension or "authority" in dimension:
        return "事业画像以官杀压力、责任边界和印星承接为主，重点看规则、职位压力、资质平台与路径化解决。"
    if "wealth" in dimension:
        return "财富画像不直接落收入结果，重点看财星是否经由输出、官杀责任或资源分配路径被承接。"
    if "relationship" in dimension or "romance" in dimension:
        return "关系画像以十神标记、地支互动和宫位线索为入口，需要先分清互动模式、冲合压力与现实反馈。"
    if "health" in dimension:
        return "身心健康画像只表达五行偏性、冲刑压力和生活节律线索，不生成疾病诊断或医疗结论。"
    if "hidden" in dimension:
        return "背景校准画像来自藏干、重复状态和用户反馈，只能作为放大线索，不能变成确定事实。"
    if "useful_god" in dimension:
        return "用神画像保持候选表达，必须由调候、流通、反证和动态结构共同支撑。"
    if "structure" in dimension or "element" in dimension or "seasonal" in dimension:
        return "结构画像以月令、五行分布、十神角色和动态路径共同成像，不能用单一旺衰标签定局。"
    if guidance:
        return f"{guidance[0]} 该画像维度用于约束表达和排序，不作为固定人生结论。"
    if title:
        return f"{title} 该画像维度只作为规则投影，不作为固定人生结论。"
    return f"{dimension}画像由规则{rule.rule_id}触发，用于可追踪表达。"


def _path_statement(path: DiagnosisPath, domain: DiagnosisDomain) -> str:
    if path.mechanism == "财官印制化":
        if domain == "wealth":
            return "财富画像呈现财星牵动官杀再入印星的形态，钱财议题常与责任、规则、资质或平台承接绑定。"
        if domain == "career":
            return "事业画像呈现财官印联动，机会不是单靠职位名义，而是看资源、责任和资质承接是否成链。"
        return "结构画像出现财官印制化，财、责、印相互牵动，是后续断语的主路径之一。"
    if path.mechanism == "官印相生":
        return "画像重心落在压力转资质、规则转平台、责任转学习承接，适合用官印相生路径解释事业和结构。"
    if path.mechanism == "食伤生财":
        return "画像重心落在输出、技术、表达、方案或流量转财，财富判断需要看输出是否稳定转化。"
    if path.mechanism == "食伤制官杀":
        return "画像显示表达行动力会触碰规则和权责边界，适合看压力处理、制度适配和反证。"
    if path.mechanism == "比劫争财":
        return "画像显示资源竞争、合伙分配或现金流消耗需要复核，不能直接定破财。"
    if "health" == domain:
        return "身心节律画像来自冲突压力路径，只能提示五行偏性和压力触发，不做疾病预测。"
    return f"画像沿{path.mechanism}展开：{path.diagnosis_statement}"


def _portrait_domains_for_path(path: DiagnosisPath) -> list[DiagnosisDomain]:
    domains: list[DiagnosisDomain] = []
    for domain in path.domain_targets:
        if domain not in domains:
            domains.append(domain)
    return domains[:4]


def _path_dimension(path: DiagnosisPath, domain: DiagnosisDomain) -> str:
    mechanism = {
        "财官印制化": "wealth_authority_resource_portrait",
        "官印相生": "authority_resource_portrait",
        "食伤生财": "output_wealth_portrait",
        "食伤制官杀": "output_authority_portrait",
        "比劫争财": "peer_wealth_competition_portrait",
        "印星通关": "resource_mediator_portrait",
        "制化转生": "control_to_generation_portrait",
        "冲突压力路径": "conflict_pressure_portrait",
    }.get(path.mechanism, "dynamic_path_portrait")
    return f"{domain}_{mechanism}"


def _dimension_domain(dimension: str, fallback: Sequence[DiagnosisDomain]) -> DiagnosisDomain:
    for key, domain in DIMENSION_DOMAIN_HINTS.items():
        if key in dimension:
            return domain
    return fallback[0] if fallback else "overview"


def _fallback_dimension(rule: MatchedRule) -> str:
    domain = rule.domain_targets[0] if rule.domain_targets else "overview"
    return f"{domain}_rule_portrait"


def _counter_notes(rule: MatchedRule) -> list[str]:
    notes = [*rule.counter_context_hit[:5], *rule.blocked_claims[:5]]
    if rule.requires_user_calibration:
        notes.append("requires_user_calibration")
    return notes


def _confidence_band(value: float) -> str:
    if value >= 0.75:
        return "high"
    if value >= 0.55:
        return "medium"
    return "low"


def _confidence_rank(value: str) -> int:
    return {"high": 0, "medium": 1, "low": 2}.get(value, 3)


def _domain_rank(domain: DiagnosisDomain) -> int:
    order = ["overview", "structure", "useful_god", "timing", "wealth", "career", "relationship", "health", "hidden_factor"]
    return order.index(domain) if domain in order else 99


def _string_list(value: Any) -> list[str]:
    return [str(row) for row in value] if isinstance(value, list) else []


def _safe_id(value: str) -> str:
    return value.replace(":", ".").replace("/", ".")


def _dedupe_portraits(portraits: Sequence[DiagnosisPortrait]) -> list[DiagnosisPortrait]:
    seen: set[tuple[str, str]] = set()
    out: list[DiagnosisPortrait] = []
    for portrait in portraits:
        key = (portrait.domain, portrait.dimension)
        if key in seen:
            continue
        seen.add(key)
        out.append(portrait)
    return out
