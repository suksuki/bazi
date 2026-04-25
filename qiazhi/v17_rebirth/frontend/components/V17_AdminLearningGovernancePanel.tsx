"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { CheckCircle2, Eye, RefreshCcw, Rocket, XCircle } from "lucide-react";
import { jsonPostInit, noStoreInit, requestJson } from "@/lib/apiClient";

type Row = Record<string, unknown>;

function asRecord(value: unknown): Row {
  return value && typeof value === "object" && !Array.isArray(value) ? (value as Row) : {};
}

function asRows(value: unknown): Row[] {
  return Array.isArray(value) ? value.filter((row): row is Row => Boolean(row) && typeof row === "object" && !Array.isArray(row)) : [];
}

function asText(value: unknown, fallback = ""): string {
  const text = String(value || "").trim();
  return text || fallback;
}

function statusLabel(status: string): string {
  if (status === "approved_for_experiment") return "准入实验";
  if (status === "rejected") return "已驳回";
  if (status === "watch") return "观察中";
  if (status === "approved") return "发布已批";
  if (status === "rolled_back") return "已回滚";
  return "未审计";
}

function statusTone(status: string): string {
  if (status === "approved_for_experiment" || status === "approved") return "border-emerald-300/25 bg-emerald-400/10 text-emerald-100";
  if (status === "rejected") return "border-rose-300/25 bg-rose-400/10 text-rose-100";
  if (status === "watch") return "border-amber-300/25 bg-amber-400/10 text-amber-100";
  return "border-zinc-700 bg-zinc-900/70 text-zinc-300";
}

