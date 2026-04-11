import type { BaziMetadata, Lang } from "@/types/bazi";
import type {
  DeityComponent,
  DeityEnergyAxis,
  FinalVerdictChangeLog,
  InboxCard,
  LlmDiagnosticData,
  PluginSwitches,
  PluginWeights,
  SeedPayload,
} from "@/features/stream-board/models";
import type { FinalVerdictResult } from "@/features/stream-board/models";
import { calculateFireEnergyAfterConflicts } from "@/features/stream-board/utils";
import { buildBlindSchoolFeaturesPayload } from "./streamBoardPure";
import type { ConfirmedDecisionItem, ConsensusItem } from "./streamBoardTypes";

export type FinalVerdictRequestBuildInput = {
  metadata: BaziMetadata | null;
  deityScores: Record<string, number>;
  deityEnergyAxes: Record<string, DeityEnergyAxis>;
  deityComponents: Record<string, DeityComponent>;
  deityTraceDetails: Record<string, Record<string, unknown>>;
  physicsAudit: Record<string, unknown> | null;
  llmDiagnosticData: LlmDiagnosticData | null;
  timeline: Record<string, unknown> | null;
  conflicts: string[];
  selectedCards: InboxCard[];
  consensusHistory: ConsensusItem[];
  finalVerdictBody: string;
  lastConclusionText: string;
  finalLogicalEvidence: string[];
  consultationId: number | null;
  pluginSwitches: PluginSwitches;
  pluginWeights: PluginWeights;
  lang: Lang;
};

export function buildFinalVerdictRequestBody(input: FinalVerdictRequestBuildInput): Record<string, unknown> {
  const selectedPayload = input.selectedCards.map((card) => ({
    id: card.id,
    title: card.title,
    cardType: card.cardType || "conflict",
    displayText: card.displayText || card.conflictDetail || card.title,
  }));

  const absNodesFromAxes = Object.fromEntries(
    Object.entries(input.deityEnergyAxes || {}).map(([name, axis]) => [
      name,
      Number((axis && typeof axis === "object" ? axis.absolute_energy : 0) || 0),
    ]),
  );
  const absNodesFromScores = Object.fromEntries(
    Object.entries(input.deityScores || {}).map(([name, score]) => [name, Number(score || 0)]),
  );
  const absNodes = Object.keys(absNodesFromAxes).length > 0 ? absNodesFromAxes : absNodesFromScores;

  return {
    metadata: input.metadata || {},
    physics_tensor: {
      abs_nodes: absNodes,
      deity_scores: input.deityScores,
      deity_energy_axes: input.deityEnergyAxes,
      deity_components: input.deityComponents,
      deity_trace_details: input.deityTraceDetails,
      audit_log: input.physicsAudit || {},
      top_anomaly: input.llmDiagnosticData?.top_anomaly || "",
      causal_reasoning: input.llmDiagnosticData?.causal_reasoning || "",
      tuning_suggestions: input.llmDiagnosticData?.tuning_suggestions || [],
      timeline: input.timeline || {},
      conflict_list: input.conflicts || [],
      fire_energy_after_conflict: calculateFireEnergyAfterConflicts(input.metadata?.pillars, input.conflicts),
      meta: {
        enabled_plugins: [
          ...(input.pluginSwitches.blindSchool ? ["classical.blind_school.v1"] : []),
          ...(input.pluginSwitches.wangshuai ? ["classical.wangshuai.v1"] : []),
          ...(input.pluginSwitches.wealthRisk ? ["modern.wealth_risk.v1"] : []),
        ],
        blind_school_features: buildBlindSchoolFeaturesPayload(input.pluginSwitches),
      },
    },
    selected_cards: selectedPayload,
    consensus_history: input.consensusHistory,
    previous_verdict: input.finalVerdictBody || input.lastConclusionText || "",
    previous_logical_evidence: input.finalLogicalEvidence,
    consultation_id: input.consultationId ?? undefined,
    clear_previous_verdict: true,
    force_clear_cache: true,
    enabled_plugins: [
      ...(input.pluginSwitches.blindSchool ? ["classical.blind_school.v1"] : []),
      ...(input.pluginSwitches.wangshuai ? ["classical.wangshuai.v1"] : []),
      ...(input.pluginSwitches.wealthRisk ? ["modern.wealth_risk.v1"] : []),
    ],
    plugin_weights: {
      "classical.blind_school.v1": Number(input.pluginWeights.blindSchool || 0),
      "classical.wangshuai.v1": Number(input.pluginWeights.wangshuai || 0),
    },
    lang: input.lang,
  };
}

export function parseFinalVerdictFromApiData(data: unknown): FinalVerdictResult | null {
  if (!data || typeof data !== "object" || Array.isArray(data)) return null;
  const d = data as Record<string, unknown>;
  if (typeof d.verdict_body !== "string" || !d.verdict_body) return null;
  const changeLogRaw = d.change_log as Record<string, unknown> | undefined;
  return {
    body: String(d.verdict_body),
    changeLog: {
      physics_diff: Array.isArray(changeLogRaw?.physics_diff)
        ? changeLogRaw.physics_diff.map((item: unknown) => String(item))
        : [],
      consensus_diff: Array.isArray(changeLogRaw?.consensus_diff)
        ? changeLogRaw.consensus_diff.map((item: unknown) => String(item))
        : [],
      text_diff_hint: String(changeLogRaw?.text_diff_hint || ""),
    },
    logicalEvidence: Array.isArray(d.logical_evidence) ? d.logical_evidence.map((item: unknown) => String(item)) : [],
    versionId: String(d.version_id || ""),
    workVector: d.work_vector && typeof d.work_vector === "object" ? (d.work_vector as Record<string, unknown>) : {},
    topologyGraphV1:
      d.topology_graph_v1 && typeof d.topology_graph_v1 === "object"
        ? (d.topology_graph_v1 as Record<string, unknown>)
        : {},
    structureCandidatesV0:
      d.structure_candidates_v0 && typeof d.structure_candidates_v0 === "object"
        ? (d.structure_candidates_v0 as Record<string, unknown>)
        : {},
    structureFinalDecisionV0:
      d.structure_final_decision_v0 && typeof d.structure_final_decision_v0 === "object"
        ? (d.structure_final_decision_v0 as Record<string, unknown>)
        : {},
    auditLog: d.audit_log && typeof d.audit_log === "object" ? (d.audit_log as Record<string, unknown>) : {},
    confirmedDecisions: Array.isArray(d.confirmed_decisions)
      ? d.confirmed_decisions
          .filter((item: unknown) => item && typeof item === "object")
          .map((item: unknown) => {
            const obj = item as Record<string, unknown>;
            return {
              id: String(obj.id || ""),
              label: String(obj.label || ""),
              is_confirmed: Boolean(obj.is_confirmed),
              confirmed_at: typeof obj.confirmed_at === "string" ? obj.confirmed_at : undefined,
            };
          })
          .filter((item: ConfirmedDecisionItem) => item.id)
      : [],
  };
}

export function finalVerdictHttpFallbackLog(response: Response, data: unknown): string {
  const detail =
    data && typeof data === "object" && !Array.isArray(data) && "detail" in data
      ? String((data as { detail?: unknown }).detail ?? "unknown")
      : "unknown";
  return `⚠️ 终判接口回退：status=${response.status} detail=${detail}`;
}
