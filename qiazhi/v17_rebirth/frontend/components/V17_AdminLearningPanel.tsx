"use client";

import { useState } from "react";

type LooseRecord = Record<string, unknown>;

export type LearningCampaignUiConfig = {
  maxMinutes: number;
  maxExtendedCases: string;
  requestLlmReview: boolean;
};

export type LearningCampaignRuntime = {
  status?: string;
  progress_percent?: number;
  current_step?: string;
  current_step_label?: string;
  estimated_remaining_seconds?: number;
  started_at?: string;
  completed_at?: string;
  message?: string;
  latest_report?: LooseRecord;
  latest_report_markdown?: string;
  config?: LooseRecord;
};

type Props = {
  campaign: LearningCampaignRuntime;
  config: LearningCampaignUiConfig;
  setConfig: (next: LearningCampaignUiConfig) => void;
  loading: boolean;
  onStart: () => void;
  onPause: () => void;
  onRefresh: () => void;
};

function asRecord(value: unknown): LooseRecord {
  return value && typeof value === "object" && !Array.isArray(value) ? (value as LooseRecord) : {};
}

function asNumber(value: unknown, fallback = 0): number {
  const next = Number(value);
  return Number.isFinite(next) ? next : fallback;
}

function statusTone(status: string): string {
  if (status === "running") return "border-cyan-500/30 bg-cyan-950/25 text-cyan-100";
  if (status === "completed") return "border-emerald-500/30 bg-emerald-950/25 text-emerald-100";
  if (status === "failed") return "border-rose-500/30 bg-rose-950/25 text-rose-100";
  if (status === "paused" || status === "pause_requested") return "border-amber-500/30 bg-amber-950/25 text-amber-100";
  return "border-zinc-700 bg-zinc-950/60 text-zinc-300";
}

function statusLabel(status: string): string {
  if (status === "running") return "运行中";
  if (status === "completed") return "已完成";
  if (status === "failed") return "失败";
  if (status === "paused") return "已暂停";
  if (status === "pause_requested") return "暂停请求中";
  return "待启动";
}

function formatDuration(seconds: unknown): string {
  const raw = Math.max(0, Math.round(asNumber(seconds)));
  const hours = Math.floor(raw / 3600);
  const minutes = Math.floor((raw % 3600) / 60);
  const sec = raw % 60;
  if (hours > 0) return `${hours}h ${minutes}m`;
  if (minutes > 0) return `${minutes}m ${sec}s`;
  return `${sec}s`;
}

function scoreRows(report: LooseRecord) {
  const scorecard = asRecord(report.scorecard);
  const batch = asRecord(report.synthetic_batch);
  const extended = asRecord(report.extended_synthetic);
  const practitioner = asRecord(report.practitioner_benchmarks);
  return [
    { label: "Synthetic Batch", value: `${asNumber(batch.passed_count)}/${asNumber(batch.case_count)}`, hint: "批量代表样盘" },
    { label: "Extended Lab", value: `${asNumber(extended.passed_count)}/${asNumber(extended.case_count)}`, hint: "完整实验室矩阵" },
    { label: "Benchmark", value: `${asNumber(practitioner.passed_count)}/${asNumber(practitioner.case_count)}`, hint: "真实校盘基准" },
    { label: "Findings", value: `${asNumber(scorecard.finding_count)}`, hint: "异常 / 待审计" },
  ];
}

