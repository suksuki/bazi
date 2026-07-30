import { isRelationEffectAdmissionReviewDisplayable } from "./homeRelationEffectAdmissionGuard";
import {
  arraysEqual,
  hasOnlyKeys,
  isHash,
  isRecord,
  isRef,
} from "./homeRelationEffectAdmissionValidation";
import { isRelationEffectEvidenceDemandPacketSafe } from "./homeRelationEffectEvidenceDemandGuard";
import {
  RELATION_EFFECT_EVIDENCE_DECISION_PATH,
  RELATION_EFFECT_EVIDENCE_PACKET_VERSION,
  RELATION_EFFECT_REQUIRED_PROFESSIONAL_PATH,
  type HomeRelationEffectEvidencePacketBindings,
  type HomeRelationEffectEvidencePacketEnvelope,
} from "./homeRelationEffectEvidencePacketTypes";

const PACKET_KEYS = [
  "packet_ref",
  "packet_hash",
  "packet_version",
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
  "demand_packets",
  "demand_packet_count",
  "required_dimension_slot_count",
  "ready_dimension_slot_count",
  "professional_evidence_count",
  "status",
  "projection_semantics",
  "decision_path_semantics",
  "decision_path",
  "required_professional_path_semantics",
  "required_professional_path",
  "effect_decision_status",
  "effect_status",
  "usability_status",
  "knowledge_admission_eligible",
  "llm_allowed",
  "provider_invoked",
  "reasoner_invoked",
  "decision_request_created",
  "owner_professional_review_invoked",
  "knowledge_promotion_request_created",
  "gate_invoked",
  "ledger_invoked",
  "decision_created",
  "selection_authority",
  "professional_verdict_allowed",
  "probability_claim_allowed",
  "canonical_write_allowed",
  "read_only",
] as const;

export function isRelationEffectEvidencePacketDisplayable(
  candidate: unknown,
  bindings: HomeRelationEffectEvidencePacketBindings,
): candidate is HomeRelationEffectEvidencePacketEnvelope {
  if (
    !isRecord(candidate) ||
    !hasOnlyKeys(candidate, PACKET_KEYS) ||
    !isRelationEffectAdmissionReviewDisplayable(bindings.review, {
      frontier: bindings.frontier,
      reading: bindings.reading,
      lab: bindings.lab,
    }) ||
    candidate.packet_version !== RELATION_EFFECT_EVIDENCE_PACKET_VERSION ||
    !isRef(candidate.packet_ref) ||
    !isHash(candidate.packet_hash) ||
    !isRef(candidate.case_ref) ||
    !isRef(candidate.chart_version_ref) ||
    !isRef(candidate.reading_ref) ||
    !isHash(candidate.reading_hash) ||
    !isRef(candidate.frontier_ref) ||
    !isHash(candidate.frontier_hash) ||
    !isRef(candidate.admission_review_ref) ||
    !isHash(candidate.admission_review_hash) ||
    !isRef(candidate.policy_ref) ||
    !isHash(candidate.policy_hash) ||
    !isRef(candidate.proposal_ref) ||
    !isHash(candidate.proposal_hash)
  ) {
    return false;
  }
  if (
    candidate.projection_semantics !==
      "PROFESSIONAL_EVIDENCE_READINESS_NOT_DECISION" ||
    candidate.decision_path_semantics !==
      "READINESS_PATH_NOT_DECISION" ||
    candidate.required_professional_path_semantics !==
      "FUTURE_AUTHORITY_PATH_NOT_EXECUTED" ||
    !arraysEqual(
      candidate.required_professional_path,
      RELATION_EFFECT_REQUIRED_PROFESSIONAL_PATH,
    ) ||
    candidate.effect_status !== "UNRESOLVED" ||
    candidate.usability_status !== "UNRESOLVED" ||
    candidate.knowledge_admission_eligible !== false ||
    candidate.llm_allowed !== false ||
    candidate.provider_invoked !== false ||
    candidate.reasoner_invoked !== false ||
    candidate.decision_request_created !== false ||
    candidate.owner_professional_review_invoked !== false ||
    candidate.knowledge_promotion_request_created !== false ||
    candidate.gate_invoked !== false ||
    candidate.ledger_invoked !== false ||
    candidate.decision_created !== false ||
    candidate.selection_authority !== false ||
    candidate.professional_verdict_allowed !== false ||
    candidate.probability_claim_allowed !== false ||
    candidate.canonical_write_allowed !== false ||
    candidate.read_only !== true
  ) {
    return false;
  }
  if (!identitiesAreSafe(candidate, bindings)) {
    return false;
  }
  if (
    !Array.isArray(candidate.demand_packets) ||
    !Number.isInteger(candidate.demand_packet_count) ||
    !Number.isInteger(candidate.required_dimension_slot_count) ||
    candidate.demand_packet_count !== candidate.demand_packets.length ||
    candidate.required_dimension_slot_count !==
      candidate.demand_packets.length * 6 ||
    candidate.ready_dimension_slot_count !== 0 ||
    candidate.professional_evidence_count !== 0 ||
    candidate.demand_packets.length !== bindings.review.assessments.length
  ) {
    return false;
  }
  const assessmentRefs = candidate.demand_packets.map((item) =>
    isRecord(item) ? item.assessment_ref : null,
  );
  const expectedAssessmentRefs = bindings.review.assessments.map(
    (item) => item.assessment_ref,
  );
  if (
    !arraysEqual(assessmentRefs, expectedAssessmentRefs) ||
    !arraysEqual(
      assessmentRefs,
      [...assessmentRefs].sort((left, right) =>
        String(left).localeCompare(String(right)),
      ),
    )
  ) {
    return false;
  }
  if (
    candidate.demand_packets.some(
      (item, index) =>
        !isRelationEffectEvidenceDemandPacketSafe(
          item,
          bindings.review.assessments[index],
          candidate,
        ),
    )
  ) {
    return false;
  }
  const demandPacketRefs = candidate.demand_packets.map((item) =>
    isRecord(item) ? item.demand_packet_ref : null,
  );
  if (
    demandPacketRefs.some((ref) => !isRef(ref)) ||
    new Set(demandPacketRefs).size !== demandPacketRefs.length
  ) {
    return false;
  }
  return readinessStateIsSafe(candidate);
}

