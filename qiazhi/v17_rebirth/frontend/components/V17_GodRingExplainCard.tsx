"use client";

type LooseRecord = Record<string, unknown>;

function asRecord(value: unknown): LooseRecord {
  return value && typeof value === "object" && !Array.isArray(value) ? (value as LooseRecord) : {};
}

function asString(value: unknown, fallback = ""): string {
  if (typeof value === "string") return value;
  if (typeof value === "number" || typeof value === "boolean") return String(value);
  return fallback;
}

function asNumber(value: unknown, fallback = 0): number {
  const next = Number(value);
  return Number.isFinite(next) ? next : fallback;
}

function asStringArray(value: unknown): string[] {
  return Array.isArray(value)
    ? value.map((item) => String(item || "").trim()).filter(Boolean)
    : [];
}

function asStringMatrix(value: unknown): string[] {
  if (typeof value === "string") {
    return value
      .split(",")
      .map((item) => item.trim())
      .filter(Boolean);
  }
  return asStringArray(value);
}

function candidateTone(score: number): string {
  if (score >= 0.75) return "border-emerald-500/30 bg-emerald-950/25 text-emerald-200";
  if (score >= 0.45) return "border-cyan-500/30 bg-cyan-950/25 text-cyan-200";
  return "border-zinc-700 bg-zinc-950/70 text-zinc-300";
}

function netTone(value: number): string {
  if (value >= 0.4) return "text-emerald-300";
  if (value <= -0.2) return "text-rose-300";
  return "text-zinc-300";
}

function scopeLabel(value: string): string {
  const normalized = value.trim().toLowerCase();
  if (normalized === "natal" || normalized === "natal_basis") return "原局";
  if (normalized === "luck") return "大运";
  if (normalized === "flow") return "流年";
  if (normalized === "runtime" || normalized === "mixed") return "运流联动";
  return value || "来源待定";
}

function biasPairs(value: unknown): Array<[string, number]> {
  return Object.entries(asRecord(value))
    .map(([god, raw]) => [god, asNumber(raw)] as [string, number])
    .filter(([god, score]) => Boolean(god) && score > 0)
    .sort((left, right) => right[1] - left[1]);
}

function stageBiasRows(value: unknown) {
  return Object.entries(asRecord(value))
    .map(([god, raw]) => {
      const row = asRecord(raw);
      return {
        god: String(god || "").trim(),
        lu: asNumber(row.lu),
        blade: asNumber(row.blade),
        general: asNumber(row.general),
        useBoost: asNumber(row.use_boost),
        tabooBoost: asNumber(row.taboo_boost),
        stabilityBoost: asNumber(row.stability_boost),
        volatilityBoost: asNumber(row.volatility_boost),
      };
    })
    .filter((row) => row.god && Math.max(row.lu, row.blade, row.general, row.useBoost, row.tabooBoost) > 0)
    .sort(
      (left, right) =>
        right.useBoost + right.tabooBoost + right.lu + right.blade - (left.useBoost + left.tabooBoost + left.lu + left.blade),
    )
    .slice(0, 6);
}

