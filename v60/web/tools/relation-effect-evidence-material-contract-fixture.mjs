import {
  buildClearRelationEffectEvidenceRequestFixture,
  buildEmptyRelationEffectEvidenceRequestFixture,
  buildRecordedRelationEffectEvidenceRequestFixture,
} from "./relation-effect-evidence-request-contract-fixture.mjs";

export function buildEmptyRelationEffectEvidenceMaterialFixture() {
  return buildRecordedRelationEffectEvidenceRequestFixture();
}

export function buildRecordedRelationEffectEvidenceMaterialFixture() {
  const fixture = buildRecordedRelationEffectEvidenceRequestFixture();
  const requestItem = fixture.requestReceipt.request_items[0];
  const slot = requestItem.dimension_slots.find(
    (candidate) =>
      candidate.dimension_id === "PROFESSIONAL_PROVENANCE",
  );
  if (!slot) throw new Error("fixture-professional-provenance-slot-missing");
  const material = {
    material_ref: "relation-effect-evidence-material-ref-visible",
    material_hash: "f".repeat(64),
    material_version:
      "v60.mingli-relation-effect-evidence-material.001",
    material_request_version:
      "v60.mingli-relation-effect-evidence-material-request.001",
    requester_account_ref:
      fixture.requestReceipt.requester_account_ref,
    idempotency_key:
      "relation-effect-material:" +
      fixture.requestReceipt.receipt_hash.slice(0, 24) +
      ":fixture",
    case_ref: fixture.requestReceipt.case_ref,
    chart_version_ref: fixture.requestReceipt.chart_version_ref,
    reading_ref: fixture.requestReceipt.reading_ref,
    reading_hash: fixture.requestReceipt.reading_hash,
    request_receipt_ref: fixture.requestReceipt.receipt_ref,
    request_receipt_hash: fixture.requestReceipt.receipt_hash,
    packet_ref: fixture.requestReceipt.packet_ref,
    packet_hash: fixture.requestReceipt.packet_hash,
    request_item_ref: requestItem.request_item_ref,
    demand_packet_ref: requestItem.demand_packet_ref,
    demand_packet_hash: requestItem.demand_packet_hash,
    slot_ref: slot.slot_ref,
    dimension_id: "PROFESSIONAL_PROVENANCE",
    candidate_kind: "BIBLIOGRAPHIC_COORDINATE_CANDIDATE",
    target_artifact_kind: "PROFESSIONAL_SOURCE_MANIFEST",
    bibliography: {
      title: "子平规则史料校注",
      responsible_party: "示例编校组",
      edition_or_publication_identity: "校注版 · 第一辑",
      locator: "卷二 · 第三章 · 第 18 页",
    },
    bibliography_hash:
      "0a824d379bc83dfaf2c79703cb67f77fca4649a7a7063c8e155e43b114eb1530",
    status: "CANDIDATE_METADATA_RECORDED_NOT_REQUESTED_ARTIFACT",
    semantics: "UNVERIFIED_BIBLIOGRAPHY_METADATA_ONLY",
    evidence_role: "NOT_EVIDENCE",
    requested_artifact_satisfied: false,
    candidate_material_count: 1,
    professional_material_count: 0,
    professional_evidence_count: 0,
    ready_dimension_slot_count: 0,
    effect_decision_status: "WITHHELD",
    effect_status: "UNRESOLVED",
    usability_status: "UNRESOLVED",
    material_truth_verified: false,
    source_authenticity_verified: false,
    artifact_content_present: false,
    citation_body_present: false,
    structured_bibliography_metadata_only: true,
    llm_allowed: false,
    provider_invoked: false,
    reasoner_invoked: false,
    owner_professional_review_invoked: false,
    knowledge_admission_eligible: false,
    knowledge_write_allowed: false,
    gate_invoked: false,
    decision_request_created: false,
    decision_created: false,
    professional_verdict_allowed: false,
    probability_claim_allowed: false,
    effect_or_usability_write_allowed: false,
    private_to_requester_account: true,
    append_only: true,
    structured_bibliography_metadata_allowed: true,
    file_upload_allowed: false,
    url_submission_allowed: false,
    quotation_body_submission_allowed: false,
    conclusion_submission_allowed: false,
    unstructured_notes_submission_allowed: false,
    read_only: true,
  };
  fixture.materials = [material];
  fixture.bindings.lab.relation_effect_evidence_material_refs = [
    material.material_ref,
  ];
  fixture.bindings.lab.relation_effect_evidence_material_hashes = [
    material.material_hash,
  ];
  fixture.bindings.lab.relation_effect_evidence_material_count = 1;
  fixture.material = material;
  fixture.materialRequestItem = requestItem;
  fixture.materialSlot = slot;
  return fixture;
}

export function buildNoRequestRelationEffectEvidenceMaterialFixture() {
  return buildEmptyRelationEffectEvidenceRequestFixture();
}

export function buildClearRelationEffectEvidenceMaterialFixture() {
  return buildClearRelationEffectEvidenceRequestFixture();
}
