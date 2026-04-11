import type { AuditItem, AuditRole } from "@/components/AuditSidebar";
import type {
  DeityComponent,
  DeityEnergyAxis,
  FinalVerdictChangeLog,
  LogicDiff,
  LlmDiagnosticData,
  LogicProposal,
  SeedPayload,
} from "@/features/stream-board/models";
import type { LabSnapshot } from "@/features/stream-board/stores/LabSessionContext";
import type { BaziMetadata, TimelineSnapshot } from "@/types/bazi";
import { normalizedSnapshotDecisionIds } from "./streamBoardPure";

export type LabSnapshotHydrationPatch = {
  metadata: BaziMetadata;
  timeline: TimelineSnapshot | null;
  firstPromptText: string;
  consultationId: number | null;
  health?: { dbOk: boolean; llmOk: boolean };
  auditItems?: AuditItem[];
  resultLogs?: string[];
  llmDiagnosticData?: LlmDiagnosticData;
  deityScores?: Record<string, number>;
  deityEnergyAxes?: Record<string, DeityEnergyAxis>;
  deityComponents?: Record<string, DeityComponent>;
  deityTraceDetails?: Record<string, Record<string, unknown>>;
  physicsAudit?: Record<string, unknown> | null;
  physicsConfidence?: number | null;
  physicsEvidence?: string[];
  physicsParams?: Record<string, number>;
  globalEntropy?: number | null;
  finalVerdictBody?: string;
  finalVerdictChangeLog?: FinalVerdictChangeLog;
  finalVerdictVersionId?: string;
  finalLogicalEvidence?: string[];
  finalWorkVector?: Record<string, unknown> | null;
  finalTopologyGraphV1?: Record<string, unknown> | null;
  finalStructureCandidatesV0?: Record<string, unknown> | null;
  finalStructureFinalDecisionV0?: Record<string, unknown> | null;
  resolvedCardIds?: string[];
  confirmedDecisionIds?: string[];
  logicDiff?: LogicDiff;
  lastSeedPayload?: SeedPayload;
};

