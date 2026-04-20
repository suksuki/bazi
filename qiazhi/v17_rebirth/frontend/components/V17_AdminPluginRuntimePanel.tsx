"use client";

type KnowledgeSnapshotLite = {
  claim_history?: {
    total_claims?: number;
  };
  conflict_history?: {
    total_conflicts?: number;
    recommended_arbiters?: Record<string, number>;
    feedback_arbiters?: Record<string, number>;
    feedback_arbiter_scores?: Record<string, number>;
  };
  resolution_preview?: {
    total_suggestions?: number;
  };
};

type BrainActionLite = {
  action_id?: string;
  conflict_id?: string;
  action_type?: string;
  queue?: string;
  confidence?: number;
  reason?: string;
};

type PluginConflictLite = {
  conflict_id: string;
  conflict_type?: string;
  severity?: string;
  why_conflict?: string;
  recommended_arbiter?: string;
  routing_reason?: string;
  routing_policy?: string;
  routing_scores?: Record<string, number>;
};

type PluginConflictResolutionLite = {
  resolved_by?: string;
  next_queue?: string;
  reason?: string;
  policy?: string;
};

type BrainTimelineRowLite = {
  conflict: PluginConflictLite;
  resolution?: PluginConflictResolutionLite;
  action?: BrainActionLite;
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
  pluginRuntimeSessionId: string;
  setPluginRuntimeSessionId: (value: string) => void;
  resolvedPluginRuntimeSessionId: string;
  loadPlugins: () => Promise<void>;
  scannedPluginCount: number;
  hitPluginCount: number;
  inboxPluginCount: number;
  policyWarnCount: number;
  knowledgeSnapshot: KnowledgeSnapshotLite;
  brainActionQueue: BrainActionLite[];
  recomputeContributionCount: number;
  pluginPolicyFilter: "all" | "warn";
  setPluginPolicyFilter: (value: "all" | "warn") => void;
  resolveBusyKeys: string[];
  pendingConflictGroups: ConflictGroupLite[];
  resolveAllConflictByRule: (groups: ConflictGroupLite[]) => Promise<void>;
  brainTimeline: BrainTimelineRowLite[];
  formatQueueLabel: (value?: string) => string;
  formatArbiterLabel: (value?: string) => string;
  conflictTone: (severity?: string) => string;
  brainStepTone: (value?: string) => string;
  resolveRoutingPolicy: (conflict: PluginConflictLite) => string;
  compactRoutingScores: (scores?: Record<string, number>) => string;
};

function statPill(label: string, value: number | string, tone = "text-zinc-300") {
  return (
    <span className="rounded-full border border-zinc-800 bg-zinc-950/70 px-3 py-1 text-[10px] text-zinc-500">
      {label} <span className={`ml-1 font-semibold ${tone}`}>{value}</span>
    </span>
  );
}

