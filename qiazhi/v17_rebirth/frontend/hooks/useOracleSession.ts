/**
 * V17.23 — useOracleSession
 *
 * 将 OraclePage 全部状态、衍生值、事件处理从页面中抽离。
 * 页面层只做纯粹的 JSX 组合。
 */
"use client";

import { useEffect, useMemo, useState } from "react";
import {
  mergeV17LlmMetaForUi,
  shouldReleaseDecisionInboxLock,
  useV17WebStream,
} from "@/hooks/useV17WebStream";

// ─── Type helpers ─────────────────────────────────────────────────────────────

export type Decision = { id: string; label: string };

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
  handleAdopted: (d: { id?: string; label?: string; title?: string }) => void;
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
  connectPhase: boolean;
  collapsePhase: boolean;
  llmTerminal: boolean;
  modelLabel: string;
  connectTickMs: number;

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

  // Trace panel
  const [traceOpen, setTraceOpen] = useState(false);

  // Connection tick
  const [connectTickMs, setConnectTickMs] = useState(0);

  // ── Stream ───────────────────────────────────────────────────────────────────
  const { frames } = useV17WebStream({
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
        return sk === "physics" || sk === "physical_void" || sk === "system_init_failure";
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
  const narratorHasChunk = Boolean(String(latestNarrator?.payload?.render_text || "").trim());
  const streamPartial = llmMeta.stream_partial === true;
  const hasFinalLlmMeta =
    !streamPartial &&
    typeof llmMeta.elapsed_ms === "number" &&
    !Number.isNaN(Number(llmMeta.elapsed_ms));
  const llmTerminal = hasFinalLlmMeta || llmMeta.ok === false;
  const modelLabel = String(llmMeta.model || "").trim() || "叙事引擎";
  const connectPhase = running && !narratorHasChunk;
  const collapsePhase = running && narratorHasChunk && !hasFinalLlmMeta;

  // ── Decision lock ────────────────────────────────────────────────────────────
  const latestFrameTimestamp = useMemo(
    () =>
      [...frames]
        .reverse()
        .find((f) => String(f?.timestamp || "").trim().length > 0)?.timestamp,
    [frames],
  );

  useEffect(() => {
    if (
      shouldReleaseDecisionInboxLock({
        lockStartedAtMs: decisionLockStartedAtMs,
        latestFrameTimestamp,
        hasFinalLlmMeta,
        llmOk: llmMeta.ok as boolean | undefined,
      })
    ) {
      setDecisionLockStartedAtMs(null);
    }
  }, [decisionLockStartedAtMs, latestFrameTimestamp, hasFinalLlmMeta, llmMeta.ok]);

  const initialVerdictLocked =
    running && frames.length > 0 && decisionLockStartedAtMs == null && !llmTerminal;
  const decisionInboxLocked = initialVerdictLocked || decisionLockStartedAtMs != null;
  const decisionInboxLockMessage =
    decisionLockStartedAtMs != null
      ? "上一条决策仍在织造中，待 LLM 完成后才可选择新的 item。"
      : initialVerdictLocked
        ? "首轮判词仍在织造中，待 LLM 完成后才可选择 decision item。"
        : "";

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
  }

  function handleAdopted(decision: { id?: string; label?: string; title?: string }) {
    const id = String(decision.id || decision.title || `d_${Date.now()}`);
    const label = String(decision.label || decision.title || "").trim();
    if (!label || decisionLockStartedAtMs != null) return;
    setDecisionLockStartedAtMs(Date.now());
    setAdoptedDecisions((prev) => {
      if (prev.some((x) => x.id === id)) return prev;
      const next = [...prev, { id, label }];
      const base =
        streamEndpoint?.split("&_pulse=")[0] || DEFAULT_ENDPOINT;
      setStreamEndpoint(`${base}&_pulse=${Date.now()}`);
      setStreamBody((prevBody) => ({
        ...(prevBody || {}),
        v17_origin: "v17_rebirth",
        session_id: sessionId || "default",
        user_message: label,
        decisions: next,
      }));
      return next;
    });
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
    connectPhase,
    collapsePhase,
    llmTerminal,
    modelLabel,
    connectTickMs,
    streamEndpoint,
    streamBody,
    streamQuery,
    startRun,
    resetRun,
  };
}
