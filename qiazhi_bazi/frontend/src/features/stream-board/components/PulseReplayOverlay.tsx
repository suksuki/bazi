"use client";

import type { PulseReplayOverlayState } from "@/features/stream-board/stores/pulseReplayContext";

function maxAbs(scores: Record<string, number>): number {
  let m = 1e-9;
  for (const v of Object.values(scores)) {
    const a = Math.abs(Number(v) || 0);
    if (a > m) m = a;
  }
  return m;
}

function EnergySnapshotBars({ scores }: { scores: Record<string, number> }) {
  const cap = maxAbs(scores);
  const entries = Object.entries(scores).sort((a, b) => Math.abs(b[1]) - Math.abs(a[1])).slice(0, 12);
  return (
    <div className="space-y-1">
      {entries.map(([k, v]) => {
        const pct = Math.min(100, (Math.abs(Number(v) || 0) / cap) * 100);
        return (
          <div key={k} className="flex items-center gap-2">
            <span className="w-10 shrink-0 text-[10px] text-zinc-400">{k}</span>
            <div className="h-2 min-w-0 flex-1 rounded bg-zinc-800">
              <div
                className="h-2 rounded bg-cyan-500/70"
                style={{ width: `${pct}%` }}
                title={`${v}`}
              />
            </div>
            <span className="w-14 shrink-0 text-right font-mono text-[9px] text-zinc-500">{Number(v).toFixed(2)}</span>
          </div>
        );
      })}
    </div>
  );
}

type Props = {
  overlay: PulseReplayOverlayState;
  onClose: () => void;
  /** 浮层内副标题等 */
  t: (s: string) => string;
};

export function PulseReplayOverlay({ overlay, onClose, t }: Props) {
  const hasEnergy = overlay.energy && Object.keys(overlay.energy).length > 0;
  const hasSk = Boolean(overlay.skeleton?.trim());

  return (
    <div
      className="pointer-events-auto fixed inset-x-2 bottom-20 z-[90] max-h-[min(72vh,520px)] overflow-hidden rounded-xl border border-cyan-700/50 bg-zinc-950/98 p-3 shadow-[0_0_40px_rgba(6,182,212,0.18)] backdrop-blur-md sm:inset-x-6"
      role="dialog"
      aria-modal="true"
      aria-label={t("逻辑脉冲回放")}
    >
      <div className="mb-2 flex items-start justify-between gap-2 border-b border-zinc-800 pb-2">
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-wide text-cyan-200/90">{t("逻辑脉冲回放")}</p>
          <p className="mt-0.5 text-[11px] text-zinc-300">{overlay.label}</p>
          <p className="mt-0.5 font-mono text-[9px] text-zinc-600">
            {overlay.kind}
            {overlay.pulseId ? ` · ${overlay.pulseId}` : ""}
          </p>
        </div>
        <button
          type="button"
          onClick={onClose}
          className="shrink-0 rounded-lg border border-zinc-600 bg-zinc-900 px-2 py-1 text-[11px] text-zinc-200 hover:border-cyan-500/50 hover:text-cyan-100"
        >
          {t("关闭")}
        </button>
      </div>
      {overlay.bufferMiss ? (
        <p className="mb-2 text-[10px] leading-relaxed text-amber-200/90">{t("脉冲回放：环形缓冲未命中，以下为最近可得快照或空态。")}</p>
      ) : null}
      {overlay.hubLine ? (
        <p className="mb-2 rounded border border-zinc-800 bg-black/40 p-2 font-mono text-[9px] text-zinc-400">{overlay.hubLine}</p>
      ) : null}
      <div className="grid max-h-[min(56vh,420px)] gap-3 overflow-y-auto sm:grid-cols-2">
        <div className="rounded-lg border border-zinc-800/90 bg-black/35 p-2">
          <p className="mb-1.5 text-[10px] font-medium text-cyan-100/90">{t("能量图快照")}</p>
          {hasEnergy ? (
            <EnergySnapshotBars scores={overlay.energy!} />
          ) : (
            <p className="text-[10px] text-zinc-600">{t("无十神能量条可展示")}</p>
          )}
        </div>
        <div className="rounded-lg border border-zinc-800/90 bg-black/35 p-2">
          <p className="mb-1.5 text-[10px] font-medium text-zinc-200">{t("引擎骨架快照")}</p>
          {hasSk ? (
            <pre className="max-h-52 overflow-auto whitespace-pre-wrap break-words font-mono text-[9px] leading-snug text-zinc-300">
              {overlay.skeleton}
            </pre>
          ) : (
            <p className="text-[10px] text-zinc-600">{t("无 verdict_skeleton")}</p>
          )}
        </div>
      </div>
      {overlay.roundEntry?.response_text?.trim() ? (
        <details className="mt-2 rounded border border-violet-900/40 bg-violet-950/15 p-2">
          <summary className="cursor-pointer text-[10px] text-violet-200/90">{t("该轮次模型回复摘录")}</summary>
          <pre className="mt-1 max-h-32 overflow-auto whitespace-pre-wrap break-words text-[9px] text-zinc-400">
            {String(overlay.roundEntry.response_text).slice(0, 2400)}
          </pre>
        </details>
      ) : null}
    </div>
  );
}
