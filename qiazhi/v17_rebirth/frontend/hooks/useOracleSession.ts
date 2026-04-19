/**
 * V17.23 — useOracleSession
 *
 * 将 OraclePage 全部状态、衍生值、事件处理从页面中抽离。
 * 页面层只做纯粹的 JSX 组合。
 */
"use client";

import { useEffect, useMemo, useState } from "react";
import {
  deriveV17LlmLifecycle,
  mergeV17LlmMetaForUi,
  shouldReleaseDecisionInboxLock,
  useV17WebStream,
} from "@/hooks/useV17WebStream";

// ─── Type helpers ─────────────────────────────────────────────────────────────

export type Decision = {
  id?: string;
  label?: string;
  title?: string;
  batch_id?: string;
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
  physical_impact?: {
    target_god?: string;
    impact_ratio?: number;
    significance_level?: string;
    significance_weight?: number;
    intensity_level?: number;
    resistance_mod?: Record<string, unknown>;
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
  selectedLuckYear: number;
  setSelectedLuckYear: (y: number) => void;

  // --- decisions ---
  adoptedDecisions: Decision[];
  handleAdopted: (d: Decision & { status: "APPROVED" | "REJECTED" }) => Promise<void>;
  handleAdoptedBatch: (decisions: Decision[], status: "APPROVED" | "REJECTED") => Promise<void>;
  handlePlanAction: (plan: PlanActionInput, status: PlanActionStatus) => Promise<void>;
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
  streamQuery: { will_proxy: string; birth_time: string; gender: string; flow_year: string };

  // --- actions ---
  startRun: (input: { birthTimeISO: string; gender: "male" | "female"; calendarType: "solar" | "lunar" }) => void;
  resetRun: () => void;
}

// ─── Hook ─────────────────────────────────────────────────────────────────────

const DEFAULT_ENDPOINT = "/api/v17/stream?will_proxy=stable&v17_origin=v17_rebirth";
const ORACLE_SESSION_STORAGE_KEY = "v17.oracle.current_session_id";

export function useOracleSession(): OracleSession {
  // Session state
  const [sessionId, setSessionId] = useState("");
  const [running, setRunning] = useState(false);
  const [streamEndpoint, setStreamEndpoint] = useState<string | null>(DEFAULT_ENDPOINT);
  const [streamBody, setStreamBody] = useState<Record<string, unknown> | null>(null);

  // Natal inputs
  const [birthTimeISO, setBirthTimeISO] = useState("");
  const [natalGender, setNatalGender] = useState<"male" | "female" | undefined>(undefined);
  const [natalCalendar, setNatalCalendar] = useState<"solar" | "lunar" | undefined>(undefined);
  const [selectedLuckYear, setSelectedLuckYear] = useState<number>(new Date().getFullYear());

  // Decisions
  const [adoptedDecisions, setAdoptedDecisions] = useState<Decision[]>([]);
  const [decisionLockStartedAtMs, setDecisionLockStartedAtMs] = useState<number | null>(null);
  const [decisionActionError, setDecisionActionError] = useState("");

  // Trace panel
  const [traceOpen, setTraceOpen] = useState(false);

  // Connection tick
  const [connectTickMs, setConnectTickMs] = useState(0);

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
  });
  const streamPartial = llmMeta.stream_partial === true;
  const hasFinalLlmMeta =
    !streamPartial &&
    typeof llmMeta.elapsed_ms === "number" &&
    !Number.isNaN(Number(llmMeta.elapsed_ms));
  const llmTerminal = ["completed", "failed", "closed_without_output"].includes(lifecycle.phase);
  const modelLabel = String(llmMeta.model || "").trim() || "叙事引擎";
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
      setDecisionActionError("动作回执超时，已解除锁定，请重试该 decision item。");
    }, 8000);
    return () => window.clearTimeout(timerId);
  }, [decisionLockStartedAtMs]);

  const initialVerdictLocked =
    running && frames.length > 0 && decisionLockStartedAtMs == null && !llmTerminal;
  const decisionInboxLocked = initialVerdictLocked || decisionLockStartedAtMs != null;
  const decisionInboxLockMessage =
    decisionLockStartedAtMs != null
      ? "上一条决策仍在织造中，待 LLM 完成后才可选择新的 item。"
      : initialVerdictLocked
        ? "首轮判词仍在织造中，待 LLM 完成后才可选择 decision item。"
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
      };
    } catch {
      return { will_proxy: "", birth_time: "", gender: "", flow_year: "" };
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
      v17_origin: "v17_rebirth",
    });
    setStreamEndpoint(`/api/v17/stream?${query.toString()}`);
  }, [selectedLuckYear, running, birthTimeISO, natalGender, streamEndpoint]);

  // ── Actions ──────────────────────────────────────────────────────────────────
  function startRun(input: {
    birthTimeISO: string;
    gender: "male" | "female";
    calendarType: "solar" | "lunar";
  }) {
    const fy = new Date().getFullYear();
    const query = new URLSearchParams({
      will_proxy: "stable",
      birth_time: input.birthTimeISO,
      gender: input.gender,
      flow_year: String(fy),
      v17_origin: "v17_rebirth",
    });
    const sid = crypto.randomUUID();
    setStreamEndpoint(`/api/v17/stream?${query.toString()}`);
    setSessionId(sid);
    setBirthTimeISO(input.birthTimeISO);
    setNatalGender(input.gender);
    setNatalCalendar(input.calendarType);
    setSelectedLuckYear(fy);
    setStreamBody({ v17_origin: "v17_rebirth", calendar_type: input.calendarType, session_id: sid });
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
  }

  async function handleAdoptedBatch(decisions: Decision[], status: "APPROVED" | "REJECTED") {
    const normalized = decisions
      .map((item, index) => {
        const id = String(item.id || item.label || item.title || `d_${Date.now()}_${index}`).trim();
        const title = String(item.title || "").trim();
        const label = String(item.label || title || "").trim();
        return {
          ...item,
          id,
          title,
          label,
        };
      })
      .filter((item) => item.id && (item.label || item.title));

    if (!normalized.length || decisionLockStartedAtMs != null) return;

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
    if (!action || !ids.length) return;

    setDecisionActionError("");
    setDecisionLockStartedAtMs(Date.now());

    try {
      const response = await fetch("/api/v17/action", {
        method: "POST",
        headers: { "Content-Type": "application/json", "v17_origin": "v17_rebirth" },
      body: JSON.stringify({
          session_id: sessionId || "default",
          decision_ids: ids,
          status,
          action,
          title,
          target_god: String(normalized[0]?.target_god || "").trim() || undefined,
          physical_impact: normalized[0]?.physical_impact || undefined,
          signal: status === "APPROVED" ? "PLAN_APPROVE" : "PLAN_REJECT",
          batch_ids: normalized[0]?.batch_id ? [normalized[0]?.batch_id] : undefined,
          v17_origin: "v17_rebirth",
        }),
      });
      const payload = await response.json().catch(() => null);
      if (!response.ok || payload?.ok === false) {
        const detail =
          typeof payload?.detail === "string" && payload.detail.trim().length > 0
            ? payload.detail.trim()
            : "动作提交失败";
        throw new Error(detail);
      }
    } catch (error) {
      console.error("[V17-ACTION-ERROR]", error);
      setDecisionLockStartedAtMs(null);
      setDecisionActionError("动作提交失败，已解除锁定，请稍后重试。");
      return;
    }

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
        const base = streamEndpoint?.split("&_pulse=")[0] || DEFAULT_ENDPOINT;
        setStreamEndpoint(`${base}&_pulse=${Date.now()}`);
        setStreamBody((prevBody) => ({
          ...(prevBody || {}),
          v17_origin: "v17_rebirth",
          session_id: sessionId || "default",
          user_message: action,
          decisions: next,
        }));
      setRunning(true);
      return next;
    });
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

    try {
      const signal =
        status === "APPROVED"
          ? "PLAN_APPROVE"
          : status === "ESCALATE"
            ? "PLAN_ESCALATE"
            : status === "WITHDRAW"
              ? "PLAN_WITHDRAW"
              : "PLAN_REJECT";

      const response = await fetch("/api/v17/action", {
        method: "POST",
        headers: { "Content-Type": "application/json", "v17_origin": "v17_rebirth" },
        body: JSON.stringify({
          session_id: sessionId || "default",
          plan_id: planId || undefined,
          anchor: anchor || undefined,
          status,
          action,
          signal,
          batch_ids: batchIds.length ? batchIds : undefined,
          decision_ids: decisionIds.length ? decisionIds : undefined,
          v17_origin: "v17_rebirth",
        }),
      });
      const payload = await response.json().catch(() => null);
      if (!response.ok || payload?.ok === false) {
        const detail =
          typeof payload?.detail === "string" && payload.detail.trim().length > 0
            ? payload.detail.trim()
            : "决策计划提交失败";
        throw new Error(detail);
      }
    } catch (error) {
      console.error("[V17-PLAN-ACTION-ERROR]", error);
      setDecisionLockStartedAtMs(null);
      setDecisionActionError("决策计划提交失败，已解除锁定，请稍后重试。");
      return;
    }

    const base = streamEndpoint?.split("&_pulse=")[0] || DEFAULT_ENDPOINT;
    setStreamEndpoint(`${base}&_pulse=${Date.now()}`);
    setStreamBody((prevBody) => ({
      ...(prevBody || {}),
      v17_origin: "v17_rebirth",
      session_id: sessionId || "default",
      user_message: action,
    }));
    if (decisionIds.length) {
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
    setRunning(true);
  }

  return {
    frames,
    sessionId,
    running,
    birthTimeISO,
    natalGender,
    natalCalendar,
    selectedLuckYear,
    setSelectedLuckYear,
    adoptedDecisions,
    handleAdopted,
    handleAdoptedBatch,
    handlePlanAction,
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
