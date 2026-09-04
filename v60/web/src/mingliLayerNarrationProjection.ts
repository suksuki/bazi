import type {
  MingliReadingClaim,
  MingliReadingClaimGraph,
  MingliReadingClaimSemanticKey,
} from "./mingliClaimGraphTypes";
import { claimStatusLabel } from "./mingliClaimPresentation";
import type { MingliReadingLayer } from "./mingliStageNavigation";
import type {
  MingliFocus,
  MingliFocusedPassResult,
  MingliNarrationCue,
  MingliReadingSummaryProjection,
} from "./mingliStageTypes";
import { isPublicPassSafe } from "./publicReadingPresentation";

export interface MingliLayerNarrationChapter {
  chapterId: string;
  sourceItemRef: string;
  claimRef: string | null;
  eyebrow: string;
  title: string;
  text: string;
  evidenceLine: string | null;
  condition: string | null;
  reviewNote: string | null;
  statusLabel: string;
  semanticAction: MingliNarrationCue["semantic_action"];
}

export interface MingliLayerNarrationProjection {
  sourceKind: "CLAIM_GRAPH" | "FOCUSED_PASSES";
  sourceRef: string;
  sourceHash: string;
  graphRef: string | null;
  graphHash: string | null;
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

const LAYER_FOCUSES: Record<MingliReadingLayer, readonly MingliFocus[]> = {
  principle: ["STRUCTURE"],
  image: ["LIFE_IMAGE_PERSONALITY"],
  themes: ["CAREER_WEALTH", "RELATIONSHIP_FAMILY"],
  timing: ["TIMING"],
};

const FOCUSED_PASS_LABELS: Record<
  MingliFocus,
  { eyebrow: string; title: string }
> = {
  STRUCTURE: { eyebrow: "原局结构", title: "命局主线" },
  LIFE_IMAGE_PERSONALITY: {
    eyebrow: "生命意象与性情",
    title: "这份命局呈现出的生命气质",
  },
  CAREER_WEALTH: { eyebrow: "事业与财富", title: "事业与财富的发力方式" },
  RELATIONSHIP_FAMILY: {
    eyebrow: "关系与家庭",
    title: "关系与家庭中的互动主题",
  },
  TIMING: { eyebrow: "当前大运与流年", title: "此刻的时间趋势" },
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
    sourceKind: "CLAIM_GRAPH",
    sourceRef: graph.graph_ref,
    sourceHash: graph.graph_hash,
    graphRef: graph.graph_ref,
    graphHash: graph.graph_hash,
    layer,
    layerLabel: LAYER_LABELS[layer],
    notice: layer === "timing"
      ? "岁运段落还在校对眼前的大运与流年；这一轮先看原局基线与需要你回答的问题。"
      : null,
    chapters: unique.map((item, index) => ({
      chapterId: `${layer}-${index + 1}`,
      sourceItemRef: item.claim_ref,
      claimRef: item.claim_ref,
      eyebrow: claimEyebrow(item),
      title: claimTitle(item),
      text: item.statement,
      evidenceLine: item.causal_chain.length
        ? item.causal_chain.join(" → ")
        : null,
      condition: item.condition,
      reviewNote: null,
      statusLabel: claimStatusLabel(item),
      semanticAction: "PILLARS_PRESENT",
    })),
  };
}

export function mingliLayerFocuses(
  layer: MingliReadingLayer,
): readonly MingliFocus[] {
  return LAYER_FOCUSES[layer];
}

export function hasMingliSummaryLayerNarration(
  summary: MingliReadingSummaryProjection,
  layer: MingliReadingLayer,
): boolean {
  return projectMingliSummaryLayerNarration(summary, layer) !== null;
}

export function projectMingliSummaryLayerNarration(
  summary: MingliReadingSummaryProjection,
  layer: MingliReadingLayer,
): MingliLayerNarrationProjection | null {
  const passes = selectCompleteFocusedPasses(summary, layer);
  if (passes !== null) {
    return projectFocusedPassNarration(summary, layer, passes);
  }
  if (
    summary.claim_graph !== null
    && hasMingliLayerNarration(summary.claim_graph, layer)
  ) {
    return projectMingliLayerNarration({ graph: summary.claim_graph, layer });
  }
  return null;
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

function selectCompleteFocusedPasses(
  summary: MingliReadingSummaryProjection,
  layer: MingliReadingLayer,
): MingliFocusedPassResult[] | null {
  const byFocus = new Map<MingliFocus, MingliFocusedPassResult>();
  for (const item of summary.focused_reading?.passes ?? []) {
    byFocus.set(item.focus, item);
  }
  for (const record of summary.focused_pass_records) {
    byFocus.set(record.focus, record.pass_result);
  }
  const selected = LAYER_FOCUSES[layer].map((focus) => byFocus.get(focus));
  if (selected.some((item) => item === undefined || !isPublicPassSafe(item))) {
    return null;
  }
  return selected.filter(
    (item): item is MingliFocusedPassResult => item !== undefined,
  );
}

function projectFocusedPassNarration(
  summary: MingliReadingSummaryProjection,
  layer: MingliReadingLayer,
  passes: MingliFocusedPassResult[],
): MingliLayerNarrationProjection {
  return {
    sourceKind: "FOCUSED_PASSES",
    sourceRef: summary.summary_ref,
    sourceHash: summary.summary_hash,
    graphRef: null,
    graphHash: null,
    layer,
    layerLabel: LAYER_LABELS[layer],
    notice: layer === "timing"
      ? "本段是当前岁运的分层初断；舞台只呈现时间坐标，画面上的靠近或远离不构成命理证据。"
      : "这是本地模型形成的分层初断，已保留原文来源，仍可在研发期继续校准。",
    chapters: passes.map((item, index) => {
      const label = FOCUSED_PASS_LABELS[item.focus];
      const needsReview = item.normalization_codes.length > 0;
      return {
        chapterId: `${layer}-${index + 1}`,
        sourceItemRef: item.pass_ref,
        claimRef: null,
        eyebrow: label.eyebrow,
        title: label.title,
        text: item.normalized_text,
        evidenceLine: null,
        condition: null,
        reviewNote: needsReview
          ? "本段触发了本地边界标记，请把它视为待继续校准的初断。"
          : null,
        statusLabel: needsReview
          ? "已标记边界 · 待校准"
          : "本地模型初断 · 待校准",
        // Focused timing prose has no typed binding to the selected visual year.
        semanticAction: "PILLARS_PRESENT",
      };
    }),
  };
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
