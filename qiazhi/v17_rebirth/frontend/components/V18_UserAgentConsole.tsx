"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import {
  AlertTriangle,
  ArrowRight,
  Bot,
  Bug,
  CheckCircle2,
  CircleDashed,
  ClipboardList,
  History,
  Loader2,
  MessageSquare,
  Send,
  ShieldCheck,
  Sparkles,
} from "lucide-react";

import { jsonPostInit, noStoreInit, requestJson } from "@/lib/apiClient";

type FeedbackType = "hit" | "miss" | "partial" | "unclear";
type MessageKind = "status" | "clarification" | "prediction" | "error";

type UserAgentConsoleProps = {
  displayName?: string;
  roleLabel?: string;
  onLogout?: () => void | Promise<void>;
};

type ChatMessage = {
  id: string;
  role: "user" | "agent" | "system";
  kind: MessageKind;
  text: string;
  createdAt: string;
  predictionId?: string;
  contractId?: string;
  conclusionRef?: string;
  uncertainty?: string;
  evidenceTrace?: unknown[];
  replay?: Record<string, unknown>;
  learningSignalId?: string;
};

type PredictionHistoryItem = {
  predictionId: string;
  contractId?: string;
  conclusionRef?: string;
  title: string;
  createdAt: string;
  replay?: Record<string, unknown>;
};

type BirthInfo = {
  year: string;
  month: string;
  day: string;
  hour: string;
  gender: "unknown" | "male" | "female";
};

const SESSION_STORAGE_KEY = "v18.user_agent.session_id";
const FEEDBACK_LABELS: Record<FeedbackType, string> = {
  hit: "准",
  miss: "不准",
  partial: "部分准",
  unclear: "不清楚",
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value && typeof value === "object" && !Array.isArray(value));
}

function unwrapEnvelope(value: unknown): Record<string, unknown> {
  if (isRecord(value) && isRecord(value.data)) return value.data;
  return isRecord(value) ? value : {};
}

function apiFailureMessage(value: unknown, requestError: string | undefined, fallback: string): string {
  return requestError || readString(value, ["message", "detail", "error"]) || readString(unwrapEnvelope(value), ["message", "detail", "error"]) || fallback;
}

function readRecord(source: unknown, key: string): Record<string, unknown> {
  if (!isRecord(source)) return {};
  const value = source[key];
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

function readBool(source: unknown, key: string, fallback = false): boolean {
  if (!isRecord(source)) return fallback;
  const value = source[key];
  return typeof value === "boolean" ? value : fallback;
}

function stableId(prefix: string): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return `${prefix}_${crypto.randomUUID()}`;
  }
  return `${prefix}_${Date.now()}_${Math.random().toString(16).slice(2)}`;
}

function nowIso(): string {
  return new Date().toISOString();
}

function compactJson(value: unknown): string {
  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value);
  }
}

function safeOutputText(safeOutput: Record<string, unknown>): string {
  const direct = readString(safeOutput, [
    "safe_output",
    "display_text",
    "text",
    "message",
    "answer",
    "summary",
    "clarification_question",
    "explanation",
  ]);
  if (direct) return direct;

  const sections = readRecord(safeOutput, "sections");
  const sectionText = readString(sections, ["summary", "main", "answer", "conclusion"]);
  if (sectionText) return sectionText;

  const conclusions = readArray(safeOutput, "conclusions");
  if (conclusions.length > 0) {
    return conclusions
      .map((item) => {
        if (typeof item === "string") return item;
        return readString(item, ["text", "summary", "conclusion", "claim"]);
      })
      .filter(Boolean)
      .join("\n");
  }

  return "";
}

function firstConclusionRef(...sources: unknown[]): string {
  for (const source of sources) {
    if (!isRecord(source)) continue;
    const keys = ["conclusion_ref", "conclusion_id", "conclusion_refs", "conclusion_ids"];
    for (const key of keys) {
      const value = source[key];
      if (typeof value === "string" && value.trim()) return value.trim();
      if (Array.isArray(value)) {
        const first = value.find((item) => typeof item === "string" && item.trim());
        if (typeof first === "string") return first.trim();
      }
    }
    const conclusions = readArray(source, "conclusions");
    for (const conclusion of conclusions) {
      const ref = readString(conclusion, ["conclusion_ref", "conclusion_id", "id", "ref"]);
      if (ref) return ref;
    }
  }
  return "";
}

