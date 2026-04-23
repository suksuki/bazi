"use client";

import { useState } from "react";

type LooseRecord = Record<string, unknown>;

type Props = {
  pluginCount: number;
  hasAuthoritySource: boolean;
  authority?: LooseRecord;
  climateField?: LooseRecord;
  climateModifierLayer?: LooseRecord;
  climateTheme?: LooseRecord;
  xiangfaTheme?: LooseRecord;
  projectionBridgeProtocol?: LooseRecord;
  relationFormationSummary?: LooseRecord[];
  relationDynamicsSummary?: LooseRecord[];
  tenGodDecomposition?: Record<
    string,
    {
      manifest?: number;
      root?: number;
      momentum?: number;
      momentum_month_order?: number;
      momentum_stage?: number;
      momentum_stage_lu?: number;
      momentum_stage_blade?: number;
      momentum_stage_general?: number;
      momentum_structure?: number;
      momentum_auxiliary?: number;
      momentum_other?: number;
      hidden?: number;
      total?: number;
    }
  >;
};

const fallbackPositionWeights: Array<[string, string]> = [
  ["月柱", "1.00"],
  ["日柱", "0.92"],
  ["时柱", "0.85"],
  ["年柱", "0.72"],
  ["大运", "0.88"],
  ["流年", "0.56"],
];

const fallbackDistanceWeights: Array<[string, string]> = [
  ["同柱", "1.00"],
  ["相邻", "0.78"],
  ["隔柱", "0.52"],
  ["远隔", "0.31"],
];

const designBus = [
  {
    stage: "L0 Static Basis",
    title: "原局静态基线",
    body: "先冻结四柱、大运、流年的结构底图，分离干支、柱位和十神基线，不在这一层做关系互相打压。",
  },
  {
    stage: "L1/L2 Evidence",
    title: "关系与结构证据",
    body: "三合、六合、六冲、格局、风险类插件不直接修改真相，而是输出标准化 work evidence。",
  },
  {
    stage: "Path Engine",
    title: "做功路径传播",
    body: "核心层按柱位权重、远近衰减、运流引动、关系家族和条件态去枚举并传播做功路径。",
  },
  {
    stage: "Effect Resolver",
    title: "效应裁决",
    body: "把路径折算成 benefit / harm / activation / stability，得到每个十神的净效应。",
  },
  {
    stage: "God Ring Authority",
    title: "体用权威输出",
    body: "最终输出用神候选、忌神候选、双刃神和置信度，主页面与 admin 都只消费这份结果。",
  },
];

type TopicHubItem = {
  key: string;
  title: string;
  layer: string;
  status: string;
  tone: "hard" | "structure" | "soft" | "risk" | "muted";
  metrics: string[];
  notes: string[];
};

function asRecord(value: unknown): LooseRecord {
  return value && typeof value === "object" && !Array.isArray(value) ? (value as LooseRecord) : {};
}

function asNumber(value: unknown, fallback = 0): number {
  const next = Number(value);
  return Number.isFinite(next) ? next : fallback;
}

function asStringArray(value: unknown): string[] {
  return Array.isArray(value) ? value.map((item) => String(item || "").trim()).filter(Boolean) : [];
}

function bridgeDirectionLabel(raw: unknown): string {
  const text = String(raw || "").trim();
  if (text === "stem<-branch_hidden") return "天干 <- 地支藏干";
  if (text === "branch_hidden->visible_stem") return "地支藏干 -> 天干";
  return text || "未定义";
}

function formatWeightEntries(
  value: unknown,
  options: {
    fallback: Array<[string, string]>;
    labelMap: Record<string, string>;
  },
): Array<[string, string]> {
  const { fallback, labelMap } = options;
  const row = asRecord(value);
  const entries = Object.entries(row)
    .map(([key, raw]) => [labelMap[key] || key, asNumber(raw).toFixed(2)] as [string, string])
    .filter(([label]) => Boolean(label));
  return entries.length ? entries : fallback;
}

function candidateTone(score: number): string {
  if (score >= 0.75) return "border-emerald-500/30 bg-emerald-950/20 text-emerald-200";
  if (score >= 0.4) return "border-cyan-500/30 bg-cyan-950/20 text-cyan-200";
  return "border-zinc-700 bg-zinc-950/70 text-zinc-300";
}

function topicHubTone(tone: TopicHubItem["tone"]): string {
  if (tone === "hard") return "border-cyan-500/25 bg-cyan-950/20 text-cyan-50";
  if (tone === "structure") return "border-emerald-500/25 bg-emerald-950/20 text-emerald-50";
  if (tone === "soft") return "border-fuchsia-500/25 bg-fuchsia-950/20 text-fuchsia-50";
  if (tone === "risk") return "border-rose-500/25 bg-rose-950/20 text-rose-50";
  return "border-zinc-800 bg-zinc-950/60 text-zinc-300";
}

function topicHubBadgeTone(tone: TopicHubItem["tone"]): string {
  if (tone === "hard") return "border-cyan-500/25 bg-cyan-950/30 text-cyan-100";
  if (tone === "structure") return "border-emerald-500/25 bg-emerald-950/30 text-emerald-100";
  if (tone === "soft") return "border-fuchsia-500/25 bg-fuchsia-950/30 text-fuchsia-100";
  if (tone === "risk") return "border-rose-500/25 bg-rose-950/30 text-rose-100";
  return "border-zinc-700 bg-zinc-900/70 text-zinc-300";
}

function biasPairs(value: unknown): Array<[string, number]> {
  return Object.entries(asRecord(value))
    .map(([god, raw]) => [god, asNumber(raw)] as [string, number])
    .filter(([god, score]) => Boolean(god) && score > 0)
    .sort((left, right) => right[1] - left[1]);
}

function relationFormationRows(value: unknown) {
  if (!Array.isArray(value)) return [];
  return value
    .map((item) => {
      const row = asRecord(item);
      return {
        formationLabel: String(row.formation_label || "").trim(),
        formationPercent: asNumber(row.formation_percent),
        familyFactor: asNumber(row.family_factor),
        status: String(row.status || "").trim(),
        summary: String(row.summary || "").trim(),
      };
    })
    .filter((row) => row.formationLabel && row.formationPercent > 0)
    .sort((left, right) => right.formationPercent - left.formationPercent)
    .slice(0, 6);
}

function relationDynamicsRows(value: unknown) {
  if (!Array.isArray(value)) return [];
  return value
    .map((item) => {
      const row = asRecord(item);
      return {
        label: String(row.label || "").trim(),
        energyAxis: String(row.energy_axis || "").trim(),
        energyEffectRatio: asNumber(row.energy_effect_ratio),
        stabilityDeltaRatio: asNumber(row.stability_delta_ratio),
        freeEnergyLockRatio: asNumber(row.free_energy_lock_ratio),
        note: String(row.note || "").trim(),
        pillars: asStringArray(row.pillars),
      };
    })
    .filter((row) => row.label)
    .sort(
      (left, right) =>
        Math.abs(right.stabilityDeltaRatio) + right.energyEffectRatio - (Math.abs(left.stabilityDeltaRatio) + left.energyEffectRatio),
    )
    .slice(0, 8);
}

function signed(value: number): string {
  return `${value > 0 ? "+" : ""}${value.toFixed(2)}`;
}

function climateGodRows(value: unknown) {
  return Object.entries(asRecord(value))
    .map(([god, raw]) => ({ god: String(god || "").trim(), delta: asNumber(raw) }))
    .filter((row) => row.god && Math.abs(row.delta) > 0.001)
    .sort((left, right) => Math.abs(right.delta) - Math.abs(left.delta))
    .slice(0, 6);
}

function climatePatternRows(value: unknown) {
  if (Array.isArray(value)) {
    return value
      .map((item) => {
        const row = asRecord(item);
        return {
          label: String(row.label || row.key || "").trim(),
          delta: asNumber(row.delta),
          bucket: String(row.bucket || "").trim(),
        };
      })
      .filter((row) => row.label)
      .sort((left, right) => Math.abs(right.delta) - Math.abs(left.delta))
      .slice(0, 4);
  }
  return Object.entries(asRecord(value))
    .map(([label, raw]) => ({ label: String(label || "").trim(), delta: asNumber(raw), bucket: "" }))
    .filter((row) => row.label && Math.abs(row.delta) > 0.001)
    .sort((left, right) => Math.abs(right.delta) - Math.abs(left.delta))
    .slice(0, 4);
}

function climateSourceRows(value: unknown) {
  if (Array.isArray(value)) {
    return value
      .map((item) => {
        const row = asRecord(item);
        const thermal = asNumber(row.thermal);
        const moisture = asNumber(row.moisture);
        return {
          scopeLabel: String(row.scope_label || row.scope || "").trim(),
          thermal,
          moisture,
          dominance: asNumber(row.dominance, Math.abs(thermal) + Math.abs(moisture)),
        };
      })
      .filter((row) => row.scopeLabel)
      .sort((left, right) => right.dominance - left.dominance)
      .slice(0, 4);
  }
  return Object.entries(asRecord(value))
    .map(([scope, raw]) => {
      const row = asRecord(raw);
      const thermal = asNumber(row.thermal);
      const moisture = asNumber(row.moisture);
      return {
        scopeLabel: pillarLabel(String(scope || "").trim()),
        thermal,
        moisture,
        dominance: Math.abs(thermal) + Math.abs(moisture),
      };
    })
    .filter((row) => row.scopeLabel)
    .sort((left, right) => right.dominance - left.dominance)
    .slice(0, 4);
}

function relationDynamicsTone(axis: string, stabilityDeltaRatio: number): string {
  const text = String(axis || "").trim();
  if (text === "激发" || text === "解构") return "border-rose-500/25 bg-rose-950/20 text-rose-200";
  if (text === "内耗" || text === "暗损" || stabilityDeltaRatio < 0) return "border-amber-500/25 bg-amber-950/20 text-amber-200";
  if (text === "绑定" || text === "组织化" || text === "转化") return "border-cyan-500/25 bg-cyan-950/20 text-cyan-200";
  return "border-zinc-700 bg-zinc-950/60 text-zinc-300";
}

function pillarLabel(value: string): string {
  const map: Record<string, string> = {
    year: "年柱",
    month: "月柱",
    day: "日柱",
    hour: "时柱",
    luck: "大运",
    flow: "流年",
  };
  return map[value] || value || "未定";
}

function stageBiasRows(value: unknown) {
  return Object.entries(asRecord(value))
    .map(([god, raw]) => {
      const row = asRecord(raw);
      return {
        god: String(god || "").trim(),
        lu: asNumber(row.lu),
        blade: asNumber(row.blade),
        general: asNumber(row.general),
        useBoost: asNumber(row.use_boost),
        tabooBoost: asNumber(row.taboo_boost),
        stabilityBoost: asNumber(row.stability_boost),
        volatilityBoost: asNumber(row.volatility_boost),
      };
    })
    .filter((row) => row.god && Math.max(row.lu, row.blade, row.general, row.useBoost, row.tabooBoost) > 0)
    .sort(
      (left, right) =>
        right.useBoost + right.tabooBoost + right.lu + right.blade - (left.useBoost + left.tabooBoost + left.lu + left.blade),
    )
    .slice(0, 6);
}

type FluxChainRow = {
  source: string;
  target: string;
  flux: number;
  depth: number;
  eta: number;
  sign: number;
  nodes: string[];
  nodeSource?: string;
  nodeTarget?: string;
  trace: Array<{ source: string; target: string; eta: number; sign: number }>;
};

function fluxChainRows(value: unknown): FluxChainRow[] {
  if (!Array.isArray(value)) return [];
  return value
    .map((item) => {
      const row = asRecord(item);
      return {
        source: String(row.source || "").trim(),
        target: String(row.target || "").trim(),
        flux: asNumber(row.flux),
        depth: asNumber(row.depth),
        eta: asNumber(row.eta_product),
        sign: asNumber(row.sign, 0),
        nodes: asStringArray(row.nodes),
        nodeSource: String(row.node_source || "").trim() || undefined,
        nodeTarget: String(row.node_target || "").trim() || undefined,
        trace: Array.isArray(row.trace)
          ? (row.trace as unknown[])
              .map((traceRow) => {
                const trace = asRecord(traceRow);
                return {
                  source: String(trace.source || "").trim(),
                  target: String(trace.target || "").trim(),
                  eta: asNumber(trace.eta),
                  sign: asNumber(trace.sign, 0),
                };
              })
              .filter((trace) => trace.source && trace.target)
          : [],
      };
    })
    .filter((row) => row.source && row.target)
    .sort((left, right) => Math.abs(right.flux) - Math.abs(left.flux));
}

