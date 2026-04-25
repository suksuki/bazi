/**
 * V17.23 — useOracleSession
 *
 * 将 OraclePage 全部状态、衍生值、事件处理从页面中抽离。
 * 页面层只做纯粹的 JSX 组合。
 */
"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  deriveV17LlmLifecycle,
  mergeV17LlmMetaForUi,
  shouldReleaseDecisionInboxLock,
  useV17WebStream,
} from "@/hooks/useV17WebStream";
import { jsonPostInit, requestJson } from "@/lib/apiClient";
import { t, type AppLanguage } from "@/lib/i18n";

// ─── Type helpers ─────────────────────────────────────────────────────────────

export type Decision = {
  id?: string;
  label?: string;
  title?: string;
  batch_id?: string;
  match_ratio?: number;
  target_god?: string;
  exclusivity_key?: string;
  source_event?: string;
  plugin_id?: string;
  source?: string;
  source_label?: string;
  priority?: number;
  status?: "APPROVED" | "REJECTED" | "pending";
  arbitration_trace?: string;
  llm_resolution_policy?: string;
  llm_resolution_result?: string;
  resolved_from_llm?: boolean;
  llm_resolution_state?: string;
  llm_terminal_state?: string;
  arbitration_mode?: "manual" | "system" | "llm" | string;
  pattern_name?: string;
  pattern_candidate?: string;
  pattern_scope?: string;
  pattern_scope_label?: string;
  pattern_mix_mode?: string;
  pattern_confidence?: number;
  pattern_confidence_percent?: number;
  pattern_confidence_label?: string;
  pattern_profile?: Array<{
    family?: string;
    gods?: string[];
    score?: number;
    share?: number;
    percent?: number;
  }>;
  physical_impact?: {
    target_god?: string;
    impact_ratio?: number;
    significance_level?: string;
    significance_weight?: number;
    intensity_level?: number;
    resistance_mod?: Record<string, unknown>;
    god_ring_bias?: {
      use_bias?: Record<string, number>;
      taboo_bias?: Record<string, number>;
      reason?: string;
    };
  };
};

type PlanActionInput = {
  plan_id?: string;
  anchor?: string;
  routing?: string;
  action?: string;
  decision_ids?: string[];
  batch_ids?: string[];
  meta?: Record<string, unknown>;
};

type PlanActionStatus = "APPROVED" | "REJECTED" | "ESCALATE" | "WITHDRAW";

export interface OracleSession {
  // --- stream frames ---
  frames: ReturnType<typeof useV17WebStream>["frames"];

  // --- session identity ---
  sessionId: string;
  running: boolean;

  // --- natal inputs (read-back for trace panel) ---
  birthTimeISO: string;
  natalGender: "male" | "female" | undefined;
  natalCalendar: "solar" | "lunar" | undefined;
  lunarIsLeapMonth: boolean;
  selectedLuckYear: number;
  setSelectedLuckYear: (y: number) => void;

  // --- decisions ---
  adoptedDecisions: Decision[];
  handleAdopted: (d: Decision & { status: "APPROVED" | "REJECTED" }) => Promise<void>;
  handleAdoptedBatch: (
    decisions: Decision[],
    status: "APPROVED" | "REJECTED",
    batchIds?: string[],
  ) => Promise<void>;
  handlePlanAction: (plan: PlanActionInput, status: PlanActionStatus) => Promise<void>;
  triggerVerdict: (reason?: string, options?: { practitionerOverrideContext?: Record<string, unknown> }) => void;
  pendingDecisionWorkCount: number;
  canAutoGenerateVerdict: boolean;
  decisionInboxLocked: boolean;
  decisionInboxLockMessage: string;

  // --- trace panel ---
  traceOpen: boolean;
  setTraceOpen: (v: boolean | ((prev: boolean) => boolean)) => void;

