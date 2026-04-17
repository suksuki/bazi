import { sysCorePhysicsPayload } from "@/features/stream-board/sysCorePhysics";
import { humanizePluginId } from "./semanticLexicon";

export type PluginInteractionHit = {
  id: string;
  displayName: string;
  /** L0 原子流水线中首次出现步序（0-based），无则 null */
  traceFirstStep: number | null;
  hasPluginOutput: boolean;
  lifecycleHitCount: number;
  hasMatchScore: boolean;
};

function asRecord(x: unknown): Record<string, unknown> | undefined {
  return x && typeof x === "object" ? (x as Record<string, unknown>) : undefined;
}

function traceRowsFromCore(corePl: Record<string, unknown> | undefined): Record<string, unknown>[] {
  if (!corePl) return [];
  const direct = corePl.physics_trace;
  if (Array.isArray(direct) && direct.length > 0) {
    return direct.filter((x): x is Record<string, unknown> => !!x && typeof x === "object");
  }
  const pipe = asRecord(corePl.l1_atomic_pipeline);
  const steps = pipe?.steps;
  if (!Array.isArray(steps) || steps.length === 0) return [];
  return steps.map((raw, i) => {
    if (raw && typeof raw === "object") {
      const row = raw as Record<string, unknown>;
      return {
        step_index: typeof row.step_index === "number" ? row.step_index : i,
        plugin: row.plugin,
        reason: row.label ?? row.summary ?? row.op_id ?? row.operator,
        delta_summary: row.delta,
      };
    }
    return { step_index: i, plugin: "", reason: "", delta_summary: "" };
  });
}

/**
 * 合并「L0 流水线先后 + physics_tensor.plugin_outputs + Inbox 生命周期 + MatchScore」中的插件 ID，
 * 去重后给出可展示的命中表（中文名由 humanizePluginId）。
 */
export function buildPluginInteractionRollup(physics: Record<string, unknown> | undefined): PluginInteractionHit[] {
  const meta = asRecord(physics?.meta) ?? {};
  const inbox = asRecord(meta.decision_inbox_v1);
  const po = asRecord(physics?.plugin_outputs) ?? {};
  const corePl = sysCorePhysicsPayload(po);
  const trace = traceRowsFromCore(corePl);
  const lifecycles = Array.isArray(inbox?.lifecycle_traces) ? inbox.lifecycle_traces : [];
  const scores = Array.isArray(inbox?.match_scores) ? inbox.match_scores : [];

  const order: string[] = [];
  const seen = new Set<string>();
  const push = (id: unknown) => {
    const s = String(id ?? "").trim();
    if (!s || s.startsWith("_")) return;
    if (seen.has(s)) return;
    seen.add(s);
    order.push(s);
  };

  for (const t of trace) {
    const plug = t.plugin;
    if (typeof plug === "string" && plug.trim()) push(plug.trim());
  }

  for (const k of Object.keys(po).sort()) {
    if (k.startsWith("_")) continue;
    push(k);
  }

  for (const raw of lifecycles) {
    if (!raw || typeof raw !== "object") continue;
    const e = raw as Record<string, unknown>;
    push(e.plugin_id);
  }

  for (const raw of scores) {
    if (!raw || typeof raw !== "object") continue;
    const s = raw as Record<string, unknown>;
    push(s.plugin_id);
  }

  const firstStep = new Map<string, number>();
  trace.forEach((t, i) => {
    const plug = typeof t.plugin === "string" ? t.plugin.trim() : "";
    if (!plug) return;
    const idx = typeof t.step_index === "number" && Number.isFinite(t.step_index) ? (t.step_index as number) : i;
    if (!firstStep.has(plug)) firstStep.set(plug, idx);
  });

  const lifeCount = new Map<string, number>();
  for (const raw of lifecycles) {
    if (!raw || typeof raw !== "object") continue;
    const pid = String((raw as Record<string, unknown>).plugin_id ?? "").trim();
    if (!pid) continue;
    lifeCount.set(pid, (lifeCount.get(pid) ?? 0) + 1);
  }

  const scoreSet = new Set<string>();
  for (const raw of scores) {
    if (!raw || typeof raw !== "object") continue;
    const pid = String((raw as Record<string, unknown>).plugin_id ?? "").trim();
    if (pid) scoreSet.add(pid);
  }

  return order.map((id) => ({
    id,
    displayName: humanizePluginId(id),
    traceFirstStep: firstStep.has(id) ? (firstStep.get(id) as number) : null,
    hasPluginOutput: Object.prototype.hasOwnProperty.call(po, id),
    lifecycleHitCount: lifeCount.get(id) ?? 0,
    hasMatchScore: scoreSet.has(id),
  }));
}
