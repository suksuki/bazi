import type { LabLlmRoundSnapshot } from "@/features/stream-board/stores/LabSessionContext";

export function parseFirstObservationLlmFromAnalyze(data: Record<string, unknown>): LabLlmRoundSnapshot | undefined {
  const fo = data.first_observation_llm;
  if (!fo || typeof fo !== "object" || Array.isArray(fo)) return undefined;
  const o = fo as Record<string, unknown>;
  const messagesRaw = o.messages;
  const messages = Array.isArray(messagesRaw)
    ? messagesRaw
        .filter((m) => m && typeof m === "object" && !Array.isArray(m))
        .map((m) => {
          const r = m as Record<string, unknown>;
          return { role: String(r.role ?? ""), content: String(r.content ?? "") };
        })
    : [];
  const meta = o.meta && typeof o.meta === "object" && !Array.isArray(o.meta) ? (o.meta as Record<string, unknown>) : undefined;
  return {
    messages,
    response_text: typeof o.response_text === "string" ? o.response_text : String(data.llm_prompt ?? ""),
    meta,
  };
}

export function parsePhysicsAuditorLlm(auditData: Record<string, unknown>): LabLlmRoundSnapshot {
  const prompt = auditData.prompt;
  const messages = Array.isArray(prompt)
    ? prompt
        .filter((m) => m && typeof m === "object" && !Array.isArray(m))
        .map((m) => {
          const r = m as Record<string, unknown>;
          return { role: String(r.role ?? ""), content: String(r.content ?? "") };
        })
    : [];
  return {
    messages,
    response_text: typeof auditData.llm_raw === "string" ? auditData.llm_raw : "",
    meta:
      auditData.llm_meta && typeof auditData.llm_meta === "object" && !Array.isArray(auditData.llm_meta)
        ? (auditData.llm_meta as Record<string, unknown>)
        : undefined,
    repair_mode: typeof auditData.repair_mode === "string" ? auditData.repair_mode : undefined,
  };
}
