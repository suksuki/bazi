import type { MingliReadingClaimGraph } from "./mingliClaimGraphTypes";
import type { MingliAgentReading, MingliStageProjection } from "./mingliStageTypes";

const HASH = /^[0-9a-f]{64}$/;
const CLAIM_SEMANTIC_KEY_ORDER = [
  "WHOLE_CHART",
  "DAY_MASTER",
  "HYPOTHESIS_H1",
  "HYPOTHESIS_H2",
  "WORK_PATH",
  "LIFE_IMAGE",
  "DOMAIN_PERSONALITY",
  "DOMAIN_CAREER",
  "DOMAIN_WEALTH",
  "DOMAIN_RELATIONSHIP",
  "DOMAIN_FAMILY",
  "TIMING_NATAL",
  "TIMING_DAYUN",
  "TIMING_ANNUAL",
  "DISCRIMINATING_QUESTION",
] as const;
const CLAIM_ASSESSMENT_CODES = new Set([
  "PRIMARY_HYPOTHESIS_CHART_BASIS_INCOMPLETE",
  "MECHANISM_CANDIDATE_REQUIRES_ADJUDICATION",
  "CONFIDENCE_EXCEEDS_PACKET",
  "DEPENDENCY_WITHHELD",
  "NATAL_CLAIM_CITES_TIMING_EVIDENCE",
  "NATAL_CLAIM_USES_SELECTED_TIMING",
  "TIMING_COORDINATE_EVIDENCE_MISSING",
  "TIMING_RELATION_EVIDENCE_MISSING",
  "RELATION_MEMBERSHIP_PROMOTED_TO_EFFECT",
  "WORK_PATH_CLOSURE_EXCEEDS_PACKET",
  "HIGH_RISK_EVENT_ASSERTION",
  "ROOT_ASSERTION_CONFLICTS_WITH_PACKET",
  "NAMED_COORDINATE_CONFLICTS_WITH_PACKET",
  "UNLISTED_RELATION_COORDINATE_ASSERTION",
  "UNADMITTED_CLASSICAL_ASSERTION",
]);
const SOFT_CLAIM_ASSESSMENT_CODES = new Set([
  "PRIMARY_HYPOTHESIS_CHART_BASIS_INCOMPLETE",
  "MECHANISM_CANDIDATE_REQUIRES_ADJUDICATION",
  "CONFIDENCE_EXCEEDS_PACKET",
  "DEPENDENCY_WITHHELD",
]);
const CLAIM_LAYERS = new Set(["PRINCIPLE", "IMAGE", "THEMES", "TIMING", "QUESTION"]);
const CLAIM_KINDS = new Set([
  "WHOLE_CHART_THESIS",
  "DAY_MASTER_STATE",
  "COMPETING_HYPOTHESIS",
  "WORK_PATH",
  "LIFE_IMAGE",
  "LIFE_DOMAIN",
  "TIMING_BASELINE",
  "TIMING_LAYER",
  "DISCRIMINATING_QUESTION",
]);
const CLAIM_ROLES = new Set(["SYNTHESIS", "PRIMARY", "ALTERNATIVE", "PROJECTION", "QUESTION"]);
const CLAIM_STATUSES = new Set([
  "ESTABLISHED",
  "PROVISIONAL",
  "NEEDS_RECONCILIATION",
  "WITHHELD",
  "OPEN_QUESTION",
]);
const CLAIM_CONFIDENCES = new Set(["LOW", "MEDIUM", "HIGH"]);
const CLAIM_EDGE_RELATIONS = new Set([
  "SUPPORTS",
  "COMPETES_WITH",
  "PROJECTS_TO",
  "TEMPORALLY_EXTENDS",
  "DISCRIMINATES",
]);

