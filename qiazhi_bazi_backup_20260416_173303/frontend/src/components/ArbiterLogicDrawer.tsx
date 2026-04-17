"use client";

type Props = {
  open: boolean;
  title: string;
  focus: string;
  details: string[];
  deityTrace?: Record<string, unknown> | null;
  auditSource?: Record<string, unknown> | null;
  onClose: () => void;
  onApplySql?: () => Promise<void> | void;
};

export function ArbiterLogicDrawer({
  open,
  title,
  focus,
  details,
  deityTrace = null,
  auditSource,
  onClose,
  onApplySql,
}: Props) {
  const hideNoiseByDefault = true;
  const baseEnergy = (deityTrace && typeof deityTrace === "object" ? (deityTrace as { base_energy?: Record<string, unknown> }).base_energy : null) || null;
  const interventions = (deityTrace && typeof deityTrace === "object" ? (deityTrace as { interventions?: Record<string, unknown> }).interventions : null) || null;
  const normalization = (deityTrace && typeof deityTrace === "object" ? (deityTrace as { normalization?: Record<string, unknown> }).normalization : null) || null;
  const rootStrength = (deityTrace && typeof deityTrace === "object" ? (deityTrace as { root_strength?: Record<string, unknown> }).root_strength : null) || null;
  const contributionSources = ((baseEnergy?.contribution_sources as Array<Record<string, unknown>> | undefined) || []).slice(0, 8);
  const appliedParams = ((interventions?.applied_params as Record<string, number> | undefined) || {});
  const hasTrace = Boolean(baseEnergy || interventions || normalization);
  return (
    <aside
      className={`fixed bottom-0 right-0 z-50 h-[68vh] w-full max-w-xl overflow-y-auto border-l border-t border-zinc-800 bg-zinc-950 p-4 pr-3 shadow-2xl transition-transform duration-300 ${
        open ? "translate-x-0" : "translate-x-[110%]"
      }`}
    >
      <div className="mb-3 flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-zinc-100">{title || "Arbiter Logic Drawer"}</h3>
          <p className="text-xs text-zinc-500">Focus: {focus || "N/A"}</p>
        </div>
        <button type="button" onClick={onClose} className="rounded border border-zinc-700 bg-zinc-900 px-2 py-1 text-xs text-zinc-300">
          关闭
        </button>
      </div>

      <section className={hideNoiseByDefault ? "hidden" : "rounded-xl border border-zinc-800 bg-zinc-900 p-3"}>
        <h4 className="text-xs font-medium text-zinc-300">挑刺对话流</h4>
        <div className="mt-2 space-y-2">
          {details.length === 0 ? <p className="text-xs text-zinc-500">暂无对话内容。</p> : null}
          {details.map((x, i) => (
            <p
              key={`drawer-detail-${i}`}
              className="min-w-0 max-w-full break-words whitespace-pre-wrap rounded-lg border border-zinc-800 bg-zinc-950 px-2 py-1 text-xs text-zinc-300 [overflow-wrap:anywhere]"
            >
              {x}
            </p>
          ))}
        </div>
      </section>

      {hasTrace ? (
        <section className="mt-3 rounded-xl border border-sky-800/70 bg-sky-950/20 p-3">
          <h4 className="text-xs font-medium text-sky-200">演算全息简报</h4>

          <div className="mt-2 rounded-lg border border-zinc-800 bg-zinc-950 p-2">
            <p className="text-[11px] font-medium text-zinc-300">[基础动能]</p>
            <p className="mt-1 text-[11px] text-zinc-400">Raw: {String(baseEnergy?.raw_deity_energy ?? 0)}</p>
            <div className="mt-1 space-y-1">
              {contributionSources.length === 0 ? <p className="text-[11px] text-zinc-500">无贡献源明细。</p> : null}
              {contributionSources.map((s, idx) => (
                <p key={`src-${idx}`} className="text-[11px] text-zinc-400">
                  {String(s.source ?? "unknown")} (+{String(s.contribution_energy ?? 0)})
                </p>
              ))}
            </div>
          </div>

          <div className="mt-2 rounded-lg border border-zinc-800 bg-zinc-950 p-2">
            <p className="text-[11px] font-medium text-zinc-300">[物理干预]</p>
            <div className="mt-1 flex flex-wrap gap-1">
              {Object.keys(appliedParams).length === 0 ? <p className="text-[11px] text-zinc-500">无参数信息。</p> : null}
              {Object.entries(appliedParams).map(([k, v]) => {
                const isHard = k.startsWith("CF_") || k === "A_PROTRUSION";
                return (
                  <span
                    key={k}
                    className={`rounded border px-1.5 py-0.5 text-[10px] ${
                      isHard ? "border-sky-500/50 bg-sky-500/10 font-semibold text-sky-200" : "border-zinc-700 bg-zinc-900 text-zinc-400"
                    }`}
                  >
                    {k}={String(v)}
                  </span>
                );
              })}
            </div>
          </div>

          <div className="mt-2 rounded-lg border border-zinc-800 bg-zinc-950 p-2">
            <p className="text-[11px] font-medium text-zinc-300">[归一化校准]</p>
            <p className="mt-1 text-[11px] text-zinc-400">
              {String(normalization?.final_energy_before_pct ?? 0)} / {String(normalization?.all_deities_final_energy_sum ?? 1)} * 100
              {" => "}
              {String(normalization?.final_percent ?? 0)}%
            </p>
            <p className="text-[10px] text-zinc-500">{String(normalization?.formula ?? "")}</p>
          </div>

          <div className="mt-2 rounded-lg border border-zinc-800 bg-zinc-950 p-2">
            <p className="text-[11px] font-medium text-zinc-300">[通根强度表]</p>
            <div className="mt-1 text-[11px] text-zinc-400">
              <p>root_sources: {((rootStrength?.root_sources as string[] | undefined) || []).join(", ") || "none"}</p>
              <p>stem_sources: {((rootStrength?.stem_sources as string[] | undefined) || []).join(", ") || "none"}</p>
              <p>is_floating: {String(rootStrength?.is_floating ?? false)}</p>
              <p>root_score: {String(rootStrength?.root_score ?? 0)}%</p>
              <p>stem_score: {String(rootStrength?.stem_score ?? 0)}%</p>
              <p className={`${rootStrength?.is_floating ? "text-rose-300" : "text-emerald-300"}`}>
                Floating_Decay: {rootStrength?.is_floating ? "Active" : "Inactive"}
              </p>
            </div>
          </div>
        </section>
      ) : null}

      <div className={hideNoiseByDefault ? "hidden" : "mt-3 flex items-center gap-2"}>
        <button
          type="button"
          onClick={() => void onApplySql?.()}
          className="rounded border border-emerald-500/40 bg-emerald-500/10 px-2 py-1 text-xs text-emerald-300"
        >
          在抽屉中应用参数建议
        </button>
      </div>

      <section className="mt-3 rounded-xl border border-zinc-800 bg-zinc-900 p-3">
        <h4 className="text-xs font-medium text-zinc-300">AuditLog 溯源</h4>
        <pre className="mt-2 max-h-56 overflow-auto rounded border border-zinc-800 bg-zinc-950 p-2 text-[11px] text-zinc-400">
          {JSON.stringify(auditSource || {}, null, 2)}
        </pre>
      </section>
    </aside>
  );
}