export function V17_GodRingExplainCard({
  godRings,
  focusedDecisionId,
  onFocusDecision,
}: {
  godRings?: Record<string, unknown>;
  focusedDecisionId?: string;
  onFocusDecision?: (decisionId: string) => void;
}) {
  const row = asRecord(godRings);
  const displayMode = asString(row.display_mode).trim();
  const authorityMode = displayMode === "authority";
  const mode = asString(row.mode, authorityMode ? "authority" : "pending").trim();
  const source = asString(row.source, "待定").trim();
  const confidence = asNumber(row.confidence);
  const pathCount = asNumber(row.core_path_count);

  const useGods = asStringArray(row.god_of_use);
  const tabooGods = asStringArray(row.god_of_taboo);
  const useCandidates = Array.isArray(row.core_use_candidates)
    ? (row.core_use_candidates as LooseRecord[])
    : [];
  const tabooCandidates = Array.isArray(row.core_taboo_candidates)
    ? (row.core_taboo_candidates as LooseRecord[])
    : [];
  const dualRoleCandidates = Array.isArray(row.dual_role_candidates)
    ? (row.dual_role_candidates as LooseRecord[])
    : [];
  const effectScores = asRecord(row.effect_scores);
  const graphMeta = asRecord(row.core_graph_meta);
  const positiveTargets = asRecord(graphMeta.positive_targets);
  const negativeTargets = asRecord(graphMeta.negative_targets);
  const pathPreview = Array.isArray(row.core_paths_preview)
    ? (row.core_paths_preview as LooseRecord[])
    : [];
  const judgementBias = asRecord(row.judgement_bias);
  const stageBias = stageBiasRows(row.stage_bias);
  const judgementUseBias = biasPairs(judgementBias.use_bias).slice(0, 6);
  const judgementTabooBias = biasPairs(judgementBias.taboo_bias).slice(0, 6);
  const judgementBiasEntries = Array.isArray(row.judgement_bias_entries)
    ? (row.judgement_bias_entries as LooseRecord[])
        .map((item) => {
          const entry = asRecord(item);
          const sourceLabel = asString(entry.source_label || entry.decision_label || entry.plugin_id).trim();
          const reason = asString(entry.reason).trim();
          const decisionId = asString(entry.decision_id).trim();
          const usePairs = biasPairs(entry.use_bias);
          const tabooPairs = biasPairs(entry.taboo_bias);
          if (!sourceLabel || (!usePairs.length && !tabooPairs.length)) return null;
          return { sourceLabel, reason, decisionId, usePairs, tabooPairs };
        })
        .filter(Boolean) as Array<{
          sourceLabel: string;
          reason: string;
          decisionId: string;
          usePairs: Array<[string, number]>;
          tabooPairs: Array<[string, number]>;
        }>
    : [];

  const effectRows = Object.entries(effectScores)
    .map(([god, raw]) => [god, asRecord(raw)] as const)
    .sort(
      (left, right) =>
        asNumber(right[1].net_utility) - asNumber(left[1].net_utility) ||
        asNumber(right[1].harm_score) - asNumber(left[1].harm_score),
    )
    .slice(0, 6);

  return (
    <section className="rounded-2xl border border-cyan-500/20 bg-[linear-gradient(180deg,rgba(8,47,73,0.36),rgba(9,9,11,0.84))] p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="text-[11px] uppercase tracking-[0.24em] text-cyan-300/80">
            God Ring Explain
          </div>
          <h3 className="mt-2 text-sm font-semibold text-cyan-50">体用裁决说明</h3>
          <p className="mt-1 text-[11px] leading-6 text-zinc-400">
            这里展示核心层如何把六柱、大运、流年与关系做功折算成用神、忌神和双刃神。
          </p>
        </div>
        <div className="flex flex-wrap gap-2 text-[10px]">
          <span
            className={`rounded-full border px-3 py-1 ${
              authorityMode
                ? "border-emerald-500/30 bg-emerald-950/20 text-emerald-200"
                : "border-amber-500/30 bg-amber-950/20 text-amber-200"
            }`}
          >
            {authorityMode ? "权威体用" : "等待权威裁决"}
          </span>
          <span className="rounded-full border border-cyan-500/20 bg-cyan-950/25 px-3 py-1 text-cyan-200">
            模式 {mode}
          </span>
          <span className="rounded-full border border-zinc-700 bg-zinc-950/70 px-3 py-1 text-zinc-300">
            置信 {Math.round(confidence * 100)}%
          </span>
          <span className="rounded-full border border-zinc-700 bg-zinc-950/70 px-3 py-1 text-zinc-300">
            路径 {pathCount}
          </span>
        </div>
      </div>

      {!authorityMode ? (
        <div className="mt-4 rounded-xl border border-dashed border-amber-500/25 bg-amber-950/15 px-4 py-3 text-[12px] leading-6 text-amber-100/90">
          当前尚未拿到核心层的权威体用结果。主页面已经停止把“主导/弱势十神”冒充成用神/忌神；待核心路径完成后，这里会亮起完整解释。
        </div>
      ) : (
        <>
          <div className="mt-4 grid gap-4 xl:grid-cols-[0.96fr,1.04fr]">
            <div className="grid gap-4">
              <div className="rounded-xl border border-zinc-800 bg-zinc-950/55 p-3">
                <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
                  <div className="text-[11px] font-semibold text-zinc-300">体用候选</div>
                  <div className="text-[10px] text-zinc-500">来源 {source}</div>
                </div>
                <div className="grid gap-3 md:grid-cols-2">
                  <div>
                    <div className="mb-2 text-[10px] uppercase tracking-[0.16em] text-emerald-300">用神候选</div>
                    <div className="flex flex-wrap gap-2">
                      {(useCandidates.length
                        ? useCandidates
                        : useGods.map((god) => ({ god, score: confidence })) as LooseRecord[]
                      ).map((item, idx) => {
                        const god = asString(item.god || useGods[idx] || "").trim();
                        const score = asNumber(item.score, confidence);
                        return (
                          <span
                            key={`use_${god}_${idx}`}
                            className={`rounded-full border px-3 py-1 text-[10px] ${candidateTone(score)}`}
                          >
                            用 {god || "未定"} · {Math.round(score * 100)}%
                          </span>
                        );
                      })}
                    </div>
                  </div>
                  <div>
                    <div className="mb-2 text-[10px] uppercase tracking-[0.16em] text-rose-300">忌神候选</div>
                    <div className="flex flex-wrap gap-2">
                      {(tabooCandidates.length
                        ? tabooCandidates
                        : tabooGods.map((god) => ({ god, score: confidence })) as LooseRecord[]
                      ).map((item, idx) => {
                        const god = asString(item.god || tabooGods[idx] || "").trim();
                        const score = asNumber(item.score, confidence);
                        return (
                          <span
                            key={`taboo_${god}_${idx}`}
                            className={`rounded-full border px-3 py-1 text-[10px] ${
                              score >= 0.5
                                ? "border-rose-500/30 bg-rose-950/20 text-rose-200"
                                : "border-amber-500/30 bg-amber-950/20 text-amber-200"
                            }`}
                          >
                            忌 {god || "未定"} · {Math.round(score * 100)}%
                          </span>
                        );
                      })}
                    </div>
                  </div>
                </div>
              </div>

              {stageBias.length ? (
                <div className="rounded-xl border border-zinc-800 bg-zinc-950/55 p-3">
                  <div className="mb-2 flex items-center justify-between gap-2">
                    <div className="text-[11px] font-semibold text-zinc-300">禄刃阶段偏置</div>
                    <div className="text-[10px] text-zinc-500">为何会推用 / 推忌</div>
                  </div>
                  <div className="space-y-2 text-[10px] text-zinc-300">
                    {stageBias.map((entry) => (
                      <div key={`stage_bias_${entry.god}`} className="rounded-lg border border-zinc-800 bg-zinc-950/60 px-3 py-2">
                        <div className="flex flex-wrap items-center justify-between gap-2">
                          <span className="font-medium text-zinc-100">{entry.god}</span>
                          <span className="text-zinc-500">
                            禄 {entry.lu.toFixed(2)} · 刃 {entry.blade.toFixed(2)} · 长生 {entry.general.toFixed(2)}
                          </span>
                        </div>
                        <div className="mt-2 flex flex-wrap gap-2">
                          {entry.useBoost > 0 ? (
                            <span className="rounded-full border border-emerald-500/30 bg-emerald-950/25 px-3 py-1 text-emerald-200">
                              推用 +{entry.useBoost.toFixed(2)}
                            </span>
                          ) : null}
                          {entry.tabooBoost > 0 ? (
                            <span className="rounded-full border border-rose-500/30 bg-rose-950/25 px-3 py-1 text-rose-200">
                              推忌 +{entry.tabooBoost.toFixed(2)}
                            </span>
                          ) : null}
                          {entry.stabilityBoost > 0 ? (
                            <span className="rounded-full border border-cyan-500/30 bg-cyan-950/25 px-3 py-1 text-cyan-200">
                              稳定 +{entry.stabilityBoost.toFixed(2)}
                            </span>
                          ) : null}
                          {entry.volatilityBoost > 0 ? (
                            <span className="rounded-full border border-amber-500/30 bg-amber-950/25 px-3 py-1 text-amber-200">
                              波动 +{entry.volatilityBoost.toFixed(2)}
                            </span>
                          ) : null}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ) : null}

              <div className="rounded-xl border border-zinc-800 bg-zinc-950/55 p-3">
                <div className="mb-2 text-[11px] font-semibold text-zinc-300">双刃神与引动热区</div>
                <div className="grid gap-3 lg:grid-cols-2">
                  <div className="rounded-lg border border-zinc-800 bg-zinc-950/60 p-3">
                    <div className="mb-2 text-[10px] uppercase tracking-[0.16em] text-fuchsia-300">双刃神</div>
                    <div className="flex flex-wrap gap-2">
                      {dualRoleCandidates.length ? (
                        dualRoleCandidates.map((item, idx) => {
                          const god = asString(item.god).trim();
                          const benefit = asNumber(item.benefit);
                          const risk = asNumber(item.risk);
                          return (
                            <span
                              key={`dual_${god}_${idx}`}
                              className="rounded-full border border-fuchsia-500/30 bg-fuchsia-950/20 px-3 py-1 text-[10px] text-fuchsia-200"
                            >
                              {god || "未定"} · 利 {benefit.toFixed(2)} / 害 {risk.toFixed(2)}
                            </span>
                          );
                        })
                      ) : (
                        <span className="text-[11px] text-zinc-500">当前无显著双刃神。</span>
                      )}
                    </div>
                  </div>
                  <div className="rounded-lg border border-zinc-800 bg-zinc-950/60 p-3">
                    <div className="mb-2 text-[10px] uppercase tracking-[0.16em] text-cyan-300">引动热区</div>
                    <div className="space-y-2">
                      <div className="rounded-lg border border-zinc-800 bg-zinc-950/60 px-3 py-2">
                        <div className="mb-1 text-[10px] text-zinc-500">正向引动</div>
                        <div className="flex flex-wrap gap-2">
                          {Object.keys(positiveTargets).length ? (
                            Object.entries(positiveTargets).map(([god, raw]) => (
                              <span
                                key={`pos_${god}`}
                                className="rounded-full border border-emerald-500/20 bg-emerald-950/20 px-2 py-1 text-[10px] text-emerald-200"
                              >
                                {god} {asNumber(raw).toFixed(2)}
                              </span>
                            ))
                          ) : (
                            <span className="text-[11px] text-zinc-500">暂无。</span>
                          )}
                        </div>
                      </div>
                      <div className="rounded-lg border border-zinc-800 bg-zinc-950/60 px-3 py-2">
                        <div className="mb-1 text-[10px] text-zinc-500">负向引动</div>
                        <div className="flex flex-wrap gap-2">
                          {Object.keys(negativeTargets).length ? (
                            Object.entries(negativeTargets).map(([god, raw]) => (
                              <span
                                key={`neg_${god}`}
                                className="rounded-full border border-amber-500/20 bg-amber-950/20 px-2 py-1 text-[10px] text-amber-200"
                              >
                                {god} {asNumber(raw).toFixed(2)}
                              </span>
                            ))
                          ) : (
                            <span className="text-[11px] text-zinc-500">暂无。</span>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="grid gap-4">
              <div className="rounded-xl border border-zinc-800 bg-zinc-950/55 p-3">
                <div className="mb-3 flex items-center justify-between gap-2">
                  <div className="text-[11px] font-semibold text-zinc-300">判定 Bias 账本</div>
                  <div className="text-[10px] text-zinc-500">谁在推动体用</div>
                </div>
                <div className="grid gap-3 lg:grid-cols-2">
                  <div className="rounded-lg border border-zinc-800 bg-zinc-950/60 p-3">
                    <div className="mb-2 text-[10px] uppercase tracking-[0.16em] text-emerald-300">用侧推动</div>
                    <div className="flex flex-wrap gap-2">
                      {judgementUseBias.length ? (
                        judgementUseBias.map(([god, score]) => (
                          <span
                            key={`judgement_use_${god}`}
                            className="rounded-full border border-emerald-500/30 bg-emerald-950/25 px-3 py-1 text-[10px] text-emerald-200"
                          >
                            {god} +{score.toFixed(2)}
                          </span>
                        ))
                      ) : (
                        <span className="text-[11px] text-zinc-500">暂无。</span>
                      )}
                    </div>
                  </div>
                  <div className="rounded-lg border border-zinc-800 bg-zinc-950/60 p-3">
                    <div className="mb-2 text-[10px] uppercase tracking-[0.16em] text-rose-300">忌侧推动</div>
                    <div className="flex flex-wrap gap-2">
                      {judgementTabooBias.length ? (
                        judgementTabooBias.map(([god, score]) => (
                          <span
                            key={`judgement_taboo_${god}`}
                            className="rounded-full border border-rose-500/30 bg-rose-950/25 px-3 py-1 text-[10px] text-rose-200"
                          >
                            {god} +{score.toFixed(2)}
                          </span>
                        ))
                      ) : (
                        <span className="text-[11px] text-zinc-500">暂无。</span>
                      )}
                    </div>
                  </div>
                </div>
                <div className="mt-3 space-y-2 text-[10px] text-zinc-400">
                  {judgementBiasEntries.length ? (
                    judgementBiasEntries.slice(0, 6).map((entry, idx) => {
                      const isFocused = Boolean(entry.decisionId && focusedDecisionId && entry.decisionId === focusedDecisionId);
                      return (
                        <div key={`bias_entry_${idx}_${entry.sourceLabel}`} className="rounded-lg border border-zinc-800 bg-zinc-950/60 px-3 py-2">
                          <div className="flex flex-wrap items-center justify-between gap-2">
                            <span className="font-medium text-zinc-100">{entry.sourceLabel}</span>
                            {entry.reason ? <span className="text-zinc-500">{entry.reason}</span> : null}
                          </div>
                          <div className="mt-1 space-y-1">
                            {entry.usePairs.length ? (
                              <div className="break-words text-emerald-200/90">
                                用侧：{entry.usePairs.map(([god, score]) => `${god} +${score.toFixed(2)}`).join(" · ")}
                              </div>
                            ) : null}
                            {entry.tabooPairs.length ? (
                              <div className="break-words text-rose-200/90">
                                忌侧：{entry.tabooPairs.map(([god, score]) => `${god} +${score.toFixed(2)}`).join(" · ")}
                              </div>
                            ) : null}
                          </div>
                          {entry.decisionId ? (
                            <div className="mt-2 flex flex-wrap items-center gap-2">
                              <span className="rounded-full border border-zinc-700 bg-zinc-900/70 px-2 py-1 text-[10px] text-zinc-300">
                                ID {entry.decisionId}
                              </span>
                              <button
                                type="button"
                                onClick={() => onFocusDecision?.(entry.decisionId)}
                                className={`rounded-full border px-2 py-1 transition ${
                                  isFocused
                                    ? "border-emerald-500/35 bg-emerald-950/25 text-emerald-200"
                                    : "border-cyan-500/20 bg-cyan-950/20 text-cyan-200 hover:bg-cyan-900/35"
                                }`}
                              >
                                {isFocused ? "已联动到决策" : "联动决策"}
                              </button>
                            </div>
                          ) : null}
                        </div>
                      );
                    })
                  ) : (
                    <div className="rounded-lg border border-dashed border-zinc-800 px-3 py-4 text-zinc-500">
                      当前没有来自判定性插件的 bias 账本。
                    </div>
                  )}
                </div>
              </div>

              <div className="rounded-xl border border-zinc-800 bg-zinc-950/55 p-3">
                <div className="mb-3 flex items-center justify-between gap-2">
                  <div className="text-[11px] font-semibold text-zinc-300">效应分数</div>
                  <div className="text-[10px] text-zinc-500">
                    raw / contest / release / resolved
                  </div>
                </div>
                <div className="space-y-2 text-[10px] text-zinc-400">
                  {effectRows.length ? (
                    effectRows.map(([god, item]) => {
                      const net = asNumber(item.net_utility);
                      const resolved = asNumber(item.resolved_utility);
                      const rawBenefit = asNumber(item.raw_benefit);
                      const rawHarm = asNumber(item.raw_harm);
                      const contest = asNumber(item.contest_pressure);
                      const release = asNumber(item.release_pressure);
                      const contestPairs = asStringMatrix(item.contest_pairs);
                      const contestDamp = asNumber(item.contest_weight);
                      const releaseBoost = asNumber(item.release_weight);
                      return (
                        <div key={god} className="rounded-lg border border-zinc-800 bg-zinc-950/60 px-3 py-2">
                          <div className="flex items-center justify-between gap-3">
                            <span className="font-medium text-zinc-100">{god}</span>
                            <span className={`font-mono ${netTone(net)}`}>
                              net {net.toFixed(2)} / resolved {resolved.toFixed(2)}
                            </span>
                          </div>
                          <div className="mt-2 grid gap-2 sm:grid-cols-2">
                            <span>原始利 {rawBenefit.toFixed(2)} / 原始害 {rawHarm.toFixed(2)}</span>
                            <span>
                              对抗 {contest.toFixed(2)}（抑制权重 {contestDamp.toFixed(2)}） /
                              通道 {release.toFixed(2)}（提升权重 {releaseBoost.toFixed(2)}）
                            </span>
                          </div>
                          <div className="mt-2 grid gap-2 sm:grid-cols-3">
                            <span>利 {asNumber(item.benefit_score).toFixed(2)}</span>
                            <span>害 {asNumber(item.harm_score).toFixed(2)}</span>
                            <span>稳定 {asNumber(item.stability_score).toFixed(2)} / 激活 {asNumber(item.activation_score).toFixed(2)}</span>
                          </div>
                          <div className="mt-2 flex flex-wrap gap-1.5">
                            {contestPairs.length ? (
                              contestPairs.map((pair) => (
                                <span
                                  key={`${god}_pair_${pair}`}
                                  className="rounded-full border border-zinc-700/90 bg-zinc-900/70 px-2 py-1 text-[10px] text-zinc-300"
                                >
                                  对抗对 {pair}
                                </span>
                              ))
                            ) : (
                              <span className="text-[11px] text-zinc-500">无显著对抗对</span>
                            )}
                          </div>
                        </div>
                      );
                    })
                  ) : (
                    <div className="rounded-lg border border-dashed border-zinc-800 px-3 py-4 text-zinc-500">
                      当前还没有可展示的效应分数。
                    </div>
                  )}
                </div>
              </div>

              <div className="rounded-xl border border-zinc-800 bg-zinc-950/55 p-3">
                <div className="mb-3 flex items-center justify-between gap-2">
                  <div className="text-[11px] font-semibold text-zinc-300">做功路径预览</div>
                  <div className="text-[10px] text-zinc-500">前 6 条核心链路</div>
                </div>
                <div className="space-y-2 text-[10px] text-zinc-400">
                  {pathPreview.length ? (
                    pathPreview.slice(0, 6).map((item, idx) => {
                      const target = asString(item.target_god, "未定目标").trim();
                      const pathType = asString(item.path_type, "path").trim();
                      const participants = asStringArray(item.participants);
                      const originScope = scopeLabel(asString(item.origin_scope).trim());
                      const net = asNumber(item.net_effect);
                      const evidence = asRecord(item.evidence);
                      const sourceLabel = asString(evidence.source_label || evidence.plugin_id || evidence.source).trim();
                      const decisionLabel = asString(evidence.decision_label).trim();
                      const decisionId = asString(evidence.decision_id).trim();
                      const conditionState = asString(evidence.condition_state).trim();
                      const layer = asString(evidence.layer).trim();
                      const isFocused = Boolean(decisionId && focusedDecisionId && decisionId === focusedDecisionId);
                      return (
                        <div key={`path_${idx}_${target}`} className="rounded-lg border border-zinc-800 bg-zinc-950/60 px-3 py-2">
                          <div className="flex flex-wrap items-center justify-between gap-2">
                            <span className="font-medium text-zinc-100">
                              {target} · {pathType}
                            </span>
                            <span className={`font-mono ${netTone(net)}`}>net {net.toFixed(2)}</span>
                          </div>
                          <div className="mt-1 text-zinc-500">
                            {participants.length ? participants.join(" -> ") : "单点路径"} · {originScope}
                          </div>
                          {sourceLabel || decisionLabel || decisionId ? (
                            <div className="mt-2 flex flex-wrap gap-2 text-[10px]">
                              {sourceLabel ? (
                                <span className="rounded-full border border-cyan-500/20 bg-cyan-950/20 px-2 py-1 text-cyan-200">
                                  插件 {sourceLabel}
                                </span>
                              ) : null}
                              {decisionLabel ? (
                                <span className="rounded-full border border-violet-500/20 bg-violet-950/20 px-2 py-1 text-violet-200">
                                  决策 {decisionLabel}
                                </span>
                              ) : null}
                              {decisionId ? (
                                <span className="rounded-full border border-zinc-700 bg-zinc-900/70 px-2 py-1 text-zinc-300">
                                  ID {decisionId}
                                </span>
                              ) : null}
                              {layer ? (
                                <span className="rounded-full border border-zinc-700 bg-zinc-900/70 px-2 py-1 text-zinc-300">
                                  层 {layer}
                                </span>
                              ) : null}
                              {conditionState ? (
                                <span className="rounded-full border border-zinc-700 bg-zinc-900/70 px-2 py-1 text-zinc-300">
                                  态 {conditionState}
                                </span>
                              ) : null}
                              {decisionId ? (
                                <button
                                  type="button"
                                  onClick={() => onFocusDecision?.(decisionId)}
                                  className={`rounded-full border px-2 py-1 transition ${
                                    isFocused
                                      ? "border-emerald-500/35 bg-emerald-950/25 text-emerald-200"
                                      : "border-violet-500/20 bg-violet-950/20 text-violet-200 hover:bg-violet-900/35"
                                  }`}
                                >
                                  {isFocused ? "已联动到决策" : "联动决策"}
                                </button>
                              ) : null}
                            </div>
                          ) : null}
                          <div className="mt-2 grid gap-2 sm:grid-cols-4">
                            <span>激活 {asNumber(item.activation).toFixed(2)}</span>
                            <span>传导 {asNumber(item.transmission).toFixed(2)}</span>
                            <span>损耗 {asNumber(item.loss).toFixed(2)}</span>
                            <span>稳定 {asNumber(item.stability).toFixed(2)}</span>
                          </div>
                        </div>
                      );
                    })
                  ) : (
                    <div className="rounded-lg border border-dashed border-zinc-800 px-3 py-4 text-zinc-500">
                      当前还没有做功路径预览。
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </>
      )}
    </section>
  );
}
