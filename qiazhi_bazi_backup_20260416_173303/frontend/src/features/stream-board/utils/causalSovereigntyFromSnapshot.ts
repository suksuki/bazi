import type { ConflictPoint } from "@/types/bazi";

export type CausalSovereigntySlice = {
  strategyLabel: string;
  willInfusedPct: number | null;
  routingDigest?: string;
};

export function strategyAppliedLabel(strategy: string): string {
  const s = String(strategy || "").trim();
  if (s === "school_priority") return "流派优先";
  if (s === "weighted_sum") return "加权融合（保守）";
  if (s === "manual_arbitration") return "人工仲裁";
  if (!s) return "未记录";
  return s;
}

function readCausalRoutingFromSnapshot(
  snapshot: Record<string, unknown> | null | undefined,
): Record<string, unknown> | null {
  if (!snapshot || typeof snapshot !== "object") return null;
  const pt = snapshot.physics_tensor as { meta?: Record<string, unknown> } | undefined;
  const cr = pt?.meta?.causal_routing;
  return cr && typeof cr === "object" ? (cr as Record<string, unknown>) : null;
}

/** 与 DebugView 中 conflict 点勾选逻辑对齐，用于 WILL_INFUSED 占比 */
export function computeWillInfusedPctFromSnapshot(
  snapshot: Record<string, unknown> | null | undefined,
): number | null {
  if (!snapshot || typeof snapshot !== "object") return null;
  const meta = (snapshot.metadata || {}) as { conflict_matrix?: { points?: ConflictPoint[] } };
  const points = meta.conflict_matrix?.points ?? [];
  if (points.length === 0) return null;
  const decisionIds = new Set(
    Array.isArray(snapshot.decision_selection_ids)
      ? snapshot.decision_selection_ids.map((x) => String(x))
      : [],
  );
  const hub = snapshot.interaction_hub as { pending_cards?: unknown[] } | undefined;
  const pending = Array.isArray(hub?.pending_cards) ? hub.pending_cards : [];
  let checked = 0;
  points.forEach((p, i) => {
    const detail = String(p.detail || "—");
    const pendingMatch = pending.find((c) => {
      const title = String((c as { title?: string }).title || "");
      return title && (detail.includes(title.slice(0, 4)) || title.includes(detail.slice(0, 4)));
    }) as { id?: string } | undefined;
    const did = pendingMatch?.id ? String(pendingMatch.id) : `physics:${i}`;
    const isChecked =
      did.startsWith("physics:")
        ? [...decisionIds].some((id) => id.startsWith("llm-observe"))
        : decisionIds.has(did);
    if (isChecked) checked += 1;
  });
  return Math.round((checked / points.length) * 100);
}

/**
 * 终审证书「因果主权」切片：策略标签 + 意志注入占比 + 路由决策摘要。
 */
export function buildCausalSovereigntySlice(
  snapshot: Record<string, unknown> | null | undefined,
  causalRoutingOverride?: Record<string, unknown> | null,
): CausalSovereigntySlice | undefined {
  const cr = causalRoutingOverride ?? readCausalRoutingFromSnapshot(snapshot);
  if (!cr) return undefined;
  const strategy = String(cr.strategy_applied || "");
  const digest = String(cr.routing_decision || "").trim();
  return {
    strategyLabel: strategyAppliedLabel(strategy),
    willInfusedPct: computeWillInfusedPctFromSnapshot(snapshot),
    routingDigest: digest ? digest.slice(0, 160) : undefined,
  };
}
