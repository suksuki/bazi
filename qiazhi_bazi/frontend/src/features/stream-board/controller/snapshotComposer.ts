import type { AuditItem } from "@/components/AuditSidebar";
import type {
  FinalVerdictChangeLog,
  InboxCard,
  LlmDiagnosticData,
  SeedPayload,
} from "@/features/stream-board/models";
import { extractInteractionHubMangpai, normalizeDecisionIds, seedPayloadSignature } from "./streamBoardPure";

type HealthState = { dbOk: boolean; llmOk: boolean };

type FinalVerdictShape = {
  body?: string;
  change_log?: FinalVerdictChangeLog;
  logical_evidence?: string[];
  work_vector?: Record<string, unknown> | null;
  topology_graph_v1?: Record<string, unknown> | null;
  structure_candidates_v0?: Record<string, unknown> | null;
  structure_final_decision_v0?: Record<string, unknown> | null;
  version_id?: string;
};

type BuildInteractionHubInput = {
  consultationId: number | null;
  health: HealthState;
  i18nCalls: number;
  auditItems: AuditItem[];
  resultLogs: string[];
  cards: InboxCard[];
  resolvedCardIds: string[];
  llmDiagnosticData: LlmDiagnosticData | null;
};

type BuildInteractionHubOpts = {
  consultationIdOverride?: number | null;
  healthOverride?: HealthState;
  auditorBriefingOverride?: Record<string, unknown> | null;
};

export function buildInteractionHubPayload(
  input: BuildInteractionHubInput,
  opts?: BuildInteractionHubOpts,
): Record<string, unknown> {
  const h = opts?.healthOverride || input.health;
  const briefing = opts?.auditorBriefingOverride || (input.llmDiagnosticData ? {
    alignment_score: input.llmDiagnosticData.alignment_score,
    structured_hit: input.llmDiagnosticData.structured_hit,
    repair_mode: input.llmDiagnosticData.repair_mode,
    top_anomaly: input.llmDiagnosticData.top_anomaly,
    causal_reasoning: input.llmDiagnosticData.causal_reasoning,
    tuning_suggestions: input.llmDiagnosticData.tuning_suggestions,
    logic_proposal: input.llmDiagnosticData.logic_proposal,
    auto_joined_decision_box: Boolean(input.llmDiagnosticData.logic_proposal?.param_key),
  } : null);

  return {
    consultation_id: opts?.consultationIdOverride ?? input.consultationId ?? null,
    health: {
      db_ok: Boolean(h.dbOk),
      llm_ok: Boolean(h.llmOk),
    },
    i18n_calls: input.i18nCalls,
    audit_items: input.auditItems.map((item) => ({
      id: item.id,
      step: item.step || "",
      role: item.role,
      action: item.action,
      timestamp: item.timestamp,
    })),
    result_logs: input.resultLogs.slice(-24),
    pending_cards: input.cards
      .filter((card) => card.id !== "fallback-deep-scan")
      .map((card) => ({
        id: card.id,
        title: card.title,
        card_type: card.cardType || "conflict",
      })),
    resolved_card_ids: input.resolvedCardIds.slice(-120),
    auditor_briefing: briefing || undefined,
  };
}

type PersistSnapshotComposeInput = {
  payload: {
    physics_tensor: Record<string, unknown>;
    metadata?: Record<string, unknown>;
    timeline?: Record<string, unknown> | null;
    llm_prompt?: string;
    audit_summary?: unknown;
    consultationIdOverride?: number | null;
    healthOverride?: HealthState;
    auditorBriefingOverride?: Record<string, unknown> | null;
    seedSignatureOverride?: string | null;
    finalVerdictOverride?: FinalVerdictShape;
  };
  activeSessionId: string | null;
  previousFinalVerdict: Record<string, unknown> | null;
  lastSeedPayload: SeedPayload | null;
  confirmedDecisionIds: string[];
  resolvedCardIds: string[];
  finalVerdictBody: string;
  finalVerdictChangeLog: FinalVerdictChangeLog;
  finalLogicalEvidence: string[];
  finalWorkVector: Record<string, unknown> | null;
  finalTopologyGraphV1: Record<string, unknown> | null;
  finalStructureCandidatesV0: Record<string, unknown> | null;
  finalStructureFinalDecisionV0: Record<string, unknown> | null;
  finalVerdictVersionId: string;
  interactionHubInput: BuildInteractionHubInput;
};

export function composePersistSnapshotPayload(input: PersistSnapshotComposeInput): Record<string, unknown> {
  const { payload } = input;
  const seedSig =
    payload.seedSignatureOverride !== undefined
      ? payload.seedSignatureOverride
      : seedPayloadSignature(input.lastSeedPayload);

  return {
    active_session_id: payload.consultationIdOverride != null
      ? String(payload.consultationIdOverride)
      : (input.activeSessionId || `session-${Date.now()}`),
    physics_tensor: payload.physics_tensor,
    metadata: payload.metadata,
    timeline: payload.timeline ?? null,
    llm_prompt: payload.llm_prompt || "",
    audit_summary: payload.audit_summary,
    ...(seedSig ? { seed_signature: seedSig } : {}),
    resolved_card_ids: input.resolvedCardIds.slice(-240),
    decision_selection_ids: normalizeDecisionIds(input.confirmedDecisionIds),
    interaction_hub: {
      ...buildInteractionHubPayload(input.interactionHubInput, {
        consultationIdOverride: payload.consultationIdOverride,
        healthOverride: payload.healthOverride,
        auditorBriefingOverride: payload.auditorBriefingOverride,
      }),
      ...extractInteractionHubMangpai(payload.physics_tensor),
    },
    final_verdict: payload.finalVerdictOverride || input.previousFinalVerdict || {
      body: input.finalVerdictBody,
      change_log: input.finalVerdictChangeLog,
      logical_evidence: input.finalLogicalEvidence,
      work_vector: input.finalWorkVector,
      topology_graph_v1: input.finalTopologyGraphV1,
      structure_candidates_v0: input.finalStructureCandidatesV0,
      structure_final_decision_v0: input.finalStructureFinalDecisionV0,
      version_id: input.finalVerdictVersionId,
    },
  };
}
