"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import {
  AlertTriangle,
  ArrowLeft,
  ArrowRight,
  CheckCircle2,
  ClipboardCheck,
  Copy,
  Database,
  History,
  Loader2,
  RefreshCcw,
  ShieldCheck,
  Sparkles,
} from "lucide-react";

import { useAppLanguage } from "@/hooks/useAppLanguage";
import type { AppLanguage } from "@/lib/i18n";
import { jsonPostInit, noStoreInit, requestJson } from "@/lib/apiClient";
import { userFacingApiMessage, userFacingExceptionMessage } from "@/lib/v18UserMessages";

type ReplayShareViewerProps = {
  predictionId: string;
};

type ReplayCopy = {
  product: string;
  back: string;
  title: string;
  subtitle: string;
  loading: string;
  failed: string;
  refresh: string;
  copied: string;
  copyLink: string;
  predictionId: string;
  verifier: string;
  replayMode: string;
  conclusion: string;
  confidence: string;
  uncertainty: string;
  evidence: string;
  feedback: string;
  learningSignals: string;
  ruleDrift: string;
  noDrift: string;
  hasDrift: string;
  redactedNotice: string;
  fullRecordNotice: string;
  evidenceCount: string;
  feedbackPrompt: string;
  feedbackHit: string;
  feedbackPartial: string;
  feedbackMiss: string;
  feedbackUnclear: string;
  feedbackThanks: string;
  tryDemoCta: string;
  loginSaveCta: string;
};

