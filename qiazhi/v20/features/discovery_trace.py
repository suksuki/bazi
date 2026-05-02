from __future__ import annotations

from v20.features.schema import BaziFeature


DOMAIN_MECHANISM_TYPES: dict[str, str] = {
    "strength": "capacity_arbitration",
    "useful_god": "useful_god_path",
    "ten_god": "ten_god_structure",
    "element": "element_climate_balance",
    "branch": "branch_relation_mechanism",
    "time": "time_activation",
    "wealth": "topic_material_projection",
    "career": "topic_material_projection",
    "relationship": "topic_material_projection",
    "health": "topic_material_projection",
    "pattern": "pattern_review",
}

TOPIC_PROJECTIONS: tuple[dict[str, object], ...] = (
    {
        "projection_id": "projection.wealth",
        "topic_domain": "wealth",
        "title": "财富主题投射",
        "source_domains": ("wealth", "strength", "ten_god", "branch", "time", "useful_god"),
        "output_focus": ("材料", "机会", "承接", "波动", "风险"),
        "boundary": "不把财星存在直接表达为财运好。",
    },
    {
        "projection_id": "projection.career",
        "topic_domain": "career",
        "title": "事业主题投射",
        "source_domains": ("career", "ten_god", "pattern", "strength", "branch", "time"),
        "output_focus": ("规则", "平台", "表达", "承接", "冲突"),
        "boundary": "不把官杀或印星单点命中直接表达为事业成败。",
    },
    {
        "projection_id": "projection.relationship",
        "topic_domain": "relationship",
        "title": "关系主题投射",
        "source_domains": ("relationship", "ten_god", "branch", "palace", "blind_lifa", "time"),
        "output_focus": ("互动", "合作", "竞争", "边界", "引动"),
        "boundary": "关系主题必须保留宫位、十神互动和反证边界。",
    },
    {
        "projection_id": "projection.romance",
        "topic_domain": "romance",
        "title": "感情主题投射",
        "source_domains": ("relationship", "palace", "ten_god", "branch", "time"),
        "output_focus": ("伴侣星", "夫妻宫", "合冲", "承接", "安全边界"),
        "boundary": "感情主题在专属规则完成前沿用 relationship evidence domain。",
    },
    {
        "projection_id": "projection.health",
        "topic_domain": "health",
        "title": "健康主题投射",
        "source_domains": ("health", "element", "strength", "time"),
        "output_focus": ("偏枯", "寒暖燥湿", "压力", "恢复", "禁断边界"),
        "boundary": "健康只做结构和生活节律表达，不做医疗诊断。",
    },
)


def build_feature_discovery_trace(features: tuple[BaziFeature, ...] | list[BaziFeature]) -> dict[str, object]:
    feature_rows = tuple(features)
    decision_states = tuple(_decision_state_for(row) for row in feature_rows)
    topic_projections = _matched_topic_projections(feature_rows)
    return {
        "version": "v20.feature_discovery_trace.v1",
        "status": "ready",
        "source": "compiled_bazi_features_phase1_projection",
        "feature_count": len(feature_rows),
        "evidence_atom_count": len(_evidence_atoms(feature_rows)),
        "rule_path_count": len(feature_rows),
        "mechanism_path_count": len(_mechanism_paths(feature_rows)),
        "decision_state_count": len(decision_states),
        "topic_projection_count": len(topic_projections),
        "evidence_atoms": _evidence_atoms(feature_rows),
        "rule_paths": _rule_paths(feature_rows),
        "mechanism_paths": _mechanism_paths(feature_rows),
        "decision_states": decision_states,
        "topic_projections": topic_projections,
        "runtime_mutation": False,
        "guardrails": (
            "TRACE_IS_INTERNAL_REASONING_CONTEXT",
            "TRACE_IS_NOT_USER_FACING_VERDICT",
            "BaziFeature_REMAINS_PRODUCT_CONTRACT",
            "TOPIC_PROJECTION_REQUIRED_BEFORE_APPLICATION_OUTPUT",
        ),
    }


