"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import {
  AlertTriangle,
  ArrowRight,
  BadgeCheck,
  BookOpenCheck,
  Bot,
  CheckCircle2,
  ClipboardCheck,
  Copy as CopyIcon,
  Database,
  ExternalLink,
  History,
  Loader2,
  MessageSquare,
  Play,
  RefreshCcw,
  Share2,
  ShieldCheck,
  Sparkles,
} from "lucide-react";

import { useAppLanguage } from "@/hooks/useAppLanguage";
import { APP_LANGUAGE_COOKIE, APP_LANGUAGE_STORAGE_KEY, type AppLanguage } from "@/lib/i18n";
import { jsonPostInit, noStoreInit, requestJson } from "@/lib/apiClient";

type LandingDemoExperienceProps = {
  initialMode?: "landing" | "demo";
};

type Copy = {
  navLogin: string;
  navProduct: string;
  heroEyebrow: string;
  heroTitle: string;
  heroSubtitle: string;
  primaryCta: string;
  secondaryCta: string;
  demoStepsTitle: string;
  demoStep1: string;
  demoStep2: string;
  demoStep3: string;
  demoStep4: string;
  demoStep5: string;
  trustRule: string;
  trustEvidence: string;
  trustLedger: string;
  trustReplay: string;
  diffAiTitle: string;
  diffSystemTitle: string;
  ai1: string;
  ai2: string;
  ai3: string;
  ai4: string;
  system1: string;
  system2: string;
  system3: string;
  system4: string;
  howTitle: string;
  how1: string;
  how2: string;
  how3: string;
  how4: string;
  how5: string;
  how6: string;
  how7: string;
  how8: string;
  metricsTitle: string;
  metricPredictions: string;
  metricFeedback: string;
  metricRules: string;
  metricUpdated: string;
  metricHit: string;
  metricMiss: string;
  metricLive: string;
  metricTrustHeadline: string;
  metricTrustMatchLabel: string;
  metricTrustReplayLine: string;
  metricTrustEvidenceLine: string;
  metricTrustVerifiedLine: string;
  metricTrustGrowthLine: string;
  metricTrustFallbackLine: string;
  metricCollecting: string;
  demoTitle: string;
  demoSubtitle: string;
  activeRules: string;
  questionPlaceholder: string;
  sampleQuestion: string;
  sampleChart: string;
  sampleChartReady: string;
  generate: string;
  needActiveRule: string;
  needSampleChart: string;
  conclusion: string;
  confidence: string;
  uncertainty: string;
  verifiedExplanation: string;
  explanationBoundary: string;
  evidence: string;
  feedbackTitle: string;
  feedbackCopy: string;
  feedbackHit: string;
  feedbackMiss: string;
  feedbackPartial: string;
  feedbackUnclear: string;
  replayTitle: string;
  replayCopy: string;
  replaySummary: string;
  predictionId: string;
  verified: string;
  predictionTrustSummaryTitle: string;
  predictionTrustSummaryHint: string;
  shareReplayTitle: string;
  shareReplayCopy: string;
  shareReplayButton: string;
  shareReplayCopied: string;
  shareReplayOpen: string;
  refresh: string;
};

