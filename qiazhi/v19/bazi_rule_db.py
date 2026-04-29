from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any, Dict, List, Tuple

from v19.core.chart import BRANCH_HIDDEN_STEMS, VAULT_BRANCHES, element_of_stem
from v19.runtime import RUNTIME, utc_now

RULE_DB_VERSION = "v19.bazi_rule_db.v1"
STRUCTURAL_SIGNAL_VERSION = "v19.p9.structural_rule_signals.v1"
RULE_DB_FILE = RUNTIME / "bazi_rule_db.json"
SOURCE_ARCHIVE_FILE = RUNTIME / "bazi_source_archive.json"

GUARDRAILS = [
    "RULE_DB_INGESTION",
    "NO_LLM_AUTHORITY",
    "NO_PLUGIN_BLACK_BOX",
    "R4_ARCHIVE_ONLY",
]


def bazi_rule_db_status() -> Dict[str, Any]:
    state, storage = _load_state()
    rules = list(state.get("rules") or [])
    return {
        "ok": True,
        "version": RULE_DB_VERSION,
        "storage": storage,
        "runtime_scope": "rule_database_available_for_engine_adapter",
        "counts": {
            "rules": len(rules),
            "by_domain": _count_by(rules, "domain"),
            "by_risk_level": _count_by(rules, "risk_level"),
            "by_status": _count_by(rules, "status"),
            "engine_enabled": len([row for row in rules if row.get("engine_enabled") is True]),
        },
        "guardrails": GUARDRAILS,
    }


def list_bazi_rules(*, domain: str = "", risk_level: str = "", q: str = "") -> Dict[str, Any]:
    state, storage = _load_state()
    rows = [dict(row) for row in state.get("rules") or []]
    if domain:
        rows = [row for row in rows if row.get("domain") == domain]
    if risk_level:
        rows = [row for row in rows if row.get("risk_level") == risk_level]
    if q:
        needle = q.lower().strip()
        rows = [row for row in rows if _rule_search_text(row).lower().find(needle) >= 0]
    rows.sort(key=lambda row: (str(row.get("domain") or ""), str(row.get("rule_id") or "")))
    return {
        "ok": True,
        "count": len(rows),
        "items": rows[:500],
        "storage": storage,
        "runtime_scope": "rule_database_available_for_engine_adapter",
        "guardrails": GUARDRAILS,
    }


def build_structural_rule_signals(
    chart: Dict[str, Any],
    time_context: Dict[str, Any] | None = None,
    inference_context: Dict[str, Any] | None = None,
    *,
    rules: List[Dict[str, Any]] | None = None,
) -> Dict[str, Any]:
    state, storage = _load_state()
    active_rules = [dict(row) for row in (rules if rules is not None else state.get("rules") or [])]
    facts = _adapter_facts(chart, time_context or {}, inference_context or {})
    signals: List[Dict[str, Any]] = []
    for rule in active_rules:
        if rule.get("engine_enabled") is not True:
            continue
        if str(rule.get("status") or "") not in {"active_in_rule_db", "active_record", "approved"}:
            continue
        match = _adapter_match_rule(rule, facts)
        if not match.get("matched"):
            continue
        signals.append(_adapter_signal(rule, match, facts))
    signals.sort(key=lambda row: (int(row.get("score") or 0), str(row.get("signal_id") or "")), reverse=True)
    return {
        "ok": True,
        "version": STRUCTURAL_SIGNAL_VERSION,
        "count": len(signals),
        "signals": signals[:64],
        "facts_summary": _facts_summary(facts),
        "storage": storage,
        "runtime_scope": "structural_rule_signals_only_no_result_mutation",
        "guardrails": ["NO_RESULT_MUTATION", "NO_FORTUNE", "RULE_DB_ATTRIBUTION_REQUIRED", "ANSWER_AND_QUESTION_GUIDANCE_ONLY"],
    }


