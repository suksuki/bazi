import type { PatternThresholdRow } from "@/features/stream-board/models";

export const MANIFEST_STRICT_V = "MANIFEST_V5.8_STRICT" as const;

/** 碰撞中子：与后端 affinity 对齐的匹配度（0–1） */
export function affinityMatch(row: PatternThresholdRow): number {
  const a = row.affinity_score;
  if (typeof a === "number" && Number.isFinite(a)) return Math.max(0, Math.min(1, a));
  return Math.max(0, Math.min(1, row.progress));
}

/** WILL_PROXY 重塑前亲和度（仅后端写入 affinity_pre_will_proxy 时有值） */
export function affinityPreWillProxy(row: PatternThresholdRow): number | null {
  const a = row.affinity_pre_will_proxy;
  if (typeof a === "number" && Number.isFinite(a)) return Math.max(0, Math.min(1, a));
  return null;
}

export function allRowsStrictFingerprint(rows: PatternThresholdRow[]): boolean {
  if (!rows.length) return true;
  return rows.every((r) => r.engine_v === MANIFEST_STRICT_V);
}

/** 门控：主轴能量 ≥ 法典 min_energy（无 min 则视为通过） */
export function axisGatePass(row: PatternThresholdRow): boolean {
  const minE = row.gating_min_energy;
  if (minE == null || Number.isNaN(minE)) return true;
  const e = row.primary_axis_energy;
  if (typeof e !== "number" || !Number.isFinite(e)) return false;
  return e + 1e-9 >= minE;
}

export function isRedlineExclusion(row: PatternThresholdRow): boolean {
  return row.exclusion_hit === true;
}

/** 有资格竞争 Top3：过门控且未触红线 */
export function eligibleForTopCompetition(row: PatternThresholdRow): boolean {
  return axisGatePass(row) && !isRedlineExclusion(row);
}

/** 按 affinity（匹配度）降序；数据源须已为 L2 strict 行 */
export function sortRowsByAffinityMatch(rows: PatternThresholdRow[]): PatternThresholdRow[] {
  return [...rows].sort((a, b) => affinityMatch(b) - affinityMatch(a));
}

export function topEligibleByAffinity(rows: PatternThresholdRow[], n: number): PatternThresholdRow[] {
  const elig = sortRowsByAffinityMatch(rows.filter(eligibleForTopCompetition));
  return elig.slice(0, n);
}
