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
import type { FinalVerdictResult, LlmChatMessage, VerdictNarrativeChunk } from "@/features/stream-board/models";
import { calculateFireEnergyAfterConflicts } from "@/features/stream-board/utils";
import { buildBlindSchoolFeaturesPayload } from "./streamBoardPure";
import type { ConfirmedDecisionItem, ConsensusItem } from "./streamBoardTypes";

/** 与后端 `RegenerationContext` 对齐，供 history_context.regeneration_events 审计 */
export type RegenerationContextInput = {
  reason: string;
  trigger: string;
  previous_version_id?: string;
};

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
  regenerationContext?: RegenerationContextInput | null;
};

/** 将终判返回的 metadata_memory_patch 合并进当前 BaziMetadata（浅合并 + 覆盖锚点层）。 */
export function mergeBaziMetadataMemoryPatch(
  base: BaziMetadata | null | undefined,
  patch: Record<string, unknown> | null | undefined,
): BaziMetadata {
  const b = { ...(base || ({} as BaziMetadata)) } as Record<string, unknown>;
  if (!patch || typeof patch !== "object" || Array.isArray(patch)) {
    return b as BaziMetadata;
  }
  const ver = patch.memory_schema_version;
  if (typeof ver === "string" && ver.trim()) b.memory_schema_version = ver.trim();
  const layer = patch.verdict_anchor_layer;
  if (layer && typeof layer === "object" && !Array.isArray(layer)) {
    b.verdict_anchor_layer = layer as BaziMetadata["verdict_anchor_layer"];
  }
  const hcPatch = patch.history_context;
  if (hcPatch && typeof hcPatch === "object" && !Array.isArray(hcPatch)) {
    const inc = hcPatch as {
      regeneration_events?: unknown[];
      confirmed_verdicts?: unknown[];
      verdict_model_stamps?: unknown[];
      learning_annotation?: { schema?: string; entries?: unknown[] };
    };
    const baseHc = { ...(typeof b.history_context === "object" && b.history_context ? b.history_context : {}) } as {
      regeneration_events?: unknown[];
      confirmed_verdicts?: unknown[];
      verdict_model_stamps?: unknown[];
      learning_annotation?: { schema?: string; entries?: unknown[] };
    };
    if (Array.isArray(inc.regeneration_events) && inc.regeneration_events.length > 0) {
      const prev = Array.isArray(baseHc.regeneration_events) ? baseHc.regeneration_events : [];
      baseHc.regeneration_events = [...prev, ...inc.regeneration_events].slice(-48);
    }
    if (Array.isArray(inc.verdict_model_stamps) && inc.verdict_model_stamps.length > 0) {
      const prevS = Array.isArray(baseHc.verdict_model_stamps) ? baseHc.verdict_model_stamps : [];
      baseHc.verdict_model_stamps = [...prevS, ...inc.verdict_model_stamps].slice(-96);
    }
    if (Array.isArray(inc.confirmed_verdicts)) {
      baseHc.confirmed_verdicts = inc.confirmed_verdicts;
    }
    const laInc = inc.learning_annotation;
    if (laInc && typeof laInc === "object" && !Array.isArray(laInc)) {
      const prevLa = baseHc.learning_annotation && typeof baseHc.learning_annotation === "object" ? baseHc.learning_annotation : {};
      const prevEntries = Array.isArray(prevLa.entries) ? prevLa.entries : [];
      const incEntries = Array.isArray((laInc as { entries?: unknown[] }).entries)
        ? (laInc as { entries: unknown[] }).entries
        : [];
      baseHc.learning_annotation = {
        ...prevLa,
        ...laInc,
        entries: [...prevEntries, ...incEntries].slice(-200),
      };
    }
    b.history_context = baseHc as BaziMetadata["history_context"];
  }
  const rfb = patch.reasoning_feedback_loop;
  if (rfb !== undefined && rfb !== null) {
    b.reasoning_feedback_loop = rfb;
  }
  return b as BaziMetadata;
}

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

  const body: Record<string, unknown> = {
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
  const reg = input.regenerationContext;
  if (reg && (String(reg.reason || "").trim() || String(reg.trigger || "").trim())) {
    body.regeneration_context = {
      reason: String(reg.reason || "").slice(0, 480),
      trigger: String(reg.trigger || "").slice(0, 64),
      previous_version_id: String(reg.previous_version_id || "").slice(0, 64),
    };
  }
  return body;
}

function parseNarrativeChunks(raw: unknown): VerdictNarrativeChunk[] | undefined {
  if (!Array.isArray(raw)) return undefined;
  const out: VerdictNarrativeChunk[] = [];
  for (const item of raw) {
    if (!item || typeof item !== "object" || Array.isArray(item)) continue;
    const o = item as Record<string, unknown>;
    out.push({
      chunk_id: String(o.chunk_id ?? ""),
      text: String(o.text ?? ""),
      branch_chars: Array.isArray(o.branch_chars) ? o.branch_chars.map((x) => String(x)) : undefined,
      pillar_keys: Array.isArray(o.pillar_keys) ? o.pillar_keys.map((x) => String(x)) : undefined,
      conflict_point_ids: Array.isArray(o.conflict_point_ids) ? o.conflict_point_ids.map((x) => String(x)) : undefined,
    });
  }
  return out.length ? out : undefined;
}

function parseLlmMessages(raw: unknown): LlmChatMessage[] | undefined {
  if (!Array.isArray(raw)) return undefined;
  const out: LlmChatMessage[] = [];
  for (const item of raw) {
    if (!item || typeof item !== "object" || Array.isArray(item)) continue;
    const o = item as Record<string, unknown>;
    out.push({ role: String(o.role ?? ""), content: String(o.content ?? "") });
  }
  return out;
}

export function parseFinalVerdictFromApiData(data: unknown): FinalVerdictResult | null {
  if (!data || typeof data !== "object" || Array.isArray(data)) return null;
  const d = data as Record<string, unknown>;
  if (typeof d.verdict_body !== "string" || !d.verdict_body) return null;
  const changeLogRaw = d.change_log as Record<string, unknown> | undefined;
  const llmMeta = d.llm_meta && typeof d.llm_meta === "object" && !Array.isArray(d.llm_meta) ? (d.llm_meta as Record<string, unknown>) : undefined;
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
    llmRequestMessages: parseLlmMessages(d.llm_request_messages),
    llmRawResponse: typeof d.llm_raw_response === "string" ? d.llm_raw_response : "",
    llmMeta,
    narrativeChunks: parseNarrativeChunks(d.narrative_chunks),
    metadataMemoryPatch:
      d.metadata_memory_patch && typeof d.metadata_memory_patch === "object" && !Array.isArray(d.metadata_memory_patch)
        ? (d.metadata_memory_patch as Record<string, unknown>)
        : undefined,
  };
}

export function finalVerdictHttpFallbackLog(response: Response, data: unknown): string {
  const detail =
    data && typeof data === "object" && !Array.isArray(data) && "detail" in data
      ? String((data as { detail?: unknown }).detail ?? "unknown")
      : "unknown";
  return `⚠️ 终判接口回退：status=${response.status} detail=${detail}`;
}
