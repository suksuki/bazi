"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import {
  AlertTriangle,
  BadgeCheck,
  Bot,
  BrainCircuit,
  Bug,
  ChevronRight,
  ClipboardCheck,
  Database,
  History,
  Layers3,
  Loader2,
  MessageSquareText,
  Send,
  ShieldCheck,
  Sparkles,
  TrendingUp,
} from "lucide-react";

import { jsonPostInit, noStoreInit, requestJson } from "@/lib/apiClient";

type FeedbackType = "hit" | "miss" | "partial" | "unclear";
type BirthGender = "unknown" | "male" | "female";

type OracleUserAgentExperienceProps = {
  displayName?: string;
  roleLabel?: string;
  isAdmin?: boolean;
  onLogout?: () => void | Promise<void>;
};

type BirthInfo = {
  year: string;
  month: string;
  day: string;
  hour: string;
  gender: BirthGender;
};

type OraclePrediction = {
  predictionId: string;
  contractId: string;
  conclusionRef: string;
  conclusionTitle: string;
  summary: string;
  explanationText: string;
  confidence: number | null;
  uncertaintyText: string;
  uncertaintyLevel: "low" | "medium" | "high" | "unknown";
  uncertaintyReasons: string[];
  missingAssumptions: string[];
  sensitiveFactors: string[];
  evidenceTrace: EvidenceItem[];
  chartSnapshot: Record<string, unknown>;
  replay: Record<string, unknown>;
  verifierStatus: string;
  engineVersion: string;
  modelVersion: string;
  ledgerId: string;
  contractHash: string;
  ruleDrift: boolean;
  ledgerStatus: string;
  createdAt: string;
};

type EvidenceItem = {
  ruleId: string;
  version: string;
  contentHash: string;
  matchedFacts: unknown[];
  effect: unknown;
  confidenceDelta: number | null;
};

type PredictionHistoryItem = {
  predictionId: string;
  contractId: string;
  conclusionTitle: string;
  feedbackStatus: string;
  ruleDrift: boolean;
  createdAt: string;
  replay?: Record<string, unknown>;
};

const SESSION_STORAGE_KEY = "v18.oracle_agent.session_id";
const FEEDBACK_LABELS: Record<FeedbackType, string> = {
  hit: "准",
  miss: "不准",
  partial: "部分准",
  unclear: "不清楚",
};

const FEEDBACK_HINTS: Record<FeedbackType, string> = {
  hit: "命中会形成正向 learning_signal，但不会直接改 active rule。",
  miss: "不命中会进入规则复核线索，不会直接改 active rule。",
  partial: "部分命中会提示 Reviewer 关注条件边界。",
  unclear: "不清楚会先进入观察，不触发规则修改。",
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

function readNumber(source: unknown, keys: string[]): number | null {
  if (!isRecord(source)) return null;
  for (const key of keys) {
    const value = source[key];
    if (typeof value === "number" && Number.isFinite(value)) return value;
    if (typeof value === "string" && value.trim() && Number.isFinite(Number(value))) return Number(value);
  }
  return null;
}

function stableId(prefix: string): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) return `${prefix}_${crypto.randomUUID()}`;
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

function clampConfidence(value: number | null): number | null {
  if (value === null || !Number.isFinite(value)) return null;
  if (value > 1) return Math.max(0, Math.min(100, value)) / 100;
  return Math.max(0, Math.min(1, value));
}

function shortHash(value: string): string {
  if (!value) return "n/a";
  return value.length > 18 ? `${value.slice(0, 14)}...` : value;
}

function safeOutputText(safeOutput: Record<string, unknown>): string {
  const direct = readString(safeOutput, ["safe_output", "display_text", "text", "message", "answer", "summary", "explanation"]);
  if (direct) return direct;

  const sections = readRecord(safeOutput, "sections");
  const sectionText = readString(sections, ["summary", "main", "answer", "conclusion"]);
  if (sectionText) return sectionText;

  const sectionConclusion = sections.conclusion;
  if (Array.isArray(sectionConclusion)) {
    return sectionConclusion.map((item) => String(item || "").trim()).filter(Boolean).join("；");
  }

  const conclusions = readArray(safeOutput, "conclusions");
  if (conclusions.length > 0) {
    return conclusions
      .map((item) => {
        if (typeof item === "string") return item;
        return readString(item, ["text", "summary", "conclusion", "claim"]);
      })
      .filter(Boolean)
      .join("；");
  }

  return "";
}