  // --- derived stream data ---
  hasNarrative: boolean;
  latestRenderText: string;
  physicsSnapshot: ReturnType<typeof useV17WebStream>["frames"][number] | undefined;
  llmAuditSnapshot: ReturnType<typeof useV17WebStream>["frames"][number] | undefined;
  latestNarrator: ReturnType<typeof useV17WebStream>["frames"][number] | undefined;
  narratorForAudit: ReturnType<typeof useV17WebStream>["frames"][number] | undefined;
  llmMeta: Record<string, unknown>;
  traceHits: unknown[];
  traceFacts: unknown[];
  fullTrace: Record<string, unknown> | undefined;

  // --- UI phase flags ---
  llmLifecyclePhase: ReturnType<typeof deriveV17LlmLifecycle>["phase"];
  llmStatusText: string;
  llmStatusDetail: string;
  llmTerminal: boolean;
  modelLabel: string;
  connectTickMs: number;
  lastHeartbeatStep: string;
  heartbeatHistory: ReturnType<typeof useV17WebStream>["streamState"]["heartbeatHistory"];
  streamClosed: boolean;

  // --- endpoint helpers ---
  streamEndpoint: string | null;
  streamBody: Record<string, unknown> | null;
  streamQuery: { will_proxy: string; birth_time: string; gender: string; flow_year: string; ui_lang: string };

  // --- actions ---
  startRun: (input: {
    birthTimeISO: string;
    gender: "male" | "female";
    calendarType: "solar" | "lunar";
    lunarIsLeapMonth?: boolean;
  }) => void;
  resetRun: () => void;
}

// ─── Hook ─────────────────────────────────────────────────────────────────────

const DEFAULT_ENDPOINT = "/api/v17/stream?will_proxy=stable&v17_origin=v17_rebirth";
const ORACLE_SESSION_STORAGE_KEY = "v17.oracle.current_session_id";

function refreshEndpointLanguage(endpoint: string | null | undefined, lang: AppLanguage): string {
  const raw = String(endpoint || DEFAULT_ENDPOINT);
  const [path, queryText = ""] = raw.split("?");
  const query = new URLSearchParams(queryText.split("&_pulse=")[0] || "");
  query.set("ui_lang", lang);
  return `${path}?${query.toString()}&_pulse=${Date.now()}`;
}

