from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from v30.contracts import FeatureEvidence
from v30.diagnosis.contracts import DiagnosisDomain, DiagnosisFeature, MatchedRule


FEATURE_ENGINE_VERSION = "v30.real_bazi_diagnosis.feature_engine.v1"

DOMAIN_MAP: dict[str, DiagnosisDomain] = {
    "chart": "overview",
    "element": "structure",
    "ten_god": "structure",
    "ten_god_energy": "structure",
    "branch_relation": "structure",
    "structure_pattern": "structure",
    "structure_dynamic": "structure",
    "domain_rule": "overview",
    "time_context": "timing",
    "useful_god": "useful_god",
    "hidden_factor": "hidden_factor",
    "rule": "overview",
    "foundation": "overview",
}

CLAIM_TYPES_BY_DOMAIN: dict[DiagnosisDomain, list[str]] = {
    "overview": ["fact", "feature", "domain"],
    "career": ["feature", "path", "domain"],
    "wealth": ["feature", "path", "domain"],
    "relationship": ["feature", "path", "domain"],
    "health": ["feature", "path", "domain"],
    "timing": ["timing", "question"],
    "structure": ["feature", "path", "portrait"],
    "useful_god": ["feature", "path", "question"],
    "hidden_factor": ["feature", "question"],
}


def extract_diagnosis_features(
    *,
    feature_evidence: Sequence[FeatureEvidence],
    matched_rules: Sequence[MatchedRule] | None = None,
    diagnosis_paths: Sequence[Any] | None = None,
    limit: int | None = None,
) -> list[DiagnosisFeature]:
    rule_index = _rule_index(matched_rules or [])
    path_domains = _path_domain_counts(diagnosis_paths or [])
    rows: list[DiagnosisFeature] = []
    for evidence in feature_evidence:
        domain = _domain(evidence)
        statement = _statement(evidence, domain, rule_index=rule_index, path_domains=path_domains)
        if not statement:
            continue
        rows.append(
            DiagnosisFeature(
                feature_id=f"rbd.feature:{_safe_id(evidence.evidence_id)}",
                family=_family(evidence),
                domain=domain,
                statement=statement,
                evidence_ids=[evidence.evidence_id],
                confidence_band=_confidence_band(evidence.confidence),
                supports_claim_types=CLAIM_TYPES_BY_DOMAIN.get(domain, ["feature"]),
                counter_notes=_counter_notes(evidence),
            )
        )
    rows.sort(key=lambda row: (_domain_rank(row.domain), -_feature_confidence(row), row.feature_id))
    deduped = _dedupe_features(rows)
    if limit is not None:
        return deduped[:limit]
    return deduped


def summarize_diagnosis_features(features: Sequence[DiagnosisFeature]) -> dict[str, Any]:
    by_domain: dict[str, int] = {}
    by_family: dict[str, int] = {}
    by_confidence: dict[str, int] = {}
    for feature in features:
        by_domain[feature.domain] = by_domain.get(feature.domain, 0) + 1
        by_family[feature.family] = by_family.get(feature.family, 0) + 1
        by_confidence[feature.confidence_band] = by_confidence.get(feature.confidence_band, 0) + 1
    return {
        "version": FEATURE_ENGINE_VERSION,
        "feature_count": len(features),
        "domain_counts": dict(sorted(by_domain.items())),
        "family_counts": dict(sorted(by_family.items())),
        "confidence_counts": dict(sorted(by_confidence.items())),
        "top_feature_ids": [row.feature_id for row in list(features)[:8]],
        "boundary": "diagnosis_feature_summary_is_traceable_projection_not_new_chart_fact",
    }


def _statement(
    evidence: FeatureEvidence,
    domain: DiagnosisDomain,
    *,
    rule_index: Mapping[str, list[str]],
    path_domains: Mapping[str, int],
) -> str:
    label = evidence.label
    if evidence.domain == "chart" and evidence.kind == "fact":
        return f"{_label_text(label)}已经作为不可改写的排盘事实，后续断语只能引用它，不能重新生成四柱或日主。"
    if evidence.kind == "visibility" and evidence.domain == "ten_god":
        return f"显性十神为{_after_colon(label)}，明面事件和外显关系优先从这些十神落点进入。"
    if evidence.kind == "hidden_stem":
        return f"藏干十神为{_after_colon(label)}，可作为背景校准与反复状态的放大线索，但需要问答校准。"
    if evidence.kind == "distribution":
        return f"五行分布显示{_kv_text(label)}，适合进入旺衰、调候和流通复核，不能单点定强弱。"
    if evidence.kind == "strength_pattern_review":
        return f"旺衰格局复核显示{_kv_text(label)}，当前只支持候选路径，不支持固定格局或固定用神。"
    if evidence.kind == "month_command":
        return f"月令复核显示{_kv_text(label)}，月令是结构入口，但仍要结合反证与动态路径。"
    if evidence.kind == "seasonal_state":
        return f"旺相休囚死状态为{_kv_text(label)}，这是季节权重线索，需要和生克制化路径一起使用。"
    if evidence.kind == "source_backed_review":
        return f"M3 来源复核显示{_kv_text(label)}，知识库、规则和调候线索已经进入同一证据层。"
    if evidence.kind == "role_set":
        return f"十神角色集合显示{_kv_text(label)}，可支撑画像和领域断语，但不能脱离结构路径单断。"
    if evidence.kind == "relation":
        return f"地支关系触发{_after_colon(label)}，需要进入结构动态复核，而不是以合冲刑害单点下结论。"
    if evidence.kind == "domain_path_review":
        domains = _domain_rule_families(label)
        path_note = _path_note(path_domains)
        return f"领域规则已触发{domains}等路径，财富、事业、关系、健康只能沿证据路径表达{path_note}。"
    if evidence.kind == "explicit_layer":
        return f"时运层已绑定{_after_colon(label)}，大运流年可作为触发层参与判断，但不能独立制造事件结论。"
    if evidence.kind == "evidence_gate":
        return "用神候选仍处于证据门控，需要结构路径、调候、反证和用户反馈共同校准。"
    if evidence.kind == "energy_vector":
        return f"十神能量模型显示{_kv_text(label)}，可用于排序显著十神和波动十神，但不替代命局事实。"
    if evidence.domain == "rule":
        impacted = _rules_for_evidence(evidence.evidence_id, rule_index)
        suffix = f"，已匹配规则{', '.join(impacted[:3])}" if impacted else ""
        return f"规则证据{_label_text(label)}进入边界控制{suffix}，用于限制断语范围和追踪依据。"
    if domain in {"career", "wealth", "relationship", "health"}:
        return f"{domain} 领域证据{_label_text(label)}已进入诊断候选，必须和路径、反证、时运一起使用。"
    return f"{_label_text(label)}进入{domain}诊断特征层，用于生成可追踪断语，不新增排盘事实。"


