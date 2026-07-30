import type { HomeRelationEffectAdmissionDimension } from "./homeRelationEffectAdmissionTypes";
import type {
  HomeRelationEffectEvidencePacketEnvelope,
  HomeRelationEffectProfessionalArtifactKind,
} from "./homeRelationEffectEvidencePacketTypes";

export const RELATION_EFFECT_EVIDENCE_REQUEST_VERSION =
  "v60.mingli-relation-effect-evidence-request.001" as const;

export const RELATION_EFFECT_EVIDENCE_REQUEST_RECEIPT_VERSION =
  "v60.mingli-relation-effect-evidence-request-receipt.001" as const;

export interface RelationEffectEvidenceRequestPayload {
  request_version: typeof RELATION_EFFECT_EVIDENCE_REQUEST_VERSION;
  expected_packet_ref: string;
  expected_packet_hash: string;
  idempotency_key: string;
}

export interface HomeRelationEffectEvidenceRequestedSlot {
  slot_ref: string;
  dimension_id: HomeRelationEffectAdmissionDimension;
  requirement: string;
  requested_artifact_kinds: HomeRelationEffectProfessionalArtifactKind[];
  next_action: string;
  status: "REQUESTED_NOT_EVIDENCE";
  professional_material_count: 0;
  professional_evidence_count: 0;
  ready: false;
}

export interface HomeRelationEffectEvidenceRequestItem {
  request_item_ref: string;
  demand_packet_ref: string;
  demand_packet_hash: string;
  assessment_ref: string;
  assessment_hash: string;
  demand_ref: string;
  dimension_slots: HomeRelationEffectEvidenceRequestedSlot[];
  requested_dimension_slot_count: number;
}

export interface HomeRelationEffectEvidenceRequestReceipt {
  receipt_ref: string;
  receipt_hash: string;
  receipt_version: typeof RELATION_EFFECT_EVIDENCE_REQUEST_RECEIPT_VERSION;
  request_version: typeof RELATION_EFFECT_EVIDENCE_REQUEST_VERSION;
  requester_account_ref: string;
  idempotency_key: string;
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
  packet_ref: string;
  packet_hash: string;
  request_items: HomeRelationEffectEvidenceRequestItem[];
  request_item_count: number;
  requested_dimension_slot_count: number;
  ready_dimension_slot_count: 0;
  professional_material_count: 0;
  professional_evidence_count: 0;
  status: "REQUEST_RECORDED_NOT_EVIDENCE";
  semantics: "PREPARATION_REQUEST_NOT_PROFESSIONAL_EVIDENCE";
  evidence_role: "NOT_EVIDENCE";
  effect_decision_status: "WITHHELD";
  effect_status: "UNRESOLVED";
  usability_status: "UNRESOLVED";
  llm_allowed: false;
  provider_invoked: false;
  reasoner_invoked: false;
  owner_professional_review_invoked: false;
  knowledge_admission_eligible: false;
  knowledge_write_allowed: false;
  gate_invoked: false;
  decision_request_created: false;
  decision_created: false;
  professional_verdict_allowed: false;
  probability_claim_allowed: false;
  effect_or_usability_write_allowed: false;
  private_to_requester_account: true;
  append_only: true;
  material_intake_open: false;
  file_upload_allowed: false;
  url_submission_allowed: false;
  free_text_submission_allowed: false;
  read_only: true;
}

export interface HomeRelationEffectEvidenceRequestBindings {
  packet: HomeRelationEffectEvidencePacketEnvelope;
  lab: {
    relation_effect_evidence_request_receipt_ref: string | null;
    relation_effect_evidence_request_receipt_hash: string | null;
  };
}