export function V17_AdminPluginRuntimePanel({
  pluginRuntimeSessionId,
  setPluginRuntimeSessionId,
  resolvedPluginRuntimeSessionId,
  loadPlugins,
  scannedPluginCount,
  hitPluginCount,
  inboxPluginCount,
  policyWarnCount,
  knowledgeSnapshot,
  brainActionQueue,
  recomputeContributionCount,
  pluginPolicyFilter,
  setPluginPolicyFilter,
  resolveBusyKeys,
  pendingConflictGroups,
  resolveAllConflictByRule,
  brainTimeline,
  formatQueueLabel,
  formatArbiterLabel,
  conflictTone,
  brainStepTone,
  resolveRoutingPolicy,
  compactRoutingScores,
}: Props) {
  return (
    <div className="space-y-4">
      <section className="rounded-2xl border border-zinc-800 bg-[radial-gradient(circle_at_top_left,rgba(34,211,238,0.10),transparent_35%),linear-gradient(180deg,rgba(24,24,27,0.9),rgba(9,9,11,0.96))] p-4 shadow-[0_0_0_1px_rgba(39,39,42,0.2)]">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h2 className="text-lg font-semibold text-zinc-100">插件运行图谱</h2>
            <p className="mt-1 text-[11px] text-zinc-400">
              统一查看插件家族、命中层、决策入口、冲突层与重算贡献。
            </p>
          </div>
          <div className="rounded-full border border-cyan-500/20 bg-cyan-950/20 px-3 py-1 text-[10px] text-cyan-200">
            Session · {resolvedPluginRuntimeSessionId || "default"}
          </div>
        </div>

        <div className="mt-4 flex flex-wrap items-center gap-2">
          <input
            className="w-full rounded-xl border border-zinc-800 bg-zinc-950/80 px-3 py-2 text-xs text-zinc-200 outline-none transition focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/20 md:w-80"
            placeholder="session_id（留 default 自动回退最近活跃会话）"
            value={pluginRuntimeSessionId}
            onChange={(e) => setPluginRuntimeSessionId(e.target.value)}
          />
          <button
            onClick={() => void loadPlugins()}
            className="rounded-xl border border-cyan-500/40 bg-cyan-950/30 px-3 py-2 text-xs font-medium text-cyan-100 transition hover:border-cyan-400 hover:bg-cyan-950/40"
          >
            刷新运行态
          </button>
        </div>

        <div className="mt-4 flex flex-wrap gap-2">
          {statPill("已扫描", scannedPluginCount)}
          {statPill("命中", hitPluginCount, "text-emerald-300")}
          {statPill("入队", inboxPluginCount, "text-amber-300")}
          {statPill("策略告警", policyWarnCount, "text-rose-300")}
          {statPill("主张", Number(knowledgeSnapshot.claim_history?.total_claims || 0), "text-fuchsia-300")}
          {statPill("冲突", Number(knowledgeSnapshot.conflict_history?.total_conflicts || 0), "text-orange-300")}
          {statPill("建议", Number(knowledgeSnapshot.resolution_preview?.total_suggestions || 0), "text-cyan-300")}
          {statPill("大脑动作", brainActionQueue.length)}
          {statPill("重算", recomputeContributionCount)}
        </div>

        <div className="mt-3 flex flex-wrap gap-2">
          {statPill("偏好 系统", Number(knowledgeSnapshot.conflict_history?.recommended_arbiters?.system || 0))}
          {statPill("偏好 LLM", Number(knowledgeSnapshot.conflict_history?.recommended_arbiters?.llm || 0))}
          {statPill("偏好 用户", Number(knowledgeSnapshot.conflict_history?.recommended_arbiters?.user || 0))}
          {statPill("反馈 系统", Number((knowledgeSnapshot.conflict_history?.feedback_arbiters || {}).system || 0))}
          {statPill("反馈 LLM", Number((knowledgeSnapshot.conflict_history?.feedback_arbiters || {}).llm || 0))}
          {statPill("反馈 用户", Number((knowledgeSnapshot.conflict_history?.feedback_arbiters || {}).user || 0))}
          {statPill("得分 系统", Number((knowledgeSnapshot.conflict_history?.feedback_arbiter_scores || {}).system || 0).toFixed(2))}
          {statPill("得分 LLM", Number((knowledgeSnapshot.conflict_history?.feedback_arbiter_scores || {}).llm || 0).toFixed(2))}
          {statPill("得分 用户", Number((knowledgeSnapshot.conflict_history?.feedback_arbiter_scores || {}).user || 0).toFixed(2))}
        </div>
      </section>

      <section className="flex flex-wrap items-center gap-2 rounded-2xl border border-zinc-800 bg-zinc-950/40 p-3">
        <button
          type="button"
          onClick={() => setPluginPolicyFilter("all")}
          className={`rounded-xl border px-3 py-1.5 text-xs transition ${
            pluginPolicyFilter === "all"
              ? "border-zinc-300 bg-zinc-100 text-zinc-900"
              : "border-zinc-700 bg-zinc-950 text-zinc-300 hover:border-zinc-500"
          }`}
        >
          全部插件
        </button>
        <button
          type="button"
          onClick={() => setPluginPolicyFilter("warn")}
          className={`rounded-xl border px-3 py-1.5 text-xs transition ${
            pluginPolicyFilter === "warn"
              ? "border-rose-300 bg-rose-100 text-rose-900"
              : "border-zinc-700 bg-zinc-950 text-zinc-300 hover:border-zinc-500"
          }`}
        >
          只看策略告警
        </button>
        <button
          type="button"
          disabled={resolveBusyKeys.includes("auto_rule_all_conflicts") || pendingConflictGroups.length === 0}
          onClick={() => void resolveAllConflictByRule(pendingConflictGroups)}
          className="rounded-xl border border-emerald-500/50 bg-emerald-950/20 px-3 py-1.5 text-xs text-emerald-200 transition hover:border-emerald-400 disabled:opacity-40"
        >
          规则自动裁决
        </button>
        <span className="text-[10px] text-zinc-500">规则：P1→系统，P2→LLM，P3→人工</span>
        <span className="text-[10px] text-zinc-500">
          当前视图：{pluginPolicyFilter === "warn" ? "仅显示策略告警插件" : "显示全部插件"}
        </span>
      </section>

      <div className="grid gap-4 xl:grid-cols-2">
        <section className="rounded-2xl border border-zinc-800 bg-zinc-950/40 p-3">
          <div className="mb-2 flex items-center justify-between">
            <div className="text-[11px] font-semibold text-zinc-300">大脑动作队列</div>
            <div className="text-[10px] text-zinc-500">{brainActionQueue.length} 条</div>
          </div>
          <div className="space-y-2">
            {brainActionQueue.length ? (
              brainActionQueue.slice(0, 6).map((row, idx) => (
                <div key={row.action_id || `brain_${idx}`} className="rounded-xl border border-zinc-800 bg-zinc-950/70 p-3">
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-[10px] uppercase tracking-wide text-sky-300">
                      {row.action_type || "大脑动作"}
                    </span>
                    <span className="rounded-full border border-zinc-700 px-2 py-0.5 text-[10px] text-zinc-500">
                      {formatQueueLabel(row.queue)}
                    </span>
                  </div>
                  <div className="mt-2 text-[10px] text-zinc-300">{row.reason || "—"}</div>
                  <div className="mt-2 text-[10px] text-zinc-500">
                    冲突 {row.conflict_id || "—"} / 置信度 {Number(row.confidence || 0).toFixed(2)}
                  </div>
                </div>
              ))
            ) : (
              <div className="rounded-xl border border-dashed border-zinc-800 bg-zinc-950/50 px-4 py-6 text-center text-[11px] text-zinc-500">
                当前暂无大脑动作队列。
              </div>
            )}
          </div>
        </section>

        <section className="rounded-2xl border border-zinc-800 bg-zinc-950/40 p-3">
          <div className="mb-2 flex items-center justify-between">
            <div className="text-[11px] font-semibold text-zinc-300">大脑时间线</div>
            <div className="text-[10px] text-zinc-500">{brainTimeline.length} 条</div>
          </div>
          <div className="space-y-2">
            {brainTimeline.length ? (
              brainTimeline.map((row, idx) => (
                <div key={row.conflict.conflict_id || `timeline_${idx}`} className="rounded-xl border border-zinc-800 bg-zinc-950/70 p-3">
                  <div className="text-[10px] uppercase tracking-wide text-zinc-400">
                    {row.conflict.conflict_type || "冲突"} · {row.conflict.conflict_id || "—"}
                  </div>
                  <div className="mt-2 flex flex-wrap items-center gap-2 text-[10px]">
                    <span className={`rounded-full border border-zinc-700 px-2 py-1 ${conflictTone(row.conflict.severity)}`}>
                      冲突 · {row.conflict.severity || "P?"}
                    </span>
                    <span className={`rounded-full border border-zinc-700 px-2 py-1 ${brainStepTone(row.resolution?.resolved_by || row.conflict.recommended_arbiter)}`}>
                      裁决 · {formatArbiterLabel(row.resolution?.resolved_by || row.conflict.recommended_arbiter)}
                    </span>
                    <span className={`rounded-full border border-zinc-700 px-2 py-1 ${brainStepTone(row.action?.action_type || row.resolution?.policy)}`}>
                      大脑动作 · {formatArbiterLabel(row.action?.action_type || row.resolution?.policy)}
                    </span>
                    <span className={`rounded-full border border-zinc-700 px-2 py-1 ${brainStepTone(row.action?.queue || row.resolution?.resolved_by)}`}>
                      队列 · {formatQueueLabel(row.action?.queue || row.resolution?.next_queue)}
                    </span>
                  </div>
                  <div className="mt-2 text-[10px] text-zinc-400">
                    {row.action?.reason || row.resolution?.reason || row.conflict.why_conflict || "—"}
                  </div>
                  <div className="mt-1 text-[10px] text-zinc-500">
                    裁决策略 {resolveRoutingPolicy(row.conflict)} · {row.conflict.routing_policy || row.conflict.routing_reason || "路由原因待补充"}
                  </div>
                  {compactRoutingScores(row.conflict.routing_scores || undefined) ? (
                    <div className="mt-1 text-[10px] text-zinc-500">
                      路由候选分数 {compactRoutingScores(row.conflict.routing_scores || undefined)}
                    </div>
                  ) : null}
                </div>
              ))
            ) : (
              <div className="rounded-xl border border-dashed border-zinc-800 bg-zinc-950/50 px-4 py-6 text-center text-[11px] text-zinc-500">
                当前暂无冲突到动作的时间线数据。
              </div>
            )}
          </div>
        </section>
      </div>
    </div>
  );
}
