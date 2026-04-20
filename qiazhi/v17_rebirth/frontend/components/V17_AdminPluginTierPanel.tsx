"use client";

type PluginAdminRowLite = {
  layer: string;
  layer_dir: string;
  module: string;
  plugin_id: string;
  display_name?: string;
  definition_text?: string;
  display_definition?: string;
  function_summary?: string;
  display_description?: string;
  detail_description?: string;
  design_rationale?: string;
  technical_label?: string;
  causal_tier: number;
  execution_order?: number;
  kind: string;
  activated?: boolean;
  config_required?: boolean;
  config_exists?: boolean;
  config_file?: string;
  policy_valid?: boolean;
  policy_errors?: string[];
};

type PluginRuntimeStatusLite = {
  fact_count?: number;
  proposal_count?: number;
  decision_count?: number;
  status?: string;
  target_god?: string;
  reason?: string;
};

type PluginClaimLite = {
  target_god?: string;
  projection_share?: number;
  cluster_projection?: Record<string, unknown>;
  match_ratio?: number;
};

type PluginConflictLite = {
  conflict_id: string;
  conflict_type?: string;
  severity?: string;
  conflict_score?: number;
  why_conflict?: string;
  recommended_arbiter?: string;
  routing_reason?: string;
  routing_policy?: string;
  routing_scores?: Record<string, number>;
  plugins?: string[];
};

type PluginConflictResolutionLite = {
  conflict_id: string;
  resolved_by?: string;
  policy?: string;
  winner_claim_id?: string;
  applied_to_settlement?: boolean;
  next_queue?: string;
  reason?: string;
  status?: string;
};

type RecomputeContributionLite = {
  target_god?: string;
  before?: number;
  after?: number;
  ratio_total?: number;
  delta_abs?: number;
};

type PluginPanelRow = {
  plugin: PluginAdminRowLite;
  runtime?: PluginRuntimeStatusLite;
  relatedClaims: PluginClaimLite[];
  relatedConflicts: PluginConflictLite[];
};

type PluginCategoryBucket = {
  key: string;
  label: string;
  rows: PluginPanelRow[];
};

type PluginTierBucket = {
  tier: string;
  title: string;
  rows: PluginPanelRow[];
  categories: PluginCategoryBucket[];
};

type ConflictGroupLite = {
  key: string;
  severity: string;
  recommended_arbiter: string;
  conflict_type: string;
  target_god: string;
  conflict_ids: string[];
  max_conflict_score: number;
  conflicts: PluginConflictLite[];
};

type Props = {
  pluginTierBuckets: PluginTierBucket[];
  recomputeContributions: RecomputeContributionLite[];
  resolveBusyKeys: string[];
  pluginConflictResolutions: PluginConflictResolutionLite[];
  pluginCardTitle: (row: PluginAdminRowLite) => string;
  pluginCardDefinition: (row: PluginAdminRowLite) => string;
  pluginCardDescription: (row: PluginAdminRowLite) => string;
  runtimeStatusTone: (status?: string) => string;
  runtimeStatusLabel: (status?: string) => string;
  compactProjection: (projection: unknown) => string;
  buildConflictGroups: (conflicts: PluginConflictLite[], resolutions: PluginConflictResolutionLite[]) => ConflictGroupLite[];
  conflictTone: (severity?: string) => string;
  formatArbiterLabel: (value?: string) => string;
  resolveRoutingPolicy: (conflict: PluginConflictLite) => string;
  compactRoutingScores: (scores?: Record<string, number>) => string;
  resolveConflictByRule: (group: ConflictGroupLite, busyKey: string) => Promise<void>;
  resolveConflictBatch: (conflictIds: string[], arbiter: "system" | "llm" | "user", busyKey: string) => Promise<void>;
};

