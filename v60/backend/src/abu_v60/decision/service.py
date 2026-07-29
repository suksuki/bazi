from __future__ import annotations

import json

from sqlalchemy import text

from abu_v60.decision.contracts import (
    DecisionAuthority,
    DecisionKind,
    DecisionLedgerResult,
    DecisionProposal,
    DecisionRequest,
    DecisionRoute,
    DecisionRouteStatus,
    EpistemicGateReceipt,
    GateDisposition,
)
from abu_v60.provenance import canonical_json, content_hash, stable_ref

DECISION_KERNEL_VERSION = "v60.cognitive-decision-kernel.004"


class DecisionLedgerError(ValueError):
    pass


_SYSTEM_ONLY_KINDS = {
    DecisionKind.FACT,
    DecisionKind.POLICY,
    DecisionKind.WORLD_TRANSITION,
    DecisionKind.WORLD_OUTCOME,
}

_LLM_ELIGIBLE_KINDS = {
    DecisionKind.DOMAIN_INFERENCE,
    DecisionKind.INTERPRETATION,
    DecisionKind.NPC_INTENT,
    DecisionKind.STORY_PRESENTATION,
}


class CognitiveDecisionKernel:
    """Route a decision without letting a reasoning provider commit domain state."""

    def route(self, request: DecisionRequest) -> DecisionRoute:
        if request.decision_kind is DecisionKind.KNOWLEDGE_PROMOTION:
            return DecisionRoute(
                request_id=request.request_id,
                status=DecisionRouteStatus.PENDING,
                authority=DecisionAuthority.OWNER_PROFESSIONAL_REVIEW,
                reason="global_knowledge_requires_owner_professional_review",
            )

        if request.human_required or request.decision_kind is DecisionKind.HUMAN_CONSENT:
            return DecisionRoute(
                request_id=request.request_id,
                status=DecisionRouteStatus.PENDING,
                authority=DecisionAuthority.HUMAN,
                reason="human_authority_required",
            )

        if request.deterministic_result is not None:
            return DecisionRoute(
                request_id=request.request_id,
                status=DecisionRouteStatus.RESOLVED,
                authority=DecisionAuthority.SYSTEM,
                result=request.deterministic_result,
                reason="deterministic_result_available",
            )

        qualified = tuple(candidate for candidate in request.candidates if candidate.qualified)

        if request.decision_kind in _SYSTEM_ONLY_KINDS:
            return DecisionRoute(
                request_id=request.request_id,
                status=DecisionRouteStatus.UNRESOLVED,
                authority=DecisionAuthority.SYSTEM,
                reason="system_only_decision_has_no_deterministic_result",
            )

        if len(qualified) == 1:
            return DecisionRoute(
                request_id=request.request_id,
                status=DecisionRouteStatus.RESOLVED,
                authority=DecisionAuthority.RULE_ENGINE,
                selected_candidate_ref=qualified[0].candidate_ref,
                reason="one_qualified_candidate_remains",
            )

        if (
            len(qualified) > 1
            and request.llm_allowed
            and request.decision_kind in _LLM_ELIGIBLE_KINDS
        ):
            return DecisionRoute(
                request_id=request.request_id,
                status=DecisionRouteStatus.PENDING,
                authority=DecisionAuthority.LLM_REASONER,
                reason="qualified_interpretations_require_bounded_comparison",
            )

        return DecisionRoute(
            request_id=request.request_id,
            status=DecisionRouteStatus.UNRESOLVED,
            authority=DecisionAuthority.NONE,
            reason="insufficient_qualified_evidence",
        )


