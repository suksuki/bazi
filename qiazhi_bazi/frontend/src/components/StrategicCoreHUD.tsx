"use client";

type Props = {
  structureFinalDecision?: Record<string, unknown>;
  pluginWeights?: { blindSchool: number; wangshuai: number };
  onPickDeity?: (deity: string) => void;
  hasReboundRisk?: boolean;
  energyPeak?: number;
  /** L1 global_entropy：越高顶部应力条脉冲越快 */
  globalEntropy?: number | null;
  diagnosticHint?: string;
  genderLabel?: string;
  t?: (s: string) => string;
};

export function StrategicCoreHUD({
  structureFinalDecision = {},
  pluginWeights = { blindSchool: 0.8, wangshuai: 0.6 },
  onPickDeity,
  hasReboundRisk = false,
  energyPeak = 0,
  globalEntropy = null,
  diagnosticHint = "",
  genderLabel = "",
  t = (s: string) => s,
}: Props) {
  const useful = ((structureFinalDecision as { utility_god?: string[] }).utility_god || []) as string[];
  const obstacle = ((structureFinalDecision as { obstacle_god?: string[] }).obstacle_god || []) as string[];
  const climate = ((structureFinalDecision as { climate_adjustment?: { summary?: string } }).climate_adjustment || {});
  const title = String((structureFinalDecision as { primary_structure_humanized?: string }).primary_structure_humanized || "");
  const summary = title.includes("建禄")
    ? t("当前为【建禄格】，物理能量处于溢出状态，排水（泄耗）是优先策略。")
    : title.includes("月劫")
      ? t("当前为【月劫格】，争夺态明显，需以食伤泄压并谨慎控风险。")
      : title.includes("身强无依")
        ? t("当前为【身强无依】，核能空转，必须建立有效做功出口。")
        : "";
  const roleHint = genderLabel === "female"
    ? t("女性语义：官杀常映射事业/伴侣压力轴；用忌建议侧重官杀链路稳定性。")
    : genderLabel === "male"
      ? t("男性语义：财星常映射财富/伴侣压力轴；用忌建议侧重财星链路稳定性。")
      : "";
  const conflictReport = ((structureFinalDecision as { plugin_conflict_report?: { tension_level?: number; zone?: string; divergence_notes?: string[] } }).plugin_conflict_report || {});
  const tensionLevel = Number(conflictReport.tension_level || 0);
  const zone = String(conflictReport.zone || "BLUE");
  const conflictColor = zone === "RED" ? "from-rose-500 to-red-300" : zone === "YELLOW" ? "from-amber-500 to-yellow-300" : "from-sky-500 to-cyan-300";
  const overloaded = zone === "RED" && tensionLevel > 0.8;
  const totalWeight = Math.max(0.0001, Number(pluginWeights.blindSchool || 0) + Number(pluginWeights.wangshuai || 0));
  const blindPct = Math.round((Number(pluginWeights.blindSchool || 0) / totalWeight) * 100);
  const wanshuaiPct = 100 - blindPct;
  const entropyPulseSec =
    typeof globalEntropy === "number" && Number.isFinite(globalEntropy)
      ? Math.max(0.75, 2.1 - globalEntropy * 1.65)
      : null;
  const entropyStress = typeof globalEntropy === "number" && globalEntropy >= 0.4;
  if (!useful.length && !obstacle.length && !climate.summary) return null;
  return (
    <section
      className={`mb-3 rounded-xl border border-zinc-700 bg-zinc-950 p-3 transition-all ${overloaded ? "animate-pulse shadow-[0_0_18px_rgba(130,0,20,0.45)]" : ""} ${entropyStress ? "shadow-[0_0_14px_rgba(220,90,40,0.22)]" : ""}`}
    >
      <div
        className={`mb-2 h-1 w-full rounded bg-gradient-to-r ${conflictColor} ${zone === "RED" || entropyStress ? "animate-pulse" : ""}`}
        style={{
          opacity: Math.max(0.35, Math.min(1, tensionLevel)),
          ...(entropyPulseSec ? { animationDuration: `${entropyPulseSec}s` } : {}),
        }}
      />
      <div className="mb-2 rounded border border-zinc-700 bg-zinc-900 px-2 py-1 text-[11px] text-zinc-300">
        {t("话语权占比：盲派 {blPct}% | 旺衰 {wPct}%").replace("{blPct}", String(blindPct)).replace("{wPct}", String(wanshuaiPct))}
      </div>
      <p className="mb-2 text-xs text-zinc-400">{t("战略核心看板（Strategic HUD）")}</p>
      {Array.isArray(conflictReport.divergence_notes) && conflictReport.divergence_notes.length > 0 ? (
        <div className="mb-2 rounded border border-zinc-700 bg-zinc-900 px-2 py-1 text-[11px] text-zinc-300">
          {t(String(conflictReport.divergence_notes[0] || ""))}
        </div>
      ) : null}
      {genderLabel ? (
        <div className="mb-2 inline-flex rounded border border-zinc-700 bg-zinc-900 px-2 py-0.5 text-[11px] text-zinc-300">
          {t("性别坐标：")}
          {genderLabel === "male" ? t("乾造（男）") : t("坤造（女）")}
        </div>
      ) : null}
      {roleHint ? (
        <div className="mb-2 rounded border border-zinc-700 bg-zinc-900 px-2 py-1 text-[11px] text-zinc-300">
          {roleHint}
        </div>
      ) : null}
      {summary ? (
        <div className={`mb-2 rounded border px-2 py-1 text-[11px] ${title.includes("身强无依") ? "border-amber-500/40 bg-amber-500/10 text-amber-200" : "border-zinc-700 bg-zinc-900 text-zinc-300"}`}>
          {title.includes("身强无依") ? "⚠ " : ""}
          {summary}
        </div>
      ) : null}
      {diagnosticHint ? (
        <div className="mb-2 rounded border border-amber-500/50 bg-amber-500/10 px-2 py-1 text-[11px] text-amber-200">
          ⚠ {diagnosticHint}
        </div>
      ) : null}
      {energyPeak > 0 ? (
        <div className="mb-2 rounded border border-fuchsia-600/40 bg-fuchsia-500/10 px-2 py-1 text-[11px] text-fuchsia-200">
          <p className="mb-1">
            {t("峰值能量（Abs）:")} {energyPeak.toFixed(2)}
          </p>
          <div className="h-1.5 w-full overflow-hidden rounded bg-zinc-800">
            <div className="h-full bg-fuchsia-400/80" style={{ width: `${Math.max(5, Math.min(100, energyPeak))}%` }} />
          </div>
        </div>
      ) : null}
      <div className="grid grid-cols-1 gap-2 md:grid-cols-3">
        <div className="rounded border border-emerald-600/40 bg-emerald-500/10 p-2 text-[11px] text-emerald-200">
          <p className="mb-1">{t("用神（能量出口）")}</p>
          <p>
            {(useful.length ? useful : ["-"]).map((item, idx) => (
              <button key={`use-${idx}`} type="button" className="mr-1 underline decoration-dotted" onMouseEnter={() => onPickDeity?.(item)} onClick={() => onPickDeity?.(item)}>
                {item}
              </button>
            ))}
          </p>
        </div>
        <div className={`rounded border border-rose-600/40 bg-rose-500/10 p-2 text-[11px] text-rose-200 ${hasReboundRisk ? "animate-pulse shadow-[0_0_12px_rgba(244,63,94,0.35)]" : ""}`}>
          <p className="mb-1">{t("忌神（坍塌风险）")}</p>
          <p>
            {(obstacle.length ? obstacle : ["-"]).map((item, idx) => (
              <button key={`obs-${idx}`} type="button" className="mr-1 underline decoration-dotted" onMouseEnter={() => onPickDeity?.(item)} onClick={() => onPickDeity?.(item)}>
                {item}
              </button>
            ))}
          </p>
        </div>
        <div className="rounded border border-sky-600/40 bg-sky-500/10 p-2 text-[11px] text-sky-200">
          <p className="mb-1">{t("调候（硬修正）")}</p>
          <p>{climate.summary ? t(String(climate.summary)) : t("已启用")}</p>
        </div>
      </div>
    </section>
  );
}