const COPY: Record<AppLanguage, Copy> = {
  zh: {
    navLogin: "登录正式版",
    navProduct: "掐指一算",
    heroEyebrow: "Contract-first 命理智能",
    heroTitle: "不是 AI 算命，是可验证的命理决策系统",
    heroSubtitle: "每一次判断，都有证据、有账本、可回放、可被你修正。",
    primaryCta: "开始体验 Demo",
    secondaryCta: "查看它如何工作",
    demoStepsTitle: "60 秒 Demo",
    demoStep1: "输入问题",
    demoStep2: "使用示例命盘",
    demoStep3: "生成 Contract",
    demoStep4: "查看证据与解释",
    demoStep5: "反馈并回放",
    trustRule: "已通过规则裁决",
    trustEvidence: "已绑定证据链",
    trustLedger: "已写入预测账本",
    trustReplay: "可回放",
    diffAiTitle: "普通 AI",
    diffSystemTitle: "本系统",
    ai1: "生成一段话",
    ai2: "无法追溯",
    ai3: "说完就完",
    ai4: "无法复盘",
    system1: "生成 Prediction Contract",
    system2: "Evidence + Ledger 可追溯",
    system3: "可反馈 → Learning Signal",
    system4: "Replay 可回放",
    howTitle: "它如何工作",
    how1: "问题",
    how2: "补充信息",
    how3: "规则裁决",
    how4: "Contract",
    how5: "解释（已校验）",
    how6: "记录到账本",
    how7: "反馈学习",
    how8: "可回放",
    metricsTitle: "Trust Metrics",
    metricPredictions: "已记录预测",
    metricFeedback: "用户反馈",
    metricRules: "活跃规则",
    metricUpdated: "最近规则更新",
    metricHit: "匹配率",
    metricMiss: "偏差率",
    metricLive: "实时更新中",
    metricTrustHeadline: "可信度指标",
    metricTrustMatchLabel: "用户认为完全或部分符合",
    metricTrustReplayLine: "可回放",
    metricTrustEvidenceLine: "有证据链",
    metricTrustVerifiedLine: "已通过校验",
    metricTrustGrowthLine: "你的反馈将直接影响这些指标",
    metricTrustFallbackLine: "系统正在持续学习，随着使用会不断优化",
    metricCollecting: "数据积累中",
    demoTitle: "Live Demo",
    demoSubtitle: "无需登录，使用示例命盘走真实 Contract → Verifier → Ledger → Feedback → Replay 链路。",
    activeRules: "活跃规则",
    questionPlaceholder: "例如：我未来两年财运如何？",
    sampleQuestion: "我未来两年财运如何？",
    sampleChart: "使用示例命盘",
    sampleChartReady: "示例命盘已就绪",
    generate: "生成预测",
    needActiveRule: "Demo 需要至少一条 active rule。请先由 admin 在 /v17/admin/rules 初始化财富预测规则。",
    needSampleChart: "请先点击“使用示例命盘”，Demo 不会自行补判出生信息。",
    conclusion: "系统裁决",
    confidence: "置信度",
    uncertainty: "不确定性",
    verifiedExplanation: "系统解释（基于已验证 Contract）",
    explanationBoundary: "解释层不参与命理裁决",
    evidence: "Evidence",
    feedbackTitle: "Demo 反馈",
    feedbackCopy: "你的反馈会进入学习信号，用于改进规则评分与候选规则，但不会直接修改当前规则。",
    feedbackHit: "准",
    feedbackMiss: "不准",
    feedbackPartial: "部分准",
    feedbackUnclear: "不清楚",
    replayTitle: "Replay",
    replayCopy: "本次 Demo 已可回放：Ledger、Contract、Evidence、Feedback 会按 prediction_id 关联。",
    replaySummary: "查看回放摘要",
    predictionId: "prediction_id",
    verified: "已验证",
    predictionTrustSummaryTitle: "Prediction Summary",
    predictionTrustSummaryHint: "以下指标是系统级可见度，反馈会持续让预测链路更准。",
    shareReplayTitle: "分享 Replay Link",
    shareReplayCopy: "把这次预测的回放链接发给别人，对方可以看到 prediction_id、Contract、Evidence、Feedback 与 Learning Signal 摘要。",
    shareReplayButton: "复制链接",
    shareReplayCopied: "已复制",
    shareReplayOpen: "打开回放",
    refresh: "刷新",
  },
  en: {
    navLogin: "Sign in",
    navProduct: "Qiazhi",
    heroEyebrow: "Contract-first destiny intelligence",
    heroTitle: "Not fortune telling. A verifiable decision system.",
    heroSubtitle: "Every answer is backed by evidence, recorded in a ledger, replayable, and correctable through feedback.",
    primaryCta: "Start the demo",
    secondaryCta: "See how it works",
    demoStepsTitle: "60-second demo",
    demoStep1: "Ask a question",
    demoStep2: "Use a sample chart",
    demoStep3: "Generate a Contract",
    demoStep4: "Inspect evidence and explanation",
    demoStep5: "Give feedback and replay",
    trustRule: "Rule-adjudicated",
    trustEvidence: "Evidence-linked",
    trustLedger: "Ledger-recorded",
    trustReplay: "Replayable",
    diffAiTitle: "Typical AI",
    diffSystemTitle: "This system",
    ai1: "Generates text",
    ai2: "Hard to trace",
    ai3: "Ends after the answer",
    ai4: "No replay",
    system1: "Generates a Prediction Contract",
    system2: "Traceable Evidence + Ledger",
    system3: "Feedback → Learning Signal",
    system4: "Replayable decisions",
    howTitle: "How it works",
    how1: "Question",
    how2: "Missing info",
    how3: "Rule adjudication",
    how4: "Contract",
    how5: "Verified explanation",
    how6: "Ledger record",
    how7: "Feedback learning",
    how8: "Replay",
    metricsTitle: "Trust Metrics",
    metricPredictions: "Recorded predictions",
    metricFeedback: "User feedback",
    metricRules: "Active rules",
    metricUpdated: "Latest rule update",
    metricHit: "Hit rate",
    metricMiss: "Miss rate",
    metricLive: "Updating live",
    metricTrustHeadline: "Trust Metrics",
    metricTrustMatchLabel: "users marked as fully or partially accurate",
    metricTrustReplayLine: "Replayable",
    metricTrustEvidenceLine: "Evidence-backed",
    metricTrustVerifiedLine: "Verifier-checked",
    metricTrustGrowthLine: "Your feedback directly improves these metrics",
    metricTrustFallbackLine: "The system is still learning and improves with more usage",
    metricCollecting: "Collecting data",
    demoTitle: "Live Demo",
    demoSubtitle: "No sign-in required. Use a sample chart to run the real Contract → Verifier → Ledger → Feedback → Replay path.",
    activeRules: "Active rules",
    questionPlaceholder: "Example: How does my wealth outlook look over the next two years?",
    sampleQuestion: "How does my wealth outlook look over the next two years?",
    sampleChart: "Use sample chart",
    sampleChartReady: "Sample chart ready",
    generate: "Generate prediction",
    needActiveRule: "The demo needs at least one active rule. Ask an admin to initialize the wealth rule in /v17/admin/rules first.",
    needSampleChart: "Please use the sample chart first. The demo will not invent missing birth information.",
    conclusion: "System adjudication",
    confidence: "Confidence",
    uncertainty: "Uncertainty",
    verifiedExplanation: "System explanation (from a verified Contract)",
    explanationBoundary: "The explanation layer does not make destiny decisions",
    evidence: "Evidence",
    feedbackTitle: "Demo feedback",
    feedbackCopy: "Your feedback becomes a learning signal for rule scoring and candidate suggestions, but it does not directly modify the current rule.",
    feedbackHit: "Accurate",
    feedbackMiss: "Not accurate",
    feedbackPartial: "Partly accurate",
    feedbackUnclear: "Unclear",
    replayTitle: "Replay",
    replayCopy: "This demo is replayable: Ledger, Contract, Evidence, and Feedback are linked by prediction_id.",
    replaySummary: "View replay summary",
    predictionId: "prediction_id",
    verified: "Verified",
    predictionTrustSummaryTitle: "Prediction trust summary",
    predictionTrustSummaryHint: "These metrics measure product trust, and your feedback makes them better over time.",
    shareReplayTitle: "Share replay link",
    shareReplayCopy: "Share this replay link so others can inspect the prediction_id, Contract, Evidence, Feedback, and Learning Signal summary.",
    shareReplayButton: "Copy link",
    shareReplayCopied: "Copied",
    shareReplayOpen: "Open replay",
    refresh: "Refresh",
  },
  ko: {
    navLogin: "로그인",
    navProduct: "Qiazhi",
    heroEyebrow: "근거 기반 명리 판단 시스템",
    heroTitle: "단순한 AI 점술이 아니라, 검증 가능한 판단 시스템입니다",
    heroSubtitle: "모든 판단에는 근거와 기록이 남고, 다시 확인할 수 있으며, 사용자의 피드백으로 더 좋아집니다.",
    primaryCta: "Demo 시작하기",
    secondaryCta: "작동 방식 보기",
    demoStepsTitle: "60초 Demo",
    demoStep1: "질문 입력",
    demoStep2: "예시 명식 사용",
    demoStep3: "Contract 생성",
    demoStep4: "근거와 설명 확인",
    demoStep5: "피드백과 회고",
    trustRule: "규칙 판단 완료",
    trustEvidence: "근거 연결 완료",
    trustLedger: "예측 기록 저장",
    trustReplay: "다시 보기 가능",
    diffAiTitle: "일반 AI",
    diffSystemTitle: "이 시스템",
    ai1: "문장만 생성",
    ai2: "근거 추적 어려움",
    ai3: "답변 후 종료",
    ai4: "복기 불가",
    system1: "Prediction Contract 생성",
    system2: "Evidence + Ledger 추적 가능",
    system3: "피드백 → Learning Signal",
    system4: "Replay 가능",
    howTitle: "작동 방식",
    how1: "질문",
    how2: "정보 보완",
    how3: "규칙 판단",
    how4: "Contract",
    how5: "검증된 설명",
    how6: "Ledger 기록",
    how7: "피드백 학습",
    how8: "Replay",
    metricsTitle: "Trust Metrics",
    metricPredictions: "기록된 예측",
    metricFeedback: "사용자 피드백",
    metricRules: "활성 규칙",
    metricUpdated: "최근 규칙 업데이트",
    metricHit: "일치율",
    metricMiss: "오차율",
    metricLive: "실시간 업데이트",
    metricTrustHeadline: "신뢰도 지표",
    metricTrustMatchLabel: "사용자 피드백 기준 부분 또는 완전 일치",
    metricTrustReplayLine: "다시 확인 가능",
    metricTrustEvidenceLine: "근거 기반",
    metricTrustVerifiedLine: "검증 완료",
    metricTrustGrowthLine: "피드백은 이 지표를 직접 개선합니다",
    metricTrustFallbackLine: "시스템이 계속 학습 중입니다. 사용이 늘수록 정확도가 향상됩니다.",
    metricCollecting: "데이터 축적 중",
    demoTitle: "Live Demo",
    demoSubtitle: "로그인 없이 예시 명식으로 실제 Contract → Verifier → Ledger → Feedback → Replay 흐름을 체험합니다.",
    activeRules: "활성 규칙",
    questionPlaceholder: "예: 앞으로 2년 재물운은 어떨까요?",
    sampleQuestion: "앞으로 2년 재물운은 어떨까요?",
    sampleChart: "예시 명식 사용",
    sampleChartReady: "예시 명식 준비됨",
    generate: "예측 생성",
    needActiveRule: "Demo에는 최소 1개의 active rule이 필요합니다. 먼저 admin이 /v17/admin/rules에서 재물 규칙을 초기화해야 합니다.",
    needSampleChart: "먼저 예시 명식을 선택해 주세요. Demo는 부족한 출생 정보를 임의로 채우지 않습니다.",
    conclusion: "시스템 판단",
    confidence: "신뢰도",
    uncertainty: "불확실성",
    verifiedExplanation: "시스템 설명 (검증된 Contract 기반)",
    explanationBoundary: "설명 계층은 명리 판단에 참여하지 않습니다",
    evidence: "근거",
    feedbackTitle: "Demo 피드백",
    feedbackCopy: "피드백은 규칙 점수와 후보 규칙 제안을 개선하는 learning signal이 되지만, 현재 규칙을 직접 수정하지 않습니다.",
    feedbackHit: "맞아요",
    feedbackMiss: "아니에요",
    feedbackPartial: "부분적으로 맞아요",
    feedbackUnclear: "잘 모르겠어요",
    replayTitle: "Replay",
    replayCopy: "이 Demo는 다시 확인할 수 있습니다. Ledger, Contract, Evidence, Feedback이 prediction_id로 연결됩니다.",
    replaySummary: "Replay 요약 보기",
    predictionId: "prediction_id",
    verified: "검증됨",
    predictionTrustSummaryTitle: "예측 신뢰 요약",
    predictionTrustSummaryHint: "이 지표는 제품 신뢰도를 보여주며, 피드백이 누적될수록 더 정확해집니다.",
    shareReplayTitle: "Replay 링크 공유",
    shareReplayCopy: "이 예측의 replay 링크를 공유하면 prediction_id, Contract, Evidence, Feedback, Learning Signal 요약을 확인할 수 있습니다.",
    shareReplayButton: "링크 복사",
    shareReplayCopied: "복사됨",
    shareReplayOpen: "Replay 열기",
    refresh: "새로고침",
  },
};