function firstConclusionRef(...sources: unknown[]): string {
  for (const source of sources) {
    if (!isRecord(source)) continue;
    const direct = readString(source, ["conclusion_ref", "conclusion_id", "id", "ref"]);
    if (direct) return direct;
    for (const key of ["conclusion_refs", "conclusion_ids"]) {
      const value = source[key];
      if (Array.isArray(value)) {
        const first = value.find((item) => typeof item === "string" && item.trim());
        if (typeof first === "string") return first.trim();
      }
    }
    const sections = readRecord(source, "sections");
    for (const key of ["conclusion_refs", "conclusion_ids"]) {
      const value = sections[key];
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

function extractSessionId(payload: Record<string, unknown>): string {
  const session = readRecord(payload, "session");
  return readString(payload, ["agent_session_id", "session_id", "id"]) || readString(session, ["agent_session_id", "session_id", "id"]);
}

function providedBirthPayload(birthInfo: BirthInfo): Record<string, unknown> {
  const payload: Record<string, unknown> = {};
  if (birthInfo.year.trim()) payload.year = birthInfo.year.trim();
  if (birthInfo.month.trim()) payload.month = birthInfo.month.trim();
  if (birthInfo.day.trim()) payload.day = birthInfo.day.trim();
  if (birthInfo.hour.trim()) payload.hour = birthInfo.hour.trim();
  if (birthInfo.gender !== "unknown") payload.gender = birthInfo.gender;
  return payload;
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
  const birthPayload = providedBirthPayload(birthInfo);
  if (!hasCompleteBirthInfo(birthInfo)) {
    return {
      source: "oracle_user_agent_ui",
      completeness: "missing_required_birth_fields",
      provided_birth_fields: birthPayload,
    };
  }

  const year = birthInfo.year.trim().padStart(4, "0");
  const month = birthInfo.month.trim().padStart(2, "0");
  const day = birthInfo.day.trim().padStart(2, "0");
  const hour = birthInfo.hour.trim().padStart(2, "0");
  return {
    source: "oracle_user_agent_ui",
    completeness: "complete_birth_fields",
    birth_time: `${year}-${month}-${day}T${hour}:00:00`,
    calendar: "solar",
    gender: birthInfo.gender,
    birth_fields: { year, month, day, hour, gender: birthInfo.gender },
    four_pillars: { year, month, day, hour },
  };
}

function normalizeEvidence(value: unknown): EvidenceItem[] {
  const rows = Array.isArray(value) ? value : [];
  return rows
    .map((row) => {
      const evidence = isRecord(row) ? row : {};
      return {
        ruleId: readString(evidence, ["rule_id", "ruleId", "id"]),
        version: readString(evidence, ["version", "rule_version"]),
        contentHash: readString(evidence, ["content_hash", "rule_hash", "hash"]),
        matchedFacts: readArray(evidence, "matched_facts").length ? readArray(evidence, "matched_facts") : readArray(evidence, "facts"),
        effect: evidence.effect || evidence.effects || evidence.effect_delta || {},
        confidenceDelta: clampConfidence(readNumber(evidence, ["confidence_delta", "confidence", "score"])),
      };
    })
    .filter((item) => item.ruleId || item.version || item.contentHash || item.matchedFacts.length > 0);
}

function evidenceFromSources(...sources: unknown[]): EvidenceItem[] {
  for (const source of sources) {
    if (!isRecord(source)) continue;
    const direct =
      normalizeEvidence(source.rule_evidence).length > 0
        ? normalizeEvidence(source.rule_evidence)
        : normalizeEvidence(source.evidence_trace).length > 0
          ? normalizeEvidence(source.evidence_trace)
          : normalizeEvidence(source.evidence);
    if (direct.length > 0) return direct;
    const contract = readRecord(source, "contract");
    const fromContract = normalizeEvidence(contract.rule_evidence).length > 0 ? normalizeEvidence(contract.rule_evidence) : normalizeEvidence(readArray(source, "evidence"));
    if (fromContract.length > 0) return fromContract;
  }
  return [];
}

function uncertaintyFromContract(contract: Record<string, unknown>, explanation: Record<string, unknown>): Pick<
  OraclePrediction,
  "uncertaintyText" | "uncertaintyLevel" | "uncertaintyReasons" | "missingAssumptions" | "sensitiveFactors"
> {
  const raw = readRecord(contract, "uncertainty");
  const score = clampConfidence(readNumber(raw, ["score", "value"]));
  const reasons = readArray(raw, "source").map((item) => String(item || "").trim()).filter(Boolean);
  const extraReasons = readArray(raw, "reasons").map((item) => String(item || "").trim()).filter(Boolean);
  const assumptions = readArray(raw, "missing_assumptions").map((item) => String(item || "").trim()).filter(Boolean);
  const factors = readArray(raw, "sensitive_factors").map((item) => String(item || "").trim()).filter(Boolean);
  const explanationUncertainty = readString(explanation, ["uncertainty", "uncertainty_text", "risk_note"]);
  const level: OraclePrediction["uncertaintyLevel"] =
    score === null ? "unknown" : score >= 0.66 ? "high" : score >= 0.34 ? "medium" : "low";
  const reasonList = [...reasons, ...extraReasons];
  return {
    uncertaintyText:
      explanationUncertainty ||
      (score === null
        ? "不确定性：当前仅覆盖 Prediction Contract 中已有证据，不扩展到 Contract 外判断。"
        : `不确定性评分 ${Math.round(score * 100)}%，需结合证据边界理解。`),
    uncertaintyLevel: level,
    uncertaintyReasons: reasonList.length > 0 ? reasonList : ["证据覆盖范围有限", "用户问题仍可能受外部环境影响"],
    missingAssumptions: assumptions.length > 0 ? assumptions : ["未补充的现实背景不会被系统自行假设"],
    sensitiveFactors: factors.length > 0 ? factors : ["时间窗口", "现实选择", "环境变量"],
  };
}

function confidenceFromSources(contract: Record<string, unknown>, safeOutput: Record<string, unknown>, evidence: EvidenceItem[]): number | null {
  const direct = clampConfidence(readNumber(contract, ["confidence", "confidence_score"]));
  if (direct !== null) return direct;
  const safe = clampConfidence(readNumber(safeOutput, ["confidence", "confidence_score"]));
  if (safe !== null) return safe;
  const deltas = evidence.map((item) => item.confidenceDelta).filter((item): item is number => typeof item === "number");
  if (deltas.length === 0) return null;
  return clampConfidence(deltas.reduce((sum, item) => sum + item, 0) / deltas.length);
}

function conclusionFromSources(contract: Record<string, unknown>, safeOutput: Record<string, unknown>, explanationText: string): string {
  const contractConclusions = readArray(contract, "conclusions");
  for (const row of contractConclusions) {
    const claim = readString(row, ["title", "claim", "text", "summary"]);
    if (claim) return claim;
  }
  const safeText = safeOutputText(safeOutput);
  if (safeText) return safeText.length > 72 ? `${safeText.slice(0, 72)}...` : safeText;
  return explanationText ? "系统裁决已生成" : "等待系统裁决";
}

function buildPrediction({
  predictionId,
  contractId,
  turnSafeOutput,
  explanationPayload,
  replayPayload,
  chartSnapshot,
}: {
  predictionId: string;
  contractId: string;
  turnSafeOutput: Record<string, unknown>;
  explanationPayload: Record<string, unknown>;
  replayPayload: Record<string, unknown>;
  chartSnapshot: Record<string, unknown>;
}): OraclePrediction {
  const explanationResponse =
    readRecord(explanationPayload, "explanation_response").safe_output || explanationPayload.explanation_response
      ? readRecord(explanationPayload, "explanation_response")
      : explanationPayload;
  const explanationSafeOutput = readRecord(explanationResponse, "safe_output");
  const replayContract = readRecord(replayPayload, "contract");
  const contract = Object.keys(replayContract).length > 0 ? replayContract : readRecord(explanationPayload, "contract");
  const ledger = readRecord(replayPayload, "ledger");
  const evidenceTrace = evidenceFromSources(explanationResponse, explanationSafeOutput, replayPayload, contract, turnSafeOutput);
  const explanationText =
    readString(explanationResponse, ["explanation", "verified_output", "output"]) ||
    safeOutputText(explanationSafeOutput) ||
    safeOutputText(turnSafeOutput) ||
    "系统解释已通过输出校验，但当前没有可展示的长文本。";
  const confidence = confidenceFromSources(contract, turnSafeOutput, evidenceTrace);
  const uncertainty = uncertaintyFromContract(contract, explanationResponse);
  const conclusionTitle = conclusionFromSources(contract, turnSafeOutput, explanationText);
  const conclusionRef = firstConclusionRef(turnSafeOutput, explanationSafeOutput, explanationResponse, ledger, contract);
  const verifier = readRecord(explanationResponse, "verifier");
  const verifierStatus =
    readString(verifier, ["status", "action"]) ||
    (readBool(verifier, "ok", true) && readBool(explanationResponse, "verified", true) ? "verified" : "blocked");

  return {
    predictionId,
    contractId: extractContractId(explanationResponse, explanationPayload, contract) || contractId,
    conclusionRef,
    conclusionTitle,
    summary: safeOutputText(turnSafeOutput) || explanationText,
    explanationText,
    confidence,
    ...uncertainty,
    evidenceTrace,
    chartSnapshot: Object.keys(chartSnapshot).length > 0 ? chartSnapshot : readRecord(contract, "chart_snapshot"),
    replay: replayPayload,
    verifierStatus,
    engineVersion: readString(contract, ["engine_version", "schema_version"], "v18.1"),
    modelVersion: readString(contract, ["model_version", "engine_version"], "v18.1"),
    ledgerId: readString(ledger, ["ledger_id", "id"]),
    contractHash: readString(ledger, ["contract_hash", "prediction_hash"]),
    ruleDrift: readBool(replayPayload, "rule_drift", false),
    ledgerStatus: Object.keys(ledger).length > 0 ? "written" : "not loaded",
    createdAt: nowIso(),
  };
}

function historyTitle(value: string): string {
  const text = value.replace(/\s+/g, " ").trim();
  if (!text) return "系统裁决";
  return text.length > 36 ? `${text.slice(0, 36)}...` : text;
}

export function V18_OracleUserAgentExperience({
  displayName,
  roleLabel,
  isAdmin = false,
  onLogout,
}: OracleUserAgentExperienceProps): ReactNode {
  const [sessionId, setSessionId] = useState("");
  const [loadingSession, setLoadingSession] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [question, setQuestion] = useState("");
  const [birthInfo, setBirthInfo] = useState<BirthInfo>({ year: "", month: "", day: "", hour: "", gender: "unknown" });
  const [clarificationQuestion, setClarificationQuestion] = useState("");
  const [missingFields, setMissingFields] = useState<string[]>([]);
  const [currentPrediction, setCurrentPrediction] = useState<OraclePrediction | null>(null);
  const [history, setHistory] = useState<PredictionHistoryItem[]>([]);
  const [feedbackText, setFeedbackText] = useState("");
  const [feedbackStatus, setFeedbackStatus] = useState("");
  const [error, setError] = useState("");

  const birthComplete = useMemo(() => hasCompleteBirthInfo(birthInfo), [birthInfo]);

  const upsertHistory = useCallback((item: PredictionHistoryItem) => {
    setHistory((prev) => {
      const next = prev.filter((row) => row.predictionId !== item.predictionId);
      return [item, ...next].slice(0, 10);
    });
  }, []);

  const restoreSessionHistory = useCallback(
    (payload: Record<string, unknown>) => {
      const session = readRecord(payload, "session");
      const turns = readArray(payload, "turns").length > 0 ? readArray(payload, "turns") : readArray(session, "agent_turns");
      turns.forEach((turn) => {
        const predictionId = extractPredictionId(turn);
        if (!predictionId) return;
        const safeOutput = readRecord(turn, "safe_output");
        upsertHistory({
          predictionId,
          contractId: extractContractId(turn),
          conclusionTitle: historyTitle(safeOutputText(safeOutput) || readString(turn, ["user_message"], "历史预测")),
          feedbackStatus: "unknown",
          ruleDrift: false,
          createdAt: readString(turn, ["created_at"], nowIso()),
        });
      });
    },
    [upsertHistory],
  );

  const fetchAgentSession = useCallback(
    async (candidateSessionId: string): Promise<boolean> => {
      const { data, ok } = await requestJson<unknown>(
        `/api/v18.1/agent/sessions/${encodeURIComponent(candidateSessionId)}`,
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
      "/api/v18.1/agent/sessions",
      jsonPostInit(
        {
          surface: "oracle_user_agent_ui",
          user_locale: "zh-CN",
          created_by: "oracle_frontend",
        },
        noStoreInit(),
      ),
    );
    if (!ok) throw new Error(apiFailureMessage(data, requestError, "Agent session 创建失败。"));
    const payload = unwrapEnvelope(data);
    const resolvedId = extractSessionId(payload);
    if (!resolvedId) throw new Error("Agent session 响应缺少 session_id。");
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
        if (!cancelled) setError(err instanceof Error ? err.message : "Agent session 初始化失败。");
      } finally {
        if (!cancelled) setLoadingSession(false);
      }
    }
    void boot();
    return () => {
      cancelled = true;
    };
  }, [createAgentSession, fetchAgentSession]);

  const loadReplay = useCallback(async (predictionId: string): Promise<Record<string, unknown>> => {
    const { data, ok, error: requestError } = await requestJson<unknown>(
      `/api/v18.1/predictions/${encodeURIComponent(predictionId)}/replay`,
      noStoreInit(),
    );
    if (!ok) throw new Error(apiFailureMessage(data, requestError, "Replay 加载失败。"));
    return unwrapEnvelope(data);
  }, []);

  const explainPrediction = useCallback(
    async ({
      predictionId,
      contractId,
      safeOutput,
      chartSnapshot,
    }: {
      predictionId: string;
      contractId: string;
      safeOutput: Record<string, unknown>;
      chartSnapshot: Record<string, unknown>;
    }): Promise<OraclePrediction> => {
      const { data, ok, error: requestError } = await requestJson<unknown>(
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
      if (!ok) throw new Error(apiFailureMessage(data, requestError, "系统解释被输出校验拦截。"));
      const explanationPayload = unwrapEnvelope(data);
      const explanationResponse =
        readRecord(explanationPayload, "explanation_response").safe_output || explanationPayload.explanation_response
          ? readRecord(explanationPayload, "explanation_response")
          : explanationPayload;
      const verifier = readRecord(explanationResponse, "verifier");
      if (readBool(verifier, "ok", true) === false || readBool(explanationResponse, "verified", true) === false) {
        throw new Error("系统解释未通过输出校验，前端拒绝展示。");
      }

      let replayPayload: Record<string, unknown> = {};
      try {
        replayPayload = await loadReplay(predictionId);
      } catch {
        replayPayload = {};
      }

      return buildPrediction({
        predictionId,
        contractId,
        turnSafeOutput: safeOutput,
        explanationPayload,
        replayPayload,
        chartSnapshot,
      });
    },
    [loadReplay],
  );

  const submitQuestion = useCallback(async () => {
    const userQuestion = question.trim();
    if (!userQuestion || !sessionId || submitting) return;
    setSubmitting(true);
    setError("");
    setFeedbackStatus("");
    setClarificationQuestion("");
    setMissingFields([]);

    try {
      const birthPayload = providedBirthPayload(birthInfo);
      const chartSnapshot = buildChartSnapshot(birthInfo);
      const { data, ok, error: requestError } = await requestJson<unknown>(
        `/api/v18.1/agent/sessions/${encodeURIComponent(sessionId)}/turns`,
        jsonPostInit(
          {
            request_id: stableId("oracle_agent_turn"),
            agent_session_id: sessionId,
            user_message: userQuestion,
            user_query: userQuestion,
            plugin_claims: [{ plugin_id: "plugin.agent", claim_id: "oracle_user_agent_runtime" }],
            normalized_intent: {
              source: "oracle_user_agent_ui",
              topic: "bazi_prediction",
              language: "zh-CN",
              requires_chart_snapshot: true,
            },
            missing_info_policy: "clarify_before_predict",
            birth_payload: birthPayload,
            birth_info: birthPayload,
            chart_snapshot: chartSnapshot,
            allowed_output_scope: ["clarification_question", "prediction_safe_output"],
            surface: "ordinary_oracle_agent",
          },
          noStoreInit(),
        ),
      );

      if (!ok) throw new Error(apiFailureMessage(data, requestError, "Agent turn 提交失败。"));
      const payload = unwrapEnvelope(data);
      const turn = readRecord(payload, "turn");
      const safeOutput = Object.keys(readRecord(turn, "safe_output")).length > 0 ? readRecord(turn, "safe_output") : readRecord(payload, "safe_output");
      const returnedMissingFields =
        readArray(turn, "missing_fields").length > 0
          ? readArray(turn, "missing_fields").map((item) => String(item || "").trim()).filter(Boolean)
          : readArray(payload, "missing_fields").map((item) => String(item || "").trim()).filter(Boolean);
      const predictionId = extractPredictionId(payload, turn, safeOutput);
      const contractId = extractContractId(payload, turn, safeOutput);
      const isClarification =
        readString(safeOutput, ["type"]) === "clarification_question" ||
        readBool(safeOutput, "is_prediction", true) === false ||
        returnedMissingFields.length > 0 ||
        !predictionId;

      if (isClarification) {
        setCurrentPrediction(null);
        setMissingFields(returnedMissingFields);
        setClarificationQuestion(
          safeOutputText(safeOutput) ||
            `还需要补充：${returnedMissingFields.length > 0 ? returnedMissingFields.join("、") : "出生年、月、日、时与性别"}。补齐前不会生成预测。`,
        );
        return;
      }

      const prediction = await explainPrediction({ predictionId, contractId, safeOutput, chartSnapshot });
      setCurrentPrediction(prediction);
      setFeedbackText("");
      upsertHistory({
        predictionId: prediction.predictionId,
        contractId: prediction.contractId,
        conclusionTitle: historyTitle(prediction.conclusionTitle),
        feedbackStatus: "pending",
        ruleDrift: prediction.ruleDrift,
        createdAt: prediction.createdAt,
        replay: prediction.replay,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Agent 处理失败。");
    } finally {
      setSubmitting(false);
    }
  }, [birthInfo, explainPrediction, question, sessionId, submitting, upsertHistory]);

  const submitFeedback = useCallback(
    async (feedbackType: FeedbackType) => {
      if (!currentPrediction?.predictionId) return;
      setError("");
      setFeedbackStatus("");
      try {
        const { data, ok, error: requestError } = await requestJson<unknown>(
          `/api/v18.1/predictions/${encodeURIComponent(currentPrediction.predictionId)}/feedback`,
          jsonPostInit(
            {
              request_id: stableId("oracle_feedback"),
              prediction_id: currentPrediction.predictionId,
              conclusion_ref: currentPrediction.conclusionRef,
              conclusion_id: currentPrediction.conclusionRef,
              feedback_type: feedbackType,
              user_comment: feedbackText.trim(),
              observed_event: {
                source: "oracle_user_agent_ui",
                label: FEEDBACK_LABELS[feedbackType],
                note: feedbackText.trim(),
              },
              observed_at: nowIso(),
            },
            noStoreInit(),
          ),
        );
        if (!ok) throw new Error(apiFailureMessage(data, requestError, "Feedback 提交失败。"));
        const payload = unwrapEnvelope(data);
        const learningSignal = readRecord(payload, "learning_signal");
        const signalId = readString(learningSignal, ["signal_id", "id"], "created");
        setFeedbackStatus(`已记录，这会进入学习信号，但不会直接修改规则。learning_signal=${signalId}`);
        upsertHistory({
          predictionId: currentPrediction.predictionId,
          contractId: currentPrediction.contractId,
          conclusionTitle: historyTitle(currentPrediction.conclusionTitle),
          feedbackStatus: feedbackType,
          ruleDrift: currentPrediction.ruleDrift,
          createdAt: currentPrediction.createdAt,
          replay: currentPrediction.replay,
        });
      } catch (err) {
        setError(err instanceof Error ? err.message : "Feedback 提交失败。");
      }
    },
    [currentPrediction, feedbackText, upsertHistory],
  );

  const replayHistoryItem = useCallback(
    async (item: PredictionHistoryItem) => {
      setError("");
      try {
        const replay = await loadReplay(item.predictionId);
        setHistory((prev) =>
          prev.map((row) =>
            row.predictionId === item.predictionId
              ? {
                  ...row,
                  replay,
                  ruleDrift: readBool(replay, "rule_drift", row.ruleDrift),
                }
              : row,
          ),
        );
      } catch (err) {
        setError(err instanceof Error ? err.message : "Replay 加载失败。");
      }
    },
    [loadReplay],
  );

  return (
    <main className="min-h-screen overflow-hidden bg-[#080c11] text-slate-100">
      <div className="pointer-events-none fixed inset-0">
        <div className="absolute left-[-14%] top-[-20%] h-[34rem] w-[34rem] rounded-full bg-cyan-400/20 blur-3xl" />
        <div className="absolute bottom-[-20%] right-[-10%] h-[38rem] w-[38rem] rounded-full bg-amber-300/12 blur-3xl" />
        <div className="absolute inset-0 bg-[linear-gradient(135deg,rgba(255,255,255,0.07),transparent_32%),radial-gradient(circle_at_top_right,rgba(34,211,238,0.12),transparent_32%)]" />
      </div>

      <section className="relative mx-auto w-full max-w-7xl px-4 py-5 sm:px-6 lg:px-8">
        <OracleAgentPanel
          displayName={displayName}
          roleLabel={roleLabel}
          loading={loadingSession || submitting}
          sessionReady={Boolean(sessionId)}
          question={question}
          onQuestionChange={setQuestion}
          onSubmit={() => void submitQuestion()}
          onLogout={onLogout}
        />

        {error ? (
          <div className="mt-5 flex items-start gap-3 rounded-[1.5rem] border border-rose-300/20 bg-rose-500/10 p-4 text-sm text-rose-100">
            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
            <span>{error}</span>
          </div>
        ) : null}

        <BirthInfoClarificationForm
          birthInfo={birthInfo}
          onChange={setBirthInfo}
          clarificationQuestion={clarificationQuestion}
          missingFields={missingFields}
          birthComplete={birthComplete}
        />

        {currentPrediction ? (
          <section className="mt-6 grid gap-5 lg:grid-cols-[minmax(0,1fr)_24rem]">
            <div className="space-y-5">
              <PredictionSummaryCard prediction={currentPrediction} isAdmin={isAdmin} />
              <PredictionProvenanceCard prediction={currentPrediction} isAdmin={isAdmin} />
              <PredictionFeedbackPanel
                prediction={currentPrediction}
                feedbackText={feedbackText}
                feedbackStatus={feedbackStatus}
                onFeedbackTextChange={setFeedbackText}
                onSubmitFeedback={(feedbackType) => void submitFeedback(feedbackType)}
              />
              <VerifiedExplanationCard prediction={currentPrediction} />
            </div>
            <div className="space-y-5">
              <EvidenceTracePanel evidenceTrace={currentPrediction.evidenceTrace} />
              <UncertaintyPanel prediction={currentPrediction} />
              {isAdmin ? <AdminDebugPanel prediction={currentPrediction} /> : null}
            </div>
          </section>
        ) : (
          <section className="mt-6 rounded-[2rem] border border-white/10 bg-white/[0.05] p-6 text-slate-300 shadow-2xl shadow-black/25 backdrop-blur">
            <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
              <div>
                <p className="text-sm uppercase tracking-[0.2em] text-cyan-200">等待系统裁决</p>
                <h2 className="mt-2 text-2xl font-semibold text-white">先提出问题，系统会判断是否需要追问。</h2>
                <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-400">
                  缺出生信息时不会生成 Prediction Contract，也不会展示预测结论。这是为了避免前端或 LLM 自行补判。
                </p>
              </div>
              <ShieldCheck className="h-12 w-12 text-cyan-200/80" />
            </div>
          </section>
        )}

        <section className="mt-6 grid gap-5 lg:grid-cols-[minmax(0,1fr)_24rem]">
          <div className="space-y-5">
            <ChartSnapshotPanel prediction={currentPrediction} birthInfo={birthInfo} />
            <div className="grid gap-4 md:grid-cols-3">
              <TopicAnalysisCard title="专题分析" source={currentPrediction ? "contract" : "generated"} prediction={currentPrediction} />
              <TopicAnalysisCard title="财富路径推演" source={currentPrediction?.evidenceTrace.length ? "evidence" : "generated"} prediction={currentPrediction} />
              <TopicAnalysisCard title="十年流年参考" source={currentPrediction ? "contract" : "generated"} prediction={currentPrediction} />
            </div>
          </div>
          <PredictionHistoryPanel history={history} onReplay={(item) => void replayHistoryItem(item)} />
        </section>
      </section>
    </main>
  );
}

function OracleAgentPanel({
  displayName,
  roleLabel,
  loading,
  sessionReady,
  question,
  onQuestionChange,
  onSubmit,
  onLogout,
}: {
  displayName?: string;
  roleLabel?: string;
  loading: boolean;
  sessionReady: boolean;
  question: string;
  onQuestionChange: (value: string) => void;
  onSubmit: () => void;
  onLogout?: () => void | Promise<void>;
}): ReactNode {
  return (
    <section className="rounded-[2.25rem] border border-white/10 bg-white/[0.07] p-5 shadow-2xl shadow-black/30 backdrop-blur md:p-7">
      <div className="mb-6 flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
        <div>
          <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-cyan-200/20 bg-cyan-200/10 px-3 py-1 text-xs text-cyan-100">
            <Bot className="h-3.5 w-3.5" />
            Oracle Agent / Contract-first
          </div>
          <h1 className="text-3xl font-semibold tracking-tight text-white md:text-5xl">你想了解什么？</h1>
          <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-300 md:text-base">
            我会根据命盘、规则证据和历史反馈，给出可追溯的判断。
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2 text-sm">
          <span className="rounded-full border border-white/10 bg-black/20 px-3 py-2 text-slate-300">
            {displayName || "User"} {roleLabel ? `· ${roleLabel}` : ""}
          </span>
          <span className={`rounded-full border px-3 py-2 text-xs ${sessionReady ? "border-emerald-300/20 bg-emerald-300/10 text-emerald-100" : "border-amber-300/20 bg-amber-300/10 text-amber-100"}`}>
            {loading ? "connecting" : sessionReady ? "agent ready" : "session pending"}
          </span>
          {onLogout ? (
            <button type="button" onClick={() => void onLogout()} className="rounded-full border border-white/10 bg-black/20 px-3 py-2 text-slate-300 transition hover:bg-black/30">
              退出
            </button>
          ) : null}
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_10rem]">
        <textarea
          value={question}
          onChange={(event) => onQuestionChange(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter" && (event.metaKey || event.ctrlKey)) onSubmit();
          }}
          placeholder="例如：我未来两年财运怎么样？适合创业还是稳定工作？"
          className="min-h-36 resize-none rounded-[1.75rem] border border-white/10 bg-[#070b10]/70 px-5 py-4 text-base leading-7 text-slate-100 outline-none transition placeholder:text-slate-500 focus:border-cyan-300/60"
        />
        <button
          type="button"
          onClick={onSubmit}
          disabled={!question.trim() || loading || !sessionReady}
          className="inline-flex min-h-16 items-center justify-center gap-2 rounded-[1.75rem] bg-cyan-300 px-5 py-4 font-semibold text-slate-950 transition hover:bg-cyan-200 disabled:cursor-not-allowed disabled:bg-slate-600 disabled:text-slate-300 lg:min-h-full"
        >
          {loading ? <Loader2 className="h-5 w-5 animate-spin" /> : <Send className="h-5 w-5" />}
          开始分析
        </button>
      </div>
    </section>
  );
}

function BirthInfoClarificationForm({
  birthInfo,
  onChange,
  clarificationQuestion,
  missingFields,
  birthComplete,
}: {
  birthInfo: BirthInfo;
  onChange: (value: BirthInfo) => void;
  clarificationQuestion: string;
  missingFields: string[];
  birthComplete: boolean;
}): ReactNode {
  return (
    <section className="mt-5 rounded-[2rem] border border-white/10 bg-[#101722]/85 p-5 shadow-xl shadow-black/20 backdrop-blur">
      <div className="mb-4 flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
        <div>
          <h2 className="flex items-center gap-2 text-lg font-semibold text-white">
            <MessageSquareText className="h-5 w-5 text-amber-200" />
            出生信息追问
          </h2>
          <p className="mt-1 text-sm text-slate-400">
            {clarificationQuestion || "如果信息不足，Agent 会在这里追问；补齐前不会进入预测结果。"}
          </p>
        </div>
        <span className={`rounded-full border px-3 py-1.5 text-xs ${birthComplete ? "border-emerald-300/20 bg-emerald-300/10 text-emerald-100" : "border-amber-300/20 bg-amber-300/10 text-amber-100"}`}>
          {birthComplete ? "排盘信息完整" : missingFields.length ? `缺少 ${missingFields.join(" / ")}` : "可先提问，再补信息"}
        </span>
      </div>
      <div className="grid gap-3 md:grid-cols-5">
        <BirthInput label="年" value={birthInfo.year} onChange={(year) => onChange({ ...birthInfo, year })} />
        <BirthInput label="月" value={birthInfo.month} onChange={(month) => onChange({ ...birthInfo, month })} />
        <BirthInput label="日" value={birthInfo.day} onChange={(day) => onChange({ ...birthInfo, day })} />
        <BirthInput label="时" value={birthInfo.hour} onChange={(hour) => onChange({ ...birthInfo, hour })} />
        <label className="block">
          <span className="mb-1 block text-xs text-slate-400">性别</span>
          <select
            value={birthInfo.gender}
            onChange={(event) => onChange({ ...birthInfo, gender: event.target.value as BirthGender })}
            className="h-11 w-full rounded-2xl border border-white/10 bg-black/30 px-3 text-sm text-slate-100 outline-none transition focus:border-cyan-300/50"
          >
            <option value="unknown">未填</option>
            <option value="male">男</option>
            <option value="female">女</option>
          </select>
        </label>
      </div>
    </section>
  );
}

function BirthInput({ label, value, onChange }: { label: string; value: string; onChange: (value: string) => void }): ReactNode {
  return (
    <label className="block">
      <span className="mb-1 block text-xs text-slate-400">{label}</span>
      <input
        value={value}
        inputMode="numeric"
        onChange={(event) => onChange(event.target.value.replace(/[^\d]/g, ""))}
        placeholder={label === "年" ? "1990" : label === "时" ? "09" : "01"}
        className="h-11 w-full rounded-2xl border border-white/10 bg-black/30 px-3 text-sm text-slate-100 outline-none transition placeholder:text-slate-500 focus:border-cyan-300/50"
      />
    </label>
  );
}

function PredictionSummaryCard({ prediction, isAdmin }: { prediction: OraclePrediction; isAdmin: boolean }): ReactNode {
  const confidencePercent = prediction.confidence === null ? null : Math.round(prediction.confidence * 100);
  return (
    <section className="rounded-[2rem] border border-cyan-200/20 bg-cyan-200/[0.08] p-6 shadow-2xl shadow-cyan-950/20">
      <TrustBadgeBar prediction={prediction} />
      <h2 className="text-2xl font-semibold leading-tight text-white md:text-3xl">{prediction.conclusionTitle}</h2>
      <p className="mt-3 text-sm leading-7 text-slate-300">{prediction.summary}</p>
      <div className="mt-5 grid gap-4 md:grid-cols-2">
        <div className="rounded-2xl border border-white/10 bg-black/20 p-4">
          <div className="mb-2 flex items-center justify-between text-sm">
            <span className="text-slate-300">置信度</span>
            <span className="font-semibold text-white">{confidencePercent === null ? "未公开" : `${confidencePercent}%`}</span>
          </div>
          <div className="h-2 overflow-hidden rounded-full bg-white/10">
            <div className="h-full rounded-full bg-cyan-300 transition-all" style={{ width: `${confidencePercent ?? 18}%` }} />
          </div>
        </div>
        <UncertaintyCallout prediction={prediction} compact />
      </div>
      {isAdmin ? (
        <div className="mt-4 grid gap-2 text-xs text-slate-400 md:grid-cols-2">
          <DebugChip label="prediction_id" value={prediction.predictionId} />
          <DebugChip label="contract_id" value={prediction.contractId} />
        </div>
      ) : null}
    </section>
  );
}

function TrustBadgeBar({ prediction }: { prediction: OraclePrediction }): ReactNode {
  const badges = [
    { label: "已通过规则裁决", ok: true },
    { label: "已绑定证据链", ok: prediction.evidenceTrace.length > 0 },
    { label: "已通过输出校验", ok: prediction.verifierStatus !== "blocked" },
    { label: "已写入预测账本", ok: prediction.ledgerStatus === "written" },
    { label: "可反馈学习", ok: Boolean(prediction.predictionId) },
  ];
  return (
    <div className="mb-5 flex flex-wrap gap-2">
      {badges.map((badge) => (
        <span
          key={badge.label}
          className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-xs ${
            badge.ok
              ? "border-emerald-300/20 bg-emerald-300/10 text-emerald-100"
              : "border-slate-400/20 bg-slate-500/10 text-slate-300"
          }`}
        >
          <CheckIcon ok={badge.ok} />
          {badge.label}
        </span>
      ))}
    </div>
  );
}

function CheckIcon({ ok }: { ok: boolean }): ReactNode {
  return ok ? <BadgeCheck className="h-3.5 w-3.5" /> : <AlertTriangle className="h-3.5 w-3.5" />;
}

function PredictionProvenanceCard({ prediction, isAdmin }: { prediction: OraclePrediction; isAdmin: boolean }): ReactNode {
  const id = (value: string) => (isAdmin ? value || "n/a" : shortHash(value));
  return (
    <section className="rounded-[2rem] border border-white/10 bg-white/[0.06] p-5 shadow-2xl shadow-black/20 backdrop-blur">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="flex items-center gap-2 text-lg font-semibold text-white">
            <ShieldCheck className="h-5 w-5 text-cyan-200" />
            预测来源
          </h2>
          <p className="mt-1 text-sm text-slate-400">这条结果已绑定 Contract、Verifier 与 Ledger，可追踪、可反馈、可回放。</p>
        </div>
        <span className="rounded-full border border-cyan-200/20 bg-cyan-200/10 px-3 py-1 text-xs text-cyan-100">
          Provenance
        </span>
      </div>
      <div className="grid gap-3 md:grid-cols-3">
        <ProvenanceLine label="prediction_id" value={id(prediction.predictionId)} />
        <ProvenanceLine label="contract_id" value={id(prediction.contractId)} />
        <ProvenanceLine label="contract_hash" value={id(prediction.contractHash)} />
        <ProvenanceLine label="verifier_status" value={prediction.verifierStatus || "verified"} />
        <ProvenanceLine label="ledger_status" value={prediction.ledgerStatus} />
        <ProvenanceLine label="generated_at" value={new Date(prediction.createdAt).toLocaleString()} />
      </div>
    </section>
  );
}

function ProvenanceLine({ label, value }: { label: string; value: string }): ReactNode {
  return (
    <div className="rounded-2xl border border-white/10 bg-black/20 p-3">
      <div className="text-[11px] uppercase tracking-[0.16em] text-slate-500">{label}</div>
      <div className="mt-1 break-all font-mono text-xs text-slate-200">{value || "n/a"}</div>
    </div>
  );
}

function VerifiedExplanationCard({ prediction }: { prediction: OraclePrediction }): ReactNode {
  return (
    <section className="rounded-[2rem] border border-white/10 bg-white/[0.06] p-6 shadow-2xl shadow-black/20 backdrop-blur">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="flex items-center gap-2 text-xl font-semibold text-white">
            <BadgeCheck className="h-5 w-5 text-emerald-200" />
            系统解释（基于规则裁决）
          </h2>
          <p className="mt-1 text-sm text-slate-400">这不是 raw LLM output；仅展示通过输出校验后的解释。</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <span className="rounded-full border border-emerald-300/20 bg-emerald-300/10 px-3 py-1 text-xs text-emerald-100">已通过输出校验</span>
          <span className="rounded-full border border-cyan-200/20 bg-cyan-200/10 px-3 py-1 text-xs text-cyan-100">解释层不参与命理裁决</span>
          <span className="rounded-full border border-cyan-200/20 bg-cyan-200/10 px-3 py-1 text-xs text-cyan-100">解释内容来自已验证 Contract</span>
          <span className="rounded-full border border-white/10 bg-black/20 px-3 py-1 text-xs text-slate-300">model {prediction.modelVersion}</span>
          <span className="rounded-full border border-white/10 bg-black/20 px-3 py-1 text-xs text-slate-300">engine {prediction.engineVersion}</span>
        </div>
      </div>
      <p className="whitespace-pre-wrap text-sm leading-7 text-slate-200">{prediction.explanationText}</p>
    </section>
  );
}

function EvidenceTracePanel({ evidenceTrace }: { evidenceTrace: EvidenceItem[] }): ReactNode {
  const preview = evidenceTrace.slice(0, 2);
  const rest = evidenceTrace.slice(2);
  return (
    <section className="rounded-[2rem] border border-white/10 bg-white/[0.06] p-5 shadow-2xl shadow-black/20 backdrop-blur">
      <div className="mb-4 flex items-center justify-between gap-3 text-white">
        <h2 className="flex items-center gap-2 text-lg font-semibold">
          <ClipboardCheck className="h-5 w-5 text-cyan-200" />
          判断依据
        </h2>
        <span className="rounded-full border border-cyan-200/20 bg-cyan-200/10 px-3 py-1 text-xs text-cyan-100">核心证据预览</span>
      </div>
      <div className="space-y-3">
        {evidenceTrace.length === 0 ? (
          <p className="rounded-2xl border border-dashed border-white/10 bg-black/20 p-4 text-sm text-slate-400">
            当前 response 未暴露 evidence_trace。正式预测仍以 Contract / Ledger 为事实源。
          </p>
        ) : (
          preview.map((item, index) => <EvidencePreview key={`${item.ruleId}-${item.version}-preview-${index}`} item={item} />)
        )}
      </div>
      {rest.length > 0 ? (
        <details className="mt-4 rounded-2xl border border-white/10 bg-black/20 p-4 text-sm text-slate-300">
          <summary className="cursor-pointer text-slate-100">查看其余 {rest.length} 条规则证据</summary>
          <div className="mt-3 space-y-3">
            {rest.map((item, index) => (
              <EvidencePreview key={`${item.ruleId}-${item.version}-rest-${index}`} item={item} compact />
            ))}
          </div>
        </details>
      ) : null}
    </section>
  );
}

function EvidencePreview({ item, compact = false }: { item: EvidenceItem; compact?: boolean }): ReactNode {
  return (
    <article className={`rounded-2xl border border-white/10 bg-black/20 ${compact ? "p-3" : "p-4"}`}>
      <div className="mb-3 flex flex-wrap items-center gap-2">
        <span className="rounded-full bg-cyan-300/10 px-3 py-1 text-xs text-cyan-100">规则证据</span>
        <span className="font-mono text-xs text-slate-400">{item.ruleId || "unknown_rule"}</span>
      </div>
      <dl className="grid gap-3 text-sm">
        <EvidenceLine label="effect" value={compactJson(item.effect)} />
        <EvidenceLine label="命中事实" value={item.matchedFacts.length ? compactJson(item.matchedFacts) : "n/a"} />
        <EvidenceLine label="confidence_delta" value={item.confidenceDelta === null ? "n/a" : `${Math.round(item.confidenceDelta * 100)}%`} />
        {!compact ? <EvidenceLine label="version / hash" value={`${item.version || "n/a"} / ${shortHash(item.contentHash)}`} /> : null}
      </dl>
    </article>
  );
}

function EvidenceLine({ label, value }: { label: string; value: string }): ReactNode {
  return (
    <div className="grid gap-1">
      <dt className="text-xs uppercase tracking-[0.18em] text-slate-500">{label}</dt>
      <dd className="break-words text-slate-200">{value}</dd>
    </div>
  );
}

function UncertaintyPanel({ prediction }: { prediction: OraclePrediction }): ReactNode {
  return <UncertaintyCallout prediction={prediction} />;
}

function UncertaintyCallout({ prediction, compact = false }: { prediction: OraclePrediction; compact?: boolean }): ReactNode {
  return (
    <section className={`rounded-[2rem] border border-amber-300/20 bg-amber-300/[0.08] ${compact ? "p-4" : "p-5 shadow-2xl shadow-black/20"}`}>
      <div className="mb-2 flex flex-wrap items-center gap-2">
        <AlertTriangle className="h-5 w-5" />
        <h2 className="text-lg font-semibold text-amber-50">不确定性来源</h2>
        <span className="rounded-full border border-amber-100/20 bg-black/20 px-3 py-1 text-xs uppercase tracking-[0.12em] text-amber-50">
          {prediction.uncertaintyLevel}
        </span>
      </div>
      <p className="mt-2 text-sm leading-6 text-amber-50/90">{prediction.uncertaintyText}</p>
      <p className="mt-3 text-xs font-semibold text-amber-100">本判断不是绝对结论，以下因素会影响结果。</p>
      <InfoList title="影响因素" items={prediction.sensitiveFactors} />
      {!compact ? <InfoList title="缺失假设" items={prediction.missingAssumptions} /> : null}
      <InfoList title="来源" items={prediction.uncertaintyReasons} />
    </section>
  );
}

function InfoList({ title, items }: { title: string; items: string[] }): ReactNode {
  return (
    <div className="mt-4">
      <p className="mb-2 text-xs font-semibold uppercase tracking-[0.16em] text-amber-100/70">{title}</p>
      <div className="flex flex-wrap gap-2">
        {items.map((item) => (
          <span key={item} className="rounded-full border border-amber-100/10 bg-black/20 px-3 py-1 text-xs text-amber-50/90">
            {item}
          </span>
        ))}
      </div>
    </div>
  );
}

function PredictionFeedbackPanel({
  prediction,
  feedbackText,
  feedbackStatus,
  onFeedbackTextChange,
  onSubmitFeedback,
}: {
  prediction: OraclePrediction;
  feedbackText: string;
  feedbackStatus: string;
  onFeedbackTextChange: (value: string) => void;
  onSubmitFeedback: (feedbackType: FeedbackType) => void;
}): ReactNode {
  return (
    <section id="prediction-feedback-panel" className="rounded-[2rem] border border-white/10 bg-white/[0.06] p-5 shadow-2xl shadow-black/20 backdrop-blur">
      <h2 className="flex items-center gap-2 text-lg font-semibold text-white">
        <Sparkles className="h-5 w-5 text-amber-200" />
        用户反馈
      </h2>
      <p className="mt-1 text-sm text-slate-400">
        反馈会绑定 prediction_id{prediction.conclusionRef ? " + conclusion_ref" : ""}，只生成 learning_signal，不会直接修改 active rule。
      </p>
      <div className="mt-4 rounded-2xl border border-emerald-300/20 bg-emerald-300/10 p-4 text-sm leading-6 text-emerald-50">
        你的反馈会进入学习信号，用于改进规则评分和候选规则建议，但不会直接修改当前规则。
      </div>
      <textarea
        value={feedbackText}
        onChange={(event) => onFeedbackTextChange(event.target.value)}
        placeholder="补充实际情况，例如：2024年确实换工作/收入上涨/投资亏损"
        className="mt-4 min-h-24 w-full resize-none rounded-2xl border border-white/10 bg-black/25 px-4 py-3 text-sm leading-6 text-slate-100 outline-none placeholder:text-slate-500 focus:border-cyan-300/50"
      />
      <div className="mt-3 flex flex-wrap gap-2">
        {(Object.keys(FEEDBACK_LABELS) as FeedbackType[]).map((type) => (
          <button
            key={type}
            type="button"
            disabled={!prediction.predictionId}
            title={FEEDBACK_HINTS[type]}
            onClick={() => onSubmitFeedback(type)}
            className="rounded-full border border-white/10 bg-black/25 px-4 py-2 text-sm text-slate-100 transition hover:bg-white/10 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {FEEDBACK_LABELS[type]}
          </button>
        ))}
      </div>
      {feedbackStatus ? (
        <div className="mt-4 rounded-2xl border border-emerald-300/20 bg-emerald-300/10 p-3 text-sm text-emerald-100">
          {feedbackStatus}
        </div>
      ) : null}
    </section>
  );
}

function ChartSnapshotPanel({ prediction, birthInfo }: { prediction: OraclePrediction | null; birthInfo: BirthInfo }): ReactNode {
  const chartSnapshot = prediction?.chartSnapshot || buildChartSnapshot(birthInfo);
  return (
    <details className="rounded-[2rem] border border-white/10 bg-white/[0.05] p-5 shadow-xl shadow-black/20 backdrop-blur">
      <summary className="flex cursor-pointer list-none items-center justify-between gap-3 text-white">
        <span className="flex items-center gap-2 text-lg font-semibold">
          <Layers3 className="h-5 w-5 text-cyan-200" />
          命盘结构 / 专业视图
        </span>
        <span className="rounded-full border border-white/10 bg-black/20 px-3 py-1 text-xs text-slate-300">默认折叠</span>
      </summary>
      <p className="mt-3 text-sm text-slate-400">以下为系统裁决使用的结构化命盘快照。命局六柱、体用中和、格局、十年流年等专业内容默认作为 evidence detail 展示。</p>
      <div className="mt-4 grid gap-3 md:grid-cols-2">
        <ProfessionalBlock title="命局六柱" value={compactJson(readRecord(chartSnapshot, "four_pillars"))} />
        <ProfessionalBlock title="体用中和" value="等待 Contract / evidence 暴露结构化字段" />
        <ProfessionalBlock title="格局" value="作为规则证据 detail 展开，不作为首屏结论" />
        <ProfessionalBlock title="十年流年" value="作为专题分析参考，不绕过 Prediction Contract" />
      </div>
      <pre className="mt-4 max-h-72 overflow-auto rounded-2xl bg-black/30 p-4 text-xs leading-5 text-slate-400">{compactJson(chartSnapshot)}</pre>
    </details>
  );
}

function ProfessionalBlock({ title, value }: { title: string; value: string }): ReactNode {
  return (
    <div className="rounded-2xl border border-white/10 bg-black/20 p-4">
      <p className="mb-2 text-sm font-semibold text-slate-100">{title}</p>
      <p className="break-words text-xs leading-5 text-slate-400">{value}</p>
    </div>
  );
}

function TopicAnalysisCard({
  title,
  source,
  prediction,
}: {
  title: string;
  source: "contract" | "evidence" | "generated";
  prediction: OraclePrediction | null;
}): ReactNode {
  const confidence = prediction?.confidence === null || prediction?.confidence === undefined ? "未生成" : `${Math.round(prediction.confidence * 100)}%`;
  const generated = Boolean(prediction);
  return (
    <article className="rounded-[1.5rem] border border-white/10 bg-white/[0.05] p-4 shadow-xl shadow-black/20">
      <div className="mb-3 flex items-center justify-between gap-2">
        <h3 className="font-semibold text-white">{title}</h3>
        <span className={`rounded-full px-2.5 py-1 text-[11px] ${generated ? "bg-emerald-300/10 text-emerald-100" : "bg-slate-500/15 text-slate-400"}`}>
          {generated ? "已生成" : "未生成"}
        </span>
      </div>
      <div className="space-y-2 text-sm text-slate-300">
        <p>source: {source}</p>
        <p>confidence: {confidence}</p>
        <p>uncertainty: {prediction?.uncertaintyLevel || "unknown"}</p>
      </div>
      <button
        type="button"
        onClick={() => document.getElementById("prediction-feedback-panel")?.scrollIntoView({ behavior: "smooth", block: "center" })}
        className="mt-4 inline-flex items-center gap-2 rounded-full border border-white/10 bg-black/20 px-3 py-1.5 text-xs text-cyan-100 transition hover:bg-white/10"
      >
        反馈入口
        <ChevronRight className="h-3.5 w-3.5" />
      </button>
    </article>
  );
}

function PredictionHistoryPanel({
  history,
  onReplay,
}: {
  history: PredictionHistoryItem[];
  onReplay: (item: PredictionHistoryItem) => void;
}): ReactNode {
  return (
    <section className="rounded-[2rem] border border-white/10 bg-white/[0.06] p-5 shadow-2xl shadow-black/20 backdrop-blur">
      <h2 className="mb-3 flex items-center gap-2 text-lg font-semibold text-white">
        <History className="h-5 w-5 text-cyan-200" />
        Prediction History
      </h2>
      {history.length === 0 ? (
        <p className="rounded-2xl border border-dashed border-white/10 bg-black/20 p-4 text-sm text-slate-400">完成预测后，这里会显示最近 prediction 与 replay。</p>
      ) : (
        <div className="space-y-3">
          {history.map((item) => (
            <article key={item.predictionId} className="rounded-2xl border border-white/10 bg-black/20 p-4">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="text-sm font-semibold text-slate-100">{item.conclusionTitle}</p>
                  <p className="mt-1 text-xs text-slate-500">{new Date(item.createdAt).toLocaleString()}</p>
                </div>
                <span className={`rounded-full px-2.5 py-1 text-[11px] ${item.ruleDrift ? "bg-amber-300/10 text-amber-100" : "bg-emerald-300/10 text-emerald-100"}`}>
                  {item.ruleDrift ? "rule_drift" : "no drift"}
                </span>
              </div>
              <p className="mt-2 text-xs text-slate-400">feedback: {item.feedbackStatus}</p>
              <button type="button" onClick={() => onReplay(item)} className="mt-3 rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-xs text-cyan-100 transition hover:bg-white/10">
                查看回放 / 查看当时证据
              </button>
              {item.replay ? (
                <details className="mt-3 rounded-xl bg-black/30 p-3 text-xs text-slate-300">
                  <summary className="cursor-pointer text-slate-100">Replay snapshot</summary>
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
  );
}

function AdminDebugPanel({ prediction }: { prediction: OraclePrediction }): ReactNode {
  const evidenceCount = prediction.evidenceTrace.length;
  return (
    <section className="rounded-[2rem] border border-fuchsia-300/20 bg-fuchsia-300/[0.07] p-5 shadow-2xl shadow-black/20">
      <h2 className="mb-3 flex items-center gap-2 text-lg font-semibold text-fuchsia-50">
        <Bug className="h-5 w-5" />
        Admin Debug Panel
      </h2>
      <div className="grid gap-2">
        <DebugChip label="prediction_id" value={prediction.predictionId} />
        <DebugChip label="contract_id" value={prediction.contractId} />
        <DebugChip label="ledger_id" value={prediction.ledgerId || "not loaded"} />
        <DebugChip label="contract_hash" value={prediction.contractHash || "not loaded"} />
        <DebugChip label="rule evidence count" value={String(evidenceCount)} />
        <DebugChip label="verifier status" value={prediction.verifierStatus} />
        <DebugChip label="storage backend" value={readString(prediction.replay, ["storage_backend"], "backend response not exposed")} />
        <DebugChip label="redis status" value={readString(prediction.replay, ["redis_status"], "not exposed")} />
      </div>
    </section>
  );
}

function DebugChip({ label, value }: { label: string; value: string }): ReactNode {
  return (
    <div className="rounded-2xl border border-white/10 bg-black/25 p-3">
      <div className="mb-1 flex items-center gap-2 text-[11px] uppercase tracking-[0.18em] text-slate-500">
        <Database className="h-3 w-3" />
        {label}
      </div>
      <div className="break-all font-mono text-xs text-slate-200">{value || "n/a"}</div>
    </div>
  );
}

export function V18_UserAgentConsole(props: OracleUserAgentExperienceProps): ReactNode {
  return <V18_OracleUserAgentExperience {...props} />;
}
