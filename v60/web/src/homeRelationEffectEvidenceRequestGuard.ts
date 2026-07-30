import {
  arraysEqual,
  hasOnlyKeys,
  isHash,
  isRecord,
  isRef,
} from "./homeRelationEffectAdmissionValidation";
import type {
  HomeRelationEffectEvidenceDemandPacket,
  HomeRelationEffectEvidenceDimensionSlot,
} from "./homeRelationEffectEvidencePacketTypes";
import {
  RELATION_EFFECT_EVIDENCE_REQUEST_RECEIPT_VERSION,
  RELATION_EFFECT_EVIDENCE_REQUEST_VERSION,
  type HomeRelationEffectEvidenceRequestBindings,
  type HomeRelationEffectEvidenceRequestReceipt,
} from "./homeRelationEffectEvidenceRequestTypes";

const RECEIPT_KEYS = [
  "receipt_ref",
  "receipt_hash",
  "receipt_version",
  "request_version",
  "requester_account_ref",
  "idempotency_key",
  "case_ref",
  "chart_version_ref",
  "reading_ref",
  "reading_hash",
  "frontier_ref",
  "frontier_hash",
  "admission_review_ref",
  "admission_review_hash",
  "policy_ref",
  "policy_hash",
  "proposal_ref",
  "proposal_hash",
  "packet_ref",
  "packet_hash",
  "request_items",
  "request_item_count",
  "requested_dimension_slot_count",
  "ready_dimension_slot_count",
  "professional_material_count",
  "professional_evidence_count",
  "status",
  "semantics",
  "evidence_role",
  "effect_decision_status",
  "effect_status",
  "usability_status",
  "llm_allowed",
  "provider_invoked",
  "reasoner_invoked",
  "owner_professional_review_invoked",
  "knowledge_admission_eligible",
  "knowledge_write_allowed",
  "gate_invoked",
  "decision_request_created",
  "decision_created",
  "professional_verdict_allowed",
  "probability_claim_allowed",
  "effect_or_usability_write_allowed",
  "private_to_requester_account",
  "append_only",
  "material_intake_open",
  "file_upload_allowed",
  "url_submission_allowed",
  "free_text_submission_allowed",
  "read_only",
] as const;

const REQUEST_ITEM_KEYS = [
  "request_item_ref",
  "demand_packet_ref",
  "demand_packet_hash",
  "assessment_ref",
  "assessment_hash",
  "demand_ref",
  "dimension_slots",
  "requested_dimension_slot_count",
] as const;

const REQUESTED_SLOT_KEYS = [
  "slot_ref",
  "dimension_id",
  "requirement",
  "requested_artifact_kinds",
  "next_action",
  "status",
  "professional_material_count",
  "professional_evidence_count",
  "ready",
] as const;

export function isRelationEffectEvidenceRequestStateDisplayable(
  candidate: unknown,
  bindings: HomeRelationEffectEvidenceRequestBindings,
): candidate is HomeRelationEffectEvidenceRequestReceipt | null {
  if (candidate === null) {
    const triggeredPacketIsSafe =
      bindings.packet.status === "EVIDENCE_INTAKE_REQUIRED" &&
      bindings.packet.effect_decision_status === "WITHHELD" &&
      bindings.packet.demand_packets.length > 0 &&
      bindings.packet.demand_packet_count ===
        bindings.packet.demand_packets.length &&
      bindings.packet.ready_dimension_slot_count === 0 &&
      bindings.packet.professional_evidence_count === 0;
    const clearPacketIsSafe =
      bindings.packet.status === "NOT_TRIGGERED" &&
      bindings.packet.effect_decision_status === "NOT_TRIGGERED" &&
      bindings.packet.demand_packets.length === 0 &&
      bindings.packet.demand_packet_count === 0 &&
      bindings.packet.required_dimension_slot_count === 0 &&
      bindings.packet.ready_dimension_slot_count === 0 &&
      bindings.packet.professional_evidence_count === 0;
    return (
      (triggeredPacketIsSafe || clearPacketIsSafe) &&
      bindings.lab.relation_effect_evidence_request_receipt_ref === null &&
      bindings.lab.relation_effect_evidence_request_receipt_hash === null
    );
  }
  return isRelationEffectEvidenceRequestReceiptDisplayable(
    candidate,
    bindings,
  );
}