type DemoPrediction = {
  predictionId: string;
  contractId: string;
  conclusionRef: string;
  conclusion: string;
  explanation: string;
  confidence: number | null;
  uncertainty: string;
  evidence: EvidenceItem[];
  verifierStatus: string;
  replay?: Record<string, unknown>;
  feedbackStatus?: string;
};

type EvidenceItem = {
  ruleId: string;
  version: string;
  contentHash: string;
  matchedFacts: unknown[];
  effect: unknown;
  confidenceDelta: number | null;
};

type TrustMetrics = {
  totalPredictions: number | null;
  totalFeedback: number | null;
  feedbackDistribution: {
    hit: number;
    partial: number;
    miss: number;
    unclear: number;
  };
  verifiedExplanationsRate: number | null;
  replayAvailableRate: number | null;
  activeRules: number | null;
  rulesLastUpdatedAt: string;
  highConfidenceMissRate: number | null;
  learningSignalsGenerated: number | null;
  insightsGenerated: number | null;
  suggestionsGenerated: number | null;
};

const LANGUAGE_LABELS: Record<AppLanguage, string> = {
  zh: "中文",
  en: "English",
  ko: "한국어",
};

const TRUST_METRICS_WARMUP_THRESHOLD = 100;

const EMPTY_TRUST_METRICS: TrustMetrics = {
  totalPredictions: null,
  totalFeedback: null,
  feedbackDistribution: {
    hit: 0,
    partial: 0,
    miss: 0,
    unclear: 0,
  },
  verifiedExplanationsRate: null,
  replayAvailableRate: null,
  activeRules: null,
  rulesLastUpdatedAt: "",
  highConfidenceMissRate: null,
  learningSignalsGenerated: null,
  insightsGenerated: null,
  suggestionsGenerated: null,
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value && typeof value === "object" && !Array.isArray(value));
}

function unwrapEnvelope(value: unknown): Record<string, unknown> {
  if (isRecord(value) && isRecord(value.data)) return value.data;
  return isRecord(value) ? value : {};
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

function readNumber(source: unknown, keys: string[]): number | null {
  if (!isRecord(source)) return null;
  for (const key of keys) {
    const value = source[key];
    if (typeof value === "number" && Number.isFinite(value)) return value;
    if (typeof value === "string" && value.trim() && Number.isFinite(Number(value))) return Number(value);
  }
  return null;
}

function readBool(source: unknown, key: string, fallback = false): boolean {
  if (!isRecord(source)) return fallback;
  const value = source[key];
  return typeof value === "boolean" ? value : fallback;
}

function apiFailureMessage(value: unknown, requestError: string | undefined, fallback: string): string {
  return requestError || readString(value, ["message", "detail", "error"]) || readString(unwrapEnvelope(value), ["message", "detail", "error"]) || fallback;
}

function stableId(prefix: string): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) return `${prefix}_${crypto.randomUUID()}`;
  return `${prefix}_${Date.now()}_${Math.random().toString(16).slice(2)}`;
}

function shortHash(value: string, size = 18): string {
  if (!value) return "n/a";
  return value.length > size ? `${value.slice(0, size - 3)}...` : value;
}

function clampConfidence(value: number | null): number | null {
  if (value === null || !Number.isFinite(value)) return null;
  if (value > 1) return Math.max(0, Math.min(100, value)) / 100;
  return Math.max(0, Math.min(1, value));
}

function percentText(value: number | null): string {
  if (value === null || !Number.isFinite(value)) return "0%";
  return `${Math.max(0, Math.min(100, Math.round(value * 100)))}%`;
}

function numberText(value: number | null): string {
  if (value === null || !Number.isFinite(value)) return "...";
  return new Intl.NumberFormat().format(value);
}

function readRatio(value: unknown, fallback = 0): number {
  if (typeof value === "number" && Number.isFinite(value)) return Math.max(0, Math.min(1, value));
  return fallback;
}

function parseTrustMetrics(source: unknown): TrustMetrics {
  const payload = isRecord(source) ? (isRecord(source.data) ? source.data : source) : {};
  const distribution = readRecord(payload, "feedback_distribution");
  const trust: TrustMetrics = {
    totalPredictions: readNumber(payload, ["total_predictions", "total"]),
    totalFeedback: readNumber(payload, ["total_feedback"]),
    feedbackDistribution: {
      hit: readRatio(distribution.hit),
      partial: readRatio(distribution.partial),
      miss: readRatio(distribution.miss),
      unclear: readRatio(distribution.unclear),
    },
    verifiedExplanationsRate: readNumber(payload, ["verified_explanations_rate"]),
    replayAvailableRate: readNumber(payload, ["replay_available_rate"]),
    activeRules: readNumber(payload, ["active_rules", "activeRuleCount"]),
    rulesLastUpdatedAt: readString(payload, ["rules_last_updated_at", "rulesLastUpdatedAt", "latest_rule_update"]),
    highConfidenceMissRate: readNumber(payload, ["high_confidence_miss_rate"]),
    learningSignalsGenerated: readNumber(payload, ["learning_signals_generated"]),
    insightsGenerated: readNumber(payload, ["insights_generated"]),
    suggestionsGenerated: readNumber(payload, ["suggestions_generated"]),
  };
  return trust;
}

function hasTrustHistory(metrics: TrustMetrics): boolean {
  return (metrics.totalPredictions ?? 0) >= TRUST_METRICS_WARMUP_THRESHOLD;
}

function matchRateText(metrics: TrustMetrics): string {
  const matched = metrics.feedbackDistribution.hit + metrics.feedbackDistribution.partial;
  return percentText(Math.max(0, Math.min(1, matched)));
}

