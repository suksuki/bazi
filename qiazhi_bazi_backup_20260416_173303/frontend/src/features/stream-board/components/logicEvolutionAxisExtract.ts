import type { LabLlmRoundEntry } from "@/features/stream-board/controller/labLlmRounds";
import { hoistPhysicsAuditDiagnosis } from "@/features/stream-board/controller/streamBoardPure";
import { coerceVerdictDisplayBody } from "@/features/stream-board/controller/verdictBodyStream";

/** 从各轮 LLM response 中抽取可读的 diagnosis / 判词摘要，供逻辑演化轴展开。 */
export function extractLlmRoundDiagnosisText(round: Pick<LabLlmRoundEntry, "scenario" | "response_text">): string {
  const rt = String(round.response_text || "").trim();
  if (!rt) return "";
  const sc = String(round.scenario || "");
  if (sc.includes("final_verdict")) {
    const coerced = coerceVerdictDisplayBody(rt).trim();
    return coerced || rt.slice(0, 2000);
  }
  if (sc === "physics_audit" || rt.startsWith("{")) {
    try {
      const o = JSON.parse(rt) as Record<string, unknown>;
      const h = hoistPhysicsAuditDiagnosis(o);
      if (h) return h;
    } catch {
      /* ignore */
    }
    return rt.slice(0, 2000);
  }
  return rt.slice(0, 2000);
}
