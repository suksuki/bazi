import { useEffect, useRef, useState } from "react";
import type { PlanDecisionClaim, PlanDecisionRoutingFeatures } from "@/types/decisionBrain";
import { t, type AppLanguage } from "@/lib/i18n";

const NDJSON_TAIL_CAP = 120;

export type V17HeartbeatSnapshot = {
  stepPosition: string;
  idleSec: number;
  timestamp?: string;
};

export type V17StreamState = {
  closed: boolean;
  closeReason: "idle" | "http_error" | "runtime_error" | "stream_eof" | "aborted";
  lastHeartbeat?: V17HeartbeatSnapshot;
  heartbeatHistory: V17HeartbeatSnapshot[];
};

export type V17LlmLifecyclePhase =
  | "idle"
  | "connecting"
  | "awaiting_first_token"
  | "streaming"
  | "completed"
  | "failed"
  | "closed_without_output";

export type V17Frame = {
  layer?: string;
  timestamp?: string;
  payload?: {
    type?: string;
    snapshot_kind?: string;
    render_text?: string;
    will_flash?: boolean;
    ten_gods_base_l0?: Record<string, number>;
    ten_gods_runtime?: Record<string, number>;
    ten_gods_narrative?: Record<string, number>;
    deity_scores?: Record<string, number>;
    ten_gods_absolute_intensity?: Record<string, number>;
    ten_gods_ledger?: Record<string, unknown[]>;
    ten_gods_decomposition_l0?: Record<string, unknown>;
    projection_bridge_protocol?: Record<string, unknown>;
    total_energy_index?: number;
    four_pillars?: {
      year?: string;
      month?: string;
      day?: string;
      hour?: string;
    };
    luck_pillar?: string;
    flow_pillar?: string;
    flow_year?: number;
    debug_trace?: {
      hits?: string[];
      facts?: string[];
    };
    llm_meta?: {
      ok?: boolean;
      engine_state?: string;
      elapsed_ms?: number;
      model?: string;
      provider?: string;
      error_id?: string;
      error?: string;
      facts?: string[];
      stream_partial?: boolean;
      stream?: boolean;
      llm_system_prompt?: string;
      llm_user_prompt?: string;
      llm_request_messages?: Array<{ role?: string; content?: string }>;
      llm_reply?: string;
      llm_raw_response_json?: string;
      full_prompt_trace?: {
        system_role?: string;
        user_role?: string;
        decision_anchor_literal_in_system_role?: boolean;
        decision_anchor_len?: number;
        request_messages?: Array<{ role?: string; content?: string }>;
      };
      llm_endpoint_host?: string;
      llm_meta_redacted?: boolean;
    };
    source_facts?: string[];
    manual_decisions?: Array<{
      id?: string;
      title?: string;
      label?: string;
      source?: string;
      priority?: number;
    }>;
    auto_resolutions?: Array<Record<string, unknown>>;
    llm_arbitration_context?: Array<Record<string, unknown>>;
    pending_decisions?: Array<{
      id?: string;
      title?: string;
      label?: string;
      source?: string;
      priority?: number;
    }>;
    all_decisions?: Array<{
      id?: string;
      title?: string;
      label?: string;
      source?: string;
      priority?: number;
      arbitration_mode?: string;
    }>;
    god_rings?: {
      god_of_use?: string[];
      god_of_taboo?: string[];
      tongguan_gods?: string[];
      source?: string;
      mode?: string;
      display_mode?: string;
      label_of_use?: string;
      label_of_taboo?: string;
      confidence?: number;
      core_path_count?: number;
      core_use_candidates?: Array<Record<string, unknown>>;
      core_taboo_candidates?: Array<Record<string, unknown>>;
      dual_role_candidates?: Array<Record<string, unknown>>;
      judgement_bias?: {
        use_bias?: Record<string, number>;
        taboo_bias?: Record<string, number>;
      };
      judgement_bias_entries?: Array<Record<string, unknown>>;
      judgement_bias_protocol?: Record<string, unknown>;
      blind_theme?: Record<string, unknown>;
      blind_bias?: Record<string, unknown>;
      blind_bias_protocol?: Record<string, unknown>;
      stage_bias?: Record<string, Record<string, number>>;
      stage_bias_protocol?: Record<string, unknown>;
      effect_scores?: Record<string, Record<string, unknown>>;
      core_graph_meta?: Record<string, unknown>;
      core_paths_preview?: Array<Record<string, unknown>>;
      positive_work?: Record<string, unknown>;
      negative_work?: Record<string, unknown>;
    };
    plugins?: {
      hits?: unknown[];
      rows?: Array<Record<string, unknown>>;
      evidence?: Array<Record<string, unknown>>;
      statuses?: Array<Record<string, unknown>>;
      claims?: Array<Record<string, unknown>>;
      conflicts?: Array<Record<string, unknown>>;
      conflict_resolutions?: Array<Record<string, unknown>>;
      knowledge_snapshot?: Record<string, unknown>;
      brain_action_queue?: Array<Record<string, unknown>>;
    };
    evidence_bundle?: {
      contract?: string;
      summary?: Record<string, unknown>;
      items?: Array<Record<string, unknown>>;
    };
    decision_brain_state?: {
      plan_queue?: Array<{
        plan_id?: string;
        anchor?: string;
        status?: string;
        routing?: string;
        routing_reason?: string;
        routing_policy?: string;
        routing_features?: PlanDecisionRoutingFeatures;
        routing_claim?: PlanDecisionClaim;
        decision_ids?: string[];
        impact_summary?: Record<string, number>;
        meta?: Record<string, unknown>;
        created_at?: string;
        updated_at?: string;
        batch_ids?: string[];
      }>;
    };
  };
};