const REPLAY_COPY: Record<AppLanguage, ReplayCopy> = {
  zh: {
    product: "掐指一算",
    back: "返回 Demo",
    title: "可验证 Replay",
    subtitle: "这不是截图分享。它会按 prediction_id 读取账本、Contract、Evidence、Feedback 与 Learning Signal 摘要。",
    loading: "正在读取回放...",
    failed: "Replay 加载失败",
    refresh: "刷新",
    copied: "已复制",
    copyLink: "复制链接",
    predictionId: "prediction_id",
    verifier: "校验状态",
    replayMode: "回放模式",
    conclusion: "结论",
    confidence: "置信度",
    uncertainty: "不确定性",
    evidence: "证据",
    feedback: "反馈",
    learningSignals: "学习信号",
    ruleDrift: "规则漂移",
    noDrift: "未检测到漂移",
    hasDrift: "检测到漂移",
    redactedNotice: "此回放已隐藏个人信息",
    fullRecordNotice: "完整记录仅本人登录后可见",
    evidenceCount: "证据数量",
    feedbackPrompt: "你觉得准吗？",
    feedbackHit: "准",
    feedbackPartial: "部分准",
    feedbackMiss: "不准",
    feedbackUnclear: "不确定",
    feedbackThanks: "已记录你的反馈，它会进入学习信号。",
    tryDemoCta: "我也想试一次",
    loginSaveCta: "登录保存我的预测",
  },
  en: {
    product: "Qiazhi",
    back: "Back to demo",
    title: "Verifiable Replay",
    subtitle: "This is not a screenshot. The page reads the ledger, Contract, Evidence, Feedback, and Learning Signal summary by prediction_id.",
    loading: "Loading replay...",
    failed: "Replay failed to load",
    refresh: "Refresh",
    copied: "Copied",
    copyLink: "Copy link",
    predictionId: "prediction_id",
    verifier: "Verifier status",
    replayMode: "Replay mode",
    conclusion: "Conclusion",
    confidence: "Confidence",
    uncertainty: "Uncertainty",
    evidence: "Evidence",
    feedback: "Feedback",
    learningSignals: "Learning signals",
    ruleDrift: "Rule drift",
    noDrift: "No drift detected",
    hasDrift: "Drift detected",
    redactedNotice: "Personal information is hidden in this replay",
    fullRecordNotice: "The complete record is visible only after signing in as the owner",
    evidenceCount: "Evidence count",
    feedbackPrompt: "Does this feel accurate?",
    feedbackHit: "Accurate",
    feedbackPartial: "Partly accurate",
    feedbackMiss: "Not accurate",
    feedbackUnclear: "Not sure",
    feedbackThanks: "Feedback recorded. It will be used as a learning signal.",
    tryDemoCta: "Try one myself",
    loginSaveCta: "Sign in to save my prediction",
  },
  ko: {
    product: "Qiazhi",
    back: "Demo로 돌아가기",
    title: "검증 가능한 Replay",
    subtitle: "스크린샷 공유가 아닙니다. prediction_id로 Ledger, Contract, Evidence, Feedback, Learning Signal 요약을 읽어옵니다.",
    loading: "Replay를 불러오는 중...",
    failed: "Replay를 불러오지 못했습니다",
    refresh: "새로고침",
    copied: "복사됨",
    copyLink: "링크 복사",
    predictionId: "prediction_id",
    verifier: "검증 상태",
    replayMode: "Replay 모드",
    conclusion: "결론",
    confidence: "신뢰도",
    uncertainty: "불확실성",
    evidence: "근거",
    feedback: "피드백",
    learningSignals: "Learning signal",
    ruleDrift: "규칙 변화",
    noDrift: "변화 없음",
    hasDrift: "변화 감지",
    redactedNotice: "이 replay는 개인정보를 숨긴 상태입니다",
    fullRecordNotice: "전체 기록은 본인 로그인 후에만 확인할 수 있습니다",
    evidenceCount: "근거 수",
    feedbackPrompt: "정확하다고 느끼셨나요?",
    feedbackHit: "맞아요",
    feedbackPartial: "부분적으로 맞아요",
    feedbackMiss: "아니에요",
    feedbackUnclear: "잘 모르겠어요",
    feedbackThanks: "피드백이 기록되었습니다. 학습 신호로 반영됩니다.",
    tryDemoCta: "나도 한번 해보기",
    loginSaveCta: "로그인하고 내 예측 저장",
  },
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

function shortHash(value: string, size = 24): string {
  if (!value) return "n/a";
  return value.length > size ? `${value.slice(0, size - 3)}...` : value;
}

function wealthFeatureLabel(value: string): string {
  const labels: Record<string, string> = {
    wealth_strength: "财星强弱",
    wealth_vault: "财库状态",
    output_generate_wealth: "食伤生财",
    constraint_structure: "官杀制约财富",
    flow_activation: "大运流年引动",
    stability_risk: "合冲刑害稳定性",
  };
  return labels[value] || value;
}

export function V18_ReplayShareViewer({ predictionId }: ReplayShareViewerProps): ReactNode {
  const { language, setLanguage } = useAppLanguage();
  const text = REPLAY_COPY[language];
  const [replay, setReplay] = useState<Record<string, unknown>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [copied, setCopied] = useState(false);
  const [feedbackStatus, setFeedbackStatus] = useState("");
  const [feedbackLoading, setFeedbackLoading] = useState(false);

  const loadReplay = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const resp = await requestJson<unknown>(`/api/v18.1/predictions/${encodeURIComponent(predictionId)}/public-replay`, noStoreInit());
      if (!resp.ok) throw new Error(userFacingApiMessage(resp.data, resp.error, text.failed, language));
      setReplay(unwrapEnvelope(resp.data));
    } catch (err) {
      setError(userFacingExceptionMessage(err, text.failed, language));
    } finally {
      setLoading(false);
    }
  }, [language, predictionId, text.failed]);

  useEffect(() => {
    void loadReplay();
  }, [loadReplay]);

  const replayUrl = useMemo(() => {
    if (typeof window === "undefined") return "";
    return window.location.href;
  }, []);

  const copyReplayLink = useCallback(async () => {
    if (!replayUrl) return;
    await navigator.clipboard?.writeText(replayUrl);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1600);
  }, [replayUrl]);

  const submitReplayFeedback = useCallback(
    async (feedbackType: "hit" | "partial" | "miss" | "unclear") => {
      setFeedbackLoading(true);
      setFeedbackStatus("");
      setError("");
      try {
        const resp = await requestJson<unknown>(
          `/api/v18.1/predictions/${encodeURIComponent(predictionId)}/feedback`,
          jsonPostInit(
            {
              feedback_type: feedbackType,
              user_comment: "public replay quick feedback",
              observed_event: {
                source: "public_replay",
                label: feedbackType,
              },
              observed_at: new Date().toISOString(),
            },
            noStoreInit(),
          ),
        );
        if (!resp.ok) throw new Error(userFacingApiMessage(resp.data, resp.error, text.feedbackThanks, language));
        setFeedbackStatus(text.feedbackThanks);
      } catch (err) {
        setFeedbackStatus(userFacingExceptionMessage(err, text.feedbackThanks, language));
      } finally {
        setFeedbackLoading(false);
      }
    },
    [language, predictionId, text.feedbackThanks],
  );

  const uncertainty = isRecord(replay.uncertainty) ? replay.uncertainty : {};
  const evidence = readArray(replay, "evidence_summary").filter(isRecord);
  const feedbackCount = readNumber(replay, ["feedback_count"]) ?? 0;
  const learningSignalCount = readNumber(replay, ["learning_signal_count"]) ?? 0;
  const ruleDrift = replay.rule_drift === true;
  const confidence = readNumber(replay, ["confidence"]);
  const redaction = isRecord(replay.redaction) ? replay.redaction : {};
  const redactionNotice = readString(redaction, ["notice"], text.redactedNotice);
  const fullRecordNotice = readString(redaction, ["full_record_notice"], text.fullRecordNotice);

  return (
    <main className="min-h-screen bg-[#070b10] text-slate-100">
      <section className="mx-auto w-full max-w-6xl px-4 py-6 sm:px-6 lg:px-8">
        <nav className="mb-6 flex flex-wrap items-center justify-between gap-3 border-b border-white/10 pb-4">
          <a href="/demo" className="inline-flex items-center gap-2 text-sm font-semibold text-white">
            <ArrowLeft className="h-4 w-4 text-cyan-200" />
            {text.back}
          </a>
          <div className="flex flex-wrap items-center gap-2">
            {(["zh", "en", "ko"] as AppLanguage[]).map((item) => (
              <button
                key={item}
                type="button"
                onClick={() => setLanguage(item)}
                className={`rounded-full border px-3 py-1.5 text-xs transition ${
                  item === language ? "border-cyan-200/30 bg-cyan-200/15 text-cyan-50" : "border-white/10 bg-black/20 text-slate-300 hover:bg-white/10"
                }`}
              >
                {item === "zh" ? "中文" : item === "ko" ? "한국어" : "English"}
              </button>
            ))}
          </div>
        </nav>

        <header className="max-w-3xl">
          <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-cyan-200/20 bg-cyan-200/10 px-3 py-1.5 text-sm text-cyan-100">
            <Sparkles className="h-4 w-4" />
            {text.product}
          </div>
          <h1 className="text-3xl font-semibold text-white sm:text-4xl md:text-6xl">{text.title}</h1>
          <p className="mt-5 text-base leading-8 text-slate-300">{text.subtitle}</p>
        </header>

        <section className="mt-8 rounded-[2rem] border border-white/10 bg-white/[0.06] p-5">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="text-xs uppercase tracking-[0.16em] text-slate-500">{text.predictionId}</p>
              <p className="mt-1 break-all font-mono text-sm text-cyan-100">{readString(replay, ["prediction_id_short"], shortHash(predictionId))}</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <button type="button" onClick={() => void copyReplayLink()} className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-black/20 px-4 py-2 text-sm text-slate-100 transition hover:bg-white/10">
                <Copy className="h-4 w-4" />
                {copied ? text.copied : text.copyLink}
              </button>
              <button type="button" onClick={() => void loadReplay()} className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/10 px-4 py-2 text-sm text-slate-100 transition hover:bg-white/15">
                <RefreshCcw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
                {text.refresh}
              </button>
            </div>
          </div>
        </section>

        {loading ? (
          <section className="mt-6 flex items-center gap-3 rounded-[2rem] border border-white/10 bg-white/[0.05] p-5 text-sm text-slate-300">
            <Loader2 className="h-4 w-4 animate-spin text-cyan-200" />
            {text.loading}
          </section>
        ) : null}

        {error ? (
          <section className="mt-6 flex items-start gap-3 rounded-[2rem] border border-rose-300/20 bg-rose-500/10 p-5 text-sm text-rose-100">
            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
            {error}
          </section>
        ) : null}

        {!loading && !error ? (
          <section className="mt-6 grid gap-5 lg:grid-cols-[minmax(0,1fr)_24rem]">
            <div className="space-y-5">
              <article className="rounded-[2rem] border border-emerald-300/20 bg-emerald-300/[0.08] p-5">
                <h2 className="mb-3 flex items-center gap-2 text-lg font-semibold text-white">
                  <ShieldCheck className="h-5 w-5 text-emerald-200" />
                  {redactionNotice}
                </h2>
                <p className="text-sm leading-6 text-slate-300">{fullRecordNotice}</p>
              </article>

              <article className="rounded-[2rem] border border-white/10 bg-black/25 p-5">
                <h2 className="mb-3 flex items-center gap-2 text-xl font-semibold text-white">
                  <ShieldCheck className="h-5 w-5 text-cyan-200" />
                  {text.conclusion}
                </h2>
                <p className="text-sm leading-7 text-slate-200">{readString(replay, ["conclusion_summary"], "n/a")}</p>
                <div className="mt-4 grid gap-3 sm:grid-cols-3">
                  <ReplayStat label={text.confidence} value={confidence === null ? "n/a" : `${Math.round(confidence * 100)}%`} />
                  <ReplayStat label={text.verifier} value={readString(replay, ["verifier_status"], "n/a")} />
                  <ReplayStat label={text.replayMode} value={readString(replay, ["replay_mode"], "n/a")} />
                </div>
              </article>

              <article className="rounded-[2rem] border border-white/10 bg-white/[0.06] p-5">
                <h2 className="mb-3 flex items-center gap-2 text-lg font-semibold text-white">
                  <Database className="h-5 w-5 text-emerald-200" />
                  {text.uncertainty}
                </h2>
                <div className="grid gap-3 sm:grid-cols-2">
                  <ReplayStat label={text.uncertainty} value={`${Math.round((readNumber(uncertainty, ["score"]) ?? 0) * 100)}%`} />
                  <ReplayStat label={text.evidenceCount} value={`${evidence.length}`} />
                </div>
              </article>
            </div>

            <aside className="space-y-5">
              <article className="rounded-[2rem] border border-white/10 bg-white/[0.06] p-5">
                <h2 className="mb-3 flex items-center gap-2 text-lg font-semibold text-white">
                  <ClipboardCheck className="h-5 w-5 text-cyan-200" />
                  {text.evidence}
                </h2>
                <div className="space-y-3">
                  {evidence.slice(0, 2).map((item, index) => (
                    <div key={`${readString(item, ["rule_id"], "rule")}-${index}`} className="rounded-2xl border border-white/10 bg-black/20 p-4 text-sm">
                      <p className="font-mono text-xs text-cyan-100">{shortHash(readString(item, ["rule_id"], "rule"))}</p>
                      <p className="mt-2 text-emerald-100">{readString(item, ["feature_label"]) || wealthFeatureLabel(readString(item, ["feature_type"])) || text.evidence}</p>
                      <p className="mt-2 text-slate-300">effect_keys: {readArray(item, "effect_keys").map(String).join(", ") || "n/a"}</p>
                      <p className="mt-1 text-slate-400">matched_fact_count: {readNumber(item, ["matched_fact_count"]) ?? 0}</p>
                      <p className="mt-1 text-slate-400">stability / risk: {Math.round((readNumber(item, ["stability"]) ?? 0) * 100)}% / {Math.round((readNumber(item, ["risk"]) ?? 0) * 100)}%</p>
                    </div>
                  ))}
                </div>
              </article>

              <article className="rounded-[2rem] border border-white/10 bg-white/[0.06] p-5">
                <h2 className="mb-3 flex items-center gap-2 text-lg font-semibold text-white">
                  <History className="h-5 w-5 text-cyan-200" />
                  {text.replayMode}
                </h2>
                <div className="grid gap-3">
                  <ReplayStat label={text.feedback} value={`${feedbackCount}`} />
                  <ReplayStat label={text.learningSignals} value={`${learningSignalCount}`} />
                  <ReplayStat label={text.ruleDrift} value={ruleDrift ? text.hasDrift : text.noDrift} tone={ruleDrift ? "warn" : "ok"} />
                </div>
              </article>
            </aside>
          </section>
        ) : null}

        {!loading && !error ? (
          <section className="mt-6 rounded-[2rem] border border-cyan-200/20 bg-cyan-200/[0.06] p-5">
            <h2 className="mb-3 flex items-center gap-2 text-lg font-semibold text-white">
              <Sparkles className="h-5 w-5 text-cyan-200" />
              {text.feedbackPrompt}
            </h2>
            <div className="flex flex-wrap gap-2">
              {[
                ["hit", text.feedbackHit],
                ["partial", text.feedbackPartial],
                ["miss", text.feedbackMiss],
                ["unclear", text.feedbackUnclear],
              ].map(([type, label]) => (
                <button
                  key={type}
                  type="button"
                  disabled={feedbackLoading}
                  onClick={() => void submitReplayFeedback(type as "hit" | "partial" | "miss" | "unclear")}
                  className="rounded-full border border-white/10 bg-black/20 px-4 py-2 text-sm text-slate-100 transition hover:bg-white/10 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {label}
                </button>
              ))}
            </div>
            {feedbackStatus ? (
              <p className="mt-3 rounded-2xl border border-emerald-300/20 bg-emerald-300/10 p-3 text-sm text-emerald-100">{feedbackStatus}</p>
            ) : null}
          </section>
        ) : null}

        <section className="mt-6 flex flex-col gap-3 border-t border-white/10 pt-6 sm:flex-row">
          <a href="/demo" className="inline-flex items-center justify-center gap-2 rounded-full bg-cyan-300 px-5 py-3 text-sm font-semibold text-slate-950 transition hover:bg-cyan-200">
            {text.tryDemoCta}
            <ArrowRight className="h-4 w-4" />
          </a>
          <a href="/login?next=/v17/oracle" className="inline-flex items-center justify-center gap-2 rounded-full border border-white/10 bg-white/10 px-5 py-3 text-sm font-semibold text-slate-100 transition hover:bg-white/15">
            <ShieldCheck className="h-4 w-4" />
            {text.loginSaveCta}
          </a>
        </section>
      </section>
    </main>
  );
}

function ReplayStat({ label, value, tone = "default" }: { label: string; value: string; tone?: "default" | "ok" | "warn" }): ReactNode {
  return (
    <div className="rounded-2xl border border-white/10 bg-black/20 p-4">
      <p className="text-xs uppercase tracking-[0.16em] text-slate-500">{label}</p>
      <p className={`mt-1 break-words text-sm font-semibold ${tone === "ok" ? "text-emerald-100" : tone === "warn" ? "text-amber-100" : "text-white"}`}>
        {tone === "ok" ? <CheckCircle2 className="mr-1 inline h-4 w-4" /> : null}
        {value}
      </p>
    </div>
  );
}