function buildRulesLastUpdatedText(metrics: TrustMetrics, text: Copy): string {
  if (metrics.rulesLastUpdatedAt) return metrics.rulesLastUpdatedAt;
  return text.metricLive;
}

function compactJson(value: unknown): string {
  try {
    return JSON.stringify(value);
  } catch {
    return String(value);
  }
}

function safeOutputText(safeOutput: Record<string, unknown>): string {
  const direct = readString(safeOutput, ["text", "summary", "answer", "explanation"]);
  if (direct) return direct;
  const sections = readRecord(safeOutput, "sections");
  const conclusion = sections.conclusion;
  if (Array.isArray(conclusion)) return conclusion.map(String).filter(Boolean).join("；");
  return readString(sections, ["conclusion", "summary"], "");
}

function extractConclusionRef(safeOutput: Record<string, unknown>, contract: Record<string, unknown>): string {
  for (const source of [safeOutput, readRecord(safeOutput, "sections"), contract]) {
    for (const key of ["conclusion_ref", "conclusion_id"]) {
      const value = readString(source, [key]);
      if (value) return value;
    }
    for (const key of ["conclusion_refs", "conclusion_ids"]) {
      const values = readArray(source, key);
      const first = values.find((item) => typeof item === "string" && item.trim());
      if (typeof first === "string") return first.trim();
    }
  }
  return "conclusion_1";
}

function normalizeEvidence(rows: unknown[]): EvidenceItem[] {
  return rows.filter(isRecord).map((row) => ({
    ruleId: readString(row, ["rule_id", "ruleId"]),
    version: readString(row, ["version", "rule_version"]),
    contentHash: readString(row, ["content_hash", "rule_hash"]),
    matchedFacts: readArray(row, "matched_facts"),
    effect: row.effect || row.effects || {},
    confidenceDelta: clampConfidence(readNumber(row, ["confidence_delta", "confidence"])),
  }));
}

function buildDemoChartSnapshot(): Record<string, unknown> {
  return {
    source: "landing_demo",
    is_demo: true,
    completeness: "complete_birth_fields",
    birth_time: "1990-01-01T09:00:00",
    calendar: "solar",
    gender: "male",
    matched_facts: ["complete_birth_fields"],
    birth_fields: { year: "1990", month: "01", day: "01", hour: "09", gender: "male" },
    four_pillars: { year: "1990", month: "01", day: "01", hour: "09" },
  };
}

function browserLanguage(): AppLanguage | "" {
  if (typeof navigator === "undefined") return "";
  const langs = navigator.languages?.length ? navigator.languages : [navigator.language];
  const hit = langs.map((lang) => lang.toLowerCase()).find((lang) => lang.startsWith("zh") || lang.startsWith("ko") || lang.startsWith("en"));
  if (!hit) return "";
  if (hit.startsWith("zh")) return "zh";
  if (hit.startsWith("ko")) return "ko";
  return "en";
}

function hasPersistedLanguage(): boolean {
  if (typeof window === "undefined" || typeof document === "undefined") return true;
  const stored = window.localStorage.getItem(APP_LANGUAGE_STORAGE_KEY);
  const cookie = document.cookie.split(";").map((item) => item.trim()).find((item) => item.startsWith(`${APP_LANGUAGE_COOKIE}=`));
  return Boolean(stored || cookie);
}