/** 首帧格局物理 SNAPSHOT（含完整四柱）；用于在环形缓冲中钉住，避免被大量 NARRATOR 挤出。 */
export function isCanonPhysicsSnapshot(f: V17Frame): boolean {
  if (String(f?.layer || "").toUpperCase() !== "SNAPSHOT") return false;
  const sk = String((f?.payload as { snapshot_kind?: string })?.snapshot_kind || "").trim();
  if (sk !== "physics") return false;
  const fp = (f?.payload as { four_pillars?: Record<string, unknown> })?.four_pillars;
  if (!fp || typeof fp !== "object") return false;
  const g = (k: string) => String((fp as Record<string, unknown>)[k] ?? "").trim();
  return g("year").length >= 2 && g("month").length >= 2 && g("day").length >= 2 && g("hour").length >= 2;
}

/** 任意含 payload.llm_meta 的 NDJSON 帧，供 UI 合并展示用 */
export type V17LlmFrameRef = {
  payload?: {
    llm_meta?: Record<string, unknown>;
    full_prompt_trace?: unknown;
    llm_system_prompt?: unknown;
    llm_user_prompt?: unknown;
    llm_raw_response_json?: unknown;
    llm_reply?: unknown;
  };
};

/**
 * 流式过程中「最新 NARRATOR」往往只有 render_text，而 full_prompt_trace 只在 llm_audit_preview 下发过；
 * 合并后因果面板能稳定看到 System/User，而不会误显示「未携带」。
 */
export function mergeV17LlmMetaForUi(
  narratorAudit?: V17LlmFrameRef,
  latestNarr?: V17LlmFrameRef,
  auditSnap?: V17LlmFrameRef,
): Record<string, unknown> {
  const base = ((narratorAudit?.payload?.llm_meta ?? latestNarr?.payload?.llm_meta) ?? {}) as Record<string, unknown>;
  const auditPayload = (auditSnap?.payload ?? {}) as Record<string, unknown>;
  const auditLm = (auditPayload.llm_meta ?? {}) as Record<string, unknown>;
  return {
    ...auditLm,
    ...base,
    full_prompt_trace:
      base.full_prompt_trace ?? auditLm.full_prompt_trace ?? auditPayload.full_prompt_trace,
    llm_system_prompt: String(
      base.llm_system_prompt ?? auditLm.llm_system_prompt ?? auditPayload.llm_system_prompt ?? "",
    ),
    llm_user_prompt: String(
      base.llm_user_prompt ?? auditLm.llm_user_prompt ?? auditPayload.llm_user_prompt ?? "",
    ),
    llm_raw_response_json: String(
      base.llm_raw_response_json ??
        auditLm.llm_raw_response_json ??
        auditPayload.llm_raw_response_json ??
        "",
    ),
    llm_reply: String(base.llm_reply ?? auditLm.llm_reply ?? auditPayload.llm_reply ?? ""),
  };
}

