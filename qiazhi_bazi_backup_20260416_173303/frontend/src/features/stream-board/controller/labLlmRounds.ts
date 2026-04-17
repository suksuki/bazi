import type { LabLlmRoundSnapshot } from "@/features/stream-board/stores/LabSessionContext";

/** 与后端 llm_meta.prompt_scenario 对齐的可扩展枚举 */
export type LlmPromptScenario =
  | "first_observation"
  | "physics_audit"
  | "final_verdict_decision"
  | "final_verdict_mandatory_synthesis"
  | "final_verdict_regeneration"
  | "unknown";

export type LabLlmRoundEntry = LabLlmRoundSnapshot & {
  id: string;
  scenario: LlmPromptScenario;
  title_zh: string;
  at: number;
};

/** 与 LabSnapshot 的 LLM 相关字段子集（避免与 LabSessionContext 循环 import） */
export type LabSnapshotLlmSlice = {
  ts?: number;
  first_observation_llm?: LabLlmRoundSnapshot;
  physics_auditor_llm?: LabLlmRoundSnapshot;
  final_verdict?: Record<string, unknown>;
  llm_rounds?: LabLlmRoundEntry[];
};

const SCENARIO_LABELS: Record<LlmPromptScenario, string> = {
  first_observation: "首观 LLM（四柱初读）",
  physics_audit: "物理审计 LLM（结构化 JSON）",
  final_verdict_decision: "终局裁决 LLM（用户勾选）",
  final_verdict_mandatory_synthesis: "终局裁决 LLM（系统整合）",
  final_verdict_regeneration: "终局裁决 LLM（再生）",
  unknown: "LLM 往返",
};

export function scenarioTitleZh(s: LlmPromptScenario): string {
  return SCENARIO_LABELS[s] ?? SCENARIO_LABELS.unknown;
}

function metaScenario(meta: Record<string, unknown> | undefined): string | undefined {
  const raw = meta?.prompt_scenario;
  return typeof raw === "string" && raw.trim() ? raw.trim() : undefined;
}

export function inferLlmPromptScenario(meta: Record<string, unknown> | undefined, fallback: LlmPromptScenario): LlmPromptScenario {
  const s = metaScenario(meta);
  if (!s) return fallback;
  if (Object.prototype.hasOwnProperty.call(SCENARIO_LABELS, s)) return s as LlmPromptScenario;
  if (s === "final_verdict") return "final_verdict_decision";
  return fallback;
}

function roundFingerprint(r: LabLlmRoundSnapshot): string {
  const msgs = Array.isArray(r.messages) ? r.messages : [];
  const head = msgs
    .slice(0, 2)
    .map((m) => `${m.role}:${String(m.content || "").slice(0, 400)}`)
    .join("|");
  const tail = String(r.response_text || "").slice(0, 1200);
  return `${head}::${tail}`;
}

function buildRoundEntry(
  id: string,
  fallbackScenario: LlmPromptScenario,
  titleZh: string,
  snap: LabLlmRoundSnapshot | undefined,
  at: number,
): LabLlmRoundEntry | null {
  if (!snap) return null;
  const hasMsg = Array.isArray(snap.messages) && snap.messages.length > 0;
  const hasResp = Boolean(String(snap.response_text || "").trim());
  if (!hasMsg && !hasResp) return null;
  const meta = snap.meta && typeof snap.meta === "object" && !Array.isArray(snap.meta) ? snap.meta : undefined;
  const scenario = inferLlmPromptScenario(meta, fallbackScenario);
  return {
    ...snap,
    id,
    scenario,
    title_zh: titleZh.trim() ? titleZh : scenarioTitleZh(scenario),
    at,
  };
}

/**
 * 将「首观 / 审计 / 终审」规范为有序多轮记录，供 Debug 与后续扩展。
 * - 首观、审计：同 id 幂等替换（内容指纹变化时更新）。
 * - 终审：按 version_id 追加，保留最近若干条。
 */
export function syncLlmRoundsCanonical(
  prevFull: LabSnapshotLlmSlice | null | undefined,
  next: LabSnapshotLlmSlice,
  seedUniverseChanged: boolean,
): LabLlmRoundEntry[] {
  const at = typeof next.ts === "number" ? next.ts : Date.now();
  let base: LabLlmRoundEntry[] = [];
  if (!seedUniverseChanged && Array.isArray(prevFull?.llm_rounds)) {
    base = [...(prevFull!.llm_rounds as LabLlmRoundEntry[])];
  }

  const upsertFixed = (id: string, entry: LabLlmRoundEntry | null) => {
    if (!entry) return;
    const idx = base.findIndex((r) => r.id === id);
    if (idx >= 0) {
      if (roundFingerprint(base[idx]) !== roundFingerprint(entry)) {
        const nextRows = [...base];
        nextRows[idx] = { ...entry, at };
        base = nextRows;
      }
      return;
    }
    base = [...base, { ...entry, at }];
  };

  const fo = buildRoundEntry("round:first_observation", "first_observation", "", next.first_observation_llm, at);
  upsertFixed("round:first_observation", fo);

  const au = buildRoundEntry("round:physics_audit", "physics_audit", "", next.physics_auditor_llm, at);
  upsertFixed("round:physics_audit", au);

  const fv = next.final_verdict as Record<string, unknown> | undefined;
  if (!fv || typeof fv !== "object") {
    return base.slice(-32);
  }
  const vid = typeof fv.version_id === "string" ? fv.version_id.trim() : "";
  const msgs = Array.isArray(fv.llm_request_messages) ? fv.llm_request_messages : [];
  const raw = typeof fv.llm_raw_response === "string" ? fv.llm_raw_response.trim() : "";
  if (vid && (msgs.length > 0 || raw)) {
    const meta =
      fv.llm_meta && typeof fv.llm_meta === "object" && !Array.isArray(fv.llm_meta)
        ? (fv.llm_meta as Record<string, unknown>)
        : undefined;
    const scenario = inferLlmPromptScenario(meta, "final_verdict_decision");
    const entry: LabLlmRoundEntry = {
      id: `round:final_verdict:${vid}`,
      scenario,
      title_zh: scenarioTitleZh(scenario),
      at,
      messages: msgs
        .filter((m) => m && typeof m === "object" && !Array.isArray(m))
        .map((m) => {
          const r = m as Record<string, unknown>;
          return { role: String(r.role ?? ""), content: String(r.content ?? "") };
        }),
      response_text: raw,
      meta,
    };
    const exists = base.some((r) => r.id === entry.id);
    if (!exists) {
      base = [...base, entry];
    } else {
      upsertFixed(entry.id, entry);
    }
    const finalKeep = 14;
    const finals = base.filter((r) => r.id.startsWith("round:final_verdict:"));
    const nonFinals = base.filter((r) => !r.id.startsWith("round:final_verdict:"));
    if (finals.length > finalKeep) {
      base = [...nonFinals, ...finals.slice(-finalKeep)];
    }
  }

  return base.slice(-32);
}
