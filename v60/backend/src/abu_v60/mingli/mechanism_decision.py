from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from sqlalchemy import text
from sqlalchemy.engine import Connection, Engine

from abu_v60.decision import (
    BoundedReasonerContext,
    CognitiveDecisionCoordinator,
    CognitiveDecisionKernel,
    DecisionAuthority,
    DecisionCandidate,
    DecisionKind,
    DecisionProposal,
    DecisionRequest,
    DecisionRoute,
    DecisionRouteStatus,
    EpistemicGate,
    EpistemicGateReceipt,
    ReasonerCandidateContext,
    ReasonerEvidenceContext,
    reasoner_runtime_manifest,
)
from abu_v60.decision.service import DECISION_KERNEL_VERSION
from abu_v60.identity import lock_account_transaction
from abu_v60.mingli.mechanism_contracts import (
    MechanismCandidateEvidence,
    MingliMechanismEvidenceVector,
)
from abu_v60.provenance import content_hash, stable_ref

MECHANISM_COMPARISON_VERSION = "v60.mechanism-attention-comparison.002"
MECHANISM_DECISION_TRACE_VERSION = "v60.mingli-decision-trace.001"


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
        request, reasoner_context = self._request_and_context(vector)
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
        decision_trace = None
        if row is not None:
            record = row["record_json"]
            if isinstance(record, str):
                record = json.loads(record)
            if not isinstance(record, dict):
                raise MechanismComparisonUnavailableError(
                    "mechanism_decision_record_payload_invalid"
                )
            decision_trace = _verified_decision_trace(
                decision_ref=str(row["decision_id"]),
                decision_hash=str(row["record_hash"]),
                row_authority=str(row["authority"]),
                row_status=str(row["status"]),
                record=record,
                request=request,
                expected_context_hash=(
                    reasoner_context.context_hash
                    if reasoner_context is not None
                    else None
                ),
            )
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
            "decision_trace": decision_trace,
            "meaning": "ATTENTION_PRIORITY_ONLY",
            "professional_verdict": False,
            "canonical_mingli_write_allowed": False,
        }

    def compare(
        self,
        *,
        account_ref: str,
        vector: MingliMechanismEvidenceVector,
    ) -> dict[str, Any]:
        with self._engine.begin() as connection:
            return self.compare_in_connection(
                connection,
                account_ref=account_ref,
                vector=vector,
            )

    def compare_in_connection(
        self,
        connection: Connection,
        *,
        account_ref: str,
        vector: MingliMechanismEvidenceVector,
    ) -> dict[str, Any]:
        lock_account_transaction(
            connection,
            account_ref=account_ref,
        )
        if not self._case_is_active_owned(
            connection,
            account_ref=account_ref,
            case_ref=vector.case_ref,
        ):
            raise MechanismComparisonUnavailableError(
                "mechanism_comparison_active_owner_case_conflict"
            )
        request, context = self._request_and_context(vector)
        if not vector.candidates:
            raise MechanismComparisonUnavailableError("mechanism_comparison_has_no_candidates")
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
    def _case_is_active_owned(
        connection: Connection,
        *,
        account_ref: str,
        case_ref: str,
    ) -> bool:
        return bool(
            connection.execute(
                text(
                    """
                    SELECT EXISTS (
                        SELECT 1
                        FROM mingli.cases
                        WHERE case_ref = :case_ref
                          AND owner_account_ref = :account_ref
                          AND subject_kind = 'HUMAN_OWNER'
                          AND status = 'ACTIVE'
                    )
                    """
                ),
                {
                    "case_ref": case_ref,
                    "account_ref": account_ref,
                },
            ).scalar_one()
        )

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


