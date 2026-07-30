import {
  RELATION_EFFECT_ADMISSION_REVIEW_VERSION,
  type HomeRelationEffectAdmissionDisplayBindings,
  type HomeRelationEffectAdmissionReviewEnvelope,
} from "./homeRelationEffectAdmissionTypes";
import { isRelationEffectAdmissionAssessmentSafe } from "./homeRelationEffectAdmissionAssessmentGuard";
import {
  arraysEqual,
  hasOnlyKeys,
  isHash,
  isNonNegativeInteger,
  isOneOf,
  isRecord,
  isRef,
  isUniqueRefArray,
} from "./homeRelationEffectAdmissionValidation";

const REVIEW_KEYS = [
  "review_ref",
  "review_hash",
  "review_version",
  "case_ref",
  "chart_version_ref",
  "reading_ref",
  "reading_hash",
  "frontier_ref",
  "frontier_hash",
  "policy_ref",
  "policy_hash",
  "proposal_ref",
  "proposal_hash",
  "assessments",
  "reviewed_demand_count",
  "rejected_pre_admission_count",
  "admitted_effect_rule_count",
  "frontier_scope_invariant_demand_refs",
  "frontier_match_scope_demand_refs",
  "deferred_match_scope_demand_refs",
  "unreviewed_scope_invariant_demand_refs",
  "disposition",
  "review_semantics",
  "effect_status",
  "usability_status",
  "provider_invoked",
  "owner_professional_review_invoked",
  "knowledge_promotion_request_created",
  "gate_invoked",
  "decision_created",
  "selection_authority",
  "professional_verdict_allowed",
  "probability_claim_allowed",
  "canonical_write_allowed",
  "read_only",
] as const;

export function isRelationEffectAdmissionReviewDisplayable(
  candidate: unknown,
  bindings: HomeRelationEffectAdmissionDisplayBindings,
): candidate is HomeRelationEffectAdmissionReviewEnvelope {
  if (!isRecord(candidate) || !hasOnlyKeys(candidate, REVIEW_KEYS)) {
    return false;
  }
  const frontier = bindings.frontier as unknown;
  const reading = bindings.reading as unknown;
  const lab = bindings.lab as unknown;
  if (!isRecord(frontier) || !isRecord(reading) || !isRecord(lab)) {
    return false;
  }
  if (
    candidate.review_version !== RELATION_EFFECT_ADMISSION_REVIEW_VERSION ||
    !isRef(candidate.review_ref) ||
    !isHash(candidate.review_hash) ||
    !isRef(candidate.case_ref) ||
    !isRef(candidate.chart_version_ref) ||
    !isRef(candidate.reading_ref) ||
    !isHash(candidate.reading_hash) ||
    !isRef(candidate.frontier_ref) ||
    !isHash(candidate.frontier_hash) ||
    !isRef(candidate.policy_ref) ||
    !isHash(candidate.policy_hash) ||
    !isRef(candidate.proposal_ref) ||
    !isHash(candidate.proposal_hash)
  ) {
    return false;
  }
  if (
    candidate.review_semantics !==
      "SHORTCUT_ADMISSION_REJECTION_NOT_EFFECT_NEGATION" ||
    candidate.effect_status !== "UNRESOLVED" ||
    candidate.usability_status !== "UNRESOLVED" ||
    candidate.provider_invoked !== false ||
    candidate.owner_professional_review_invoked !== false ||
    candidate.knowledge_promotion_request_created !== false ||
    candidate.gate_invoked !== false ||
    candidate.decision_created !== false ||
    candidate.selection_authority !== false ||
    candidate.professional_verdict_allowed !== false ||
    candidate.probability_claim_allowed !== false ||
    candidate.canonical_write_allowed !== false ||
    candidate.read_only !== true
  ) {
    return false;
  }
  if (!frontierAndReadingBindingsAreSafe(candidate, frontier, reading, lab)) {
    return false;
  }
  if (
    !Array.isArray(candidate.assessments) ||
    !isNonNegativeInteger(candidate.reviewed_demand_count) ||
    !isNonNegativeInteger(candidate.rejected_pre_admission_count) ||
    candidate.admitted_effect_rule_count !== 0 ||
    candidate.reviewed_demand_count !== candidate.assessments.length ||
    candidate.rejected_pre_admission_count !== candidate.assessments.length ||
    !isUniqueRefArray(candidate.frontier_scope_invariant_demand_refs) ||
    !isUniqueRefArray(candidate.frontier_match_scope_demand_refs) ||
    !isUniqueRefArray(candidate.deferred_match_scope_demand_refs) ||
    !isUniqueRefArray(candidate.unreviewed_scope_invariant_demand_refs)
  ) {
    return false;
  }
  const expectedDisposition =
    candidate.assessments.length > 0
      ? "REJECTED_PRE_ADMISSION"
      : "NOT_TRIGGERED";
  if (candidate.disposition !== expectedDisposition) {
    return false;
  }
  const assessmentRefs = candidate.assessments.map((item) =>
    isRecord(item) ? item.assessment_ref : null,
  );
  if (
    assessmentRefs.some((ref) => !isRef(ref)) ||
    !arraysEqual(
      assessmentRefs,
      [...assessmentRefs].sort((left, right) =>
        String(left).localeCompare(String(right)),
      ),
    ) ||
    new Set(assessmentRefs).size !== assessmentRefs.length
  ) {
    return false;
  }

  const demands = Array.isArray(frontier.demands)
    ? frontier.demands
    : null;
  if (
    !demands ||
    demands.some(
      (item) =>
        !isRecord(item) ||
        !isRef(item.demand_ref) ||
        !isOneOf(item.dependency_status, [
          "SCOPE_INVARIANT_RULE_DEMAND",
          "MATCH_SCOPE_RULE_FIRST",
        ]),
    )
  ) {
    return false;
  }
  const demandsByRef = new Map(
    demands.map((item) => [String(item.demand_ref), item]),
  );
  const frontierScopeInvariantRefs = demands
    .filter((item) => item.dependency_status === "SCOPE_INVARIANT_RULE_DEMAND")
    .map((item) => String(item.demand_ref));
  const frontierMatchScopeRefs = demands
    .filter((item) => item.dependency_status === "MATCH_SCOPE_RULE_FIRST")
    .map((item) => String(item.demand_ref));
  if (
    demandsByRef.size !== demands.length ||
    frontier.demand_count !== demands.length ||
    frontier.scope_invariant_rule_demand_count !==
      frontierScopeInvariantRefs.length ||
    frontier.match_scope_rule_first_count !== frontierMatchScopeRefs.length ||
    !arraysEqual(
      candidate.frontier_scope_invariant_demand_refs,
      frontierScopeInvariantRefs,
    ) ||
    !arraysEqual(
      candidate.frontier_match_scope_demand_refs,
      frontierMatchScopeRefs,
    ) ||
    candidate.assessments.some(
      (assessment) =>
        !isRelationEffectAdmissionAssessmentSafe(
          assessment,
          candidate,
          demandsByRef.get(
            isRecord(assessment) ? String(assessment.demand_ref) : "",
          ),
        ),
    )
  ) {
    return false;
  }
  const assessedDemandRefs = new Set(
    candidate.assessments.map((assessment) => assessment.demand_ref),
  );
  const expectedDeferredRefs = demands
    .filter((demand) => demand.dependency_status === "MATCH_SCOPE_RULE_FIRST")
    .map((demand) => String(demand.demand_ref));
  const expectedUnreviewedRefs = demands
    .filter(
      (demand) =>
        demand.dependency_status === "SCOPE_INVARIANT_RULE_DEMAND" &&
        !assessedDemandRefs.has(String(demand.demand_ref)),
    )
    .map((demand) => String(demand.demand_ref));
  const deferredRefs =
    candidate.deferred_match_scope_demand_refs as string[];
  const unreviewedRefs =
    candidate.unreviewed_scope_invariant_demand_refs as string[];
  const classifiedDemandRefs = [
    ...assessedDemandRefs,
    ...deferredRefs,
    ...unreviewedRefs,
  ];
  return (
    classifiedDemandRefs.length === demands.length &&
    new Set(classifiedDemandRefs).size === classifiedDemandRefs.length &&
    frontierScopeInvariantRefs.every((ref) =>
      assessedDemandRefs.has(ref) ||
      unreviewedRefs.includes(ref)
    ) &&
    frontierMatchScopeRefs.every((ref) =>
      deferredRefs.includes(ref)
    ) &&
    arraysEqual(
      deferredRefs,
      expectedDeferredRefs,
    ) &&
    arraysEqual(
      unreviewedRefs,
      expectedUnreviewedRefs,
    )
  );
}