export function buildLabSnapshotHydrationPatch(
  snap: LabSnapshot | null,
  lastSeedPayload: SeedPayload | null,
): LabSnapshotHydrationPatch | null {
  if (!snap?.metadata) return null;

  const rawMeta = snap.metadata as Record<string, unknown>;
  const points = (rawMeta.conflict_matrix as { points?: unknown } | undefined)?.points;
  const metadata: BaziMetadata = {
    version: String(rawMeta.version ?? "1"),
    pillars: (rawMeta.pillars ?? null) as BaziMetadata["pillars"],
    conflict_matrix: {
      points: Array.isArray(points) ? (points as BaziMetadata["conflict_matrix"]["points"]) : [],
    },
    flow_state: String(rawMeta.flow_state ?? "ready"),
    notes: String(rawMeta.notes ?? ""),
  };

  const hub = snap.interaction_hub;
  let consultationId: number | null = null;
  if (hub?.consultation_id != null && typeof hub.consultation_id === "number") {
    consultationId = hub.consultation_id;
  } else if (snap.active_session_id) {
    const n = Number(String(snap.active_session_id));
    if (Number.isFinite(n)) consultationId = n;
  }

  const patch: LabSnapshotHydrationPatch = {
    metadata,
    timeline: (snap.timeline as TimelineSnapshot) ?? null,
    firstPromptText: String(snap.llm_prompt || ""),
    consultationId,
  };

  if (hub?.health) {
    patch.health = { dbOk: Boolean(hub.health.db_ok), llmOk: Boolean(hub.health.llm_ok) };
  }

  const rawItems = hub?.audit_items;
  if (Array.isArray(rawItems) && rawItems.length > 0) {
    patch.auditItems = rawItems.map((item, idx) => ({
      id: String(item?.id ?? `audit-${idx}`),
      step: item?.step,
      role: (String(item?.role ?? "Core") as AuditRole),
      action: String(item?.action ?? item?.step ?? "—"),
      timestamp: String(item?.timestamp ?? ""),
    }));
  }

  if (Array.isArray(hub?.result_logs)) {
    patch.resultLogs = hub.result_logs.map((x) => String(x));
  }

  const briefing = hub?.auditor_briefing;
  if (briefing && typeof briefing === "object") {
    const b = briefing as Record<string, unknown>;
    const proposal = b.logic_proposal as LogicProposal | undefined;
    patch.llmDiagnosticData = {
      alignment_score: typeof b.alignment_score === "number" ? b.alignment_score : undefined,
      structured_hit: typeof b.structured_hit === "boolean" ? b.structured_hit : undefined,
      repair_mode: b.repair_mode != null ? String(b.repair_mode) : undefined,
      top_anomaly: b.top_anomaly != null ? String(b.top_anomaly) : undefined,
      causal_reasoning: b.causal_reasoning != null ? String(b.causal_reasoning) : undefined,
      tuning_suggestions: Array.isArray(b.tuning_suggestions) ? b.tuning_suggestions.map((x) => String(x)) : undefined,
      logic_proposal: proposal,
      sql_patch: b.sql_patch != null ? String(b.sql_patch) : undefined,
    };
  }

  const tensor = snap.physics_tensor as Record<string, unknown> | undefined;
  if (tensor && typeof tensor === "object") {
    if (tensor.deity_scores && typeof tensor.deity_scores === "object") {
      patch.deityScores = tensor.deity_scores as Record<string, number>;
    }
    if (tensor.deity_energy_axes && typeof tensor.deity_energy_axes === "object") {
      patch.deityEnergyAxes = tensor.deity_energy_axes as Record<string, DeityEnergyAxis>;
    }
    if (tensor.deity_components && typeof tensor.deity_components === "object") {
      patch.deityComponents = tensor.deity_components as Record<string, DeityComponent>;
    }
    if (tensor.deity_trace_details && typeof tensor.deity_trace_details === "object") {
      patch.deityTraceDetails = tensor.deity_trace_details as Record<string, Record<string, unknown>>;
    }
    const pMeta = (tensor.meta || {}) as Record<string, unknown>;
    if (pMeta.deity_trace_details && typeof pMeta.deity_trace_details === "object" && !tensor.deity_trace_details) {
      patch.deityTraceDetails = pMeta.deity_trace_details as Record<string, Record<string, unknown>>;
    }
    if (tensor.audit_log && typeof tensor.audit_log === "object") {
      patch.physicsAudit = tensor.audit_log as Record<string, unknown>;
    }
    patch.physicsConfidence = typeof tensor.confidence === "number" ? tensor.confidence : null;
    if (Array.isArray(tensor.evidence)) {
      patch.physicsEvidence = tensor.evidence.map((x) => String(x));
    } else {
      patch.physicsEvidence = [];
    }
    if (pMeta.params && typeof pMeta.params === "object") {
      patch.physicsParams = pMeta.params as Record<string, number>;
    }
    const ge = pMeta.global_entropy;
    patch.globalEntropy = typeof ge === "number" && Number.isFinite(ge) ? ge : null;
    if (patch.deityTraceDetails === undefined) {
      patch.deityTraceDetails = {};
    }
  }

  const fv = snap.final_verdict;
  if (fv && typeof fv === "object") {
    patch.finalVerdictBody = String(fv.body ?? "");
    patch.finalVerdictChangeLog = (fv.change_log || {}) as FinalVerdictChangeLog;
    patch.finalVerdictVersionId = String(fv.version_id ?? "");
    patch.finalLogicalEvidence = Array.isArray(fv.logical_evidence) ? fv.logical_evidence.map((x) => String(x)) : [];
    patch.finalWorkVector = (fv.work_vector as Record<string, unknown>) || null;
    patch.finalTopologyGraphV1 = (fv.topology_graph_v1 as Record<string, unknown>) || null;
    patch.finalStructureCandidatesV0 = (fv.structure_candidates_v0 as Record<string, unknown>) || null;
    patch.finalStructureFinalDecisionV0 = (fv.structure_final_decision_v0 as Record<string, unknown>) || null;
  }

  if (Array.isArray(snap.resolved_card_ids)) {
    patch.resolvedCardIds = snap.resolved_card_ids.map((x) => String(x));
  }
  const normalizedDecisionIds = normalizedSnapshotDecisionIds(snap.decision_selection_ids);
  if (normalizedDecisionIds.length > 0 || Array.isArray(snap.decision_selection_ids)) {
    patch.confirmedDecisionIds = normalizedDecisionIds;
  }

  const ld = snap.logic_diff;
  if (ld) {
    patch.logicDiff = {
      baseline_abs_loss_total: ld.baseline_abs_loss_total ?? null,
      current_abs_loss_total: ld.current_abs_loss_total ?? null,
      abs_delta: ld.abs_delta ?? null,
      baseline_entropy: ld.baseline_entropy ?? null,
      current_entropy: ld.current_entropy ?? null,
      entropy_delta: ld.entropy_delta ?? null,
    };
  }

  if (lastSeedPayload) {
    patch.lastSeedPayload = lastSeedPayload;
  }

  return patch;
}

