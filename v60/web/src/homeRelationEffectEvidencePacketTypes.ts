import type {
  HomeRelationEffectAdmissionDimension,
  HomeRelationEffectAdmissionReviewEnvelope,
} from "./homeRelationEffectAdmissionTypes";
import type { HomeRelationEffectResearchFrontierEnvelope } from "./homeRelationEffectFrontierTypes";

export const RELATION_EFFECT_EVIDENCE_PACKET_VERSION =
  "v60.mingli-relation-effect-evidence-packet.001" as const;

export const RELATION_EFFECT_EVIDENCE_DECISION_PATH = [
  "DETERMINISTIC_RELATION_FACT_AVAILABLE",
  "PROFESSIONAL_RULE_EVIDENCE_BLOCKED",
  "OWNER_PROFESSIONAL_REVIEW_NOT_INVOKED",
  "KNOWLEDGE_ADMISSION_NOT_ELIGIBLE",
  "READING_RULE_PROFILE_QUALIFICATION_NOT_AUTHORIZED",
  "EFFECT_DECISION_WITHHELD",
] as const;

export const RELATION_EFFECT_REQUIRED_PROFESSIONAL_PATH = [
  "COMPLETE_PROFESSIONAL_EVIDENCE_PACKET",
  "OWNER_PROFESSIONAL_REVIEW_APPROVED",
  "KNOWLEDGE_IMMUTABLE_RULE_PROFILE_ADMITTED",
  "NEW_READING_BINDS_ADMITTED_RULE_PROFILE",
  "DETERMINISTIC_RULE_APPLICATION_OR_UNRESOLVED",
] as const;

export const RELATION_EFFECT_PROFESSIONAL_ARTIFACT_KINDS = [
  "PROFESSIONAL_APPLICABILITY_RULE",
  "PROFESSIONAL_EFFECT_DIRECTION_RULE",
  "PROFESSIONAL_COMPLETION_RULE",
  "PROFESSIONAL_BLOCKING_RULE",
  "PROFESSIONAL_COUNTER_EVIDENCE_PROTOCOL",
  "PROFESSIONAL_SOURCE_MANIFEST",
  "PROFESSIONAL_SOURCE_CITATION",
  "OWNER_PROFESSIONAL_REVIEW_RECEIPT",
] as const;

export type HomeRelationEffectProfessionalArtifactKind =
  (typeof RELATION_EFFECT_PROFESSIONAL_ARTIFACT_KINDS)[number];

export const RELATION_EFFECT_EVIDENCE_REQUIREMENTS = {
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
} as const satisfies Record<HomeRelationEffectAdmissionDimension, string>;

export const RELATION_EFFECT_EVIDENCE_REQUESTED_ARTIFACTS = {
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
} as const satisfies Record<
  HomeRelationEffectAdmissionDimension,
  readonly HomeRelationEffectProfessionalArtifactKind[]
>;

export const RELATION_EFFECT_EVIDENCE_NEXT_ACTIONS = {
  APPLICABILITY_CONTEXT:
    "提交带版本与章节定位的适用范围规则，保持当前坐标事实只作上下文。",
  EFFECT_DIRECTION: "提交能排除竞争解释的专业方向规则与对应引文。",
  COMPLETION_CONDITIONS: "提交可执行且可反驳的作用完成条件。",
  BLOCKING_CONDITIONS:
    "提交逐项阻断条件及其优先级、适用范围与引文。",
  COUNTER_EVIDENCE: "提交反例类型、撤销条件与负向案例协议。",
  PROFESSIONAL_PROVENANCE:
    "提交专业来源清单、命题级引文，并在材料完整后请求 Owner 专业审阅。",
} as const satisfies Record<HomeRelationEffectAdmissionDimension, string>;

export interface HomeRelationEffectEvidenceDimensionSlot {
  slot_ref: string;
  dimension_id: HomeRelationEffectAdmissionDimension;
  proposal_submission_status:
    | "VERIFIED"
    | "PARTIAL"
    | "COMPETING"
    | "UNSUPPORTED"
    | "MISSING";
  current_basis_refs: string[];
  current_basis_status: "RUNTIME_CONTEXT_ONLY_NOT_PROFESSIONAL_EVIDENCE";
  requirement: string;
  requested_artifact_kinds: HomeRelationEffectProfessionalArtifactKind[];
  guidance_semantics: "REQUEST_GUIDANCE_NOT_KNOWLEDGE_ADMISSION";
  professional_evidence_refs: string[];
  professional_evidence_count: 0;
  slot_status: "BLOCKED_MISSING_PROFESSIONAL_EVIDENCE";
  next_action: string;
  ready: false;
}

