"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import {
  AlertTriangle,
  BadgeCheck,
  Beaker,
  Boxes,
  CheckCircle2,
  Database,
  FlaskConical,
  History,
  Loader2,
  Lock,
  Play,
  RefreshCcw,
  ShieldCheck,
  Sparkles,
} from "lucide-react";

import { jsonPostInit, noStoreInit, requestJson } from "@/lib/apiClient";

type BootstrapStep = {
  step_key: string;
  status: string;
  object_id?: string;
  audit_event_id?: string;
  audit_event_type?: string;
  error?: string;
  details?: Record<string, unknown>;
};

type ActiveRule = {
  rule_id?: string;
  version?: string;
  content_hash?: string;
  status?: string;
  approved_at?: string;
  approved_by?: string;
  effect_scope?: string[];
  allowed_topics?: string[];
};

type QualityScore = {
  rule_id?: string;
  version?: string;
  quality_score?: number;
  risk_score?: number;
  recommended_action?: string;
};

type SmokeStep = {
  key: string;
  status: "pending" | "passed" | "failed";
  detail: string;
};

type AdminRuleBootstrapPanelProps = {
  displayName?: string;
  onLogout?: () => void | Promise<void>;
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value && typeof value === "object" && !Array.isArray(value));
}

function unwrapEnvelope(value: unknown): Record<string, unknown> {
  if (isRecord(value) && isRecord(value.data)) return value.data;
  return isRecord(value) ? value : {};
}

function readArray(source: unknown, key: string): unknown[] {
  if (!isRecord(source)) return [];
  const value = source[key];
  return Array.isArray(value) ? value : [];
}

function readRecord(source: unknown, key: string): Record<string, unknown> {
  if (!isRecord(source)) return {};
  const value = source[key];
  return isRecord(value) ? value : {};
}

function readString(source: unknown, keys: string[], fallback = ""): string {
  if (!isRecord(source)) return fallback;
  for (const key of keys) {
    const value = source[key];
    if (typeof value === "string" && value.trim()) return value.trim();
    if (typeof value === "number" && Number.isFinite(value)) return String(value);
  }
  return fallback;
}

function readNumber(source: unknown, keys: string[]): number | null {
  if (!isRecord(source)) return null;
  for (const key of keys) {
    const value = source[key];
    if (typeof value === "number" && Number.isFinite(value)) return value;
    if (typeof value === "string" && value.trim() && Number.isFinite(Number(value))) return Number(value);
  }
  return null;
}

function apiFailureMessage(value: unknown, requestError: string | undefined, fallback: string): string {
  return requestError || readString(value, ["message", "detail", "error"]) || readString(unwrapEnvelope(value), ["message", "detail", "error"]) || fallback;
}

function shortHash(value?: string): string {
  if (!value) return "n/a";
  return value.length > 18 ? `${value.slice(0, 14)}...` : value;
}

function stableId(prefix: string): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) return `${prefix}_${crypto.randomUUID()}`;
  return `${prefix}_${Date.now()}_${Math.random().toString(16).slice(2)}`;
}

function qualityForRule(rule: ActiveRule, scores: QualityScore[]): QualityScore {
  return (
    scores.find((score) => score.rule_id === rule.rule_id && (!score.version || score.version === rule.version)) ||
    scores.find((score) => score.rule_id === rule.rule_id) ||
    {}
  );
}

function normalizeActiveRules(payload: Record<string, unknown>): ActiveRule[] {
  const rows = readArray(payload, "items").length > 0 ? readArray(payload, "items") : readArray(payload, "active_rules");
  return rows.filter(isRecord).map((row) => ({
    rule_id: readString(row, ["rule_id"]),
    version: readString(row, ["version"]),
    content_hash: readString(row, ["content_hash"]),
    status: readString(row, ["status"]),
    approved_at: readString(row, ["approved_at", "last_activated_at"]),
    approved_by: readString(row, ["approved_by"]),
    effect_scope: readArray(row, "effect_scope").map(String),
    allowed_topics: readArray(row, "allowed_topics").map(String),
  }));
}

function normalizeQualityScores(payload: Record<string, unknown>): QualityScore[] {
  const rows = readArray(payload, "items").length > 0 ? readArray(payload, "items") : readArray(payload, "scores");
  return rows.filter(isRecord).map((row) => ({
    rule_id: readString(row, ["rule_id"]),
    version: readString(row, ["version"]),
    quality_score: readNumber(row, ["quality_score"]) ?? undefined,
    risk_score: readNumber(row, ["risk_score"]) ?? undefined,
    recommended_action: readString(row, ["recommended_action"]),
  }));
}

