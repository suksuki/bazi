import {
  arraysEqual,
  hasOnlyKeys,
  isHash,
  isRecord,
  isRef,
} from "./homeRelationEffectAdmissionValidation";
import {
  RELATION_EFFECT_EVIDENCE_TARGET_ARTIFACT_KIND,
  RELATION_EFFECT_EVIDENCE_MATERIAL_REQUEST_VERSION,
  RELATION_EFFECT_EVIDENCE_MATERIAL_VERSION,
  type HomeRelationEffectEvidenceMaterial,
  type HomeRelationEffectEvidenceMaterialBindings,
} from "./homeRelationEffectEvidenceMaterialTypes";
import { isRelationEffectEvidenceRequestStateDisplayable } from "./homeRelationEffectEvidenceRequestGuard";
import type {
  HomeRelationEffectEvidenceRequestItem,
  HomeRelationEffectEvidenceRequestReceipt,
} from "./homeRelationEffectEvidenceRequestTypes";
import { isRelationEffectMaterialBibliographyValid } from "./relationEffectEvidenceMaterialValidation";

const MATERIAL_KEYS = [
  "material_ref",
  "material_hash",
  "material_version",
  "material_request_version",
  "requester_account_ref",
  "idempotency_key",
  "case_ref",
  "chart_version_ref",
  "reading_ref",
  "reading_hash",
  "request_receipt_ref",
  "request_receipt_hash",
  "packet_ref",
  "packet_hash",
  "request_item_ref",
  "demand_packet_ref",
  "demand_packet_hash",
  "slot_ref",
  "dimension_id",
  "candidate_kind",
  "target_artifact_kind",
  "bibliography",
  "bibliography_hash",
  "status",
  "semantics",
  "evidence_role",
  "requested_artifact_satisfied",
  "candidate_material_count",
  "professional_material_count",
  "professional_evidence_count",
  "ready_dimension_slot_count",
  "effect_decision_status",
  "effect_status",
  "usability_status",
  "material_truth_verified",
  "source_authenticity_verified",
  "artifact_content_present",
  "citation_body_present",
  "structured_bibliography_metadata_only",
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
  "structured_bibliography_metadata_allowed",
  "file_upload_allowed",
  "url_submission_allowed",
  "quotation_body_submission_allowed",
  "conclusion_submission_allowed",
  "unstructured_notes_submission_allowed",
  "read_only",
] as const;

const BIBLIOGRAPHY_KEYS = [
  "title",
  "responsible_party",
  "edition_or_publication_identity",
  "locator",
] as const;

export function isRelationEffectEvidenceMaterialStateDisplayable(
  candidate: unknown,
  bindings: HomeRelationEffectEvidenceMaterialBindings,
): candidate is HomeRelationEffectEvidenceMaterial[] {
  if (
    !isRelationEffectEvidenceRequestStateDisplayable(bindings.receipt, {
      packet: bindings.packet,
      lab: bindings.lab,
    }) ||
    !Array.isArray(candidate) ||
    !Array.isArray(
      bindings.lab.relation_effect_evidence_material_refs,
    ) ||
    !Array.isArray(
      bindings.lab.relation_effect_evidence_material_hashes,
    ) ||
    bindings.lab.relation_effect_evidence_material_count !==
      candidate.length ||
    !arraysEqual(
      candidate.map((material) =>
        isRecord(material) ? material.material_ref : null,
      ),
      bindings.lab.relation_effect_evidence_material_refs,
    ) ||
    !arraysEqual(
      candidate.map((material) =>
        isRecord(material) ? material.material_hash : null,
      ),
      bindings.lab.relation_effect_evidence_material_hashes,
    )
  ) {
    return false;
  }
  if (!bindings.receipt) return candidate.length === 0;
  return (
    bindings.packet.ready_dimension_slot_count === 0 &&
    bindings.packet.professional_evidence_count === 0 &&
    bindings.receipt.ready_dimension_slot_count === 0 &&
    bindings.receipt.professional_material_count === 0 &&
    bindings.receipt.professional_evidence_count === 0 &&
    new Set(
      candidate.map((material) =>
        isRecord(material) ? material.material_ref : null,
      ),
    ).size === candidate.length &&
    new Set(
      candidate.map((material) =>
        isRecord(material) ? material.material_hash : null,
      ),
    ).size === candidate.length &&
    candidate.every((material) =>
      isMaterialSafe(
        material,
        bindings.receipt as HomeRelationEffectEvidenceRequestReceipt,
      ),
    )
  );
}

