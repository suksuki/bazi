from __future__ import annotations

from v20.answer.measurement_policy import domain_label, measurement_stage
from v20.features.schema import FeatureLayer


PORTRAIT_INTELLIGENCE_VERSION = "v20.portrait_intelligence.v1"


def build_portrait_intelligence(
    feature_layer: FeatureLayer,
    portrait_projection: dict[str, object],
    *,
    knowledge_semantic_model: dict[str, object] | None = None,
    feature_discovery: dict[str, object] | None = None,
    limit: int = 10,
) -> dict[str, object]:
    semantic_index = _semantic_index(knowledge_semantic_model)
    discovery_index = _discovery_index(feature_discovery)
    axes = []
    for axis in _portrait_axes(portrait_projection):
        domain = str(axis.get("domain", ""))
        semantic = semantic_index.get(domain, {})
        discovery = discovery_index.get(domain, {})
        feature_ids = tuple(str(item) for item in axis.get("feature_ids", ()) if str(item))
        sub_axes = _sub_axis_candidates(domain, semantic, feature_ids)
        score = _axis_score(axis, semantic, discovery)
        axes.append(
            {
                "axis_id": axis.get("axis_id", f"portrait.axis.{domain}"),
                "domain": domain,
                "label": axis.get("label") or domain_label(domain),
                "measurement_stage": axis.get("measurement_stage") or measurement_stage(domain),
                "intelligence_score": score,
                "feature_count": axis.get("feature_count", 0),
                "knowledge_ref_count": axis.get("knowledge_ref_count", 0),
                "semantic_weight": semantic.get("semantic_weight", 0),
                "discovery_score": discovery.get("discovery_score", 0),
                "sub_axis_candidates": sub_axes,
                "profile_tags": _profile_tags(domain, sub_axes, discovery),
                "calibration_prompt": _calibration_prompt(domain, sub_axes),
                "runtime_mutation": False,
            }
        )
    ranked_axes = sorted(axes, key=lambda row: (float(row["intelligence_score"]), str(row["domain"])), reverse=True)
    return {
        "version": PORTRAIT_INTELLIGENCE_VERSION,
        "status": "ready" if ranked_axes else "empty",
        "role": "knowledge_semantic_feature_discovery_portrait_model",
        "axis_models": ranked_axes[:limit],
        "profile_tags": _global_profile_tags(ranked_axes),
        "interaction_prompts": _interaction_prompts(ranked_axes),
        "training_lane": {
            "status": "shadow_ready",
            "allowed_updates": [
                "portrait_sub_axis_label_weight",
                "feature_to_axis_prior",
                "calibration_prompt_order",
            ],
            "blocked_updates": [
                "personality_verdict",
                "answer_conclusion",
                "question_truth_override",
            ],
            "runtime_mutation": False,
        },
        "runtime_mutation": False,
        "guardrails": [
            "PORTRAIT_INTELLIGENCE_IS_LABEL_AND_CALIBRATION_MODEL",
            "FEATURE_DISCOVERY_DRIVES_EMPHASIS_ONLY",
            "KNOWLEDGE_BOUNDARIES_PREVENT_VERDICTS",
            "NO_PERSONALITY_OR_FORTUNE_LABEL",
        ],
    }


def validate_portrait_intelligence(report: dict[str, object]) -> dict[str, object]:
    failures: list[str] = []
    if report.get("version") != PORTRAIT_INTELLIGENCE_VERSION:
        failures.append("version_mismatch")
    if report.get("runtime_mutation") is not False:
        failures.append("runtime_mutation_must_be_false")
    for axis in report.get("axis_models", ()):
        if not isinstance(axis, dict):
            failures.append("malformed_axis_model")
            continue
        if float(axis.get("intelligence_score", -1)) < 0:
            failures.append(f"negative_axis_score:{axis.get('domain', '')}")
        for candidate in axis.get("sub_axis_candidates", ()):
            if isinstance(candidate, dict) and candidate.get("runtime_allowed") is True:
                failures.append(f"sub_axis_runtime_allowed:{candidate.get('candidate_id', '')}")
    return {
        "version": "v20.portrait_intelligence_validation.v1",
        "status": "pass" if not failures else "fail",
        "ok": not failures,
        "axis_count": len([row for row in report.get("axis_models", ()) if isinstance(row, dict)]),
        "failures": failures,
        "runtime_mutation": False,
        "guardrails": [
            "VALIDATION_ONLY",
            "PORTRAIT_INTELLIGENCE_REMAINS_CALIBRATION_SURFACE",
            "NO_RUNTIME_MUTATION",
        ],
    }


