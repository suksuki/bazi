import type { PatternThresholdRow } from "@/features/stream-board/models";

export function maxPatternProgress(rows: PatternThresholdRow[] | null | undefined): number {
  if (!rows?.length) return 0;
  return rows.reduce((m, r) => (Number(r.progress) > m ? Number(r.progress) : m), 0);
}

/** 预览态：达成度由低阈之下跃迁至高阈之上（质变探测器） */
export function detectPhaseTransitionSurge(
  prevMax: number,
  nextMax: number,
  opts: { low: number; high: number } = { low: 0.85, high: 0.92 },
): boolean {
  return prevMax < opts.low && nextMax > opts.high;
}