function frontierAndReadingBindingsAreSafe(
  review: Record<string, unknown>,
  frontier: Record<string, unknown>,
  reading: Record<string, unknown>,
  lab: Record<string, unknown>,
): boolean {
  return (
    review.case_ref === frontier.case_ref &&
    review.case_ref === reading.case_ref &&
    review.chart_version_ref === frontier.chart_version_ref &&
    review.chart_version_ref === reading.chart_version_ref &&
    review.reading_ref === frontier.reading_ref &&
    review.reading_ref === reading.reading_ref &&
    review.reading_ref === lab.reading_ref &&
    review.reading_hash === frontier.reading_hash &&
    review.reading_hash === reading.reading_hash &&
    review.reading_hash === lab.reading_hash &&
    review.frontier_ref === frontier.frontier_ref &&
    review.frontier_ref === lab.relation_effect_frontier_ref &&
    review.frontier_hash === frontier.frontier_hash &&
    review.frontier_hash === lab.relation_effect_frontier_hash &&
    review.review_ref === lab.relation_effect_admission_review_ref &&
    review.review_hash === lab.relation_effect_admission_review_hash &&
    reading.read_only === true &&
    frontier.frontier_version ===
      "v60.mingli-relation-effect-research-frontier.001" &&
    frontier.research_semantics ===
      "MEMBERSHIP_DEPENDENCY_AND_RULE_GAPS_ONLY" &&
    frontier.source_discussion_disposition === "ABSTAIN" &&
    frontier.effect_status === "UNRESOLVED" &&
    frontier.usability_status === "UNRESOLVED" &&
    frontier.admitted_effect_rule_count === 0 &&
    frontier.provider_invoked === false &&
    frontier.decision_created === false &&
    frontier.gate_invoked === false &&
    frontier.selection_authority === false &&
    frontier.professional_verdict_allowed === false &&
    frontier.probability_claim_allowed === false &&
    frontier.canonical_write_allowed === false &&
    frontier.read_only === true
  );
}