export function V18_LandingDemoExperience({ initialMode = "landing" }: LandingDemoExperienceProps): ReactNode {
  const { language, setLanguage } = useAppLanguage();
  const text = COPY[language];
  const [question, setQuestion] = useState(text.sampleQuestion);
  const [useSampleChart, setUseSampleChart] = useState(initialMode === "demo");
  const [metrics, setMetrics] = useState<TrustMetrics>(EMPTY_TRUST_METRICS);
  const [loadingMetrics, setLoadingMetrics] = useState(false);
  const [running, setRunning] = useState(false);
  const [prediction, setPrediction] = useState<DemoPrediction | null>(null);
  const [error, setError] = useState("");

  const demoReady = useMemo(() => (metrics.activeRules ?? 0) > 0, [metrics.activeRules]);

  useEffect(() => {
    if (!hasPersistedLanguage()) {
      const detected = browserLanguage();
      if (detected) setLanguage(detected);
    }
  }, [setLanguage]);

  useEffect(() => {
    setQuestion((prev) => (prev.trim() ? prev : COPY[language].sampleQuestion));
  }, [language]);

  const loadMetrics = useCallback(async () => {
    setLoadingMetrics(true);
    try {
      const trustResp = await requestJson<unknown>("/api/v18.1/trust-metrics", noStoreInit());
      if (trustResp.ok) {
        setMetrics(parseTrustMetrics(trustResp.data));
        return;
      }

      const rulesResp = await requestJson<unknown>("/api/v18.1/rule-kernels?status=active", noStoreInit());
      const feedbackResp = await requestJson<unknown>("/api/v18.1/feedback?limit=1", noStoreInit());
      const rulesPayload = unwrapEnvelope(rulesResp.data);
      const rules = readArray(rulesPayload, "items").filter(isRecord);
      const latest = rules
        .map((rule) => readString(rule, ["approved_at", "updated_at", "created_at"]))
        .filter(Boolean)
        .sort()
        .at(-1);
      const feedbackPayload = unwrapEnvelope(feedbackResp.data);
      const feedbackTotal = readNumber(feedbackPayload, ["total_matched", "total", "count"]);
      setMetrics({
        ...EMPTY_TRUST_METRICS,
        totalFeedback: feedbackTotal,
        activeRules: rules.length,
        rulesLastUpdatedAt: latest || text.metricLive,
      });
    } catch {
      const [rulesResp, feedbackResp] = await Promise.all([
        requestJson<unknown>("/api/v18.1/rule-kernels?status=active", noStoreInit()),
        requestJson<unknown>("/api/v18.1/feedback?limit=1", noStoreInit()),
      ]);
      const rulesPayload = unwrapEnvelope(rulesResp.data);
      const rules = readArray(rulesPayload, "items").filter(isRecord);
      const latest = rules
        .map((rule) => readString(rule, ["approved_at", "updated_at", "created_at"]))
        .filter(Boolean)
        .sort()
        .at(-1);
      const feedbackPayload = unwrapEnvelope(feedbackResp.data);
      const feedbackTotal = readNumber(feedbackPayload, ["total_matched", "total", "count"]);
      setMetrics({
        ...EMPTY_TRUST_METRICS,
        totalFeedback: feedbackTotal,
        activeRules: rules.length,
        rulesLastUpdatedAt: latest || text.metricLive,
      });
    } finally {
      setLoadingMetrics(false);
    }
  }, [text.metricLive]);

  useEffect(() => {
    void loadMetrics();
  }, [loadMetrics]);

  const runDemo = useCallback(async () => {
    setError("");
    setPrediction(null);
    setRunning(true);
    try {
      if (!demoReady) throw new Error(text.needActiveRule);
      if (!useSampleChart) throw new Error(text.needSampleChart);

      const sessionResp = await requestJson<unknown>(
        "/api/v18.1/agent/sessions",
        jsonPostInit({ surface: "landing_demo", user_locale: language, is_demo: true }, noStoreInit()),
      );
      if (!sessionResp.ok) throw new Error(apiFailureMessage(sessionResp.data, sessionResp.error, "Demo session failed."));
      const session = unwrapEnvelope(sessionResp.data);
      const sessionId = readString(session, ["agent_session_id", "session_id", "id"]);
      if (!sessionId) throw new Error("Demo session missing session_id.");

      const turnResp = await requestJson<unknown>(
        `/api/v18.1/agent/sessions/${encodeURIComponent(sessionId)}/turns`,
        jsonPostInit(
          {
            request_id: stableId("landing_demo_turn"),
            is_demo: true,
            user_message: question.trim() || text.sampleQuestion,
            user_query: question.trim() || text.sampleQuestion,
            plugin_claims: [{ plugin_id: "plugin.agent", claim_id: "landing_demo" }],
            birth_payload: { year: "1990", month: "01", day: "01", hour: "09", gender: "male" },
            chart_snapshot: buildDemoChartSnapshot(),
            missing_info_policy: "clarify_before_predict",
          },
          noStoreInit(),
        ),
      );
      if (!turnResp.ok) throw new Error(apiFailureMessage(turnResp.data, turnResp.error, "Demo prediction failed."));
      const turn = unwrapEnvelope(turnResp.data);
      const safeOutput = readRecord(turn, "safe_output");
      if (readString(safeOutput, ["type"]) === "clarification_question" || readBool(safeOutput, "is_prediction", true) === false) {
        throw new Error("Demo returned a clarification instead of a prediction.");
      }
      const predictionId = readString(turn, ["prediction_id"]);
      const contractId = readString(turn, ["contract_id"]);
      if (!predictionId) throw new Error("Demo response missing prediction_id.");

      const explainResp = await requestJson<unknown>(
        `/api/v18.1/predictions/${encodeURIComponent(predictionId)}/explain`,
        jsonPostInit(
          {
            prediction_id: predictionId,
            contract_id: contractId,
            is_demo: true,
            allowed_output_scope: "verified_prediction_explanation",
            user_locale: language,
            tone: "calm",
            explanation_level: "brief",
            include_uncertainty: true,
            include_evidence_trace: true,
          },
          noStoreInit(),
        ),
      );
      if (!explainResp.ok) throw new Error(apiFailureMessage(explainResp.data, explainResp.error, "Verified explanation failed."));
      const explainPayload = unwrapEnvelope(explainResp.data);
      const explanationResponse =
        readRecord(explainPayload, "explanation_response").safe_output || explainPayload.explanation_response
          ? readRecord(explainPayload, "explanation_response")
          : explainPayload;
      const verifier = readRecord(explanationResponse, "verifier");
      if (readBool(verifier, "ok", true) === false || readBool(explanationResponse, "verified", true) === false) {
        throw new Error("Explanation verifier blocked the output.");
      }

      const replayResp = await requestJson<unknown>(`/api/v18.1/predictions/${encodeURIComponent(predictionId)}/replay`, noStoreInit());
      const replay = replayResp.ok ? unwrapEnvelope(replayResp.data) : {};
      const contract = readRecord(replay, "contract");
      const evidence = normalizeEvidence(readArray(contract, "rule_evidence").length ? readArray(contract, "rule_evidence") : readArray(replay, "evidence"));
      const uncertainty = readRecord(contract, "uncertainty");
      const explanation =
        readString(explanationResponse, ["explanation", "verified_output", "output"]) ||
        safeOutputText(readRecord(explanationResponse, "safe_output")) ||
        safeOutputText(safeOutput);

      setPrediction({
        predictionId,
        contractId,
        conclusionRef: extractConclusionRef(safeOutput, contract),
        conclusion: safeOutputText(safeOutput) || text.conclusion,
        explanation,
        confidence: clampConfidence(readNumber(contract, ["confidence"])),
        uncertainty:
          readString(explanationResponse, ["uncertainty", "uncertainty_text"]) ||
          `${text.uncertainty}: ${Math.round((clampConfidence(readNumber(uncertainty, ["score"])) ?? 1) * 100)}%`,
        evidence,
        verifierStatus: readString(verifier, ["action", "status"], text.verified),
        replay,
      });
      void loadMetrics();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Demo failed.");
    } finally {
      setRunning(false);
    }
  }, [demoReady, language, loadMetrics, question, text, useSampleChart]);

  const submitFeedback = useCallback(
    async (feedbackType: "hit" | "miss" | "partial" | "unclear") => {
      if (!prediction?.predictionId) return;
      setError("");
      try {
        const feedbackResp = await requestJson<unknown>(
          `/api/v18.1/predictions/${encodeURIComponent(prediction.predictionId)}/feedback`,
          jsonPostInit(
            {
              request_id: stableId("landing_demo_feedback"),
              is_demo: true,
              prediction_id: prediction.predictionId,
              conclusion_ref: prediction.conclusionRef,
              conclusion_id: prediction.conclusionRef,
              feedback_type: feedbackType,
              user_comment: "Demo feedback",
              observed_event: { source: "landing_demo", is_demo: true, label: feedbackType },
              observed_at: new Date().toISOString(),
            },
            noStoreInit(),
          ),
        );
        if (!feedbackResp.ok) throw new Error(apiFailureMessage(feedbackResp.data, feedbackResp.error, "Demo feedback failed."));
        const payload = unwrapEnvelope(feedbackResp.data);
        const signal = readRecord(payload, "learning_signal");
        setPrediction((prev) =>
          prev
            ? {
                ...prev,
                feedbackStatus: `learning_signal=${readString(signal, ["signal_id", "id"], "created")}`,
              }
            : prev,
        );
        void loadMetrics();
      } catch (err) {
        setError(err instanceof Error ? err.message : "Demo feedback failed.");
      }
    },
    [prediction, loadMetrics],
  );

  return (
    <main className="min-h-screen overflow-hidden bg-[#070b10] text-slate-100">
      <div className="pointer-events-none fixed inset-0">
        <div className="absolute left-[-12%] top-[-20%] h-[36rem] w-[36rem] rounded-full bg-cyan-400/20 blur-3xl" />
        <div className="absolute bottom-[-20%] right-[-10%] h-[38rem] w-[38rem] rounded-full bg-emerald-300/12 blur-3xl" />
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(255,255,255,0.08),transparent_35%),linear-gradient(135deg,rgba(255,255,255,0.06),transparent_34%)]" />
      </div>
      <section className="relative mx-auto w-full max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
        <LanguageNav language={language} setLanguage={setLanguage} text={text} />
        <LandingHero text={text} onDemoClick={() => document.getElementById("live-demo")?.scrollIntoView({ behavior: "smooth", block: "start" })} />
        <TrustMetricsPanel text={text} metrics={metrics} loading={loadingMetrics} onRefresh={() => void loadMetrics()} />
        <TrustStrip text={text} />
        <DifferenceGrid text={text} />
        <HowItWorksFlow text={text} />
        <DemoAgentPanel
          activeRuleCount={metrics.activeRules}
          metrics={metrics}
          error={error}
          prediction={prediction}
          question={question}
          running={running}
          text={text}
          useSampleChart={useSampleChart}
          onFeedback={(type) => void submitFeedback(type)}
          onQuestionChange={setQuestion}
          onRunDemo={() => void runDemo()}
          onSampleChart={() => setUseSampleChart(true)}
        />
      </section>
    </main>
  );
}