function normalizeBootstrapSteps(payload: Record<string, unknown>): BootstrapStep[] {
  return readArray(payload, "steps")
    .filter(isRecord)
    .map((row) => ({
      step_key: readString(row, ["step_key", "key"]),
      status: readString(row, ["status"], "pending"),
      object_id: readString(row, ["object_id"]),
      audit_event_id: readString(row, ["audit_event_id"]),
      audit_event_type: readString(row, ["audit_event_type"]),
      error: readString(row, ["error"]),
      details: readRecord(row, "details"),
    }));
}

function normalizeSessionId(payload: Record<string, unknown>): string {
  const session = readRecord(payload, "session");
  return readString(payload, ["agent_session_id", "session_id", "id"]) || readString(session, ["agent_session_id", "session_id", "id"]);
}

function normalizePredictionId(...sources: unknown[]): string {
  for (const source of sources) {
    const value = readString(source, ["prediction_id"]);
    if (value) return value;
  }
  return "";
}

function normalizeContractId(...sources: unknown[]): string {
  for (const source of sources) {
    const value = readString(source, ["contract_id"]);
    if (value) return value;
  }
  return "";
}

export function V18_AdminRuleBootstrapPanel({ displayName, onLogout }: AdminRuleBootstrapPanelProps): ReactNode {
  const [activeRules, setActiveRules] = useState<ActiveRule[]>([]);
  const [qualityScores, setQualityScores] = useState<QualityScore[]>([]);
  const [steps, setSteps] = useState<BootstrapStep[]>([]);
  const [smokeSteps, setSmokeSteps] = useState<SmokeStep[]>([]);
  const [loading, setLoading] = useState(false);
  const [bootstrapping, setBootstrapping] = useState(false);
  const [smokeRunning, setSmokeRunning] = useState(false);
  const [error, setError] = useState("");

  const activeRuleCount = activeRules.length;
  const latestActiveRule = activeRules[0];
  const latestQuality = latestActiveRule ? qualityForRule(latestActiveRule, qualityScores) : {};

  const loadStatus = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [rulesResp, qualityResp] = await Promise.all([
        requestJson<unknown>("/api/v18.1/rule-kernels?status=active", noStoreInit()),
        requestJson<unknown>("/api/v18.1/rules/quality-scores", noStoreInit()),
      ]);
      if (!rulesResp.ok) throw new Error(apiFailureMessage(rulesResp.data, rulesResp.error, "Active rule status 加载失败。"));
      setActiveRules(normalizeActiveRules(unwrapEnvelope(rulesResp.data)));
      if (qualityResp.ok) setQualityScores(normalizeQualityScores(unwrapEnvelope(qualityResp.data)));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Rule status 加载失败。");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadStatus();
  }, [loadStatus]);

  const runBootstrap = useCallback(async () => {
    setBootstrapping(true);
    setError("");
    setSteps([]);
    try {
      const bootstrapId = stableId("p3b").replace(/[^a-zA-Z0-9_]/g, "_");
      const { data, ok, error: requestError } = await requestJson<unknown>(
        "/api/v18.1/admin/rule-bootstrap/wealth",
        jsonPostInit(
          {
            bootstrap_id: bootstrapId,
            rule_id: "bootstrap.wealth.baseline",
          },
          noStoreInit(),
        ),
      );
      const payload = unwrapEnvelope(data);
      setSteps(normalizeBootstrapSteps(payload));
      if (!ok) throw new Error(apiFailureMessage(data, requestError, "Bootstrap 生命周期执行失败。"));
      setActiveRules(normalizeActiveRules(payload));
      await loadStatus();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Bootstrap 生命周期执行失败。");
    } finally {
      setBootstrapping(false);
    }
  }, [loadStatus]);

  const setSmokeStep = useCallback((step: SmokeStep) => {
    setSmokeSteps((prev) => {
      const next = prev.filter((item) => item.key !== step.key);
      return [...next, step];
    });
  }, []);

  const runUserPathSmoke = useCallback(async () => {
    setSmokeRunning(true);
    setError("");
    setSmokeSteps([]);
    try {
      const sessionResp = await requestJson<unknown>(
        "/api/v18.1/agent/sessions",
        jsonPostInit({ surface: "admin_rule_bootstrap_smoke", user_locale: "zh-CN" }, noStoreInit()),
      );
      if (!sessionResp.ok) throw new Error(apiFailureMessage(sessionResp.data, sessionResp.error, "Agent session 创建失败。"));
      const sessionId = normalizeSessionId(unwrapEnvelope(sessionResp.data));
      setSmokeStep({ key: "session", status: "passed", detail: sessionId });

      const turnResp = await requestJson<unknown>(
        `/api/v18.1/agent/sessions/${encodeURIComponent(sessionId)}/turns`,
        jsonPostInit(
          {
            request_id: stableId("admin_smoke_turn"),
            user_message: "我未来两年财运怎么样？",
            user_query: "我未来两年财运怎么样？",
            plugin_claims: [{ plugin_id: "plugin.agent", claim_id: "admin_bootstrap_smoke" }],
            birth_payload: { year: "1990", month: "01", day: "01", hour: "09", gender: "male" },
            chart_snapshot: {
              source: "admin_rule_bootstrap_smoke",
              completeness: "complete_birth_fields",
              birth_time: "1990-01-01T09:00:00",
              calendar: "solar",
              gender: "male",
              birth_fields: { year: "1990", month: "01", day: "01", hour: "09", gender: "male" },
              four_pillars: { year: "1990", month: "01", day: "01", hour: "09" },
            },
            missing_info_policy: "clarify_before_predict",
          },
          noStoreInit(),
        ),
      );
      if (!turnResp.ok) throw new Error(apiFailureMessage(turnResp.data, turnResp.error, "Agent prediction 生成失败。"));
      const turnPayload = unwrapEnvelope(turnResp.data);
      const turn = readRecord(turnPayload, "turn");
      const predictionId = normalizePredictionId(turnPayload, turn);
      const contractId = normalizeContractId(turnPayload, turn);
      if (!predictionId) throw new Error("Agent turn 未生成 prediction_id。");
      setSmokeStep({ key: "prediction", status: "passed", detail: predictionId });

      const explainResp = await requestJson<unknown>(
        `/api/v18.1/predictions/${encodeURIComponent(predictionId)}/explain`,
        jsonPostInit(
          {
            prediction_id: predictionId,
            contract_id: contractId,
            allowed_output_scope: "verified_prediction_explanation",
            user_locale: "zh-CN",
            tone: "calm",
            explanation_level: "normal",
            include_uncertainty: true,
            include_evidence_trace: true,
          },
          noStoreInit(),
        ),
      );
      if (!explainResp.ok) throw new Error(apiFailureMessage(explainResp.data, explainResp.error, "Explanation 生成失败。"));
      setSmokeStep({ key: "explanation", status: "passed", detail: "verified explanation generated" });

      const safeOutput = readRecord(turn, "safe_output");
      const sections = readRecord(safeOutput, "sections");
      const conclusionIds = readArray(safeOutput, "conclusion_ids").length > 0 ? readArray(safeOutput, "conclusion_ids") : readArray(sections, "conclusion_ids");
      const conclusionRef = String(conclusionIds[0] || "conclusion_1");
      const feedbackResp = await requestJson<unknown>(
        `/api/v18.1/predictions/${encodeURIComponent(predictionId)}/feedback`,
        jsonPostInit(
          {
            request_id: stableId("admin_smoke_feedback"),
            prediction_id: predictionId,
            conclusion_ref: conclusionRef,
            conclusion_id: conclusionRef,
            feedback_type: "unclear",
            user_comment: "admin bootstrap smoke feedback",
            observed_event: { source: "admin_rule_bootstrap_smoke" },
            observed_at: new Date().toISOString(),
          },
          noStoreInit(),
        ),
      );
      if (!feedbackResp.ok) throw new Error(apiFailureMessage(feedbackResp.data, feedbackResp.error, "Feedback 提交失败。"));
      const learningSignal = readRecord(unwrapEnvelope(feedbackResp.data), "learning_signal");
      setSmokeStep({ key: "feedback", status: "passed", detail: readString(learningSignal, ["signal_id", "id"], "learning_signal created") });

      const replayResp = await requestJson<unknown>(`/api/v18.1/predictions/${encodeURIComponent(predictionId)}/replay`, noStoreInit());
      if (!replayResp.ok) throw new Error(apiFailureMessage(replayResp.data, replayResp.error, "Replay 查询失败。"));
      setSmokeStep({ key: "replay", status: "passed", detail: "replay returned" });
    } catch (err) {
      const message = err instanceof Error ? err.message : "用户路径 smoke test 失败。";
      setError(message);
      setSmokeStep({ key: "failed", status: "failed", detail: message });
    } finally {
      setSmokeRunning(false);
    }
  }, [setSmokeStep]);

  const activeRuleSummary = useMemo(() => {
    if (!latestActiveRule) return "当前没有 active rule，普通用户预测会 fail-close。";
    return `${latestActiveRule.rule_id}@${latestActiveRule.version} 已 active，可进入普通用户预测链路。`;
  }, [latestActiveRule]);

  return (
    <main className="min-h-screen overflow-hidden bg-[#07100c] text-slate-100">
      <div className="pointer-events-none fixed inset-0">
        <div className="absolute left-[-12%] top-[-18%] h-[32rem] w-[32rem] rounded-full bg-emerald-400/18 blur-3xl" />
        <div className="absolute bottom-[-18%] right-[-10%] h-[34rem] w-[34rem] rounded-full bg-cyan-300/14 blur-3xl" />
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(255,255,255,0.08),transparent_36%),linear-gradient(135deg,rgba(255,255,255,0.06),transparent_34%)]" />
      </div>

      <section className="relative mx-auto w-full max-w-7xl px-4 py-5 sm:px-6 lg:px-8">
        <header className="rounded-[2rem] border border-white/10 bg-white/[0.07] p-6 shadow-2xl shadow-black/30 backdrop-blur">
          <div className="flex flex-col gap-5 md:flex-row md:items-start md:justify-between">
            <div>
              <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-emerald-200/20 bg-emerald-200/10 px-3 py-1 text-xs text-emerald-100">
                <Lock className="h-3.5 w-3.5" />
                Admin Rule Bootstrap
              </div>
              <h1 className="text-3xl font-semibold tracking-tight md:text-5xl">Active Rule Onboarding</h1>
              <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-300 md:text-base">
                把第一条财富预测规则从 Knowledge Card 走完整生命周期上线。这里不会直接写 active rule，也不会让 sandbox rule 参与普通预测。
              </p>
            </div>
            <div className="flex flex-wrap items-center gap-2 text-sm">
              <span className="rounded-full border border-white/10 bg-black/20 px-3 py-2 text-slate-300">{displayName || "Admin"}</span>
              <button
                type="button"
                onClick={() => void loadStatus()}
                className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/10 px-3 py-2 text-slate-100 transition hover:bg-white/15"
              >
                <RefreshCcw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
                刷新
              </button>
              {onLogout ? (
                <button type="button" onClick={() => void onLogout()} className="rounded-full border border-white/10 bg-black/20 px-3 py-2 text-slate-300 transition hover:bg-black/30">
                  退出
                </button>
              ) : null}
            </div>
          </div>
        </header>

        {error ? (
          <div className="mt-5 flex items-start gap-3 rounded-[1.5rem] border border-rose-300/20 bg-rose-500/10 p-4 text-sm text-rose-100">
            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
            <span>{error}</span>
          </div>
        ) : null}

        <section className="mt-5 grid gap-5 lg:grid-cols-[24rem_minmax(0,1fr)]">
          <ActiveRuleStatusCard
            activeRuleCount={activeRuleCount}
            activeRuleSummary={activeRuleSummary}
            latestActiveRule={latestActiveRule}
            latestQuality={latestQuality}
          />
          <BootstrapWizardCard
            bootstrapping={bootstrapping}
            onRunBootstrap={() => void runBootstrap()}
            steps={steps}
          />
        </section>

        <section className="mt-5 grid gap-5 lg:grid-cols-[minmax(0,1fr)_24rem]">
          <ActiveRuleTable activeRules={activeRules} qualityScores={qualityScores} />
          <UserPathSmokeCard
            disabled={activeRuleCount === 0}
            running={smokeRunning}
            smokeSteps={smokeSteps}
            onRun={() => void runUserPathSmoke()}
          />
        </section>
      </section>
    </main>
  );
}