export function validateReadingClaimGraph(
  value: unknown,
  stage: MingliStageProjection,
  reading: MingliAgentReading,
): MingliReadingClaimGraph {
  if (!isRecord(value)) {
    throw new Error("mingli_reading_claim_graph_invalid");
  }
  const graph = value as unknown as MingliReadingClaimGraph;
  const claims = Array.isArray(graph.claims) ? graph.claims : [];
  const claimRefs = new Set(claims.map((item) => item.claim_ref));
  const edges = Array.isArray(graph.edges) ? graph.edges : [];
  if (
    graph.graph_version !== "v60.mingli-reading-claim-graph.005"
    || !graph.graph_ref
    || !HASH.test(graph.graph_hash)
    || graph.case_ref !== stage.case_ref
    || graph.chart_version_ref !== stage.chart_version_ref
    || graph.life_case_revision_ref !== stage.life_case_revision_ref
    || graph.reading_ref !== stage.reading_ref
    || graph.reading_hash !== stage.reading_hash
    || graph.agent_reading_ref !== reading.agent_reading_ref
    || graph.agent_reading_hash !== reading.agent_reading_hash
    || graph.packet_ref !== reading.packet_ref
    || graph.packet_hash !== reading.packet_hash
    || graph.agent_profile_ref !== reading.agent_profile_ref
    || graph.agent_profile_hash !== reading.agent_profile_hash
    || graph.model_ref !== reading.model_ref
    || graph.model_digest !== reading.model_digest
    || graph.reasoning_mode !== "BLIND_READING"
    || !graph.reasoning_mode_contract_ref
    || !HASH.test(graph.reasoning_mode_contract_hash)
    || graph.reconciliation_status !== "NOT_ADMITTED"
    || graph.projection_authority !== "DETERMINISTIC_AGENT_READING"
    || graph.qualification_status !== "OWNER_REVIEW_REQUIRED"
    || claims.length !== CLAIM_SEMANTIC_KEY_ORDER.length
    || claims.some((item, index) => claimInvalid(item, index, reading))
    || claimRefs.size !== claims.length
    || edges.length === 0
    || edges.some((edge) => (
      !edge.edge_ref
      || !CLAIM_EDGE_RELATIONS.has(edge.relation)
      || !claimRefs.has(edge.source_claim_ref)
      || !claimRefs.has(edge.target_claim_ref)
      || claims.find((item) => item.claim_ref === edge.source_claim_ref)?.status === "WITHHELD"
      || claims.find((item) => item.claim_ref === edge.target_claim_ref)?.status === "WITHHELD"
    ))
    || graph.owner_review_projection_allowed !== true
    || graph.public_projection_allowed !== false
    || graph.canonical_fact_write_allowed !== false
    || graph.read_only !== true
  ) {
    throw new Error("mingli_reading_claim_graph_shape_invalid");
  }
  return graph;
}

function claimInvalid(
  item: MingliReadingClaimGraph["claims"][number],
  index: number,
  reading: MingliAgentReading,
) {
  return item.semantic_key !== CLAIM_SEMANTIC_KEY_ORDER[index]
    || !item.claim_ref
    || item.source_agent_reading_ref !== reading.agent_reading_ref
    || !CLAIM_LAYERS.has(item.layer)
    || !CLAIM_KINDS.has(item.kind)
    || !CLAIM_ROLES.has(item.role)
    || !CLAIM_STATUSES.has(item.status)
    || typeof item.headline !== "string"
    || typeof item.statement !== "string"
    || !Array.isArray(item.causal_chain)
    || item.causal_chain.some((step) => typeof step !== "string")
    || (item.condition !== null && typeof item.condition !== "string")
    || !Array.isArray(item.evidence_ids)
    || item.evidence_ids.some((evidenceId) => !/^E\d{3}$/.test(evidenceId))
    || !Array.isArray(item.mechanism_evidence_ids)
    || item.mechanism_evidence_ids.some(
      (evidenceId) => !item.evidence_ids.includes(evidenceId),
    )
    || (
      item.coordinate_evidence_id !== null
      && !item.evidence_ids.includes(item.coordinate_evidence_id)
    )
    || !Array.isArray(item.relation_evidence_ids)
    || item.relation_evidence_ids.some(
      (evidenceId) => !item.evidence_ids.includes(evidenceId),
    )
    || (item.confidence !== null && !CLAIM_CONFIDENCES.has(item.confidence))
    || !Array.isArray(item.codes)
    || item.codes.some((code) => typeof code !== "string")
    || !Array.isArray(item.assessment_codes)
    || item.assessment_codes.some((code) => !CLAIM_ASSESSMENT_CODES.has(code))
    || (
      item.status === "WITHHELD"
      && !item.assessment_codes.some(
        (code) => !SOFT_CLAIM_ASSESSMENT_CODES.has(code),
      )
    )
    || (
      item.assessment_codes.length > 0
      && item.assessment_codes.every((code) => SOFT_CLAIM_ASSESSMENT_CODES.has(code))
      && item.status !== "NEEDS_RECONCILIATION"
    )
    || (
      item.assessment_codes.some(
        (code) => !SOFT_CLAIM_ASSESSMENT_CODES.has(code),
      )
      && item.status !== "WITHHELD"
    );
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}
