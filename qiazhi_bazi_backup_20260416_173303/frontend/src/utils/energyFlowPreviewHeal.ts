/**
 * 影子预览下「相生链」假想修补：仅 UI 提示，不修改 energy_flow_audit 真值。
 * 规则：某断裂段 from→to 若存在对应十神 Δ% 为正且超过阈值，则该段显示淡紫 ✓。
 *
 * 与 `shadowPreviewI18n.ts` / `shadowPreviewPure.ts` 无依赖关系；导出函数均为纯函数（仅依赖入参）。
 */

const THRESH = 0.12;

/** 生我 / 我生 方向上的十神提示：与审计段元素粗对齐（启发式） */
const LINK_HINT_DEITIES: Record<string, readonly string[]> = {
  "wood-fire": ["食神", "伤官"],
  "fire-earth": ["食神", "伤官", "比肩", "劫财"],
  "earth-metal": ["食神", "伤官", "比肩", "劫财"],
  "metal-water": ["正印", "偏印", "食神", "伤官"],
  "water-wood": ["正印", "偏印"],
};

function sumPositiveHints(
  deities: readonly string[],
  previewDeltaPctByDeity: Record<string, number> | null | undefined,
): number {
  if (!previewDeltaPctByDeity) return 0;
  let s = 0;
  for (const d of deities) {
    const v = previewDeltaPctByDeity[d];
    if (typeof v === "number" && Number.isFinite(v) && v > 0) s += v;
  }
  return s;
}

export type FlowAuditLike = {
  segments?: Array<{ from?: string; to?: string; state?: string }>;
  break_indices?: number[];
};

export function inferPreviewHealSegmentIndices(
  audit: FlowAuditLike | null | undefined,
  previewDeltaPctByDeity: Record<string, number> | null | undefined,
): Set<number> {
  const out = new Set<number>();
  const segments = Array.isArray(audit?.segments) ? audit!.segments! : [];
  if (!segments.length || !previewDeltaPctByDeity || !Object.keys(previewDeltaPctByDeity).length) return out;
  const breaks = new Set(Array.isArray(audit?.break_indices) ? audit!.break_indices! : []);

  segments.forEach((seg, idx) => {
    const broken = breaks.has(idx) || seg.state === "BROKEN";
    if (!broken) return;
    const from = String(seg.from || "").toLowerCase();
    const to = String(seg.to || "").toLowerCase();
    const key = `${from}-${to}`;
    const hints = LINK_HINT_DEITIES[key];
    if (!hints) return;
    if (sumPositiveHints(hints, previewDeltaPctByDeity) >= THRESH) out.add(idx);
  });
  return out;
}