function isMaterialSafe(
  candidate: unknown,
  receipt: HomeRelationEffectEvidenceRequestReceipt,
): candidate is HomeRelationEffectEvidenceMaterial {
  if (
    !isRecord(candidate) ||
    !hasOnlyKeys(candidate, MATERIAL_KEYS) ||
    !isRef(candidate.material_ref) ||
    !isHash(candidate.material_hash) ||
    candidate.material_version !==
      RELATION_EFFECT_EVIDENCE_MATERIAL_VERSION ||
    candidate.material_request_version !==
      RELATION_EFFECT_EVIDENCE_MATERIAL_REQUEST_VERSION ||
    candidate.requester_account_ref !== receipt.requester_account_ref ||
    !isIdempotencyKey(candidate.idempotency_key) ||
    candidate.case_ref !== receipt.case_ref ||
    candidate.chart_version_ref !== receipt.chart_version_ref ||
    candidate.reading_ref !== receipt.reading_ref ||
    candidate.reading_hash !== receipt.reading_hash ||
    candidate.request_receipt_ref !== receipt.receipt_ref ||
    candidate.request_receipt_hash !== receipt.receipt_hash ||
    candidate.packet_ref !== receipt.packet_ref ||
    candidate.packet_hash !== receipt.packet_hash
  ) {
    return false;
  }
  const requestItem = receipt.request_items.find(
    (item) => item.request_item_ref === candidate.request_item_ref,
  );
  return (
    !!requestItem &&
    isRequestLineageSafe(candidate, requestItem) &&
    candidate.dimension_id === "PROFESSIONAL_PROVENANCE" &&
    candidate.candidate_kind ===
      "BIBLIOGRAPHIC_COORDINATE_CANDIDATE" &&
    candidate.target_artifact_kind ===
      RELATION_EFFECT_EVIDENCE_TARGET_ARTIFACT_KIND &&
    isBibliographySafe(candidate.bibliography) &&
    isHash(candidate.bibliography_hash) &&
    candidate.status ===
      "CANDIDATE_METADATA_RECORDED_NOT_REQUESTED_ARTIFACT" &&
    candidate.semantics ===
      "UNVERIFIED_BIBLIOGRAPHY_METADATA_ONLY" &&
    candidate.evidence_role === "NOT_EVIDENCE" &&
    candidate.requested_artifact_satisfied === false &&
    candidate.candidate_material_count === 1 &&
    candidate.professional_material_count === 0 &&
    candidate.professional_evidence_count === 0 &&
    candidate.ready_dimension_slot_count === 0 &&
    candidate.effect_decision_status === "WITHHELD" &&
    candidate.effect_status === "UNRESOLVED" &&
    candidate.usability_status === "UNRESOLVED" &&
    candidate.material_truth_verified === false &&
    candidate.source_authenticity_verified === false &&
    candidate.artifact_content_present === false &&
    candidate.citation_body_present === false &&
    candidate.structured_bibliography_metadata_only === true &&
    candidate.llm_allowed === false &&
    candidate.provider_invoked === false &&
    candidate.reasoner_invoked === false &&
    candidate.owner_professional_review_invoked === false &&
    candidate.knowledge_admission_eligible === false &&
    candidate.knowledge_write_allowed === false &&
    candidate.gate_invoked === false &&
    candidate.decision_request_created === false &&
    candidate.decision_created === false &&
    candidate.professional_verdict_allowed === false &&
    candidate.probability_claim_allowed === false &&
    candidate.effect_or_usability_write_allowed === false &&
    candidate.private_to_requester_account === true &&
    candidate.append_only === true &&
    candidate.structured_bibliography_metadata_allowed === true &&
    candidate.file_upload_allowed === false &&
    candidate.url_submission_allowed === false &&
    candidate.quotation_body_submission_allowed === false &&
    candidate.conclusion_submission_allowed === false &&
    candidate.unstructured_notes_submission_allowed === false &&
    candidate.read_only === true
  );
}

function isRequestLineageSafe(
  candidate: Record<string, unknown>,
  requestItem: HomeRelationEffectEvidenceRequestItem,
): boolean {
  const slot = requestItem.dimension_slots.find(
    (item) => item.slot_ref === candidate.slot_ref,
  );
  return (
    candidate.demand_packet_ref === requestItem.demand_packet_ref &&
    candidate.demand_packet_hash === requestItem.demand_packet_hash &&
    !!slot &&
    slot.dimension_id === "PROFESSIONAL_PROVENANCE" &&
    slot.requested_artifact_kinds.includes(
      RELATION_EFFECT_EVIDENCE_TARGET_ARTIFACT_KIND,
    )
  );
}

function isBibliographySafe(candidate: unknown): boolean {
  return (
    isRecord(candidate) &&
    hasOnlyKeys(candidate, BIBLIOGRAPHY_KEYS) &&
    typeof candidate.title === "string" &&
    typeof candidate.responsible_party === "string" &&
    typeof candidate.edition_or_publication_identity === "string" &&
    typeof candidate.locator === "string" &&
    isRelationEffectMaterialBibliographyValid({
      title: candidate.title,
      responsible_party: candidate.responsible_party,
      edition_or_publication_identity:
        candidate.edition_or_publication_identity,
      locator: candidate.locator,
    })
  );
}

function isIdempotencyKey(value: unknown): value is string {
  return (
    typeof value === "string" &&
    value.length >= 1 &&
    value.length <= 180
  );
}
