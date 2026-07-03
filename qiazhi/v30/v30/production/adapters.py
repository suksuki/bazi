from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any

from v30.contracts import FeatureEvidence, RankedDecision
from v30.production.contracts import (
    AssertionLevelHint,
    BaziDomain,
    BaziSignal,
    BaziTopic,
    SignalPolarity,
    SignalSourceType,
    SourceModule,
)


def signals_from_feature_evidence(rows: Sequence[FeatureEvidence | Mapping[str, Any]]) -> list[BaziSignal]:
    signals: list[BaziSignal] = []
    for row in rows:
        payload = _dict(row)
        evidence_id = _string(payload.get("evidence_id"))
        claim = _string(payload.get("label")) or evidence_id
        confidence = _bounded_float(payload.get("confidence"), 0.0)
        evidence_refs = [evidence_id] if evidence_id else []
        weakens = _string_list(payload.get("weakens"))
        signals.append(
            BaziSignal(
                signal_id=_signal_id(SignalSourceType.FEATURE_EVIDENCE, evidence_id or claim),
                source_module=SourceModule.FEATURE_COMPILER,
                source_type=SignalSourceType.FEATURE_EVIDENCE,
                source_ref=evidence_id,
                topic=_topic_from_domain(_string(payload.get("domain")), fallback=BaziTopic.FEATURE),
                domain=_domain(_string(payload.get("domain"))),
                role_visibility=["user", "practitioner", "admin", "analyst", "lab"],
                claim=claim,
                claim_key=_claim_key(_string(payload.get("domain")), claim),
                polarity=SignalPolarity.MIXED if weakens else SignalPolarity.SUPPORT,
                strength=confidence,
                confidence=confidence,
                assertion_level_hint=_assertion_from_confidence(confidence, confirmed=payload.get("kind") == "fact"),
                evidence_refs=evidence_refs,
                counter_evidence_refs=weakens,
                branch_group_id=_string(payload.get("domain")),
                training_targets=["evidence_binding", "source_weight"],
                boundary=_string(payload.get("boundary")) or "feature_evidence_signal_not_final_verdict",
                raw_ref=evidence_id,
            )
        )
    return signals


def signals_from_macro_dimensions(rows: Sequence[Mapping[str, Any]]) -> list[BaziSignal]:
    signals: list[BaziSignal] = []
    for row in rows:
        payload = _dict(row)
        signal_id = _string(payload.get("signal_id"))
        claim = _string(payload.get("label_zh")) or _string(payload.get("dimension_id")) or signal_id
        score = _bounded_float(payload.get("score"), 0.0)
        domain = _string(payload.get("domain"))
        signals.append(
            BaziSignal(
                signal_id=_signal_id(SignalSourceType.MACRO_DIMENSION, signal_id or claim),
                source_module=SourceModule.KNOWLEDGE_MACRO,
                source_type=SignalSourceType.MACRO_DIMENSION,
                source_ref=signal_id,
                topic=_topic_from_domain(domain, fallback=BaziTopic.MACRO),
                domain=_domain(domain),
                role_visibility=["user", "practitioner", "admin", "analyst", "lab"],
                claim=claim,
                claim_key=_claim_key(domain, claim),
                polarity=SignalPolarity.SUPPORT,
                strength=score,
                confidence=score,
                assertion_level_hint=_assertion_from_confidence(score),
                evidence_refs=_string_list(payload.get("evidence_ids")),
                branch_group_id=_string(payload.get("dimension_id")),
                training_targets=_string_list(payload.get("training_tags")) or ["macro_dimension_weight"],
                boundary=_string(payload.get("boundary")) or "macro_dimension_signal_is_context_projection_not_verdict",
                raw_ref=signal_id,
            )
        )
    return signals


