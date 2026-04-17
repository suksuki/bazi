import { useEffect, useState } from "react";

const NDJSON_TAIL_CAP = 120;

export type V17Frame = {
  layer?: string;
  timestamp?: string;
  payload?: {
    snapshot_kind?: string;
    render_text?: string;
    will_flash?: boolean;
    deity_scores?: Record<string, number>;
    ten_gods_absolute_intensity?: Record<string, number>;
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
    pending_decisions?: Array<{
      id?: string;
      title?: string;
      label?: string;
      source?: string;
      priority?: number;
    }>;
    god_rings?: {
      god_of_use?: string[];
      god_of_taboo?: string[];
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
}: {
  lockStartedAtMs: number | null;
  latestFrameTimestamp?: string;
  hasFinalLlmMeta: boolean;
  llmOk?: boolean;
}): boolean {
  if (lockStartedAtMs == null) return false;
  const latestFrameTs = Date.parse(String(latestFrameTimestamp || ""));
  if (Number.isNaN(latestFrameTs) || latestFrameTs < lockStartedAtMs) {
    return false;
  }
  return hasFinalLlmMeta || llmOk === false;
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
  // 将 body 序列化为稳定字符串，避免每次 render 产生新对象引用导致 effect 重新触发（SSE 重连）
  const bodyKey = JSON.stringify(body ?? null);

  useEffect(() => {
    if (!enabled || !endpoint) {
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
            const msg = `[流连接失败] HTTP ${resp.status}。请确认后端 8017 已启动，且 Next 代理 V17_BACKEND_INTERNAL_URL 指向正确（默认同机 127.0.0.1:8017）。`;
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
          setFrames([]);
        }
        const reader = resp.body.getReader();
        const decoder = new TextDecoder("utf-8");
        let buf = "";

        let localFrames: V17Frame[] = [];
        let pinnedPhysics: V17Frame | null = null;

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
      } catch (err) {
        // 仅静默正常中止；其他错误推入错误帧以供调试
        if (err instanceof DOMException && err.name === "AbortError") return;
        if (mounted) {
          setFrames((prev) => [
            ...prev,
            {
              timestamp: new Date().toISOString(),
              layer: "NARRATOR",
              payload: {
                render_text: `[流错误] ${String(err)}`,
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
  }, [enabled, endpoint, method, bodyKey]);

  return { frames };
}
