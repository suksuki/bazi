import type {
  MingliFocusedSpeechAsset,
  MingliFocusedSpeechCue,
} from "./publicSpeechApi";
import type { MingliStageColumn, MingliStageProjection } from "./mingliStageTypes";

export interface MingliFocusedSubtitle {
  chapterId: string;
  cueIndex: number;
  cueCount: number;
  text: string;
  startMs: number;
  endMs: number;
  activeColumnRefs: string[];
}

export function focusedCueAtTime(
  asset: MingliFocusedSpeechAsset,
  currentTimeMs: number,
): MingliFocusedSpeechCue {
  const boundedTime = Math.max(0, Math.min(currentTimeMs, asset.durationMs));
  return asset.cues.find(
    (cue) => boundedTime >= cue.startMs && boundedTime < cue.endMs,
  ) ?? asset.cues[asset.cues.length - 1];
}

export function focusedCueProgress(
  cue: MingliFocusedSpeechCue,
  currentTimeMs: number,
): number {
  const duration = Math.max(1, cue.endMs - cue.startMs);
  return Math.max(0, Math.min(1, (currentTimeMs - cue.startMs) / duration));
}

export function focusedSubtitle(
  asset: MingliFocusedSpeechAsset,
  chapterId: string,
  currentTimeMs: number,
  stage: MingliStageProjection,
): MingliFocusedSubtitle {
  const cue = focusedCueAtTime(asset, currentTimeMs);
  return {
    chapterId,
    cueIndex: cue.cueIndex,
    cueCount: asset.cues.length,
    text: cue.text,
    startMs: cue.startMs,
    endMs: cue.endMs,
    activeColumnRefs: focusedColumnRefs(stage, cue.text),
  };
}

export function focusedColumnRefs(
  stage: MingliStageProjection,
  subtitle: string,
): string[] {
  const temporalLayerMentioned = subtitle.includes("岁运");
  return stage.columns
    .filter((column) => {
      if (subtitle.includes(column.pillar)) return true;
      if (temporalLayerMentioned && column.source_layer !== "NATAL") return true;
      return termsForColumn(column, stage.selected_year).some(
        (term) => subtitle.includes(term),
      );
    })
    .map((column) => column.column_ref);
}

function termsForColumn(column: MingliStageColumn, selectedYear: number | null): string[] {
  if (column.slot === "NATAL_YEAR") return ["年柱", "年干", "年支"];
  if (column.slot === "NATAL_MONTH") {
    return ["月柱", "月令", "月干", "月支", `${column.branch}月`];
  }
  if (column.slot === "NATAL_DAY") {
    return ["日柱", "日主", "日元", "日干", "日支"];
  }
  if (column.slot === "NATAL_HOUR") return ["时柱", "时干", "时支"];
  if (column.slot === "DAYUN") return ["大运", "运柱"];
  return ["流年", "岁柱", ...(selectedYear === null ? [] : [`${selectedYear}年`])];
}