def knowledge_rule_signal_coverage(
    chart: Dict[str, Any] | None = None,
    time_context: Dict[str, Any] | None = None,
    inference_context: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    source = _load_source_archive()
    drafts = [dict(row) for row in source.get("knowledge_drafts") or [] if isinstance(row, dict)]
    state, storage = _load_state()
    rules = [dict(row) for row in state.get("rules") or [] if isinstance(row, dict)]
    signal_report = build_structural_rule_signals(chart or {}, time_context or {}, inference_context or {}, rules=rules) if chart else {"signals": []}
    signals = [dict(row) for row in signal_report.get("signals") or [] if isinstance(row, dict)]
    signals_by_knowledge: Dict[str, List[Dict[str, Any]]] = {}
    for signal in signals:
        knowledge_id = str(signal.get("knowledge_id") or "")
        if knowledge_id:
            signals_by_knowledge.setdefault(knowledge_id, []).append(signal)
    rules_by_knowledge: Dict[str, List[Dict[str, Any]]] = {}
    for rule in rules:
        knowledge_id = str(rule.get("knowledge_id") or "")
        if knowledge_id:
            rules_by_knowledge.setdefault(knowledge_id, []).append(rule)

    rows: List[Dict[str, Any]] = []
    for draft in sorted(drafts, key=lambda row: str(row.get("knowledge_id") or "")):
        knowledge_id = str(draft.get("knowledge_id") or "")
        risk = str(draft.get("risk_level") or "R4")
        review_status = str(draft.get("review_status") or "pending")
        eligible = bool(knowledge_id) and risk != "R4" and review_status not in {"rejected", "deprecated"}
        mapped_rules = rules_by_knowledge.get(knowledge_id, [])
        active_rules = [
            rule
            for rule in mapped_rules
            if rule.get("engine_enabled") is True and str(rule.get("status") or "") in {"active_in_rule_db", "active_record", "approved"}
        ]
        matched_signals = signals_by_knowledge.get(knowledge_id, [])
        gaps: List[str] = []
        if not eligible:
            gaps.append("not_rule_db_eligible")
        if eligible and not mapped_rules:
            gaps.append("missing_rule_db_record")
        if mapped_rules and not active_rules:
            gaps.append("rule_not_engine_ready")
        if chart and active_rules and not matched_signals:
            gaps.append("no_sample_structural_signal")
        status = "archive_only"
        if eligible:
            if not mapped_rules:
                status = "missing_rule"
            elif not active_rules:
                status = "rule_present_not_engine_ready"
            elif matched_signals:
                status = "sample_signal_covered"
            else:
                status = "rule_ready_unmatched_in_sample"
        rows.append(
            {
                "knowledge_id": knowledge_id,
                "draft_id": draft.get("draft_id"),
                "title": draft.get("title"),
                "domain": draft.get("domain"),
                "category": draft.get("category"),
                "risk_level": risk,
                "review_status": review_status,
                "eligible_for_rule_db": eligible,
                "rule_ids": [rule.get("rule_id") for rule in mapped_rules],
                "active_engine_rule_ids": [rule.get("rule_id") for rule in active_rules],
                "signal_ids": [signal.get("signal_id") for signal in matched_signals],
                "answer_scopes": sorted({str(signal.get("answer_scope") or "") for signal in matched_signals if signal.get("answer_scope")}),
                "question_keys": sorted({key for signal in matched_signals for key in signal.get("question_keys") or []}),
                "status": status,
                "gaps": gaps,
            }
        )

    rule_knowledge_ids = {str(rule.get("knowledge_id") or "") for rule in rules if rule.get("knowledge_id")}
    draft_knowledge_ids = {str(draft.get("knowledge_id") or "") for draft in drafts if draft.get("knowledge_id")}
    orphan_rules = [rule for rule in rules if str(rule.get("knowledge_id") or "") not in draft_knowledge_ids]
    eligible_rows = [row for row in rows if row.get("eligible_for_rule_db")]
    engine_ready_rows = [row for row in eligible_rows if row.get("active_engine_rule_ids")]
    sample_signal_rows = [row for row in eligible_rows if row.get("signal_ids")]
    gap_rows = [row for row in rows if row.get("gaps")]
    return {
        "ok": True,
        "version": "v19.p9.knowledge_rule_signal_coverage.v1",
        "storage": {"rule_db": storage, "source_archive": str(SOURCE_ARCHIVE_FILE)},
        "summary": {
            "draft_count": len(drafts),
            "eligible_draft_count": len(eligible_rows),
            "rule_count": len(rules),
            "knowledge_ids_with_rules": len(rule_knowledge_ids),
            "engine_ready_eligible_count": len(engine_ready_rows),
            "sample_signal_covered_count": len(sample_signal_rows),
            "orphan_rule_count": len(orphan_rules),
            "gap_count": len(gap_rows),
            "by_status": _count_by(rows, "status"),
        },
        "items": rows,
        "orphan_rules": [
            {
                "rule_id": rule.get("rule_id"),
                "knowledge_id": rule.get("knowledge_id"),
                "domain": rule.get("domain"),
                "category": rule.get("category"),
                "status": rule.get("status"),
            }
            for rule in orphan_rules[:100]
        ],
        "sample_signal_report": signal_report,
        "runtime_scope": "coverage_review_only_no_runtime_mutation",
        "guardrails": ["REVIEW_ONLY", "NO_RESULT_MUTATION", "NO_AUTO_RULE_ACTIVATION", "NO_LLM_AUTHORITY"],
    }


def ingest_current_knowledge_drafts_to_rule_db(*, force: bool = False, enable_engine: bool = True) -> Dict[str, Any]:
    source = _load_source_archive()
    drafts = [dict(row) for row in source.get("knowledge_drafts") or []]
    state, _ = _load_state()
    if force:
        state["rules"] = []
    existing = {str(row.get("rule_id") or ""): row for row in state.get("rules") or []}
    imported = 0
    updated = 0
    blocked = []
    for draft in drafts:
        risk = _clean(draft.get("risk_level"), "R4")
        review_status = _clean(draft.get("review_status"), "pending")
        knowledge_id = _clean(draft.get("knowledge_id"))
        if not knowledge_id:
            continue
        if risk == "R4":
            blocked.append({"knowledge_id": knowledge_id, "reason": "R4_ARCHIVE_ONLY"})
            continue
        if review_status in {"rejected", "deprecated"}:
            blocked.append({"knowledge_id": knowledge_id, "reason": "DRAFT_REJECTED_OR_DEPRECATED"})
            continue
        rule = _rule_from_draft(draft, enable_engine=enable_engine)
        rule_id = rule["rule_id"]
        if rule_id in existing:
            merged = {**existing[rule_id], **rule, "rule_record_id": existing[rule_id].get("rule_record_id") or rule["rule_record_id"], "updated_at": utc_now()}
            merged.setdefault("history", []).append(_history("updated_from_draft", "system", "Rule DB record updated from knowledge draft ingestion."))
            existing[rule_id] = merged
            updated += 1
        else:
            existing[rule_id] = rule
            imported += 1
    state["rules"] = sorted(existing.values(), key=lambda row: str(row.get("rule_id") or ""))
    state["last_ingestion"] = {
        "created_at": utc_now(),
        "source": str(SOURCE_ARCHIVE_FILE),
        "draft_count": len(drafts),
        "imported_count": imported,
        "updated_count": updated,
        "blocked_count": len(blocked),
        "blocked": blocked,
        "enable_engine": enable_engine,
    }
    saved = _save_state(state)
    return {
        "ok": True,
        "status": "ingested",
        "draft_count": len(drafts),
        "imported_count": imported,
        "updated_count": updated,
        "blocked_count": len(blocked),
        "blocked": blocked,
        "rule_count": len(state["rules"]),
        "storage": saved,
        "guardrails": GUARDRAILS,
    }


def _rule_from_draft(draft: Dict[str, Any], *, enable_engine: bool) -> Dict[str, Any]:
    knowledge_id = _clean(draft.get("knowledge_id"))
    domain = _draft_to_rule_domain(draft)
    rule_id = "v19.rule." + knowledge_id
    now = utc_now()
    return {
        "rule_record_id": "brr_" + uuid.uuid4().hex[:16],
        "rule_id": rule_id,
        "knowledge_id": knowledge_id,
        "source_draft_id": _clean(draft.get("draft_id")),
        "domain": domain,
        "category": _clean(draft.get("category"), "uncategorized"),
        "title": _clean(draft.get("title"), knowledge_id),
        "statement": _clean(draft.get("statement")),
        "risk_level": _clean(draft.get("risk_level"), "R2"),
        "status": "active_in_rule_db",
        "engine_enabled": enable_engine,
        "engine_adapter_status": "available_for_structural_signal_adapter",
        "input_contract": {"required": _draft_input_contract(draft, domain)},
        "condition": {
            "structured_facts": draft.get("structured_facts") or {},
            "conditions": draft.get("conditions") or {},
            "category": draft.get("category"),
            "risk_level": draft.get("risk_level"),
        },
        "output_contract": {
            "signal": _draft_output_signal(draft, domain),
            "value_set": _draft_value_set(domain),
            "is_prediction": False,
            "prediction_scope": "structural_rule_signal",
        },
        "reasoning_path": [
            "load active_in_rule_db record",
            "match structured facts against chart/time context",
            "emit structural rule signal with attribution",
        ],
        "evidence": {
            "source_refs": draft.get("source_refs") or [],
            "source_excerpt_ids": draft.get("source_excerpt_ids") or [],
            "source_draft_id": draft.get("draft_id"),
            "review_status": draft.get("review_status") or "pending",
            "review_note": draft.get("review_note") or "",
        },
        "confidence": _bounded_float(draft.get("confidence_prior"), 0.5, 0.0, 1.0),
        "allowed_usage": draft.get("allowed_usage") or ["rule_db", "engine_adapter_candidate"],
        "forbidden_usage": draft.get("forbidden_usage") or ["direct_fortune_output", "traditional_prediction_text"],
        "created_at": now,
        "updated_at": now,
        "history": [_history("ingested", "system", "Directly ingested from V19 knowledge draft into Bazi Rule DB.")],
        "guardrails": GUARDRAILS,
    }


def _load_state() -> Tuple[Dict[str, Any], Dict[str, Any]]:
    if RULE_DB_FILE.exists():
        try:
            state = json.loads(RULE_DB_FILE.read_text(encoding="utf-8"))
            if isinstance(state, dict):
                state.setdefault("rules", [])
                state.setdefault("guardrails", GUARDRAILS)
                return state, {"backend": "file", "path": str(RULE_DB_FILE)}
        except Exception:
            pass
    return {
        "version": RULE_DB_VERSION,
        "created_at": utc_now(),
        "updated_at": utc_now(),
        "rules": [],
        "guardrails": GUARDRAILS,
    }, {"backend": "file", "path": str(RULE_DB_FILE)}


def _save_state(state: Dict[str, Any]) -> Dict[str, Any]:
    RUNTIME.mkdir(parents=True, exist_ok=True)
    state["version"] = RULE_DB_VERSION
    state["updated_at"] = utc_now()
    state["guardrails"] = GUARDRAILS
    RULE_DB_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return {"backend": "file", "path": str(RULE_DB_FILE)}


def _load_source_archive() -> Dict[str, Any]:
    if not SOURCE_ARCHIVE_FILE.exists():
        return {"knowledge_drafts": []}
    try:
        data = json.loads(SOURCE_ARCHIVE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"knowledge_drafts": []}
    return data if isinstance(data, dict) else {"knowledge_drafts": []}


def _draft_to_rule_domain(draft: Dict[str, Any]) -> str:
    domain = _clean(draft.get("domain"))
    category = _clean(draft.get("category"))
    if domain == "ten_god" or category == "ten_god":
        return "ten_god_relation"
    if domain == "luck_flow" or category == "timing_context":
        return "time_structure"
    if domain == "wealth":
        return "income_stability"
    if domain in {"five_element", "strength"} or category in {"stem_branch_attribute", "strength_model"}:
        return "day_master_element"
    if domain == "core_structure" and category in {"core_symbol", "hidden_stem", "five_element_relation"}:
        return "day_master_element"
    return "structural_relation"


def _draft_input_contract(draft: Dict[str, Any], domain: str) -> List[str]:
    if domain == "ten_god_relation":
        return ["chart.day_master", "chart.pillars"]
    if domain == "time_structure":
        return ["chart", "time_context"]
    if domain == "income_stability":
        return ["chart", "inference_context.income_stability"]
    if domain == "structural_relation":
        return ["chart.pillars", "time_context"]
    return ["chart"]


def _draft_output_signal(draft: Dict[str, Any], domain: str) -> str:
    category = _clean(draft.get("category"), "structure")
    if domain == "income_stability":
        return "income_stability_rule_feature"
    if domain == "time_structure":
        return "time_context_structure"
    if domain == "ten_god_relation":
        return "ten_god_signal"
    return category + "_signal"


def _draft_value_set(domain: str) -> List[str]:
    if domain == "time_structure":
        return ["present", "absent", "unknown"]
    return ["none", "low", "medium", "high", "unknown"]


def _count_by(rows: List[Dict[str, Any]], key: str) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for row in rows:
        value = str(row.get(key) or "unknown")
        counts[value] = counts.get(value, 0) + 1
    return counts


def _rule_search_text(row: Dict[str, Any]) -> str:
    parts = [row.get("rule_id"), row.get("knowledge_id"), row.get("domain"), row.get("category"), row.get("title"), row.get("statement")]
    return " ".join(str(part or "") for part in parts)


def _adapter_facts(chart: Dict[str, Any], time_context: Dict[str, Any], inference_context: Dict[str, Any]) -> Dict[str, Any]:
    pillars = dict(chart.get("pillars") or {})
    branches = [str((pillars.get(name) or {}).get("branch") or "") for name in ["year", "month", "day", "hour"]]
    stems = [str((pillars.get(name) or {}).get("stem") or "") for name in ["year", "month", "day", "hour"]]
    hidden = {branch: list(BRANCH_HIDDEN_STEMS.get(branch, [])) for branch in branches if branch}
    relation_items = list((chart.get("relations") or {}).get("items") or [])
    relation_pairs, relation_types = _adapter_relation_facts(relation_items)
    time_pairs, time_types, time_layers = _adapter_time_relation_facts(time_context)
    income_bundle = dict(inference_context.get("income_stability") or {})
    income_signals = {
        str(row.get("key") or ""): str(row.get("value") or "")
        for row in income_bundle.get("signals") or []
        if isinstance(row, dict) and str(row.get("key") or "")
    }
    return {
        "pillars": pillars,
        "branches": [item for item in branches if item],
        "branch_set": set(item for item in branches if item),
        "stems": [item for item in stems if item],
        "stem_set": set(item for item in stems if item),
        "day_stem": str((pillars.get("day") or {}).get("stem") or ""),
        "day_branch": str((pillars.get("day") or {}).get("branch") or ""),
        "month_branch": str((pillars.get("month") or {}).get("branch") or ""),
        "hidden_stems_by_branch": hidden,
        "all_stems": set(item for item in stems if item) | {stem for rows in hidden.values() for stem in rows},
        "all_elements": {element_of_stem(stem) for stem in stems if stem} | {element_of_stem(stem) for rows in hidden.values() for stem in rows},
        "vault_branches": sorted({branch for branch in branches if branch in VAULT_BRANCHES}),
        "relation_pairs": sorted(set(relation_pairs) | set(time_pairs)),
        "relation_types": sorted(set(relation_types) | set(time_types)),
        "has_time_context": bool(time_context),
        "time_layers": sorted(set(time_layers)),
        "luck_branch": str(((time_context.get("luck_cycle") or {}).get("pillar") or {}).get("branch") or ""),
        "flow_branch": str(((time_context.get("flow_year") or {}).get("pillar") or {}).get("branch") or ""),
        "income_signals": income_signals,
    }


def _adapter_relation_facts(items: List[Any]) -> Tuple[List[str], List[str]]:
    pairs: List[str] = []
    types: List[str] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        relation_type = _normalize_relation_type(str(item.get("type") or item.get("relation_type") or ""))
        if relation_type:
            types.append(relation_type)
        branches = item.get("branches")
        if isinstance(branches, str):
            raw = branches.replace("/", "").replace("-", "").replace(" ", "")
            if len(raw) >= 2:
                pairs.append(_pair_key(raw[0], raw[1]))
        elif isinstance(branches, list) and len(branches) >= 2:
            pairs.append(_pair_key(str(branches[0]), str(branches[1])))
    return sorted(set(pairs)), sorted(set(types))


def _adapter_time_relation_facts(time_context: Dict[str, Any]) -> Tuple[List[str], List[str], List[str]]:
    pairs: List[str] = []
    types: List[str] = []
    layers: List[str] = []
    for layer_key in ["luck_cycle", "flow_year"]:
        layer = dict(time_context.get(layer_key) or {})
        rel = dict(layer.get("relations_with_natal") or {})
        for relation_type, rows in rel.items():
            normalized = _normalize_relation_type(str(relation_type))
            for row in rows or []:
                pair = _relation_pair_from_any(row)
                if pair:
                    pairs.append(pair)
                    types.append(normalized)
                    layers.append(layer_key)
    return sorted(set(pairs)), sorted(set(types)), sorted(set(layers))


def _adapter_match_rule(rule: Dict[str, Any], facts: Dict[str, Any]) -> Dict[str, Any]:
    domain = str(rule.get("domain") or "")
    category = str(rule.get("category") or "")
    structured = _extract_structured_facts_from_rule(rule)
    observed: List[str] = []
    fact_refs: List[str] = []
    layer = "chart_structure"

    if category in {"structure_anchor", "core_symbol", "stem_branch_attribute"} and (facts.get("day_stem") or facts.get("month_branch")):
        observed = [str(item) for item in [facts.get("day_stem"), facts.get("month_branch")] if str(item)]
        fact_refs = ["chart.day_stem", "chart.month_branch"]
    elif category == "hidden_stem" and facts.get("hidden_stems_by_branch"):
        observed = [f"{branch}藏{'/'.join(stems)}" for branch, stems in list(facts.get("hidden_stems_by_branch", {}).items())[:6]]
        fact_refs = ["chart.hidden_stems"]
    elif category in {"branch_relation", "stem_relation", "five_element_relation"} and (facts.get("relation_pairs") or facts.get("relation_types")):
        observed = list(facts.get("relation_pairs") or facts.get("relation_types") or [])[:8]
        fact_refs = ["chart.relations", "time_context.relations"]
        layer = "chart_or_time_relation"
    elif category == "vault" and facts.get("vault_branches"):
        observed = list(facts.get("vault_branches") or [])
        fact_refs = ["chart.vault_branches", "chart.hidden_stems"]
    elif category in {"time_boundary", "timing_context"} or domain == "time_structure":
        if facts.get("has_time_context"):
            observed = list(facts.get("time_layers") or ["time_context"])
            fact_refs = ["time_context"]
            layer = "time_context"
    elif category in {"ten_god", "wealth_boundary"} or domain == "ten_god_relation":
        if facts.get("day_stem") and facts.get("all_stems"):
            observed = [str(facts.get("day_stem")), "relation_metadata"]
            fact_refs = ["chart.day_stem", "chart.visible_hidden_stems"]
    elif domain == "income_stability" or category in {"wealth_feature", "wealth_mechanism"}:
        if facts.get("income_signals"):
            observed = [f"{key}={value}" for key, value in list(facts.get("income_signals", {}).items())[:8]]
            fact_refs = ["inference_context.income_stability.signals"]
            layer = "supported_result_context"
    elif category == "strength_model" and (facts.get("day_stem") or facts.get("month_branch")):
        observed = [str(item) for item in [facts.get("day_stem"), facts.get("month_branch"), "capacity_evidence_candidate"] if str(item)]
        fact_refs = ["chart.day_stem", "chart.month_branch", "chart.hidden_stems"]
    elif category == "pattern_structure" and facts.get("branches"):
        observed = list(facts.get("branches") or [])[:4]
        fact_refs = ["chart.pillars"]

    if not observed and structured:
        structured_match = _match_adapter_structured_facts(structured, facts)
        if structured_match.get("matched"):
            observed = list(structured_match.get("observed") or [])
            fact_refs = list(structured_match.get("fact_refs") or [])

    if observed:
        return {"matched": True, "reason": _adapter_reason(rule), "observed": observed, "fact_refs": fact_refs, "layer": layer}
    return {"matched": False, "reason": "no_matching_structural_fact", "observed": [], "fact_refs": [], "layer": layer}


def _adapter_signal(rule: Dict[str, Any], match: Dict[str, Any], facts: Dict[str, Any]) -> Dict[str, Any]:
    category = str(rule.get("category") or "")
    domain = str(rule.get("domain") or "")
    return {
        "signal_id": "srs." + str(rule.get("knowledge_id") or rule.get("rule_id") or "unknown"),
        "source": "bazi_rule_db_engine_adapter",
        "version": STRUCTURAL_SIGNAL_VERSION,
        "rule_id": rule.get("rule_id"),
        "knowledge_id": rule.get("knowledge_id"),
        "domain": domain,
        "category": category,
        "risk_level": rule.get("risk_level"),
        "title": rule.get("title"),
        "layer": match.get("layer") or "chart_structure",
        "observed": match.get("observed") or [],
        "reason": match.get("reason") or "",
        "fact_refs": match.get("fact_refs") or [],
        "answer_scope": _adapter_answer_scope(domain, category),
        "question_keys": _adapter_question_keys(domain, category),
        "score": _adapter_score(domain, category),
        "mutates_result": False,
        "runtime_scope": "structural_rule_signal_only_no_result_mutation",
        "guardrails": ["RULE_DB_SIGNAL_ONLY", "NO_RESULT_MUTATION", "NO_FORTUNE", "NO_AUTO_RULE_ACTIVATION"],
    }


def _extract_structured_facts_from_rule(rule: Dict[str, Any]) -> Dict[str, Any]:
    condition = rule.get("condition")
    if isinstance(condition, dict) and isinstance(condition.get("structured_facts"), dict):
        return dict(condition.get("structured_facts") or {})
    if isinstance(rule.get("structured_facts"), dict):
        return dict(rule.get("structured_facts") or {})
    return {}


def _match_adapter_structured_facts(structured: Dict[str, Any], facts: Dict[str, Any]) -> Dict[str, Any]:
    observed: List[str] = []
    fact_refs: List[str] = []
    branches = set(facts.get("branch_set") or set())
    stems = set(facts.get("stem_set") or set())
    all_stems = set(facts.get("all_stems") or set())
    all_elements = set(facts.get("all_elements") or set())
    for branch in _string_list(structured.get("vault_branches")) + _string_list(structured.get("branches")):
        if branch in branches:
            observed.append(branch)
            fact_refs.append("chart.branches")
    for stem in _string_list(structured.get("stems")):
        if stem in stems or stem in all_stems:
            observed.append(stem)
            fact_refs.append("chart.stems")
    if isinstance(structured.get("hidden_stems"), dict):
        for branch in structured.get("hidden_stems", {}).keys():
            if str(branch) in branches:
                observed.append(str(branch))
                fact_refs.append("chart.hidden_stems")
    for pair in _string_list(structured.get("generation_cycle")):
        parsed = _parse_pair(pair)
        if parsed and parsed[0] in all_elements and parsed[1] in all_elements:
            observed.append(f"gen:{parsed[0]}->{parsed[1]}")
            fact_refs.append("chart.elements")
    for pair in _string_list(structured.get("control_cycle")):
        parsed = _parse_pair(pair)
        if parsed and parsed[0] in all_elements and parsed[1] in all_elements:
            observed.append(f"ctrl:{parsed[0]}x{parsed[1]}")
            fact_refs.append("chart.elements")
    if structured.get("anchor") in {"day_master", "day_stem"} and facts.get("day_stem"):
        observed.append(str(facts.get("day_stem")))
        fact_refs.append("chart.day_stem")
    if structured.get("anchor") == "month_branch" and facts.get("month_branch"):
        observed.append(str(facts.get("month_branch")))
        fact_refs.append("chart.month_branch")
    return {"matched": bool(observed), "observed": _dedupe(observed), "fact_refs": _dedupe(fact_refs)}


def _adapter_reason(rule: Dict[str, Any]) -> str:
    category = str(rule.get("category") or "")
    labels = {
        "structure_anchor": "Rule DB matched chart anchors used for structural reading.",
        "hidden_stem": "Rule DB matched hidden-stem facts used as structure sources.",
        "branch_relation": "Rule DB matched branch-relation facts by layer.",
        "vault": "Rule DB matched vault branch facts and hidden-stem boundary.",
        "ten_god": "Rule DB matched ten-god relationship metadata boundary.",
        "wealth_boundary": "Rule DB matched wealth-star boundary as structure metadata.",
        "wealth_feature": "Rule DB matched income-structure feature context.",
        "wealth_mechanism": "Rule DB matched income-structure mechanism context.",
        "timing_context": "Rule DB matched time-context boundary.",
        "time_boundary": "Rule DB matched time-context boundary.",
        "strength_model": "Rule DB matched capacity-evidence structure context.",
    }
    return labels.get(category, "Rule DB matched structural facts.")


def _adapter_answer_scope(domain: str, category: str) -> str:
    if category == "vault":
        return "explain_vault_location_hidden_stems_and_boundary"
    if category == "branch_relation":
        return "explain_branch_relations_by_layer"
    if category in {"time_boundary", "timing_context"} or domain == "time_structure":
        return "explain_time_context_without_result_mutation"
    if domain == "income_stability" or category.startswith("wealth"):
        return "explain_income_structure_signals_without_prediction"
    if category in {"ten_god", "wealth_boundary"}:
        return "explain_relationship_metadata_without_verdict"
    return "explain_structural_fact_without_prediction"


def _adapter_question_keys(domain: str, category: str) -> List[str]:
    if category == "vault":
        return ["q_vault_structure", "q_hidden_stem_role", "q_time_context_boundary"]
    if category == "branch_relation":
        return ["q_branch_relation_detail", "q_time_vs_natal_relation", "q_combination_context"]
    if category in {"time_boundary", "timing_context"} or domain == "time_structure":
        return ["q_time_context_boundary", "q_time_not_inference", "q_luck_flow_layers"]
    if domain == "income_stability" or category in {"wealth_feature", "wealth_mechanism"}:
        return ["q_income_factors", "q_income_path_structure", "q_signal_combination"]
    if category in {"ten_god", "wealth_boundary"}:
        return ["q_ten_god_metadata", "q_hidden_stem_role", "q_read_result_not_fortune"]
    if category == "hidden_stem":
        return ["q_hidden_stem_role", "q_ten_god_metadata", "q_element_flow_metadata"]
    if category == "structure_anchor":
        return ["q_day_master_month_anchor", "q_month_command_anchor", "q_structure_overview"]
    return ["q_structure_overview", "q_read_result_not_fortune", "follow_rule_basis"]


def _adapter_score(domain: str, category: str) -> int:
    if category in {"branch_relation", "vault", "structure_anchor"}:
        return 86
    if category in {"time_boundary", "timing_context"} or domain == "time_structure":
        return 82
    if domain == "income_stability" or category.startswith("wealth"):
        return 76
    if category in {"hidden_stem", "ten_god"}:
        return 72
    return 60


def _facts_summary(facts: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "day_stem": facts.get("day_stem") or "",
        "month_branch": facts.get("month_branch") or "",
        "branch_count": len(facts.get("branches") or []),
        "hidden_stem_branches": len(facts.get("hidden_stems_by_branch") or {}),
        "vault_branches": list(facts.get("vault_branches") or []),
        "relation_types": list(facts.get("relation_types") or []),
        "time_layers": list(facts.get("time_layers") or []),
        "income_signal_count": len(facts.get("income_signals") or {}),
    }


def _normalize_relation_type(value: str) -> str:
    text = str(value or "").lower()
    if "clash" in text or "冲" in text or text in {"chong", "liu_chong", "six_clash", "clashes"}:
        return "clash"
    if "comb" in text or "合" in text or text in {"he", "liu_he", "six_combination", "combinations"}:
        return "combination"
    if "harm" in text or "害" in text or text in {"hai", "six_harm", "harms"}:
        return "harm"
    if "break" in text or "破" in text or "刑" in text or text in {"po", "breaks"}:
        return "break"
    return text or "relation"


def _relation_pair_from_any(value: Any) -> str:
    if isinstance(value, dict):
        branches = value.get("branches") or value.get("pair")
        if isinstance(branches, str):
            raw = branches.replace("/", "").replace("-", "").replace(" ", "")
            return _pair_key(raw[0], raw[1]) if len(raw) >= 2 else ""
        if isinstance(branches, list) and len(branches) >= 2:
            return _pair_key(str(branches[0]), str(branches[1]))
        left = value.get("left") or value.get("source") or value.get("time_branch")
        right = value.get("right") or value.get("target") or value.get("natal_branch")
        if left and right:
            return _pair_key(str(left), str(right))
    if isinstance(value, str):
        raw = value.replace("/", "").replace("-", "").replace(" ", "")
        return _pair_key(raw[0], raw[1]) if len(raw) >= 2 else ""
    return ""


def _pair_key(a: str, b: str) -> str:
    left, right = sorted([str(a), str(b)])
    return left + right


def _parse_pair(value: Any) -> Tuple[str, str] | None:
    if isinstance(value, (list, tuple)) and len(value) >= 2:
        return str(value[0]), str(value[1])
    raw = str(value or "").strip()
    for sep in ["->", "=>", "×", "x", "/", "-", ",", "，"]:
        if sep in raw:
            parts = [part.strip() for part in raw.split(sep) if part.strip()]
            if len(parts) >= 2:
                return parts[0], parts[1]
    text = raw.replace(" ", "")
    if len(text) >= 2:
        return text[0], text[1]
    return None


def _string_list(value: Any) -> List[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, tuple):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        return [item.strip() for item in value.replace("，", ",").split(",") if item.strip()]
    return []


def _dedupe(rows: List[str]) -> List[str]:
    seen = set()
    out = []
    for row in rows:
        if row in seen:
            continue
        seen.add(row)
        out.append(row)
    return out


def _history(status: str, actor_role: str, note: str) -> Dict[str, Any]:
    return {"created_at": utc_now(), "status": status, "actor_role": actor_role, "note": note}


def _clean(value: Any, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def _bounded_float(value: Any, default: float, minimum: float, maximum: float) -> float:
    try:
        raw = float(value)
    except (TypeError, ValueError):
        raw = default
    if raw != raw:
        raw = default
    return max(minimum, min(maximum, raw))
