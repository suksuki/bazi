"use client";

import { useMemo } from "react";

const SKILL_LABELS: Record<string, string> = {
  mp_chronos_command: "月令司令",
  mp_chronos_residual: "余气进气",
  ws_season: "旺衰·得令",
  ws_root: "旺衰·得地",
  ws_support: "旺衰·得助",
  l1_status_01: "十二长生缩放",
  l1_prod_01: "L1 相生 η",
  l1_dest_01: "L1 相克 η",
  l1_conn_01: "L1 合绊 η",
  l1_interdim_vert_01: "盖头截脚",
  mw_host_abs: "财富·宿主能量",
  mw_work_net: "财富·净做功",
  mw_exit_lock: "财富·出口闭锁",
  mw_structure: "财富·结构锚",
  mw_risk_band: "财富·风险带",
};

function collectAuditRows(audit: Record<string, unknown> | null | undefined): unknown[] {
  if (!audit || typeof audit !== "object") return [];
  const keys = ["l1_operator_audit_items", "wangshuai_audit_items", "chronos_audit_items"] as const;
  const out: unknown[] = [];
  for (const k of keys) {
    const raw = audit[k];
    if (Array.isArray(raw)) out.push(...raw);
  }
  return out;
}

function contributionFromRow(row: unknown): number {
  if (!row || typeof row !== "object") return 0;
  const r = row as Record<string, unknown>;
  const p = r.payload;
  if (p && typeof p === "object") {
    const pl = p as Record<string, unknown>;
    if (typeof pl.abs_contribution === "number" && Number.isFinite(pl.abs_contribution)) {
      return pl.abs_contribution;
    }
    const d = pl.delta;
    if (d && typeof d === "object") {
      const dl = d as Record<string, unknown>;
      const gain = Number(dl.abs_gain) || 0;
      const loss = Number(dl.abs_loss) || 0;
      return gain - loss;
    }
    if (typeof pl.main_qi_weight === "number" && Number.isFinite(pl.main_qi_weight)) {
      return pl.main_qi_weight * 100;
    }
    if (typeof pl.effective_chronos_weight === "number" && Number.isFinite(pl.effective_chronos_weight)) {
      return pl.effective_chronos_weight * 50;
    }
  }
  return 0;
}

function skillIdFromRow(row: unknown): string {
  if (!row || typeof row !== "object") return "";
  const r = row as Record<string, unknown>;
  const p = r.payload;
  if (p && typeof p === "object") {
    const sid = (p as Record<string, unknown>).skill_id;
    if (typeof sid === "string" && sid) return sid;
  }
  const act = typeof r.action === "string" ? r.action : "";
  const part = act.split("·")[0]?.trim();
  return part || String(r.step ?? "");
}

export function LogicSummary({ physicsAudit }: { physicsAudit: Record<string, unknown> | null | undefined }) {
  const top = useMemo(() => {
    const rows = collectAuditRows(physicsAudit ?? null);
    const scored = rows.map((row) => ({
      row,
      skillId: skillIdFromRow(row),
      score: Math.abs(contributionFromRow(row)),
      signed: contributionFromRow(row),
    }));
    scored.sort((a, b) => b.score - a.score);
    return scored.slice(0, 5);
  }, [physicsAudit]);

  if (!top.length) {
    return (
      <div className="rounded-lg border border-zinc-800/90 bg-zinc-950/50 px-2 py-2 text-[10px] text-zinc-500">
        暂无 physics_audit 条目；提交命盘后展示 Skill 能量贡献 Top5。
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-emerald-500/25 bg-emerald-950/20 px-2 py-2">
      <p className="text-[10px] font-medium uppercase tracking-wide text-emerald-300/90">逻辑概览 · Skill 贡献 Top5</p>
      <ol className="mt-1.5 space-y-1 text-[11px] text-emerald-100/90">
        {top.map((item, idx) => {
          const label = SKILL_LABELS[item.skillId] || item.skillId || "Skill";
          const v = item.signed;
          const sign = v >= 0 ? "+" : "";
          return (
            <li key={`${item.skillId}-${idx}`} className="flex justify-between gap-2 font-mono">
              <span className="min-w-0 truncate text-zinc-200">{label}</span>
              <span className="shrink-0 text-amber-200/90">
                {sign}
                {v.toFixed(2)} Abs
              </span>
            </li>
          );
        })}
      </ol>
    </div>
  );
}