def _evidence_atoms(features: tuple[BaziFeature, ...]) -> tuple[dict[str, object], ...]:
    rows: dict[str, dict[str, object]] = {}
    for feature in features:
        for ref in feature.evidence_refs:
            atom_id = f"evidence.{feature.domain}.{ref.ref_id}"
            rows.setdefault(
                atom_id,
                {
                    "atom_id": atom_id,
                    "domain": feature.domain,
                    "evidence_type": ref.kind,
                    "title": ref.title,
                    "required_fact_types": (ref.source_layer,),
                    "supports": (feature.feature_id,),
                    "boundary": feature.boundary,
                },
            )
    return tuple(rows[key] for key in sorted(rows))


def _rule_paths(features: tuple[BaziFeature, ...]) -> tuple[dict[str, object], ...]:
    rows = []
    for feature in features:
        evidence_atom_ids = tuple(f"evidence.{feature.domain}.{ref.ref_id}" for ref in feature.evidence_refs)
        state = _decision_state_for(feature)["state"]
        rows.append(
            {
                "path_id": f"rule_path.{feature.feature_id}",
                "title": feature.title,
                "domain": feature.domain,
                "evidence_atom_ids": evidence_atom_ids,
                "target_feature": feature.feature_id,
                "decision_state_policy": state,
                "counter_evidence_ids": (),
            }
        )
    return tuple(rows)


def _mechanism_paths(features: tuple[BaziFeature, ...]) -> tuple[dict[str, object], ...]:
    by_domain: dict[str, list[BaziFeature]] = {}
    for feature in features:
        by_domain.setdefault(feature.domain, []).append(feature)
    rows = []
    for domain, domain_features in sorted(by_domain.items()):
        rows.append(
            {
                "mechanism_id": f"mechanism.{domain}",
                "title": f"{domain} feature mechanism path",
                "mechanism_type": DOMAIN_MECHANISM_TYPES.get(domain, "feature_mechanism"),
                "source_feature_ids": tuple(row.feature_id for row in domain_features),
                "target_domains": _target_domains(domain),
                "boundary": domain_features[0].boundary if domain_features else "",
            }
        )
    return tuple(rows)


def _decision_state_for(feature: BaziFeature) -> dict[str, object]:
    state = "candidate"
    if feature.readiness == "ready" and feature.confidence >= 0.48:
        state = "confirmed"
    elif feature.readiness == "ready":
        state = "candidate"
    elif feature.readiness == "boundary_ready":
        state = "weak_candidate"
    elif feature.domain == "time":
        state = "volatile"
    elif feature.readiness == "review_ready":
        state = "requires_review"
    if "not_visible" in feature.feature_id or "quiet" in feature.feature_id:
        state = "out_of_scope" if feature.confidence < 0.33 else "weak_candidate"
    if "hidden_material" in feature.feature_id:
        state = "mixed"
    return {
        "state_id": f"decision_state.{feature.feature_id}",
        "state": state,
        "title": feature.title,
        "source_feature_id": feature.feature_id,
        "domain": feature.domain,
        "confidence": feature.confidence,
        "readiness": feature.readiness,
    }


def _matched_topic_projections(
    features: tuple[BaziFeature, ...],
) -> tuple[dict[str, object], ...]:
    feature_domains = {row.domain for row in features}
    rows = []
    for projection in TOPIC_PROJECTIONS:
        source_domains = set(projection.get("source_domains", ()))
        matched = tuple(sorted(feature_domains & source_domains))
        if matched:
            rows.append(
                {
                    "projection_id": projection.get("projection_id", ""),
                    "topic_domain": projection.get("topic_domain", ""),
                    "title": projection.get("title", ""),
                    "matched_source_domains": matched,
                    "output_focus": projection.get("output_focus", ()),
                    "boundary": projection.get("boundary", ""),
                }
            )
    return tuple(rows)


def _target_domains(domain: str) -> tuple[str, ...]:
    if domain in {"strength", "ten_god", "branch", "time", "useful_god", "pattern"}:
        return ("wealth", "career", "relationship", "romance", "health")
    if domain == "wealth":
        return ("wealth",)
    if domain == "health":
        return ("health",)
    if domain == "relationship":
        return ("relationship", "romance")
    return (domain,)
