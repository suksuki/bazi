import type { ConflictPoint } from "@/types/bazi";

/** 与 backend skill_manifest 中盲派 Skill ID 对齐 */
export function skillIdForConflictPoint(p: ConflictPoint): string {
  const d = String(p.detail || "");
  const k = String(p.kind || "");
  if (k === "harm" || d.includes("穿")) return "mp_pierce_01";
  if (d.includes("墓库") || d.includes("闭库") || /辰|戌|丑|未/.test(d)) return "mp_tomb_01";
  if (d.includes("宾主") || d.includes("财官")) return "mp_host_guest_01";
  return "mp_semantic_layer";
}

function inferFromFreeText(text: string): string {
  const t = text.trim();
  if (!t) return "mp_semantic_layer";
  if (t.includes("穿") || /子未|丑午|寅巳|卯辰|申亥|酉戌/.test(t)) return "mp_pierce_01";
  if (t.includes("墓库") || t.includes("闭库")) return "mp_tomb_01";
  if (t.includes("宾主") || (t.includes("财官") && (t.includes("日时") || t.includes("红利")))) return "mp_host_guest_01";
  return "mp_semantic_layer";
}

/**
 * 将 Decision 卡片与 L1 冲突点 / 文案做弱关联，用于角落 Skill 徽章。
 */
export function inferDecisionSkillId(
  card: {
    id: string;
    conflictDetail?: string;
    displayText?: string;
    title: string;
    cardType?: string;
  },
  points: ConflictPoint[] | undefined,
): string {
  if (card.cardType === "auditor-proposal") return "mp_l1_param";
  if (card.id === "fallback-deep-scan") return "mp_deep_scan";
  const blob = `${card.conflictDetail || ""} ${card.displayText || ""} ${card.title}`;
  if (points?.length) {
    for (const p of points) {
      const d = String(p.detail || "");
      if (!d) continue;
      if (blob.includes(d) || d.includes(blob.trim().slice(0, 8))) {
        return skillIdForConflictPoint(p);
      }
    }
  }
  return inferFromFreeText(blob);
}