function ActiveRuleStatusCard({
  activeRuleCount,
  activeRuleSummary,
  latestActiveRule,
  latestQuality,
}: {
  activeRuleCount: number;
  activeRuleSummary: string;
  latestActiveRule?: ActiveRule;
  latestQuality: QualityScore;
}): ReactNode {
  return (
    <section className="rounded-[2rem] border border-white/10 bg-white/[0.06] p-5 shadow-2xl shadow-black/20 backdrop-blur">
      <h2 className="mb-4 flex items-center gap-2 text-lg font-semibold">
        <Database className="h-5 w-5 text-emerald-200" />
        Active Rule Status
      </h2>
      <div className="rounded-3xl border border-emerald-300/20 bg-emerald-300/10 p-5">
        <div className="text-5xl font-semibold text-white">{activeRuleCount}</div>
        <p className="mt-2 text-sm leading-6 text-emerald-50/90">{activeRuleSummary}</p>
      </div>
      <div className="mt-4 space-y-3 text-sm">
        <StatusLine label="rule_id" value={latestActiveRule?.rule_id || "none"} />
        <StatusLine label="version" value={latestActiveRule?.version || "none"} />
        <StatusLine label="content_hash" value={shortHash(latestActiveRule?.content_hash)} />
        <StatusLine label="quality_score" value={latestQuality.quality_score === undefined ? "n/a" : String(latestQuality.quality_score)} />
        <StatusLine label="risk_score" value={latestQuality.risk_score === undefined ? "n/a" : String(latestQuality.risk_score)} />
        <StatusLine label="last_activated_at" value={latestActiveRule?.approved_at || "n/a"} />
      </div>
    </section>
  );
}