export interface HomeRelationEffectEvidenceDemandPacket {
  demand_packet_ref: string;
  demand_packet_hash: string;
  assessment_ref: string;
  assessment_hash: string;
  demand_ref: string;
  source_review_ref: string;
  source_evidence_ref: string;
  intersection_ref: string;
  relation_fact_ref: string;
  carrier_ref: string;
  visible_slot: "year" | "month" | "day" | "hour";
  visible_stem: string;
  source_slot: "year" | "month" | "day" | "hour";
  source_branch: "午";
  peer_slot: "year" | "month" | "day" | "hour";
  peer_branch: "子";
  relation_type: "six_clash_membership";
  source_match_kind: "EXACT_IDENTITY";
  policy_ref: string;
  policy_hash: string;
  proposal_ref: string;
  proposal_hash: string;
  dimension_slots: HomeRelationEffectEvidenceDimensionSlot[];
  required_dimension_slot_count: 6;
  ready_dimension_slot_count: 0;
  professional_evidence_count: 0;
  status: "EVIDENCE_INTAKE_REQUIRED";
  effect_status: "UNRESOLVED";
  usability_status: "UNRESOLVED";
}

export interface HomeRelationEffectEvidencePacketEnvelope {
  packet_ref: string;
  packet_hash: string;
  packet_version: typeof RELATION_EFFECT_EVIDENCE_PACKET_VERSION;
  case_ref: string;
  chart_version_ref: string;
  reading_ref: string;
  reading_hash: string;
  frontier_ref: string;
  frontier_hash: string;
  admission_review_ref: string;
  admission_review_hash: string;
  policy_ref: string;
  policy_hash: string;
  proposal_ref: string;
  proposal_hash: string;
  demand_packets: HomeRelationEffectEvidenceDemandPacket[];
  demand_packet_count: number;
  required_dimension_slot_count: number;
  ready_dimension_slot_count: 0;
  professional_evidence_count: 0;
  status: "EVIDENCE_INTAKE_REQUIRED" | "NOT_TRIGGERED";
  projection_semantics: "PROFESSIONAL_EVIDENCE_READINESS_NOT_DECISION";
  decision_path_semantics: "READINESS_PATH_NOT_DECISION";
  decision_path: Array<
    (typeof RELATION_EFFECT_EVIDENCE_DECISION_PATH)[number]
  >;
  required_professional_path_semantics: "FUTURE_AUTHORITY_PATH_NOT_EXECUTED";
  required_professional_path: Array<
    (typeof RELATION_EFFECT_REQUIRED_PROFESSIONAL_PATH)[number]
  >;
  effect_decision_status: "WITHHELD" | "NOT_TRIGGERED";
  effect_status: "UNRESOLVED";
  usability_status: "UNRESOLVED";
  knowledge_admission_eligible: false;
  llm_allowed: false;
  provider_invoked: false;
  reasoner_invoked: false;
  decision_request_created: false;
  owner_professional_review_invoked: false;
  knowledge_promotion_request_created: false;
  gate_invoked: false;
  ledger_invoked: false;
  decision_created: false;
  selection_authority: false;
  professional_verdict_allowed: false;
  probability_claim_allowed: false;
  canonical_write_allowed: false;
  read_only: true;
}

export interface HomeRelationEffectEvidencePacketBindings {
  reading: {
    case_ref: string;
    chart_version_ref: string;
    reading_ref: string;
    reading_hash: string;
    read_only: true;
  };
  frontier: HomeRelationEffectResearchFrontierEnvelope;
  review: HomeRelationEffectAdmissionReviewEnvelope;
  lab: {
    reading_ref: string;
    reading_hash: string;
    relation_effect_frontier_ref: string;
    relation_effect_frontier_hash: string;
    relation_effect_admission_review_ref: string;
    relation_effect_admission_review_hash: string;
    relation_effect_evidence_packet_ref: string;
    relation_effect_evidence_packet_hash: string;
  };
}
