import {
  RELATION_EFFECT_ADMISSION_DIMENSIONS,
  RELATION_EFFECT_BLOCKED_CLAIMS,
  RELATION_EFFECT_INTERPRETATIONS,
  RELATION_EFFECT_REJECTION_CODES,
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

const ASSESSMENT_KEYS = [
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
  "proposal_claim",
  "interpretations",
  "dimension_assessments",
  "disposition",
  "candidate_truth_status",
  "rejection_codes",
  "blocked_claims",
  "admitted_effect_atom_refs",
  "effect_status",
  "usability_status",
] as const;

const INTERPRETATION_KEYS = [
  "interpretation_ref",
  "interpretation_id",
  "summary",
  "status",
  "selected",
  "effect_atom_created",
] as const;

const DIMENSION_KEYS = [
  "dimension_id",
  "submission_status",
  "current_basis_refs",
  "gap",
  "satisfied",
] as const;

const PILLAR_SLOTS = ["year", "month", "day", "hour"] as const;
const SUBMISSION_STATUSES = [
  "VERIFIED",
  "PARTIAL",
  "COMPETING",
  "UNSUPPORTED",
  "MISSING",
] as const;

export function isRelationEffectAdmissionAssessmentSafe(
  candidate: unknown,
  review: Record<string, unknown>,
  demand: Record<string, unknown> | undefined,
): candidate is HomeRelationEffectRuleAdmissionAssessment {
  if (
    !isRecord(candidate) ||
    !hasOnlyKeys(candidate, ASSESSMENT_KEYS) ||
    !demand ||
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
    candidate.policy_ref !== review.policy_ref ||
    candidate.policy_hash !== review.policy_hash ||
    candidate.proposal_ref !== review.proposal_ref ||
    candidate.proposal_hash !== review.proposal_hash ||
    typeof candidate.proposal_claim !== "string" ||
    candidate.proposal_claim.length === 0 ||
    candidate.disposition !== "REJECTED_PRE_ADMISSION" ||
    candidate.candidate_truth_status !==
      "NOT_EVALUATED_AS_TRUE_OR_FALSE" ||
    !arraysEqual(candidate.rejection_codes, RELATION_EFFECT_REJECTION_CODES) ||
    !arraysEqual(candidate.blocked_claims, RELATION_EFFECT_BLOCKED_CLAIMS) ||
    !Array.isArray(candidate.admitted_effect_atom_refs) ||
    candidate.admitted_effect_atom_refs.length !== 0 ||
    candidate.effect_status !== "UNRESOLVED" ||
    candidate.usability_status !== "UNRESOLVED"
  ) {
    return false;
  }
  if (
    demand.dependency_status !== "SCOPE_INVARIANT_RULE_DEMAND" ||
    demand.source_match_kind !== "EXACT_IDENTITY" ||
    demand.relation_type !== "six_clash_membership" ||
    candidate.demand_ref !== demand.demand_ref ||
    candidate.source_review_ref !== demand.source_review_ref ||
    candidate.source_evidence_ref !== demand.source_evidence_ref ||
    candidate.intersection_ref !== demand.intersection_ref ||
    candidate.relation_fact_ref !== demand.relation_fact_ref ||
    candidate.carrier_ref !== demand.carrier_ref ||
    candidate.visible_slot !== demand.visible_slot ||
    candidate.visible_stem !== demand.visible_stem ||
    demand.source_branch !== "午" ||
    demand.peer_branch !== "子" ||
    candidate.source_slot !== demand.source_slot ||
    candidate.peer_slot !== demand.peer_slot
  ) {
    return false;
  }
  return (
    isInterpretationSetSafe(candidate.interpretations) &&
    isDimensionSetSafe(candidate.dimension_assessments)
  );
}

function isInterpretationSetSafe(candidate: unknown): boolean {
  return (
    Array.isArray(candidate) &&
    candidate.length === RELATION_EFFECT_INTERPRETATIONS.length &&
    new Set(
      candidate.map((item) =>
        isRecord(item) ? item.interpretation_ref : null,
      ),
    ).size === candidate.length &&
    candidate.every((item, index) => {
      if (!isRecord(item) || !hasOnlyKeys(item, INTERPRETATION_KEYS)) {
        return false;
      }
      return (
        isRef(item.interpretation_ref) &&
        item.interpretation_id === RELATION_EFFECT_INTERPRETATIONS[index] &&
        typeof item.summary === "string" &&
        item.summary.length > 0 &&
        item.status === "HELD" &&
        item.selected === false &&
        item.effect_atom_created === false
      );
    })
  );
}

function isDimensionSetSafe(candidate: unknown): boolean {
  return (
    Array.isArray(candidate) &&
    candidate.length === RELATION_EFFECT_ADMISSION_DIMENSIONS.length &&
    candidate.every((item, index) => {
      if (!isRecord(item) || !hasOnlyKeys(item, DIMENSION_KEYS)) {
        return false;
      }
      return (
        item.dimension_id === RELATION_EFFECT_ADMISSION_DIMENSIONS[index] &&
        isOneOf(item.submission_status, SUBMISSION_STATUSES) &&
        isUniqueRefArray(item.current_basis_refs) &&
        typeof item.gap === "string" &&
        item.gap.length > 0 &&
        item.satisfied === false
      );
    })
  );
}