function BootstrapWizardCard({
  bootstrapping,
  onRunBootstrap,
  steps,
}: {
  bootstrapping: boolean;
  onRunBootstrap: () => void;
  steps: BootstrapStep[];
}): ReactNode {
  return (
    <section className="rounded-[2rem] border border-white/10 bg-white/[0.06] p-5 shadow-2xl shadow-black/20 backdrop-blur">
      <div className="mb-5 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div>
          <h2 className="flex items-center gap-2 text-xl font-semibold">
            <Sparkles className="h-5 w-5 text-cyan-200" />
            Bootstrap Wizard
          </h2>
          <p className="mt-1 text-sm text-slate-400">
            Knowledge Card → sandbox candidate → Rule Test Run → Knowledge PR → Reviewer approve → materialized version → activate API。
          </p>
        </div>
        <button
          type="button"
          onClick={onRunBootstrap}
          disabled={bootstrapping}
          className="inline-flex items-center justify-center gap-2 rounded-full bg-emerald-300 px-5 py-3 text-sm font-semibold text-emerald-950 transition hover:bg-emerald-200 disabled:cursor-not-allowed disabled:bg-slate-600 disabled:text-slate-300"
        >
          {bootstrapping ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
          初始化财富预测规则
        </button>
      </div>
      <div className="grid gap-3 md:grid-cols-2">
        {[
          "knowledge_card",
          "sandbox_candidate",
          "synthetic_test_case",
          "rule_test_run",
          "knowledge_pr",
          "reviewer_approve",
          "activate",
          "active_snapshot_refresh",
        ].map((key) => {
          const step = steps.find((item) => item.step_key === key);
          return <BootstrapStepCard key={key} stepKey={key} step={step} />;
        })}
      </div>
    </section>
  );
}

function BootstrapStepCard({ stepKey, step }: { stepKey: string; step?: BootstrapStep }): ReactNode {
  const passed = step?.status === "passed";
  const failed = step?.status === "failed";
  return (
    <article className={`rounded-2xl border p-4 ${passed ? "border-emerald-300/20 bg-emerald-300/10" : failed ? "border-rose-300/20 bg-rose-500/10" : "border-white/10 bg-black/20"}`}>
      <div className="mb-2 flex items-center justify-between gap-2">
        <h3 className="text-sm font-semibold text-white">{stepKey}</h3>
        {passed ? <CheckCircle2 className="h-4 w-4 text-emerald-200" /> : failed ? <AlertTriangle className="h-4 w-4 text-rose-200" /> : <Boxes className="h-4 w-4 text-slate-500" />}
      </div>
      <div className="space-y-1 text-xs text-slate-400">
        <p>status: {step?.status || "pending"}</p>
        <p>object_id: {step?.object_id || "n/a"}</p>
        <p>audit_event_id: {shortHash(step?.audit_event_id)}</p>
        {step?.error ? <p className="text-rose-200">error: {step.error}</p> : null}
      </div>
    </article>
  );
}

function ActiveRuleTable({ activeRules, qualityScores }: { activeRules: ActiveRule[]; qualityScores: QualityScore[] }): ReactNode {
  return (
    <section className="rounded-[2rem] border border-white/10 bg-white/[0.06] p-5 shadow-2xl shadow-black/20 backdrop-blur">
      <h2 className="mb-4 flex items-center gap-2 text-xl font-semibold">
        <ShieldCheck className="h-5 w-5 text-emerald-200" />
        Active Rule Snapshot
      </h2>
      {activeRules.length === 0 ? (
        <p className="rounded-2xl border border-dashed border-white/10 bg-black/20 p-5 text-sm text-slate-400">
          当前没有 active rule。普通用户端会保持 fail-close，不会自动注入 seed/sandbox rule。
        </p>
      ) : (
        <div className="overflow-hidden rounded-2xl border border-white/10">
          <div className="grid grid-cols-[1.4fr_0.7fr_1fr_0.7fr_0.7fr] bg-white/10 px-4 py-3 text-xs uppercase tracking-[0.16em] text-slate-400">
            <span>rule_id</span>
            <span>version</span>
            <span>content_hash</span>
            <span>quality</span>
            <span>risk</span>
          </div>
          {activeRules.map((rule) => {
            const quality = qualityForRule(rule, qualityScores);
            return (
              <div key={`${rule.rule_id}-${rule.version}`} className="grid grid-cols-[1.4fr_0.7fr_1fr_0.7fr_0.7fr] border-t border-white/10 px-4 py-3 text-sm text-slate-200">
                <span className="break-all font-mono text-xs">{rule.rule_id}</span>
                <span>{rule.version}</span>
                <span className="font-mono text-xs">{shortHash(rule.content_hash)}</span>
                <span>{quality.quality_score ?? "n/a"}</span>
                <span>{quality.risk_score ?? "n/a"}</span>
              </div>
            );
          })}
        </div>
      )}
    </section>
  );
}

function UserPathSmokeCard({
  disabled,
  running,
  smokeSteps,
  onRun,
}: {
  disabled: boolean;
  running: boolean;
  smokeSteps: SmokeStep[];
  onRun: () => void;
}): ReactNode {
  return (
    <section className="rounded-[2rem] border border-white/10 bg-white/[0.06] p-5 shadow-2xl shadow-black/20 backdrop-blur">
      <h2 className="mb-2 flex items-center gap-2 text-lg font-semibold">
        <Beaker className="h-5 w-5 text-cyan-200" />
        User Path Smoke
      </h2>
      <p className="text-sm leading-6 text-slate-400">
        验证 /v17/oracle 同链路：Agent turn → prediction_id → explanation → feedback → replay。
      </p>
      <button
        type="button"
        onClick={onRun}
        disabled={disabled || running}
        className="mt-4 inline-flex w-full items-center justify-center gap-2 rounded-full bg-cyan-300 px-5 py-3 text-sm font-semibold text-cyan-950 transition hover:bg-cyan-200 disabled:cursor-not-allowed disabled:bg-slate-600 disabled:text-slate-300"
      >
        {running ? <Loader2 className="h-4 w-4 animate-spin" /> : <FlaskConical className="h-4 w-4" />}
        跑通普通用户预测链路
      </button>
      <div className="mt-4 space-y-2">
        {smokeSteps.length === 0 ? (
          <p className="rounded-2xl border border-dashed border-white/10 bg-black/20 p-4 text-sm text-slate-500">
            {disabled ? "需要先上线 active rule。" : "等待执行 smoke test。"}
          </p>
        ) : (
          smokeSteps.map((step) => (
            <div key={step.key} className={`rounded-2xl border p-3 text-sm ${step.status === "passed" ? "border-emerald-300/20 bg-emerald-300/10 text-emerald-100" : step.status === "failed" ? "border-rose-300/20 bg-rose-500/10 text-rose-100" : "border-white/10 bg-black/20 text-slate-300"}`}>
              <div className="font-semibold">{step.key}</div>
              <div className="mt-1 break-words text-xs opacity-80">{step.detail}</div>
            </div>
          ))
        )}
      </div>
    </section>
  );
}

function StatusLine({ label, value }: { label: string; value: string }): ReactNode {
  return (
    <div className="rounded-2xl border border-white/10 bg-black/20 p-3">
      <div className="text-[11px] uppercase tracking-[0.18em] text-slate-500">{label}</div>
      <div className="mt-1 break-all font-mono text-xs text-slate-200">{value}</div>
    </div>
  );
}

