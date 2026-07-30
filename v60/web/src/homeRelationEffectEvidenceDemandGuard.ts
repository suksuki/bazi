import {
  RELATION_EFFECT_ADMISSION_DIMENSIONS,
  type HomeRelationEffectRuleAdmissionAssessment,
} from "./homeRelationEffectAdmissionTypes";
import {
  arraysEqual,
  hasOnlyKeys,
  isHash,
  isOneOf,
  isRecord,
  isRef,
  isUniqueRefArray,
} from "./homeRelationEffectAdmissionValidation";
import {
  RELATION_EFFECT_EVIDENCE_NEXT_ACTIONS,
  RELATION_EFFECT_EVIDENCE_REQUESTED_ARTIFACTS,
  RELATION_EFFECT_EVIDENCE_REQUIREMENTS,
  type HomeRelationEffectEvidenceDemandPacket,
} from "./homeRelationEffectEvidencePacketTypes";

const DEMAND_PACKET_KEYS = [
  "demand_packet_ref",
  "demand_packet_hash",
  "assessment_ref",
  "assessment_hash",
  "demand_ref",
  "source_review_ref",
  "source_evidence_ref",
  "intersection_ref",
  "relation_fact_ref",
  "carrier_ref",
  "visible_slot",
  "visible_stem",
  "source_slot",
  "source_branch",
  "peer_slot",
  "peer_branch",
  "relation_type",
  "source_match_kind",
  "policy_ref",
  "policy_hash",
  "proposal_ref",
  "proposal_hash",
  "dimension_slots",
  "required_dimension_slot_count",
  "ready_dimension_slot_count",
  "professional_evidence_count",
  "status",
  "effect_status",
  "usability_status",
] as const;

const DIMENSION_SLOT_KEYS = [
  "slot_ref",
  "dimension_id",
  "proposal_submission_status",
  "current_basis_refs",
  "current_basis_status",
  "requirement",
  "requested_artifact_kinds",
  "guidance_semantics",
  "professional_evidence_refs",
  "professional_evidence_count",
  "slot_status",
  "next_action",
  "ready",
] as const;

const PILLAR_SLOTS = ["year", "month", "day", "hour"] as const;
const SUBMISSION_STATUSES = [
  "VERIFIED",
  "PARTIAL",
  "COMPETING",
  "UNSUPPORTED",
  "MISSING",
] as const;

