import { detectElementFromText } from "@/constants/termMap";

import type { DecisionInboxCard } from "./types";

const DEITIES = ["比肩", "劫财", "食神", "伤官", "正财", "偏财", "正官", "七杀", "正印", "偏印"] as const;

export function pruneSelectedIds(selectedIds: Record<string, boolean>, validCardIds: string[]) {
  const validIds = new Set(validCardIds);
  const next: Record<string, boolean> = {};
  Object.entries(selectedIds).forEach(([id, checked]) => {
    if (validIds.has(id)) next[id] = checked;
  });
  return next;
}

export function getEvidenceTone(evidence: string) {
  const text = String(evidence || "");
  const matched = text.match(/Abs=([0-9]+(?:\.[0-9]+)?)/);
  const abs = matched ? Number(matched[1]) : NaN;
  if (Number.isFinite(abs)) {
    if (abs < 0.5) return "border-zinc-600 bg-zinc-950 text-zinc-300 animate-pulse";
    if (abs < 2.0) return "border-orange-700/70 bg-orange-950/40 text-orange-300";
    if (abs < 5.0) return "border-sky-700/70 bg-sky-950/40 text-sky-300";
    return "border-fuchsia-600/70 bg-fuchsia-950/35 text-fuchsia-300";
  }
  if (text.includes("状态:熄灭")) return "border-zinc-600 bg-zinc-950 text-zinc-300 animate-pulse";
  if (text.includes("状态:衰微")) return "border-orange-700/70 bg-orange-950/40 text-orange-300";
  if (text.includes("状态:中和")) return "border-sky-700/70 bg-sky-950/40 text-sky-300";
  if (text.includes("状态:强旺")) return "border-fuchsia-600/70 bg-fuchsia-950/35 text-fuchsia-300";
  return "border-zinc-800 bg-zinc-950 text-zinc-400";
}

export function splitVerdictLine(line: string) {
  return line.split(new RegExp(`(${DEITIES.join("|")})`, "g"));
}

export function isVerdictDeity(text: string) {
  return DEITIES.includes(text as (typeof DEITIES)[number]);
}

export function getCardLabel(card: { displayText?: string; conflictDetail?: string; title: string }) {
  return card.displayText ?? card.conflictDetail ?? card.title;
}

export function getCardElement(card: { displayText?: string; conflictDetail?: string; title: string }) {
  return detectElementFromText(getCardLabel(card));
}

export function isAuditorProposal(cardType?: string) {
  return cardType === "auditor-proposal" || cardType === "proposal";
}

/** 判词/卡片文案含「伤官见官」且 L1 已标记时，展示 physics 下发的能级标签 */
export function sgjgEnergeticLabelForCard(
  card: DecisionInboxCard,
  l1JunctionFlags: Record<string, unknown> | undefined,
): string | undefined {
  if (!l1JunctionFlags || !l1JunctionFlags.SHANG_GUAN_JIAN_GUAN) return undefined;
  const blob = `${card.title} ${card.displayText ?? ""} ${card.conflictDetail ?? ""} ${card.markdown ?? ""}`;
  if (!blob.includes("伤官见官")) return undefined;
  const label = l1JunctionFlags.sgjg_level_label;
  return typeof label === "string" && label.trim() ? label : undefined;
}