export function useOracleSession({ uiLanguage = "zh" }: { uiLanguage?: AppLanguage } = {}): OracleSession {
  // Session state
  const [sessionId, setSessionId] = useState("");
  const [running, setRunning] = useState(false);
  const [streamEndpoint, setStreamEndpoint] = useState<string | null>(DEFAULT_ENDPOINT);
  const [streamBody, setStreamBody] = useState<Record<string, unknown> | null>(null);

  // Natal inputs
  const [birthTimeISO, setBirthTimeISO] = useState("");
  const [natalGender, setNatalGender] = useState<"male" | "female" | undefined>(undefined);
  const [natalCalendar, setNatalCalendar] = useState<"solar" | "lunar" | undefined>(undefined);
  const [lunarIsLeapMonth, setLunarIsLeapMonth] = useState(false);
  const [selectedLuckYear, setSelectedLuckYear] = useState<number>(new Date().getFullYear());

  // Decisions
  const [adoptedDecisions, setAdoptedDecisions] = useState<Decision[]>([]);
  const [decisionLockStartedAtMs, setDecisionLockStartedAtMs] = useState<number | null>(null);
  const [decisionActionError, setDecisionActionError] = useState("");
  const [decisionDirtySinceLastVerdict, setDecisionDirtySinceLastVerdict] = useState(false);

  // Trace panel
  const [traceOpen, setTraceOpen] = useState(false);

  // Connection tick
  const [connectTickMs, setConnectTickMs] = useState(0);

  const refreshPhysicsOnly = useCallback(() => {
    setStreamEndpoint(refreshEndpointLanguage(streamEndpoint, uiLanguage));
    setStreamBody((prevBody) => ({
      ...(prevBody || {}),
      v17_origin: "v17_rebirth",
      session_id: sessionId || "default",
      suppress_narrator: true,
      user_message: "",
      ui_lang: uiLanguage,
    }));
    setRunning(true);
  }, [sessionId, streamEndpoint, uiLanguage]);

  // ── Stream ───────────────────────────────────────────────────────────────────
  const { frames, streamState } = useV17WebStream({
    endpoint: streamEndpoint,
    enabled: running,
    method: "POST",
    body: streamBody,
  });

  // ── Derived frame data ───────────────────────────────────────────────────────
  const hasNarrative = useMemo(
    () => frames.some((f) => String(f?.payload?.render_text || "").trim().length > 0),
    [frames],
  );

  const latestRenderText = useMemo(
    () =>
      String(
        [...frames]
          .reverse()
          .find((f) => String(f?.payload?.render_text || "").trim().length > 0)
          ?.payload?.render_text || "",
      ).trim(),
    [frames],
  );

  const physicsSnapshot = useMemo(
    () =>
      [...frames].reverse().find((f) => {
        if (String(f?.layer || "").toUpperCase() !== "SNAPSHOT") return false;
        const sk = String((f?.payload as { snapshot_kind?: string })?.snapshot_kind || "").trim();
        const type = String((f?.payload as { type?: string })?.type || "").trim();
        return (
          sk === "physics" ||
          sk === "physical_void" ||
          sk === "system_init_failure" ||
          type === "PHYSICS_SYNC"
        );
      }),
    [frames],
  );

  const pendingDecisionWorkCount = useMemo(() => {
    const payload = (physicsSnapshot?.payload || {}) as Record<string, unknown>;
    const pendingRows = Array.isArray(payload.pending_decisions)
      ? payload.pending_decisions
      : Array.isArray(payload.manual_inbox)
        ? payload.manual_inbox
        : Array.isArray(payload.manual_decisions)
          ? payload.manual_decisions
          : [];
    const pendingManual = pendingRows.filter((row) => {
      if (!row || typeof row !== "object") return false;
      const status = String((row as { status?: string }).status || "").trim().toUpperCase();
      return !status || status === "PENDING" || status === "AWAIT_REVIEW";
    }).length;
    const brain = payload.decision_brain_state as { plan_queue?: Array<{ status?: string }> } | undefined;
    const planQueue = Array.isArray(brain?.plan_queue) ? brain.plan_queue : [];
    const activePlans = planQueue.filter((plan) => {
      const status = String(plan?.status || "").trim().toUpperCase();
      return !status || !new Set(["COMPLETED", "DONE", "APPROVED", "REJECTED", "COMMITTED", "FAILED"]).has(status);
    }).length;
    return pendingManual + activePlans;
  }, [physicsSnapshot]);

  const canAutoGenerateVerdict = pendingDecisionWorkCount === 0;

  const llmAuditSnapshot = useMemo(
    () =>
      [...frames].reverse().find((f) => {
        if (String(f?.layer || "").toUpperCase() !== "SNAPSHOT") return false;
        return (
          String((f?.payload as { snapshot_kind?: string })?.snapshot_kind || "") ===
          "llm_audit_preview"
        );
      }),
    [frames],
  );

  const latestNarrator = useMemo(
    () => [...frames].reverse().find((f) => String(f?.layer || "").toUpperCase() === "NARRATOR"),
    [frames],
  );

  const narratorForAudit = useMemo(
    () =>
      [...frames].reverse().find((f) => {
        if (String(f?.layer || "").toUpperCase() !== "NARRATOR") return false;
        const p = f?.payload;
        if (!p) return false;
        const rt = String(p.render_text || "").trim();
        const m = (p.llm_meta || {}) as Record<string, unknown>;
        const sp = String(
          m.llm_system_prompt ||
            (m.full_prompt_trace as { system_role?: string } | undefined)?.system_role ||
            "",
        ).trim();
        const unlock = m.prompt_dead_audit_unlock === true;
        return rt.length > 0 || sp.length > 0 || unlock;
      }) ||
      [...frames].reverse().find((f) => {
        if (String(f?.layer || "").toUpperCase() !== "SNAPSHOT") return false;
        return (
          String((f?.payload as { snapshot_kind?: string })?.snapshot_kind || "") ===
          "llm_audit_preview"
        );
      }),
    [frames],
  );

  const llmMeta = mergeV17LlmMetaForUi(narratorForAudit, latestNarrator, llmAuditSnapshot) as Record<
    string,
    unknown
  >;

  const traceHits = (physicsSnapshot?.payload?.debug_trace as { hits?: unknown[] } | undefined)?.hits ?? [];
  const traceFacts = (
    latestNarrator?.payload?.source_facts ||
    (physicsSnapshot?.payload?.debug_trace as { facts?: unknown[] } | undefined)?.facts ||
    []
  ).slice(0, 32);
  const fullTrace = llmMeta.full_prompt_trace as Record<string, unknown> | undefined;

  // ── UI phase flags ───────────────────────────────────────────────────────────
  const lifecycle = deriveV17LlmLifecycle({
    running,
    llmMeta,
    latestNarrator,
    hasAuditPreview: Boolean(llmAuditSnapshot),
    streamState,
    language: uiLanguage,
  });
  const streamPartial = llmMeta.stream_partial === true;
  const hasFinalLlmMeta =
    !streamPartial &&
    typeof llmMeta.elapsed_ms === "number" &&
    !Number.isNaN(Number(llmMeta.elapsed_ms));
  const llmTerminal = ["completed", "failed", "closed_without_output"].includes(lifecycle.phase);
  const modelLabel = String(llmMeta.model || "").trim() || t(uiLanguage, "verdict.model");
  const lastHeartbeatStep = String(streamState.lastHeartbeat?.stepPosition || "").trim();
  const heartbeatHistory = streamState.heartbeatHistory;
  const streamClosed = streamState.closed;

  // ── Decision lock ────────────────────────────────────────────────────────────
  const latestFrameTimestamp = useMemo(
    () =>
      [...frames]
        .reverse()
        .find((f) => String(f?.timestamp || "").trim().length > 0)?.timestamp,
    [frames],
  );

  useEffect(() => {
    const latestFrame = [...frames].reverse()[0];
    const isPhysicsUpdate = latestFrame?.payload?.type === "PHYSICS_UPDATE" || latestFrame?.payload?.type === "PHYSICS_SYNC";
    
    if (
      shouldReleaseDecisionInboxLock({
        lockStartedAtMs: decisionLockStartedAtMs,
        latestFrameTimestamp,
        hasFinalLlmMeta,
        llmOk: llmMeta.ok as boolean | undefined,
        isPhysicsUpdate
      })
    ) {
      setDecisionLockStartedAtMs(null);
      setDecisionActionError("");
    }
  }, [frames, decisionLockStartedAtMs, latestFrameTimestamp, hasFinalLlmMeta, llmMeta.ok]);

  useEffect(() => {
    if (decisionLockStartedAtMs == null) return;
    const timerId = window.setTimeout(() => {
      setDecisionLockStartedAtMs(null);
      setDecisionActionError(t(uiLanguage, "decision.action.timeout"));
    }, 8000);
    return () => window.clearTimeout(timerId);
  }, [decisionLockStartedAtMs, uiLanguage]);

  const initialVerdictLocked =
    running && frames.length > 0 && decisionLockStartedAtMs == null && !llmTerminal;
  const decisionInboxLocked = initialVerdictLocked || decisionLockStartedAtMs != null;
  const decisionInboxLockMessage =
    decisionLockStartedAtMs != null
      ? t(uiLanguage, "decision.manual.lock.action")
      : initialVerdictLocked
        ? t(uiLanguage, "decision.manual.lock.initial")
        : decisionActionError;

  // ── Connection tick ──────────────────────────────────────────────────────────
  useEffect(() => {
    if (!running) {
      setConnectTickMs(0);
      return;
    }
    const t0 = Date.now();
    const id = window.setInterval(() => setConnectTickMs(Date.now() - t0), 80);
    return () => window.clearInterval(id);
  }, [running, streamEndpoint]);

  // ── Stream query (read-back for trace panel) ─────────────────────────────────
  const streamQuery = useMemo(() => {
    const u = streamEndpoint || "";
    try {
      const q = u.includes("?")
        ? new URLSearchParams(u.split("?")[1] || "")
        : new URLSearchParams();
      return {
        will_proxy: q.get("will_proxy") || "",
        birth_time: q.get("birth_time") || "",
        gender: q.get("gender") || "",
        flow_year: q.get("flow_year") || "",
        ui_lang: q.get("ui_lang") || "",
      };
    } catch {
      return { will_proxy: "", birth_time: "", gender: "", flow_year: "", ui_lang: "" };
    }
  }, [streamEndpoint]);

  // ── Flow year sync ───────────────────────────────────────────────────────────
  useEffect(() => {
    if (!sessionId) return;
    try {
      window.localStorage.setItem(ORACLE_SESSION_STORAGE_KEY, sessionId);
    } catch {}
  }, [sessionId]);

  useEffect(() => {
    if (!running || !birthTimeISO || !natalGender) return;
    const u = streamEndpoint ?? "";
    const m = u.match(/[?&]flow_year=(\d+)/);
    if (m && Number(m[1]) === selectedLuckYear) return;
    const query = new URLSearchParams({
      will_proxy: "stable",
      birth_time: birthTimeISO,
      gender: natalGender,
      flow_year: String(selectedLuckYear),
      ui_lang: uiLanguage,
      calendar_type: natalCalendar || "solar",
      lunar_is_leap_month: natalCalendar === "lunar" && lunarIsLeapMonth ? "1" : "0",
      v17_origin: "v17_rebirth",
    });
    setStreamEndpoint(`/api/v17/stream?${query.toString()}&_pulse=${Date.now()}`);
    setStreamBody((prevBody) => ({
      ...(prevBody || {}),
      v17_origin: "v17_rebirth",
      calendar_type: natalCalendar,
      lunar_is_leap_month: natalCalendar === "lunar" && lunarIsLeapMonth,
      session_id: sessionId || "default",
      suppress_narrator: false,
      reset_stream_cache: true,
      user_message: "",
      ui_lang: uiLanguage,
    }));
    setAdoptedDecisions([]);
    setDecisionDirtySinceLastVerdict(false);
    setDecisionLockStartedAtMs(null);
    setDecisionActionError("");
    setRunning(true);
  }, [selectedLuckYear, running, birthTimeISO, natalGender, natalCalendar, lunarIsLeapMonth, sessionId, streamEndpoint, uiLanguage]);

  // ── Actions ──────────────────────────────────────────────────────────────────
  function startRun(input: {
    birthTimeISO: string;
    gender: "male" | "female";
    calendarType: "solar" | "lunar";
    lunarIsLeapMonth?: boolean;
  }) {
    const fy = new Date().getFullYear();
    const isLeapMonth = input.calendarType === "lunar" && Boolean(input.lunarIsLeapMonth);
    const query = new URLSearchParams({
      will_proxy: "stable",
      birth_time: input.birthTimeISO,
      gender: input.gender,
      flow_year: String(fy),
      ui_lang: uiLanguage,
      calendar_type: input.calendarType,
      lunar_is_leap_month: isLeapMonth ? "1" : "0",
      v17_origin: "v17_rebirth",
    });
    const sid = globalThis.crypto?.randomUUID?.() ?? `v17_${Date.now()}_${Math.random().toString(36).slice(2)}`;
    setStreamEndpoint(`/api/v17/stream?${query.toString()}`);
    setSessionId(sid);
    setBirthTimeISO(input.birthTimeISO);
    setNatalGender(input.gender);
    setNatalCalendar(input.calendarType);
    setLunarIsLeapMonth(isLeapMonth);
    setSelectedLuckYear(fy);
    setStreamBody({
      v17_origin: "v17_rebirth",
      calendar_type: input.calendarType,
      lunar_is_leap_month: isLeapMonth,
      session_id: sid,
      reset_stream_cache: true,
      ui_lang: uiLanguage,
    });
    setDecisionLockStartedAtMs(null);
    setAdoptedDecisions([]);
    setRunning(true);
  }

  function resetRun() {
    setRunning(false);
    setStreamBody(null);
    setAdoptedDecisions([]);
    setDecisionLockStartedAtMs(null);
    setDecisionActionError("");
    setDecisionDirtySinceLastVerdict(false);
  }

  const triggerVerdict = useCallback((reason: string = t(uiLanguage, "verdict.prompt.default"), options?: { practitionerOverrideContext?: Record<string, unknown> }) => {
    setStreamEndpoint(refreshEndpointLanguage(streamEndpoint, uiLanguage));
    setStreamBody((prevBody) => ({
      ...(prevBody || {}),
      v17_origin: "v17_rebirth",
      session_id: sessionId || "default",
      suppress_narrator: false,
      user_message: String(reason || "").trim() || t(uiLanguage, "verdict.prompt.generate"),
      ui_lang: uiLanguage,
      practitioner_override_context: options?.practitionerOverrideContext || undefined,
    }));
    setRunning(true);
    setDecisionDirtySinceLastVerdict(false);
  }, [sessionId, streamEndpoint, uiLanguage]);

  function fallbackDecisionAction(item: Decision, index: number): { title: string; label: string } {
    const target = String(item.target_god || item.physical_impact?.target_god || "").trim();
    const source = String(item.source_label || item.source || item.plugin_id || "").trim();
    const rawTitle = String(item.title || "").trim();
    const rawLabel = String(item.label || "").trim();
    const title = rawTitle || rawLabel || source || `decision_${index + 1}`;
    const label = rawLabel || rawTitle || (target ? `${t(uiLanguage, "decision.manual.button")} ${target}` : title);
    return {
      title,
      label,
    };
  }

  async function handleAdoptedBatch(
    decisions: Decision[],
    status: "APPROVED" | "REJECTED",
    batchIds: string[] = [],
  ) {
    const normalized = decisions
      .map((item, index) => {
        const id = String(item.id || item.label || item.title || `d_${Date.now()}_${index}`).trim();
        const fallback = fallbackDecisionAction(item, index);
        const title = fallback.title;
        const label = fallback.label;
        return {
          ...item,
          id,
          title,
          label,
        };
      })
      .filter((item) => item.id);

    if (!normalized.length) {
      setDecisionActionError(t(uiLanguage, "decision.action.missing"));
      return;
    }
    if (decisionLockStartedAtMs != null) return;

    const ids: string[] = [];
    const seenIds = new Set<string>();
    for (const item of normalized) {
      if (item.id && !seenIds.has(item.id)) {
        seenIds.add(item.id);
        ids.push(item.id);
      }
    }

    const title = String(normalized[0]?.title || "").trim();
    const action = String(normalized[0]?.label || title || "").trim();
    if (!action || !ids.length) {
      setDecisionActionError(t(uiLanguage, "decision.action.missing_title"));
      return;
    }

    const carryImplicitBatchIds = normalized.length > 1;
    const mergedBatchIds = [
      ...(carryImplicitBatchIds
        ? normalized.map((item) => String(item.batch_id || "").trim()).filter(Boolean)
        : []),
      ...batchIds.map((item) => String(item || "").trim()).filter(Boolean),
    ];
    const uniqBatchIds = Array.from(new Set(mergedBatchIds));

    setDecisionActionError("");
    setDecisionLockStartedAtMs(Date.now());
    let actionPayload: Record<string, unknown> | null = null;

    try {
      const { data, ok } = await requestJson<Record<string, unknown>>("/api/v17/action", jsonPostInit({
          session_id: sessionId || "default",
          decision_ids: ids,
          status,
          action,
          title,
          target_god: String(normalized[0]?.target_god || "").trim() || undefined,
          physical_impact: normalized[0]?.physical_impact || undefined,
          signal: status === "APPROVED" ? "PLAN_APPROVE" : "PLAN_REJECT",
          batch_ids: uniqBatchIds.length ? uniqBatchIds : undefined,
          request_verdict: false,
          v17_origin: "v17_rebirth",
        }, { headers: { v17_origin: "v17_rebirth" } }));
      actionPayload = data;
      if (!ok || actionPayload?.ok === false) {
        const detail =
          typeof actionPayload?.detail === "string" && actionPayload.detail.trim().length > 0
            ? actionPayload.detail.trim()
            : t(uiLanguage, "decision.action.failed_short");
        throw new Error(detail);
      }
    } catch (error) {
      console.error("[V17-ACTION-ERROR]", error);
      setDecisionLockStartedAtMs(null);
      setDecisionActionError(t(uiLanguage, "decision.action.failed"));
      return;
    }

    setDecisionLockStartedAtMs(null);
    setDecisionActionError("");
    refreshPhysicsOnly();

    const signal = String(actionPayload?.signal || "").trim().toUpperCase();
    const shouldHideFromManual =
      status === "REJECTED" ||
      signal === "PLAN_APPROVE" ||
      signal === "NARRATIVE_TRIGGER" ||
      signal === "VOTE_IGNORED" ||
      signal === "CONTEXT_CONSUMED" ||
      signal === "ACTION_TAKEN" ||
      signal === "VOTE_REJECTED" ||
      signal === "VOTE_WITHDRAWN";
    if (shouldHideFromManual) {
      setAdoptedDecisions((prev) => {
        const next = [...prev];
        const idIndex = new Set(prev.map((item) => item.id).filter((value): value is string => Boolean(value)));
        for (const item of normalized) {
          if (item.id && !idIndex.has(item.id)) {
            next.push({
              id: item.id,
              label: item.label,
              title: item.title,
              target_god: String(item.target_god || "").trim() || undefined,
              physical_impact: item.physical_impact || undefined,
            });
            idIndex.add(item.id);
          }
        }
        return next;
      });
    }
    if (signal === "DECISION_NOT_FOUND") {
      setDecisionActionError(
        t(uiLanguage, "decision.action.not_found", { action }),
      );
      setDecisionDirtySinceLastVerdict(false);
      return;
    }
    setDecisionDirtySinceLastVerdict(true);
  }

  async function handleAdopted(decision: Decision & { status: "APPROVED" | "REJECTED" }) {
    await handleAdoptedBatch([decision], decision.status || "APPROVED");
  }

  async function handlePlanAction(plan: PlanActionInput, status: PlanActionStatus) {
    const planId = String(plan.plan_id || "").trim();
    const anchor = String(plan.anchor || "").trim();
    const action = String(plan.action || anchor || String(plan.meta?.action || "").trim() || planId || "PLAN_ACTION").trim();
    const batchIds = Array.isArray(plan.batch_ids)
      ? plan.batch_ids.map((id) => String(id || "").trim()).filter(Boolean)
      : [];
    const decisionIds = Array.isArray(plan.decision_ids)
      ? plan.decision_ids.map((id) => String(id || "").trim()).filter(Boolean)
      : [];
    if (!planId && !batchIds.length && !decisionIds.length) return;
    if (decisionLockStartedAtMs != null) return;

    setDecisionActionError("");
    setDecisionLockStartedAtMs(Date.now());
    let actionPayload: Record<string, unknown> | null = null;

    try {
      const signal =
        status === "APPROVED"
          ? "PLAN_APPROVE"
          : status === "ESCALATE"
            ? "PLAN_ESCALATE"
            : status === "WITHDRAW"
              ? "PLAN_WITHDRAW"
              : "PLAN_REJECT";

      const { data, ok } = await requestJson<Record<string, unknown>>("/api/v17/action", jsonPostInit({
          session_id: sessionId || "default",
          plan_id: planId || undefined,
          anchor: anchor || undefined,
          status,
          action,
          signal,
          batch_ids: batchIds.length ? batchIds : undefined,
          decision_ids: decisionIds.length ? decisionIds : undefined,
          request_verdict: false,
          v17_origin: "v17_rebirth",
        }, { headers: { v17_origin: "v17_rebirth" } }));
      actionPayload = data;
      if (!ok || actionPayload?.ok === false) {
        const detail =
          typeof actionPayload?.detail === "string" && actionPayload.detail.trim().length > 0
            ? actionPayload.detail.trim()
            : t(uiLanguage, "decision.plan.failed_short");
        throw new Error(detail);
      }
    } catch (error) {
      console.error("[V17-PLAN-ACTION-ERROR]", error);
      setDecisionLockStartedAtMs(null);
      setDecisionActionError(t(uiLanguage, "decision.plan.failed"));
      return;
    }

    setDecisionLockStartedAtMs(null);
    setDecisionActionError("");
    refreshPhysicsOnly();

    const signal = String(actionPayload?.signal || "").trim().toUpperCase();
    const shouldHideFromManual =
      status !== "APPROVED" ||
      signal === "PLAN_APPROVE" ||
      signal === "NARRATIVE_TRIGGER" ||
      signal === "VOTE_IGNORED" ||
      signal === "CONTEXT_CONSUMED" ||
      signal === "ACTION_TAKEN" ||
      signal === "VOTE_REJECTED" ||
      signal === "VOTE_WITHDRAWN";
    if (decisionIds.length && shouldHideFromManual) {
      setAdoptedDecisions((prev) => {
        const next = [...prev];
        const idx = new Set(prev.map((item) => item.id).filter((value): value is string => Boolean(value)));
        for (const id of decisionIds) {
          if (idx.has(id)) continue;
          next.push({ id, label: action, title: action });
          idx.add(id);
        }
        return next;
      });
    }
    if (signal === "DECISION_NOT_FOUND") {
      const planLabel = planId ? t(uiLanguage, "decision.plan.not_found_plan", { planId }) : "";
      setDecisionActionError(
        t(uiLanguage, "decision.plan.not_found", { plan: planLabel }),
      );
      setDecisionDirtySinceLastVerdict(false);
      return;
    }
    setDecisionDirtySinceLastVerdict(true);
  }

  useEffect(() => {
    if (!decisionDirtySinceLastVerdict) return;
    if (decisionLockStartedAtMs != null) return;
    if (!canAutoGenerateVerdict) return;
    triggerVerdict(t(uiLanguage, "verdict.prompt.after_decision"));
  }, [decisionDirtySinceLastVerdict, decisionLockStartedAtMs, canAutoGenerateVerdict, triggerVerdict, uiLanguage]);

  return {
    frames,
    sessionId,
    running,
    birthTimeISO,
    natalGender,
    natalCalendar,
    lunarIsLeapMonth,
    selectedLuckYear,
    setSelectedLuckYear,
    adoptedDecisions,
    handleAdopted,
    handleAdoptedBatch,
    handlePlanAction,
    triggerVerdict,
    pendingDecisionWorkCount,
    canAutoGenerateVerdict,
    decisionInboxLocked,
    decisionInboxLockMessage,
    traceOpen,
    setTraceOpen,
    hasNarrative,
    latestRenderText,
    physicsSnapshot,
    llmAuditSnapshot,
    latestNarrator,
    narratorForAudit,
    llmMeta,
    traceHits,
    traceFacts,
    fullTrace,
    llmLifecyclePhase: lifecycle.phase,
    llmStatusText: lifecycle.statusText,
    llmStatusDetail: lifecycle.detailText,
    llmTerminal,
    modelLabel,
    connectTickMs,
    lastHeartbeatStep,
    heartbeatHistory,
    streamClosed,
    streamEndpoint,
    streamBody,
    streamQuery,
    startRun,
    resetRun,
  };
}