export function shouldReleaseDecisionInboxLock({
  lockStartedAtMs,
  latestFrameTimestamp,
  hasFinalLlmMeta,
  llmOk,
  isPhysicsUpdate,
}: {
  lockStartedAtMs: number | null;
  latestFrameTimestamp?: string;
  hasFinalLlmMeta: boolean;
  llmOk?: boolean;
  isPhysicsUpdate?: boolean;
}): boolean {
  if (lockStartedAtMs == null) return false;
  
  // V17.50: 如果是物理同步帧，立即释放锁
  if (isPhysicsUpdate) return true;
  
  const latestFrameTs = Date.parse(String(latestFrameTimestamp || ""));
  // V17.65: 增加 3 秒的时差容忍度，防止由于服务器时钟滞后导致的决策锁死
  const isAfterLock = !Number.isNaN(latestFrameTs) && latestFrameTs > (lockStartedAtMs - 3000);
  
  if (hasFinalLlmMeta || llmOk === false) {
    // LLM 已完成，只要不是明显陈旧的帧就释放
    return isAfterLock || !latestFrameTimestamp;
  }
  
  return false;
}

export function deriveV17LlmLifecycle({
  running,
  llmMeta,
  latestNarrator,
  hasAuditPreview,
  streamState,
  language = "zh",
}: {
  running: boolean;
  llmMeta: Record<string, unknown>;
  latestNarrator?: { payload?: Record<string, unknown> } | undefined;
  hasAuditPreview: boolean;
  streamState: V17StreamState;
  language?: AppLanguage;
}): {
  phase: V17LlmLifecyclePhase;
  statusText: string;
  detailText: string;
} {
  const modelLabel = String(llmMeta.model || llmMeta.llm_endpoint_host || t(language, "verdict.model")).trim() || t(language, "verdict.model");
  const engineState = String(llmMeta.engine_state || "").trim();
  const rhythmBeat = String(llmMeta["叙事节拍"] || "").trim();
  const streamPartial = llmMeta.stream_partial === true;
  const hasFinalLlmMeta =
    !streamPartial &&
    typeof llmMeta.elapsed_ms === "number" &&
    !Number.isNaN(Number(llmMeta.elapsed_ms));
  const latestNarratorPayload =
    latestNarrator && typeof latestNarrator === "object" ? latestNarrator.payload ?? {} : {};
  const hasNarratorFrame = Boolean(latestNarrator);
  const narratorText = String(latestNarratorPayload.render_text || "").trim();
  const hasNarratorText = narratorText.length > 0;
  const heartbeatStep = String(streamState.lastHeartbeat?.stepPosition || "").trim();
  const waitingUpstream =
    hasAuditPreview ||
    hasNarratorFrame ||
    heartbeatStep.startsWith("NARRATOR:") ||
    heartbeatStep.startsWith("SNAPSHOT:llm_audit_preview");

  if (!running) {
    return { phase: "idle", statusText: t(language, "verdict.status.idle"), detailText: t(language, "verdict.detail.idle") };
  }
  if (llmMeta.ok === false) {
    return {
      phase: "failed",
      statusText: String(llmMeta.error || engineState || t(language, "verdict.status.failed")),
      detailText: t(language, "verdict.detail.failed", { model: modelLabel }),
    };
  }
  if (hasFinalLlmMeta) {
    return {
      phase: "completed",
      statusText: t(language, "verdict.status.completed"),
      detailText: `${modelLabel} · ${Number(llmMeta.elapsed_ms || 0)} ms`,
    };
  }
  if (streamState.closed) {
    return {
      phase: "closed_without_output",
      statusText: t(language, "verdict.status.closed_without_output"),
      detailText: heartbeatStep || streamState.closeReason,
    };
  }
  if (engineState === "awaiting_first_token" || rhythmBeat === "已联通") {
    return {
      phase: "awaiting_first_token",
      statusText: t(language, "verdict.status.awaiting_first_token"),
      detailText: heartbeatStep || engineState || rhythmBeat,
    };
  }
  if (engineState === "stream_stalled") {
    return {
      phase: "streaming",
      statusText: t(language, "verdict.status.stream_stalled"),
      detailText: heartbeatStep || engineState,
    };
  }
  if (streamPartial && hasNarratorText) {
    return {
      phase: "streaming",
      statusText: t(language, "verdict.status.streaming"),
      detailText: heartbeatStep || engineState || "NARRATOR:streaming_partial",
    };
  }
  if (waitingUpstream) {
    return {
      phase: "awaiting_first_token",
      statusText: t(language, "verdict.status.awaiting_dispatched"),
      detailText: heartbeatStep || engineState || "AUDIT_PREVIEW",
    };
  }
  return {
    phase: "connecting",
    statusText: t(language, "verdict.status.connecting", { model: modelLabel }),
    detailText: t(language, "verdict.detail.connecting"),
  };
}

