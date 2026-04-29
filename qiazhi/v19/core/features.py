from __future__ import annotations

from typing import Any, Dict, List

from v19.core.chart import (
    BRANCH_CLASHES,
    BRANCH_COMBINATIONS,
    BRANCH_HARMS,
    BRANCH_HIDDEN_STEMS,
    VAULT_BRANCHES,
    branch_pairs,
    element_of_stem,
    normalize_chart,
    stable_hash,
    ten_god,
)


V19_CORE_FEATURE_VERSION = "v19.core_feature.v1"


def _feature(feature_id: str, feature_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "feature_id": feature_id,
        "feature_type": feature_type,
        "payload": dict(payload),
        "layer": "feature",
        "version": V19_CORE_FEATURE_VERSION,
    }


def extract_core_features(chart: Dict[str, Any]) -> Dict[str, Any]:
    normalized = normalize_chart(chart)
    pillars = normalized["pillars"]
    day_stem = pillars["day"]["stem"]
    day_element = element_of_stem(day_stem)
    feature_rows: List[Dict[str, Any]] = []
    element_weights: Dict[str, float] = {"wood": 0.0, "fire": 0.0, "earth": 0.0, "metal": 0.0, "water": 0.0}
    ten_god_weights: Dict[str, float] = {"peer": 0.0, "output": 0.0, "wealth": 0.0, "officer": 0.0, "seal": 0.0, "unknown": 0.0}

    for pillar_name, pillar in pillars.items():
        stem = pillar["stem"]
        branch = pillar["branch"]
        stem_element = element_of_stem(stem)
        stem_ten_god = ten_god(day_stem, stem)
        if stem_element:
            element_weights[stem_element] += 1.0
        ten_god_weights[stem_ten_god] = ten_god_weights.get(stem_ten_god, 0.0) + 1.0
        feature_rows.append(
            _feature(
                f"pillar.{pillar_name}",
                "pillar_fact",
                {"pillar": pillar_name, "stem": stem, "branch": branch, "stem_element": stem_element, "stem_ten_god": stem_ten_god},
            )
        )
        for hidden_index, (hidden_stem, weight) in enumerate(BRANCH_HIDDEN_STEMS.get(branch, [])):
            hidden_element = element_of_stem(hidden_stem)
            hidden_ten_god = ten_god(day_stem, hidden_stem)
            if hidden_element:
                element_weights[hidden_element] += weight * 0.6
            ten_god_weights[hidden_ten_god] = ten_god_weights.get(hidden_ten_god, 0.0) + weight * 0.6
            feature_rows.append(
                _feature(
                    f"hidden.{pillar_name}.{hidden_index}",
                    "hidden_stem_fact",
                    {
                        "pillar": pillar_name,
                        "branch": branch,
                        "hidden_stem": hidden_stem,
                        "weight": weight,
                        "element": hidden_element,
                        "ten_god": hidden_ten_god,
                    },
                )
            )

    branches = [pillars[name]["branch"] for name in ["year", "month", "day", "hour"]]
    for left, right in branch_pairs(branches):
        pair = frozenset((left, right))
        if pair in BRANCH_CLASHES:
            relation_type = "clash"
        elif pair in BRANCH_COMBINATIONS:
            relation_type = "combination"
        elif pair in BRANCH_HARMS:
            relation_type = "harm"
        else:
            continue
        feature_rows.append(
            _feature(
                f"branch_relation.{left}{right}.{relation_type}",
                "branch_relation_fact",
                {"left": left, "right": right, "relation_type": relation_type},
            )
        )

    for pillar_name, pillar in pillars.items():
        branch = pillar["branch"]
        if branch not in VAULT_BRANCHES:
            continue
        hidden_ten_gods = [ten_god(day_stem, hidden_stem) for hidden_stem, _ in BRANCH_HIDDEN_STEMS.get(branch, [])]
        feature_rows.append(
            _feature(
                f"vault.{pillar_name}.{branch}",
                "vault_fact",
                {"pillar": pillar_name, "branch": branch, "hidden_ten_gods": hidden_ten_gods, "contains_wealth": "wealth" in hidden_ten_gods},
            )
        )

    for flow_name in ["luck", "flow"]:
        pillar = normalized.get(flow_name) or {}
        stem = pillar.get("stem", "")
        branch = pillar.get("branch", "")
        if not stem and not branch:
            continue
        feature_rows.append(
            _feature(
                f"{flow_name}.{stem}{branch}",
                "flow_pillar_fact",
                {
                    "flow_type": flow_name,
                    "stem": stem,
                    "branch": branch,
                    "stem_element": element_of_stem(stem),
                    "stem_ten_god": ten_god(day_stem, stem),
                    "hidden_ten_gods": [ten_god(day_stem, hidden_stem) for hidden_stem, _ in BRANCH_HIDDEN_STEMS.get(branch, [])],
                },
            )
        )

    return {
        "version": V19_CORE_FEATURE_VERSION,
        "chart_id": normalized["chart_id"],
        "day_master": {"stem": day_stem, "element": day_element},
        "features": feature_rows,
        "element_weights": element_weights,
        "ten_god_weights": ten_god_weights,
        "guardrails": ["FEATURES_ARE_FACTS", "NO_CONCLUSION", "NO_THEME_OUTPUT"],
        "content_hash": "sha256:" + stable_hash({"chart": normalized, "features": feature_rows}),
    }
