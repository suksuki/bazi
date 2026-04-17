import type { DecisionInboxCard } from "@/features/decision-inbox/types";
import type { BaziMetadata } from "@/types/bazi";
import { appendManualEnergyPatchEntry } from "@/features/stream-board/controller/individualAdjustment";

/**
 * 为悬停影子预览构造临时 metadata（新对象，不修改 React state 中的 meta）。
 * 仅能量补丁类卡片；结构类（三合、插件、逻辑覆盖等）返回 null，由 `structuralPreviewHint` + 后端 `structural_preview` 处理。
 */
export function buildMetadataForDecisionPreview(
  meta: BaziMetadata | null,
  card: DecisionInboxCard,
  seedSig: string | null,
): BaziMetadata | null {
  if (!meta || !seedSig) return null;
  const isEnergy =
    card.cardType === "energy-patch" ||
    (card.cardType === "auditor-proposal" &&
      String((card.proposal as { adjustment_type?: string } | undefined)?.adjustment_type || "") === "ENERGY_PATCH");
  if (!isEnergy) return null;
  const proposal = card.proposal as {
    energy_deltas?: Record<string, number>;
    param_key?: string;
    suggested_value?: number;
    reason?: string;
    expected_impact?: string;
  };
  const deltas = proposal?.energy_deltas || {};
  if (!Object.keys(deltas).length) return null;

  return appendManualEnergyPatchEntry(meta, seedSig, {
    delta_by_deity: { ...deltas },
    param_key: proposal?.param_key,
    suggested_value: proposal?.suggested_value,
    reason: String(proposal?.reason || proposal?.expected_impact || "shadow_preview"),
    confirmed_at: new Date().toISOString(),
    source_card_id: String(card.id),
  });
}
