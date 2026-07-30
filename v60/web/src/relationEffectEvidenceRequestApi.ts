import { request } from "./http";
import type { HomeRelationEffectEvidencePacketEnvelope } from "./homeRelationEffectEvidencePacketTypes";
import {
  RELATION_EFFECT_EVIDENCE_REQUEST_VERSION,
  type HomeRelationEffectEvidenceRequestReceipt,
  type RelationEffectEvidenceRequestPayload,
} from "./homeRelationEffectEvidenceRequestTypes";

const ENDPOINT =
  "/api/v60/experience/home/relation-effect-evidence-request";

export function buildRelationEffectEvidenceRequestPayload(
  packet: HomeRelationEffectEvidencePacketEnvelope,
): RelationEffectEvidenceRequestPayload {
  return {
    request_version: RELATION_EFFECT_EVIDENCE_REQUEST_VERSION,
    expected_packet_ref: packet.packet_ref,
    expected_packet_hash: packet.packet_hash,
    idempotency_key: [
      RELATION_EFFECT_EVIDENCE_REQUEST_VERSION,
      packet.packet_ref,
    ].join(":"),
  };
}

export function createRelationEffectEvidenceRequest(
  packet: HomeRelationEffectEvidencePacketEnvelope,
): Promise<HomeRelationEffectEvidenceRequestReceipt> {
  return request(ENDPOINT, {
    method: "POST",
    body: JSON.stringify(
      buildRelationEffectEvidenceRequestPayload(packet),
    ),
  });
}