def signals_from_ranked_decisions(payload: Mapping[str, Any] | None) -> list[BaziSignal]:
    rows = _dict(payload)
    signals: list[BaziSignal] = []
    for key, value in sorted(rows.items()):
        row = _dict(value)
        decision_id = _string(row.get("decision_id")) or key
        primary = _string(row.get("primary_candidate"))
        claim = f"{key}: {primary}" if primary else decision_id
        confidence = _bounded_float(row.get("confidence"), 0.0)
        unresolved = _string_list(row.get("unresolved_requirements"))
        signals.append(
            BaziSignal(
                signal_id=_signal_id(SignalSourceType.RANKED_DECISION, decision_id),
                source_module=SourceModule.RANKED_DECISION,
                source_type=SignalSourceType.RANKED_DECISION,
                source_ref=decision_id,
                topic=_topic_from_domain(_string(row.get("domain") or key), fallback=BaziTopic.STRUCTURE),
                domain=_domain(_ranked_decision_domain(key, row)),
                role_visibility=["user", "practitioner", "admin", "analyst", "lab"],
                claim=claim,
                claim_key=_claim_key(_ranked_decision_domain(key, row), primary or decision_id),
                polarity=SignalPolarity.MIXED if unresolved else SignalPolarity.SUPPORT,
                strength=confidence,
                confidence=confidence,
                assertion_level_hint=_assertion_from_confidence(confidence),
                evidence_refs=_string_list(row.get("supporting_evidence")),
                counter_evidence_refs=_string_list(row.get("weakening_evidence")),
                branch_group_id=decision_id,
                conflict_group_id=decision_id if unresolved else "",
                training_targets=["ranked_decision_weight", "assertion_threshold"],
                boundary=_string(row.get("boundary")) or "ranked_decision_signal_is_candidate_not_verdict",
                raw_ref=decision_id,
            )
        )
    return signals


def signals_from_diagnosis(diagnosis: Mapping[str, Any] | None) -> list[BaziSignal]:
    payload = _dict(diagnosis)
    signals: list[BaziSignal] = []
    signals.extend(signals_from_matched_rules(_list(payload.get("matched_rules"))))
    signals.extend(signals_from_diagnosis_features(_list(payload.get("features"))))
    signals.extend(signals_from_diagnosis_paths(_list(payload.get("paths"))))
    signals.extend(signals_from_diagnosis_portraits(_list(payload.get("portraits"))))
    signals.extend(signals_from_diagnosis_claims(_list(payload.get("claims"))))
    return signals


def signals_from_matched_rules(rows: Sequence[Mapping[str, Any]]) -> list[BaziSignal]:
    signals: list[BaziSignal] = []
    for row in rows:
        payload = _dict(row)
        source_ref = _string(payload.get("rule_match_id")) or _string(payload.get("rule_id"))
        templates = _string_list(payload.get("claim_templates"))
        claim = templates[0] if templates else _string(payload.get("rule_id")) or source_ref
        strength = _bounded_float(payload.get("match_strength"), 0.0)
        can_generate = bool(payload.get("can_generate_claim"))
        domain = _first(_string_list(payload.get("domain_targets")), "overview")
        signals.append(
            BaziSignal(
                signal_id=_signal_id(SignalSourceType.MATCHED_RULE, source_ref or claim),
                source_module=SourceModule.RULE_MATCHER,
                source_type=SignalSourceType.MATCHED_RULE,
                source_ref=source_ref,
                topic=BaziTopic.RULE,
                domain=_domain(domain),
                role_visibility=["practitioner", "admin", "analyst", "lab"],
                claim=claim,
                claim_key=_claim_key(domain, claim),
                polarity=SignalPolarity.SUPPORT if can_generate else SignalPolarity.OPPOSE,
                strength=strength,
                confidence=strength,
                assertion_level_hint=_assertion_from_confidence(strength) if can_generate else AssertionLevelHint.BLOCKED,
                evidence_refs=_string_list(payload.get("evidence_ids")),
                counter_evidence_refs=_string_list(payload.get("counter_context_hit")) + _string_list(payload.get("blocked_claims")),
                branch_group_id=_string(payload.get("rule_id")),
                conflict_group_id=_first(_string_list(payload.get("blocked_claims")), ""),
                training_targets=["rule_weight", "rule_boundary_quality"],
                boundary="matched_rule_signal_is_rule_material_not_public_verdict",
                raw_ref=source_ref,
            )
        )
    return signals


