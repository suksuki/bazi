from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.engine import Engine

from abu_v60.decision import (
    BoundedReasonerContext,
    CognitiveDecisionCoordinator,
    DecisionCandidate,
    DecisionKind,
    DecisionRequest,
    ReasonerCandidateContext,
    ReasonerEvidenceContext,
    reasoner_runtime_manifest,
)
from abu_v60.mingli.mechanism_contracts import (
    MechanismCandidateEvidence,
    MingliMechanismEvidenceVector,
)
from abu_v60.provenance import content_hash, stable_ref

MECHANISM_COMPARISON_VERSION = "v60.mechanism-attention-comparison.002"


class MechanismComparisonUnavailableError(ValueError):
    pass


class MingliMechanismComparisonService:
    """Route bounded candidate attention through the one cognition owner."""

    def __init__(
        self,
        engine: Engine,
        *,
        coordinator: CognitiveDecisionCoordinator | None = None,
    ) -> None:
        self._engine = engine
        self._coordinator = coordinator or CognitiveDecisionCoordinator()

    def current_state(
        self,
        *,
        vector: MingliMechanismEvidenceVector,
    ) -> dict[str, Any]:
        request, _ = self._request_and_context(vector)
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    text(
                        """
                        SELECT decision_id, authority, status,
                               record_json, record_hash, created_at
                        FROM cognition.decision_records
                        WHERE subject_ref = :subject_ref
                          AND decision_type = 'INTERPRETATION'
                          AND record_json->'request'->>'request_id' = :request_id
                        ORDER BY created_at DESC
                        LIMIT 1
                        """
                    ),
                    {
                        "subject_ref": vector.vector_ref,
                        "request_id": request.request_id,
                    },
                )
                .mappings()
                .one_or_none()
            )
        selected = None
        rationale_summary = None
        evidence_refs_used: list[str] = []
        if row is not None:
            record = row["record_json"]
            selected = record["route"].get("selected_candidate_ref")
            proposal = record.get("proposal") or {}
            rationale_summary = proposal.get("rationale_summary")
            evidence_refs_used = list(proposal.get("evidence_refs_used") or ())
        return {
            "comparison_version": MECHANISM_COMPARISON_VERSION,
            "request_id": request.request_id,
            "reasoner_runtime": reasoner_runtime_manifest(),
            "candidate_count": len(vector.candidates),
            "decision_ref": str(row["decision_id"]) if row is not None else None,
            "decision_hash": str(row["record_hash"]) if row is not None else None,
            "authority": str(row["authority"]) if row is not None else None,
            "status": str(row["status"]) if row is not None else "NOT_RUN",
            "selected_candidate_ref": selected,
            "rationale_summary": rationale_summary,
            "evidence_refs_used": evidence_refs_used,
            "meaning": "ATTENTION_PRIORITY_ONLY",
            "professional_verdict": False,
            "canonical_mingli_write_allowed": False,
        }

    def compare(
        self,
        *,
        vector: MingliMechanismEvidenceVector,
    ) -> dict[str, Any]:
        request, context = self._request_and_context(vector)
        if not vector.candidates:
            raise MechanismComparisonUnavailableError("mechanism_comparison_has_no_candidates")
        with self._engine.begin() as connection:
            execution = self._coordinator.decide_and_record(
                connection=connection,
                request=request,
                reasoner_context=context,
            )
        return {
            "decision_ref": execution.ledger_result.decision_id,
            "decision_hash": execution.ledger_result.record_hash,
            "already_recorded": execution.ledger_result.already_recorded,
            "authority": execution.route.authority.value,
            "selected_candidate_ref": execution.route.selected_candidate_ref,
            "meaning": "ATTENTION_PRIORITY_ONLY",
            "professional_verdict": False,
            "canonical_mingli_write_allowed": False,
            "reasoner_execution": (
                {
                    "runtime_ref": execution.reasoner_execution.runtime_ref,
                    "provider_response_ref": (execution.reasoner_execution.provider_response_ref),
                    "context_hash": execution.reasoner_execution.context_hash,
                    "input_tokens": execution.reasoner_execution.input_tokens,
                    "output_tokens": execution.reasoner_execution.output_tokens,
                    "total_tokens": execution.reasoner_execution.total_tokens,
                    "duration_ms": execution.reasoner_execution.duration_ms,
                }
                if execution.reasoner_execution is not None
                else None
            ),
        }

    @staticmethod
    def _request_and_context(
        vector: MingliMechanismEvidenceVector,
    ) -> tuple[DecisionRequest, BoundedReasonerContext | None]:
        derived_evidence = tuple(
            _candidate_evidence(candidate, vector=vector) for candidate in vector.candidates
        )
        identity = {
            "comparison_version": MECHANISM_COMPARISON_VERSION,
            "vector_ref": vector.vector_ref,
            "vector_hash": vector.vector_hash,
            "candidate_refs": [candidate.candidate_ref for candidate in vector.candidates],
        }
        request = DecisionRequest(
            request_id=stable_ref("v60-mechanism-comparison-request", identity),
            decision_kind=DecisionKind.INTERPRETATION,
            subject_ref=vector.vector_ref,
            evidence_refs=tuple(item.evidence_ref for item in derived_evidence),
            candidates=tuple(
                DecisionCandidate(
                    candidate_ref=candidate.candidate_ref,
                    evidence_refs=(evidence.evidence_ref,),
                    qualified=candidate.comparison_eligible,
                )
                for candidate, evidence in zip(
                    vector.candidates,
                    derived_evidence,
                    strict=True,
                )
            ),
            llm_allowed=True,
            correlation_id=stable_ref(
                "v60-mechanism-comparison-correlation",
                {"case_ref": vector.case_ref, "chart": vector.chart_version_ref},
            ),
            causation_id=vector.vector_ref,
        )
        if len(vector.candidates) < 2:
            return request, None
        return request, BoundedReasonerContext(
            candidates=tuple(
                ReasonerCandidateContext(
                    candidate_ref=candidate.candidate_ref,
                    statement=(
                        f"{candidate.pattern_label}。"
                        f"{candidate.structural_statement}"
                        f"边界：{candidate.forbidden_shortcut}"
                        "本次只能比较后续关注优先级，不能裁定有效做功。"
                    ),
                )
                for candidate in vector.candidates
            ),
            evidence=derived_evidence,
            locale="zh-CN",
        )