type FluxNodeEdgeRow = {
  source: string;
  target: string;
  signed: number;
  eta: number;
  sourceGod?: string;
  targetGod?: string;
};

const pillarSequence = ["year", "month", "day", "hour", "luck", "flow"] as const;
const pillarLabelMap: Record<string, string> = {
  year: "年",
  month: "月",
  day: "日",
  hour: "时",
  luck: "运",
  flow: "流",
};
const kindLabelMap: Record<string, string> = {
  stem: "干",
  branch: "支",
};

function fluxNodeEdgeRows(value: unknown): FluxNodeEdgeRow[] {
  if (!Array.isArray(value)) return [];
  return value
    .map((item) => {
      const row = asRecord(item);
      return {
        source: String(row.source || "").trim(),
        target: String(row.target || "").trim(),
        signed: asNumber(row.signed),
        eta: asNumber(row.eta),
        sourceGod: String(row.source_god || "").trim() || undefined,
        targetGod: String(row.target_god || "").trim() || undefined,
      };
    })
    .filter((row) => row.source && row.target);
}

function parseNodeId(nodeId: string) {
  const raw = String(nodeId || "").trim();
  const [pillar, kind] = raw.split("_");
  return {
    nodeId: raw,
    pillar,
    kind,
    pillarLabel: pillarLabelMap[pillar] || pillar || "?",
    kindLabel: kindLabelMap[kind] || kind || "?",
  };
}

function nodeDisplayLabel(nodeId: string): string {
  const parsed = parseNodeId(nodeId);
  return `${parsed.pillarLabel}${parsed.kindLabel}`;
}

function nodeEdgeKey(source: string, target: string): string {
  return `${source}->${target}`;
}

function chainEdgeSet(row: FluxChainRow | undefined): Set<string> {
  const out = new Set<string>();
  if (!row) return out;
  if (row.trace.length) {
    for (const trace of row.trace) {
      out.add(nodeEdgeKey(trace.source, trace.target));
    }
    return out;
  }
  for (let idx = 0; idx < row.nodes.length - 1; idx += 1) {
    out.add(nodeEdgeKey(row.nodes[idx], row.nodes[idx + 1]));
  }
  return out;
}

type FluxSinkRow = {
  god: string;
  benefit: number;
  harm: number;
  net: number;
  chainCount: number;
  topCauses: Array<{
    source: string;
    flux: number;
    ratio: number;
    depth: number;
    nodes: string[];
  }>;
};

function fluxSinkRows(value: unknown): FluxSinkRow[] {
  const bucket = asRecord(value);
  return Object.entries(bucket)
    .map(([god, raw]) => {
      const row = asRecord(raw);
      const topCauses = Array.isArray(row.top_causes)
        ? (row.top_causes as unknown[])
            .map((item) => {
              const cause = asRecord(item);
              return {
                source: String(cause.source || "").trim(),
                flux: asNumber(cause.flux),
                ratio: asNumber(cause.ratio),
                depth: asNumber(cause.depth),
                nodes: asStringArray(cause.nodes),
              };
            })
            .filter((cause) => cause.source)
        : [];
      return {
        god: String(god || "").trim(),
        benefit: asNumber(row.benefit),
        harm: asNumber(row.harm),
        net: asNumber(row.net),
        chainCount: asNumber(row.chain_count),
        topCauses,
      };
    })
    .filter((row) => row.god)
    .sort((left, right) => Math.abs(right.net) - Math.abs(left.net));
}

type FluxInteractionRow = {
  source: string;
  target: string;
  benefit: number;
  harm: number;
  net: number;
  count: number;
  avgDepth: number;
  supportRatio: number;
  resistRatio: number;
  dominance: number;
  polarity: string;
};

function fluxInteractionRows(value: unknown): FluxInteractionRow[] {
  if (!Array.isArray(value)) return [];
  return value
    .map((item) => {
      const row = asRecord(item);
      return {
        source: String(row.source || "").trim(),
        target: String(row.target || "").trim(),
        benefit: asNumber(row.benefit),
        harm: asNumber(row.harm),
        net: asNumber(row.net),
        count: asNumber(row.count),
        avgDepth: asNumber(row.avg_depth),
        supportRatio: asNumber(row.support_ratio),
        resistRatio: asNumber(row.resist_ratio),
        dominance: asNumber(row.dominance),
        polarity: String(row.polarity || "mixed").trim() || "mixed",
      };
    })
    .filter((row) => row.source && row.target)
    .sort((left, right) => Math.abs(right.net) - Math.abs(left.net));
}

type FluxTensionPairRow = {
  left: string;
  right: string;
  leftToRight: number;
  rightToLeft: number;
  mode: string;
  score: number;
  reinforce: number;
  tension: number;
  dominant: number;
};

function fluxTensionPairRows(value: unknown): FluxTensionPairRow[] {
  if (!Array.isArray(value)) return [];
  return value
    .map((item) => {
      const row = asRecord(item);
      return {
        left: String(row.left || "").trim(),
        right: String(row.right || "").trim(),
        leftToRight: asNumber(row.left_to_right),
        rightToLeft: asNumber(row.right_to_left),
        mode: String(row.mode || "tension").trim() || "tension",
        score: asNumber(row.score),
        reinforce: asNumber(row.reinforce),
        tension: asNumber(row.tension),
        dominant: asNumber(row.dominant),
      };
    })
    .filter((row) => row.left && row.right)
    .sort((left, right) => right.score - left.score);
}

