/**
 * 从 audit_log / evidence / 合成场 中抽取与十神能量波动相关的简短归因（中文）。
 */

function pickSanheHint(physics: Record<string, unknown> | null | undefined): string | null {
  if (!physics) return null;
  const comp = physics.composite_field_impact as Record<string, unknown> | undefined;
  const clusters = Array.isArray(comp?.sanhe_clusters) ? (comp.sanhe_clusters as unknown[]) : [];
  for (const c of clusters) {
    if (!c || typeof c !== "object") continue;
    const row = c as Record<string, unknown>;
    const brs = Array.isArray(row.branches) ? row.branches.map((x) => String(x)) : [];
    if (brs.length >= 3) return `因「${brs.join("·")}」三合合成场登记，相关五行场强被抬升`;
  }
  return null;
}

function pickEvidenceHint(physics: Record<string, unknown> | null | undefined, deity: string): string | null {
  const ev = Array.isArray(physics?.evidence) ? (physics!.evidence as unknown[]) : [];
  const d = deity.trim();
  for (const x of ev) {
    const s = String(x || "");
    if (!s) continue;
    if (d && (s.includes(d) || s.includes("十神") || s.includes("泄") || s.includes("合"))) {
      return s.length > 80 ? `${s.slice(0, 78)}…` : s;
    }
  }
  return null;
}

function pickAuditSnippet(physics: Record<string, unknown> | null | undefined): string | null {
  const audit = (physics?.audit_log as Record<string, unknown> | undefined) || {};
  const items = Array.isArray(audit.causal_routing_audit_items) ? audit.causal_routing_audit_items : [];
  const last = items.length > 0 ? items[items.length - 1] : null;
  if (last && typeof last === "object") {
    const rd = String((last as Record<string, unknown>).routing_decision || "").trim();
    if (rd) return rd.length > 100 ? `${rd.slice(0, 98)}…` : rd;
  }
  const dims = Array.isArray(audit.dimensional_shield_logs) ? audit.dimensional_shield_logs : [];
  if (dims.length) {
    const t = String(dims[dims.length - 1] || "");
    if (t) return t.length > 90 ? `${t.slice(0, 88)}…` : t;
  }
  return null;
}

/** 相对变化超过 ratio 视为「剧烈波动」 */
export function isSpike(prev: number, next: number, ratio = 0.22): boolean {
  const base = Math.max(1e-4, Math.abs(prev));
  return Math.abs(next - prev) / base >= ratio;
}

function relDeltaPct(prevAbs: number, nextAbs: number): string | null {
  if (!(prevAbs > 1e-6)) return null;
  const pct = Math.round(((nextAbs - prevAbs) / prevAbs) * 100);
  return `${pct > 0 ? "+" : ""}${pct}%`;
}

export function inferDeityEnergyAttribution(
  physics: Record<string, unknown> | null | undefined,
  deityName: string,
  prevAbs: number,
  nextAbs: number,
): string | null {
  if (!isSpike(prevAbs, nextAbs)) return null;
  const pctStr = relDeltaPct(prevAbs, nextAbs);
  const deltaBit = pctStr ? `，相对变化约 ${pctStr}` : "";
  const sanhe = pickSanheHint(physics);
  if (sanhe) return `${sanhe}；「${deityName}」绝对能量出现阶跃（${prevAbs.toFixed(3)}→${nextAbs.toFixed(3)}）${deltaBit}`;
  const ev = pickEvidenceHint(physics, deityName);
  if (ev) return `因证据链：${ev}；「${deityName}」${prevAbs.toFixed(3)}→${nextAbs.toFixed(3)}${deltaBit}`;
  const aud = pickAuditSnippet(physics);
  if (aud) return `因路由/审计侧更新：${aud}；「${deityName}」${prevAbs.toFixed(3)}→${nextAbs.toFixed(3)}${deltaBit}`;
  return `「${deityName}」绝对能量剧烈变化（${prevAbs.toFixed(3)}→${nextAbs.toFixed(3)}）${deltaBit}，请结合静默重算后的 evidence 与 causal_routing 核查`;
}
