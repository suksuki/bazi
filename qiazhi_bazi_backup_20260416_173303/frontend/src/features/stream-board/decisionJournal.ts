/** 追加型决策日志：按语义（地支集合 / 卡片 id）抑制 Inbox，与 physics 张量版本解耦 */

export type DecisionJournalAction = "suppress_inbox";

export type DecisionJournalEntry = {
  ts: number;
  action: DecisionJournalAction;
  /** NFKC 后排序拼接的三合键，与 `inbox-sanhe-` 后缀一致 */
  branch_set_key?: string;
  /** 写入时的 Inbox 卡片 id（含非三合卡） */
  inbox_card_id?: string;
};

export function normalizeDecisionJournalEntries(raw: unknown): DecisionJournalEntry[] {
  if (!Array.isArray(raw)) return [];
  const out: DecisionJournalEntry[] = [];
  for (const item of raw) {
    if (!item || typeof item !== "object" || Array.isArray(item)) continue;
    const o = item as Record<string, unknown>;
    const ts = typeof o.ts === "number" && Number.isFinite(o.ts) ? o.ts : Date.now();
    const action = o.action === "suppress_inbox" ? "suppress_inbox" : null;
    if (!action) continue;
    const branch_set_key =
      typeof o.branch_set_key === "string" && o.branch_set_key.trim()
        ? o.branch_set_key.trim().normalize("NFKC")
        : undefined;
    const inbox_card_id =
      typeof o.inbox_card_id === "string" && o.inbox_card_id.trim()
        ? o.inbox_card_id.trim().normalize("NFKC")
        : undefined;
    out.push({ ts, action, branch_set_key, inbox_card_id });
  }
  return out;
}

/** 由 journal 推导应抑制的 inbox 卡片 id 集合（供 expandResolvedInboxIds 输入） */
export function inboxIdsSuppressedByJournal(journal: DecisionJournalEntry[] | undefined): string[] {
  const ids = new Set<string>();
  for (const e of journal || []) {
    if (e.action !== "suppress_inbox") continue;
    if (e.inbox_card_id?.trim()) ids.add(e.inbox_card_id.trim());
    if (e.branch_set_key?.trim()) ids.add(`inbox-sanhe-${e.branch_set_key.trim()}`);
  }
  return [...ids];
}