function collectEvidenceTrace(...sources: unknown[]): unknown[] {
  for (const source of sources) {
    if (!isRecord(source)) continue;
    for (const key of ["evidence_trace", "rule_evidence", "evidence", "evidence_refs"]) {
      const value = source[key];
      if (Array.isArray(value) && value.length > 0) return value;
    }
    const safeOutput = readRecord(source, "safe_output");
    for (const key of ["evidence_trace", "rule_evidence", "evidence", "evidence_refs"]) {
      const value = safeOutput[key];
      if (Array.isArray(value) && value.length > 0) return value;
    }
  }
  return [];
}

function extractUncertainty(...sources: unknown[]): string {
  for (const source of sources) {
    const direct = readString(source, ["uncertainty", "uncertainty_text", "risk_note"]);
    if (direct) return direct;
    const safeOutput = readRecord(source, "safe_output");
    const nested = readString(safeOutput, ["uncertainty", "uncertainty_text", "risk_note"]);
    if (nested) return nested;
  }
  return "不确定性：当前解释仅覆盖 Prediction Contract 中已有证据，不扩展到 Contract 外的新判断。";
}

function extractPredictionId(...sources: unknown[]): string {
  for (const source of sources) {
    const value = readString(source, ["prediction_id", "predictionId"]);
    if (value) return value;
  }
  return "";
}

function extractContractId(...sources: unknown[]): string {
  for (const source of sources) {
    const value = readString(source, ["contract_id", "contractId"]);
    if (value) return value;
  }
  return "";
}

function buildProvidedBirthInfo(birthInfo: BirthInfo): Record<string, unknown> {
  const provided: Record<string, unknown> = {};
  if (birthInfo.year.trim()) provided.year = birthInfo.year.trim();
  if (birthInfo.month.trim()) provided.month = birthInfo.month.trim();
  if (birthInfo.day.trim()) provided.day = birthInfo.day.trim();
  if (birthInfo.hour.trim()) provided.hour = birthInfo.hour.trim();
  if (birthInfo.gender !== "unknown") provided.gender = birthInfo.gender;
  return provided;
}

function hasCompleteBirthInfo(birthInfo: BirthInfo): boolean {
  return Boolean(
    birthInfo.year.trim() &&
      birthInfo.month.trim() &&
      birthInfo.day.trim() &&
      birthInfo.hour.trim() &&
      birthInfo.gender !== "unknown",
  );
}

function buildChartSnapshot(birthInfo: BirthInfo): Record<string, unknown> {
  const provided = buildProvidedBirthInfo(birthInfo);
  if (!hasCompleteBirthInfo(birthInfo)) {
    return {
      source: "user_agent_frontend",
      completeness: "missing_required_birth_fields",
      provided_birth_fields: provided,
    };
  }

  const year = birthInfo.year.trim().padStart(4, "0");
  const month = birthInfo.month.trim().padStart(2, "0");
  const day = birthInfo.day.trim().padStart(2, "0");
  const hour = birthInfo.hour.trim().padStart(2, "0");
  const birthTime = `${year}-${month}-${day}T${hour}:00:00`;

  return {
    source: "user_agent_frontend",
    completeness: "complete_birth_fields",
    birth_time: birthTime,
    calendar: "solar",
    gender: birthInfo.gender,
    birth_fields: {
      year,
      month,
      day,
      hour,
      gender: birthInfo.gender,
    },
    four_pillars: {
      year,
      month,
      day,
      hour,
    },
  };
}

function extractSessionId(payload: Record<string, unknown>): string {
  const session = readRecord(payload, "session");
  return (
    readString(payload, ["agent_session_id", "session_id", "id"]) ||
    readString(session, ["agent_session_id", "session_id", "id"])
  );
}

function predictionTitle(text: string): string {
  const trimmed = text.replace(/\s+/g, " ").trim();
  if (!trimmed) return "Prediction Contract";
  return trimmed.length > 32 ? `${trimmed.slice(0, 32)}...` : trimmed;
}