export function isRelationEffectEvidenceRequestReceiptDisplayable(
  candidate: unknown,
  { lab, packet }: HomeRelationEffectEvidenceRequestBindings,
): candidate is HomeRelationEffectEvidenceRequestReceipt {
  if (
    packet.status !== "EVIDENCE_INTAKE_REQUIRED" ||
    !isRecord(candidate) ||
    !hasOnlyKeys(candidate, RECEIPT_KEYS) ||
    candidate.receipt_version !==
      RELATION_EFFECT_EVIDENCE_REQUEST_RECEIPT_VERSION ||
    candidate.request_version !== RELATION_EFFECT_EVIDENCE_REQUEST_VERSION ||
    !isRef(candidate.receipt_ref) ||
    !isHash(candidate.receipt_hash) ||
    !isRef(candidate.requester_account_ref) ||
    !isIdempotencyKey(candidate.idempotency_key) ||
    !isHash(candidate.reading_hash) ||
    !isHash(candidate.frontier_hash) ||
    !isHash(candidate.admission_review_hash) ||
    !isHash(candidate.policy_hash) ||
    !isHash(candidate.proposal_hash) ||
    !isHash(candidate.packet_hash)
  ) {
    return false;
  }
  if (
    candidate.case_ref !== packet.case_ref ||
    candidate.chart_version_ref !== packet.chart_version_ref ||
    candidate.reading_ref !== packet.reading_ref ||
    candidate.reading_hash !== packet.reading_hash ||
    candidate.frontier_ref !== packet.frontier_ref ||
    candidate.frontier_hash !== packet.frontier_hash ||
    candidate.admission_review_ref !== packet.admission_review_ref ||
    candidate.admission_review_hash !== packet.admission_review_hash ||
    candidate.policy_ref !== packet.policy_ref ||
    candidate.policy_hash !== packet.policy_hash ||
    candidate.proposal_ref !== packet.proposal_ref ||
    candidate.proposal_hash !== packet.proposal_hash ||
    candidate.packet_ref !== packet.packet_ref ||
    candidate.packet_hash !== packet.packet_hash ||
    candidate.receipt_ref !==
      lab.relation_effect_evidence_request_receipt_ref ||
    candidate.receipt_hash !==
      lab.relation_effect_evidence_request_receipt_hash
  ) {
    return false;
  }
  if (
    candidate.status !== "REQUEST_RECORDED_NOT_EVIDENCE" ||
    candidate.semantics !==
      "PREPARATION_REQUEST_NOT_PROFESSIONAL_EVIDENCE" ||
    candidate.evidence_role !== "NOT_EVIDENCE" ||
    candidate.effect_decision_status !== "WITHHELD" ||
    candidate.effect_status !== "UNRESOLVED" ||
    candidate.usability_status !== "UNRESOLVED" ||
    candidate.ready_dimension_slot_count !== 0 ||
    candidate.professional_material_count !== 0 ||
    candidate.professional_evidence_count !== 0 ||
    candidate.llm_allowed !== false ||
    candidate.provider_invoked !== false ||
    candidate.reasoner_invoked !== false ||
    candidate.owner_professional_review_invoked !== false ||
    candidate.knowledge_admission_eligible !== false ||
    candidate.knowledge_write_allowed !== false ||
    candidate.gate_invoked !== false ||
    candidate.decision_request_created !== false ||
    candidate.decision_created !== false ||
    candidate.professional_verdict_allowed !== false ||
    candidate.probability_claim_allowed !== false ||
    candidate.effect_or_usability_write_allowed !== false ||
    candidate.private_to_requester_account !== true ||
    candidate.append_only !== true ||
    candidate.material_intake_open !== false ||
    candidate.file_upload_allowed !== false ||
    candidate.url_submission_allowed !== false ||
    candidate.free_text_submission_allowed !== false ||
    candidate.read_only !== true
  ) {
    return false;
  }
  if (
    !Array.isArray(candidate.request_items) ||
    candidate.request_item_count !== candidate.request_items.length ||
    candidate.request_items.length !== packet.demand_packets.length ||
    candidate.requested_dimension_slot_count !==
      packet.required_dimension_slot_count
  ) {
    return false;
  }
  const itemRefs = candidate.request_items.map((item) =>
    isRecord(item) ? item.request_item_ref : null,
  );
  return (
    itemRefs.every(isRef) &&
    new Set(itemRefs).size === itemRefs.length &&
    candidate.request_items.every((item) =>
      isRequestItemSafe(
        item,
        isRecord(item)
          ? packet.demand_packets.find(
              (demand) =>
                demand.demand_packet_ref === item.demand_packet_ref,
            )
          : undefined,
      ),
    )
  );
}

function isRequestItemSafe(
  candidate: unknown,
  demandPacket: HomeRelationEffectEvidenceDemandPacket | undefined,
): boolean {
  if (
    !demandPacket ||
    !isRecord(candidate) ||
    !hasOnlyKeys(candidate, REQUEST_ITEM_KEYS) ||
    !isRef(candidate.request_item_ref) ||
    candidate.demand_packet_ref !== demandPacket.demand_packet_ref ||
    candidate.demand_packet_hash !== demandPacket.demand_packet_hash ||
    candidate.assessment_ref !== demandPacket.assessment_ref ||
    candidate.assessment_hash !== demandPacket.assessment_hash ||
    candidate.demand_ref !== demandPacket.demand_ref ||
    !Array.isArray(candidate.dimension_slots) ||
    candidate.requested_dimension_slot_count !==
      demandPacket.required_dimension_slot_count ||
    candidate.dimension_slots.length !==
      demandPacket.dimension_slots.length
  ) {
    return false;
  }
  return candidate.dimension_slots.every((slot, index) =>
    isRequestedSlotSafe(slot, demandPacket.dimension_slots[index]),
  );
}

function isRequestedSlotSafe(
  candidate: unknown,
  packetSlot: HomeRelationEffectEvidenceDimensionSlot | undefined,
): boolean {
  return (
    !!packetSlot &&
    isRecord(candidate) &&
    hasOnlyKeys(candidate, REQUESTED_SLOT_KEYS) &&
    candidate.slot_ref === packetSlot.slot_ref &&
    candidate.dimension_id === packetSlot.dimension_id &&
    candidate.requirement === packetSlot.requirement &&
    arraysEqual(
      candidate.requested_artifact_kinds,
      packetSlot.requested_artifact_kinds,
    ) &&
    candidate.next_action === packetSlot.next_action &&
    candidate.status === "REQUESTED_NOT_EVIDENCE" &&
    candidate.professional_material_count === 0 &&
    candidate.professional_evidence_count === 0 &&
    candidate.ready === false
  );
}

function isIdempotencyKey(value: unknown): value is string {
  return (
    typeof value === "string" &&
    value.length >= 1 &&
    value.length <= 180
  );
}