def _domain(evidence: FeatureEvidence) -> DiagnosisDomain:
    if evidence.domain == "domain_rule":
        return "overview"
    if evidence.domain == "rule":
        return DOMAIN_MAP.get(_rule_domain(evidence), "overview")
    return DOMAIN_MAP.get(evidence.domain, "overview")


def _rule_domain(evidence: FeatureEvidence) -> str:
    for token in evidence.supports:
        if token.startswith("rule_domain:"):
            return token.removeprefix("rule_domain:")
    return "overview"


def _family(evidence: FeatureEvidence) -> str:
    if evidence.domain == "rule":
        for token in evidence.supports:
            if token.startswith("rule_domain:"):
                return f"rule:{token.removeprefix('rule_domain:')}"
    return f"{evidence.domain}:{evidence.kind}"


def _confidence_band(value: float) -> str:
    if value >= 0.75:
        return "high"
    if value >= 0.55:
        return "medium"
    return "low"


def _feature_confidence(feature: DiagnosisFeature) -> float:
    return {"high": 3.0, "medium": 2.0, "low": 1.0}.get(feature.confidence_band, 0.0)


def _domain_rank(domain: DiagnosisDomain) -> int:
    order = ["overview", "structure", "useful_god", "timing", "wealth", "career", "relationship", "health", "hidden_factor"]
    return order.index(domain) if domain in order else 99


def _counter_notes(evidence: FeatureEvidence) -> list[str]:
    notes = [f"blocks:{item}" for item in evidence.weakens[:6]]
    if evidence.boundary:
        notes.append(str(evidence.boundary))
    return notes


def _rule_index(matched_rules: Sequence[MatchedRule]) -> dict[str, list[str]]:
    index: dict[str, list[str]] = {}
    for rule in matched_rules:
        for evidence_id in rule.evidence_ids:
            index.setdefault(evidence_id, []).append(rule.rule_id)
    return index


def _rules_for_evidence(evidence_id: str, index: Mapping[str, list[str]]) -> list[str]:
    return list(index.get(evidence_id, []))


def _path_domain_counts(paths: Sequence[Any]) -> dict[str, int]:
    out: dict[str, int] = {}
    for path in paths:
        for domain in getattr(path, "domain_targets", []):
            out[str(domain)] = out.get(str(domain), 0) + 1
    return out


def _path_note(path_domains: Mapping[str, int]) -> str:
    active = [f"{domain}:{count}" for domain, count in sorted(path_domains.items()) if count]
    return f"，当前动态路径覆盖{';'.join(active[:5])}" if active else ""


def _label_text(label: str) -> str:
    return label.split(":", 1)[-1] if ":" in label else label


def _after_colon(label: str) -> str:
    return label.split(":", 1)[-1] if ":" in label else label


def _kv_text(label: str) -> str:
    value = _after_colon(label)
    return value.replace(";", "、")


def _domain_rule_families(label: str) -> str:
    tokens = [token.strip() for token in _after_colon(label).split(",") if token.strip()]
    families = [token.removeprefix("domain_rule_family:") for token in tokens if token.startswith("domain_rule_family:")]
    return "、".join(families[:6]) if families else "领域规则"


def _safe_id(value: str) -> str:
    return value.replace(":", ".").replace("/", ".")


def _dedupe_features(features: Sequence[DiagnosisFeature]) -> list[DiagnosisFeature]:
    seen: set[tuple[str, str, str]] = set()
    out: list[DiagnosisFeature] = []
    for feature in features:
        key = (feature.domain, feature.family, feature.statement)
        if key in seen:
            continue
        seen.add(key)
        out.append(feature)
    return out