export type LabSnapshotHydrationSinks = {
  setMetadata: (v: BaziMetadata) => void;
  setTimeline: (v: TimelineSnapshot | null) => void;
  setFirstPromptText: (v: string) => void;
  setConsultationId: (v: number | null) => void;
  setHealth: (v: { dbOk: boolean; llmOk: boolean }) => void;
  setAuditItems: (v: AuditItem[]) => void;
  setResultLogs: (v: string[]) => void;
  setLlmDiagnosticData: (v: LlmDiagnosticData | null) => void;
  setDeityScores: (v: Record<string, number>) => void;
  setDeityEnergyAxes: (v: Record<string, DeityEnergyAxis>) => void;
  setDeityComponents: (v: Record<string, DeityComponent>) => void;
  setDeityTraceDetails: (v: Record<string, Record<string, unknown>>) => void;
  setPhysicsAudit: (v: Record<string, unknown> | null) => void;
  setPhysicsConfidence: (v: number | null) => void;
  setPhysicsEvidence: (v: string[]) => void;
  setPhysicsParams: (v: Record<string, number>) => void;
  setGlobalEntropy: (v: number | null) => void;
  setFinalVerdictBody: (v: string) => void;
  setFinalVerdictChangeLog: (v: FinalVerdictChangeLog) => void;
  setFinalVerdictVersionId: (v: string) => void;
  setFinalLogicalEvidence: (v: string[]) => void;
  setFinalWorkVector: (v: Record<string, unknown> | null) => void;
  setFinalTopologyGraphV1: (v: Record<string, unknown> | null) => void;
  setFinalStructureCandidatesV0: (v: Record<string, unknown> | null) => void;
  setFinalStructureFinalDecisionV0: (v: Record<string, unknown> | null) => void;
  setResolvedCardIds: (v: string[]) => void;
  setConfirmedDecisionIds: (v: string[]) => void;
  setLogicDiff: (v: LogicDiff) => void;
  setLastSeedPayload: (v: SeedPayload | null) => void;
  setSnapshotAvailable: (v: boolean) => void;
};

export function applyLabSnapshotHydrationPatch(patch: LabSnapshotHydrationPatch, sinks: LabSnapshotHydrationSinks): void {
  sinks.setMetadata(patch.metadata);
  sinks.setTimeline(patch.timeline);
  sinks.setFirstPromptText(patch.firstPromptText);
  sinks.setConsultationId(patch.consultationId);

  if (patch.health !== undefined) sinks.setHealth(patch.health);
  if (patch.auditItems !== undefined) sinks.setAuditItems(patch.auditItems);
  if (patch.resultLogs !== undefined) sinks.setResultLogs(patch.resultLogs);
  if (patch.llmDiagnosticData !== undefined) sinks.setLlmDiagnosticData(patch.llmDiagnosticData);

  if (patch.deityScores !== undefined) sinks.setDeityScores(patch.deityScores);
  if (patch.deityEnergyAxes !== undefined) sinks.setDeityEnergyAxes(patch.deityEnergyAxes);
  if (patch.deityComponents !== undefined) sinks.setDeityComponents(patch.deityComponents);
  if (patch.deityTraceDetails !== undefined) sinks.setDeityTraceDetails(patch.deityTraceDetails);
  if (patch.physicsAudit !== undefined) sinks.setPhysicsAudit(patch.physicsAudit);
  if (patch.physicsConfidence !== undefined) sinks.setPhysicsConfidence(patch.physicsConfidence);
  if (patch.physicsEvidence !== undefined) sinks.setPhysicsEvidence(patch.physicsEvidence);
  if (patch.physicsParams !== undefined) sinks.setPhysicsParams(patch.physicsParams);
  if (patch.globalEntropy !== undefined) sinks.setGlobalEntropy(patch.globalEntropy);

  if (patch.finalVerdictBody !== undefined) sinks.setFinalVerdictBody(patch.finalVerdictBody);
  if (patch.finalVerdictChangeLog !== undefined) sinks.setFinalVerdictChangeLog(patch.finalVerdictChangeLog);
  if (patch.finalVerdictVersionId !== undefined) sinks.setFinalVerdictVersionId(patch.finalVerdictVersionId);
  if (patch.finalLogicalEvidence !== undefined) sinks.setFinalLogicalEvidence(patch.finalLogicalEvidence);
  if (patch.finalWorkVector !== undefined) sinks.setFinalWorkVector(patch.finalWorkVector);
  if (patch.finalTopologyGraphV1 !== undefined) sinks.setFinalTopologyGraphV1(patch.finalTopologyGraphV1);
  if (patch.finalStructureCandidatesV0 !== undefined) sinks.setFinalStructureCandidatesV0(patch.finalStructureCandidatesV0);
  if (patch.finalStructureFinalDecisionV0 !== undefined) {
    sinks.setFinalStructureFinalDecisionV0(patch.finalStructureFinalDecisionV0);
  }

  if (patch.resolvedCardIds !== undefined) sinks.setResolvedCardIds(patch.resolvedCardIds);
  if (patch.confirmedDecisionIds !== undefined) sinks.setConfirmedDecisionIds(patch.confirmedDecisionIds);
  if (patch.logicDiff !== undefined) sinks.setLogicDiff(patch.logicDiff);
  if (patch.lastSeedPayload) sinks.setLastSeedPayload(patch.lastSeedPayload);

  sinks.setSnapshotAvailable(true);
}
