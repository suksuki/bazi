/** Tooltip 文案（与产品口径一致；策略细节见 meta.causal_routing.routing_decision） */
export const ROUTING_CONFLICT_TOOLTIP =
  "[ROUTING]: 基础物理与盲派冲突，已按流派优先策略自动校准";

/**
 * 从 `meta.causal_routing.conflict_events` 收集被路由协商触及的十神轴（极性冲突 / 合并覆盖）。
 */
export function buildRoutingHighlightDeities(causalRouting: unknown): Set<string> {
  const out = new Set<string>();
  if (!causalRouting || typeof causalRouting !== "object") return out;
  const events = (causalRouting as { conflict_events?: unknown }).conflict_events;
  if (!Array.isArray(events)) return out;
  for (const ev of events) {
    if (!ev || typeof ev !== "object") continue;
    const d = String((ev as { deity?: string }).deity || "").trim();
    if (d) out.add(d);
  }
  return out;
}
