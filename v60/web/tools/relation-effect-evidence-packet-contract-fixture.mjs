import { buildRelationEffectAdmissionFixture } from "./relation-effect-admission-contract-fixture.mjs";

export const evidenceDimensions = [
  "APPLICABILITY_CONTEXT",
  "EFFECT_DIRECTION",
  "COMPLETION_CONDITIONS",
  "BLOCKING_CONDITIONS",
  "COUNTER_EVIDENCE",
  "PROFESSIONAL_PROVENANCE",
];

export const evidenceDecisionPath = [
  "DETERMINISTIC_RELATION_FACT_AVAILABLE",
  "PROFESSIONAL_RULE_EVIDENCE_BLOCKED",
  "OWNER_PROFESSIONAL_REVIEW_NOT_INVOKED",
  "KNOWLEDGE_ADMISSION_NOT_ELIGIBLE",
  "READING_RULE_PROFILE_QUALIFICATION_NOT_AUTHORIZED",
  "EFFECT_DECISION_WITHHELD",
];

export const requiredProfessionalPath = [
  "COMPLETE_PROFESSIONAL_EVIDENCE_PACKET",
  "OWNER_PROFESSIONAL_REVIEW_APPROVED",
  "KNOWLEDGE_IMMUTABLE_RULE_PROFILE_ADMITTED",
  "NEW_READING_BINDS_ADMITTED_RULE_PROFILE",
  "DETERMINISTIC_RULE_APPLICATION_OR_UNRESOLVED",
];

const requirements = {
  APPLICABILITY_CONTEXT:
    "需要专业规则明确子午六冲成员关系在本命、严格同干与支藏来源坐标中何时可向作用命题传播。",
  EFFECT_DIRECTION:
    "需要专业规则在扰动、打开或暴露、损伤或移除等竞争解释间给出可复核的方向判据。",
  COMPLETION_CONDITIONS:
    "需要专业规则给出关系作用从成员事实到完成状态的必要与充分条件。",
  BLOCKING_CONDITIONS:
    "需要专业规则给出合会、距离、时令及其他条件如何阻断或改变该作用原子。",
  COUNTER_EVIDENCE:
    "需要专业反例协议定义逐项反证、撤销条件与适用边界。",
  PROFESSIONAL_PROVENANCE:
    "需要命题级专业来源清单、可定位引文及 Owner 专业审阅回执。",
};

const requestedArtifacts = {
  APPLICABILITY_CONTEXT: [
    "PROFESSIONAL_APPLICABILITY_RULE",
    "PROFESSIONAL_SOURCE_CITATION",
  ],
  EFFECT_DIRECTION: [
    "PROFESSIONAL_EFFECT_DIRECTION_RULE",
    "PROFESSIONAL_SOURCE_CITATION",
  ],
  COMPLETION_CONDITIONS: [
    "PROFESSIONAL_COMPLETION_RULE",
    "PROFESSIONAL_SOURCE_CITATION",
  ],
  BLOCKING_CONDITIONS: [
    "PROFESSIONAL_BLOCKING_RULE",
    "PROFESSIONAL_SOURCE_CITATION",
  ],
  COUNTER_EVIDENCE: [
    "PROFESSIONAL_COUNTER_EVIDENCE_PROTOCOL",
    "PROFESSIONAL_SOURCE_CITATION",
  ],
  PROFESSIONAL_PROVENANCE: [
    "PROFESSIONAL_SOURCE_MANIFEST",
    "PROFESSIONAL_SOURCE_CITATION",
    "OWNER_PROFESSIONAL_REVIEW_RECEIPT",
  ],
};

const nextActions = {
  APPLICABILITY_CONTEXT:
    "提交带版本与章节定位的适用范围规则，保持当前坐标事实只作上下文。",
  EFFECT_DIRECTION: "提交能排除竞争解释的专业方向规则与对应引文。",
  COMPLETION_CONDITIONS: "提交可执行且可反驳的作用完成条件。",
  BLOCKING_CONDITIONS:
    "提交逐项阻断条件及其优先级、适用范围与引文。",
  COUNTER_EVIDENCE: "提交反例类型、撤销条件与负向案例协议。",
  PROFESSIONAL_PROVENANCE:
    "提交专业来源清单、命题级引文，并在材料完整后请求 Owner 专业审阅。",
};

