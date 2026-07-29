from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from abu_v60.knowledge import KnowledgeAuthority
from abu_v60.mingli.contracts import (
    CandidateQualificationDimension,
    CandidateQualificationReceipt,
    CandidateQualificationStatus,
    MingliCandidatePath,
)
from abu_v60.provenance import content_hash, stable_ref

CANDIDATE_QUALIFICATION_ENGINE_VERSION = "v60.candidate-qualification-engine.001"


class CandidateQualificationEngine:
    """Evaluate admitted evidence dimensions without deciding professional effect."""

    def __init__(self, authority: KnowledgeAuthority | None = None) -> None:
        self._authority = authority or KnowledgeAuthority()

    @property
    def profile_ref(self) -> str:
        return self._profile().source_ref

    def evaluate_structure_evidence(
        self,
        *,
        candidate: MingliCandidatePath,
        fact: Mapping[str, Any],
    ) -> CandidateQualificationReceipt:
        profile = self._profile()
        fact_type = str(fact.get("fact_type", ""))
        rule = next(
            (item for item in profile.rules if fact_type in item.admitted_fact_types),
            None,
        )
        if rule is None:
            return self._receipt(
                candidate=candidate,
                status=CandidateQualificationStatus.NOT_ADMITTED,
                rule_ref=None,
                rule_hash=None,
                evidence_refs=(),
                evaluated_claims=(f"fact_type:{fact_type or 'missing'}",),
                missing_claims=("admitted_rule",),
                forbidden_conclusions=(),
                reason="no_admitted_structure_evidence_rule",
            )

        payload = fact.get("fact_json")
        claims = (
            f"fact_type:{fact_type}",
            f"authority:{fact.get('authority', 'missing')}",
            f"source_ref:{fact.get('source_ref', 'missing')}",
        )
        missing: list[str] = []
        if fact.get("fact_ref") != candidate.relation_fact_ref:
            missing.append("candidate_relation_fact_binding")
        if fact.get("authority") != rule.required_authority:
            missing.append("required_authority")
        if fact.get("source_ref") not in rule.required_source_refs:
            missing.append("required_source_ref")
        if not isinstance(payload, Mapping):
            missing.append("fact_payload")
        else:
            for claim in rule.required_boolean_claims:
                if payload.get(claim) is not True:
                    missing.append(claim)

        status = (
            CandidateQualificationStatus.REJECTED
            if missing
            else CandidateQualificationStatus.SATISFIED
        )
        evidence_refs = (
            (candidate.relation_fact_ref,)
            if fact.get("fact_ref") == candidate.relation_fact_ref
            else ()
        )
        return self._receipt(
            candidate=candidate,
            status=status,
            rule_ref=rule.rule_ref,
            rule_hash=rule.rule_hash,
            evidence_refs=evidence_refs,
            evaluated_claims=claims
            + tuple(f"{claim}:true" for claim in rule.required_boolean_claims if not missing),
            missing_claims=tuple(missing),
            forbidden_conclusions=rule.forbidden_conclusions,
            reason=(
                "structure_membership_evidence_satisfied"
                if status is CandidateQualificationStatus.SATISFIED
                else "structure_membership_evidence_rejected"
            ),
        )

    def _profile(self):
        return self._authority.active_candidate_rule_profile()

    def _receipt(
        self,
        *,
        candidate: MingliCandidatePath,
        status: CandidateQualificationStatus,
        rule_ref: str | None,
        rule_hash: str | None,
        evidence_refs: tuple[str, ...],
        evaluated_claims: tuple[str, ...],
        missing_claims: tuple[str, ...],
        forbidden_conclusions: tuple[str, ...],
        reason: str,
    ) -> CandidateQualificationReceipt:
        fields = {
            "evaluator_version": CANDIDATE_QUALIFICATION_ENGINE_VERSION,
            "candidate_ref": candidate.candidate_ref,
            "dimension": CandidateQualificationDimension.STRUCTURE_EVIDENCE,
            "status": status,
            "rule_ref": rule_ref,
            "rule_hash": rule_hash,
            "evidence_refs": evidence_refs,
            "evaluated_claims": evaluated_claims,
            "missing_claims": missing_claims,
            "forbidden_conclusions": forbidden_conclusions,
            "reason": reason,
            "selection_authority": False,
        }
        identity = {
            key: value.value if hasattr(value, "value") else value for key, value in fields.items()
        }
        receipt_hash = content_hash(identity)
        return CandidateQualificationReceipt(
            receipt_ref=stable_ref("v60-candidate-qualification", identity),
            receipt_hash=receipt_hash,
            **fields,
        )
