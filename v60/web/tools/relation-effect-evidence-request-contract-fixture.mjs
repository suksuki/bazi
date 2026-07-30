import {
  buildRelationEffectEvidencePacketFixture,
  makeNotTriggeredEvidencePacketFixture,
} from "./relation-effect-evidence-packet-contract-fixture.mjs";

export function buildRecordedRelationEffectEvidenceRequestFixture() {
  const fixture = buildRelationEffectEvidencePacketFixture();
  const requestItems = fixture.packet.demand_packets.map(
    (demandPacket, requestIndex) => ({
      request_item_ref: `evidence-request-item-ref-${requestIndex + 1}`,
      demand_packet_ref: demandPacket.demand_packet_ref,
      demand_packet_hash: demandPacket.demand_packet_hash,
      assessment_ref: demandPacket.assessment_ref,
      assessment_hash: demandPacket.assessment_hash,
      demand_ref: demandPacket.demand_ref,
      dimension_slots: demandPacket.dimension_slots.map((slot) => ({
        slot_ref: slot.slot_ref,
        dimension_id: slot.dimension_id,
        requirement: slot.requirement,
        requested_artifact_kinds: [...slot.requested_artifact_kinds],
        next_action: slot.next_action,
        status: "REQUESTED_NOT_EVIDENCE",
        professional_material_count: 0,
        professional_evidence_count: 0,
        ready: false,
      })),
      requested_dimension_slot_count:
        demandPacket.required_dimension_slot_count,
    }),
  );
  const requestReceipt = {
    receipt_ref: "relation-effect-evidence-request-receipt-ref-visible",
    receipt_hash: "e".repeat(64),
    receipt_version:
      "v60.mingli-relation-effect-evidence-request-receipt.001",
    request_version:
      "v60.mingli-relation-effect-evidence-request.001",
    requester_account_ref: "account-ref-owner-visible",
    idempotency_key:
      "v60.mingli-relation-effect-evidence-request.001:" +
      fixture.packet.packet_ref,
    case_ref: fixture.packet.case_ref,
    chart_version_ref: fixture.packet.chart_version_ref,
    reading_ref: fixture.packet.reading_ref,
    reading_hash: fixture.packet.reading_hash,
    frontier_ref: fixture.packet.frontier_ref,
    frontier_hash: fixture.packet.frontier_hash,
    admission_review_ref: fixture.packet.admission_review_ref,
    admission_review_hash: fixture.packet.admission_review_hash,
    policy_ref: fixture.packet.policy_ref,
    policy_hash: fixture.packet.policy_hash,
    proposal_ref: fixture.packet.proposal_ref,
    proposal_hash: fixture.packet.proposal_hash,
    packet_ref: fixture.packet.packet_ref,
    packet_hash: fixture.packet.packet_hash,
    request_items: requestItems,
    request_item_count: requestItems.length,
    requested_dimension_slot_count:
      fixture.packet.required_dimension_slot_count,
    ready_dimension_slot_count: 0,
    professional_material_count: 0,
    professional_evidence_count: 0,
    status: "REQUEST_RECORDED_NOT_EVIDENCE",
    semantics: "PREPARATION_REQUEST_NOT_PROFESSIONAL_EVIDENCE",
    evidence_role: "NOT_EVIDENCE",
    effect_decision_status: "WITHHELD",
    effect_status: "UNRESOLVED",
    usability_status: "UNRESOLVED",
    llm_allowed: false,
    provider_invoked: false,
    reasoner_invoked: false,
    owner_professional_review_invoked: false,
    knowledge_admission_eligible: false,
    knowledge_write_allowed: false,
    gate_invoked: false,
    decision_request_created: false,
    decision_created: false,
    professional_verdict_allowed: false,
    probability_claim_allowed: false,
    effect_or_usability_write_allowed: false,
    private_to_requester_account: true,
    append_only: true,
    material_intake_open: false,
    file_upload_allowed: false,
    url_submission_allowed: false,
    free_text_submission_allowed: false,
    read_only: true,
  };
  fixture.bindings.lab.relation_effect_evidence_request_receipt_ref =
    requestReceipt.receipt_ref;
  fixture.bindings.lab.relation_effect_evidence_request_receipt_hash =
    requestReceipt.receipt_hash;
  fixture.requestReceipt = requestReceipt;
  return fixture;
}

export function buildEmptyRelationEffectEvidenceRequestFixture() {
  return buildRelationEffectEvidencePacketFixture();
}

export function buildClearRelationEffectEvidenceRequestFixture() {
  return makeNotTriggeredEvidencePacketFixture();
}
