"use client";

import { USER_INTENTION_IDS, type UserIntentionId } from "@/features/stream-board/models";

const OPTION_LABELS: Record<UserIntentionId, string> = {
  seek_stability: "willProxy.anchor.stability",
  seek_wealth: "willProxy.anchor.wealth",
  seek_fame: "willProxy.anchor.fame",
};

type Props = {
  value: UserIntentionId | "" | undefined;
  onChange: (next: UserIntentionId) => void;
  disabled?: boolean;
  t: (s: string) => string;
  className?: string;
};

/** V10：意志锚点 → physics_config.user_intention + WILL_PROXY 链 */
export function WillIntentionSelector({ value, onChange, disabled = false, t, className = "" }: Props) {
  const active = (value || "") as string;
  return (
    <div
      className={`rounded-lg border border-cyan-900/40 bg-zinc-950/90 px-2 py-2 ${className}`}
      data-testid="will-intention-selector"
    >
      <p className="mb-1.5 text-[9px] font-semibold uppercase tracking-[0.18em] text-cyan-200/80">{t("willProxy.title")}</p>
      <div className="flex flex-wrap gap-1.5">
        {USER_INTENTION_IDS.map((opt) => {
          const sel = active === opt;
          return (
            <button
              key={opt}
              type="button"
              disabled={disabled}
              data-testid={`will-intention-${opt}`}
              onClick={() => onChange(opt)}
              className={`rounded-md border px-2 py-1 text-[10px] font-medium transition-colors ${
                sel
                  ? "border-cyan-400/70 bg-cyan-950/60 text-cyan-100"
                  : "border-zinc-700 bg-zinc-900/80 text-zinc-400 hover:border-cyan-700/50 hover:text-zinc-200"
              } ${disabled ? "cursor-not-allowed opacity-50" : ""}`}
            >
              {t(OPTION_LABELS[opt])}
            </button>
          );
        })}
      </div>
    </div>
  );
}
