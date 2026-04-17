import type {
  BaziMetadata,
  ManualEnergyPatchEntry,
  ManualEnergyPatchState,
  SemanticVerdictArchiveEntry,
} from "@/types/bazi";
import { TEN_GOD_ORDER } from "@/features/ten-god-list/constants";
import type { DeityEnergyAxis } from "@/features/stream-board/models";
import { seedPayloadSignaturesCompatible } from "@/features/stream-board/controller/streamBoardPure";

/** 物理键 → 十神轴上的柔性方向模板（量纲与 deity_scores 对齐的「小步」偏移，非全局公式常数） */
const PARAM_KEY_DELTA_TEMPLATE: Record<string, Partial<Record<string, number>>> = {
  CF_FLOATING_DECAY: { 比肩: -0.6, 劫财: -0.6, 正印: 0.25, 偏印: 0.25 },
  THROUGH_STEM_BOOST: { 伤官: 0.45, 食神: 0.45, 正官: 0.15, 七杀: 0.15 },
  CONFLICT_PENALTY_GAMMA: { 七杀: -0.35, 正官: -0.35, 伤官: 0.25, 食神: 0.25 },
  A_PROTRUSION: { 伤官: 0.35, 食神: 0.35, 偏财: 0.15, 正财: 0.15 },
  /** 官杀克制修正：略抑官杀簇、轻抬印绶以缓和「独强官星」张力 */
  OFFICER_RESTRAINT_ALPHA: { 正官: -0.3, 七杀: -0.3, 正印: 0.22, 偏印: 0.22 },
  /** 权重分布修正：略平抑比劫独大、微调食伤财以再平衡 */
  POWER_DISTRIBUTION_GAMMA: { 比肩: -0.2, 劫财: -0.2, 食神: 0.12, 伤官: 0.12, 正财: 0.08, 偏财: 0.08 },
};

const ADJUSTMENT_AMPLITUDE = 2.2;

export function buildEnergyDeltasFromLogicProposal(paramKey: string, suggestedValue: number | undefined): Record<string, number> {
  const base = PARAM_KEY_DELTA_TEMPLATE[paramKey];
  if (!base || suggestedValue == null || !Number.isFinite(suggestedValue)) return {};
  const deltaScale = (Number(suggestedValue) - 1.0) * ADJUSTMENT_AMPLITUDE;
  const out: Record<string, number> = {};
  for (const [deity, w] of Object.entries(base)) {
    if (typeof w === "number" && Number.isFinite(w)) {
      out[deity] = w * deltaScale;
    }
  }
  return out;
}

export function aggregateManualEnergyDeltas(entries: ManualEnergyPatchEntry[] | undefined): Record<string, number> {
  const acc: Record<string, number> = {};
  if (!Array.isArray(entries)) return acc;
  for (const e of entries) {
    const row = e?.delta_by_deity;
    if (!row || typeof row !== "object") continue;
    for (const [k, v] of Object.entries(row)) {
      if (typeof v === "number" && Number.isFinite(v)) {
        acc[k] = (acc[k] ?? 0) + v;
      }
    }
  }
  return acc;
}

export function manualInterventionDeityKeys(entries: ManualEnergyPatchEntry[] | undefined): Set<string> {
  const deltas = aggregateManualEnergyDeltas(entries);
  return new Set(Object.keys(deltas).filter((k) => Math.abs(deltas[k] ?? 0) > 1e-6));
}