export function V17_AdminCoreEnginePanel({
  pluginCount,
  hasAuthoritySource,
  authority,
  climateField,
  climateModifierLayer,
  climateTheme,
  xiangfaTheme,
  projectionBridgeProtocol,
  relationFormationSummary,
  relationDynamicsSummary,
  tenGodDecomposition,
}: Props) {
  const authorityRow = asRecord(authority);
  const climateFieldRow = asRecord(climateField);
  const climateModifierRow = asRecord(climateModifierLayer);
  const climateThemeRow = asRecord(climateTheme);
  const xiangfaThemeRow = asRecord(xiangfaTheme);
  const bridgeProtocol = asRecord(projectionBridgeProtocol);
  const [selectedNodeChainIndex, setSelectedNodeChainIndex] = useState(0);
  const graphMeta = asRecord(authorityRow.core_graph_meta);
  const fluxMeta = asRecord(authorityRow.core_flux_meta);
  const effectScores = asRecord(authorityRow.effect_scores);
  const mode = String(authorityRow.mode || "未接通").trim();
  const confidence = asNumber(authorityRow.confidence);
  const pathCount = asNumber(authorityRow.core_path_count || authorityRow.path_count);
  const fluxEnabled = Boolean(fluxMeta.enabled);
  const fluxEdgeCount = asNumber(fluxMeta.edge_count || graphMeta.flux_edge_count);
  const fluxChainCount = asNumber(fluxMeta.chain_count || graphMeta.flux_chain_count);
  const fluxNodeEdgeCount = asNumber(fluxMeta.node_edge_count || graphMeta.flux_node_edge_count);
  const fluxNodeChainCount = asNumber(fluxMeta.node_chain_count || graphMeta.flux_node_chain_count);
  const fluxProjectedChainCount = asNumber(fluxMeta.projected_chain_count || graphMeta.flux_projected_chain_count);
  const fluxInteractionCount = asNumber(fluxMeta.interaction_count || graphMeta.flux_interaction_count);
  const fluxTensionPairCount = asNumber(fluxMeta.tension_pair_count || graphMeta.flux_tension_pair_count);
  const useGods = asStringArray(authorityRow.use_gods);
  const tabooGods = asStringArray(authorityRow.taboo_gods);
  const useCandidates = Array.isArray(authorityRow.core_use_candidates)
    ? (authorityRow.core_use_candidates as LooseRecord[])
    : [];
  const tabooCandidates = Array.isArray(authorityRow.core_taboo_candidates)
    ? (authorityRow.core_taboo_candidates as LooseRecord[])
    : [];
  const dualRoleCandidates = Array.isArray(authorityRow.dual_role_candidates)
    ? (authorityRow.dual_role_candidates as LooseRecord[])
    : [];
  const pathPreview = Array.isArray(authorityRow.core_paths_preview)
    ? (authorityRow.core_paths_preview as LooseRecord[])
    : [];
  const judgementBias = asRecord(authorityRow.judgement_bias);
  const judgementProtocol = asRecord(authorityRow.judgement_bias_protocol);
  const judgementSummary = asRecord(judgementProtocol.summary);
  const blindTheme = asRecord(authorityRow.blind_theme);
  const blindBias = asRecord(authorityRow.blind_bias);
  const blindProtocol = asRecord(authorityRow.blind_bias_protocol);
  const blindSummary = asRecord(blindProtocol.summary);
  const stageBias = stageBiasRows(authorityRow.stage_bias);
  const stageProtocol = asRecord(authorityRow.stage_bias_protocol);
  const stageSummary = asRecord(stageProtocol.summary);
  const relationRows = relationFormationRows(relationFormationSummary);
  const relationDynamicRows = relationDynamicsRows(relationDynamicsSummary);
  const climateFavored = asStringArray(climateThemeRow.favored_gods);
  const climateStrained = asStringArray(climateThemeRow.strained_gods);
  const climateFocus = climateSourceRows(climateThemeRow.source_focus || climateFieldRow.source_by_scope);
  const climatePattern = climatePatternRows(climateThemeRow.pattern_survival || climateModifierRow.pattern_survival_delta);
  const climateEfficiency = climateGodRows(climateModifierRow.ten_god_efficiency);
  const climateStability = climateGodRows(climateModifierRow.ten_god_stability);
  const climatePriority = climateGodRows(climateModifierRow.yongshen_priority_delta);
  const xiangfaSemantic = asStringArray(xiangfaThemeRow.semantic_mapping);
  const xiangfaEvidence = asStringArray(xiangfaThemeRow.evidence);
  const xiangfaHints = asStringArray(xiangfaThemeRow.narrative_hint);
  const xiangfaFraming = asStringArray(xiangfaThemeRow.event_framing);
  const xiangfaTopics = asStringArray(xiangfaThemeRow.source_topics);
  const judgementUseBias = biasPairs(judgementBias.use_bias).slice(0, 6);
  const judgementTabooBias = biasPairs(judgementBias.taboo_bias).slice(0, 6);
  const blindUseBias = biasPairs(blindBias.use_bias).slice(0, 6);
  const blindTabooBias = biasPairs(blindBias.taboo_bias).slice(0, 6);
  const blindHouseRoles = asRecord(blindTheme.house_roles);
  const blindInside = Object.entries(blindHouseRoles)
    .filter(([, role]) => String(role || "").trim() === "inside")
    .map(([god]) => god);
  const blindOutside = Object.entries(blindHouseRoles)
    .filter(([, role]) => String(role || "").trim() === "outside")
    .map(([god]) => god);
  const blindBridge = Object.entries(blindHouseRoles)
    .filter(([, role]) => String(role || "").trim() === "bridge")
    .map(([god]) => god);
  const blindSwitches = asStringArray(blindProtocol.runtime_switches || blindTheme.runtime_switches).slice(0, 3);
  const judgementBiasEntries = Array.isArray(authorityRow.judgement_bias_entries)
    ? (authorityRow.judgement_bias_entries as LooseRecord[])
        .map((item) => {
          const row = asRecord(item);
          const sourceLabel = String(row.source_label || row.decision_label || row.plugin_id || "").trim();
          const reason = String(row.reason || "").trim();
          const usePairs = biasPairs(row.use_bias);
          const tabooPairs = biasPairs(row.taboo_bias);
          if (!sourceLabel || (!usePairs.length && !tabooPairs.length)) return null;
          return { sourceLabel, reason, usePairs, tabooPairs };
        })
        .filter(Boolean) as Array<{
          sourceLabel: string;
          reason: string;
          usePairs: Array<[string, number]>;
          tabooPairs: Array<[string, number]>;
        }>
    : [];
  const positiveTargets = asRecord(graphMeta.positive_targets);
  const negativeTargets = asRecord(graphMeta.negative_targets);
  const fluxGodChains = fluxChainRows(fluxMeta.top_chains).slice(0, 6);
  const fluxNodeChains = fluxChainRows(fluxMeta.node_top_chains).slice(0, 8);
  const fluxProjectedChains = fluxChainRows(fluxMeta.projected_top_chains).slice(0, 6);
  const fluxSink = fluxSinkRows(fluxMeta.sink_summary).slice(0, 6);
  const fluxInteractions = fluxInteractionRows(fluxMeta.interaction_matrix).slice(0, 8);
  const fluxTensionPairs = fluxTensionPairRows(fluxMeta.tension_pairs).slice(0, 8);
  const fluxNodeEdges = fluxNodeEdgeRows(fluxMeta.node_edges);
  const activeNodeChain = fluxNodeChains[selectedNodeChainIndex] || fluxNodeChains[0];
  const activeNodeEdgeSet = chainEdgeSet(activeNodeChain);
  const activeNodeSet = new Set<string>((activeNodeChain?.nodes || []).map((node) => String(node || "").trim()).filter(Boolean));
  const nodeIdSet = new Set<string>();
  for (const edge of fluxNodeEdges) {
    if (edge.source) nodeIdSet.add(edge.source);
    if (edge.target) nodeIdSet.add(edge.target);
  }
  for (const chain of fluxNodeChains) {
    for (const node of chain.nodes) {
      if (node) nodeIdSet.add(node);
    }
  }
  const nodeIds = Array.from(nodeIdSet)
    .filter(Boolean)
    .sort((left, right) => {
      const l = parseNodeId(left);
      const r = parseNodeId(right);
      const pillarGap = pillarSequence.indexOf(l.pillar as (typeof pillarSequence)[number]) - pillarSequence.indexOf(r.pillar as (typeof pillarSequence)[number]);
      if (pillarGap !== 0) return pillarGap;
      const kindGap = (l.kind === "stem" ? 0 : 1) - (r.kind === "stem" ? 0 : 1);
      if (kindGap !== 0) return kindGap;
      return left.localeCompare(right, "zh-Hans");
    });
  const nodePositions: Record<string, { x: number; y: number }> = {};
  const svgWidth = 680;
  const svgHeight = 220;
  const xStart = 70;
  const xStep = 108;
  const stemY = 66;
  const branchY = 154;
  for (const nodeId of nodeIds) {
    const parsed = parseNodeId(nodeId);
    const pillarIndex = Math.max(0, pillarSequence.indexOf(parsed.pillar as (typeof pillarSequence)[number]));
    nodePositions[nodeId] = {
      x: xStart + xStep * pillarIndex,
      y: parsed.kind === "branch" ? branchY : stemY,
    };
  }

  const positionWeights = formatWeightEntries(graphMeta.position_weights, {
    fallback: fallbackPositionWeights,
    labelMap: { year: "年柱", month: "月柱", day: "日柱", hour: "时柱", luck: "大运", flow: "流年" },
  });
  const distanceWeights = formatWeightEntries(graphMeta.distance_weights, {
    fallback: fallbackDistanceWeights,
    labelMap: { "0": "同柱", "1": "相邻", "2": "隔柱", "3": "远隔" },
  });
  const runtimeFieldProtocol = asRecord(graphMeta.runtime_field_protocol);
  const runtimeAnchorLabel = String(runtimeFieldProtocol.anchor_priority_label || "日柱/日支 > 月柱/月令 > 时柱 > 年柱").trim();
  const runtimeRootScopeWeights = formatWeightEntries(runtimeFieldProtocol.root_scope_weights, {
    fallback: [["大运", "0.92"], ["流年", "0.42"]],
    labelMap: { year: "年柱根域", month: "月柱根域", day: "日柱根域", hour: "时柱根域", luck: "大运根域", flow: "流年根域" },
  });
  const runtimeOriginFactors = formatWeightEntries(runtimeFieldProtocol.work_origin_scope_factors, {
    fallback: [["大运来源", "1.16"], ["流年来源", "0.84"]],
    labelMap: {
      natal: "原局来源",
      natal_basis: "原局基线",
      natal_projection: "原局投影",
      runtime: "运流混合",
      mixed: "运流混合",
      luck: "大运来源",
      flow: "流年来源",
    },
  });
  const dynamicModeProfile = Object.entries(asRecord(graphMeta.dynamic_mode_profile))
    .map(([mode, raw]) => {
      const row = asRecord(raw);
      return {
        mode: String(mode || "").trim(),
        count: asNumber(row.count),
        avgWeight: asNumber(row.avg_weight),
        minPriority: asNumber(row.min_priority, 99),
      };
    })
    .filter((row) => row.mode)
    .sort((left, right) => left.minPriority - right.minPriority || right.avgWeight - left.avgWeight);
  const effectRows = Object.entries(effectScores)
    .map(([god, raw]) => [god, asRecord(raw)] as [string, LooseRecord])
    .sort(
      (left, right) =>
        asNumber(right[1].net_utility) - asNumber(left[1].net_utility) ||
        asNumber(right[1].harm_score) - asNumber(left[1].harm_score),
    )
    .slice(0, 6);
  const decompositionRows = Object.entries(tenGodDecomposition || {})
    .map(([god, raw]) => ({
      god,
      manifest: asNumber(raw?.manifest),
      root: asNumber(raw?.root),
      momentum: asNumber(raw?.momentum),
      momentumMonthOrder: asNumber(raw?.momentum_month_order),
      momentumStage: asNumber(raw?.momentum_stage),
      momentumStageLu: asNumber(raw?.momentum_stage_lu),
      momentumStageBlade: asNumber(raw?.momentum_stage_blade),
      momentumStageGeneral: asNumber(raw?.momentum_stage_general),
      momentumStructure: asNumber(raw?.momentum_structure),
      momentumAuxiliary: asNumber(raw?.momentum_auxiliary),
      momentumOther: asNumber(raw?.momentum_other),
      hidden: asNumber(raw?.hidden),
      total: asNumber(raw?.total),
    }))
    .filter((row) => row.god && row.total > 0)
    .sort((a, b) => b.total - a.total)
    .slice(0, 6);
  const riskStressCount = relationDynamicRows.filter((row) => row.stabilityDeltaRatio < -0.05).length;
  const adminTopicHubItems: TopicHubItem[] = [
    {
      key: "ziping",
      title: "子平主裁决",
      layer: "Level 1 · hard constraint",
      status: hasAuthoritySource ? "已接通" : "fallback",
      tone: hasAuthoritySource ? "hard" : "muted",
      metrics: [
        `用 ${useGods.slice(0, 3).join(" / ") || "未定"}`,
        `忌 ${tabooGods.slice(0, 3).join(" / ") || "未定"}`,
        `候选 ${useCandidates.length + tabooCandidates.length}`,
      ],
      notes: [`模式 ${mode}`, `置信 ${Math.round(confidence * 100)}%`],
    },
    {
      key: "pattern",
      title: "格局/结构增强",
      layer: "Level 2 · structure enhancement",
      status: relationRows.length || climatePattern.length ? "有结构证据" : "等待结构",
      tone: relationRows.length || climatePattern.length ? "structure" : "muted",
      metrics: [
        `成局 ${relationRows.length}`,
        `存续修正 ${climatePattern.length}`,
        `做功路径 ${pathCount}`,
      ],
      notes: relationRows.slice(0, 2).map((row) => `${row.formationLabel} ${row.formationPercent.toFixed(0)}%`),
    },
    {
      key: "climate",
      title: "调候物理轴",
      layer: "L0/L1 field + Level 2 bridge",
      status: String(climateThemeRow.state || climateFieldRow.state || "调候观察"),
      tone: Object.keys(climateFieldRow).length || Object.keys(climateThemeRow).length ? "structure" : "muted",
      metrics: [
        `寒热 ${signed(asNumber(climateThemeRow.thermal_index ?? climateFieldRow.thermal_index))}`,
        `燥湿 ${signed(asNumber(climateThemeRow.moisture_index ?? climateFieldRow.moisture_index))}`,
        `张力 ${asNumber(climateThemeRow.climate_tension ?? climateFieldRow.climate_tension).toFixed(2)}`,
      ],
      notes: [
        ...climateFavored.slice(0, 2).map((god) => `顺势 ${god}`),
        ...climateStrained.slice(0, 2).map((god) => `承压 ${god}`),
      ],
    },
    {
      key: "blind",
      title: "盲派专题",
      layer: "Level 3 · soft bias",
      status: String(blindTheme.primary_route || "盲派未显性"),
      tone: Object.keys(blindTheme).length || blindUseBias.length || blindTabooBias.length ? "soft" : "muted",
      metrics: [
        `体态 ${String(blindTheme.body_mode || "未定")}`,
        `推用 ${blindUseBias.length}`,
        `推忌 ${blindTabooBias.length}`,
      ],
      notes: [`桥接 ${String(blindProtocol.authority_bridge_mode || "bias_only")}`, ...blindSwitches.slice(0, 2)],
    },
    {
      key: "xiangfa",
      title: "象法专题",
      layer: "semantic-only · no bias",
      status: xiangfaSemantic.length || xiangfaEvidence.length ? "已接通" : "语义等待",
      tone: xiangfaSemantic.length || xiangfaEvidence.length ? "soft" : "muted",
      metrics: [
        `语义 ${xiangfaSemantic.length}`,
        `证据 ${xiangfaEvidence.length}`,
        `框架 ${xiangfaFraming.length}`,
      ],
      notes: xiangfaTopics.slice(0, 3).length ? xiangfaTopics.slice(0, 3) : ["不改能量", "不入主分"],
    },
    {
      key: "risk",
      title: "风险/判定矩阵",
      layer: "guard rail · no override",
      status: judgementBiasEntries.length || riskStressCount ? "风险链活跃" : "稳定观察",
      tone: judgementBiasEntries.length || riskStressCount ? "risk" : "muted",
      metrics: [
        `判定偏置 ${judgementBiasEntries.length}`,
        `稳定承压 ${riskStressCount}`,
        `阶段偏置 ${stageBias.length}`,
      ],
      notes: [
        String(judgementSummary.contract || judgementProtocol.contract || "judgement guard").trim(),
        String(stageSummary.contract || stageProtocol.contract || "stage guard").trim(),
      ].filter(Boolean),
    },
  ];

  return (
    <section className="rounded-2xl border border-zinc-800 bg-[radial-gradient(circle_at_top_left,rgba(251,191,36,0.10),transparent_32%),linear-gradient(180deg,rgba(24,24,27,0.88),rgba(9,9,11,0.96))] p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="text-[11px] uppercase tracking-[0.28em] text-amber-300/80">Core Engine</div>
          <h3 className="mt-2 text-sm font-semibold text-zinc-100">Six-Pillar Spacetime Core</h3>
          <p className="mt-1 max-w-3xl text-[11px] leading-6 text-zinc-400">
            这是六柱时空作用核心层，不属于普通插件。它负责柱位权重、距离衰减、做功路径、效应裁决与体用输出。
          </p>
        </div>
        <div className="flex flex-wrap gap-2 text-[10px]">
          <span className="rounded-full border border-zinc-700 bg-zinc-950/70 px-3 py-1 text-zinc-400">
            已接插件 {pluginCount}
          </span>
          <span className={`rounded-full border px-3 py-1 ${hasAuthoritySource ? "border-emerald-500/30 bg-emerald-950/20 text-emerald-300" : "border-amber-500/30 bg-amber-950/20 text-amber-300"}`}>
            {hasAuthoritySource ? "权威体用来源已接通" : "当前仍可能降级到 fallback"}
          </span>
          <span className="rounded-full border border-cyan-500/30 bg-cyan-950/20 px-3 py-1 text-cyan-200">
            模式 {mode}
          </span>
          <span className="rounded-full border border-zinc-700 bg-zinc-950/70 px-3 py-1 text-zinc-300">
            置信 {Math.round(confidence * 100)}%
          </span>
          <span className="rounded-full border border-zinc-700 bg-zinc-950/70 px-3 py-1 text-zinc-300">
            路径 {pathCount}
          </span>
          <span className={`rounded-full border px-3 py-1 ${fluxEnabled ? "border-cyan-500/30 bg-cyan-950/20 text-cyan-200" : "border-zinc-700 bg-zinc-950/70 text-zinc-400"}`}>
            Flux {fluxEnabled ? "M2 已启用" : "未启用"}
          </span>
        </div>
      </div>

      <div className="mt-4 rounded-xl border border-cyan-500/20 bg-[radial-gradient(circle_at_top_left,rgba(34,211,238,0.12),transparent_34%),linear-gradient(180deg,rgba(9,9,11,0.78),rgba(24,24,27,0.62))] p-3">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <div className="text-[10px] uppercase tracking-[0.22em] text-cyan-300">Topic Hub</div>
            <div className="mt-1 text-[12px] font-semibold text-zinc-100">专题状态表</div>
            <p className="mt-1 max-w-3xl text-[10px] leading-5 text-zinc-500">
              这里按 authority 层级展示专题主权：子平是硬约束，格局/调候是结构增强，盲派/象法是软专题，风险只做护栏。
            </p>
          </div>
          <div className="flex flex-wrap gap-1.5 text-[10px]">
            <span className="rounded-full border border-cyan-500/25 bg-cyan-950/20 px-2 py-1 text-cyan-200">
              活跃 {adminTopicHubItems.filter((item) => item.tone !== "muted").length}
            </span>
            <span className="rounded-full border border-emerald-500/25 bg-emerald-950/20 px-2 py-1 text-emerald-200">
              structure {adminTopicHubItems.filter((item) => item.tone === "structure").length}
            </span>
            <span className="rounded-full border border-fuchsia-500/25 bg-fuchsia-950/20 px-2 py-1 text-fuchsia-200">
              soft {adminTopicHubItems.filter((item) => item.tone === "soft").length}
            </span>
          </div>
        </div>
        <div className="mt-3 grid gap-2 md:grid-cols-2 xl:grid-cols-3">
          {adminTopicHubItems.map((item) => (
            <div key={`admin_topic_${item.key}`} className={`rounded-xl border p-3 ${topicHubTone(item.tone)}`}>
              <div className="flex items-start justify-between gap-2">
                <div>
                  <div className="text-[12px] font-semibold">{item.title}</div>
                  <div className="mt-1 text-[9px] uppercase tracking-[0.14em] text-zinc-500">{item.layer}</div>
                </div>
                <span className={`rounded-full border px-2 py-0.5 text-[9px] ${topicHubBadgeTone(item.tone)}`}>
                  {item.status}
                </span>
              </div>
              <div className="mt-3 grid gap-1.5 text-[10px]">
                {item.metrics.map((metric) => (
                  <div key={`admin_topic_metric_${item.key}_${metric}`} className="rounded-lg border border-white/10 bg-black/20 px-2 py-1 text-zinc-300">
                    {metric}
                  </div>
                ))}
              </div>
              {item.notes.length ? (
                <div className="mt-3 flex flex-wrap gap-1.5">
                  {item.notes.slice(0, 4).map((note) => (
                    <span key={`admin_topic_note_${item.key}_${note}`} className={`rounded-full border px-2 py-0.5 text-[9px] ${topicHubBadgeTone(item.tone)}`}>
                      {note}
                    </span>
                  ))}
                </div>
              ) : null}
            </div>
          ))}
        </div>
      </div>

      <div className="mt-4 grid gap-4 xl:grid-cols-[0.95fr,1.05fr]">
        <div className="grid gap-4">
          <div className="rounded-xl border border-zinc-800 bg-zinc-950/60 p-3">
            <div className="mb-3 flex items-center justify-between gap-2">
              <div className="text-[11px] font-semibold text-zinc-300">设计总线</div>
              <div className="text-[10px] text-zinc-500">核心架构可视化</div>
            </div>
            <div className="space-y-2 text-[10px] text-zinc-400">
              {designBus.map((item) => (
                <div key={item.stage} className="rounded-lg border border-zinc-800 bg-zinc-950/60 px-3 py-2">
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-medium text-zinc-100">{item.title}</span>
                    <span className="rounded-full border border-zinc-700 px-2 py-0.5 font-mono text-[9px] text-zinc-400">
                      {item.stage}
                    </span>
                  </div>
                  <p className="mt-1 leading-5 text-zinc-500">{item.body}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="grid gap-4 lg:grid-cols-2">
            <div className="rounded-xl border border-zinc-800 bg-zinc-950/60 p-3">
              <div className="mb-2 text-[11px] font-semibold text-zinc-300">柱位权重</div>
              <div className="grid gap-2 text-[10px] text-zinc-400">
                {positionWeights.map(([label, value]) => (
                  <div key={label} className="flex items-center justify-between rounded-lg border border-zinc-800 bg-zinc-950/60 px-3 py-2">
                    <span>{label}</span>
                    <span className="font-mono text-zinc-200">{value}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="rounded-xl border border-zinc-800 bg-zinc-950/60 p-3">
              <div className="mb-2 text-[11px] font-semibold text-zinc-300">距离衰减</div>
              <div className="grid gap-2 text-[10px] text-zinc-400">
                {distanceWeights.map(([label, value]) => (
                  <div key={label} className="flex items-center justify-between rounded-lg border border-zinc-800 bg-zinc-950/60 px-3 py-2">
                    <span>{label}</span>
                    <span className="font-mono text-zinc-200">{value}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="rounded-xl border border-zinc-800 bg-zinc-950/60 p-3 lg:col-span-2">
              <div className="mb-2 flex items-center justify-between gap-2">
                <div className="text-[11px] font-semibold text-zinc-300">Runtime Field Protocol</div>
                <div className="text-[10px] text-zinc-500">背景场 / 扰动触发 / 运流级联</div>
              </div>
              <div className="flex flex-wrap gap-2 text-[10px]">
                <span className="rounded-full border border-cyan-500/25 bg-cyan-950/20 px-3 py-1 text-cyan-200">
                  锚点顺序 {runtimeAnchorLabel}
                </span>
                <span className="rounded-full border border-emerald-500/25 bg-emerald-950/20 px-3 py-1 text-emerald-200">
                  大运 = 背景场
                </span>
                <span className="rounded-full border border-amber-500/25 bg-amber-950/20 px-3 py-1 text-amber-200">
                  流年 = 年度扰动
                </span>
                <span className="rounded-full border border-fuchsia-500/25 bg-fuchsia-950/20 px-3 py-1 text-fuchsia-200">
                  运流 = runtime_cascade
                </span>
              </div>
              <div className="mt-3 grid gap-4 xl:grid-cols-[0.95fr,1.05fr]">
                <div className="grid gap-4 sm:grid-cols-2">
                  <div>
                    <div className="mb-2 text-[10px] uppercase tracking-[0.16em] text-zinc-500">L0 Root Scope</div>
                    <div className="grid gap-2 text-[10px] text-zinc-400">
                      {runtimeRootScopeWeights.map(([label, value]) => (
                        <div key={label} className="flex items-center justify-between rounded-lg border border-zinc-800 bg-zinc-950/60 px-3 py-2">
                          <span>{label}</span>
                          <span className="font-mono text-zinc-200">{value}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                  <div>
                    <div className="mb-2 text-[10px] uppercase tracking-[0.16em] text-zinc-500">Work Origin</div>
                    <div className="grid gap-2 text-[10px] text-zinc-400">
                      {runtimeOriginFactors.map(([label, value]) => (
                        <div key={label} className="flex items-center justify-between rounded-lg border border-zinc-800 bg-zinc-950/60 px-3 py-2">
                          <span>{label}</span>
                          <span className="font-mono text-zinc-200">{value}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
                <div>
                  <div className="mb-2 text-[10px] uppercase tracking-[0.16em] text-zinc-500">Dynamic Mode Profile</div>
                  <div className="grid gap-2 text-[10px] text-zinc-400">
                    {dynamicModeProfile.length ? dynamicModeProfile.map((row) => (
                      <div key={row.mode} className="rounded-lg border border-zinc-800 bg-zinc-950/60 px-3 py-2">
                        <div className="flex items-center justify-between gap-2">
                          <span className="font-medium text-zinc-100">{row.mode}</span>
                          <span className="font-mono text-cyan-200">avg {row.avgWeight.toFixed(2)}</span>
                        </div>
                        <div className="mt-1 flex flex-wrap gap-2 text-zinc-500">
                          <span>边数 {row.count}</span>
                          <span>优先级 {row.minPriority}</span>
                        </div>
                      </div>
                    )) : (
                      <div className="rounded-lg border border-dashed border-zinc-800 bg-zinc-950/40 px-3 py-4 text-center text-zinc-500">
                        当前尚未产出 dynamic mode profile。
                      </div>
                    )}
                  </div>
                </div>
              </div>
              <p className="mt-2 text-[10px] leading-5 text-zinc-500">
                同一个“运流”概念现在拆成三层职责：L0 的根域权重、Core 图的 dynamic edge、Work Path 的来源域系数。三者不必数值相同，但必须遵守同一套背景场/扰动触发法理。
              </p>
            </div>

            <div className="rounded-xl border border-zinc-800 bg-zinc-950/60 p-3 lg:col-span-2">
              <div className="mb-2 flex items-center justify-between gap-2">
                <div className="text-[11px] font-semibold text-zinc-300">Climate Theme</div>
                <div className="text-[10px] text-zinc-500">调候场 / 主题解释 / 存续修正</div>
              </div>
              <div className="flex flex-wrap gap-2 text-[10px]">
                <span className="rounded-full border border-emerald-500/25 bg-emerald-950/20 px-3 py-1 text-emerald-200">
                  状态 {String(climateThemeRow.state || climateFieldRow.state || "未定")}
                </span>
                <span className="rounded-full border border-amber-500/25 bg-amber-950/20 px-3 py-1 text-amber-200">
                  寒热 {signed(asNumber(climateThemeRow.thermal_index ?? climateFieldRow.thermal_index))}
                </span>
                <span className="rounded-full border border-cyan-500/25 bg-cyan-950/20 px-3 py-1 text-cyan-200">
                  燥湿 {signed(asNumber(climateThemeRow.moisture_index ?? climateFieldRow.moisture_index))}
                </span>
                <span className="rounded-full border border-rose-500/25 bg-rose-950/20 px-3 py-1 text-rose-200">
                  张力 {asNumber(climateThemeRow.climate_tension ?? climateFieldRow.climate_tension).toFixed(2)}
                </span>
              </div>
              {String(climateThemeRow.prompt_digest || "").trim() ? (
                <p className="mt-2 text-[10px] leading-5 text-zinc-400">{String(climateThemeRow.prompt_digest || "").trim()}</p>
              ) : null}
              <div className="mt-3 grid gap-4 xl:grid-cols-[0.92fr,1.08fr]">
                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="rounded-lg border border-zinc-800 bg-zinc-950/60 px-3 py-3">
                    <div className="mb-2 text-[10px] uppercase tracking-[0.16em] text-zinc-500">Favored / Strained</div>
                    <div className="flex flex-wrap gap-2">
                      {climateFavored.slice(0, 3).map((god) => (
                        <span key={`adm_climate_favored_${god}`} className="rounded-full border border-emerald-500/25 bg-emerald-950/20 px-2 py-1 text-[10px] text-emerald-200">
                          顺势 {god}
                        </span>
                      ))}
                      {climateStrained.slice(0, 3).map((god) => (
                        <span key={`adm_climate_strained_${god}`} className="rounded-full border border-rose-500/25 bg-rose-950/20 px-2 py-1 text-[10px] text-rose-200">
                          承压 {god}
                        </span>
                      ))}
                      {!climateFavored.length && !climateStrained.length ? (
                        <span className="text-[10px] text-zinc-500">当前未形成显著十神调候偏向。</span>
                      ) : null}
                    </div>
                    <div className="mt-3 grid gap-2 text-[10px] text-zinc-400">
                      <div className="rounded-lg border border-zinc-800 bg-zinc-950/60 px-3 py-2">
                        <div className="mb-1 text-zinc-500">Efficiency</div>
                        {climateEfficiency.length ? climateEfficiency.slice(0, 3).map((row) => (
                          <div key={`adm_eff_${row.god}`} className="flex items-center justify-between">
                            <span>{row.god}</span>
                            <span className="font-mono text-cyan-200">{signed(row.delta)}</span>
                          </div>
                        )) : <div className="text-zinc-500">暂无修正</div>}
                      </div>
                      <div className="rounded-lg border border-zinc-800 bg-zinc-950/60 px-3 py-2">
                        <div className="mb-1 text-zinc-500">Stability / Priority</div>
                        {climateStability.length || climatePriority.length ? (
                          <div className="space-y-1">
                            {climateStability.slice(0, 2).map((row) => (
                              <div key={`adm_stab_${row.god}`} className="flex items-center justify-between">
                                <span>{row.god} 稳定</span>
                                <span className="font-mono text-amber-200">{signed(row.delta)}</span>
                              </div>
                            ))}
                            {climatePriority.slice(0, 2).map((row) => (
                              <div key={`adm_pri_${row.god}`} className="flex items-center justify-between">
                                <span>{row.god} 优先级</span>
                                <span className="font-mono text-emerald-200">{signed(row.delta)}</span>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <div className="text-zinc-500">暂无修正</div>
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="rounded-lg border border-zinc-800 bg-zinc-950/60 px-3 py-3">
                    <div className="mb-2 text-[10px] uppercase tracking-[0.16em] text-zinc-500">Source Focus</div>
                    <div className="grid gap-2 text-[10px] text-zinc-400">
                      {climateFocus.length ? climateFocus.map((row) => (
                        <div key={`adm_climate_scope_${row.scopeLabel}`} className="rounded-lg border border-zinc-800 bg-zinc-950/60 px-3 py-2">
                          <div className="flex items-center justify-between gap-2">
                            <span className="text-zinc-100">{row.scopeLabel}</span>
                            <span className="font-mono text-zinc-500">{row.dominance.toFixed(2)}</span>
                          </div>
                          <div className="mt-1 flex flex-wrap gap-2">
                            <span className="font-mono text-cyan-200">热 {signed(row.thermal)}</span>
                            <span className="font-mono text-emerald-200">湿 {signed(row.moisture)}</span>
                          </div>
                        </div>
                      )) : (
                        <div className="rounded-lg border border-dashed border-zinc-800 bg-zinc-950/40 px-3 py-4 text-center text-zinc-500">
                          当前尚未产出调候来源焦点。
                        </div>
                      )}
                    </div>
                  </div>
                </div>
                <div className="rounded-lg border border-zinc-800 bg-zinc-950/60 px-3 py-3">
                  <div className="mb-2 text-[10px] uppercase tracking-[0.16em] text-zinc-500">Pattern Survival</div>
                  <div className="grid gap-2 text-[10px] text-zinc-400">
                    {climatePattern.length ? climatePattern.map((row) => (
                      <div key={`adm_climate_pattern_${row.label}`} className="rounded-lg border border-zinc-800 bg-zinc-950/60 px-3 py-2">
                        <div className="flex items-center justify-between gap-2">
                          <span className="text-zinc-100">{row.label}</span>
                          <span className="font-mono text-amber-200">{signed(row.delta)}</span>
                        </div>
                        <div className="mt-1 text-zinc-500">{row.bucket || "存续观察"}</div>
                      </div>
                    )) : (
                      <div className="rounded-lg border border-dashed border-zinc-800 bg-zinc-950/40 px-3 py-4 text-center text-zinc-500">
                        当前尚未产出显著的格局存续修正。
                      </div>
                    )}
                  </div>
                  {asStringArray(climateThemeRow.narrative_focus).length ? (
                    <div className="mt-3 rounded-lg border border-emerald-500/15 bg-emerald-950/10 px-3 py-2 text-[10px] leading-5 text-zinc-300">
                      {asStringArray(climateThemeRow.narrative_focus).slice(0, 4).join(" · ")}
                    </div>
                  ) : null}
                  <p className="mt-2 text-[10px] leading-5 text-zinc-500">
                    调候专题现在只解释 climate field 的下游影响，不直接回写 L0 base totals；真正进入裁决的是 modifier layer。
                  </p>
                </div>
              </div>
            </div>

            <div className="rounded-xl border border-zinc-800 bg-zinc-950/60 p-3 lg:col-span-2">
              <div className="mb-2 flex items-center justify-between gap-2">
                <div className="text-[11px] font-semibold text-zinc-300">Xiangfa Theme</div>
                <div className="text-[10px] text-zinc-500">语义映射 / 证据串 / 事件框架</div>
              </div>
              <div className="flex flex-wrap gap-2 text-[10px]">
                <span className="rounded-full border border-fuchsia-500/25 bg-fuchsia-950/20 px-3 py-1 text-fuchsia-200">
                  semantic-only
                </span>
                <span className="rounded-full border border-zinc-700 bg-zinc-950/70 px-3 py-1 text-zinc-300">
                  不入 bias
                </span>
                <span className="rounded-full border border-zinc-700 bg-zinc-950/70 px-3 py-1 text-zinc-300">
                  不改能量
                </span>
              </div>
              {String(xiangfaThemeRow.prompt_digest || "").trim() ? (
                <p className="mt-2 text-[10px] leading-5 text-zinc-400">{String(xiangfaThemeRow.prompt_digest || "").trim()}</p>
              ) : null}
              <div className="mt-3 grid gap-4 xl:grid-cols-[0.95fr,1.05fr]">
                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="rounded-lg border border-zinc-800 bg-zinc-950/60 px-3 py-3">
                    <div className="mb-2 text-[10px] uppercase tracking-[0.16em] text-zinc-500">Semantic / Framing</div>
                    <div className="space-y-2 text-[10px] leading-5 text-zinc-400">
                      {xiangfaSemantic.length ? (
                        <div>
                          <div className="mb-1 text-zinc-500">Semantic</div>
                          {xiangfaSemantic.slice(0, 3).map((row) => (
                            <div key={`adm_xiangfa_sem_${row}`} className="text-zinc-200">{row}</div>
                          ))}
                        </div>
                      ) : null}
                      {xiangfaFraming.length ? (
                        <div>
                          <div className="mb-1 text-zinc-500">Framing</div>
                          {xiangfaFraming.slice(0, 3).map((row) => (
                            <div key={`adm_xiangfa_frame_${row}`} className="text-zinc-200">{row}</div>
                          ))}
                        </div>
                      ) : null}
                      {!xiangfaSemantic.length && !xiangfaFraming.length ? (
                        <div className="text-zinc-500">当前尚未产出稳定的象法映射。</div>
                      ) : null}
                    </div>
                  </div>
                  <div className="rounded-lg border border-zinc-800 bg-zinc-950/60 px-3 py-3">
                    <div className="mb-2 text-[10px] uppercase tracking-[0.16em] text-zinc-500">Evidence / Hint</div>
                    <div className="space-y-2 text-[10px] leading-5 text-zinc-400">
                      {xiangfaEvidence.length ? (
                        <div>
                          <div className="mb-1 text-zinc-500">Evidence</div>
                          {xiangfaEvidence.slice(0, 3).map((row) => (
                            <div key={`adm_xiangfa_evi_${row}`} className="text-zinc-200">{row}</div>
                          ))}
                        </div>
                      ) : null}
                      {xiangfaHints.length ? (
                        <div>
                          <div className="mb-1 text-zinc-500">Hint</div>
                          {xiangfaHints.slice(0, 2).map((row) => (
                            <div key={`adm_xiangfa_hint_${row}`} className="text-zinc-200">{row}</div>
                          ))}
                        </div>
                      ) : null}
                      {!xiangfaEvidence.length && !xiangfaHints.length ? (
                        <div className="text-zinc-500">当前尚未产出稳定的象法证据串。</div>
                      ) : null}
                    </div>
                  </div>
                </div>
                <div className="rounded-lg border border-zinc-800 bg-zinc-950/60 px-3 py-3">
                  <div className="mb-2 text-[10px] uppercase tracking-[0.16em] text-zinc-500">Source Topics</div>
                  <div className="flex flex-wrap gap-2">
                    {xiangfaTopics.length ? xiangfaTopics.slice(0, 6).map((topic) => (
                      <span key={`adm_xiangfa_topic_${topic}`} className="rounded-full border border-fuchsia-500/20 bg-fuchsia-950/20 px-2 py-1 text-[10px] text-fuchsia-200">
                        {topic}
                      </span>
                    )) : (
                      <span className="text-[10px] text-zinc-500">当前尚未形成象法来源链。</span>
                    )}
                  </div>
                  <p className="mt-3 text-[10px] leading-5 text-zinc-500">
                    象法专题目前只消费 authority、blind、climate、relation 的现成结果，输出语义映射与事件框架，不进入 bias，不覆盖主裁决。
                  </p>
                </div>
              </div>
            </div>

            <div className="rounded-xl border border-zinc-800 bg-zinc-950/60 p-3">
              <div className="mb-2 flex items-center justify-between gap-2">
                <div className="text-[11px] font-semibold text-zinc-300">Projection Bridge Protocol</div>
                <div className="text-[10px] text-zinc-500">通根 / 透干单次耦合</div>
              </div>
              <div className="flex flex-wrap gap-2 text-[10px]">
                <span className="rounded-full border border-cyan-500/25 bg-cyan-950/20 px-3 py-1 text-cyan-200">
                  通根 {bridgeDirectionLabel(bridgeProtocol.tonggen_direction)}
                </span>
                <span className="rounded-full border border-violet-500/25 bg-violet-950/20 px-3 py-1 text-violet-200">
                  透干 {bridgeDirectionLabel(bridgeProtocol.tougan_direction)}
                </span>
                <span className="rounded-full border border-emerald-500/25 bg-emerald-950/20 px-3 py-1 text-emerald-200">
                  同五行先 {bridgeProtocol.same_element_first ? "ON" : "OFF"}
                </span>
                <span className="rounded-full border border-amber-500/25 bg-amber-950/20 px-3 py-1 text-amber-200">
                  阴阳后判 {bridgeProtocol.polarity_second ? "ON" : "OFF"}
                </span>
                <span className="rounded-full border border-zinc-700 bg-zinc-950/70 px-3 py-1 text-zinc-300">
                  {bridgeProtocol.single_pass_coupling ? "单次耦合" : "未声明"}
                </span>
                <span className="rounded-full border border-rose-500/25 bg-rose-950/20 px-3 py-1 text-rose-200">
                  {bridgeProtocol.recursive_feedback ? "允许递归" : "禁止递归"}
                </span>
              </div>
              <div className="mt-3 grid gap-2 text-[10px] text-zinc-400 sm:grid-cols-2 xl:grid-cols-3">
                <div className="rounded-lg border border-zinc-800 bg-zinc-950/60 px-3 py-2">
                  本根 <span className="ml-1 font-mono text-zinc-100">{asNumber(bridgeProtocol.exact_root_support_factor, 1).toFixed(2)}</span>
                </div>
                <div className="rounded-lg border border-zinc-800 bg-zinc-950/60 px-3 py-2">
                  异阴阳根 <span className="ml-1 font-mono text-zinc-100">{asNumber(bridgeProtocol.cross_polarity_root_support_factor).toFixed(2)}</span>
                </div>
                <div className="rounded-lg border border-zinc-800 bg-zinc-950/60 px-3 py-2">
                  精确透干 <span className="ml-1 font-mono text-zinc-100">{asNumber(bridgeProtocol.exact_exposed_hidden_gain).toFixed(2)}</span>
                </div>
                <div className="rounded-lg border border-zinc-800 bg-zinc-950/60 px-3 py-2">
                  同五行可见 <span className="ml-1 font-mono text-zinc-100">{asNumber(bridgeProtocol.same_element_visible_relief).toFixed(2)}</span>
                </div>
                <div className="rounded-lg border border-zinc-800 bg-zinc-950/60 px-3 py-2">
                  通根上限 <span className="ml-1 font-mono text-zinc-100">{asNumber(bridgeProtocol.rooted_gain_cap).toFixed(2)}</span>
                </div>
                <div className="rounded-lg border border-zinc-800 bg-zinc-950/60 px-3 py-2">
                  协议 <span className="ml-1 font-mono text-zinc-100">{String(bridgeProtocol.protocol || "—")}</span>
                </div>
              </div>
              <p className="mt-2 text-[10px] leading-5 text-zinc-500">
                Root 与 Exposed 允许互证，但都只读冻结盘面证据一次；结算后的增强值不会再次回写为新的根/透干依据。
              </p>
            </div>

            {relationRows.length ? (
              <div className="rounded-xl border border-zinc-800 bg-zinc-950/60 p-3">
                <div className="mb-2 flex items-center justify-between gap-2">
                  <div className="text-[11px] font-semibold text-zinc-300">Relation Formation Summary</div>
                  <div className="text-[10px] text-zinc-500">成局度 / 家族基准倍数</div>
                </div>
                <div className="grid gap-2">
                  {relationRows.map((row) => (
                    <div key={row.formationLabel} className="rounded-lg border border-zinc-800 bg-zinc-950/60 px-3 py-2 text-[10px] text-zinc-300">
                      <div className="flex items-center justify-between gap-2">
                        <span className="font-medium text-zinc-100">{row.formationLabel}</span>
                        <span className="font-mono text-amber-200">{row.formationPercent.toFixed(1)}%</span>
                      </div>
                      <div className="mt-1 flex flex-wrap gap-2 text-zinc-500">
                        <span>状态 {row.status || "成局观察"}</span>
                        <span>基准 x{row.familyFactor.toFixed(2)}</span>
                      </div>
                      {row.summary ? <p className="mt-1 leading-5 text-zinc-500">{row.summary}</p> : null}
                    </div>
                  ))}
                </div>
              </div>
            ) : null}

            {relationDynamicRows.length ? (
              <div className="rounded-xl border border-zinc-800 bg-zinc-950/60 p-3">
                <div className="mb-2 flex items-center justify-between gap-2">
                  <div className="text-[11px] font-semibold text-zinc-300">Relation Dynamics Summary</div>
                  <div className="text-[10px] text-zinc-500">能量轴 / 稳定性轴 / 自由能锁定</div>
                </div>
                <div className="grid gap-2">
                  {relationDynamicRows.map((row) => (
                    <div key={row.label} className="rounded-lg border border-zinc-800 bg-zinc-950/60 px-3 py-2 text-[10px] text-zinc-300">
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <span className="font-medium text-zinc-100">{row.label}</span>
                        <span className={`rounded-full border px-2 py-1 ${relationDynamicsTone(row.energyAxis, row.stabilityDeltaRatio)}`}>
                          {row.energyAxis || "动力学观察"}
                        </span>
                      </div>
                      <div className="mt-1 flex flex-wrap gap-2 text-zinc-500">
                        <span>能量 {(row.energyEffectRatio * 100).toFixed(1)}%</span>
                        <span>稳定 {row.stabilityDeltaRatio > 0 ? "+" : ""}{(row.stabilityDeltaRatio * 100).toFixed(1)}%</span>
                        <span>锁定 {(row.freeEnergyLockRatio * 100).toFixed(1)}%</span>
                      </div>
                      {row.pillars.length ? (
                        <div className="mt-1 text-zinc-500">作用柱 {row.pillars.map(pillarLabel).join(" / ")}</div>
                      ) : null}
                      {row.note ? <p className="mt-1 leading-5 text-zinc-500">{row.note}</p> : null}
                    </div>
                  ))}
                </div>
              </div>
            ) : null}
          </div>

          {decompositionRows.length ? (
            <div className="rounded-xl border border-zinc-800 bg-zinc-950/60 p-3">
              <div className="mb-2 flex items-center justify-between gap-2">
                <div className="text-[11px] font-semibold text-zinc-300">十神分解</div>
                <div className="text-[10px] text-zinc-500">显化 / 根气 / 势能细项 / 潜藏</div>
              </div>
              <div className="grid gap-2">
                {decompositionRows.map((row) => (
                  <div key={row.god} className="rounded-lg border border-zinc-800 bg-zinc-950/60 px-3 py-2 text-[10px] text-zinc-300">
                    <div className="flex items-center justify-between gap-2">
                      <span className="font-medium text-zinc-100">{row.god}</span>
                      <span className="font-mono text-cyan-200">{row.total.toFixed(2)}</span>
                    </div>
                    <div className="mt-1 grid grid-cols-2 gap-2 lg:grid-cols-4">
                      <span>显化 {row.manifest.toFixed(2)}</span>
                      <span>根气 {row.root.toFixed(2)}</span>
                      <span>势能 {row.momentum.toFixed(2)}</span>
                      <span>潜藏 {row.hidden.toFixed(2)}</span>
                    </div>
                    <div className="mt-2 flex flex-wrap gap-2 text-[10px] text-zinc-500">
                      <span>月令势 {row.momentumMonthOrder.toFixed(2)}</span>
                      <span>阶段势 {row.momentumStage.toFixed(2)}</span>
                      <span>禄势 {row.momentumStageLu.toFixed(2)}</span>
                      <span>刃势 {row.momentumStageBlade.toFixed(2)}</span>
                      <span>长生势 {row.momentumStageGeneral.toFixed(2)}</span>
                      <span>结构势 {row.momentumStructure.toFixed(2)}</span>
                      <span>辅助势 {row.momentumAuxiliary.toFixed(2)}</span>
                      <span>其他势 {row.momentumOther.toFixed(2)}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : null}

          <div className="grid gap-4 lg:grid-cols-2">
              <div className="rounded-xl border border-zinc-800 bg-zinc-950/60 p-3">
                <div className="mb-2 text-[11px] font-semibold text-zinc-300">体用候选</div>
                <div className="flex flex-wrap gap-2">
                  {(useCandidates.length ? useCandidates : useGods.map((god) => ({ god, score: confidence }))).map((row, idx) => {
                    const god = String((row as LooseRecord).god || "").trim();
                    const score = asNumber((row as LooseRecord).score, confidence);
                    const profile = String((row as LooseRecord).authority_profile || "").trim();
                    return (
                      <div key={`${god}_${idx}`} className={`rounded-full border px-3 py-1 text-[10px] ${candidateTone(score)}`}>
                        <div>用 {god || "未定"} · {Math.round(score * 100)}%</div>
                        {profile ? <div className="mt-0.5 text-[9px] text-zinc-400">{profile}</div> : null}
                      </div>
                    );
                  })}
                </div>
              </div>

              <div className="rounded-xl border border-zinc-800 bg-zinc-950/60 p-3">
                <div className="mb-2 text-[11px] font-semibold text-zinc-300">忌神候选</div>
                <div className="flex flex-wrap gap-2">
                  {(tabooCandidates.length ? tabooCandidates : tabooGods.map((god) => ({ god, score: confidence }))).map((row, idx) => {
                    const god = String((row as LooseRecord).god || "").trim();
                    const score = asNumber((row as LooseRecord).score, confidence);
                    const profile = String((row as LooseRecord).authority_profile || "").trim();
                    return (
                      <div key={`${god}_${idx}`} className="rounded-full border border-rose-500/30 bg-rose-950/20 px-3 py-1 text-[10px] text-rose-200">
                        <div>忌 {god || "未定"} · {Math.round(score * 100)}%</div>
                        {profile ? <div className="mt-0.5 text-[9px] text-zinc-400">{profile}</div> : null}
                      </div>
                    );
                  })}
                </div>
              </div>
          </div>

          {stageBias.length ? (
            <div className="rounded-xl border border-zinc-800 bg-zinc-950/60 p-3">
              <div className="mb-2 flex items-center justify-between gap-2">
                <div className="text-[11px] font-semibold text-zinc-300">禄刃阶段偏置</div>
                <div className="text-[10px] text-zinc-500">
                  {String(stageProtocol.contract || "").trim()
                    ? `${String(stageProtocol.contract || "").trim()} · 条目 ${asNumber(stageSummary.entry_count)}`
                    : "stage bias to authority"}
                </div>
              </div>
              <div className="mb-2 text-[10px] leading-5 text-zinc-500">
                阶段偏置只参与 authority 的承接与波动修正，不直接改写 L0/L1 物理总分。
              </div>
              <div className="grid gap-2 text-[10px] text-zinc-300">
                {stageBias.map((row) => (
                  <div key={`stage_${row.god}`} className="rounded-lg border border-zinc-800 bg-zinc-950/60 px-3 py-2">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <span className="font-medium text-zinc-100">{row.god}</span>
                      <span className="text-zinc-500">
                        禄 {row.lu.toFixed(2)} · 刃 {row.blade.toFixed(2)} · 长生 {row.general.toFixed(2)}
                      </span>
                    </div>
                    <div className="mt-2 flex flex-wrap gap-2">
                      {row.useBoost > 0 ? (
                        <span className="rounded-full border border-emerald-500/30 bg-emerald-950/25 px-3 py-1 text-emerald-200">
                          推用 +{row.useBoost.toFixed(2)}
                        </span>
                      ) : null}
                      {row.tabooBoost > 0 ? (
                        <span className="rounded-full border border-rose-500/30 bg-rose-950/25 px-3 py-1 text-rose-200">
                          推忌 +{row.tabooBoost.toFixed(2)}
                        </span>
                      ) : null}
                      {row.stabilityBoost > 0 ? (
                        <span className="rounded-full border border-cyan-500/30 bg-cyan-950/25 px-3 py-1 text-cyan-200">
                          稳定 +{row.stabilityBoost.toFixed(2)}
                        </span>
                      ) : null}
                      {row.volatilityBoost > 0 ? (
                        <span className="rounded-full border border-amber-500/30 bg-amber-950/25 px-3 py-1 text-amber-200">
                          波动 +{row.volatilityBoost.toFixed(2)}
                        </span>
                      ) : null}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : null}

          {Object.keys(blindTheme).length || blindUseBias.length || blindTabooBias.length ? (
            <div className="rounded-xl border border-zinc-800 bg-zinc-950/60 p-3">
              <div className="mb-2 flex items-center justify-between gap-2">
                <div className="text-[11px] font-semibold text-zinc-300">盲派专题桥接</div>
                <div className="text-[10px] text-zinc-500">
                  {String(blindProtocol.contract || "v17.blind.bias.v1").trim()} · {String(blindProtocol.authority_bridge_mode || "bias_only").trim()}
                </div>
              </div>
              <div className="mb-2 text-[10px] leading-5 text-zinc-500">
                盲派作为并行专题，把主线、家里家外与运行换挡折算成 soft bias，供 authority 参考，不直接改写物理结算。
              </div>
              <div className="flex flex-wrap gap-2 text-[10px]">
                {String(blindTheme.primary_route || "").trim() ? (
                  <span className="rounded-full border border-fuchsia-500/30 bg-fuchsia-950/20 px-3 py-1 text-fuchsia-200">
                    主线 {String(blindTheme.primary_route || "").trim()}
                  </span>
                ) : null}
                {String(blindTheme.body_mode || "").trim() ? (
                  <span className="rounded-full border border-cyan-500/30 bg-cyan-950/20 px-3 py-1 text-cyan-200">
                    体态 {String(blindTheme.body_mode || "").trim()}
                  </span>
                ) : null}
                {asNumber(blindSummary.use_total) > 0 ? (
                  <span className="rounded-full border border-emerald-500/30 bg-emerald-950/20 px-3 py-1 text-emerald-200">
                    推用 +{asNumber(blindSummary.use_total).toFixed(2)}
                  </span>
                ) : null}
                {asNumber(blindSummary.taboo_total) > 0 ? (
                  <span className="rounded-full border border-rose-500/30 bg-rose-950/20 px-3 py-1 text-rose-200">
                    推忌 +{asNumber(blindSummary.taboo_total).toFixed(2)}
                  </span>
                ) : null}
              </div>
              {(blindInside.length || blindOutside.length || blindBridge.length) ? (
                <div className="mt-3 flex flex-wrap gap-2 text-[10px]">
                  {blindInside.length ? (
                    <span className="rounded-full border border-zinc-700 bg-zinc-950/70 px-3 py-1 text-zinc-200">
                      家里 {blindInside.join("/")}
                    </span>
                  ) : null}
                  {blindOutside.length ? (
                    <span className="rounded-full border border-zinc-700 bg-zinc-950/70 px-3 py-1 text-zinc-200">
                      家外 {blindOutside.join("/")}
                    </span>
                  ) : null}
                  {blindBridge.length ? (
                    <span className="rounded-full border border-zinc-700 bg-zinc-950/70 px-3 py-1 text-zinc-200">
                      桥位 {blindBridge.join("/")}
                    </span>
                  ) : null}
                </div>
              ) : null}
              {blindSwitches.length ? (
                <div className="mt-3 rounded-lg border border-zinc-800 bg-zinc-950/60 px-3 py-2 text-[10px] text-zinc-300">
                  换挡：{blindSwitches.join("；")}
                </div>
              ) : null}
              <div className="mt-3 grid gap-3 lg:grid-cols-2">
                <div className="rounded-lg border border-zinc-800 bg-zinc-950/60 p-3">
                  <div className="mb-2 text-[10px] uppercase tracking-[0.16em] text-emerald-300">盲派推用</div>
                  <div className="flex flex-wrap gap-2">
                    {blindUseBias.length ? (
                      blindUseBias.map(([god, score]) => (
                        <span key={`blind_use_${god}`} className="rounded-full border border-emerald-500/30 bg-emerald-950/25 px-3 py-1 text-[10px] text-emerald-200">
                          {god} +{score.toFixed(2)}
                        </span>
                      ))
                    ) : (
                      <span className="text-[11px] text-zinc-500">暂无显著推用。</span>
                    )}
                  </div>
                </div>
                <div className="rounded-lg border border-zinc-800 bg-zinc-950/60 p-3">
                  <div className="mb-2 text-[10px] uppercase tracking-[0.16em] text-rose-300">盲派推忌</div>
                  <div className="flex flex-wrap gap-2">
                    {blindTabooBias.length ? (
                      blindTabooBias.map(([god, score]) => (
                        <span key={`blind_taboo_${god}`} className="rounded-full border border-rose-500/30 bg-rose-950/25 px-3 py-1 text-[10px] text-rose-200">
                          {god} +{score.toFixed(2)}
                        </span>
                      ))
                    ) : (
                      <span className="text-[11px] text-zinc-500">暂无显著推忌。</span>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ) : null}

          <div className="grid gap-4 xl:grid-cols-[0.92fr,1.08fr]">
            <div className="rounded-xl border border-zinc-800 bg-zinc-950/60 p-3">
              <div className="mb-2 flex items-center justify-between gap-2">
                <div className="text-[11px] font-semibold text-zinc-300">判定 Bias 汇总</div>
                <div className="text-[10px] text-zinc-500">
                  {String(judgementProtocol.contract || "").trim()
                    ? `${String(judgementProtocol.contract || "").trim()} · 条目 ${asNumber(judgementSummary.entry_count)} · 目标 ${asNumber(judgementSummary.target_count)}`
                    : "谁在推动体用"}
                </div>
              </div>
              <div className="mb-3 text-[10px] leading-5 text-zinc-500">
                L2 judgement 只输出 bias / evidence / narrative hint，供 authority 参考，不越权改写物理结算。
              </div>
              <div className="grid gap-3 lg:grid-cols-2">
                <div className="rounded-lg border border-zinc-800 bg-zinc-950/60 p-3">
                  <div className="mb-2 text-[10px] uppercase tracking-[0.16em] text-emerald-300">推向用神</div>
                  <div className="flex flex-wrap gap-2">
                    {judgementUseBias.length ? (
                      judgementUseBias.map(([god, score]) => (
                        <span key={`judge_use_${god}`} className="rounded-full border border-emerald-500/30 bg-emerald-950/25 px-3 py-1 text-[10px] text-emerald-200">
                          {god} +{score.toFixed(2)}
                        </span>
                      ))
                    ) : (
                      <span className="text-[11px] text-zinc-500">暂无。</span>
                    )}
                  </div>
                </div>
                <div className="rounded-lg border border-zinc-800 bg-zinc-950/60 p-3">
                  <div className="mb-2 text-[10px] uppercase tracking-[0.16em] text-rose-300">推向忌神</div>
                  <div className="flex flex-wrap gap-2">
                    {judgementTabooBias.length ? (
                      judgementTabooBias.map(([god, score]) => (
                        <span key={`judge_taboo_${god}`} className="rounded-full border border-rose-500/30 bg-rose-950/25 px-3 py-1 text-[10px] text-rose-200">
                          {god} +{score.toFixed(2)}
                        </span>
                      ))
                    ) : (
                      <span className="text-[11px] text-zinc-500">暂无。</span>
                    )}
                  </div>
                </div>
              </div>
            </div>

            <div className="rounded-xl border border-zinc-800 bg-zinc-950/60 p-3">
              <div className="mb-2 flex items-center justify-between gap-2">
                <div className="text-[11px] font-semibold text-zinc-300">判定来源账本</div>
                <div className="text-[10px] text-zinc-500">bias / evidence / narrative hint</div>
              </div>
              <div className="space-y-2 text-[10px] text-zinc-400">
                {judgementBiasEntries.length ? (
                  judgementBiasEntries.slice(0, 6).map((entry, idx) => (
                    <div key={`${entry.sourceLabel}_${idx}`} className="rounded-lg border border-zinc-800 bg-zinc-950/60 px-3 py-2">
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <span className="font-medium text-zinc-100">{entry.sourceLabel}</span>
                        {entry.reason ? <span className="text-zinc-500">{entry.reason}</span> : null}
                      </div>
                      <div className="mt-1 space-y-1">
                        {entry.usePairs.length ? (
                          <div className="break-words text-emerald-200/90">
                            用侧：{entry.usePairs.map(([god, score]) => `${god} +${score.toFixed(2)}`).join(" · ")}
                          </div>
                        ) : null}
                        {entry.tabooPairs.length ? (
                          <div className="break-words text-rose-200/90">
                            忌侧：{entry.tabooPairs.map(([god, score]) => `${god} +${score.toFixed(2)}`).join(" · ")}
                          </div>
                        ) : null}
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="rounded-lg border border-dashed border-zinc-800 bg-zinc-950/40 px-3 py-4 text-center text-zinc-500">
                    当前没有来自判定性插件的 bias 账本。
                  </div>
                )}
              </div>
            </div>
          </div>

          <div className="rounded-xl border border-zinc-800 bg-zinc-950/60 p-3">
            <div className="mb-2 text-[11px] font-semibold text-zinc-300">双刃神 / 动态引动</div>
            <div className="grid gap-2 text-[10px] text-zinc-400 lg:grid-cols-2">
              <div className="rounded-lg border border-zinc-800 bg-zinc-950/60 p-3">
                <div className="mb-2 text-zinc-300">双刃候选</div>
                <div className="flex flex-wrap gap-2">
                  {dualRoleCandidates.length ? dualRoleCandidates.map((row, idx) => {
                    const god = String((row as LooseRecord).god || "").trim();
                    const benefit = asNumber((row as LooseRecord).benefit);
                    const risk = asNumber((row as LooseRecord).risk);
                    return (
                      <span key={`${god}_${idx}`} className="rounded-full border border-fuchsia-500/30 bg-fuchsia-950/20 px-3 py-1 text-[10px] text-fuchsia-200">
                        {god || "未定"} · 利 {benefit.toFixed(2)} / 害 {risk.toFixed(2)}
                      </span>
                    );
                  }) : <span className="text-zinc-500">当前无显著双刃神。</span>}
                </div>
              </div>
              <div className="rounded-lg border border-zinc-800 bg-zinc-950/60 p-3">
                <div className="mb-2 text-zinc-300">引动热区</div>
                <div className="space-y-2">
                  <div className="rounded-lg border border-zinc-800 bg-zinc-950/60 px-3 py-2">
                    <div className="mb-1 text-[10px] text-zinc-500">正向引动</div>
                    <div className="flex flex-wrap gap-2">
                      {Object.keys(positiveTargets).length ? Object.entries(positiveTargets).map(([god, raw]) => (
                        <span key={god} className="rounded-full border border-emerald-500/20 bg-emerald-950/20 px-2 py-1 text-[10px] text-emerald-200">
                          {god} {asNumber(raw).toFixed(2)}
                        </span>
                      )) : <span className="text-zinc-500">暂无。</span>}
                    </div>
                  </div>
                  <div className="rounded-lg border border-zinc-800 bg-zinc-950/60 px-3 py-2">
                    <div className="mb-1 text-[10px] text-zinc-500">负向引动</div>
                    <div className="flex flex-wrap gap-2">
                      {Object.keys(negativeTargets).length ? Object.entries(negativeTargets).map(([god, raw]) => (
                        <span key={god} className="rounded-full border border-amber-500/20 bg-amber-950/20 px-2 py-1 text-[10px] text-amber-200">
                          {god} {asNumber(raw).toFixed(2)}
                        </span>
                      )) : <span className="text-zinc-500">暂无。</span>}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="grid gap-4">
          <div className="rounded-xl border border-zinc-800 bg-zinc-950/60 p-3">
            <div className="mb-3 flex items-center justify-between gap-2">
              <div className="text-[11px] font-semibold text-zinc-300">效应分数面板</div>
              <div className="text-[10px] text-zinc-500">benefit / harm / net utility</div>
            </div>
            <div className="space-y-2 text-[10px] text-zinc-400">
              {effectRows.length ? effectRows.map(([god, row]) => (
                <div key={god} className="rounded-lg border border-zinc-800 bg-zinc-950/60 px-3 py-2">
                  <div className="flex items-center justify-between gap-3">
                    <span className="font-medium text-zinc-100">{god}</span>
                    <span className={`rounded-full px-2 py-0.5 font-mono ${asNumber(row.net_utility) >= 0 ? "bg-emerald-950/30 text-emerald-300" : "bg-rose-950/30 text-rose-300"}`}>
                      net {asNumber(row.net_utility).toFixed(2)}
                    </span>
                  </div>
                  <div className="mt-2 grid gap-2 sm:grid-cols-4">
                    <span>利 {asNumber(row.benefit_score).toFixed(2)}</span>
                    <span>害 {asNumber(row.harm_score).toFixed(2)}</span>
                    <span>激活 {asNumber(row.activation_score).toFixed(2)}</span>
                    <span>稳定 {asNumber(row.stability_score).toFixed(2)}</span>
                  </div>
                  {String(row.authority_profile || "").trim() ? (
                    <div className="mt-2 rounded-lg border border-cyan-500/15 bg-cyan-950/10 px-3 py-2 text-[10px] text-cyan-100/90">
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <span className="font-medium">{String(row.authority_profile || "").trim()}</span>
                        <span>
                          能量 {asNumber(row.authority_energy).toFixed(2)} · 稳定 {asNumber(row.authority_stability).toFixed(2)} · 波动 {asNumber(row.authority_volatility).toFixed(2)}
                        </span>
                      </div>
                      {String(row.authority_reason || "").trim() ? (
                        <div className="mt-1 text-zinc-400">{String(row.authority_reason || "").trim()}</div>
                      ) : null}
                    </div>
                  ) : null}
                </div>
              )) : <div className="rounded-lg border border-dashed border-zinc-800 px-3 py-4 text-zinc-500">当前尚无可视化效应分数。</div>}
            </div>
          </div>

          <div className="rounded-xl border border-zinc-800 bg-zinc-950/60 p-3">
            <div className="mb-3 flex items-center justify-between gap-2">
              <div className="text-[11px] font-semibold text-zinc-300">路径预览</div>
              <div className="text-[10px] text-zinc-500">前 6 条核心做功路径</div>
            </div>
            <div className="space-y-2 text-[10px] text-zinc-400">
              {pathPreview.length ? pathPreview.map((row, idx) => {
                const item = asRecord(row);
                const target = String(item.target_god || "未定").trim();
                const pathType = String(item.path_type || "path").trim();
                const activation = asNumber(item.activation);
                const transmission = asNumber(item.transmission);
                const stability = asNumber(item.stability);
                const net = asNumber(item.net_effect);
                const evidence = asRecord(item.evidence);
                const participants = Array.isArray(item.participants)
                  ? item.participants.map((value) => String(value || "").trim()).filter(Boolean)
                  : [];
                return (
                  <div key={`${pathType}_${target}_${idx}`} className="rounded-lg border border-zinc-800 bg-zinc-950/60 px-3 py-2">
                    <div className="flex items-center justify-between gap-3">
                      <span className="text-zinc-100">{pathType} {"->"} {target}</span>
                      <span className={`rounded-full px-2 py-0.5 font-mono ${net >= 0 ? "bg-emerald-950/30 text-emerald-300" : "bg-rose-950/30 text-rose-300"}`}>
                        {net >= 0 ? "+" : ""}{net.toFixed(2)}
                      </span>
                    </div>
                    <div className="mt-2 flex flex-wrap gap-2 text-[10px] text-zinc-500">
                      {participants.length ? participants.map((value) => (
                        <span key={value} className="rounded-full border border-zinc-800 px-2 py-0.5">{value}</span>
                      )) : <span>无显式参与符号</span>}
                    </div>
                    <div className="mt-2 grid gap-2 sm:grid-cols-4">
                      <span>激活 {activation.toFixed(2)}</span>
                      <span>传导 {transmission.toFixed(2)}</span>
                      <span>稳定 {stability.toFixed(2)}</span>
                      <span>强度 {asNumber(evidence.path_strength).toFixed(2)}</span>
                    </div>
                  </div>
                );
              }) : <div className="rounded-lg border border-dashed border-zinc-800 px-3 py-4 text-zinc-500">当前尚无路径预览。</div>}
            </div>
          </div>

          <div className="rounded-xl border border-zinc-800 bg-zinc-950/60 p-3">
            <div className="mb-3 flex items-center justify-between gap-2">
              <div className="text-[11px] font-semibold text-zinc-300">Dynamic Flux M2</div>
              <div className="text-[10px] text-zinc-500">十神链路 / 柱位链路 / 逆向归因</div>
            </div>
            <div className="mb-3 flex flex-wrap gap-2 text-[10px]">
              <span className="rounded-full border border-zinc-700 bg-zinc-950/70 px-3 py-1 text-zinc-300">
                神边 {fluxEdgeCount}
              </span>
              <span className="rounded-full border border-zinc-700 bg-zinc-950/70 px-3 py-1 text-zinc-300">
                神链 {fluxChainCount}
              </span>
              <span className="rounded-full border border-zinc-700 bg-zinc-950/70 px-3 py-1 text-zinc-300">
                节点边 {fluxNodeEdgeCount}
              </span>
              <span className="rounded-full border border-zinc-700 bg-zinc-950/70 px-3 py-1 text-zinc-300">
                节点链 {fluxNodeChainCount}
              </span>
              <span className="rounded-full border border-zinc-700 bg-zinc-950/70 px-3 py-1 text-zinc-300">
                投影链 {fluxProjectedChainCount}
              </span>
              <span className="rounded-full border border-zinc-700 bg-zinc-950/70 px-3 py-1 text-zinc-300">
                方向矩阵 {fluxInteractionCount}
              </span>
              <span className="rounded-full border border-zinc-700 bg-zinc-950/70 px-3 py-1 text-zinc-300">
                回路 {fluxTensionPairCount}
              </span>
            </div>

            <div className="grid gap-3 xl:grid-cols-2">
              <div className="rounded-lg border border-zinc-800 bg-zinc-950/60 p-3">
                <div className="mb-2 text-[10px] uppercase tracking-[0.16em] text-cyan-300">God Chains</div>
                <div className="space-y-2 text-[10px] text-zinc-400">
                  {fluxGodChains.length ? fluxGodChains.map((row, idx) => (
                    <div key={`god_flux_${row.source}_${row.target}_${idx}`} className="rounded-lg border border-zinc-800 bg-zinc-950/60 px-3 py-2">
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <span className="text-zinc-100">{row.source} {"->"} {row.target}</span>
                        <span className={`rounded-full px-2 py-0.5 font-mono ${row.flux >= 0 ? "bg-emerald-950/30 text-emerald-300" : "bg-rose-950/30 text-rose-300"}`}>
                          {row.flux >= 0 ? "+" : ""}{row.flux.toFixed(3)}
                        </span>
                      </div>
                      <div className="mt-1 text-zinc-500">深度 {row.depth} · η {row.eta.toFixed(3)}</div>
                      {row.nodes.length ? <div className="mt-1 break-words text-zinc-500">{row.nodes.join(" -> ")}</div> : null}
                    </div>
                  )) : <div className="rounded-lg border border-dashed border-zinc-800 px-3 py-3 text-zinc-500">暂无神级链路。</div>}
                </div>
              </div>

              <div className="rounded-lg border border-zinc-800 bg-zinc-950/60 p-3">
                <div className="mb-2 text-[10px] uppercase tracking-[0.16em] text-violet-300">Node Chains</div>
                {fluxNodeChains.length ? (
                  <div className="space-y-3 text-[10px] text-zinc-400">
                    <div className="grid gap-2">
                      {fluxNodeChains.map((row, idx) => (
                        <button
                          type="button"
                          key={`node_flux_${row.source}_${row.target}_${idx}`}
                          onClick={() => setSelectedNodeChainIndex(idx)}
                          className={`w-full rounded-lg border px-3 py-2 text-left transition ${
                            idx === selectedNodeChainIndex
                              ? "border-cyan-500/40 bg-cyan-950/20"
                              : "border-zinc-800 bg-zinc-950/60 hover:border-zinc-700"
                          }`}
                        >
                          <div className="flex flex-wrap items-center justify-between gap-2">
                            <span className="font-mono text-zinc-200">{nodeDisplayLabel(row.source)} {"->"} {nodeDisplayLabel(row.target)}</span>
                            <span className={`rounded-full px-2 py-0.5 font-mono ${row.flux >= 0 ? "bg-emerald-950/30 text-emerald-300" : "bg-rose-950/30 text-rose-300"}`}>
                              {row.flux >= 0 ? "+" : ""}{row.flux.toFixed(3)}
                            </span>
                          </div>
                          <div className="mt-1 break-words text-zinc-500">
                            {row.nodes.map((node) => nodeDisplayLabel(node)).join(" -> ")}
                          </div>
                        </button>
                      ))}
                    </div>

                    <div className="rounded-lg border border-zinc-800 bg-zinc-950/60 p-2">
                      <div className="mb-2 text-[10px] text-zinc-500">
                        节点传导图（选择上方链路后高亮）
                      </div>
                      <svg viewBox={`0 0 ${svgWidth} ${svgHeight}`} className="h-[220px] w-full rounded-md bg-zinc-950/50">
                        {pillarSequence.map((pillar, idx) => (
                          <text
                            key={`pillar_label_${pillar}`}
                            x={xStart + xStep * idx}
                            y={18}
                            textAnchor="middle"
                            className="fill-zinc-500 text-[10px]"
                          >
                            {pillarLabelMap[pillar]}
                          </text>
                        ))}
                        {fluxNodeEdges.map((edge, idx) => {
                          const sourcePos = nodePositions[edge.source];
                          const targetPos = nodePositions[edge.target];
                          if (!sourcePos || !targetPos) return null;
                          const key = nodeEdgeKey(edge.source, edge.target);
                          const highlighted = activeNodeEdgeSet.has(key);
                          const dimmed = Boolean(activeNodeChain) && !highlighted;
                          const positive = edge.signed >= 0;
                          const stroke = positive ? "#34d399" : "#fb7185";
                          return (
                            <line
                              key={`node_edge_${key}_${idx}`}
                              x1={sourcePos.x}
                              y1={sourcePos.y}
                              x2={targetPos.x}
                              y2={targetPos.y}
                              stroke={stroke}
                              strokeWidth={highlighted ? 2.6 : 1.2}
                              opacity={dimmed ? 0.2 : highlighted ? 0.95 : 0.52}
                            />
                          );
                        })}
                        {nodeIds.map((nodeId) => {
                          const pos = nodePositions[nodeId];
                          if (!pos) return null;
                          const parsed = parseNodeId(nodeId);
                          const highlighted = activeNodeSet.has(nodeId);
                          const dimmed = Boolean(activeNodeChain) && !highlighted;
                          const isBranch = parsed.kind === "branch";
                          return (
                            <g key={`node_${nodeId}`}>
                              <circle
                                cx={pos.x}
                                cy={pos.y}
                                r={highlighted ? 14 : 12}
                                fill={isBranch ? "rgba(245, 158, 11, 0.26)" : "rgba(34, 211, 238, 0.22)"}
                                stroke={highlighted ? "#e4e4e7" : isBranch ? "#f59e0b" : "#22d3ee"}
                                strokeWidth={highlighted ? 1.6 : 1.0}
                                opacity={dimmed ? 0.3 : 0.95}
                              />
                              <text x={pos.x} y={pos.y + 3} textAnchor="middle" className="fill-zinc-100 text-[9px]">
                                {nodeDisplayLabel(nodeId)}
                              </text>
                            </g>
                          );
                        })}
                      </svg>
                    </div>
                  </div>
                ) : (
                  <div className="rounded-lg border border-dashed border-zinc-800 px-3 py-3 text-zinc-500">暂无节点级链路。</div>
                )}
              </div>
            </div>

            <div className="mt-3 grid gap-3 xl:grid-cols-2">
              <div className="rounded-lg border border-zinc-800 bg-zinc-950/60 p-3">
                <div className="mb-2 text-[10px] uppercase tracking-[0.16em] text-amber-300">Sink Attribution</div>
                <div className="space-y-2 text-[10px] text-zinc-400">
                  {fluxSink.length ? fluxSink.map((row) => (
                    <div key={`sink_${row.god}`} className="rounded-lg border border-zinc-800 bg-zinc-950/60 px-3 py-2">
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <span className="text-zinc-100">{row.god}</span>
                        <span className={`rounded-full px-2 py-0.5 font-mono ${row.net >= 0 ? "bg-emerald-950/30 text-emerald-300" : "bg-rose-950/30 text-rose-300"}`}>
                          net {row.net.toFixed(3)}
                        </span>
                      </div>
                      <div className="mt-1 text-zinc-500">
                        利 {row.benefit.toFixed(3)} · 害 {row.harm.toFixed(3)} · 链数 {row.chainCount}
                      </div>
                      {row.topCauses.length ? (
                        <div className="mt-1 break-words text-zinc-500">
                          主因：{row.topCauses.slice(0, 2).map((cause) => `${cause.source}(${cause.flux >= 0 ? "+" : ""}${cause.flux.toFixed(3)})`).join(" · ")}
                        </div>
                      ) : null}
                    </div>
                  )) : <div className="rounded-lg border border-dashed border-zinc-800 px-3 py-3 text-zinc-500">暂无归因汇总。</div>}
                </div>
              </div>

              <div className="rounded-lg border border-zinc-800 bg-zinc-950/60 p-3">
                <div className="mb-2 text-[10px] uppercase tracking-[0.16em] text-fuchsia-300">Projected God Chains</div>
                <div className="space-y-2 text-[10px] text-zinc-400">
                  {fluxProjectedChains.length ? fluxProjectedChains.map((row, idx) => (
                    <div key={`proj_flux_${row.source}_${row.target}_${idx}`} className="rounded-lg border border-zinc-800 bg-zinc-950/60 px-3 py-2">
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <span className="text-zinc-100">{row.source} {"->"} {row.target}</span>
                        <span className={`rounded-full px-2 py-0.5 font-mono ${row.flux >= 0 ? "bg-emerald-950/30 text-emerald-300" : "bg-rose-950/30 text-rose-300"}`}>
                          {row.flux >= 0 ? "+" : ""}{row.flux.toFixed(3)}
                        </span>
                      </div>
                      {row.nodes.length ? <div className="mt-1 break-words text-zinc-500">{row.nodes.join(" -> ")}</div> : null}
                    </div>
                  )) : <div className="rounded-lg border border-dashed border-zinc-800 px-3 py-3 text-zinc-500">暂无投影链路。</div>}
                </div>
              </div>
            </div>

            <div className="mt-3 grid gap-3 xl:grid-cols-2">
              <div className="rounded-lg border border-zinc-800 bg-zinc-950/60 p-3">
                <div className="mb-2 text-[10px] uppercase tracking-[0.16em] text-cyan-300">Interaction Matrix</div>
                <div className="space-y-2 text-[10px] text-zinc-400">
                  {fluxInteractions.length ? fluxInteractions.map((row, idx) => (
                    <div key={`inter_${row.source}_${row.target}_${idx}`} className="rounded-lg border border-zinc-800 bg-zinc-950/60 px-3 py-2">
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <span className="text-zinc-100">{row.source} {"->"} {row.target}</span>
                        <span className={`rounded-full px-2 py-0.5 font-mono ${row.net >= 0 ? "bg-emerald-950/30 text-emerald-300" : "bg-rose-950/30 text-rose-300"}`}>
                          {row.net >= 0 ? "+" : ""}{row.net.toFixed(3)}
                        </span>
                      </div>
                      <div className="mt-1 text-zinc-500">
                        利 {row.benefit.toFixed(3)} · 害 {row.harm.toFixed(3)} · 深度 {row.avgDepth.toFixed(2)} · 链数 {row.count}
                      </div>
                      <div className="mt-1 flex flex-wrap gap-2 text-[10px]">
                        <span className="rounded-full border border-emerald-500/20 bg-emerald-950/20 px-2 py-0.5 text-emerald-200">
                          合力 {Math.round(row.supportRatio * 100)}%
                        </span>
                        <span className="rounded-full border border-rose-500/20 bg-rose-950/20 px-2 py-0.5 text-rose-200">
                          抗力 {Math.round(row.resistRatio * 100)}%
                        </span>
                        <span className="rounded-full border border-zinc-700 px-2 py-0.5 text-zinc-300">
                          稳态 {Math.round(row.dominance * 100)}%
                        </span>
                      </div>
                    </div>
                  )) : <div className="rounded-lg border border-dashed border-zinc-800 px-3 py-3 text-zinc-500">暂无方向矩阵。</div>}
                </div>
              </div>

              <div className="rounded-lg border border-zinc-800 bg-zinc-950/60 p-3">
                <div className="mb-2 text-[10px] uppercase tracking-[0.16em] text-fuchsia-300">Loop Tension</div>
                <div className="space-y-2 text-[10px] text-zinc-400">
                  {fluxTensionPairs.length ? fluxTensionPairs.map((row, idx) => {
                    const isReinforce = row.mode === "reinforce";
                    return (
                      <div key={`tension_${row.left}_${row.right}_${idx}`} className="rounded-lg border border-zinc-800 bg-zinc-950/60 px-3 py-2">
                        <div className="flex flex-wrap items-center justify-between gap-2">
                          <span className="text-zinc-100">{row.left} {"<->"} {row.right}</span>
                          <span className={`rounded-full px-2 py-0.5 font-mono ${isReinforce ? "bg-emerald-950/30 text-emerald-300" : "bg-amber-950/30 text-amber-300"}`}>
                            {isReinforce ? "同向放大" : "对冲拉扯"} {row.score.toFixed(3)}
                          </span>
                        </div>
                        <div className="mt-1 break-words text-zinc-500">
                          {row.left} {"->"} {row.right} {row.leftToRight >= 0 ? "+" : ""}{row.leftToRight.toFixed(3)}
                          {" · "}
                          {row.right} {"->"} {row.left} {row.rightToLeft >= 0 ? "+" : ""}{row.rightToLeft.toFixed(3)}
                        </div>
                        <div className="mt-1 text-zinc-500">
                          放大 {row.reinforce.toFixed(3)} · 张力 {row.tension.toFixed(3)} · 主导 {row.dominant.toFixed(3)}
                        </div>
                      </div>
                    );
                  }) : <div className="rounded-lg border border-dashed border-zinc-800 px-3 py-3 text-zinc-500">暂无显著回路。</div>}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