def signals_from_diagnosis_features(rows: Sequence[Mapping[str, Any]]) -> list[BaziSignal]:
    signals: list[BaziSignal] = []
    for row in rows:
        payload = _dict(row)
        source_ref = _string(payload.get("feature_id"))
        domain = _string(payload.get("domain"))
        claim = _string(payload.get("statement")) or source_ref
        confidence = _confidence_band_value(_string(payload.get("confidence_band")))
        signals.append(
            BaziSignal(
                signal_id=_signal_id(SignalSourceType.DIAGNOSIS_FEATURE, source_ref or claim),
                source_module=SourceModule.DIAGNOSIS_FEATURE_ENGINE,
                source_type=SignalSourceType.DIAGNOSIS_FEATURE,
                source_ref=source_ref,
                topic=_topic_from_domain(domain, fallback=BaziTopic.FEATURE),
                domain=_domain(domain),
                role_visibility=["user", "practitioner", "admin", "analyst", "lab"],
                claim=claim,
                claim_key=_claim_key(domain, claim),
                polarity=SignalPolarity.MIXED if payload.get("counter_notes") else SignalPolarity.SUPPORT,
                strength=confidence,
                confidence=confidence,
                assertion_level_hint=_assertion_from_confidence(confidence),
                evidence_refs=_string_list(payload.get("evidence_ids")),
                counter_evidence_refs=_string_list(payload.get("counter_notes")),
                branch_group_id=_string(payload.get("family")),
                training_targets=["feature_projection_quality", "evidence_binding"],
                boundary="diagnosis_feature_signal_is_traceable_projection_not_new_chart_fact",
                raw_ref=source_ref,
            )
        )
    return signals


def signals_from_diagnosis_paths(rows: Sequence[Mapping[str, Any]]) -> list[BaziSignal]:
    signals: list[BaziSignal] = []
    for row in rows:
        payload = _dict(row)
        source_ref = _string(payload.get("path_id"))
        domains = _string_list(payload.get("domain_targets"))
        domain = _first(domains, "structure")
        claim = _string(payload.get("diagnosis_statement")) or _string(payload.get("mechanism")) or source_ref
        score = _bounded_float(payload.get("score"), 0.0)
        counter = _string_list(payload.get("counter_evidence_ids")) + _string_list(payload.get("blocked_overclaim"))
        signals.append(
            BaziSignal(
                signal_id=_signal_id(SignalSourceType.DIAGNOSIS_PATH, source_ref or claim),
                source_module=SourceModule.DIAGNOSIS_PATH_ENGINE,
                source_type=SignalSourceType.DIAGNOSIS_PATH,
                source_ref=source_ref,
                topic=BaziTopic.PATH,
                domain=_domain(domain),
                role_visibility=["user", "practitioner", "admin", "analyst", "lab"],
                claim=claim,
                claim_key=_claim_key(domain, _string(payload.get("mechanism")) or claim),
                polarity=SignalPolarity.MIXED if counter else SignalPolarity.SUPPORT,
                strength=score,
                confidence=score,
                assertion_level_hint=_assertion_from_confidence(score),
                evidence_refs=_string_list(payload.get("evidence_ids")),
                counter_evidence_refs=counter,
                branch_group_id=_string(payload.get("mechanism")),
                conflict_group_id=_string(payload.get("mechanism")) if counter else "",
                training_targets=["path_weight", "path_coherence"],
                boundary="diagnosis_path_signal_is_mechanism_material_not_event_prediction",
                raw_ref=source_ref,
            )
        )
    return signals


def signals_from_diagnosis_portraits(rows: Sequence[Mapping[str, Any]]) -> list[BaziSignal]:
    signals: list[BaziSignal] = []
    for row in rows:
        payload = _dict(row)
        source_ref = _string(payload.get("portrait_id"))
        domain = _string(payload.get("domain"))
        claim = _string(payload.get("statement")) or _string(payload.get("dimension")) or source_ref
        confidence = _confidence_band_value(_string(payload.get("confidence_band")))
        signals.append(
            BaziSignal(
                signal_id=_signal_id(SignalSourceType.DIAGNOSIS_PORTRAIT, source_ref or claim),
                source_module=SourceModule.DIAGNOSIS_PORTRAIT_ENGINE,
                source_type=SignalSourceType.DIAGNOSIS_PORTRAIT,
                source_ref=source_ref,
                topic=BaziTopic.PORTRAIT,
                domain=_domain(domain),
                role_visibility=["user", "practitioner", "admin", "analyst", "lab"],
                claim=claim,
                claim_key=_claim_key(domain, _string(payload.get("dimension")) or claim),
                polarity=SignalPolarity.MIXED if payload.get("counter_notes") else SignalPolarity.SUPPORT,
                strength=confidence,
                confidence=confidence,
                assertion_level_hint=_assertion_from_confidence(confidence),
                evidence_refs=_string_list(payload.get("evidence_ids")),
                counter_evidence_refs=_string_list(payload.get("counter_notes")),
                branch_group_id=_string(payload.get("dimension")),
                training_targets=["portrait_projection_quality", "portrait_weight"],
                boundary="diagnosis_portrait_signal_is_derived_projection_not_personality_fact",
                raw_ref=source_ref,
            )
        )
    return signals