export function applyManualEnergyPatchesToDisplay(
  scores: Record<string, number>,
  axes: Record<string, DeityEnergyAxis>,
  patch: ManualEnergyPatchState | null | undefined,
  seedHash: string | null,
): { scores: Record<string, number>; axes: Record<string, DeityEnergyAxis> } {
  if (!patch?.entries?.length || !seedHash) {
    return { scores: { ...scores }, axes: { ...axes } };
  }
  if (!seedPayloadSignaturesCompatible(patch.seed_hash, seedHash)) {
    return { scores: { ...scores }, axes: { ...axes } };
  }
  const delta = aggregateManualEnergyDeltas(patch.entries);
  const nextScores = { ...scores };
  const nextAxes: Record<string, DeityEnergyAxis> = { ...axes };
  for (const name of TEN_GOD_ORDER) {
    const d = delta[name] ?? 0;
    if (!d) continue;
    nextScores[name] = Math.max(0, (nextScores[name] ?? 0) + d);
    const ax = { ...(nextAxes[name] || {}) };
    const baseRel = typeof ax.relative_percentage === "number" ? ax.relative_percentage : (scores[name] ?? 0);
    ax.relative_percentage = Math.max(0, Math.min(100, baseRel + d));
    if (typeof ax.absolute_energy === "number" && Number.isFinite(ax.absolute_energy)) {
      ax.absolute_energy = Math.max(0, ax.absolute_energy + d * 0.12);
    }
    nextAxes[name] = ax;
  }
  return { scores: nextScores, axes: nextAxes };
}

function isVerdictAnchorLayerEmpty(anchor: BaziMetadata["verdict_anchor_layer"]): boolean {
  if (!anchor || typeof anchor !== "object") return true;
  if (String(anchor.final_verdict || "").trim()) return false;
  if (String(anchor.narrative_version_id || "").trim()) return false;
  const assertions = anchor.assertions;
  if (!Array.isArray(assertions) || assertions.length === 0) return true;
  return !assertions.some((a) => a && String(a.text || "").trim());
}

export type MergeAnalyzeSeedMetadataOpts = {
  /** 同一生辰再次测算：服务端若回传空壳，保留上一轮的判决锚点与已归档语义断语 */
  sameSeedResubmit?: boolean;
};

/**
 * analyze-seed / 静默重算 灌入元数据：先合并能量补丁侧车，再在同 seed 重算时防止空响应冲掉锚点与归档。
 */
export function mergeAnalyzeSeedMetadata(
  incoming: BaziMetadata,
  previous: BaziMetadata | null,
  seedHash: string | null,
  opts?: MergeAnalyzeSeedMetadataOpts,
): BaziMetadata {
  const sameSeed = Boolean(opts?.sameSeedResubmit);
  let out: BaziMetadata = { ...incoming };

  const patchSeed = Boolean(
    seedHash && previous?.manual_energy_patch?.seed_hash && seedPayloadSignaturesCompatible(previous.manual_energy_patch.seed_hash, seedHash),
  );

  if (patchSeed) {
    out = {
      ...out,
      manual_energy_patch: previous!.manual_energy_patch,
      persistence_layer: previous!.persistence_layer ?? out.persistence_layer,
    };
  } else if (sameSeed && previous) {
    const incSv = incoming.persistence_layer?.semantic_verdicts;
    const prevSv = previous.persistence_layer?.semantic_verdicts;
    if ((!Array.isArray(incSv) || incSv.length === 0) && Array.isArray(prevSv) && prevSv.length > 0) {
      const basePl = incoming.persistence_layer || previous.persistence_layer;
      const prevCv = previous.persistence_layer?.confirmed_verdicts;
      const incCv = incoming.persistence_layer?.confirmed_verdicts;
      const mergedCv =
        Array.isArray(prevCv) && prevCv.length > 0 && (!Array.isArray(incCv) || incCv.length === 0) ? prevCv : incCv;
      out = {
        ...out,
        persistence_layer: {
          persistence_protocol: basePl?.persistence_protocol || "persistence_layer.v1",
          semantic_verdicts: prevSv,
          ...(mergedCv && mergedCv.length ? { confirmed_verdicts: mergedCv } : {}),
        },
      };
    }
  }

  if (sameSeed && previous?.persistence_layer?.confirmed_verdicts?.length) {
    const prevPl = previous.persistence_layer;
    const cur = out.persistence_layer;
    const curCv = cur?.confirmed_verdicts;
    if (!Array.isArray(curCv) || curCv.length === 0) {
      out = {
        ...out,
        persistence_layer: {
          persistence_protocol: cur?.persistence_protocol || prevPl.persistence_protocol || "persistence_layer.v1",
          semantic_verdicts: cur?.semantic_verdicts ?? prevPl.semantic_verdicts ?? [],
          confirmed_verdicts: prevPl.confirmed_verdicts,
          ...(prevPl.will_temporal_anchor_dayun && !cur?.will_temporal_anchor_dayun
            ? { will_temporal_anchor_dayun: prevPl.will_temporal_anchor_dayun }
            : {}),
        },
      };
    }
  }

  if (sameSeed && previous && isVerdictAnchorLayerEmpty(out.verdict_anchor_layer) && !isVerdictAnchorLayerEmpty(previous.verdict_anchor_layer)) {
    out = { ...out, verdict_anchor_layer: previous.verdict_anchor_layer };
  }

  return out;
}