function identitiesAreSafe(
  packet: Record<string, unknown>,
  bindings: HomeRelationEffectEvidencePacketBindings,
): boolean {
  const { frontier, lab, reading, review } = bindings;
  return (
    packet.case_ref === reading.case_ref &&
    packet.case_ref === review.case_ref &&
    packet.case_ref === frontier.case_ref &&
    packet.chart_version_ref === reading.chart_version_ref &&
    packet.chart_version_ref === review.chart_version_ref &&
    packet.chart_version_ref === frontier.chart_version_ref &&
    packet.reading_ref === reading.reading_ref &&
    packet.reading_ref === review.reading_ref &&
    packet.reading_ref === frontier.reading_ref &&
    packet.reading_ref === lab.reading_ref &&
    packet.reading_hash === reading.reading_hash &&
    packet.reading_hash === review.reading_hash &&
    packet.reading_hash === frontier.reading_hash &&
    packet.reading_hash === lab.reading_hash &&
    packet.frontier_ref === frontier.frontier_ref &&
    packet.frontier_ref === review.frontier_ref &&
    packet.frontier_ref === lab.relation_effect_frontier_ref &&
    packet.frontier_hash === frontier.frontier_hash &&
    packet.frontier_hash === review.frontier_hash &&
    packet.frontier_hash === lab.relation_effect_frontier_hash &&
    packet.admission_review_ref === review.review_ref &&
    packet.admission_review_ref ===
      lab.relation_effect_admission_review_ref &&
    packet.admission_review_hash === review.review_hash &&
    packet.admission_review_hash ===
      lab.relation_effect_admission_review_hash &&
    packet.policy_ref === review.policy_ref &&
    packet.policy_hash === review.policy_hash &&
    packet.proposal_ref === review.proposal_ref &&
    packet.proposal_hash === review.proposal_hash &&
    packet.packet_ref === lab.relation_effect_evidence_packet_ref &&
    packet.packet_hash === lab.relation_effect_evidence_packet_hash &&
    reading.read_only === true
  );
}

function readinessStateIsSafe(packet: Record<string, unknown>): boolean {
  const triggered =
    Array.isArray(packet.demand_packets) &&
    packet.demand_packets.length > 0;
  return triggered
    ? packet.status === "EVIDENCE_INTAKE_REQUIRED" &&
        arraysEqual(
          packet.decision_path,
          RELATION_EFFECT_EVIDENCE_DECISION_PATH,
        ) &&
        packet.effect_decision_status === "WITHHELD"
    : packet.status === "NOT_TRIGGERED" &&
        arraysEqual(packet.decision_path, []) &&
        packet.effect_decision_status === "NOT_TRIGGERED";
}
