from __future__ import annotations

from collections.abc import Mapping

from v30.semantics.ontology import BAZI_SEMANTIC_ONTOLOGY_VERSION, MACRO_DOMAIN_ONTOLOGY, TEN_GOD_ONTOLOGY

SEMANTIC_DOMAIN_MAPPING_VERSION = "v30.semantic_domain_mapping.v1"

_DOMAIN_ALIASES = {
    "career": "career",
    "wealth": "wealth",
    "relationship": "relationship",
    "health": "health",
    "timing": "timing",
    "hidden_factor": "hidden_factor",
    "family": "family",
    "children": "family",
    "learning": "career",
    "decision": "career",
    "practical_reading": "career",
    "useful_god": "career",
    "structure": "career",
    "overview": "career",
}

_INTENT_DOMAIN = {
    "ask_user_career_direction": "career",
    "ask_user_wealth_tendency": "wealth",
    "ask_user_relationship_pattern": "relationship",
    "ask_user_timing_pressure": "timing",
    "ask_user_decision_blindspot": "career",
    "discover_hidden_factor_amplifier": "hidden_factor",
    "review_useful_god_candidate_paths": "career",
    "clarify_practical_reading_priority": "career",
    "confirm_missing_time_context": "timing",
}


def semantic_projection_for_claim(claim: Mapping[str, object]) -> dict[str, object]:
    domain = _canonical_domain(str(claim.get("domain") or claim.get("claim_level") or "career"))
    drivers = _drivers_for_domain(domain)
    ten_gods = _top_ten_gods_for_domain(domain)
    return {
        "version": SEMANTIC_DOMAIN_MAPPING_VERSION,
        "ontology_version": BAZI_SEMANTIC_ONTOLOGY_VERSION,
        "macro_domain": domain,
        "macro_label": _domain_label(domain),
        "semantic_drivers": drivers[:4],
        "ten_god_drivers": ten_gods[:4],
        "keywords": _domain_keywords(domain)[:8],
        "weight_slot": f"semantic.claim.{domain}",
        "boundary": "semantic_projection_is_mapping_not_new_bazi_fact",
    }


def semantic_projection_for_question(question: Mapping[str, object]) -> dict[str, object]:
    intent_id = str(question.get("intent_id") or "")
    topic = str(question.get("topic") or "")
    domain = _canonical_domain(topic or _INTENT_DOMAIN.get(intent_id, "career"))
    slots = list(MACRO_DOMAIN_ONTOLOGY.get(domain, {}).get("question_slots", []))
    gain = question.get("expected_information_gain", {})
    gain = gain if isinstance(gain, Mapping) else {}
    primary_gain = str(gain.get("primary_gain") or question.get("question_value") or "")
    return {
        "version": SEMANTIC_DOMAIN_MAPPING_VERSION,
        "ontology_version": BAZI_SEMANTIC_ONTOLOGY_VERSION,
        "macro_domain": domain,
        "macro_label": _domain_label(domain),
        "semantic_drivers": _drivers_for_domain(domain)[:4],
        "question_slots": slots[:6],
        "selected_slot": _selected_slot(domain, primary_gain, slots),
        "ten_god_drivers": _top_ten_gods_for_domain(domain)[:4],
        "keywords": _domain_keywords(domain)[:8],
        "weight_slot": f"semantic.question.{domain}",
        "boundary": "semantic_question_projection_guides_dialogue_policy_not_chart_fact",
    }


def build_semantic_dialogue_trace(
    *,
    claim_scores: list[dict[str, object]],
    recommendations: list[dict[str, object]],
    current_question: dict[str, object],
) -> dict[str, object]:
    top_claims = [
        {
            "claim_id": str(row.get("claim_id") or ""),
            "score": _float(row.get("score"), 0.0),
            "semantic": semantic_projection_for_claim(row),
        }
        for row in claim_scores[:5]
    ]
    question_semantic = semantic_projection_for_question(current_question) if current_question else {}
    candidate_domains = sorted({
        semantic_projection_for_question(row).get("macro_domain", "")
        for row in recommendations
        if isinstance(row, dict)
    })
    return {
        "version": "v30.semantic_dialogue_trace.v1",
        "ontology_version": BAZI_SEMANTIC_ONTOLOGY_VERSION,
        "top_claims": top_claims,
        "current_question_semantic": question_semantic,
        "candidate_macro_domains": [str(row) for row in candidate_domains if row],
        "training_slots": sorted({
            str(row.get("semantic", {}).get("weight_slot") or "")
            for row in top_claims
            if isinstance(row.get("semantic"), dict)
        } | ({str(question_semantic.get("weight_slot") or "")} if question_semantic else set())),
        "boundary": "semantic_dialogue_trace_feeds_training_without_changing_chart_or_claim_facts",
    }


def _canonical_domain(value: str) -> str:
    key = value.strip().lower()
    return _DOMAIN_ALIASES.get(key, key if key in MACRO_DOMAIN_ONTOLOGY else "career")


def _domain_label(domain: str) -> str:
    row = MACRO_DOMAIN_ONTOLOGY.get(domain, {})
    return str(row.get("label") or domain)


def _domain_keywords(domain: str) -> list[str]:
    row = MACRO_DOMAIN_ONTOLOGY.get(domain, {})
    keywords = row.get("keywords", [])
    return [str(item) for item in keywords] if isinstance(keywords, list) else []


def _top_ten_gods_for_domain(domain: str) -> list[dict[str, object]]:
    weights = MACRO_DOMAIN_ONTOLOGY.get(domain, {}).get("ten_god_weights", {})
    if not isinstance(weights, Mapping):
        return []
    rows = []
    for key, weight in weights.items():
        item = TEN_GOD_ONTOLOGY.get(str(key), {})
        rows.append({
            "ten_god": str(key),
            "label": str(item.get("label") or key),
            "weight": _float(weight, 0.0),
        })
    rows.sort(key=lambda row: (-float(row["weight"]), str(row["ten_god"])))
    return rows


def _drivers_for_domain(domain: str) -> list[str]:
    drivers: list[str] = []
    for row in _top_ten_gods_for_domain(domain):
        item = TEN_GOD_ONTOLOGY.get(str(row.get("ten_god") or ""), {})
        for driver in item.get("drivers", []):
            if isinstance(driver, str) and driver not in drivers:
                drivers.append(driver)
    return drivers


def _selected_slot(domain: str, primary_gain: str, slots: list[str]) -> str:
    normalized = primary_gain.lower()
    for slot in slots:
        if slot in normalized:
            return slot
    if domain == "hidden_factor":
        for slot in ("recurrence", "year", "trigger", "cost", "outcome"):
            if slot in normalized:
                return slot
    return slots[0] if slots else domain


def _float(value: object, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default