function LanguageNav({
  language,
  setLanguage,
  text,
}: {
  language: AppLanguage;
  setLanguage: (language: AppLanguage) => void;
  text: Copy;
}): ReactNode {
  return (
    <nav className="mb-5 flex flex-wrap items-center justify-between gap-3 rounded-[1.5rem] border border-white/10 bg-white/[0.05] p-3 backdrop-blur">
      <a href="/" className="inline-flex items-center gap-2 px-2 text-sm font-semibold text-white">
        <Sparkles className="h-4 w-4 text-cyan-200" />
        {text.navProduct}
      </a>
      <div className="flex flex-wrap items-center gap-2">
        {(Object.keys(LANGUAGE_LABELS) as AppLanguage[]).map((item) => (
          <button
            key={item}
            type="button"
            onClick={() => setLanguage(item)}
            className={`rounded-full border px-3 py-1.5 text-xs transition ${
              item === language ? "border-cyan-200/30 bg-cyan-200/15 text-cyan-50" : "border-white/10 bg-black/20 text-slate-300 hover:bg-white/10"
            }`}
          >
            {LANGUAGE_LABELS[item]}
          </button>
        ))}
        <a href="/login" className="rounded-full border border-white/10 bg-white/10 px-3 py-1.5 text-xs text-slate-100 transition hover:bg-white/15">
          {text.navLogin}
        </a>
      </div>
    </nav>
  );
}

