const dimensions = [
  "APPLICABILITY_CONTEXT",
  "EFFECT_DIRECTION",
  "COMPLETION_CONDITIONS",
  "BLOCKING_CONDITIONS",
  "COUNTER_EVIDENCE",
  "PROFESSIONAL_PROVENANCE",
];

const dimensionStatuses = [
  "PARTIAL",
  "COMPETING",
  "MISSING",
  "MISSING",
  "MISSING",
  "MISSING",
];

const dimensionGaps = [
  "仍缺支关系向藏干及明干载体传播的适用谓词。",
  "扰动、打开或暴露、损伤或移除仍是竞争解释。",
  "成员关系出现不等于作用完成；没有完成条件。",
  "没有精确到该作用原子的阻断谓词。",
  "没有逐项对应本候选规则的反例证据类型。",
  "没有命题级来源清单及专业审阅回执。",
];

const interpretations = [
  [
    "RELATION_MEMBERSHIP_DISTURBANCE_ONLY",
    "只确认子午属于六冲成员，不把成员关系自动传播成午中己的作用。",
  ],
  [
    "SOURCE_OPEN_OR_EXPOSE",
    "冲可能被解释为打开或暴露午中己；当前没有准入条件支持。",
  ],
  [
    "SOURCE_DAMAGE_OR_REMOVE",
    "冲可能被解释为损伤或移除午中己；当前没有准入条件支持。",
  ],
];

const rejectionCodes = [
  "APPLICABILITY_AUTHORITY_INCOMPLETE",
  "EFFECT_DIRECTION_COMPETING",
  "COMPLETION_CONDITIONS_MISSING",
  "BLOCKING_CONDITIONS_MISSING",
  "COUNTER_EVIDENCE_MISSING",
  "PROFESSIONAL_PROVENANCE_MISSING",
];

const blockedClaims = [
  "AUTOMATIC_RELATION_DAMAGE",
  "AUTOMATIC_SOURCE_UNUSABLE",
];