export function buildRelationEffectEvidencePacketFixture() {
  const fixture = buildRelationEffectAdmissionFixture();
  const assessment = fixture.review.assessments[0];
  const dimensionSlots = assessment.dimension_assessments.map(
    (dimension, index) => ({
      slot_ref: `evidence-slot-ref-${index + 1}`,
      dimension_id: dimension.dimension_id,
      proposal_submission_status: dimension.submission_status,
      current_basis_refs: [...dimension.current_basis_refs],
      current_basis_status:
        "RUNTIME_CONTEXT_ONLY_NOT_PROFESSIONAL_EVIDENCE",
      requirement: requirements[dimension.dimension_id],
      requested_artifact_kinds: [
        ...requestedArtifacts[dimension.dimension_id],
      ],
      guidance_semantics:
        "REQUEST_GUIDANCE_NOT_KNOWLEDGE_ADMISSION",
      professional_evidence_refs: [],
      professional_evidence_count: 0,
      slot_status: "BLOCKED_MISSING_PROFESSIONAL_EVIDENCE",
      next_action: nextActions[dimension.dimension_id],
      ready: false,
    }),
  );
  const demandPacket = {
    demand_packet_ref: "demand-evidence-packet-ref-visible",
    demand_packet_hash: "a".repeat(64),
    assessment_ref: assessment.assessment_ref,
    assessment_hash: assessment.assessment_hash,
    demand_ref: assessment.demand_ref,
    source_review_ref: assessment.source_review_ref,
    source_evidence_ref: assessment.source_evidence_ref,
    intersection_ref: assessment.intersection_ref,
    relation_fact_ref: assessment.relation_fact_ref,
    carrier_ref: assessment.carrier_ref,
    visible_slot: assessment.visible_slot,
    visible_stem: assessment.visible_stem,
    source_slot: assessment.source_slot,
    source_branch: assessment.source_branch,
    peer_slot: assessment.peer_slot,
    peer_branch: assessment.peer_branch,
    relation_type: assessment.relation_type,
    source_match_kind: assessment.source_match_kind,
    policy_ref: assessment.policy_ref,
    policy_hash: assessment.policy_hash,
    proposal_ref: assessment.proposal_ref,
    proposal_hash: assessment.proposal_hash,
    dimension_slots: dimensionSlots,
    required_dimension_slot_count: 6,
    ready_dimension_slot_count: 0,
    professional_evidence_count: 0,
    status: "EVIDENCE_INTAKE_REQUIRED",
    effect_status: "UNRESOLVED",
    usability_status: "UNRESOLVED",
  };
  const packet = {
    packet_ref: "relation-effect-evidence-packet-ref-visible",
    packet_hash: "b".repeat(64),
    packet_version: "v60.mingli-relation-effect-evidence-packet.001",
    case_ref: fixture.bindings.reading.case_ref,
    chart_version_ref: fixture.bindings.reading.chart_version_ref,
    reading_ref: fixture.bindings.reading.reading_ref,
    reading_hash: fixture.bindings.reading.reading_hash,
    frontier_ref: fixture.bindings.frontier.frontier_ref,
    frontier_hash: fixture.bindings.frontier.frontier_hash,
    admission_review_ref: fixture.review.review_ref,
    admission_review_hash: fixture.review.review_hash,
    policy_ref: fixture.review.policy_ref,
    policy_hash: fixture.review.policy_hash,
    proposal_ref: fixture.review.proposal_ref,
    proposal_hash: fixture.review.proposal_hash,
    demand_packets: [demandPacket],
    demand_packet_count: 1,
    required_dimension_slot_count: 6,
    ready_dimension_slot_count: 0,
    professional_evidence_count: 0,
    status: "EVIDENCE_INTAKE_REQUIRED",
    projection_semantics:
      "PROFESSIONAL_EVIDENCE_READINESS_NOT_DECISION",
    decision_path_semantics: "READINESS_PATH_NOT_DECISION",
    decision_path: [...evidenceDecisionPath],
    required_professional_path_semantics:
      "FUTURE_AUTHORITY_PATH_NOT_EXECUTED",
    required_professional_path: [...requiredProfessionalPath],
    effect_decision_status: "WITHHELD",
    effect_status: "UNRESOLVED",
    usability_status: "UNRESOLVED",
    knowledge_admission_eligible: false,
    llm_allowed: false,
    provider_invoked: false,
    reasoner_invoked: false,
    decision_request_created: false,
    owner_professional_review_invoked: false,
    knowledge_promotion_request_created: false,
    gate_invoked: false,
    ledger_invoked: false,
    decision_created: false,
    selection_authority: false,
    professional_verdict_allowed: false,
    probability_claim_allowed: false,
    canonical_write_allowed: false,
    read_only: true,
  };
  fixture.bindings.lab.relation_effect_evidence_packet_ref =
    packet.packet_ref;
  fixture.bindings.lab.relation_effect_evidence_packet_hash =
    packet.packet_hash;
  fixture.bindings.lab.relation_effect_evidence_request_receipt_ref =
    null;
  fixture.bindings.lab.relation_effect_evidence_request_receipt_hash =
    null;
  return { ...fixture, packet, requestReceipt: null };
}

export function makeNotTriggeredEvidencePacketFixture() {
  const fixture = buildRelationEffectEvidencePacketFixture();
  fixture.review.review_ref = "review-ref-not-triggered";
  fixture.review.review_hash = "c".repeat(64);
  fixture.review.assessments = [];
  fixture.review.reviewed_demand_count = 0;
  fixture.review.rejected_pre_admission_count = 0;
  fixture.review.unreviewed_scope_invariant_demand_refs = [
    fixture.targetDemandRef,
  ];
  fixture.review.disposition = "NOT_TRIGGERED";
  fixture.bindings.lab.relation_effect_admission_review_ref =
    fixture.review.review_ref;
  fixture.bindings.lab.relation_effect_admission_review_hash =
    fixture.review.review_hash;
  fixture.packet.packet_ref =
    "relation-effect-evidence-packet-ref-not-triggered";
  fixture.packet.packet_hash = "d".repeat(64);
  fixture.packet.admission_review_ref = fixture.review.review_ref;
  fixture.packet.admission_review_hash = fixture.review.review_hash;
  fixture.packet.demand_packets = [];
  fixture.packet.demand_packet_count = 0;
  fixture.packet.required_dimension_slot_count = 0;
  fixture.packet.status = "NOT_TRIGGERED";
  fixture.packet.decision_path = [];
  fixture.packet.effect_decision_status = "NOT_TRIGGERED";
  fixture.bindings.lab.relation_effect_evidence_packet_ref =
    fixture.packet.packet_ref;
  fixture.bindings.lab.relation_effect_evidence_packet_hash =
    fixture.packet.packet_hash;
  return fixture;
}