def _verified_decision_trace(
    *,
    decision_ref: str,
    decision_hash: str,
    row_authority: str,
    row_status: str,
    record: Mapping[str, Any],
    request: DecisionRequest,
    expected_context_hash: str | None,
) -> dict[str, Any]:
    """Verify and expose one immutable attention Decision without widening it."""

    expected_decision_ref = stable_ref(
        "v60-decision",
        {
            "request_id": request.request_id,
            "decision_kind": request.decision_kind.value,
            "subject_ref": request.subject_ref,
        },
    )
    if decision_ref != expected_decision_ref:
        raise MechanismComparisonUnavailableError(
            "mechanism_decision_identity_invalid"
        )
    if content_hash(record) != decision_hash:
        raise MechanismComparisonUnavailableError(
            "mechanism_decision_record_hash_invalid"
        )
    if record.get("kernel_version") != DECISION_KERNEL_VERSION:
        raise MechanismComparisonUnavailableError(
            "mechanism_decision_kernel_version_invalid"
        )
    request_payload = request.model_dump(mode="json")
    if record.get("request") != request_payload:
        raise MechanismComparisonUnavailableError(
            "mechanism_decision_record_request_mismatch"
        )
    route = _mapping(record.get("route"), "mechanism_decision_route_invalid")
    try:
        route_contract = DecisionRoute.model_validate(route)
    except ValueError as exc:
        raise MechanismComparisonUnavailableError(
            "mechanism_decision_route_invalid"
        ) from exc
    if (
        route.get("request_id") != request.request_id
        or route.get("authority") != row_authority
        or route.get("status") != row_status
        or row_status != "RESOLVED"
        or dict(route) != route_contract.model_dump(mode="json")
    ):
        raise MechanismComparisonUnavailableError(
            "mechanism_decision_route_identity_mismatch"
        )
    kernel_route = CognitiveDecisionKernel().route(request)
    expected_record_keys = {
        "kernel_version",
        "request",
        "route",
        *(
            ("proposal", "gate_receipt")
            if row_authority == "LLM_REASONER"
            else ()
        ),
    }
    if set(record) != expected_record_keys:
        raise MechanismComparisonUnavailableError(
            "mechanism_decision_record_shape_invalid"
        )

    attention_candidate_refs = tuple(
        candidate.candidate_ref
        for candidate in request.candidates
        if candidate.qualified
    )
    bound_evidence_refs = tuple(request.evidence_refs)
    selected_candidate_ref = route.get("selected_candidate_ref")
    if (
        not isinstance(selected_candidate_ref, str)
        or selected_candidate_ref not in attention_candidate_refs
    ):
        raise MechanismComparisonUnavailableError(
            "mechanism_decision_selected_candidate_invalid"
        )
    selected_candidate = next(
        candidate
        for candidate in request.candidates
        if candidate.candidate_ref == selected_candidate_ref
    )

    proposal_ref: str | None = None
    gate_receipt_ref: str | None = None
    gate_version: str | None = None
    reasoner_runtime_ref: str | None = None
    provider_id: str | None = None
    model_ref: str | None = None
    model_profile_ref: str | None = None
    model_profile_hash: str | None = None
    prompt_ref: str | None = None
    provider_response_ref: str | None = None
    context_hash: str | None = None
    provider_counter_evidence_refs: tuple[str, ...] = ()

    if row_authority == "LLM_REASONER":
        expected_recorded_route = DecisionRoute(
            request_id=request.request_id,
            status=DecisionRouteStatus.RESOLVED,
            authority=DecisionAuthority.LLM_REASONER,
            selected_candidate_ref=selected_candidate_ref,
            reason="bounded_reasoner_proposal_admitted",
        )
        if (
            kernel_route.status is not DecisionRouteStatus.PENDING
            or kernel_route.authority is not DecisionAuthority.LLM_REASONER
            or route_contract != expected_recorded_route
        ):
            raise MechanismComparisonUnavailableError(
                "mechanism_decision_route_not_canonical"
            )
        proposal = _mapping(
            record.get("proposal"),
            "mechanism_decision_proposal_missing",
        )
        gate = _mapping(
            record.get("gate_receipt"),
            "mechanism_decision_gate_receipt_missing",
        )
        try:
            proposal_contract = DecisionProposal.model_validate(proposal)
            gate_contract = EpistemicGateReceipt.model_validate(gate)
        except ValueError as exc:
            raise MechanismComparisonUnavailableError(
                "mechanism_decision_proposal_gate_contract_invalid"
            ) from exc
        if (
            dict(proposal) != proposal_contract.model_dump(mode="json")
            or dict(gate) != gate_contract.model_dump(mode="json")
        ):
            raise MechanismComparisonUnavailableError(
                "mechanism_decision_proposal_gate_contract_invalid"
            )
        canonical_gate = EpistemicGate().evaluate(
            request=request,
            route=kernel_route,
            proposal=proposal_contract,
        )
        if gate_contract != canonical_gate:
            raise MechanismComparisonUnavailableError(
                "mechanism_decision_gate_not_canonical"
            )
        reviewed_candidate_refs = _unique_string_tuple(
            proposal.get("reviewed_candidate_refs"),
            "mechanism_decision_reviewed_candidates_invalid",
        )
        evidence_refs_used = _unique_string_tuple(
            proposal.get("evidence_refs_used"),
            "mechanism_decision_evidence_refs_invalid",
        )
        provider_counter_evidence_refs = _unique_string_tuple(
            proposal.get("counter_evidence_refs"),
            "mechanism_decision_counter_refs_invalid",
        )
        candidate_coverage_semantics = (
            "PROVIDER_REVIEWED_ATTENTION_CANDIDATES"
        )
        evidence_use_semantics = "PROVIDER_CITED_BOUND_EVIDENCE"
        if (
            set(reviewed_candidate_refs) != set(attention_candidate_refs)
            or not set(evidence_refs_used) <= set(bound_evidence_refs)
            or not set(provider_counter_evidence_refs)
            <= set(bound_evidence_refs)
            or not set(selected_candidate.evidence_refs)
            <= set(evidence_refs_used)
        ):
            raise MechanismComparisonUnavailableError(
                "mechanism_decision_evidence_coverage_invalid"
            )
        if (
            proposal.get("request_id") != request.request_id
            or proposal.get("selected_candidate_ref")
            != selected_candidate_ref
            or gate.get("request_id") != request.request_id
            or gate.get("proposal_ref") != proposal.get("proposal_ref")
            or gate.get("proposal_hash") != content_hash(proposal)
            or gate.get("selected_candidate_ref")
            != selected_candidate_ref
            or gate.get("disposition") != "ADMITTED"
            or gate.get("decision_record_allowed") is not True
            or gate.get("canonical_domain_write_allowed") is not False
        ):
            raise MechanismComparisonUnavailableError(
                "mechanism_decision_gate_identity_invalid"
            )
        proposal_ref = _required_string(
            proposal.get("proposal_ref"),
            "mechanism_decision_proposal_ref_invalid",
        )
        gate_receipt_ref = _required_string(
            gate.get("receipt_ref"),
            "mechanism_decision_gate_receipt_ref_invalid",
        )
        gate_version = _required_string(
            gate.get("gate_version"),
            "mechanism_decision_gate_version_invalid",
        )
        gate_disposition = "ADMITTED"
        gate_reason = _required_string(
            gate.get("reason"),
            "mechanism_decision_gate_reason_invalid",
        )
        reasoner_runtime_ref = _required_string(
            proposal.get("reasoner_runtime_ref"),
            "mechanism_decision_runtime_ref_invalid",
        )
        provider_id = _required_string(
            proposal.get("provider_id"),
            "mechanism_decision_provider_id_invalid",
        )
        model_ref = _required_string(
            proposal.get("model_ref"),
            "mechanism_decision_model_ref_invalid",
        )
        model_profile_ref = _required_string(
            proposal.get("model_profile_ref"),
            "mechanism_decision_model_profile_ref_invalid",
        )
        model_profile_hash = _required_string(
            proposal.get("model_profile_hash"),
            "mechanism_decision_model_profile_hash_invalid",
        )
        prompt_ref = _required_string(
            proposal.get("prompt_ref"),
            "mechanism_decision_prompt_ref_invalid",
        )
        provider_response_ref = _required_string(
            proposal.get("provider_response_ref"),
            "mechanism_decision_provider_response_ref_invalid",
        )
        context_hash = _required_string(
            proposal.get("context_hash"),
            "mechanism_decision_context_hash_invalid",
        )
        confidence = proposal.get("confidence")
        rationale_summary = _required_string(
            proposal.get("rationale_summary"),
            "mechanism_decision_rationale_invalid",
        )
        if (
            expected_context_hash is None
            or context_hash != expected_context_hash
            or isinstance(confidence, bool)
            or not isinstance(confidence, (int, float))
            or not 0.0 <= confidence <= 1.0
        ):
            raise MechanismComparisonUnavailableError(
                "mechanism_decision_reasoner_context_invalid"
            )
        expected_proposal_ref = stable_ref(
            "v60-reasoner-proposal",
            {
                "runtime_ref": reasoner_runtime_ref,
                "request_id": request.request_id,
                "provider_id": provider_id,
                "model_ref": model_ref,
                "model_profile_ref": model_profile_ref,
                "model_profile_hash": model_profile_hash,
                "prompt_ref": prompt_ref,
                "provider_response_ref": provider_response_ref,
                "context_hash": context_hash,
                "output": {
                    "selected_candidate_ref": selected_candidate_ref,
                    "reviewed_candidate_refs": list(reviewed_candidate_refs),
                    "evidence_refs_used": list(evidence_refs_used),
                    "counter_evidence_refs": list(
                        provider_counter_evidence_refs
                    ),
                    "confidence": confidence,
                    "rationale_summary": rationale_summary,
                },
            },
        )
        expected_gate_receipt_ref = stable_ref(
            "v60-epistemic-gate-receipt",
            {
                "gate_version": gate_version,
                "request_id": request.request_id,
                "proposal_ref": proposal_ref,
                "proposal_hash": gate.get("proposal_hash"),
                "disposition": "ADMITTED",
                "reason": gate_reason,
            },
        )
        if (
            proposal_ref != expected_proposal_ref
            or gate_receipt_ref != expected_gate_receipt_ref
        ):
            raise MechanismComparisonUnavailableError(
                "mechanism_decision_provenance_identity_invalid"
            )
    elif row_authority == "RULE_ENGINE":
        if (
            kernel_route.status is not DecisionRouteStatus.RESOLVED
            or kernel_route.authority is not DecisionAuthority.RULE_ENGINE
            or route_contract != kernel_route
        ):
            raise MechanismComparisonUnavailableError(
                "mechanism_decision_route_not_canonical"
            )
        reviewed_candidate_refs = attention_candidate_refs
        evidence_refs_used = ()
        candidate_coverage_semantics = (
            "RULE_ENGINE_SINGLE_ATTENTION_CANDIDATE"
        )
        evidence_use_semantics = "REQUEST_BOUND_NOT_PROVIDER_USED"
        gate_disposition = "NOT_REQUIRED"
        gate_reason = "single_attention_candidate_selected_by_rule_engine"
    else:
        raise MechanismComparisonUnavailableError(
            "mechanism_decision_authority_invalid"
        )

    return {
        "trace_version": MECHANISM_DECISION_TRACE_VERSION,
        "trace_integrity_status": "VERIFIED",
        "decision_ref": decision_ref,
        "decision_hash": decision_hash,
        "kernel_version": _required_string(
            DECISION_KERNEL_VERSION,
            "mechanism_decision_kernel_version_invalid",
        ),
        "request_id": request.request_id,
        "subject_ref": request.subject_ref,
        "authority": row_authority,
        "status": row_status,
        "route_reason": _required_string(
            route.get("reason"),
            "mechanism_decision_route_reason_invalid",
        ),
        "selected_candidate_ref": selected_candidate_ref,
        "attention_candidate_refs": list(attention_candidate_refs),
        "reviewed_candidate_refs": list(reviewed_candidate_refs),
        "candidate_coverage_complete": True,
        "candidate_coverage_semantics": candidate_coverage_semantics,
        "bound_evidence_refs": list(bound_evidence_refs),
        "evidence_refs_used": list(evidence_refs_used),
        "evidence_use_semantics": evidence_use_semantics,
        "selected_evidence_bound": True,
        "selected_evidence_use_semantics": (
            "PROVIDER_CITED_BOUND_EVIDENCE"
            if row_authority == "LLM_REASONER"
            else "REQUEST_BOUND_RULE_NOT_PROVIDER_CITED"
        ),
        "provider_counter_evidence_refs": list(
            provider_counter_evidence_refs
        ),
        "proposal_ref": proposal_ref,
        "gate_receipt_ref": gate_receipt_ref,
        "gate_version": gate_version,
        "gate_disposition": gate_disposition,
        "gate_reason": gate_reason,
        "decision_record_allowed": True,
        "canonical_domain_write_allowed": False,
        "reasoner_runtime_ref": reasoner_runtime_ref,
        "provider_id": provider_id,
        "model_ref": model_ref,
        "model_profile_ref": model_profile_ref,
        "model_profile_hash": model_profile_hash,
        "prompt_ref": prompt_ref,
        "provider_response_ref": provider_response_ref,
        "context_hash": context_hash,
        "attention_scope": (
            "STATIC_NATAL_MECHANISM_CANDIDATE_PRIORITY_ONLY"
        ),
        "admitted_input_scopes": ["MECHANISM_CANDIDATE_EVIDENCE"],
        "unbound_input_scopes": [
            "SOURCE_USABILITY",
            "TIMING_ACTIVATION",
            "MECHANISM_QUALIFICATION",
            "PROFESSIONAL_ADMISSION",
            "CALIBRATION",
        ],
        "counter_evidence_semantics": (
            "BOUND_REF_ONLY_NOT_PROFESSIONALLY_ADMITTED"
        ),
        "selection_rationale_contract": (
            "FREE_TEXT_NO_DISTINCT_SELECTION_BASIS_FIELD"
            if row_authority == "LLM_REASONER"
            else "DETERMINISTIC_SINGLE_CANDIDATE_ROUTE_REASON_ONLY"
        ),
        "provider_confidence_semantics": (
            "RECORDED_UNCALIBRATED_NOT_PRODUCT_AUTHORITY"
            if row_authority == "LLM_REASONER"
            else "NOT_RECORDED_RULE_ENGINE_ROUTE"
        ),
        "professional_selection_qualified": False,
        "professional_verdict_allowed": False,
        "probability_claim_allowed": False,
        "read_only": True,
    }


def _mapping(value: Any, error: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise MechanismComparisonUnavailableError(error)
    return value


def _required_string(value: Any, error: str) -> str:
    if not isinstance(value, str) or not value:
        raise MechanismComparisonUnavailableError(error)
    return value


def _unique_string_tuple(value: Any, error: str) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        raise MechanismComparisonUnavailableError(error)
    result = tuple(value)
    if (
        any(not isinstance(item, str) or not item for item in result)
        or len(result) != len(set(result))
    ):
        raise MechanismComparisonUnavailableError(error)
    return result