def signals_from_diagnosis_claims(rows: Sequence[Mapping[str, Any]]) -> list[BaziSignal]:
    signals: list[BaziSignal] = []
    for row in rows:
        payload = _dict(row)
        source_ref = _string(payload.get("claim_id"))
        domain = _string(payload.get("domain"))
        claim = _string(payload.get("claim_text")) or source_ref
        confidence = _confidence_band_value(_string(payload.get("confidence_band")))
        blocked = _string_list(payload.get("blocked_overclaim"))
        needs_calibration = bool(payload.get("needs_user_calibration"))
        signals.append(
            BaziSignal(
                signal_id=_signal_id(SignalSourceType.DIAGNOSIS_CLAIM, source_ref or claim),
                source_module=SourceModule.DIAGNOSIS_CLAIM_GENERATOR,
                source_type=SignalSourceType.DIAGNOSIS_CLAIM,
                source_ref=source_ref,
                topic=_topic_from_domain(domain, fallback=BaziTopic.UNKNOWN),
                domain=_domain(domain),
                role_visibility=["user", "practitioner", "admin", "analyst", "lab"],
                claim=claim,
                claim_key=_claim_key(domain, claim),
                polarity=SignalPolarity.MIXED if blocked or needs_calibration else SignalPolarity.SUPPORT,
                strength=confidence,
                confidence=confidence,
                assertion_level_hint=AssertionLevelHint.WEAK_CANDIDATE if needs_calibration else _assertion_from_confidence(confidence),
                evidence_refs=_string_list(payload.get("evidence_ids")),
                counter_evidence_refs=blocked,
                branch_group_id=_first(_string_list(payload.get("path_ids")), _string(payload.get("claim_level"))),
                conflict_group_id=_first(blocked, ""),
                training_targets=["claim_score", "assertion_threshold", "final_synthesis_quality"],
                boundary="diagnosis_claim_signal_is_candidate_material_before_decision_verdict",
                raw_ref=source_ref,
            )
        )
    return signals


def signals_from_stage_points(rows: Sequence[Mapping[str, Any]]) -> list[BaziSignal]:
    signals: list[BaziSignal] = []
    for row in rows:
        payload = _dict(row)
        source_ref = _string(payload.get("point_id")) or _string(payload.get("stage_id"))
        claim = _string(payload.get("text")) or _string(payload.get("short_label")) or source_ref
        if not claim:
            continue
        confidence = _bounded_float(payload.get("score"), _bounded_float(payload.get("confidence"), 0.55))
        kind = _string(payload.get("kind"))
        signals.append(
            BaziSignal(
                signal_id=_signal_id(SignalSourceType.STAGE_POINT, source_ref or claim),
                source_module=SourceModule.STAGE_POINT,
                source_type=SignalSourceType.STAGE_POINT,
                source_ref=source_ref,
                topic=_topic_from_stage_kind(kind),
                domain=_domain(_first(_string_list(payload.get("macro_domains")), _string(payload.get("domain")))),
                role_visibility=["user", "practitioner", "admin", "analyst", "lab"],
                claim=claim,
                claim_key=_claim_key(_string(payload.get("stage_id")), claim),
                polarity=SignalPolarity.MIXED if kind == "branch" else SignalPolarity.SUPPORT,
                strength=confidence,
                confidence=confidence,
                assertion_level_hint=_assertion_from_confidence(confidence),
                evidence_refs=_string_list(payload.get("evidence_refs")),
                branch_group_id=_string(payload.get("stage_id")),
                training_targets=["stage_point_quality", "sidebar_memory_priority"],
                boundary="stage_point_signal_is_presentation_projection_only_not_decision_input",
                raw_ref=source_ref,
            )
        )
    return signals