export function V18_UserAgentConsole({ displayName, roleLabel, onLogout }: UserAgentConsoleProps): ReactNode {
  const [sessionId, setSessionId] = useState("");
  const [loadingSession, setLoadingSession] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [input, setInput] = useState("");
  const [birthInfo, setBirthInfo] = useState<BirthInfo>({
    year: "",
    month: "",
    day: "",
    hour: "",
    gender: "unknown",
  });
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [history, setHistory] = useState<PredictionHistoryItem[]>([]);
  const [debugOpen, setDebugOpen] = useState(false);
  const [error, setError] = useState("");

  const birthComplete = useMemo(() => hasCompleteBirthInfo(birthInfo), [birthInfo]);

  const appendMessage = useCallback((message: Omit<ChatMessage, "id" | "createdAt">) => {
    setMessages((prev) => [
      ...prev,
      {
        ...message,
        id: stableId("msg"),
        createdAt: nowIso(),
      },
    ]);
  }, []);

  const upsertHistory = useCallback((item: PredictionHistoryItem) => {
    setHistory((prev) => {
      const next = prev.filter((row) => row.predictionId !== item.predictionId);
      return [item, ...next].slice(0, 12);
    });
  }, []);

  const restoreSessionHistory = useCallback(
    (payload: Record<string, unknown>) => {
      const session = readRecord(payload, "session");
      const turns = readArray(payload, "turns").length > 0 ? readArray(payload, "turns") : readArray(session, "turns");
      turns.forEach((turn) => {
        const predictionId = extractPredictionId(turn);
        if (!predictionId) return;
        const contractId = extractContractId(turn);
        const safeOutput = readRecord(turn, "safe_output");
        upsertHistory({
          predictionId,
          contractId,
          conclusionRef: firstConclusionRef(turn, safeOutput),
          title: predictionTitle(safeOutputText(safeOutput) || readString(turn, ["user_message", "user_query"], "历史预测")),
          createdAt: readString(turn, ["created_at"], nowIso()),
        });
      });
    },
    [upsertHistory],
  );

  const fetchAgentSession = useCallback(
    async (candidateSessionId: string): Promise<boolean> => {
      const { data, ok } = await requestJson<unknown>(
        `/api/v18_1/agent/sessions/${encodeURIComponent(candidateSessionId)}`,
        noStoreInit(),
      );
      if (!ok) return false;
      const payload = unwrapEnvelope(data);
      const resolvedId = extractSessionId(payload) || candidateSessionId;
      setSessionId(resolvedId);
      restoreSessionHistory(payload);
      return true;
    },
    [restoreSessionHistory],
  );

  const createAgentSession = useCallback(async () => {
    const { data, ok, error: requestError } = await requestJson<unknown>(
      "/api/v18_1/agent/sessions",
      jsonPostInit(
        {
          surface: "user_agent_frontend",
          user_locale: "zh-CN",
          created_by: "ordinary_user_frontend",
        },
        noStoreInit(),
      ),
    );
    if (!ok) {
      throw new Error(apiFailureMessage(data, requestError, "Agent session 创建失败。"));
    }
    const payload = unwrapEnvelope(data);
    const resolvedId = extractSessionId(payload);
    if (!resolvedId) {
      throw new Error("Agent session 响应缺少 session_id。");
    }
    localStorage.setItem(SESSION_STORAGE_KEY, resolvedId);
    setSessionId(resolvedId);
    restoreSessionHistory(payload);
  }, [restoreSessionHistory]);

  useEffect(() => {
    let cancelled = false;
    async function boot() {
      setLoadingSession(true);
      setError("");
      try {
        const saved = localStorage.getItem(SESSION_STORAGE_KEY);
        if (saved) {
          const restored = await fetchAgentSession(saved);
          if (restored || cancelled) return;
          localStorage.removeItem(SESSION_STORAGE_KEY);
        }
        if (!cancelled) await createAgentSession();
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Agent session 初始化失败。");
        }
      } finally {
        if (!cancelled) setLoadingSession(false);
      }
    }
    void boot();
    return () => {
      cancelled = true;
    };
  }, [createAgentSession, fetchAgentSession]);

  const explainPrediction = useCallback(
    async ({
      predictionId,
      contractId,
      safeOutput,
      turnPayload,
    }: {
      predictionId: string;
      contractId?: string;
      safeOutput: Record<string, unknown>;
      turnPayload: Record<string, unknown>;
    }) => {
      const { data, ok, error: requestError } = await requestJson<unknown>(
        `/api/v18_1/predictions/${encodeURIComponent(predictionId)}/explain`,
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

      if (!ok) {
        throw new Error(apiFailureMessage(data, requestError, "Explanation verifier 拒绝输出。"));
      }

      const payload = unwrapEnvelope(data);
      const response =
        readRecord(payload, "explanation_response").safe_output || payload.explanation_response
          ? readRecord(payload, "explanation_response")
          : payload;
      const verifier = readRecord(response, "verifier");
      if (readBool(verifier, "ok", true) === false || readBool(response, "verified", true) === false) {
        throw new Error("Explanation Output Verifier 拦截了未验证输出。");
      }

      const responseSafeOutput = readRecord(response, "safe_output");
      const explanationText =
        readString(response, ["explanation", "verified_output", "output"]) ||
        safeOutputText(responseSafeOutput) ||
        safeOutputText(safeOutput);
      if (!explanationText) {
        throw new Error("Explanation endpoint 没有返回可展示的 verified output。");
      }

      const contractIdFromResponse = extractContractId(response, payload) || contractId;
      const conclusionRef = firstConclusionRef(response, responseSafeOutput, safeOutput, turnPayload);
      const evidenceTrace = collectEvidenceTrace(response, responseSafeOutput, safeOutput, turnPayload);
      const uncertainty = extractUncertainty(response, responseSafeOutput, safeOutput, turnPayload);

      appendMessage({
        role: "agent",
        kind: "prediction",
        text: explanationText,
        predictionId,
        contractId: contractIdFromResponse,
        conclusionRef,
        evidenceTrace,
        uncertainty,
      });

      upsertHistory({
        predictionId,
        contractId: contractIdFromResponse,
        conclusionRef,
        title: predictionTitle(explanationText),
        createdAt: nowIso(),
      });
    },
    [appendMessage, upsertHistory],
  );

  const submitTurn = useCallback(async () => {
    const userMessage = input.trim();
    if (!userMessage || !sessionId || submitting) return;

    setInput("");
    setError("");
    setSubmitting(true);
    appendMessage({
      role: "user",
      kind: "status",
      text: userMessage,
    });

    try {
      const chartSnapshot = buildChartSnapshot(birthInfo);
      const birthFields = buildProvidedBirthInfo(birthInfo);
      const { data, ok, error: requestError } = await requestJson<unknown>(
        `/api/v18_1/agent/sessions/${encodeURIComponent(sessionId)}/turns`,
        jsonPostInit(
          {
            request_id: stableId("agent_turn"),
            agent_session_id: sessionId,
            user_message: userMessage,
            user_query: userMessage,
            plugin_claims: [{ plugin_id: "plugin.agent", claim_id: "frontend_agent_runtime" }],
            normalized_intent: {
              source: "frontend_hint",
              topic: "bazi_prediction",
              language: "zh-CN",
              requires_chart_snapshot: true,
            },
            missing_info_policy: "clarify_before_predict",
            birth_payload: birthFields,
            birth_info: birthFields,
            chart_snapshot: chartSnapshot,
            allowed_output_scope: ["clarification_question", "prediction_safe_output"],
            surface: "ordinary_user_agent",
          },
          noStoreInit(),
        ),
      );

      if (!ok) {
        throw new Error(apiFailureMessage(data, requestError, "Agent turn 提交失败。"));
      }

      const payload = unwrapEnvelope(data);
      const turn = readRecord(payload, "turn");
      const safeOutput = readRecord(turn, "safe_output");
      const fallbackSafeOutput = Object.keys(safeOutput).length > 0 ? safeOutput : readRecord(payload, "safe_output");
      const missingFields =
        readArray(turn, "missing_fields").length > 0
          ? readArray(turn, "missing_fields")
          : readArray(fallbackSafeOutput, "missing_fields");
      const isClarification =
        readString(fallbackSafeOutput, ["type"]) === "clarification_question" ||
        readBool(fallbackSafeOutput, "is_prediction", true) === false ||
        missingFields.length > 0 ||
        !birthComplete;
      const predictionId = extractPredictionId(payload, turn, fallbackSafeOutput);
      const contractId = extractContractId(payload, turn, fallbackSafeOutput);

      if (isClarification || !predictionId) {
        const clarification =
          safeOutputText(fallbackSafeOutput) ||
          `还需要补充：${missingFields.length > 0 ? missingFields.join("、") : "出生年、月、日、时与性别"}。补齐前不会生成预测。`;
        appendMessage({
          role: "agent",
          kind: "clarification",
          text: clarification,
          uncertainty: "未进入 Prediction Contract：缺少关键排盘信息，所以此轮只允许追问，不展示预测。",
        });
        return;
      }

      await explainPrediction({
        predictionId,
        contractId,
        safeOutput: fallbackSafeOutput,
        turnPayload: turn,
      });
    } catch (err) {
      const message = err instanceof Error ? err.message : "Agent 处理失败。";
      setError(message);
      appendMessage({
        role: "system",
        kind: "error",
        text: message,
      });
    } finally {
      setSubmitting(false);
    }
  }, [appendMessage, birthComplete, birthInfo, explainPrediction, input, sessionId, submitting]);

  const submitFeedback = useCallback(
    async (message: ChatMessage, feedbackType: FeedbackType) => {
      if (!message.predictionId || !message.conclusionRef) return;
      setError("");
      try {
        const { data, ok, error: requestError } = await requestJson<unknown>(
          `/api/v18_1/predictions/${encodeURIComponent(message.predictionId)}/feedback`,
          jsonPostInit(
            {
              request_id: stableId("feedback"),
              prediction_id: message.predictionId,
              conclusion_ref: message.conclusionRef,
              conclusion_id: message.conclusionRef,
              feedback_type: feedbackType,
              user_comment: "",
              observed_event: {
                source: "user_agent_frontend",
                label: FEEDBACK_LABELS[feedbackType],
              },
              observed_at: nowIso(),
            },
            noStoreInit(),
          ),
        );
        if (!ok) {
          throw new Error(apiFailureMessage(data, requestError, "Feedback 提交失败。"));
        }
        const payload = unwrapEnvelope(data);
        const learningSignal = readRecord(payload, "learning_signal");
        const signalId = readString(learningSignal, ["signal_id", "id"]);
        setMessages((prev) =>
          prev.map((row) =>
            row.id === message.id
              ? {
                  ...row,
                  learningSignalId: signalId || "created",
                }
              : row,
          ),
        );
      } catch (err) {
        const messageText = err instanceof Error ? err.message : "Feedback 提交失败。";
        setError(messageText);
      }
    },
    [],
  );

  const loadReplay = useCallback(async (item: PredictionHistoryItem) => {
    setError("");
    try {
      const { data, ok, error: requestError } = await requestJson<unknown>(
        `/api/v18_1/predictions/${encodeURIComponent(item.predictionId)}/replay`,
        noStoreInit(),
      );
      if (!ok) {
        throw new Error(apiFailureMessage(data, requestError, "Replay 加载失败。"));
      }
      const payload = unwrapEnvelope(data);
      setHistory((prev) =>
        prev.map((row) => (row.predictionId === item.predictionId ? { ...row, replay: payload } : row)),
      );
      setMessages((prev) =>
        prev.map((row) =>
          row.predictionId === item.predictionId
            ? {
                ...row,
                replay: payload,
              }
            : row,
        ),
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Replay 加载失败。");
    }
  }, []);

  const latestPrediction = useMemo(() => {
    return [...messages].reverse().find((message) => message.kind === "prediction" && message.predictionId);
  }, [messages]);

  return (
    <main className="min-h-screen overflow-hidden bg-[#090d14] text-slate-100">
      <div className="pointer-events-none fixed inset-0">
        <div className="absolute left-[-10%] top-[-18%] h-96 w-96 rounded-full bg-cyan-500/20 blur-3xl" />
        <div className="absolute bottom-[-18%] right-[-8%] h-[34rem] w-[34rem] rounded-full bg-amber-500/10 blur-3xl" />
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(255,255,255,0.08),transparent_34%),linear-gradient(135deg,rgba(255,255,255,0.05),transparent_35%)]" />
      </div>

      <section className="relative mx-auto flex min-h-screen w-full max-w-7xl flex-col px-4 py-5 sm:px-6 lg:px-8">
        <header className="mb-5 flex flex-col gap-4 rounded-[2rem] border border-white/10 bg-white/[0.06] p-5 shadow-2xl shadow-black/30 backdrop-blur md:flex-row md:items-center md:justify-between">
          <div>
            <div className="mb-2 flex items-center gap-2 text-sm text-cyan-200">
              <ShieldCheck className="h-4 w-4" />
              Contract-first Agent
            </div>
            <h1 className="text-2xl font-semibold tracking-tight md:text-3xl">普通用户命理 Agent</h1>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-300">
              这里展示的内容只来自 Prediction Contract 的 safe output 或 verified explanation。LLM 只负责解释，不负责新增判断。
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-3 text-sm">
            <span className="rounded-full border border-white/10 bg-black/20 px-3 py-2 text-slate-300">
              {displayName || "User"} {roleLabel ? `· ${roleLabel}` : ""}
            </span>
            <button
              type="button"
              onClick={() => setDebugOpen((value) => !value)}
              className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/10 px-4 py-2 text-slate-100 transition hover:bg-white/15"
            >
              <Bug className="h-4 w-4" />
              Debug
            </button>
            {onLogout ? (
              <button
                type="button"
                onClick={() => void onLogout()}
                className="rounded-full border border-white/10 bg-black/20 px-4 py-2 text-slate-300 transition hover:bg-black/30"
              >
                退出
              </button>
            ) : null}
          </div>
        </header>

        {debugOpen ? (
          <section className="mb-5 rounded-3xl border border-cyan-300/20 bg-cyan-300/10 p-4 text-sm text-cyan-50">
            <div className="mb-2 flex items-center gap-2 font-medium">
              <Bug className="h-4 w-4" />
              Debug Panel
            </div>
            <div className="grid gap-2 md:grid-cols-3">
              <DebugLine label="agent_session_id" value={sessionId || "initializing"} />
              <DebugLine label="latest_prediction_id" value={latestPrediction?.predictionId || "none"} />
              <DebugLine label="latest_contract_id" value={latestPrediction?.contractId || "none"} />
            </div>
          </section>
        ) : null}

        <div className="grid flex-1 gap-5 lg:grid-cols-[minmax(0,1fr)_22rem]">
          <section className="flex min-h-[34rem] flex-col rounded-[2rem] border border-white/10 bg-[#111827]/80 shadow-2xl shadow-black/30 backdrop-blur">
            <div className="border-b border-white/10 p-5">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <h2 className="flex items-center gap-2 text-lg font-semibold">
                    <Bot className="h-5 w-5 text-cyan-200" />
                    Agent 对话
                  </h2>
                  <p className="mt-1 text-sm text-slate-400">信息不足时只追问；信息完整后才进入 Contract Pipeline。</p>
                </div>
                <StatusPill loading={loadingSession || submitting} ready={Boolean(sessionId)} />
              </div>
            </div>

            <div className="flex-1 space-y-4 overflow-y-auto p-5">
              {messages.length === 0 ? (
                <div className="grid min-h-[18rem] place-items-center rounded-3xl border border-dashed border-white/10 bg-white/[0.03] p-8 text-center">
                  <div>
                    <Sparkles className="mx-auto mb-4 h-9 w-9 text-amber-200" />
                    <h3 className="text-xl font-semibold">先说你的问题，也可以先补出生信息</h3>
                    <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-slate-400">
                      例如：“我想看今年事业和财运走势。”缺关键排盘信息时，Agent 会追问而不是提前预测。
                    </p>
                  </div>
                </div>
              ) : (
                messages.map((message) => (
                  <MessageCard
                    key={message.id}
                    message={message}
                    onFeedback={submitFeedback}
                    onReplay={() =>
                      message.predictionId
                        ? void loadReplay({
                            predictionId: message.predictionId,
                            contractId: message.contractId,
                            conclusionRef: message.conclusionRef,
                            title: predictionTitle(message.text),
                            createdAt: message.createdAt,
                          })
                        : undefined
                    }
                  />
                ))
              )}
            </div>

            <div className="border-t border-white/10 p-5">
              {error ? (
                <div className="mb-4 flex items-start gap-2 rounded-2xl border border-rose-300/20 bg-rose-500/10 p-3 text-sm text-rose-100">
                  <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
                  <span>{error}</span>
                </div>
              ) : null}
              <div className="grid gap-3 md:grid-cols-5">
                <BirthInput label="年" value={birthInfo.year} onChange={(year) => setBirthInfo((prev) => ({ ...prev, year }))} />
                <BirthInput
                  label="月"
                  value={birthInfo.month}
                  onChange={(month) => setBirthInfo((prev) => ({ ...prev, month }))}
                />
                <BirthInput label="日" value={birthInfo.day} onChange={(day) => setBirthInfo((prev) => ({ ...prev, day }))} />
                <BirthInput
                  label="时"
                  value={birthInfo.hour}
                  onChange={(hour) => setBirthInfo((prev) => ({ ...prev, hour }))}
                />
                <label className="block">
                  <span className="mb-1 block text-xs text-slate-400">性别</span>
                  <select
                    value={birthInfo.gender}
                    onChange={(event) =>
                      setBirthInfo((prev) => ({ ...prev, gender: event.target.value as BirthInfo["gender"] }))
                    }
                    className="h-11 w-full rounded-2xl border border-white/10 bg-black/30 px-3 text-sm text-slate-100 outline-none transition focus:border-cyan-300/50"
                  >
                    <option value="unknown">未填</option>
                    <option value="male">男</option>
                    <option value="female">女</option>
                  </select>
                </label>
              </div>
              <div className="mt-4 flex gap-3">
                <textarea
                  value={input}
                  onChange={(event) => setInput(event.target.value)}
                  onKeyDown={(event) => {
                    if (event.key === "Enter" && (event.metaKey || event.ctrlKey)) {
                      void submitTurn();
                    }
                  }}
                  placeholder="输入你的问题。按 Cmd/Ctrl + Enter 发送。"
                  className="min-h-24 flex-1 resize-none rounded-3xl border border-white/10 bg-black/30 px-4 py-3 text-sm leading-6 text-slate-100 outline-none transition placeholder:text-slate-500 focus:border-cyan-300/50"
                />
                <button
                  type="button"
                  onClick={() => void submitTurn()}
                  disabled={!input.trim() || !sessionId || submitting || loadingSession}
                  className="inline-flex w-28 shrink-0 items-center justify-center gap-2 rounded-3xl bg-cyan-300 px-4 py-3 text-sm font-semibold text-slate-950 transition hover:bg-cyan-200 disabled:cursor-not-allowed disabled:bg-slate-600 disabled:text-slate-300"
                >
                  {submitting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
                  发送
                </button>
              </div>
              <div className="mt-3 flex items-center gap-2 text-xs text-slate-500">
                <CircleDashed className="h-3.5 w-3.5" />
                {birthComplete ? "出生信息已完整，下一轮可进入预测链路。" : "出生信息未完整时，Agent 只能追问，不能展示预测。"}
              </div>
            </div>
          </section>

          <aside className="space-y-5">
            <section className="rounded-[2rem] border border-white/10 bg-white/[0.06] p-5 shadow-2xl shadow-black/20 backdrop-blur">
              <h2 className="mb-3 flex items-center gap-2 text-lg font-semibold">
                <ClipboardList className="h-5 w-5 text-amber-200" />
                安全边界
              </h2>
              <ul className="space-y-3 text-sm leading-6 text-slate-300">
                <li>不展示 raw LLM output，只展示 safe output 或 verified explanation。</li>
                <li>缺出生信息时只展示追问，不生成 conclusion。</li>
                <li>反馈必须绑定 prediction_id 和 conclusion_ref。</li>
                <li>evidence trace 默认折叠，debug 信息默认隐藏。</li>
              </ul>
            </section>

            <section className="rounded-[2rem] border border-white/10 bg-white/[0.06] p-5 shadow-2xl shadow-black/20 backdrop-blur">
              <h2 className="mb-3 flex items-center gap-2 text-lg font-semibold">
                <History className="h-5 w-5 text-cyan-200" />
                Replay / History
              </h2>
              {history.length === 0 ? (
                <p className="rounded-2xl border border-dashed border-white/10 bg-black/20 p-4 text-sm text-slate-400">
                  完成一次预测后，这里会展示可回放记录。
                </p>
              ) : (
                <div className="space-y-3">
                  {history.map((item) => (
                    <article key={item.predictionId} className="rounded-2xl border border-white/10 bg-black/20 p-4">
                      <div className="text-sm font-medium text-slate-100">{item.title}</div>
                      <div className="mt-1 text-xs text-slate-500">{new Date(item.createdAt).toLocaleString()}</div>
                      <button
                        type="button"
                        onClick={() => void loadReplay(item)}
                        className="mt-3 inline-flex items-center gap-2 rounded-full border border-white/10 px-3 py-1.5 text-xs text-cyan-100 transition hover:bg-white/10"
                      >
                        查看 replay
                        <ArrowRight className="h-3.5 w-3.5" />
                      </button>
                      {item.replay ? (
                        <details className="mt-3 rounded-xl bg-black/30 p-3 text-xs text-slate-300">
                          <summary className="cursor-pointer text-slate-100">Replay 摘要</summary>
                          <pre className="mt-2 max-h-56 overflow-auto whitespace-pre-wrap break-words text-[11px] text-slate-400">
                            {compactJson({
                              ledger: readRecord(item.replay, "ledger"),
                              feedback_count: readArray(item.replay, "feedback").length,
                              learning_signal_count: readArray(item.replay, "learning_signals").length,
                              rule_drift: readBool(item.replay, "rule_drift"),
                            })}
                          </pre>
                        </details>
                      ) : null}
                    </article>
                  ))}
                </div>
              )}
            </section>
          </aside>
        </div>
      </section>
    </main>
  );
}

