from __future__ import annotations

import hashlib
import json

from v20.api.runtime import run_runtime_from_pillars
from v20.corpus.canonical_case import CanonicalCase


def precompute_case(case: CanonicalCase) -> dict[str, object]:
    result = run_runtime_from_pillars(
        *case.pillar_displays,
        input_id=case.case_id,
        flow_year_pillar=case.time_pillars.get("flow_year", ""),
        luck_pillar=case.time_pillars.get("luck", ""),
        flow_month_pillar=case.time_pillars.get("flow_month", ""),
    )
    return {
        "version": "v20.corpus_precompute.v1",
        "case": case.to_dict(),
        "feature_count": result["feature_layer"]["feature_count"],
        "measurement_topic_count": result["measurement_report"]["topic_count"],
        "question_count": len(result["questions"]),
        "label_snapshot": build_label_snapshot(case, result),
        "answer_plan_version": result["answer_plan"]["version"],
        "llm_assist_status": result["llm_assist"]["status"],
        "runtime_mutation": False,
        "guardrails": ["PRECOMPUTE_DRY_RUN_ONLY", "NO_PROMOTION"],
    }


def build_label_snapshot(case: CanonicalCase, runtime_result: dict[str, object]) -> dict[str, object]:
    chart = runtime_result["chart_facts"]
    core = runtime_result["core_inference"]
    feature_layer = runtime_result["feature_layer"]
    measurement_report = runtime_result["measurement_report"]
    questions = runtime_result["questions"]
    knowledge_refs = runtime_result["knowledge_refs"]
    portrait_projection = runtime_result.get("decision_report", {}).get("portrait_projection", {})
    features = tuple(row for row in feature_layer["features"] if isinstance(row, dict))
    mainlines = tuple(row for row in runtime_result.get("decision_report", {}).get("mainlines", ()) if isinstance(row, dict))
    relation_types = tuple(
        sorted(
            {
                str(row.get("relation_type", ""))
                for row in chart.get("relation_hits", ())
                if isinstance(row, dict) and row.get("relation_type")
            }
        )
    )
    visible_ten_gods = tuple(
        sorted(
            {
                str(row.get("label", ""))
                for row in chart.get("visible_ten_gods", ())
                if isinstance(row, dict) and row.get("label")
            }
        )
    )
    hidden_ten_gods = tuple(
        sorted(
            {
                str(row.get("label", ""))
                for row in chart.get("hidden_ten_gods", ())
                if isinstance(row, dict) and row.get("label")
            }
        )
    )
    label_payload = {
        "case_id": case.case_id,
        "input_hash": case.input_hash,
        "pillar_displays": case.pillar_displays,
        "day_master": chart.get("day_master", ""),
        "day_master_element": chart.get("day_master_element", ""),
        "day_master_capacity": core.get("day_master_capacity", ""),
        "feature_ids": tuple(str(row.get("feature_id", "")) for row in features),
        "salience_feature_ids": tuple(
            str(row.get("feature_id", ""))
            for row in features
            if _is_salience_feature_id(str(row.get("feature_id", "")))
        ),
        "salience_domains": tuple(
            sorted(
                {
                    str(row.get("domain", ""))
                    for row in features
                    if row.get("domain") and _is_salience_feature_id(str(row.get("feature_id", "")))
                }
            )
        ),
        "feature_domains": tuple(sorted({str(row.get("domain", "")) for row in features if row.get("domain")})),
        "wealth_material_level": _wealth_material_level(features),
        "mainline_keys": tuple(str(row.get("mainline_key", "")) for row in mainlines if row.get("mainline_key")),
        "mainline_domains": tuple(str(row.get("domain", "")) for row in mainlines if row.get("domain")),
        "macro_feature_domains": tuple(
            sorted(
                {
                    str(row.get("domain", ""))
                    for row in feature_layer.get("macro_features", ())
                    if isinstance(row, dict) and row.get("domain")
                }
            )
        ),
        "measurement_domains": tuple(measurement_report.get("applied_domain_keys", ())),
        "question_keys": tuple(str(row.get("question_key", "")) for row in questions if isinstance(row, dict)),
        "knowledge_ids": tuple(str(row.get("knowledge_id", "")) for row in knowledge_refs if isinstance(row, dict)),
        "portrait_domains": tuple(str(row.get("domain", "")) for row in portrait_projection.get("axes", ()) if isinstance(row, dict)),
        "relation_types": relation_types,
        "visible_ten_gods": visible_ten_gods,
        "hidden_ten_gods": hidden_ten_gods,
        "useful_god_candidate_count": _useful_god_candidate_count(features),
        "wealth_feature_present": any(str(row.get("feature_id", "")) == "feature.wealth.visible_material" for row in features),
        "evidence_density": {
            "feature_count": feature_layer.get("feature_count", 0),
            "knowledge_ref_count": runtime_result["knowledge_report"].get("count", 0),
            "portrait_axis_count": portrait_projection.get("axis_count", 0),
            "mainline_count": len(mainlines),
        },
        "label_policy": "structural_features_and_decision_portrait_projection_axes_only",
        "guardrails": [
            "NO_DESTINY_TRUTH_LABEL",
            "NO_EVENT_OUTCOME_LABEL",
            "NO_PERSONALITY_VERDICT_LABEL",
            "FEATURE_COMPILER_OWNS_LABELS",
        ],
    }
    label_payload["snapshot_hash"] = hashlib.sha256(
        json.dumps(label_payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()[:16]
    return label_payload


def _is_salience_feature_id(feature_id: str) -> bool:
    return feature_id.startswith(
        (
            "feature.ten_god.focus.",
            "feature.element.prominent.",
            "feature.element.weak.",
            "feature.branch.relation_type.",
            "feature.time.relation_type.",
            "feature.time.ten_god.",
        )
    )


def _wealth_material_level(features: tuple[dict[str, object], ...]) -> str:
    ids = {str(row.get("feature_id", "")) for row in features}
    if "feature.wealth.visible_material" in ids:
        return "visible"
    if "feature.wealth.hidden_material" in ids:
        return "hidden_only"
    if "feature.wealth.material_not_visible" in ids:
        return "not_visible"
    return "unknown"


def _useful_god_candidate_count(features: tuple[dict[str, object], ...]) -> int:
    for feature in features:
        if str(feature.get("feature_id", "")) != "feature.useful_god.candidate_paths":
            continue
        refs = feature.get("evidence_refs", ())
        if isinstance(refs, (list, tuple)):
            return len(refs)
    return 0
