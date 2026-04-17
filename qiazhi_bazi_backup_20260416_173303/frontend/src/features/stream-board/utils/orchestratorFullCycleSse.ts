"use client";

/** 与后端 `POST /v1/orchestrator/full-cycle/stream`（`text/event-stream`）对齐的客户端解析器 */

export type OrchestratorSseHandlers = {
  onPhysicsUpdate?: (data: Record<string, unknown>) => void;
  onVfDiscovered?: (data: { line?: string }) => void;
  onAuditPulse?: (data: { fragment?: string }) => void;
  onFinalVerdictStream?: (data: { token?: string }) => void;
  onComplete?: (data: Record<string, unknown>) => void;
};

/**
 * 读取 fetch 流式响应体，按 SSE 帧分发；仅在收到 `event: complete` 时调用 `onComplete`。
 */
export type ConsumeOrchestratorSseOptions = {
  signal?: AbortSignal;
};

export async function consumeOrchestratorFullCycleSse(
  response: Response,
  handlers: OrchestratorSseHandlers,
  opts?: ConsumeOrchestratorSseOptions,
): Promise<void> {
  const body = response.body;
  if (!body) throw new Error("orchestrator SSE: empty body");
  opts?.signal?.throwIfAborted();
  const reader = body.getReader();
  const decoder = new TextDecoder();
  let buf = "";
  try {
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buf += decoder.decode(value, { stream: true });
    for (;;) {
      const sep = buf.indexOf("\n\n");
      if (sep < 0) break;
      const block = buf.slice(0, sep);
      buf = buf.slice(sep + 2);
      let eventName = "";
      const dataLines: string[] = [];
      for (const line of block.split("\n")) {
        if (line.startsWith("event:")) {
          eventName = line.slice(6).trim();
        } else if (line.startsWith("data:")) {
          dataLines.push(line.slice(5).trimStart());
        }
      }
      const rawJson = dataLines.join("\n").trim();
      if (!rawJson) continue;
      let payload: Record<string, unknown>;
      try {
        payload = JSON.parse(rawJson) as Record<string, unknown>;
      } catch {
        continue;
      }
      switch (eventName) {
        case "physics_update":
          handlers.onPhysicsUpdate?.(payload);
          break;
        case "vf_discovered":
          handlers.onVfDiscovered?.(payload as { line?: string });
          break;
        case "audit_pulse":
          handlers.onAuditPulse?.(payload as { fragment?: string });
          break;
        case "final_verdict_stream":
          handlers.onFinalVerdictStream?.(payload as { token?: string });
          break;
        case "complete":
          handlers.onComplete?.(payload);
          break;
        default:
          break;
      }
    }
  }
  } catch (e) {
    if (opts?.signal?.aborted) return;
    throw e;
  }
}
