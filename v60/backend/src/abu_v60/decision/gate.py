from __future__ import annotations

from abu_v60.decision.contracts import (
    DecisionAuthority,
    DecisionProposal,
    DecisionRequest,
    DecisionRoute,
    DecisionRouteStatus,
    EpistemicGateReceipt,
    GateDisposition,
)
from abu_v60.provenance import content_hash, stable_ref

EPISTEMIC_GATE_VERSION = "v60.epistemic-gate.001"


class EpistemicGate:
    """Admit a bounded proposal without granting domain write authority."""

    def evaluate(
        self,
        *,
        request: DecisionRequest,
        route: DecisionRoute,
        proposal: DecisionProposal,
    ) -> EpistemicGateReceipt:
        reason = self._rejection_reason(request=request, route=route, proposal=proposal)
        disposition = GateDisposition.REJECTED if reason is not None else GateDisposition.ADMITTED
        proposal_payload = proposal.model_dump(mode="json")
        proposal_hash = content_hash(proposal_payload)
        receipt_identity = {
            "gate_version": EPISTEMIC_GATE_VERSION,
            "request_id": request.request_id,
            "proposal_ref": proposal.proposal_ref,
            "proposal_hash": proposal_hash,
            "disposition": disposition.value,
            "reason": reason or "bounded_reasoner_proposal_admitted",
        }
        return EpistemicGateReceipt(
            receipt_ref=stable_ref("v60-epistemic-gate-receipt", receipt_identity),
            gate_version=EPISTEMIC_GATE_VERSION,
            request_id=request.request_id,
            proposal_ref=proposal.proposal_ref,
            proposal_hash=proposal_hash,
            disposition=disposition,
            reason=reason or "bounded_reasoner_proposal_admitted",
            selected_candidate_ref=(
                proposal.selected_candidate_ref if disposition is GateDisposition.ADMITTED else None
            ),
            decision_record_allowed=disposition is GateDisposition.ADMITTED,
            canonical_domain_write_allowed=False,
        )

    def _rejection_reason(
        self,
        *,
        request: DecisionRequest,
        route: DecisionRoute,
        proposal: DecisionProposal,
    ) -> str | None:
        if route.request_id != request.request_id:
            return "route_request_mismatch"
        if (
            route.status is not DecisionRouteStatus.PENDING
            or route.authority is not DecisionAuthority.LLM_REASONER
        ):
            return "reasoner_not_authorized_for_route"
        if proposal.request_id != request.request_id:
            return "proposal_request_mismatch"

        qualified = {
            candidate.candidate_ref: candidate
            for candidate in request.candidates
            if candidate.qualified
        }
        reviewed = tuple(dict.fromkeys(proposal.reviewed_candidate_refs))
        if set(reviewed) != set(qualified):
            return "qualified_candidate_comparison_incomplete"
        selected = qualified.get(proposal.selected_candidate_ref)
        if selected is None:
            return "selected_candidate_not_qualified"

        allowed_evidence = set(request.evidence_refs)
        used_evidence = set(proposal.evidence_refs_used)
        counter_evidence = set(proposal.counter_evidence_refs)
        if not used_evidence.issubset(allowed_evidence):
            return "proposal_uses_unbound_evidence"
        if not counter_evidence.issubset(allowed_evidence):
            return "proposal_uses_unbound_counter_evidence"
        if not set(selected.evidence_refs).issubset(used_evidence):
            return "selected_candidate_evidence_not_cited"
        return None