export function V17_AdminLearningGovernancePanel({ operatorRole }: { operatorRole: string }) {
  const [candidates, setCandidates] = useState<Row[]>([]);
  const [experiments, setExperiments] = useState<Row[]>([]);
  const [releases, setReleases] = useState<Row[]>([]);
  const [scorecards, setScorecards] = useState<Row[]>([]);
  const [summary, setSummary] = useState<Row>({});
  const [loading, setLoading] = useState(false);
  const [busyKey, setBusyKey] = useState("");
  const [message, setMessage] = useState("");
  const canRelease = operatorRole === "admin";

  const loadGovernance = useCallback(async () => {
    setLoading(true);
    setMessage("");
    try {
      const [candidateResp, experimentResp, releaseResp, scorecardResp] = await Promise.all([
        requestJson<Row>("/api/auth/practitioner-learning-candidates?scope=all&limit=120", noStoreInit()),
        requestJson<Row>("/api/auth/practitioner-learning-experiments", noStoreInit()),
        requestJson<Row>("/api/auth/practitioner-learning-releases?limit=80", noStoreInit()),
        requestJson<Row>("/api/auth/practitioner-learning-scorecards?limit=80", noStoreInit()),
      ]);
      for (const resp of [candidateResp, experimentResp, releaseResp, scorecardResp]) {
        if (!resp.ok) throw new Error(String(resp.data.detail || resp.error || "学习治理数据加载失败"));
      }
      setCandidates(asRows(candidateResp.data.candidates));
      setSummary(asRecord(candidateResp.data.summary));
      setExperiments(asRows(experimentResp.data.experiments));
      setReleases(asRows(releaseResp.data.releases));
      setScorecards(asRows(scorecardResp.data.scorecards));
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "学习治理数据加载失败");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadGovernance();
  }, [loadGovernance]);

  const releaseByExperiment = useMemo(() => {
    const map = new Map<string, Row>();
    for (const release of releases) {
      const id = asText(release.experiment_id);
      if (id && !map.has(id)) map.set(id, release);
    }
    return map;
  }, [releases]);
  const scorecardByExperiment = useMemo(() => {
    const map = new Map<string, Row>();
    for (const scorecard of scorecards) {
      const id = asText(scorecard.experiment_id);
      if (id && !map.has(id)) map.set(id, scorecard);
    }
    return map;
  }, [scorecards]);

  async function submitReview(candidate: Row, status: string) {
    const candidateId = asText(candidate.candidate_id);
    if (!candidateId) return;
    setBusyKey(`review:${candidateId}:${status}`);
    setMessage("");
    try {
      const { data, ok } = await requestJson<Row>(
        "/api/auth/practitioner-learning-reviews",
        jsonPostInit({
          candidate_id: candidateId,
          parameter_family: asText(candidate.parameter_family),
          status,
          reviewer_note:
            status === "approved_for_experiment"
              ? "准入 shadow run；仍不自动修改线上参数。"
              : status === "rejected"
                ? "当前证据不足，暂不进入实验。"
                : "继续观察，等待更多命理师反馈。",
          safety_gate: asText(candidate.safety_gate, "manual_review_required"),
          candidate_snapshot: candidate,
        }),
      );
      if (!ok) throw new Error(String(data.detail || "候选审计保存失败"));
      setMessage("学习候选审计已保存。");
      await loadGovernance();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "候选审计保存失败");
    } finally {
      setBusyKey("");
    }
  }

  async function approveRelease(experiment: Row) {
    const experimentId = asText(experiment.experiment_id);
    if (!experimentId || !canRelease) return;
    setBusyKey(`release:${experimentId}`);
    setMessage("");
    try {
      const { data, ok } = await requestJson<Row>(
        "/api/auth/practitioner-learning-releases",
        jsonPostInit({
          experiment_id: experimentId,
          candidate_id: asText(experiment.candidate_id),
          parameter_family: asText(experiment.parameter_family),
          status: "approved",
          release_summary: "管理端记录发布审批；当前仍只留痕，不自动写配置。",
          test_report: "需附 synthetic + practitioner benchmark 通过记录后再人工应用配置。",
          rollback_plan: "保留旧配置；若 benchmark 退化，恢复上一版参数并重跑全量回归。",
          experiment_snapshot: experiment,
        }),
      );
      if (!ok) throw new Error(String(data.detail || "发布审批保存失败"));
      setMessage("发布审批记录已保存，未自动写配置。");
      await loadGovernance();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "发布审批保存失败");
    } finally {
      setBusyKey("");
    }
  }

  async function recordScorecard(experiment: Row, verdict: string) {
    const experimentId = asText(experiment.experiment_id);
    if (!experimentId) return;
    setBusyKey(`scorecard:${experimentId}:${verdict}`);
    setMessage("");
    try {
      const promote = verdict === "promote";
      const { data, ok } = await requestJson<Row>(
        "/api/auth/practitioner-learning-scorecards",
        jsonPostInit({
          experiment_id: experimentId,
          candidate_id: asText(experiment.candidate_id),
          parameter_family: asText(experiment.parameter_family),
          synthetic_passed: promote,
          practitioner_passed: promote,
          improvement_count: promote ? 1 : 0,
          regression_count: 0,
          verdict,
          summary: promote
            ? "shadow run 通过，可进入发布审批记录。"
            : "shadow run 仍需调整，暂不建议发布。",
          experiment_snapshot: experiment,
          payload: { required_commands: experiment.required_commands },
        }),
      );
      if (!ok) throw new Error(String(data.detail || "实验评分保存失败"));
      setMessage("实验评分记录已保存，未自动写配置。");
      await loadGovernance();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "实验评分保存失败");
    } finally {
      setBusyKey("");
    }
  }

  const topCandidates = candidates.slice(0, 8);
  const candidateCount = Number(summary.candidate_count || candidates.length || 0);
  const reviewCount = candidates.reduce((count, row) => count + (asText(row.review_status, "unreviewed") !== "unreviewed" ? 1 : 0), 0);

  return (
    <section className="space-y-4">
      <div className="rounded-2xl border border-violet-400/20 bg-[linear-gradient(180deg,rgba(39,39,42,0.62),rgba(9,9,11,0.9))] p-4">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <div className="text-[11px] uppercase tracking-[0.24em] text-violet-300">Learning Governance</div>
            <h2 className="mt-2 text-lg font-semibold text-zinc-50">学习治理与发布控制</h2>
            <p className="mt-2 max-w-3xl text-xs leading-6 text-zinc-400">
              从命理师反馈聚合候选，经过审计、dry-run 实验队列和发布记录。所有动作默认留痕，不自动修改运行参数。
            </p>
          </div>
          <button
            type="button"
            onClick={() => void loadGovernance()}
            disabled={loading}
            className="inline-flex items-center gap-2 rounded-xl border border-violet-300/20 bg-violet-400/10 px-3 py-2 text-xs font-semibold text-violet-100 transition hover:border-violet-200/40 disabled:cursor-wait disabled:opacity-60"
          >
            <RefreshCcw className="h-4 w-4" />
            {loading ? "刷新中" : "刷新治理链路"}
          </button>
        </div>

        <div className="mt-4 grid gap-2 sm:grid-cols-4">
          {[
            ["学习候选", candidateCount],
            ["已审计", reviewCount],
            ["实验队列", experiments.length],
            ["评分记录", scorecards.length],
            ["发布记录", releases.length],
          ].map(([label, value]) => (
            <div key={String(label)} className="rounded-xl border border-white/10 bg-white/[0.035] p-3">
              <p className="text-[10px] text-zinc-500">{label}</p>
              <p className="mt-1 text-xl font-semibold text-zinc-100">{String(value)}</p>
            </div>
          ))}
        </div>

        {message ? (
          <p className="mt-3 rounded-xl border border-cyan-300/20 bg-cyan-400/10 px-3 py-2 text-xs text-cyan-100">{message}</p>
        ) : null}
      </div>

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1.25fr)_minmax(0,0.75fr)]">
        <div className="rounded-2xl border border-white/10 bg-zinc-950/55 p-4">
          <div className="flex items-center justify-between gap-3">
            <h3 className="text-sm font-semibold text-zinc-100">学习候选审计</h3>
            <span className="rounded-full border border-white/10 bg-white/[0.04] px-2 py-1 text-[10px] text-zinc-400">{topCandidates.length}/{candidateCount}</span>
          </div>
          <div className="mt-3 grid gap-2">
            {topCandidates.map((candidate) => {
              const candidateId = asText(candidate.candidate_id);
              const status = asText(candidate.review_status, "unreviewed");
              const score = Number(candidate.signal_score || 0);
              const note = asText(asRecord(candidate.latest_review).reviewer_note);
              return (
                <article key={candidateId} className="rounded-xl border border-white/10 bg-black/25 p-3">
                  <div className="flex flex-wrap items-start justify-between gap-2">
                    <div className="min-w-0">
                      <p className="truncate text-sm font-semibold text-zinc-100">{asText(candidate.parameter_family, "未分类候选")}</p>
                      <p className="mt-1 text-[10px] text-zinc-500">score {score.toFixed(2)} · {asText(candidate.recommended_action, "manual review")}</p>
                    </div>
                    <span className={`rounded-full border px-2 py-0.5 text-[10px] ${statusTone(status)}`}>{statusLabel(status)}</span>
                  </div>
                  <p className="mt-2 line-clamp-2 text-[11px] leading-5 text-zinc-400">
                    {note || asRows(candidate.review_hints).map((row) => String(row)).join(" / ") || asText(candidate.candidate_id)}
                  </p>
                  <div className="mt-3 flex flex-wrap gap-1.5">
                    {[
                      { status: "approved_for_experiment", label: "准入实验", icon: Rocket },
                      { status: "watch", label: "观察", icon: Eye },
                      { status: "rejected", label: "驳回", icon: XCircle },
                    ].map((item) => {
                      const Icon = item.icon;
                      const busy = busyKey === `review:${candidateId}:${item.status}`;
                      return (
                        <button
                          key={item.status}
                          type="button"
                          disabled={Boolean(busyKey)}
                          onClick={() => void submitReview(candidate, item.status)}
                          className="inline-flex items-center gap-1 rounded-lg border border-violet-300/15 bg-violet-400/10 px-2 py-1 text-[10px] font-semibold text-violet-100 transition hover:border-violet-200/35 disabled:cursor-wait disabled:opacity-60"
                        >
                          <Icon className="h-3 w-3" />
                          {busy ? "保存中" : item.label}
                        </button>
                      );
                    })}
                  </div>
                </article>
              );
            })}
            {!topCandidates.length ? <p className="rounded-xl border border-white/10 bg-white/[0.035] p-3 text-xs text-zinc-500">暂无学习候选。</p> : null}
          </div>
        </div>

        <div className="space-y-4">
          <div className="rounded-2xl border border-emerald-400/15 bg-zinc-950/55 p-4">
            <h3 className="text-sm font-semibold text-zinc-100">实验队列</h3>
            <div className="mt-3 grid gap-2">
              {experiments.slice(0, 5).map((experiment) => {
                const experimentId = asText(experiment.experiment_id);
                const release = releaseByExperiment.get(experimentId);
                const scorecard = scorecardByExperiment.get(experimentId);
                const released = Boolean(release);
                const scored = Boolean(scorecard);
                const promotable = asText(scorecard?.verdict) === "promote";
                return (
                  <article key={experimentId} className="rounded-xl border border-white/10 bg-black/25 p-3">
                    <div className="flex items-start justify-between gap-2">
                      <div className="min-w-0">
                        <p className="truncate text-xs font-semibold text-zinc-100">{asText(experiment.parameter_family, "experiment")}</p>
                        <p className="mt-1 line-clamp-2 text-[10px] leading-4 text-zinc-500">{asText(experiment.hypothesis)}</p>
                      </div>
                      <span className={`rounded-full border px-2 py-0.5 text-[10px] ${released ? statusTone(asText(release?.status)) : scored ? statusTone("approved_for_experiment") : statusTone("unreviewed")}`}>
                        {released ? statusLabel(asText(release?.status)) : scored ? `评分 ${asText(scorecard?.verdict)}` : "待评分"}
                      </span>
                    </div>
                    <div className="mt-3 flex flex-wrap gap-1.5">
                      <button
                        type="button"
                        disabled={Boolean(busyKey) || scored}
                        onClick={() => void recordScorecard(experiment, "promote")}
                        className="inline-flex items-center gap-1 rounded-lg border border-cyan-300/20 bg-cyan-400/10 px-2 py-1 text-[10px] font-semibold text-cyan-100 transition hover:border-cyan-200/40 disabled:cursor-not-allowed disabled:opacity-55"
                      >
                        <CheckCircle2 className="h-3 w-3" />
                        {busyKey === `scorecard:${experimentId}:promote` ? "保存中" : scored ? "已评分" : "记录通过评分"}
                      </button>
                      <button
                        type="button"
                        disabled={Boolean(busyKey) || scored}
                        onClick={() => void recordScorecard(experiment, "rework")}
                        className="inline-flex items-center gap-1 rounded-lg border border-amber-300/20 bg-amber-400/10 px-2 py-1 text-[10px] font-semibold text-amber-100 transition hover:border-amber-200/40 disabled:cursor-not-allowed disabled:opacity-55"
                      >
                        <Eye className="h-3 w-3" />
                        {busyKey === `scorecard:${experimentId}:rework` ? "保存中" : "记录返工"}
                      </button>
                    </div>
                    {canRelease ? (
                      <button
                        type="button"
                        disabled={Boolean(busyKey) || released || !promotable}
                        onClick={() => void approveRelease(experiment)}
                        className="mt-3 inline-flex items-center gap-1 rounded-lg border border-emerald-300/20 bg-emerald-400/10 px-2 py-1 text-[10px] font-semibold text-emerald-100 transition hover:border-emerald-200/40 disabled:cursor-not-allowed disabled:opacity-55"
                      >
                        <CheckCircle2 className="h-3 w-3" />
                        {busyKey === `release:${experimentId}` ? "保存中" : released ? "已记录" : promotable ? "记录发布审批" : "需通过评分"}
                      </button>
                    ) : null}
                  </article>
                );
              })}
              {!experiments.length ? <p className="rounded-xl border border-white/10 bg-white/[0.035] p-3 text-xs text-zinc-500">暂无准入实验。</p> : null}
            </div>
          </div>

          <div className="rounded-2xl border border-cyan-400/15 bg-zinc-950/55 p-4">
            <h3 className="text-sm font-semibold text-zinc-100">最近评分与发布</h3>
            <div className="mt-3 grid gap-2">
              {scorecards.slice(0, 3).map((scorecard) => (
                <article key={`scorecard_${String(scorecard.id)}`} className="rounded-xl border border-white/10 bg-black/25 p-3">
                  <div className="flex items-start justify-between gap-2">
                    <p className="min-w-0 truncate text-xs font-semibold text-zinc-100">{asText(scorecard.parameter_family, "scorecard")}</p>
                    <span className={`rounded-full border px-2 py-0.5 text-[10px] ${statusTone(asText(scorecard.verdict) === "promote" ? "approved_for_experiment" : "watch")}`}>评分 {asText(scorecard.verdict)}</span>
                  </div>
                  <p className="mt-2 line-clamp-2 text-[10px] leading-4 text-zinc-500">{asText(scorecard.summary)}</p>
                </article>
              ))}
              {releases.slice(0, 5).map((release) => (
                <article key={String(release.id)} className="rounded-xl border border-white/10 bg-black/25 p-3">
                  <div className="flex items-start justify-between gap-2">
                    <p className="min-w-0 truncate text-xs font-semibold text-zinc-100">{asText(release.parameter_family, "release")}</p>
                    <span className={`rounded-full border px-2 py-0.5 text-[10px] ${statusTone(asText(release.status))}`}>{statusLabel(asText(release.status))}</span>
                  </div>
                  <p className="mt-2 line-clamp-2 text-[10px] leading-4 text-zinc-500">{asText(release.release_summary) || asText(release.rollback_plan)}</p>
                </article>
              ))}
              {!releases.length ? <p className="rounded-xl border border-white/10 bg-white/[0.035] p-3 text-xs text-zinc-500">暂无发布记录。</p> : null}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
