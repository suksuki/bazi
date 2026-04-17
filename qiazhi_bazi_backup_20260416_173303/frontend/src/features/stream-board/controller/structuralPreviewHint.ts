import type { InboxCard } from "@/features/stream-board/models";

/** 与后端 `StructuralPreviewHint` / `structural_preview_semantics` 白名单对齐 */
export type StructuralPreviewHintPayload = {
  kind: "L1_STRUCTURE" | "PLUGIN_ENABLE" | "LOGIC_OVERRIDE" | "SEMANTIC_VERDICT" | "PATTERN_SOVEREIGNTY";
  card_id: string;
  label: string;
  plugin_id: string;
  override_key: string;
  baseline_pattern_kind?: string;
  baseline_pattern_name_zh?: string;
};

/** 从当前 physics_tensor 取格局快照，供结构预览与后端「已知→混乱」比对 */
export function snapshotPatternProfileForStructuralPreview(
  physicsTensor: Record<string, unknown> | null | undefined,
): { baseline_pattern_kind: string; baseline_pattern_name_zh: string } {
  const meta = physicsTensor?.meta as Record<string, unknown> | undefined;
  const pp = meta?.pattern_profile as Record<string, unknown> | undefined;
  return {
    baseline_pattern_kind: String(pp?.pattern_kind ?? "").trim(),
    baseline_pattern_name_zh: String(pp?.pattern_name_zh ?? "").trim(),
  };
}

/**
 * 不修改 physics_param、但表达结构/插件/逻辑意志的 Inbox 卡片 → 结构影子预览 hint。
 * 与能量补丁 `buildMetadataForDecisionPreview` 互斥：能量类优先走后者。
 */
export function buildStructuralPreviewHintForCard(card: InboxCard): StructuralPreviewHintPayload | null {
  const id = String(card.id || "").trim();
  const proposal = (card.proposal || {}) as Record<string, unknown>;
  const adj = String(proposal.adjustment_type || "").trim();

  if (card.cardType === "L1_STRUCTURE" || id.startsWith("inbox-sanhe-")) {
    const label = String(card.displayText || card.title || "").trim();
    if (!label) return null;
    return { kind: "L1_STRUCTURE", card_id: id, label, plugin_id: "", override_key: "" };
  }
  if (card.cardType === "semantic-verdict") {
    const label = String(card.displayText || card.title || "").trim();
    if (!label && !id) return null;
    return { kind: "SEMANTIC_VERDICT", card_id: id, label, plugin_id: "", override_key: "" };
  }
  if (card.sovereigntyMark === "PATTERN_SOVEREIGNTY") {
    return {
      kind: "PATTERN_SOVEREIGNTY",
      card_id: id,
      label: String(card.displayText || card.title || "").trim(),
      plugin_id: "",
      override_key: "",
    };
  }
  if (adj === "PLUGIN_ENABLE") {
    const plugin_id = String(proposal.plugin_id ?? proposal.pluginId ?? "").trim();
    if (!plugin_id) return null;
    return {
      kind: "PLUGIN_ENABLE",
      card_id: id,
      label: String(card.displayText || card.title || "").trim(),
      plugin_id,
      override_key: "",
    };
  }
  if (adj === "LOGIC_OVERRIDE") {
    const override_key = String(proposal.param_key || "").trim();
    if (!override_key) return null;
    return {
      kind: "LOGIC_OVERRIDE",
      card_id: id,
      label: String(card.displayText || card.title || "").trim(),
      plugin_id: "",
      override_key,
    };
  }
  return null;
}