function LandingHero({ text, onDemoClick }: { text: Copy; onDemoClick: () => void }): ReactNode {
  return (
    <section className="grid min-h-[78vh] items-center gap-8 rounded-[2.5rem] border border-white/10 bg-white/[0.07] p-6 shadow-2xl shadow-black/30 backdrop-blur md:p-10 lg:grid-cols-[minmax(0,1fr)_25rem]">
      <div>
        <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-cyan-200/20 bg-cyan-200/10 px-3 py-1.5 text-sm text-cyan-100">
          <ShieldCheck className="h-4 w-4" />
          {text.heroEyebrow}
        </div>
        <h1 className="max-w-4xl text-4xl font-semibold tracking-tight text-white md:text-6xl">{text.heroTitle}</h1>
        <p className="mt-6 max-w-2xl text-base leading-8 text-slate-300 md:text-lg">{text.heroSubtitle}</p>
        <div className="mt-8 flex flex-col gap-3 sm:flex-row">
          <button type="button" onClick={onDemoClick} className="inline-flex items-center justify-center gap-2 rounded-full bg-cyan-300 px-6 py-3 font-semibold text-slate-950 transition hover:bg-cyan-200">
            {text.primaryCta}
            <ArrowRight className="h-4 w-4" />
          </button>
          <button type="button" onClick={() => document.getElementById("how-it-works")?.scrollIntoView({ behavior: "smooth", block: "start" })} className="inline-flex items-center justify-center gap-2 rounded-full border border-white/10 bg-white/10 px-6 py-3 font-semibold text-slate-100 transition hover:bg-white/15">
            {text.secondaryCta}
          </button>
        </div>
      </div>
      <div className="rounded-[2rem] border border-white/10 bg-black/25 p-5">
        <p className="text-sm uppercase tracking-[0.22em] text-cyan-200">{text.demoStepsTitle}</p>
        <div className="mt-4 space-y-3">
          {[text.demoStep1, text.demoStep2, text.demoStep3, text.demoStep4, text.demoStep5].map((item, index) => (
            <div key={item} className="flex items-center gap-3 rounded-2xl border border-white/10 bg-white/[0.05] p-3 text-sm text-slate-200">
              <span className="grid h-7 w-7 place-items-center rounded-full bg-cyan-300 text-xs font-bold text-slate-950">{index + 1}</span>
              {item}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function TrustStrip({ text }: { text: Copy }): ReactNode {
  return (
    <section className="mt-5 flex flex-wrap gap-2 rounded-[1.5rem] border border-white/10 bg-white/[0.05] p-4 text-sm text-slate-200">
      {[text.trustRule, text.trustEvidence, text.trustLedger, text.trustReplay].map((item) => (
        <span key={item} className="inline-flex items-center gap-2 rounded-full border border-emerald-300/20 bg-emerald-300/10 px-3 py-1.5 text-emerald-100">
          <CheckCircle2 className="h-4 w-4" />
          {item}
        </span>
      ))}
    </section>
  );
}

function DifferenceGrid({ text }: { text: Copy }): ReactNode {
  return (
    <section className="mt-6 grid gap-4 md:grid-cols-2">
      <CompareCard title={text.diffAiTitle} tone="muted" items={[text.ai1, text.ai2, text.ai3, text.ai4]} />
      <CompareCard title={text.diffSystemTitle} tone="bright" items={[text.system1, text.system2, text.system3, text.system4]} />
    </section>
  );
}

function CompareCard({ title, tone, items }: { title: string; tone: "muted" | "bright"; items: string[] }): ReactNode {
  return (
    <article className={`rounded-[2rem] border p-6 shadow-xl shadow-black/20 ${tone === "bright" ? "border-cyan-200/20 bg-cyan-200/[0.08]" : "border-white/10 bg-white/[0.04]"}`}>
      <h2 className="mb-4 text-xl font-semibold text-white">{title}</h2>
      <div className="space-y-3">
        {items.map((item) => (
          <div key={item} className="rounded-2xl border border-white/10 bg-black/20 p-4 text-sm text-slate-200">
            {item}
          </div>
        ))}
      </div>
    </article>
  );
}

function HowItWorksFlow({ text }: { text: Copy }): ReactNode {
  const steps = [text.how1, text.how2, text.how3, text.how4, text.how5, text.how6, text.how7, text.how8];
  return (
    <section id="how-it-works" className="mt-6 rounded-[2rem] border border-white/10 bg-white/[0.06] p-6 shadow-xl shadow-black/20">
      <h2 className="flex items-center gap-2 text-2xl font-semibold text-white">
        <BookOpenCheck className="h-6 w-6 text-cyan-200" />
        {text.howTitle}
      </h2>
      <div className="mt-5 flex flex-wrap gap-3">
        {steps.map((step, index) => (
          <div key={`${step}-${index}`} className="flex items-center gap-3">
            <span className="rounded-full border border-white/10 bg-black/25 px-4 py-2 text-sm text-slate-100">{step}</span>
            {index < steps.length - 1 ? <ArrowRight className="h-4 w-4 text-slate-500" /> : null}
          </div>
        ))}
      </div>
    </section>
  );
}

function TrustMetricsPanel({ text, metrics, loading, onRefresh }: { text: Copy; metrics: TrustMetrics; loading: boolean; onRefresh: () => void }): ReactNode {
  const hasHistory = hasTrustHistory(metrics);
  return (
    <section className="mt-6 rounded-[2rem] border border-emerald-200/20 bg-emerald-200/[0.06] p-6 shadow-xl shadow-black/20">
      <div className="mb-4 flex items-center justify-between gap-3">
        <h2 className="flex items-center gap-2 text-2xl font-semibold text-white">
          <Database className="h-6 w-6 text-emerald-200" />
          {text.metricTrustHeadline}
        </h2>
        <button type="button" onClick={onRefresh} className="rounded-full border border-white/10 bg-white/10 px-3 py-2 text-xs text-slate-200 transition hover:bg-white/15">
          <RefreshCcw className={`inline h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} /> {text.refresh}
        </button>
      </div>
      <div className="grid gap-4 lg:grid-cols-2">
        <article className="rounded-2xl border border-white/10 bg-black/20 p-5">
          <div className="text-sm text-slate-300">
            {text.metricPredictions}: {numberText(metrics.totalPredictions)}
          </div>
          <div className="mt-2 text-2xl font-semibold text-white">
            {hasHistory ? `${matchRateText(metrics)} ${text.metricTrustMatchLabel}` : text.metricTrustFallbackLine}
          </div>
          <p className="mt-3 text-xs text-slate-400">{text.metricTrustGrowthLine}</p>
          <p className="mt-4 text-xs text-slate-500">
            {text.metricUpdated}: {buildRulesLastUpdatedText(metrics, text)}
          </p>
        </article>
        <article className="rounded-2xl border border-white/10 bg-black/20 p-5">
          <ul className="space-y-2 text-sm text-slate-200">
            <li className="flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-emerald-200" />
              {text.metricTrustReplayLine}
            </li>
            <li className="flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-emerald-200" />
              {text.metricTrustEvidenceLine}
            </li>
            <li className="flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-emerald-200" />
              {text.metricTrustVerifiedLine}
            </li>
          </ul>
          <div className="mt-4 grid grid-cols-2 gap-3 text-xs text-slate-300">
            <div>
              <p className="uppercase tracking-[0.16em] text-slate-500">{text.metricFeedback}</p>
              <p className="mt-1 text-sm text-white">{numberText(metrics.totalFeedback)}</p>
            </div>
            <div>
              <p className="uppercase tracking-[0.16em] text-slate-500">{text.metricRules}</p>
              <p className="mt-1 text-sm text-white">{numberText(metrics.activeRules)}</p>
            </div>
          </div>
        </article>
      </div>
      <div className="mt-4 grid gap-4 md:grid-cols-4">
        <MetricCard label={text.metricTrustReplayLine} value={hasHistory ? percentText(metrics.replayAvailableRate) : text.metricCollecting} />
        <MetricCard label={text.metricTrustVerifiedLine} value={hasHistory ? percentText(metrics.verifiedExplanationsRate) : text.metricCollecting} />
        <MetricCard label={`${text.metricHit} / ${text.metricMiss}`} value={hasHistory ? percentText(metrics.feedbackDistribution.miss + metrics.feedbackDistribution.hit) : text.metricCollecting} />
        <MetricCard label={text.metricMiss} value={hasHistory ? percentText(metrics.highConfidenceMissRate) : text.metricCollecting} />
      </div>
    </section>
  );
}

function MetricCard({ label, value }: { label: string; value: string }): ReactNode {
  return (
    <div className="rounded-2xl border border-white/10 bg-black/20 p-4">
      <div className="text-xs uppercase tracking-[0.16em] text-slate-500">{label}</div>
      <div className="mt-2 break-words text-lg font-semibold text-white">{value}</div>
    </div>
  );
}

function PredictionTrustSummary({ text, metrics }: { text: Copy; metrics: TrustMetrics }): ReactNode {
  const hasHistory = hasTrustHistory(metrics);
  return (
    <article className="rounded-[2rem] border border-cyan-200/20 bg-cyan-200/[0.06] p-5">
      <h3 className="mb-3 flex items-center gap-2 text-lg font-semibold text-white">
        <ShieldCheck className="h-5 w-5 text-cyan-200" />
        {text.predictionTrustSummaryTitle}
      </h3>
      {hasHistory ? (
        <div className="space-y-3 text-sm text-slate-200">
          <p>
            {text.metricPredictions}: {numberText(metrics.totalPredictions)}；{matchRateText(metrics)} {text.metricTrustMatchLabel}
          </p>
          <p className="text-xs text-slate-400">{text.predictionTrustSummaryHint}</p>
          <ul className="space-y-1.5 text-xs text-slate-300">
            <li>✔ {text.metricTrustReplayLine}：{percentText(metrics.replayAvailableRate)}</li>
            <li>✔ {text.metricTrustEvidenceLine}：{percentText(metrics.feedbackDistribution.hit + metrics.feedbackDistribution.partial)}</li>
            <li>✔ {text.metricTrustVerifiedLine}：{percentText(metrics.verifiedExplanationsRate)}</li>
          </ul>
        </div>
      ) : (
        <p className="text-sm leading-6 text-slate-300">{text.metricTrustFallbackLine}</p>
      )}
    </article>
  );
}

function DemoAgentPanel({
  activeRuleCount,
  metrics,
  error,
  prediction,
  question,
  running,
  text,
  useSampleChart,
  onFeedback,
  onQuestionChange,
  onRunDemo,
  onSampleChart,
}: {
  activeRuleCount: number | null;
  metrics: TrustMetrics;
  error: string;
  prediction: DemoPrediction | null;
  question: string;
  running: boolean;
  text: Copy;
  useSampleChart: boolean;
  onFeedback: (type: "hit" | "miss" | "partial" | "unclear") => void;
  onQuestionChange: (value: string) => void;
  onRunDemo: () => void;
  onSampleChart: () => void;
}): ReactNode {
  return (
    <section id="live-demo" className="mt-6 rounded-[2.25rem] border border-cyan-200/20 bg-cyan-200/[0.07] p-6 shadow-2xl shadow-black/25">
      <div className="mb-5 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div>
          <h2 className="flex items-center gap-2 text-3xl font-semibold text-white">
            <Bot className="h-7 w-7 text-cyan-200" />
            {text.demoTitle}
          </h2>
          <p className="mt-2 text-sm leading-6 text-slate-300">{text.demoSubtitle}</p>
        </div>
        <span className={`rounded-full border px-3 py-1.5 text-xs ${activeRuleCount ? "border-emerald-300/20 bg-emerald-300/10 text-emerald-100" : "border-amber-300/20 bg-amber-300/10 text-amber-100"}`}>
          {text.activeRules}: {activeRuleCount ?? "..."}
        </span>
      </div>
      {error ? (
        <div className="mb-4 flex items-start gap-2 rounded-2xl border border-rose-300/20 bg-rose-500/10 p-4 text-sm text-rose-100">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
          <span>{error}</span>
        </div>
      ) : null}
      <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_12rem]">
        <textarea
          value={question}
          onChange={(event) => onQuestionChange(event.target.value)}
          className="min-h-28 resize-none rounded-[1.5rem] border border-white/10 bg-black/25 px-4 py-3 text-sm leading-6 text-slate-100 outline-none placeholder:text-slate-500 focus:border-cyan-300/50"
          placeholder={text.questionPlaceholder}
        />
        <div className="grid gap-3">
          <button type="button" onClick={onSampleChart} className={`rounded-[1.5rem] border px-4 py-3 text-sm font-semibold transition ${useSampleChart ? "border-emerald-300/20 bg-emerald-300/10 text-emerald-100" : "border-white/10 bg-white/10 text-slate-100 hover:bg-white/15"}`}>
            {useSampleChart ? text.sampleChartReady : text.sampleChart}
          </button>
          <button type="button" onClick={onRunDemo} disabled={running} className="inline-flex items-center justify-center gap-2 rounded-[1.5rem] bg-cyan-300 px-4 py-3 text-sm font-semibold text-slate-950 transition hover:bg-cyan-200 disabled:cursor-not-allowed disabled:bg-slate-600 disabled:text-slate-300">
            {running ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
            {text.generate}
          </button>
        </div>
      </div>
      {prediction ? <DemoPredictionResult prediction={prediction} text={text} metrics={metrics} onFeedback={onFeedback} /> : null}
    </section>
  );
}

function DemoPredictionResult({
  prediction,
  text,
  metrics,
  onFeedback,
}: {
  prediction: DemoPrediction;
  text: Copy;
  metrics: TrustMetrics;
  onFeedback: (type: "hit" | "miss" | "partial" | "unclear") => void;
}): ReactNode {
  const confidence = prediction.confidence === null ? "n/a" : `${Math.round(prediction.confidence * 100)}%`;
  const [copied, setCopied] = useState(false);
  const replayUrl = useMemo(() => {
    if (typeof window === "undefined") return "";
    return `${window.location.origin}/demo/replay/${encodeURIComponent(prediction.predictionId)}`;
  }, [prediction.predictionId]);

  const copyReplayLink = useCallback(async () => {
    if (!replayUrl) return;
    await navigator.clipboard?.writeText(replayUrl);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1600);
  }, [replayUrl]);

  return (
    <section className="mt-6 grid gap-5 lg:grid-cols-[minmax(0,1fr)_24rem]">
      <div className="space-y-5">
        <article className="rounded-[2rem] border border-white/10 bg-black/25 p-5">
          <div className="mb-3 flex flex-wrap gap-2">
            <span className="rounded-full bg-emerald-300/10 px-3 py-1 text-xs text-emerald-100">{text.predictionId} {shortHash(prediction.predictionId)}</span>
            <span className="rounded-full bg-cyan-300/10 px-3 py-1 text-xs text-cyan-100">{text.verified} {prediction.verifierStatus}</span>
          </div>
          <h3 className="text-2xl font-semibold text-white">{prediction.conclusion}</h3>
          <div className="mt-4 grid gap-3 md:grid-cols-2">
            <div className="rounded-2xl border border-white/10 bg-white/[0.05] p-4">
              <p className="text-xs uppercase tracking-[0.16em] text-slate-500">{text.confidence}</p>
              <p className="mt-1 text-xl font-semibold text-white">{confidence}</p>
            </div>
            <div className="rounded-2xl border border-amber-300/20 bg-amber-300/10 p-4">
              <p className="text-xs uppercase tracking-[0.16em] text-amber-100/70">{text.uncertainty}</p>
              <p className="mt-1 text-sm leading-6 text-amber-50">{prediction.uncertainty}</p>
            </div>
          </div>
        </article>
        <PredictionTrustSummary text={text} metrics={metrics} />
        <article className="rounded-[2rem] border border-white/10 bg-white/[0.06] p-5">
          <div className="mb-3 flex flex-wrap gap-2">
            <span className="rounded-full border border-emerald-300/20 bg-emerald-300/10 px-3 py-1 text-xs text-emerald-100">{text.verifiedExplanation}</span>
            <span className="rounded-full border border-cyan-300/20 bg-cyan-300/10 px-3 py-1 text-xs text-cyan-100">{text.explanationBoundary}</span>
          </div>
          <p className="whitespace-pre-wrap text-sm leading-7 text-slate-200">{prediction.explanation}</p>
        </article>
        <article className="rounded-[2rem] border border-white/10 bg-white/[0.06] p-5">
          <h3 className="mb-2 flex items-center gap-2 text-lg font-semibold text-white">
            <MessageSquare className="h-5 w-5 text-amber-200" />
            {text.feedbackTitle}
          </h3>
          <p className="text-sm leading-6 text-slate-400">{text.feedbackCopy}</p>
          <div className="mt-4 flex flex-wrap gap-2">
            {[
              ["hit", text.feedbackHit],
              ["miss", text.feedbackMiss],
              ["partial", text.feedbackPartial],
              ["unclear", text.feedbackUnclear],
            ].map(([type, label]) => (
              <button key={type} type="button" onClick={() => onFeedback(type as "hit" | "miss" | "partial" | "unclear")} className="rounded-full border border-white/10 bg-black/20 px-4 py-2 text-sm text-slate-100 transition hover:bg-white/10">
                {label}
              </button>
            ))}
          </div>
          {prediction.feedbackStatus ? <p className="mt-3 rounded-2xl border border-emerald-300/20 bg-emerald-300/10 p-3 text-sm text-emerald-100">{prediction.feedbackStatus}</p> : null}
        </article>
        <article className="rounded-[2rem] border border-emerald-300/20 bg-emerald-300/[0.07] p-5">
          <h3 className="mb-2 flex items-center gap-2 text-lg font-semibold text-white">
            <Share2 className="h-5 w-5 text-emerald-200" />
            {text.shareReplayTitle}
          </h3>
          <p className="text-sm leading-6 text-slate-300">{text.shareReplayCopy}</p>
          <div className="mt-4 rounded-2xl border border-white/10 bg-black/20 p-3 font-mono text-xs text-slate-300">
            {replayUrl}
          </div>
          <div className="mt-4 flex flex-wrap gap-2">
            <button type="button" onClick={() => void copyReplayLink()} className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-black/20 px-4 py-2 text-sm text-slate-100 transition hover:bg-white/10">
              <CopyIcon className="h-4 w-4" />
              {copied ? text.shareReplayCopied : text.shareReplayButton}
            </button>
            <a href={replayUrl} target="_blank" rel="noreferrer" className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/10 px-4 py-2 text-sm text-slate-100 transition hover:bg-white/15">
              <ExternalLink className="h-4 w-4" />
              {text.shareReplayOpen}
            </a>
          </div>
        </article>
      </div>
      <aside className="space-y-5">
        <article className="rounded-[2rem] border border-white/10 bg-white/[0.06] p-5">
          <h3 className="mb-3 flex items-center gap-2 text-lg font-semibold text-white">
            <ClipboardCheck className="h-5 w-5 text-cyan-200" />
            {text.evidence}
          </h3>
          <div className="space-y-3">
            {prediction.evidence.slice(0, 2).map((item, index) => (
              <div key={`${item.ruleId}-${index}`} className="rounded-2xl border border-white/10 bg-black/20 p-4 text-sm">
                <p className="font-mono text-xs text-cyan-100">{item.ruleId || "rule"}</p>
                <p className="mt-2 text-slate-300">effect: {compactJson(item.effect)}</p>
                <p className="mt-1 text-slate-400">facts: {item.matchedFacts.length ? compactJson(item.matchedFacts) : "n/a"}</p>
                <p className="mt-1 text-slate-400">confidence_delta: {item.confidenceDelta === null ? "n/a" : `${Math.round(item.confidenceDelta * 100)}%`}</p>
              </div>
            ))}
          </div>
        </article>
        <article className="rounded-[2rem] border border-white/10 bg-white/[0.06] p-5">
          <h3 className="mb-3 flex items-center gap-2 text-lg font-semibold text-white">
            <History className="h-5 w-5 text-cyan-200" />
            {text.replayTitle}
          </h3>
          <p className="text-sm leading-6 text-slate-400">{text.replayCopy}</p>
          <details className="mt-3 rounded-2xl border border-white/10 bg-black/20 p-3 text-xs text-slate-300">
            <summary className="cursor-pointer text-slate-100">{text.replaySummary}</summary>
            <pre className="mt-3 max-h-60 overflow-auto whitespace-pre-wrap break-words text-[11px] text-slate-400">
              {compactJson({
                ledger: readRecord(prediction.replay, "ledger"),
                rule_drift: readBool(prediction.replay, "rule_drift"),
                feedback_count: readArray(prediction.replay, "feedback").length,
                learning_signal_count: readArray(prediction.replay, "learning_signals").length,
              })}
            </pre>
          </details>
        </article>
      </aside>
    </section>
  );
}