def _dict(value: object) -> dict[str, Any]:
    if isinstance(value, FeatureEvidence | RankedDecision):
        return value.model_dump(mode="json")
    return dict(value) if isinstance(value, Mapping) else {}


def _list(value: object) -> list[dict[str, Any]]:
    return [dict(row) for row in value if isinstance(row, Mapping)] if isinstance(value, list) else []


def _string(value: object) -> str:
    return str(value or "").strip()


def _string_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [_string(row) for row in value if _string(row)]
    if isinstance(value, tuple | set):
        return [_string(row) for row in value if _string(row)]
    return []


def _first(values: Sequence[str], default: str) -> str:
    return next((row for row in values if row), default)


def _bounded_float(value: object, default: float) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = default
    return round(max(0.0, min(1.0, number)), 3)


def _confidence_band_value(value: str) -> float:
    return {"high": 0.82, "medium": 0.62, "low": 0.42}.get(value, 0.5)


def _assertion_from_confidence(value: float, *, confirmed: bool = False) -> AssertionLevelHint:
    if confirmed and value >= 0.95:
        return AssertionLevelHint.CONFIRMED
    if value >= 0.72:
        return AssertionLevelHint.SUPPORTED
    if value >= 0.5:
        return AssertionLevelHint.WEAK_CANDIDATE
    return AssertionLevelHint.BLOCKED


def _domain(value: str) -> BaziDomain:
    normalized = value.strip().lower()
    aliases = {
        "romance": "relationship",
        "foundation": "overview",
        "ten_god_energy": "ten_god",
        "structure_pattern": "structure",
        "structure_dynamic": "structure",
        "domain_rule": "overview",
        "rule": "overview",
    }
    normalized = aliases.get(normalized, normalized)
    for domain in BaziDomain:
        if domain.value == normalized:
            return domain
    return BaziDomain.UNKNOWN


def _topic_from_domain(value: str, *, fallback: BaziTopic) -> BaziTopic:
    domain = _domain(value)
    mapping = {
        BaziDomain.CHART: BaziTopic.CHART,
        BaziDomain.STRUCTURE: BaziTopic.STRUCTURE,
        BaziDomain.USEFUL_GOD: BaziTopic.USEFUL_GOD,
        BaziDomain.TIMING: BaziTopic.TIMING,
        BaziDomain.WEALTH: BaziTopic.WEALTH,
        BaziDomain.CAREER: BaziTopic.CAREER,
        BaziDomain.RELATIONSHIP: BaziTopic.RELATIONSHIP,
        BaziDomain.HEALTH: BaziTopic.HEALTH,
        BaziDomain.HIDDEN_FACTOR: BaziTopic.HIDDEN_FACTOR,
        BaziDomain.ELEMENT: BaziTopic.STRUCTURE,
        BaziDomain.TEN_GOD: BaziTopic.STRUCTURE,
    }
    return mapping.get(domain, fallback)


def _topic_from_stage_kind(kind: str) -> BaziTopic:
    return {
        "advice": BaziTopic.ADVICE,
        "question": BaziTopic.QUESTION,
        "risk": BaziTopic.ADVICE,
        "mechanism": BaziTopic.PATH,
        "evidence": BaziTopic.FEATURE,
        "branch": BaziTopic.STRUCTURE,
        "verdict": BaziTopic.STRUCTURE,
    }.get(kind, BaziTopic.FEATURE)


def _ranked_decision_domain(key: str, row: Mapping[str, Any]) -> str:
    domain = _string(row.get("domain"))
    if domain == "strength":
        return "structure"
    if domain == "structure_pattern":
        return "structure"
    if domain == "useful_god":
        return "useful_god"
    return domain or key


def _claim_key(domain: str, claim: str) -> str:
    clean = re.sub(r"\s+", "", claim.lower())
    clean = re.sub(r"[^\w\u4e00-\u9fff:-]+", "", clean)
    return f"{domain or 'unknown'}:{clean[:80]}"


def _signal_id(source_type: SignalSourceType, ref: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_.:\-\u4e00-\u9fff]+", "_", ref or "unknown")
    return f"signal:{source_type.value}:{safe[:140]}"
