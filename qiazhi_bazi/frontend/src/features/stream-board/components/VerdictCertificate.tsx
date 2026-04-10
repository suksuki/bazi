"use client";

import { useCallback, useState } from "react";

type LogicDiffSlice = {
  baseline_abs_loss_total?: number | null;
  current_abs_loss_total?: number | null;
  abs_delta?: number | null;
  baseline_entropy?: number | null;
  current_entropy?: number | null;
  entropy_delta?: number | null;
} | null | undefined;

/** 基于 |abs_delta| 的裁决气质文案（Abs 损耗语义） */
export function getVerdictEvaluation(absDelta: number): string {
  const a = Math.abs(absDelta);
  if (!Number.isFinite(a)) return "未定：logic_diff 尚无有效 Δabs，无法宣读场强气质。";
  if (a < 10) return "共鸣：因果偏移极低，逻辑圆融。";
  if (a <= 40) return "修正：意志成功校准场强，天平已稳。";
  return "重构：因果发生剧烈位移，宿命被强制剥离。";
}

function fmt(n: unknown): string {
  if (typeof n === "number" && Number.isFinite(n)) return n.toFixed(4);
  return "—";
}

function abbreviateSha256(hex: string): string {
  const h = String(hex || "").trim();
  if (h.length <= 16) return h || "—";
  return `${h.slice(0, 10)}…${h.slice(-6)}`;
}

function summarizeLogicDiff(ld: LogicDiffSlice): string {
  if (!ld || typeof ld !== "object") return "logic_diff：尚无结构化摘要。";
  const parts = [
    `Δabs ${fmt(ld.abs_delta)}`,
    `abs ${fmt(ld.baseline_abs_loss_total)} → ${fmt(ld.current_abs_loss_total)}`,
    `ΔH ${fmt(ld.entropy_delta)}`,
    `H ${fmt(ld.baseline_entropy)} → ${fmt(ld.current_entropy)}`,
  ];
  return parts.join(" · ");
}

export function VerdictCertificate(props: {
  hash: string;
  committedAt: number;
  logicDiff: LogicDiffSlice;
  /** 终审时固化的盲派 Skill ID 列表（与 skill_manifest 一致） */
  effectiveSkillIds?: string[];
}) {
  const { hash, committedAt, logicDiff, effectiveSkillIds } = props;
  const when = committedAt ? new Date(committedAt).toLocaleString() : "—";

  const absRaw = logicDiff && typeof logicDiff === "object" ? logicDiff.abs_delta : null;
  const absDelta = typeof absRaw === "number" && Number.isFinite(absRaw) ? absRaw : NaN;
  const evaluation = getVerdictEvaluation(absDelta);

  const [flash, setFlash] = useState(false);
  const [verified, setVerified] = useState(false);

  const copyHash = useCallback(async () => {
    const h = String(hash || "").trim();
    if (!h) return;
    try {
      await navigator.clipboard.writeText(h);
      setFlash(true);
      setVerified(true);
      window.setTimeout(() => setFlash(false), 420);
      window.setTimeout(() => setVerified(false), 2200);
    } catch {
      /* ignore */
    }
  }, [hash]);

  return (
    <div
      className="mb-4 overflow-hidden rounded-2xl border-2 border-[#A855F7] shadow-[0_0_24px_rgba(168,85,247,0.12)]"
      style={{
        background:
          "linear-gradient(145deg, rgba(24,24,27,0.97) 0%, rgba(39,39,42,0.92) 45%, rgba(28,25,35,0.95) 100%), radial-gradient(120% 80% at 10% 0%, rgba(168,85,247,0.08), transparent 55%)",
      }}
    >
      <div className="border-b border-[#A855F7]/35 bg-zinc-950/60 px-4 py-2">
        <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-[#A855F7]">因果定格 · 终审存证</p>
        <p className="mt-0.5 text-[10px] text-zinc-500">Causal chain sealed — humanistic footnote</p>
      </div>
      <div className="space-y-3 px-4 py-3 text-xs text-zinc-200">
        <div>
          <p className="text-[10px] font-medium uppercase tracking-wide text-zinc-500">SHA-256（缩写 · 点击拷贝完整指纹）</p>
          <button
            type="button"
            onClick={() => void copyHash()}
            className={`mt-1 w-full rounded-md px-2 py-1.5 text-left font-mono text-[13px] tracking-tight transition-colors duration-300 ${
              flash
                ? "bg-[#A855F7]/30 text-[#A855F7] shadow-[0_0_12px_rgba(168,85,247,0.45)]"
                : "bg-transparent text-violet-100/95 hover:bg-[#A855F7]/10"
            }`}
          >
            {abbreviateSha256(hash)}
          </button>
          {verified ? (
            <p className="mt-1 font-mono text-[10px] font-medium tracking-wide text-[#A855F7]">[VERIFIED]</p>
          ) : null}
          <p className="mt-2 italic leading-relaxed text-fuchsia-300/80">{evaluation}</p>
          <p className="mt-2 font-mono text-[10px] break-all text-zinc-600">{hash}</p>
        </div>
        <div>
          <p className="text-[10px] font-medium uppercase tracking-wide text-zinc-500">签发时间</p>
          <p className="mt-1 font-mono text-[12px] text-zinc-300">{when}</p>
        </div>
        <div className="rounded-lg border border-zinc-700/80 bg-zinc-950/50 px-3 py-2">
          <p className="text-[10px] font-medium uppercase tracking-wide text-zinc-500">logic_diff 最终摘要</p>
          <p className="mt-1.5 leading-relaxed text-[11px] text-zinc-300">{summarizeLogicDiff(logicDiff)}</p>
        </div>
        <div className="rounded-lg border border-amber-500/25 bg-amber-950/20 px-3 py-2">
          <p className="text-[10px] font-medium uppercase tracking-wide text-amber-200/80">生效 Skill ID（规则索引）</p>
          {effectiveSkillIds && effectiveSkillIds.length > 0 ? (
            <ul className="mt-1.5 flex flex-wrap gap-1.5">
              {effectiveSkillIds.map((id) => (
                <li
                  key={id}
                  className="rounded border border-amber-500/35 bg-zinc-950/60 px-2 py-0.5 font-mono text-[10px] text-amber-100/95"
                >
                  {id}
                </li>
              ))}
            </ul>
          ) : (
            <p className="mt-1 text-[11px] text-zinc-500">本快照未记录盲派 Skill 列表（或非盲派会话）。</p>
          )}
        </div>
      </div>
    </div>
  );
}
