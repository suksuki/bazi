from __future__ import annotations

from v20.features.schema import BaziFeature, MacroFeature

MACRO_TITLES = {
    "strength": "日主强弱主轴",
    "useful_god": "用神候选主轴",
    "ten_god": "十神结构主轴",
    "branch": "地支关系主轴",
    "time": "时间层触发主轴",
    "wealth": "财星与收入结构主轴",
    "pattern": "格局审查主轴",
}


def cluster_features(features: tuple[BaziFeature, ...] | list[BaziFeature]) -> tuple[MacroFeature, ...]:
    grouped: dict[str, list[BaziFeature]] = {}
    for feature in features:
        grouped.setdefault(feature.domain, []).append(feature)

    rows: list[MacroFeature] = []
    for domain, domain_features in grouped.items():
        ordered = sorted(domain_features, key=lambda row: (row.confidence, row.feature_id), reverse=True)
        rows.append(
            MacroFeature(
                macro_id=f"macro.{domain}",
                title=MACRO_TITLES.get(domain, f"{domain} 主轴"),
                domain=domain,
                feature_ids=tuple(feature.feature_id for feature in ordered),
                evidence_count=sum(len(feature.evidence_refs) for feature in ordered),
                peak_confidence=max(feature.confidence for feature in ordered),
                summary=_summary_for(domain, ordered),
            )
        )
    return tuple(sorted(rows, key=lambda row: (row.peak_confidence, row.macro_id), reverse=True))


def default_context_feature_ids(macro_features: tuple[MacroFeature, ...], *, limit: int = 8) -> tuple[str, ...]:
    selected: list[str] = []
    for macro in macro_features:
        selected.extend(macro.feature_ids[:2])
        if len(selected) >= limit:
            break
    return tuple(dict.fromkeys(selected[:limit]))


def _summary_for(domain: str, features: list[BaziFeature]) -> str:
    count = len(features)
    evidence_count = sum(len(feature.evidence_refs) for feature in features)
    if domain == "branch" and evidence_count >= 3:
        return f"地支关系证据较密集，默认折叠为 {count} 个特征、{evidence_count} 条证据。"
    if domain == "ten_god" and count >= 2:
        return f"十神显隐材料并存，默认聚合为 {count} 个特征。"
    return f"默认聚合 {count} 个特征、{evidence_count} 条证据，深挖时再展开子特征。"
