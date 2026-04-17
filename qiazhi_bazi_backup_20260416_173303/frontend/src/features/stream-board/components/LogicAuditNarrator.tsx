"use client";

import type { UserIntentionId } from "@/features/stream-board/models";

const WILL_NARRATIVE_I18N_KEYS: Record<UserIntentionId, string> = {
  seek_wealth: "will.narrative.seek_wealth",
  seek_stability: "will.narrative.seek_stability",
  seek_fame: "will.narrative.seek_fame",
};

/**
 * V11：意志叙事同步 — 在 Final Verdict 语义区插入与当前 `user_intention` 对齐的说明段。
 */
export function WillCorrectionNarrative({
  userIntention,
  t,
  className = "",
}: {
  userIntention?: UserIntentionId | "" | undefined;
  t: (s: string) => string;
  className?: string;
}) {
  const id = (userIntention || "").trim() as UserIntentionId;
  if (id !== "seek_wealth" && id !== "seek_stability" && id !== "seek_fame") return null;
  const i18nKey = WILL_NARRATIVE_I18N_KEYS[id];
  return (
    <div
      className={`rounded-lg border border-cyan-700/45 bg-cyan-950/35 p-2 shadow-[inset_0_0_20px_rgba(34,211,238,0.06)] ${className}`}
      data-testid="will-correction-narrative"
    >
      <p className="mb-1 text-[9px] font-semibold uppercase tracking-[0.2em] text-cyan-200/85">{t("willAudit.sectionTitle")}</p>
      <p className="text-[11px] leading-relaxed text-cyan-50/95">{t(i18nKey)}</p>
    </div>
  );
}

/** Decision Inbox / 因果轴：意志切换时的 SYS 审计行（须含 [SYS][WILL] 供 LogicEvolutionAxis 收录） */
const ANCHOR_LABEL: Record<UserIntentionId, string> = {
  seek_stability: "willProxy.anchor.stability",
  seek_wealth: "willProxy.anchor.wealth",
  seek_fame: "willProxy.anchor.fame",
};

export function buildWillIntentionSysLogLines(
  prev: UserIntentionId | "" | undefined,
  next: UserIntentionId,
  t: (s: string) => string,
): string[] {
  const p = String(prev || "").trim() || t("willAudit.sys.unset");
  const prevLabel =
    prev && String(prev).trim() && (prev as UserIntentionId) in ANCHOR_LABEL
      ? t(ANCHOR_LABEL[prev as UserIntentionId])
      : p;
  const headline = t("willAudit.sys.headline")
    .replace("{from}", prevLabel)
    .replace("{to}", t(ANCHOR_LABEL[next]));
  const detailKey =
    next === "seek_wealth"
      ? "willAudit.sys.detailWealth"
      : next === "seek_stability"
        ? "willAudit.sys.detailStability"
        : "willAudit.sys.detailFame";
  return [`[SYS][WILL] ${headline}`, `[SYS][WILL] ${t(detailKey)}`];
}
