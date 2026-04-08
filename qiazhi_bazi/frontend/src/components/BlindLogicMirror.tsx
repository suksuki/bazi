"use client";

import { motion } from "framer-motion";
import { useEffect } from "react";
import { EnergyBridge } from "./EnergyBridge";

type WorkVectorItem = {
  detail?: string;
  type?: string;
  direction?: string;
  expected_work?: number;
  backfire_risk?: number;
  host_abs?: number;
  guest_abs?: number;
  unlock_gain?: number;
  source_deity?: string;
  target_deity?: string;
};

type Props = {
  workVector?: Record<string, unknown>;
};

type CampCard = { name: string; abs: number; state: string; tone: string };
type DamageNode = { node_id?: string; delta_abs?: number; damage_ratio?: number; critical_stress?: boolean };

function stateByAbs(abs: number): string {
  if (abs < 0.5) return "熄灭";
  if (abs < 2) return "衰微";
  if (abs < 5) return "中和";
  return "强旺";
}

function buildCamp(nameList: string[], absTotal: number, isBody: boolean): CampCard[] {
  const weights = isBody ? [0.42, 0.33, 0.25] : [0.38, 0.34, 0.28];
  return nameList.map((name, i) => {
    const abs = Math.max(0, absTotal * (weights[i] || 0.3));
    return {
      name,
      abs,
      state: stateByAbs(abs),
      tone: isBody ? "from-cyan-500/30 to-sky-500/10" : "from-amber-500/30 to-orange-500/10",
    };
  });
}

