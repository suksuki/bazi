import type { HomeRelationEffectEvidenceRequestReceipt } from "./homeRelationEffectEvidenceRequestTypes";
import type {
  HomeRelationEffectEvidencePacketEnvelope,
  HomeRelationEffectProfessionalArtifactKind,
} from "./homeRelationEffectEvidencePacketTypes";

export const RELATION_EFFECT_EVIDENCE_MATERIAL_REQUEST_VERSION =
  "v60.mingli-relation-effect-evidence-material-request.001" as const;

export const RELATION_EFFECT_EVIDENCE_MATERIAL_VERSION =
  "v60.mingli-relation-effect-evidence-material.001" as const;

export const RELATION_EFFECT_EVIDENCE_TARGET_ARTIFACT_KIND =
  "PROFESSIONAL_SOURCE_MANIFEST" as const satisfies HomeRelationEffectProfessionalArtifactKind;

export interface RelationEffectEvidenceMaterialBibliography {
  title: string;
  responsible_party: string;
  edition_or_publication_identity: string;
  locator: string;
}

export interface RelationEffectEvidenceMaterialRequestPayload {
  material_request_version: typeof RELATION_EFFECT_EVIDENCE_MATERIAL_REQUEST_VERSION;
  expected_receipt_ref: string;
  expected_receipt_hash: string;
  expected_packet_ref: string;
  expected_packet_hash: string;
  expected_request_item_ref: string;
  expected_demand_packet_ref: string;
  expected_demand_packet_hash: string;
  expected_slot_ref: string;
  candidate_kind: "BIBLIOGRAPHIC_COORDINATE_CANDIDATE";
  target_artifact_kind: typeof RELATION_EFFECT_EVIDENCE_TARGET_ARTIFACT_KIND;
  bibliography: RelationEffectEvidenceMaterialBibliography;
  idempotency_key: string;
}

export interface HomeRelationEffectEvidenceMaterial {
  material_ref: string;
  material_hash: string;
  material_version: typeof RELATION_EFFECT_EVIDENCE_MATERIAL_VERSION;
  material_request_version: typeof RELATION_EFFECT_EVIDENCE_MATERIAL_REQUEST_VERSION;
  requester_account_ref: string;
  idempotency_key: string;
  case_ref: string;
  chart_version_ref: string;
  reading_ref: string;
  reading_hash: string;
  request_receipt_ref: string;
  request_receipt_hash: string;
  packet_ref: string;
  packet_hash: string;
  demand_packet_ref: string;
  demand_packet_hash: string;
  request_item_ref: string;
  slot_ref: string;
  dimension_id: "PROFESSIONAL_PROVENANCE";
  candidate_kind: "BIBLIOGRAPHIC_COORDINATE_CANDIDATE";
  target_artifact_kind: typeof RELATION_EFFECT_EVIDENCE_TARGET_ARTIFACT_KIND;
  bibliography: RelationEffectEvidenceMaterialBibliography;
  bibliography_hash: string;
  status: "CANDIDATE_METADATA_RECORDED_NOT_REQUESTED_ARTIFACT";
  semantics: "UNVERIFIED_BIBLIOGRAPHY_METADATA_ONLY";
  evidence_role: "NOT_EVIDENCE";
  requested_artifact_satisfied: false;
  candidate_material_count: 1;
  professional_material_count: 0;
  professional_evidence_count: 0;
  ready_dimension_slot_count: 0;
  effect_decision_status: "WITHHELD";
  effect_status: "UNRESOLVED";
  usability_status: "UNRESOLVED";
  material_truth_verified: false;
  source_authenticity_verified: false;
  artifact_content_present: false;
  citation_body_present: false;
  structured_bibliography_metadata_only: true;
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
  structured_bibliography_metadata_allowed: true;
  file_upload_allowed: false;
  url_submission_allowed: false;
  quotation_body_submission_allowed: false;
  conclusion_submission_allowed: false;
  unstructured_notes_submission_allowed: false;
  read_only: true;
}

export interface HomeRelationEffectEvidenceMaterialBindings {
  packet: HomeRelationEffectEvidencePacketEnvelope;
  receipt: HomeRelationEffectEvidenceRequestReceipt | null;
  lab: {
    relation_effect_evidence_request_receipt_ref: string | null;
    relation_effect_evidence_request_receipt_hash: string | null;
    relation_effect_evidence_material_refs: string[];
    relation_effect_evidence_material_hashes: string[];
    relation_effect_evidence_material_count: number;
  };
}
