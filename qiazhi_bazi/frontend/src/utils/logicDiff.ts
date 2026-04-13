/**
 * 意志影子预览：当前十神分 vs 预览分 的相对变化率（%），供仪表盘浮动标注。
 * 分母取当前绝对值，避免除零；当前为 0 且预览非 0 时退化为以预览为基。
 */
export function computeDeityPreviewDeltaPercent(
  currentDeityScores: Record<string, number>,
  previewDeityScores: Record<string, number>,
): Record<string, number> {
  const out: Record<string, number> = {};
  const keys = new Set([...Object.keys(currentDeityScores), ...Object.keys(previewDeityScores)]);
  for (const k of keys) {
    const c = Number(currentDeityScores[k] ?? 0);
    const p = Number(previewDeityScores[k] ?? 0);
    if (!Number.isFinite(c) || !Number.isFinite(p)) continue;
    if (Math.abs(c) < 1e-9 && Math.abs(p) < 1e-9) continue;
    const denom = Math.abs(c) < 1e-9 ? (Math.abs(p) < 1e-9 ? 1 : Math.abs(p)) : Math.abs(c);
    out[k] = ((p - c) / denom) * 100;
  }
  return out;
}