export function BlindLogicMirror({ workVector = {} }: Props) {
  const workVectors = ((workVector as { work_vectors?: WorkVectorItem[] }).work_vectors || []);
  const hostAbs = Number(workVectors.reduce((acc, item) => acc + Number(item.host_abs || 0), 0)) || 0;
  const guestAbs = Number(workVectors.reduce((acc, item) => acc + Number(item.guest_abs || 0), 0)) || 0;
  const gain = Number(workVectors.reduce((acc, item) => acc + Number(item.unlock_gain || 0), 0));
  const risk = Number(workVectors.reduce((acc, item) => acc + Number(item.backfire_risk || 0), 0));
  const net = Number(workVectors.reduce((acc, item) => acc + Number(item.expected_work || 0), 0));
  const bodyLabels = ((workVector as { body_labels?: string[] }).body_labels || ["比肩", "劫财", "正印", "偏印"]).slice(0, 3);
  const useLabels = ((workVector as { use_labels?: string[] }).use_labels || ["食神", "伤官", "正财", "偏财", "正官", "七杀"]).slice(0, 3);
  const bodyCards = buildCamp(bodyLabels, hostAbs || Number((workVector as { host_abs?: number }).host_abs || 0), true);
  const useCards = buildCamp(useLabels, guestAbs || Number((workVector as { guest_abs?: number }).guest_abs || 0), false);
  const damageNodes = (((workVector as { body_damage_estimation?: { nodes?: DamageNode[] } }).body_damage_estimation || {}).nodes || []);
  const damageMap = new Map<string, DamageNode>(damageNodes.map((n) => [String(n.node_id || ""), n]));
  const maxAxisAbs = Math.max(
    Number((workVector as { host_abs?: number }).host_abs || 0),
    Number((workVector as { guest_abs?: number }).guest_abs || 0),
  );
  const showWeakPaths = Number((((workVector as { runtime_physics_config?: Record<string, unknown> }).runtime_physics_config || {}).SHOW_WEAK_WORK_PATHS) || 0) > 0.5;
  const workExpectation = Number((workVector as { work_expectation?: number }).work_expectation || 0);
  const emptyHint = (!workVectors.length && maxAxisAbs > 100 && workExpectation <= 0.05)
    ? "做功工具（午火）受大运（子水）压制，路径断裂。"
    : undefined;
  const spatialAudit = ((workVector as { spatial_audit?: Record<string, unknown> }).spatial_audit || {});
  const spatialLockWarning = String(spatialAudit.lock_warning || "");
  const isExitLocked = Boolean(spatialAudit.is_exit_locked);
  const blockingElements = ((spatialAudit.blocking_elements || []) as string[]).filter(Boolean);
  const unlockAdvice = (((workVector as { unlock_advice?: { strategic_strike_options?: Array<{ action?: string }> } }).unlock_advice || {}).strategic_strike_options || []);

  useEffect(() => {
    if (!workVectors.length && maxAxisAbs > 10) {
      // eslint-disable-next-line no-console
      console.warn("LOGIC_INCONSISTENCY_WARNING", {
        reason: "high_abs_but_no_work_vectors",
        maxAxisAbs,
      });
    }
  }, [workVectors.length, maxAxisAbs]);

  return (
    <section className="rounded-xl border border-zinc-800 bg-zinc-950 p-3">
      <h4 className="text-sm font-medium text-zinc-100">盲派体用对垒仪表盘</h4>
      <div className="mt-2 grid grid-cols-1 gap-3 md:grid-cols-3">
        <motion.div initial={{ x: -24, opacity: 0 }} animate={{ x: 0, opacity: 1 }} className="space-y-2">
          <p className="text-xs text-cyan-300">体（BODY） [家里/INTERNAL]</p>
          {bodyCards.map((card, idx) => (
            (() => {
              const damage = damageMap.get(card.name);
              const damageValue = Number(damage?.delta_abs || 0);
              const damageRatio = Number(damage?.damage_ratio || 0);
              const critical = Boolean(damage?.critical_stress);
              const baseWidth = Math.max(6, Math.min(100, card.abs * 10));
              const damageWidth = Math.max(0, Math.min(baseWidth, baseWidth * Math.max(0, Math.min(1, damageRatio))));
              return (
            <div
              key={`body-${card.name}-${idx}`}
              className={`rounded border border-cyan-700/40 bg-gradient-to-r ${card.tone} p-2 ${critical ? "animate-pulse shadow-[0_0_10px_rgba(248,113,113,0.35)]" : ""}`}
              style={critical ? { maskImage: "repeating-linear-gradient(135deg, rgba(255,255,255,0.95) 0 8px, rgba(255,255,255,0.7) 8px 11px)" } : undefined}
            >
              <div className="mb-1 flex items-center justify-between text-xs">
                <span className="text-zinc-100">{card.name}</span>
                <span className="rounded border border-zinc-600 px-1 text-[10px] text-zinc-300">
                  [{card.state}{critical ? " / CRITICAL_STRESS" : ""}]
                </span>
              </div>
              <div className="h-1.5 rounded bg-zinc-800">
                <div className="h-full rounded bg-cyan-400/80" style={{ width: `${Math.max(6, Math.min(100, card.abs * 10))}%` }} />
                {damageValue > 0 ? (
                  <div className="relative -mt-1.5 h-1.5 rounded bg-rose-500/70" style={{ width: `${damageWidth}%` }} />
                ) : null}
              </div>
              <div className="mt-1 flex items-center justify-between text-[10px]">
                <span className="text-zinc-400">Abs {card.abs.toFixed(2)}</span>
                <span className={`${damageValue > 0 ? "text-rose-300" : "text-zinc-500"}`}>{damageValue > 0 ? `-${damageValue.toFixed(2)}` : "-0.00"}</span>
              </div>
            </div>
              );
            })()
          ))}
        </motion.div>

        <div className={`rounded border bg-zinc-900 p-2 ${isExitLocked ? "border-rose-500/60 shadow-[0_0_18px_rgba(244,63,94,0.25)]" : "border-zinc-700"}`}>
          <p className="mb-1 text-xs text-zinc-300">做功空腔（Working Chamber）</p>
          {isExitLocked ? (
            <div className="mb-2 rounded border border-rose-500/50 bg-gradient-to-r from-rose-500/20 via-red-500/10 to-transparent px-2 py-1 text-[11px] text-rose-200">
              <span className="mr-1 inline-block animate-pulse">⚡</span>
              [出口被封锁：能量内溢风险]
              {blockingElements.length ? ` 阻滞点：${blockingElements.join(" / ")}` : ""}
            </div>
          ) : null}
          {spatialLockWarning ? (
            <p className="mb-2 rounded border border-rose-500/40 bg-rose-500/10 px-2 py-1 text-[11px] text-rose-200">
              {spatialLockWarning}
            </p>
          ) : null}
          <EnergyBridge vectors={workVectors} bodyLabels={bodyLabels} useLabels={useLabels} showWeakPaths={showWeakPaths} emptyHint={emptyHint} />
          <div className="mt-2 grid grid-cols-3 gap-2 text-[11px]">
            <p className="rounded border border-cyan-700/30 bg-cyan-500/10 p-1 text-cyan-200">Input: {gain.toFixed(2)}</p>
            <p className="rounded border border-orange-700/30 bg-orange-500/10 p-1 text-orange-200">Tax: {risk.toFixed(2)}</p>
            <p className={`rounded border p-1 ${net >= 0 ? "border-emerald-700/30 bg-emerald-500/10 text-emerald-200" : "border-rose-700/30 bg-rose-500/10 text-rose-200"}`}>
              Net: {net >= 0 ? "+" : ""}{net.toFixed(2)}
            </p>
          </div>
          {unlockAdvice.length > 0 ? (
            <div className="mt-2 rounded border border-cyan-700/40 bg-cyan-500/10 p-2 text-[11px] text-cyan-200">
              <p className="mb-1">解锁建议（Strategic Strike）</p>
              {unlockAdvice.slice(0, 3).map((item, idx) => (
                <p key={`unlock-${idx}`}>- {String(item.action || "")}</p>
              ))}
            </div>
          ) : null}
        </div>

        <motion.div initial={{ x: 24, opacity: 0 }} animate={{ x: 0, opacity: 1 }} className="space-y-2">
          <p className="text-xs text-amber-300">用（USE） [家外/EXTERNAL]</p>
          {isExitLocked ? (
            <div className="rounded border border-rose-500/40 bg-rose-500/10 px-2 py-1 text-[10px] text-rose-200">
              时柱出口告警：门被焊死（高压态）
            </div>
          ) : null}
          {useCards.map((card, idx) => (
            <div key={`use-${card.name}-${idx}`} className={`rounded border border-amber-700/40 bg-gradient-to-r ${card.tone} p-2`}>
              <div className="mb-1 flex items-center justify-between text-xs">
                <span className="text-zinc-100">{card.name}</span>
                <span className="rounded border border-zinc-600 px-1 text-[10px] text-zinc-300">[{card.state}]</span>
              </div>
              <div className="h-1.5 rounded bg-zinc-800">
                <div className="h-full rounded bg-amber-400/80" style={{ width: `${Math.max(6, Math.min(100, card.abs * 10))}%` }} />
              </div>
            </div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}