function DebugLine({ label, value }: { label: string; value: string }): ReactNode {
  return (
    <div className="rounded-2xl border border-cyan-100/10 bg-black/20 p-3">
      <div className="text-[11px] uppercase tracking-[0.2em] text-cyan-200/70">{label}</div>
      <div className="mt-1 break-all font-mono text-xs text-cyan-50">{value}</div>
    </div>
  );
}

function StatusPill({ loading, ready }: { loading: boolean; ready: boolean }): ReactNode {
  if (loading) {
    return (
      <span className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/10 px-3 py-1.5 text-xs text-slate-300">
        <Loader2 className="h-3.5 w-3.5 animate-spin" />
        connecting
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-2 rounded-full border border-emerald-300/20 bg-emerald-300/10 px-3 py-1.5 text-xs text-emerald-100">
      <CheckCircle2 className="h-3.5 w-3.5" />
      {ready ? "ready" : "offline"}
    </span>
  );
}

function BirthInput({ label, value, onChange }: { label: string; value: string; onChange: (value: string) => void }): ReactNode {
  return (
    <label className="block">
      <span className="mb-1 block text-xs text-slate-400">{label}</span>
      <input
        value={value}
        onChange={(event) => onChange(event.target.value.replace(/[^\d]/g, ""))}
        inputMode="numeric"
        className="h-11 w-full rounded-2xl border border-white/10 bg-black/30 px-3 text-sm text-slate-100 outline-none transition placeholder:text-slate-500 focus:border-cyan-300/50"
        placeholder={label === "年" ? "1990" : label === "时" ? "09" : "01"}
      />
    </label>
  );
}

function MessageCard({
  message,
  onFeedback,
  onReplay,
}: {
  message: ChatMessage;
  onFeedback: (message: ChatMessage, feedbackType: FeedbackType) => void | Promise<void>;
  onReplay: () => void;
}): ReactNode {
  const isUser = message.role === "user";
  const isPrediction = message.kind === "prediction";
  const isClarification = message.kind === "clarification";
  const isError = message.kind === "error";

  return (
    <article className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[92%] rounded-[1.5rem] border p-4 md:max-w-[78%] ${
          isUser
            ? "border-cyan-300/20 bg-cyan-300/15"
            : isError
              ? "border-rose-300/20 bg-rose-500/10"
              : isClarification
                ? "border-amber-300/20 bg-amber-300/10"
                : "border-white/10 bg-white/[0.06]"
        }`}
      >
        <div className="mb-2 flex items-center gap-2 text-xs uppercase tracking-[0.16em] text-slate-400">
          {isUser ? <MessageSquare className="h-3.5 w-3.5" /> : <Bot className="h-3.5 w-3.5" />}
          {isUser ? "User" : isPrediction ? "Verified Explanation" : isClarification ? "Clarification" : "System"}
        </div>
        <p className="whitespace-pre-wrap text-sm leading-7 text-slate-100">{message.text}</p>

        {!isUser && message.uncertainty ? (
          <div className="mt-3 rounded-2xl border border-white/10 bg-black/20 p-3 text-xs leading-5 text-slate-300">
            {message.uncertainty}
          </div>
        ) : null}

        {isPrediction && message.evidenceTrace && message.evidenceTrace.length > 0 ? (
          <details className="mt-3 rounded-2xl border border-white/10 bg-black/20 p-3 text-xs text-slate-300">
            <summary className="cursor-pointer select-none text-slate-100">Evidence trace（默认折叠）</summary>
            <pre className="mt-3 max-h-72 overflow-auto whitespace-pre-wrap break-words text-[11px] leading-5 text-slate-400">
              {compactJson(message.evidenceTrace)}
            </pre>
          </details>
        ) : null}

        {isPrediction ? (
          <div className="mt-4 flex flex-wrap gap-2">
            {(Object.keys(FEEDBACK_LABELS) as FeedbackType[]).map((feedbackType) => (
              <button
                key={feedbackType}
                type="button"
                disabled={!message.predictionId || !message.conclusionRef || Boolean(message.learningSignalId)}
                onClick={() => void onFeedback(message, feedbackType)}
                className="rounded-full border border-white/10 bg-black/20 px-3 py-1.5 text-xs text-slate-200 transition hover:bg-white/10 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {FEEDBACK_LABELS[feedbackType]}
              </button>
            ))}
            <button
              type="button"
              onClick={onReplay}
              className="rounded-full border border-cyan-200/20 bg-cyan-200/10 px-3 py-1.5 text-xs text-cyan-100 transition hover:bg-cyan-200/15"
            >
              Replay
            </button>
          </div>
        ) : null}

        {message.learningSignalId ? (
          <div className="mt-3 rounded-2xl border border-emerald-300/20 bg-emerald-300/10 p-3 text-xs text-emerald-100">
            Feedback 已提交，learning_signal 已生成：{message.learningSignalId}
          </div>
        ) : null}

        {message.replay ? (
          <details className="mt-3 rounded-2xl border border-white/10 bg-black/20 p-3 text-xs text-slate-300">
            <summary className="cursor-pointer text-slate-100">Replay 结果</summary>
            <pre className="mt-3 max-h-72 overflow-auto whitespace-pre-wrap break-words text-[11px] text-slate-400">
              {compactJson({
                ledger: readRecord(message.replay, "ledger"),
                contract_id: readString(readRecord(message.replay, "contract"), ["contract_id"]),
                feedback_count: readArray(message.replay, "feedback").length,
                learning_signal_count: readArray(message.replay, "learning_signals").length,
                rule_drift: readBool(message.replay, "rule_drift"),
              })}
            </pre>
          </details>
        ) : null}
      </div>
    </article>
  );
}
