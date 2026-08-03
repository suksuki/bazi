import type {
  MingliReadingClaim,
  MingliReadingClaimGraph,
  MingliReadingClaimSemanticKey,
} from "./mingliClaimGraphTypes";
import { claimStatusLabel } from "./mingliClaimPresentation";
import type { MingliReadingLayer } from "./mingliStageNavigation";
import type { MingliNarrationCue } from "./mingliStageTypes";

export interface MingliLayerNarrationChapter {
  chapterId: string;
  claimRef: string;
  eyebrow: string;
  title: string;
  text: string;
  evidenceLine: string | null;
  condition: string | null;
  statusLabel: string;
  semanticAction: MingliNarrationCue["semantic_action"];
}

export interface MingliLayerNarrationProjection {
  graphRef: string;
  graphHash: string;
  layer: MingliReadingLayer;
  layerLabel: string;
  notice: string | null;
  chapters: MingliLayerNarrationChapter[];
}

const LAYER_LABELS: Record<MingliReadingLayer, string> = {
  principle: "命局原理",
  image: "生命意象",
  themes: "人生主题",
  timing: "时间趋势",
};

const CLAIM_LABELS: Partial<Record<MingliReadingClaimSemanticKey, string>> = {
  WHOLE_CHART: "整盘总纲",
  DAY_MASTER: "日主状态",
  WORK_PATH: "命局主线",
  LIFE_IMAGE: "整盘成象",
  DOMAIN_PERSONALITY: "性情",
  DOMAIN_CAREER: "事业",
  DOMAIN_WEALTH: "财富",
  DOMAIN_RELATIONSHIP: "关系",
  DOMAIN_FAMILY: "家庭",
  TIMING_NATAL: "原局基线",
  TIMING_DAYUN: "当前大运",
  TIMING_ANNUAL: "所选流年",
  DISCRIMINATING_QUESTION: "继续校准",
};

const DAY_MASTER_LABELS: Record<string, string> = {
  STRONG: "日主偏强",
  WEAK: "日主偏弱",
  BALANCED: "日主相对均衡",
  FOLLOWING_TENDENCY: "日主呈从势倾向",
  SPECIALIZED_TENDENCY: "命局呈专旺倾向",
  UNCERTAIN: "日主状态仍需复核",
};

const WORK_PATH_LABELS: Record<string, string> = {
  CLOSED: "做功路径已经闭合",
  CONDITIONAL: "做功路径有条件成立",
  BROKEN: "做功路径尚未闭合",
  UNCERTAIN: "做功路径仍需复核",
};

// A frozen Reading has no typed binding to the independently selected stage year yet.
// Keep annual and dayun prose out of the visual rehearsal until that contract exists.
export const TIME_LAYER_STAGE_BOUND_KEYS = [
  "TIMING_NATAL",
  "DISCRIMINATING_QUESTION",
] as const satisfies readonly MingliReadingClaimSemanticKey[];

const LAYER_KEYS: Record<
  MingliReadingLayer,
  readonly MingliReadingClaimSemanticKey[]
> = {
  principle: ["WHOLE_CHART", "DAY_MASTER", "WORK_PATH"],
  image: ["LIFE_IMAGE"],
  themes: [
    "DOMAIN_PERSONALITY",
    "DOMAIN_CAREER",
    "DOMAIN_WEALTH",
    "DOMAIN_RELATIONSHIP",
    "DOMAIN_FAMILY",
  ],
  timing: TIME_LAYER_STAGE_BOUND_KEYS,
};

export function projectMingliLayerNarration({
  graph,
  layer,
}: {
  graph: MingliReadingClaimGraph;
  layer: MingliReadingLayer;
}): MingliLayerNarrationProjection {
  const unique = selectMingliLayerClaims(graph, layer);
  return {
    graphRef: graph.graph_ref,
    graphHash: graph.graph_hash,
    layer,
    layerLabel: LAYER_LABELS[layer],
    notice: layer === "timing"
      ? "岁运段落还在校对眼前的大运与流年；这一轮先看原局基线与需要你回答的问题。"
      : null,
    chapters: unique.map((item, index) => ({
      chapterId: `${layer}-${index + 1}`,
      claimRef: item.claim_ref,
      eyebrow: claimEyebrow(item),
      title: claimTitle(item),
      text: item.statement,
      evidenceLine: item.causal_chain.length
        ? item.causal_chain.join(" → ")
        : null,
      condition: item.condition,
      statusLabel: claimStatusLabel(item),
      semanticAction: "PILLARS_PRESENT",
    })),
  };
}

export function hasMingliLayerNarration(
  graph: MingliReadingClaimGraph,
  layer: MingliReadingLayer,
): boolean {
  return selectMingliLayerClaims(graph, layer).length > 0;
}

export function selectMingliLayerClaims(
  graph: MingliReadingClaimGraph,
  layer: MingliReadingLayer,
): MingliReadingClaim[] {
  const byKey = new Map(graph.claims.map((item) => [item.semantic_key, item]));
  const selected = LAYER_KEYS[layer]
    .map((key) => byKey.get(key))
    .filter(isPresentAndAdmitted);
  if (layer === "principle") {
    const primary = graph.claims.find(
      (item) => item.role === "PRIMARY" && item.status !== "WITHHELD",
    );
    if (primary) selected.splice(Math.min(2, selected.length), 0, primary);
  }
  const unique = selected.filter(
    (item, index, values) =>
      values.findIndex((candidate) => candidate.claim_ref === item.claim_ref) === index,
  );
  return unique;
}

function isPresentAndAdmitted(
  item: MingliReadingClaim | undefined,
): item is MingliReadingClaim {
  return item !== undefined && item.status !== "WITHHELD";
}

function claimEyebrow(item: MingliReadingClaim): string {
  if (item.role === "PRIMARY") return "当前主解释";
  return CLAIM_LABELS[item.semantic_key] ?? "本层判断";
}

function claimTitle(item: MingliReadingClaim): string {
  if (item.semantic_key === "DAY_MASTER") {
    return DAY_MASTER_LABELS[item.codes[0] ?? ""] ?? "日主状态待校准";
  }
  if (item.semantic_key === "WORK_PATH") {
    return WORK_PATH_LABELS[item.headline]
      ?? WORK_PATH_LABELS[item.codes.find((code) => code.startsWith("CLOSURE_"))
        ?.replace("CLOSURE_", "") ?? ""]
      ?? "做功路径仍需复核";
  }
  return item.headline;
}