export function isRelationEffectEvidenceDemandPacketSafe(
  candidate: unknown,
  assessment: HomeRelationEffectRuleAdmissionAssessment | undefined,
  packet: Record<string, unknown>,
): candidate is HomeRelationEffectEvidenceDemandPacket {
  if (
    !isRecord(candidate) ||
    !hasOnlyKeys(candidate, DEMAND_PACKET_KEYS) ||
    !assessment ||
    !isRef(candidate.demand_packet_ref) ||
    !isHash(candidate.demand_packet_hash) ||
    !isRef(candidate.assessment_ref) ||
    !isHash(candidate.assessment_hash) ||
    !isRef(candidate.demand_ref) ||
    !isRef(candidate.source_review_ref) ||
    !isRef(candidate.source_evidence_ref) ||
    !isRef(candidate.intersection_ref) ||
    !isRef(candidate.relation_fact_ref) ||
    !isRef(candidate.carrier_ref) ||
    !isOneOf(candidate.visible_slot, PILLAR_SLOTS) ||
    typeof candidate.visible_stem !== "string" ||
    candidate.visible_stem.length !== 1 ||
    !isOneOf(candidate.source_slot, PILLAR_SLOTS) ||
    candidate.source_branch !== "午" ||
    !isOneOf(candidate.peer_slot, PILLAR_SLOTS) ||
    candidate.peer_branch !== "子" ||
    candidate.relation_type !== "six_clash_membership" ||
    candidate.source_match_kind !== "EXACT_IDENTITY" ||
    candidate.policy_ref !== packet.policy_ref ||
    candidate.policy_hash !== packet.policy_hash ||
    candidate.proposal_ref !== packet.proposal_ref ||
    candidate.proposal_hash !== packet.proposal_hash ||
    candidate.required_dimension_slot_count !== 6 ||
    candidate.ready_dimension_slot_count !== 0 ||
    candidate.professional_evidence_count !== 0 ||
    candidate.status !== "EVIDENCE_INTAKE_REQUIRED" ||
    candidate.effect_status !== "UNRESOLVED" ||
    candidate.usability_status !== "UNRESOLVED"
  ) {
    return false;
  }
  if (
    candidate.assessment_ref !== assessment.assessment_ref ||
    candidate.assessment_hash !== assessment.assessment_hash ||
    candidate.demand_ref !== assessment.demand_ref ||
    candidate.source_review_ref !== assessment.source_review_ref ||
    candidate.source_evidence_ref !== assessment.source_evidence_ref ||
    candidate.intersection_ref !== assessment.intersection_ref ||
    candidate.relation_fact_ref !== assessment.relation_fact_ref ||
    candidate.carrier_ref !== assessment.carrier_ref ||
    candidate.visible_slot !== assessment.visible_slot ||
    candidate.visible_stem !== assessment.visible_stem ||
    candidate.source_slot !== assessment.source_slot ||
    candidate.source_branch !== assessment.source_branch ||
    candidate.peer_slot !== assessment.peer_slot ||
    candidate.peer_branch !== assessment.peer_branch ||
    candidate.relation_type !== assessment.relation_type ||
    candidate.source_match_kind !== assessment.source_match_kind ||
    candidate.policy_ref !== assessment.policy_ref ||
    candidate.policy_hash !== assessment.policy_hash ||
    candidate.proposal_ref !== assessment.proposal_ref ||
    candidate.proposal_hash !== assessment.proposal_hash
  ) {
    return false;
  }
  if (
    !Array.isArray(candidate.dimension_slots) ||
    candidate.dimension_slots.length !==
      RELATION_EFFECT_ADMISSION_DIMENSIONS.length
  ) {
    return false;
  }
  const slotRefs = candidate.dimension_slots.map((slot) =>
    isRecord(slot) ? slot.slot_ref : null,
  );
  return (
    slotRefs.every(isRef) &&
    new Set(slotRefs).size === slotRefs.length &&
    candidate.dimension_slots.every((slot, index) =>
      isEvidenceDimensionSlotSafe(
        slot,
        assessment.dimension_assessments[index],
        index,
      ),
    )
  );
}

function isEvidenceDimensionSlotSafe(
  candidate: unknown,
  assessmentDimension: unknown,
  index: number,
): boolean {
  if (
    !isRecord(candidate) ||
    !hasOnlyKeys(candidate, DIMENSION_SLOT_KEYS) ||
    !isRecord(assessmentDimension) ||
    !isRef(candidate.slot_ref) ||
    candidate.dimension_id !== RELATION_EFFECT_ADMISSION_DIMENSIONS[index] ||
    candidate.dimension_id !== assessmentDimension.dimension_id ||
    !isOneOf(candidate.proposal_submission_status, SUBMISSION_STATUSES) ||
    candidate.proposal_submission_status !==
      assessmentDimension.submission_status ||
    !isUniqueRefArray(candidate.current_basis_refs) ||
    !arraysEqual(
      candidate.current_basis_refs,
      Array.isArray(assessmentDimension.current_basis_refs)
        ? assessmentDimension.current_basis_refs
        : [],
    ) ||
    candidate.current_basis_status !==
      "RUNTIME_CONTEXT_ONLY_NOT_PROFESSIONAL_EVIDENCE" ||
    candidate.guidance_semantics !==
      "REQUEST_GUIDANCE_NOT_KNOWLEDGE_ADMISSION" ||
    !Array.isArray(candidate.professional_evidence_refs) ||
    candidate.professional_evidence_refs.length !== 0 ||
    candidate.professional_evidence_count !== 0 ||
    candidate.slot_status !==
      "BLOCKED_MISSING_PROFESSIONAL_EVIDENCE" ||
    candidate.ready !== false
  ) {
    return false;
  }
  const dimension = RELATION_EFFECT_ADMISSION_DIMENSIONS[index];
  return (
    candidate.requirement ===
      RELATION_EFFECT_EVIDENCE_REQUIREMENTS[dimension] &&
    arraysEqual(
      candidate.requested_artifact_kinds,
      RELATION_EFFECT_EVIDENCE_REQUESTED_ARTIFACTS[dimension],
    ) &&
    candidate.next_action ===
      RELATION_EFFECT_EVIDENCE_NEXT_ACTIONS[dimension]
  );
}