export function useV17WebStream({
  endpoint = "/api/v17/stream?will_proxy=stable&v17_origin=v17_rebirth",
  enabled = true,
  method = "GET",
  body,
}: {
  endpoint?: string | null;
  enabled?: boolean;
  method?: "GET" | "POST";
  body?: Record<string, unknown> | null;
} = {}) {
  const [frames, setFrames] = useState<V17Frame[]>([]);
  const [streamState, setStreamState] = useState<V17StreamState>({
    closed: false,
    closeReason: "idle",
    heartbeatHistory: [],
  });
  const framesRef = useRef<V17Frame[]>([]);
  const syncOnlyMode = body?.suppress_narrator === true;
  const resetVisualCache = body?.reset_stream_cache === true;
  const streamLanguage = (body?.ui_lang === "en" || body?.ui_lang === "ko" || body?.ui_lang === "zh"
    ? body.ui_lang
    : "zh") as AppLanguage;

  useEffect(() => {
    framesRef.current = frames;
  }, [frames]);

  // 将 body 序列化为稳定字符串，避免每次 render 产生新对象引用导致 effect 重新触发（SSE 重连）
  const bodyKey = JSON.stringify(body ?? null);

  useEffect(() => {
    if (!enabled || !endpoint) {
      setStreamState({ closed: false, closeReason: "idle", heartbeatHistory: [] });
      return;
    }
    const resolvedEndpoint = endpoint;
    let mounted = true;
    const aborter = new AbortController();

    async function run() {
      try {
        const resp = await fetch(resolvedEndpoint, {
          method,
          signal: aborter.signal,
          headers: method === "POST" ? { "Content-Type": "application/json" } : undefined,
          body: method === "POST" ? bodyKey : undefined,
        });
        if (!resp.ok || !resp.body) {
          if (mounted) {
            setStreamState({ closed: true, closeReason: "http_error", heartbeatHistory: [] });
            const msg =
              streamLanguage === "en"
                ? `[Stream connection failed] HTTP ${resp.status}. Please confirm backend 8017 is running and Next proxy V17_BACKEND_INTERNAL_URL points to the correct target (default same-host 127.0.0.1:8017).`
                : streamLanguage === "ko"
                  ? `[스트림 연결 실패] HTTP ${resp.status}. 백엔드 8017이 실행 중이고 Next 프록시 V17_BACKEND_INTERNAL_URL이 올바른 대상(기본 동일 호스트 127.0.0.1:8017)을 가리키는지 확인하세요.`
                  : `[流连接失败] HTTP ${resp.status}。请确认后端 8017 已启动，且 Next 代理 V17_BACKEND_INTERNAL_URL 指向正确（默认同机 127.0.0.1:8017）。`;
            setFrames((prev) => [
              ...prev,
              {
                timestamp: new Date().toISOString(),
                layer: "NARRATOR",
                payload: { render_text: msg, llm_meta: { ok: false, engine_state: "stream_http_error" } },
              },
            ]);
          }
          return;
        }
        if (mounted) {
          if (resetVisualCache && !syncOnlyMode) {
            setFrames([]);
          }
          // Keep visual cache until the first new frame arrives.
          setStreamState((prev) => ({
            ...prev,
            closed: false,
            closeReason: "idle",
            heartbeatHistory: syncOnlyMode ? prev.heartbeatHistory : [],
          }));
        }
        const reader = resp.body.getReader();
        const decoder = new TextDecoder("utf-8");
        let buf = "";

        let localFrames: V17Frame[] = syncOnlyMode ? [...framesRef.current] : resetVisualCache ? [] : [];
        let pinnedPhysics: V17Frame | null = localFrames.find(isCanonPhysicsSnapshot) || null;

        while (mounted) {
          const { value, done } = await reader.read();
          if (done) break;
          buf += decoder.decode(value, { stream: true });
          const rows = buf.split("\n");
          buf = rows.pop() || "";
          for (const line of rows) {
            const s = String(line || "").trim();
            if (!s) continue;
            try {
              const frame = JSON.parse(s) as V17Frame;
              if (String(frame.layer || "").toUpperCase() === "HEARTBEAT") {
                if (mounted) {
                  const payload = (frame.payload ?? {}) as Record<string, unknown>;
                  setStreamState((prev) => ({
                    ...prev,
                    lastHeartbeat: {
                      stepPosition: String(payload.step_position || "HEARTBEAT"),
                      idleSec: Number(payload.idle_sec || 0),
                      timestamp: frame.timestamp,
                    },
                    heartbeatHistory: [
                      ...prev.heartbeatHistory,
                      {
                        stepPosition: String(payload.step_position || "HEARTBEAT"),
                        idleSec: Number(payload.idle_sec || 0),
                        timestamp: frame.timestamp,
                      },
                    ].slice(-8),
                  }));
                }
                continue;
              }
              if (isCanonPhysicsSnapshot(frame)) {
                pinnedPhysics = frame;
              }
              localFrames = [...localFrames, frame].slice(-NDJSON_TAIL_CAP);
              if (pinnedPhysics != null && !localFrames.some(isCanonPhysicsSnapshot)) {
                // 必须保留尾部最新 NARRATOR；slice(0,119) 会丢掉刚 append 的最后一帧，判词会「被掐断」。
                localFrames = [pinnedPhysics, ...localFrames.slice(-(NDJSON_TAIL_CAP - 1))];
              }
              setFrames(localFrames);
            } catch {
              // ignore malformed chunk
            }
          }
        }
        if (mounted) {
          setStreamState((prev) =>
            syncOnlyMode
              ? {
                  ...prev,
                  closed: false,
                  closeReason: "idle",
                }
              : {
                  ...prev,
                  closed: true,
                  closeReason: aborter.signal.aborted ? "aborted" : "stream_eof",
                },
          );
        }
      } catch (err) {
        // 仅静默正常中止；其他错误推入错误帧以供调试
        if (err instanceof DOMException && err.name === "AbortError") {
          if (mounted) {
            setStreamState((prev) => ({ ...prev, closed: true, closeReason: "aborted" }));
          }
          return;
        }
        if (mounted) {
          setStreamState((prev) => ({ ...prev, closed: true, closeReason: "runtime_error" }));
          setFrames((prev) => [
            ...prev,
            {
              timestamp: new Date().toISOString(),
              layer: "NARRATOR",
              payload: {
                render_text:
                  streamLanguage === "en"
                    ? `[Stream error] ${String(err)}`
                    : streamLanguage === "ko"
                      ? `[스트림 오류] ${String(err)}`
                      : `[流错误] ${String(err)}`,
                llm_meta: { ok: false, engine_state: "stream_runtime_error" },
              },
            },
          ]);
        }
      }
    }

    // Do not setFrames([]) to keep the visual cache intact if moving between modes manually
    void run();
    return () => {
      mounted = false;
      aborter.abort();
    };
  }, [enabled, endpoint, method, bodyKey, syncOnlyMode, resetVisualCache, streamLanguage]);

  return { frames, streamState };
}