export function V17_AdminPluginTierPanel({
  pluginTierBuckets,
  recomputeContributions,
  resolveBusyKeys,
  pluginConflictResolutions,
  pluginCardTitle,
  pluginCardDefinition,
  pluginCardDescription,
  runtimeStatusTone,
  runtimeStatusLabel,
  compactProjection,
  buildConflictGroups,
  conflictTone,
  formatArbiterLabel,
  resolveRoutingPolicy,
  compactRoutingScores,
  resolveConflictByRule,
  resolveConflictBatch,
}: Props) {
  return (
    <div className="space-y-3">
      {pluginTierBuckets.map((tierBlock) => (
        <details key={tierBlock.tier} className="rounded-xl border border-zinc-800 bg-zinc-950/40 p-3" open>
          <summary className="cursor-pointer list-none">
            <div className="flex items-center justify-between text-xs">
              <span className="font-semibold text-zinc-100">{tierBlock.title}</span>
              <span className="text-zinc-400">{tierBlock.rows.length} 个插件</span>
            </div>
          </summary>
          <div className="mt-3 space-y-3">
            {tierBlock.categories.map((category) => (
              <div key={`${tierBlock.tier}-${category.key}`} className="space-y-2">
                <div className="text-[11px] font-semibold text-zinc-300">
                  {category.label} · {category.rows.length} 个
                </div>
                <div className="space-y-2">
                  {category.rows.map(({ plugin: p, runtime, relatedClaims, relatedConflicts }) => {
                    const runtimeStatus = String(runtime?.status || "未知");
                    const runtimeTone = runtimeStatusTone(runtimeStatus);
                    const matchValues = relatedClaims
                      .map((row) => Number(row.match_ratio || 0))
                      .filter((value) => Number.isFinite(value) && value > 0);
                    const avgMatch = matchValues.length
                      ? matchValues.reduce((sum, value) => sum + value, 0) / matchValues.length
                      : null;
                    const pluginTargets = Array.from(
                      new Set(
                        [
                          String(runtime?.target_god || "").trim(),
                          ...relatedClaims.map((row) => String(row.target_god || "").trim()),
                        ].filter(Boolean),
                      ),
                    );
                    const relatedContribution = recomputeContributions.find((row) =>
                      pluginTargets.includes(String(row.target_god || "").trim()),
                    );
                    const topClaim = [...relatedClaims].sort(
                      (a, b) => Number(b.match_ratio || 0) - Number(a.match_ratio || 0),
                    )[0];
                    const projectionText = compactProjection(topClaim?.cluster_projection);
                    return (
                      <div key={p.plugin_id} className="rounded-xl border border-zinc-800 bg-zinc-950/40 p-3">
                        <div className="flex items-center justify-between">
                          <div>
                            <div className="font-bold text-zinc-200">{pluginCardTitle(p)}</div>
                            <div className="text-[10px] text-zinc-500">层级: {p.causal_tier} · 顺序: {p.execution_order}</div>
                            <div className="mt-1 text-[10px] text-zinc-400">{p.technical_label || p.plugin_id}</div>
                          </div>
                          <div className={`rounded px-2 py-0.5 text-[10px] ${p.activated ? "bg-emerald-900/40 text-emerald-400" : "bg-zinc-800 text-zinc-500"}`}>
                            {p.activated ? "已启用" : "未启用"}
                          </div>
                        </div>
                        <div className="mt-2 flex items-center gap-2 text-[10px]">
                          <span className={`rounded px-2 py-0.5 uppercase ${runtimeTone}`}>{runtimeStatusLabel(runtimeStatus)}</span>
                          <span className={`rounded px-2 py-0.5 ${p.policy_valid === false ? "bg-rose-950/40 text-rose-300" : "bg-emerald-950/30 text-emerald-300"}`}>
                            {p.policy_valid === false ? "策略告警" : "策略正常"}
                          </span>
                          {runtime?.target_god ? <span className="text-zinc-500">目标 {runtime.target_god}</span> : null}
                          {typeof runtime?.fact_count === "number" ? <span className="text-zinc-600">事实 {runtime.fact_count}</span> : null}
                          {typeof runtime?.proposal_count === "number" ? <span className="text-zinc-600">建议 {runtime.proposal_count}</span> : null}
                          {typeof runtime?.decision_count === "number" ? <span className="text-zinc-600">裁决 {runtime.decision_count}</span> : null}
                          <span className="text-zinc-600">主张 {relatedClaims.length}</span>
                          <span className="text-zinc-600">冲突 {relatedConflicts.length}</span>
                          {avgMatch !== null ? <span className="text-emerald-300">命中 {(avgMatch * 100).toFixed(0)}%</span> : null}
                          {relatedContribution ? <span className="text-sky-300">位移 {Number(relatedContribution.delta_abs || 0).toFixed(2)}</span> : null}
                        </div>
                        <div className="mt-1 text-[10px] text-zinc-300">{pluginCardDefinition(p)}</div>
                        <div className="mt-1 text-[10px] text-zinc-500">{runtime?.reason || pluginCardDescription(p)}</div>
                        {topClaim ? (
                          <div className="mt-2 rounded-lg border border-zinc-800 bg-zinc-950/60 p-2 text-[10px] text-zinc-300">
                            <div className="flex flex-wrap items-center justify-between gap-2">
                              <span className="text-fuchsia-200">主落点 {String(topClaim.target_god || "未定目标")}</span>
                              <span className="text-fuchsia-300">匹配 {Math.round(Number(topClaim.match_ratio || 0) * 100)}%</span>
                            </div>
                            <div className="mt-1 text-zinc-500">
                              匹配 {Math.round(Number(topClaim.projection_share || 0) * 100)}%
                              {projectionText ? ` · ${projectionText}` : ""}
                            </div>
                          </div>
                        ) : null}
                        {relatedContribution ? (
                          <div className="mt-1 text-[10px] text-zinc-400">
                            重算贡献：{String(relatedContribution.target_god || "—")} {Number(relatedContribution.before || 0).toFixed(2)} → {Number(relatedContribution.after || 0).toFixed(2)}
                            {" · "}比例 {Number(relatedContribution.ratio_total || 0).toFixed(3)}
                            {" · "}delta {Number(relatedContribution.delta_abs || 0).toFixed(2)}
                          </div>
                        ) : null}
                        {p.config_required ? (
                          <div className="mt-1 text-[10px] text-zinc-500">配置: {p.config_exists ? p.config_file || "已存在" : "缺失"}</div>
                        ) : null}
                        {Array.isArray(p.policy_errors) && p.policy_errors.length ? (
                          <div className="mt-1 space-y-1 text-[10px] text-rose-300">
                            {p.policy_errors.slice(0, 3).map((msg) => (
                              <div key={`${p.plugin_id}_${msg}`}>策略: {msg}</div>
                            ))}
                          </div>
                        ) : null}
                        {(() => {
                          const relatedGroups = buildConflictGroups(relatedConflicts, pluginConflictResolutions);
                          return relatedGroups.length ? (
                            <div className="mt-2 space-y-2">
                              {relatedGroups.slice(0, 5).map((group) => {
                                const sample = group.conflicts[0];
                                const firstConflictId = String(sample.conflict_id || "").trim();
                                const busyKey = `${p.plugin_id}|${group.key}`;
                                const isBusy = resolveBusyKeys.includes(busyKey);
                                return (
                                  <div key={group.key} className="rounded-lg border border-zinc-800 bg-zinc-950/70 p-2">
                                    <div className="flex items-center justify-between gap-2">
                                      <span className={`rounded px-2 py-0.5 text-[10px] uppercase ${conflictTone(group.severity)}`}>
                                        {group.severity || "P3"} · {formatArbiterLabel(group.recommended_arbiter)}
                                      </span>
                                      <span className="rounded border border-zinc-700 px-2 py-1 text-[10px] text-zinc-500">
                                        {group.conflict_type || "冲突"}
                                      </span>
                                    </div>
                                    <div className="mt-1 text-[10px] text-zinc-300">
                                      目标 {group.target_god} · {group.conflict_ids.length} 条 · 评分 {group.max_conflict_score.toFixed(3)}
                                    </div>
                                    <div className="mt-1 text-[10px] text-zinc-500">
                                      裁决策略 {resolveRoutingPolicy(sample)} · {sample.routing_policy || sample.routing_reason || "路由原因待补充"}
                                    </div>
                                    {compactRoutingScores(sample.routing_scores || undefined) ? (
                                      <div className="mt-1 text-[10px] text-zinc-500">
                                        路由候选分数 {compactRoutingScores(sample.routing_scores || undefined)}
                                      </div>
                                    ) : null}
                                    <div className="mt-1 text-[10px] text-zinc-500">{sample?.why_conflict || "—"}</div>
                                    {firstConflictId ? <div className="mt-1 text-[10px] text-zinc-500">示例冲突 {firstConflictId}</div> : null}
                                    {group.conflicts.slice(0, 2).map((conflict) => {
                                      const plugins = Array.isArray(conflict.plugins) ? conflict.plugins : [];
                                      return (
                                        <div key={conflict.conflict_id} className="mt-1 text-[10px] text-zinc-400">
                                          · {conflict.why_conflict || conflict.conflict_id || "—"}
                                          {plugins.length ? `（来源插件 ${plugins.length} 个）` : ""}
                                        </div>
                                      );
                                    })}
                                    <div className="mt-2 flex items-center gap-2">
                                      <button
                                        type="button"
                                        disabled={isBusy}
                                        onClick={() => void resolveConflictByRule(group, busyKey)}
                                        className="rounded border border-emerald-700 px-2 py-1 text-[10px] text-emerald-300 disabled:opacity-40"
                                      >
                                        规则裁决
                                      </button>
                                      <button
                                        type="button"
                                        disabled={isBusy}
                                        onClick={() => void resolveConflictBatch(group.conflict_ids, "system", busyKey)}
                                        className="rounded border border-zinc-700 px-2 py-1 text-[10px] text-zinc-300 disabled:opacity-40"
                                      >
                                        系统批量裁决
                                      </button>
                                      <button
                                        type="button"
                                        disabled={isBusy}
                                        onClick={() => void resolveConflictBatch(group.conflict_ids, "llm", busyKey)}
                                        className="rounded border border-zinc-700 px-2 py-1 text-[10px] text-zinc-300 disabled:opacity-40"
                                        title="按冲突批量提交给 LLM"
                                      >
                                        LLM 批量裁决
                                      </button>
                                      <button
                                        type="button"
                                        disabled={isBusy}
                                        onClick={() => void resolveConflictBatch(group.conflict_ids, "user", busyKey)}
                                        className="rounded border border-zinc-700 px-2 py-1 text-[10px] text-zinc-300 disabled:opacity-40"
                                      >
                                        人工裁决
                                      </button>
                                    </div>
                                  </div>
                                );
                              })}
                            </div>
                          ) : null;
                        })()}
                      </div>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        </details>
      ))}
    </div>
  );
}