export function V17_AdminLearningPanel({
  campaign,
  config,
  setConfig,
  loading,
  onStart,
  onPause,
  onRefresh,
}: Props) {
  const [copied, setCopied] = useState(false);
  const status = String(campaign.status || "idle");
  const progress = Math.max(0, Math.min(100, asNumber(campaign.progress_percent)));
  const report = asRecord(campaign.latest_report);
  const reportMarkdown = String(campaign.latest_report_markdown || "");
  const scorecard = asRecord(report.scorecard);
  const llmPackage = asRecord(report.llm_review_package);
  const feedbackItems = Array.isArray(report.analyst_feedback_items) ? report.analyst_feedback_items : [];
  const parameterExperiments = Array.isArray(report.parameter_experiments) ? report.parameter_experiments : [];
  const coverage = asRecord(report.plugin_governance_coverage);

  async function copyReport() {
    const payload = reportMarkdown || JSON.stringify(report, null, 2);
    if (!payload.trim()) return;
    try {
      await navigator.clipboard.writeText(payload);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1600);
    } catch {
      setCopied(false);
    }
  }

  return (
    <section className="space-y-5">
      <div className="rounded-3xl border border-cyan-500/20 bg-[radial-gradient(circle_at_top_left,rgba(34,211,238,0.12),transparent_30%),rgba(9,9,11,0.72)] p-5">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="text-[11px] uppercase tracking-[0.28em] text-cyan-300/80">Learning Campaign</div>
            <h2 className="mt-2 text-xl font-semibold text-zinc-50">自动学习控制台</h2>
            <p className="mt-2 max-w-3xl text-xs leading-6 text-zinc-400">
              自动跑合成矩阵、真实校盘、影子调参和反馈包。这里负责“学习与审计”，不会直接改写真实参数。
            </p>
          </div>
          <span className={`rounded-full border px-3 py-1 text-[11px] ${statusTone(status)}`}>
            {statusLabel(status)}
          </span>
        </div>

        <div className="mt-5 grid gap-3 md:grid-cols-4">
          <label className="rounded-2xl border border-zinc-800 bg-zinc-950/60 p-3">
            <span className="text-[10px] uppercase tracking-[0.18em] text-zinc-500">预算</span>
            <input
              className="mt-2 w-full rounded-xl border border-zinc-800 bg-black/50 px-3 py-2 text-sm text-zinc-100 outline-none focus:border-cyan-500/60"
              type="number"
              min={1}
              max={180}
              value={config.maxMinutes}
              onChange={(event) => setConfig({ ...config, maxMinutes: Number(event.target.value || 180) })}
            />
            <span className="mt-1 block text-[10px] text-zinc-500">分钟，上限 180</span>
          </label>
          <label className="rounded-2xl border border-zinc-800 bg-zinc-950/60 p-3">
            <span className="text-[10px] uppercase tracking-[0.18em] text-zinc-500">扩展样盘上限</span>
            <input
              className="mt-2 w-full rounded-xl border border-zinc-800 bg-black/50 px-3 py-2 text-sm text-zinc-100 outline-none focus:border-cyan-500/60"
              placeholder="空 = 全量"
              value={config.maxExtendedCases}
              onChange={(event) => setConfig({ ...config, maxExtendedCases: event.target.value })}
            />
            <span className="mt-1 block text-[10px] text-zinc-500">用于长跑时缩小范围</span>
          </label>
          <label className="rounded-2xl border border-zinc-800 bg-zinc-950/60 p-3">
            <span className="text-[10px] uppercase tracking-[0.18em] text-zinc-500">LLM 复核包</span>
            <button
              type="button"
              onClick={() => setConfig({ ...config, requestLlmReview: !config.requestLlmReview })}
              className={`mt-2 w-full rounded-xl border px-3 py-2 text-sm transition ${
                config.requestLlmReview
                  ? "border-fuchsia-400/40 bg-fuchsia-950/30 text-fuchsia-100"
                  : "border-zinc-800 bg-black/40 text-zinc-400"
              }`}
            >
              {config.requestLlmReview ? "生成复核包" : "不生成"}
            </button>
            <span className="mt-1 block text-[10px] text-zinc-500">默认不直接调用模型</span>
          </label>
          <div className="rounded-2xl border border-zinc-800 bg-zinc-950/60 p-3">
            <span className="text-[10px] uppercase tracking-[0.18em] text-zinc-500">预计剩余</span>
            <div className="mt-2 font-mono text-2xl text-cyan-100">{formatDuration(campaign.estimated_remaining_seconds)}</div>
            <span className="mt-1 block text-[10px] text-zinc-500">
              {campaign.current_step_label || "等待启动"}
            </span>
          </div>
        </div>

        <div className="mt-5">
          <div className="h-3 overflow-hidden rounded-full bg-zinc-900">
            <div
              className="h-full rounded-full bg-[linear-gradient(90deg,#22d3ee,#a7f3d0)] transition-all"
              style={{ width: `${progress}%` }}
            />
          </div>
          <div className="mt-2 flex flex-wrap justify-between gap-2 text-[11px] text-zinc-500">
            <span>{campaign.message || "等待启动自动学习 Campaign。"}</span>
            <span className="font-mono">{progress.toFixed(0)}%</span>
          </div>
        </div>

        <div className="mt-5 flex flex-wrap gap-2">
          <button
            onClick={onStart}
            disabled={loading || status === "running"}
            className="rounded-full border border-cyan-400/30 bg-cyan-300 px-4 py-2 text-xs font-semibold text-black disabled:cursor-not-allowed disabled:opacity-50"
          >
            {status === "paused" ? "继续运行" : "开始学习"}
          </button>
          <button
            onClick={onPause}
            disabled={loading || status !== "running"}
            className="rounded-full border border-amber-400/30 bg-amber-950/40 px-4 py-2 text-xs text-amber-100 disabled:cursor-not-allowed disabled:opacity-40"
          >
            暂停
          </button>
          <button
            onClick={onRefresh}
            disabled={loading}
            className="rounded-full border border-zinc-700 bg-zinc-950/70 px-4 py-2 text-xs text-zinc-200 disabled:cursor-not-allowed disabled:opacity-40"
          >
            刷新状态
          </button>
          <button
            onClick={copyReport}
            disabled={!reportMarkdown && !Object.keys(report).length}
            className="rounded-full border border-emerald-400/30 bg-emerald-950/30 px-4 py-2 text-xs text-emerald-100 disabled:cursor-not-allowed disabled:opacity-40"
          >
            {copied ? "已复制" : "复制报告"}
          </button>
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-[1.05fr_0.95fr]">
        <div className="rounded-3xl border border-zinc-800 bg-zinc-950/50 p-5">
          <div className="flex items-center justify-between gap-3">
            <div>
              <div className="text-[11px] uppercase tracking-[0.24em] text-zinc-500">Scorecard</div>
              <h3 className="mt-1 text-lg font-semibold text-zinc-100">学习结果总览</h3>
            </div>
            <span className={`rounded-full border px-3 py-1 text-[11px] ${statusTone(String(scorecard.state || status))}`}>
              {String(scorecard.state || "waiting")}
            </span>
          </div>
          <div className="mt-4 grid gap-3 sm:grid-cols-2">
            {scoreRows(report).map((row) => (
              <div key={row.label} className="rounded-2xl border border-zinc-800 bg-black/30 p-3">
                <div className="text-[10px] uppercase tracking-[0.18em] text-zinc-500">{row.label}</div>
                <div className="mt-2 font-mono text-2xl text-zinc-50">{row.value}</div>
                <div className="mt-1 text-[11px] text-zinc-500">{row.hint}</div>
              </div>
            ))}
          </div>
          <div className="mt-4 rounded-2xl border border-zinc-800 bg-black/30 p-3 text-xs leading-6 text-zinc-400">
            <p>插件治理：{asNumber(coverage.plugin_count)} 个插件 · 未分类 {asNumber(coverage.unclassified_count)}</p>
            <p>参数实验：{parameterExperiments.length} 个 · 分析师反馈项 {feedbackItems.length} 个</p>
            <p>LLM 复核建议：{String(llmPackage.should_request_llm_review || false)}</p>
          </div>
        </div>

        <div className="rounded-3xl border border-zinc-800 bg-zinc-950/50 p-5">
          <div className="text-[11px] uppercase tracking-[0.24em] text-zinc-500">Feedback Routing</div>
          <h3 className="mt-1 text-lg font-semibold text-zinc-100">反馈出口</h3>
          <div className="mt-4 space-y-3 text-xs leading-6">
            <div className="rounded-2xl border border-cyan-500/20 bg-cyan-950/10 p-3 text-cyan-100">
              Codex 主审：优先审参数族、报告可信度和是否需要开新实验。
            </div>
            <div className="rounded-2xl border border-amber-500/20 bg-amber-950/10 p-3 text-amber-100">
              分析师复核：只接收冲突、gate、法理不确定项，不处理普通绿灯报告。
            </div>
            <div className="rounded-2xl border border-emerald-500/20 bg-emerald-950/10 p-3 text-emerald-100">
              系统反馈：异常会映射到 parameter_family，形成下一轮 synthetic / benchmark 任务。
            </div>
            <div className="rounded-2xl border border-fuchsia-500/20 bg-fuchsia-950/10 p-3 text-fuchsia-100">
              LLM 复核：只读摘要包，禁止直接给配置补丁或覆盖 authority。
            </div>
          </div>
        </div>
      </div>

      <div className="rounded-3xl border border-zinc-800 bg-black/40 p-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <div className="text-[11px] uppercase tracking-[0.24em] text-zinc-500">Report</div>
            <h3 className="mt-1 text-lg font-semibold text-zinc-100">自动学习报告</h3>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-[11px] text-zinc-500">Markdown 可复制给 Codex / 分析师 / LLM</span>
            <button
              onClick={copyReport}
              disabled={!reportMarkdown && !Object.keys(report).length}
              className="rounded-full border border-cyan-400/30 bg-cyan-950/30 px-3 py-1.5 text-[11px] text-cyan-100 disabled:cursor-not-allowed disabled:opacity-40"
            >
              {copied ? "已复制报告" : "复制报告"}
            </button>
          </div>
        </div>
        <pre className="mt-4 max-h-[460px] overflow-auto rounded-2xl border border-zinc-800 bg-zinc-950/80 p-4 text-xs leading-6 text-zinc-300">
          {reportMarkdown || "暂无报告。点击「开始学习」后生成。"}
        </pre>
      </div>
    </section>
  );
}