def _portrait_axes(portrait_projection: dict[str, object]) -> list[dict[str, object]]:
    return [row for row in portrait_projection.get("axes", ()) if isinstance(row, dict)]


def _semantic_index(model: dict[str, object] | None) -> dict[str, dict[str, object]]:
    if not isinstance(model, dict):
        return {}
    return {
        str(row.get("domain", "")): row
        for row in model.get("domain_models", ())
        if isinstance(row, dict) and row.get("domain")
    }


def _discovery_index(report: dict[str, object] | None) -> dict[str, dict[str, object]]:
    if not isinstance(report, dict):
        return {}
    return {
        str(row.get("domain", "")): row
        for row in report.get("domain_hypotheses", ())
        if isinstance(row, dict) and row.get("domain")
    }


def _sub_axis_candidates(domain: str, semantic: dict[str, object], feature_ids: tuple[str, ...]) -> tuple[dict[str, object], ...]:
    rows = []
    for candidate in semantic.get("portrait_label_candidates", ())[:4]:
        if not isinstance(candidate, dict):
            continue
        rows.append(
            {
                "candidate_id": candidate.get("candidate_id", ""),
                "label": candidate.get("label", domain_label(domain)),
                "domain": domain,
                "source_knowledge_id": candidate.get("source_knowledge_id", ""),
                "matched_feature_ids": tuple(
                    feature_id
                    for feature_id in feature_ids
                    if any(feature_id.startswith(str(hook)) for hook in candidate.get("feature_hooks", ()))
                ),
                "status": "shadow_label_candidate",
                "runtime_allowed": False,
            }
        )
    if not rows:
        rows.append(
            {
                "candidate_id": f"v20.portrait_label.{domain}.fallback",
                "label": f"{domain_label(domain)}结构观察",
                "domain": domain,
                "source_knowledge_id": "",
                "matched_feature_ids": feature_ids[:4],
                "status": "fallback_label_candidate",
                "runtime_allowed": False,
            }
        )
    return tuple(rows)


def _profile_tags(domain: str, sub_axes: tuple[dict[str, object], ...], discovery: dict[str, object]) -> tuple[dict[str, object], ...]:
    score = float(discovery.get("discovery_score", 0.0))
    return tuple(
        {
            "tag_id": f"v20.profile_tag.{domain}.{index:02d}",
            "label": row.get("label", domain_label(domain)),
            "domain": domain,
            "score": round(min(0.99, score + 0.05), 3) if score else 0.32,
            "source": "semantic_portrait_axis",
            "runtime_allowed": False,
        }
        for index, row in enumerate(sub_axes[:3])
    )


def _global_profile_tags(axes: list[dict[str, object]]) -> tuple[dict[str, object], ...]:
    tags = []
    for axis in axes[:5]:
        tags.extend(axis.get("profile_tags", ())[:2])
    return tuple(tags[:10])


def _interaction_prompts(axes: list[dict[str, object]]) -> tuple[dict[str, object], ...]:
    prompts = []
    for axis in axes[:5]:
        prompts.append(
            {
                "domain": axis.get("domain", ""),
                "label": axis.get("label", ""),
                "prompt": f"是否继续校准“{axis.get('label', '')}”画像轴的证据边界？",
                "runtime_mutation": False,
            }
        )
    return tuple(prompts)


def _axis_score(axis: dict[str, object], semantic: dict[str, object], discovery: dict[str, object]) -> float:
    peak = float(axis.get("peak_confidence", 0.0))
    semantic_weight = float(semantic.get("semantic_weight", 0.0))
    discovery_score = float(discovery.get("discovery_score", 0.0))
    knowledge_count = int(axis.get("knowledge_ref_count", 0))
    return round(min(0.99, peak * 0.42 + discovery_score * 0.32 + semantic_weight + min(0.08, knowledge_count * 0.018)), 3)


def _calibration_prompt(domain: str, sub_axes: tuple[dict[str, object], ...]) -> str:
    labels = "、".join(str(row.get("label", "")) for row in sub_axes[:3] if row.get("label"))
    if labels:
        return f"校准“{domain_label(domain)}”画像轴时，优先复核：{labels}。"
    return f"校准“{domain_label(domain)}”画像轴是否符合当前命理特征证据。"
