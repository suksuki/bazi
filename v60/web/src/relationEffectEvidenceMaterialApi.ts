import type {
  HomeRelationEffectEvidenceRequestedSlot,
  HomeRelationEffectEvidenceRequestItem,
  HomeRelationEffectEvidenceRequestReceipt,
} from "./homeRelationEffectEvidenceRequestTypes";
import {
  RELATION_EFFECT_EVIDENCE_TARGET_ARTIFACT_KIND,
  RELATION_EFFECT_EVIDENCE_MATERIAL_REQUEST_VERSION,
  type HomeRelationEffectEvidenceMaterial,
  type RelationEffectEvidenceMaterialBibliography,
  type RelationEffectEvidenceMaterialRequestPayload,
} from "./homeRelationEffectEvidenceMaterialTypes";
import { request } from "./http";
import {
  isRelationEffectMaterialBibliographyValid,
  normalizeRelationEffectMaterialBibliography,
} from "./relationEffectEvidenceMaterialValidation";

const ENDPOINT =
  "/api/v60/experience/home/relation-effect-evidence-material";

export function buildRelationEffectEvidenceMaterialPayload(
  receipt: HomeRelationEffectEvidenceRequestReceipt,
  requestItem: HomeRelationEffectEvidenceRequestItem,
  slot: HomeRelationEffectEvidenceRequestedSlot,
  bibliography: RelationEffectEvidenceMaterialBibliography,
): RelationEffectEvidenceMaterialRequestPayload {
  const normalized =
    normalizeRelationEffectMaterialBibliography(bibliography);
  const boundItem = receipt.request_items.find(
    (candidate) =>
      candidate.request_item_ref === requestItem.request_item_ref &&
      candidate.demand_packet_ref === requestItem.demand_packet_ref &&
      candidate.demand_packet_hash === requestItem.demand_packet_hash,
  );
  const boundSlot = boundItem?.dimension_slots.find(
    (candidate) => candidate.slot_ref === slot.slot_ref,
  );
  if (
    !boundItem ||
    !boundSlot ||
    boundSlot.dimension_id !== "PROFESSIONAL_PROVENANCE" ||
    !boundSlot.requested_artifact_kinds.includes(
      RELATION_EFFECT_EVIDENCE_TARGET_ARTIFACT_KIND,
    ) ||
    !isRelationEffectMaterialBibliographyValid(normalized)
  ) {
    throw new Error("候选书目坐标不完整或超出登记边界。");
  }
  return {
    material_request_version:
      RELATION_EFFECT_EVIDENCE_MATERIAL_REQUEST_VERSION,
    expected_receipt_ref: receipt.receipt_ref,
    expected_receipt_hash: receipt.receipt_hash,
    expected_packet_ref: receipt.packet_ref,
    expected_packet_hash: receipt.packet_hash,
    expected_request_item_ref: boundItem.request_item_ref,
    expected_demand_packet_ref: boundItem.demand_packet_ref,
    expected_demand_packet_hash: boundItem.demand_packet_hash,
    expected_slot_ref: boundSlot.slot_ref,
    candidate_kind: "BIBLIOGRAPHIC_COORDINATE_CANDIDATE",
    target_artifact_kind:
      RELATION_EFFECT_EVIDENCE_TARGET_ARTIFACT_KIND,
    bibliography: normalized,
    idempotency_key: [
      "relation-effect-material",
      receipt.receipt_hash.slice(0, 24),
      metadataFingerprint(
        JSON.stringify({
          request_item_ref: boundItem.request_item_ref,
          slot_ref: boundSlot.slot_ref,
          bibliography: normalized,
        }),
      ),
    ].join(":"),
  };
}

export function createRelationEffectEvidenceMaterial(
  receipt: HomeRelationEffectEvidenceRequestReceipt,
  requestItem: HomeRelationEffectEvidenceRequestItem,
  slot: HomeRelationEffectEvidenceRequestedSlot,
  bibliography: RelationEffectEvidenceMaterialBibliography,
): Promise<HomeRelationEffectEvidenceMaterial> {
  return request(ENDPOINT, {
    method: "POST",
    body: JSON.stringify(
      buildRelationEffectEvidenceMaterialPayload(
        receipt,
        requestItem,
        slot,
        bibliography,
      ),
    ),
  });
}

function metadataFingerprint(value: string): string {
  return [
    fnv1a(value, 0x811c9dc5),
    fnv1a(value, 0x9e3779b9),
  ]
    .map((part) => part.toString(16).padStart(8, "0"))
    .join("");
}

function fnv1a(value: string, seed: number): number {
  let hash = seed;
  for (let index = 0; index < value.length; index += 1) {
    hash ^= value.charCodeAt(index);
    hash = Math.imul(hash, 0x01000193);
  }
  return hash >>> 0;
}
