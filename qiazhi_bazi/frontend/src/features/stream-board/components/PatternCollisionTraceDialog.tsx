"use client";

import type { PatternThresholdRow } from "@/features/stream-board/models";
import { affinityMatch } from "@/features/stream-board/utils/patternWaterlineV7";

type Props = {
  row: PatternThresholdRow | null;
  open: boolean;
  onClose: () => void;
  t: (key: string) => string;
};

export function PatternCollisionTraceDialog({ row, open, onClose, t }: Props) {
  if (!open || !row) return null;

  const aff = affinityMatch(row);
  const minE = row.gating_min_energy;
  const maxS = row.gating_max_self_energy;
  const pae = row.primary_axis_energy;
  const gatePass =
    minE == null || Number.isNaN(minE)
      ? true
      : typeof pae === "number" && Number.isFinite(pae) && pae + 1e-9 >= minE;

  return (
    <div
      className="fixed inset-0 z-[80] flex items-end justify-center bg-black/55 p-2 sm:items-center"
      role="dialog"
      aria-modal
      aria-labelledby="collision-trace-title"
      onClick={onClose}
    >
      <div
        className="max-h-[min(88vh,28rem)] w-full max-w-md overflow-y-auto rounded-lg border border-violet-700/50 bg-zinc-950 p-3 text-[11px] text-zinc-200 shadow-2xl shadow-violet-950/40"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-2 flex items-start justify-between gap-2">
          <div>
            <h2 id="collision-trace-title" className="text-sm font-semibold text-violet-100">
              {t("pattern.collision.title")}
            </h2>
            <p className="mt-0.5 font-mono text-[10px] text-zinc-500">
              {row.pattern_id ? `${row.pattern_id} · ` : ""}
              {row.primary_axis ?? "—"}
            </p>
          </div>
          <button
            type="button"
            className="rounded border border-zinc-600 px-2 py-0.5 text-[10px] text-zinc-400 hover:bg-zinc-800"
            onClick={onClose}
          >
            {t("pattern.collision.close")}
          </button>
        </div>

        <p className="mb-2 rounded border border-zinc-800 bg-black/40 px-2 py-1 font-mono text-[10px] text-amber-100/90">
          Affinity_Match = {(aff * 100).toFixed(1)}%
        </p>

        <section className="mb-2 space-y-1 rounded border border-zinc-800/80 bg-zinc-900/50 p-2">
          <p className="text-[10px] font-semibold uppercase tracking-wide text-violet-300/90">
            {t("pattern.collision.gating")}
          </p>
          {minE != null && !Number.isNaN(minE) ? (
            <p className="font-mono text-zinc-300">
              min_energy (法典): <span className="text-amber-200/90">≥ {(minE * 100).toFixed(1)}%</span>
            </p>
          ) : (
            <p className="text-zinc-500">{t("pattern.collision.gatingUnset")}</p>
          )}
          {maxS != null && !Number.isNaN(maxS) ? (
            <p className="font-mono text-zinc-300">
              max_self_energy (法典): <span className="text-amber-200/90">≤ {(maxS * 100).toFixed(1)}%</span>
            </p>
          ) : null}
          <p className="text-[10px] font-semibold text-zinc-400">{t("pattern.collision.actual")}</p>
          <p className="font-mono text-zinc-200">
            {row.primary_axis ?? "axis"}:{" "}
            {typeof pae === "number" && Number.isFinite(pae) ? (
              <span className={gatePass ? "text-emerald-300/95" : "text-rose-300/95"}>
                = {(pae * 100).toFixed(1)}%
              </span>
            ) : (
              <span className="text-zinc-500">—</span>
            )}
          </p>
          <p className={`text-[10px] font-semibold ${gatePass ? "text-emerald-400/90" : "text-rose-400/90"}`}>
            {gatePass ? t("pattern.collision.gatePass") : t("pattern.collision.gateFail")}
          </p>
        </section>

        <section className="space-y-2">
          <p className="text-[10px] font-semibold uppercase tracking-wide text-rose-300/90">
            {t("pattern.collision.redline")}
          </p>
          <div className="rounded border border-rose-900/40 bg-rose-950/20 px-2 py-1.5">
            <p className="text-[10px] font-semibold uppercase tracking-wide text-rose-200/95">
              {t("pattern.collision.exclusionSnapshots")}
            </p>
            <p className="mt-0.5 text-[9px] leading-snug text-rose-200/70">{t("pattern.collision.exclusionSnapshotsHint")}</p>
          </div>
          {row.exclusion_axis_snapshots?.length ? (
            <ul className="space-y-1.5">
              {row.exclusion_axis_snapshots.map((s) => {
                const ePct = (s.energy * 100).toFixed(1);
                const tPct = (s.threshold * 100).toFixed(1);
                const label = s.label_zh || s.axis;
                return (
                  <li
                    key={s.axis}
                    className={`rounded border px-2 py-1.5 font-mono text-[10px] leading-relaxed ${
                      s.triggered
                        ? "border-rose-500/80 bg-rose-950/55 text-rose-50"
                        : "border-zinc-700/60 bg-zinc-900/40 text-zinc-400"
                    }`}
                  >
                    <div className="mb-0.5 text-[9px] font-semibold uppercase tracking-wide text-zinc-500">
                      {s.axis}
                      {s.label_zh ? <span className="ml-1 font-normal normal-case text-zinc-400">({s.label_zh})</span> : null}
                    </div>
                    <div className="text-[10px]">
                      <span className="text-zinc-500">{t("pattern.collision.axisEnergy")}</span>{" "}
                      <span
                        className={
                          s.triggered
                            ? "font-semibold text-rose-400 drop-shadow-[0_0_6px_rgba(251,113,133,0.35)]"
                            : "text-zinc-200"
                        }
                      >
                        {ePct}%
                      </span>
                      <span className="mx-1 text-zinc-600">{s.triggered ? ">" : "≤"}</span>
                      <span className="text-zinc-500">{t("pattern.collision.redlineThreshold")}</span>{" "}
                      <span className={s.triggered ? "text-amber-200/90" : "text-emerald-300/80"}>{tPct}%</span>
                    </div>
                    {s.triggered ? (
                      <p className="mt-1 border-t border-rose-500/30 pt-1 text-[10px] font-semibold text-rose-300">
                        {t("pattern.collision.breachLine")
                          .replace("{label}", label)
                          .replace("{energy}", ePct)
                          .replace("{threshold}", tPct)}
                      </p>
                    ) : (
                      <p className="mt-0.5 text-[9px] text-zinc-500">{t("pattern.collision.belowRedline")}</p>
                    )}
                  </li>
                );
              })}
            </ul>
          ) : (
            <p className="text-zinc-500">{t("pattern.collision.noSnapshots")}</p>
          )}
          {row.exclusion_hit ? (
            <p className="rounded border border-rose-600/50 bg-rose-950/35 px-2 py-1 text-[10px] font-semibold text-rose-200">
              {t("pattern.collision.redlineActive")}
            </p>
          ) : null}
        </section>
      </div>
    </div>
  );
}