export function buildRelationEffectAdmissionFixture() {
  const reading = {
    case_ref: "case-ref-visible",
    chart_version_ref: "chart-ref-visible",
    reading_ref: "reading-ref-visible",
    reading_hash: "1".repeat(64),
    read_only: true,
  };
  const targetDemand = demand({
    demandRef: "demand-exact-zi-wu",
    dependencyStatus: "SCOPE_INVARIANT_RULE_DEMAND",
    sourceMatchKind: "EXACT_IDENTITY",
    sourceSlot: "hour",
    sourceBranch: "午",
    peerSlot: "month",
    peerBranch: "子",
    scopePresence: ["EXACT_IDENTITY_ONLY", "ELEMENT_AFFINITY_INCLUDED"],
  });
  const deferredDemands = [
    demand({
      demandRef: "demand-inclusive-one",
      dependencyStatus: "MATCH_SCOPE_RULE_FIRST",
      sourceMatchKind: "SAME_ELEMENT_DIFFERENT_IDENTITY",
      sourceSlot: "year",
      sourceBranch: "巳",
      peerSlot: "month",
      peerBranch: "亥",
      scopePresence: ["ELEMENT_AFFINITY_INCLUDED"],
    }),
    demand({
      demandRef: "demand-inclusive-two",
      dependencyStatus: "MATCH_SCOPE_RULE_FIRST",
      sourceMatchKind: "SAME_ELEMENT_DIFFERENT_IDENTITY",
      sourceSlot: "day",
      sourceBranch: "卯",
      peerSlot: "year",
      peerBranch: "酉",
      scopePresence: ["ELEMENT_AFFINITY_INCLUDED"],
    }),
  ];
  const frontier = {
    frontier_ref: "frontier-ref-visible",
    frontier_hash: "2".repeat(64),
    frontier_version: "v60.mingli-relation-effect-research-frontier.001",
    ...reading,
    source_review_vector_ref: "source-review-vector-ref",
    source_review_vector_hash: "3".repeat(64),
    prerequisite_ref: "prerequisite-ref",
    prerequisite_hash: "4".repeat(64),
    refusal_receipt_ref: "refusal-receipt-ref",
    refusal_receipt_hash: "5".repeat(64),
    demands: [targetDemand, ...deferredDemands],
    demand_count: 3,
    scope_invariant_rule_demand_count: 1,
    match_scope_rule_first_count: 2,
    admitted_effect_rule_count: 0,
    research_semantics: "MEMBERSHIP_DEPENDENCY_AND_RULE_GAPS_ONLY",
    source_discussion_disposition: "ABSTAIN",
    effect_status: "UNRESOLVED",
    usability_status: "UNRESOLVED",
    provider_invoked: false,
    decision_created: false,
    gate_invoked: false,
    selection_authority: false,
    professional_verdict_allowed: false,
    probability_claim_allowed: false,
    canonical_write_allowed: false,
    read_only: true,
  };
  const review = {
    review_ref: "review-ref-visible",
    review_hash: "6".repeat(64),
    review_version: "v60.mingli-relation-rule-admission-review.001",
    case_ref: reading.case_ref,
    chart_version_ref: reading.chart_version_ref,
    reading_ref: reading.reading_ref,
    reading_hash: reading.reading_hash,
    frontier_ref: frontier.frontier_ref,
    frontier_hash: frontier.frontier_hash,
    policy_ref: "policy-ref-visible",
    policy_hash: "7".repeat(64),
    proposal_ref: "proposal-ref-visible",
    proposal_hash: "8".repeat(64),
    assessments: [
      {
        assessment_ref: "assessment-ref-visible",
        assessment_hash: "9".repeat(64),
        demand_ref: targetDemand.demand_ref,
        source_review_ref: targetDemand.source_review_ref,
        source_evidence_ref: targetDemand.source_evidence_ref,
        intersection_ref: targetDemand.intersection_ref,
        relation_fact_ref: targetDemand.relation_fact_ref,
        carrier_ref: targetDemand.carrier_ref,
        visible_slot: targetDemand.visible_slot,
        visible_stem: targetDemand.visible_stem,
        source_slot: targetDemand.source_slot,
        source_branch: "午",
        peer_slot: targetDemand.peer_slot,
        peer_branch: "子",
        relation_type: "six_clash_membership",
        source_match_kind: "EXACT_IDENTITY",
        policy_ref: "policy-ref-visible",
        policy_hash: "7".repeat(64),
        proposal_ref: "proposal-ref-visible",
        proposal_hash: "8".repeat(64),
        proposal_claim:
          "子午六冲成员命中后，自动判定午中同干来源受损，并据此判定该来源不可用。",
        interpretations: interpretations.map(([id, summary], index) => ({
          interpretation_ref: `interpretation-ref-${index + 1}`,
          interpretation_id: id,
          summary,
          status: "HELD",
          selected: false,
          effect_atom_created: false,
        })),
        dimension_assessments: dimensions.map((dimension, index) => ({
          dimension_id: dimension,
          submission_status: dimensionStatuses[index],
          current_basis_refs:
            index === 2 ? [] : [`dimension-basis-ref-${index + 1}`],
          gap: dimensionGaps[index],
          satisfied: false,
        })),
        disposition: "REJECTED_PRE_ADMISSION",
        candidate_truth_status: "NOT_EVALUATED_AS_TRUE_OR_FALSE",
        rejection_codes: rejectionCodes,
        blocked_claims: blockedClaims,
        admitted_effect_atom_refs: [],
        effect_status: "UNRESOLVED",
        usability_status: "UNRESOLVED",
      },
    ],
    reviewed_demand_count: 1,
    rejected_pre_admission_count: 1,
    admitted_effect_rule_count: 0,
    frontier_scope_invariant_demand_refs: [targetDemand.demand_ref],
    frontier_match_scope_demand_refs: deferredDemands.map(
      (item) => item.demand_ref,
    ),
    deferred_match_scope_demand_refs: deferredDemands.map(
      (item) => item.demand_ref,
    ),
    unreviewed_scope_invariant_demand_refs: [],
    disposition: "REJECTED_PRE_ADMISSION",
    review_semantics: "SHORTCUT_ADMISSION_REJECTION_NOT_EFFECT_NEGATION",
    effect_status: "UNRESOLVED",
    usability_status: "UNRESOLVED",
    provider_invoked: false,
    owner_professional_review_invoked: false,
    knowledge_promotion_request_created: false,
    gate_invoked: false,
    decision_created: false,
    selection_authority: false,
    professional_verdict_allowed: false,
    probability_claim_allowed: false,
    canonical_write_allowed: false,
    read_only: true,
  };
  const lab = {
    reading_ref: reading.reading_ref,
    reading_hash: reading.reading_hash,
    relation_effect_frontier_ref: frontier.frontier_ref,
    relation_effect_frontier_hash: frontier.frontier_hash,
    relation_effect_admission_review_ref: review.review_ref,
    relation_effect_admission_review_hash: review.review_hash,
  };
  return {
    bindings: { frontier, reading, lab },
    dimensions,
    proposalClaim: review.assessments[0].proposal_claim,
    review,
    targetDemandRef: targetDemand.demand_ref,
  };
}

function demand({
  demandRef,
  dependencyStatus,
  peerBranch,
  peerSlot,
  scopePresence,
  sourceBranch,
  sourceMatchKind,
  sourceSlot,
}) {
  return {
    demand_ref: demandRef,
    carrier_ref: `carrier-${demandRef}`,
    visible_slot: "year",
    visible_stem: "己",
    source_review_ref: `source-review-${demandRef}`,
    source_evidence_ref: `source-evidence-${demandRef}`,
    intersection_ref: `intersection-${demandRef}`,
    relation_fact_ref: `relation-fact-${demandRef}`,
    relation_type: "six_clash_membership",
    source_match_kind: sourceMatchKind,
    source_slot: sourceSlot,
    source_branch: sourceBranch,
    peer_slot: peerSlot,
    peer_branch: peerBranch,
    scope_presence: scopePresence,
    dependency_status: dependencyStatus,
    required_rule_dimensions: dimensions,
    effect_status: "UNRESOLVED",
    usability_status: "UNRESOLVED",
    selection_authority: false,
  };
}