def _candidate_evidence(
    candidate: MechanismCandidateEvidence,
    *,
    vector: MingliMechanismEvidenceVector,
) -> ReasonerEvidenceContext:
    role_text = "；".join(
        (
            f"{role.role_id}={','.join(role.occurrence_labels)}"
            f"（明干{role.visible_occurrence_count}/藏干成员"
            f"{role.hidden_occurrence_count}）"
        )
        for role in candidate.roles
    )
    payload = {
        "vector_ref": vector.vector_ref,
        "candidate_ref": candidate.candidate_ref,
        "roles": [role.model_dump(mode="json") for role in candidate.roles],
        "support_evidence_refs": candidate.support_evidence_refs,
        "context_evidence_refs": candidate.context_evidence_refs,
        "counter_evidence_refs": candidate.counter_evidence_refs,
        "blocker_codes": candidate.blocker_codes,
    }
    evidence_ref = stable_ref("v60-mechanism-comparison-evidence", payload)
    return ReasonerEvidenceContext(
        evidence_ref=evidence_ref,
        statement=(
            f"{candidate.pattern_label}的确定性结构观测：{role_text}。"
            f"直接事实{len(candidate.support_evidence_refs)}条，"
            f"上下文{len(candidate.context_evidence_refs)}条，"
            f"反证模型尚未准入；阻断项：{','.join(candidate.blocker_codes)}。"
        ),
        source_ref=vector.vector_ref,
        source_version=vector.vector_version,
        source_hash=content_hash(payload),
    )