export function mergeIncomingMetadataPersistence(
  incoming: BaziMetadata,
  previous: BaziMetadata | null,
  seedHash: string | null,
): BaziMetadata {
  return mergeAnalyzeSeedMetadata(incoming, previous, seedHash, undefined);
}

export function appendManualEnergyPatchEntry(
  meta: BaziMetadata | null,
  seedHash: string,
  entry: ManualEnergyPatchEntry,
): BaziMetadata | null {
  if (!meta) return null;
  const prev = meta.manual_energy_patch;
  const entries =
    prev && seedPayloadSignaturesCompatible(prev.seed_hash, seedHash) && Array.isArray(prev.entries)
      ? [...prev.entries, entry]
      : [entry];
  return {
    ...meta,
    manual_energy_patch: {
      patch_protocol: "manual_energy_patch.v1",
      seed_hash: seedHash,
      entries,
    },
  };
}

export function appendSemanticVerdictArchive(
  meta: BaziMetadata | null,
  seedHash: string,
  item: SemanticVerdictArchiveEntry,
): BaziMetadata | null {
  if (!meta) return null;
  const pl = meta.persistence_layer || { persistence_protocol: "persistence_layer.v1", semantic_verdicts: [] };
  const prevList = Array.isArray(pl.semantic_verdicts) ? [...pl.semantic_verdicts] : [];
  const nextList = [...prevList, item].slice(-48);
  return {
    ...meta,
    persistence_layer: {
      persistence_protocol: pl.persistence_protocol || "persistence_layer.v1",
      semantic_verdicts: nextList,
    },
  };
}

export function normalizeSemanticVerdictText(s: string): string {
  return String(s || "")
    .replace(/\s+/g, " ")
    .trim();
}

/** 同一 seed 下按正文归一化去重后再追加 */
export function appendSemanticVerdictDeduped(
  meta: BaziMetadata | null,
  seedHash: string,
  text: string,
  sourceCardId: string,
  confirmedAtIso?: string,
): BaziMetadata | null {
  const norm = normalizeSemanticVerdictText(text);
  if (!meta || !seedHash || !norm) return meta;
  const list = meta.persistence_layer?.semantic_verdicts || [];
  if (
    list.some(
      (e) =>
        normalizeSemanticVerdictText(e.text) === norm &&
        seedPayloadSignaturesCompatible(e.seed_hash, seedHash),
    )
  ) {
    return meta;
  }
  return appendSemanticVerdictArchive(meta, seedHash, {
    id: `sv-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`,
    text: norm.slice(0, 4000),
    seed_hash: seedHash,
    confirmed_at: confirmedAtIso || new Date().toISOString(),
    source_card_id: sourceCardId,
  });
}

/** 意志归档：与 appendSemanticVerdictDeduped 等价，供执行链打点；成功写入时打 Persistence 日志 */
export function archiveSemanticVerdict(
  meta: BaziMetadata | null,
  seedHash: string,
  text: string,
  sourceCardId: string,
  confirmedAtIso?: string,
): BaziMetadata | null {
  const before = meta?.persistence_layer?.semantic_verdicts?.length ?? 0;
  const out = appendSemanticVerdictDeduped(meta, seedHash, text, sourceCardId, confirmedAtIso);
  const after = out?.persistence_layer?.semantic_verdicts?.length ?? 0;
  if (out !== meta || after > before) {
    console.log("[Persistence] Writing verdict to seed:", seedHash);
  }
  return out;
}