class CognitiveDecisionLedger:
    """Persist one immutable record for each routed system decision."""

    def __init__(self, kernel: CognitiveDecisionKernel | None = None) -> None:
        self._kernel = kernel or CognitiveDecisionKernel()

    def route_and_record(
        self,
        *,
        connection: object,
        request: DecisionRequest,
    ) -> DecisionLedgerResult:
        route = self._kernel.route(request)
        if route.status is not DecisionRouteStatus.RESOLVED:
            raise DecisionLedgerError("non_final_decision_cannot_be_recorded")
        return self._record(
            connection=connection,
            request=request,
            route=route,
        )

    def replay_existing(
        self,
        *,
        connection: object,
        request: DecisionRequest,
    ) -> DecisionLedgerResult | None:
        decision_id = self._decision_id(request)
        row = (
            connection.execute(
                text(
                    """
                    SELECT record_json, record_hash
                    FROM cognition.decision_records
                    WHERE decision_id = :decision_id
                    """
                ),
                {"decision_id": decision_id},
            )
            .mappings()
            .one_or_none()
        )
        if row is None:
            return None
        record_payload = row["record_json"]
        if isinstance(record_payload, str):
            record_payload = json.loads(record_payload)
        if not isinstance(record_payload, dict):
            raise DecisionLedgerError("decision_record_payload_invalid")
        if record_payload.get("request") != request.model_dump(mode="json"):
            raise DecisionLedgerError("decision_record_conflict")
        if content_hash(record_payload) != row["record_hash"]:
            raise DecisionLedgerError("decision_record_hash_invalid")
        route = DecisionRoute.model_validate(record_payload.get("route"))
        return DecisionLedgerResult(
            decision_id=decision_id,
            route=route,
            record_hash=row["record_hash"],
            already_recorded=True,
        )

    def record_admitted_proposal(
        self,
        *,
        connection: object,
        request: DecisionRequest,
        proposal: DecisionProposal,
        gate_receipt: EpistemicGateReceipt,
    ) -> DecisionLedgerResult:
        if (
            gate_receipt.disposition is not GateDisposition.ADMITTED
            or not gate_receipt.decision_record_allowed
            or gate_receipt.canonical_domain_write_allowed
        ):
            raise DecisionLedgerError("proposal_not_admitted_for_decision_record")
        if (
            gate_receipt.request_id != request.request_id
            or gate_receipt.proposal_ref != proposal.proposal_ref
            or gate_receipt.selected_candidate_ref != proposal.selected_candidate_ref
        ):
            raise DecisionLedgerError("proposal_gate_identity_mismatch")
        if gate_receipt.proposal_hash != content_hash(proposal.model_dump(mode="json")):
            raise DecisionLedgerError("proposal_gate_hash_mismatch")

        route = DecisionRoute(
            request_id=request.request_id,
            status=DecisionRouteStatus.RESOLVED,
            authority=DecisionAuthority.LLM_REASONER,
            selected_candidate_ref=proposal.selected_candidate_ref,
            reason="bounded_reasoner_proposal_admitted",
        )
        return self._record(
            connection=connection,
            request=request,
            route=route,
            supplemental={
                "proposal": proposal.model_dump(mode="json"),
                "gate_receipt": gate_receipt.model_dump(mode="json"),
            },
        )

    def _record(
        self,
        *,
        connection: object,
        request: DecisionRequest,
        route: DecisionRoute,
        supplemental: dict[str, object] | None = None,
    ) -> DecisionLedgerResult:
        decision_id = self._decision_id(request)
        record_payload = {
            "kernel_version": DECISION_KERNEL_VERSION,
            "request": request.model_dump(mode="json"),
            "route": route.model_dump(mode="json"),
            **(supplemental or {}),
        }
        record_hash = content_hash(record_payload)
        inserted = connection.execute(
            text(
                """
                INSERT INTO cognition.decision_records
                    (decision_id, decision_type, subject_ref, authority,
                     method, status, correlation_id, causation_id,
                     record_json, record_hash)
                VALUES
                    (:decision_id, :decision_type, :subject_ref, :authority,
                     :method, :status, :correlation_id, :causation_id,
                     CAST(:record_json AS jsonb), :record_hash)
                ON CONFLICT DO NOTHING
                RETURNING decision_id
                """
            ),
            {
                "decision_id": decision_id,
                "decision_type": request.decision_kind.value,
                "subject_ref": request.subject_ref,
                "authority": route.authority.value,
                "method": DECISION_KERNEL_VERSION,
                "status": route.status.value,
                "correlation_id": request.correlation_id,
                "causation_id": request.causation_id,
                "record_json": canonical_json(record_payload),
                "record_hash": record_hash,
            },
        ).scalar_one_or_none()
        already_recorded = inserted is None
        if already_recorded:
            existing_hash = connection.execute(
                text(
                    """
                    SELECT record_hash
                    FROM cognition.decision_records
                    WHERE decision_id = :decision_id
                    """
                ),
                {"decision_id": decision_id},
            ).scalar_one_or_none()
            if existing_hash is None:
                raise DecisionLedgerError("decision_hash_owned_by_other_identity")
            if existing_hash != record_hash:
                raise DecisionLedgerError("decision_record_conflict")

        return DecisionLedgerResult(
            decision_id=decision_id,
            route=route,
            record_hash=record_hash,
            already_recorded=already_recorded,
        )

    @staticmethod
    def _decision_id(request: DecisionRequest) -> str:
        return stable_ref(
            "v60-decision",
            {
                "request_id": request.request_id,
                "decision_kind": request.decision_kind.value,
                "subject_ref": request.subject_ref,
            },
        )


# Backward-compatible public name while V60 callers move to the constitutional name.
DecisionRouter = CognitiveDecisionKernel
