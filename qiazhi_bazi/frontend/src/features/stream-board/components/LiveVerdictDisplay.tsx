"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import type { Lang } from "@/types/bazi";
import type { DeityEnergyAxis } from "@/features/stream-board/models";
import { isVerdictDeity, splitVerdictLine } from "@/features/decision-inbox/utils";
import { SkillLinkedAssertionLine } from "@/features/stream-board/components/ResultInterpretation";
import { useLabStore } from "@/features/stream-board/stores/useLabStore";
import {
  coerceVerdictDisplayBody,
  ensureVerdictFingerprintSuffix,
  extractQiazhiVerdictFingerprintComment,
} from "@/features/stream-board/controller/verdictBodyStream";

const WILL_RISK_HEADER = "### 风险预警 (意志对垒)";

export type LiveVerdictDisplayProps = {
  verdictSkeleton: string | null;
  verdictBody: string;
  /** 第二轮物理审计 LLM 定性（与终判解耦，先写裁决舱备忘） */
  physicsAuditDiagnosis?: string | null;
  metadata?: Record<string, unknown>;
  streamingText?: string;
  calculationNonce: number;
  skeletonContentKey?: string;
  highlightVerdict?: boolean;
  summaryChanged?: boolean;
  lang?: Lang;
  t: (s: string) => string;
  onVerdictDeityClick?: (deity: string) => void;
  traceResultLogs?: string[];
  traceChipLogs?: string[];
  traceConflictLabels?: string[];
  preInjectionDeityDisplay?: {
    deity_scores?: Record<string, number>;
    deity_energy_axes?: Record<string, DeityEnergyAxis>;
  } | null;
  showPreInjectionAbsSnapshot?: boolean;
  onShowPreInjectionAbsSnapshotChange?: (next: boolean) => void;
  /** Inbox 勾选等：仅驱动物理层外框一次「共振」闪烁（骨架正文本身无过渡动画） */
  physResonanceKey?: number;
  /** 终判正文强制重挂载（与 calculationNonce 并列，避免同串引用导致不刷新） */
  verdictBodyRenderNonce?: number;
};

function splitSkeletonForWillRisk(skeleton: string): { before: string; riskBlock: string | null } {
  const sk = String(skeleton || "");
  const idx = sk.indexOf(WILL_RISK_HEADER);
  if (idx < 0) return { before: sk, riskBlock: null };
  return {
    before: sk.slice(0, idx).trimEnd(),
    riskBlock: sk.slice(idx).trim(),
  };
}

export function LiveVerdictDisplay({
  verdictSkeleton,
  verdictBody,
  physicsAuditDiagnosis = null,
  metadata = {},
  streamingText = "",
  calculationNonce,
  skeletonContentKey = "",
  highlightVerdict = false,
  summaryChanged = false,
  lang = "ZH",
  t,
  onVerdictDeityClick,
  traceResultLogs = [],
  traceChipLogs = [],
  traceConflictLabels = [],
  preInjectionDeityDisplay,
  showPreInjectionAbsSnapshot = false,
  onShowPreInjectionAbsSnapshotChange,
  physResonanceKey = 0,
  verdictBodyRenderNonce = 0,
}: LiveVerdictDisplayProps) {
  const [traceOpen, setTraceOpen] = useState(false);
  const [vfResonance, setVfResonance] = useState(false);
  const [fingerprintOpen, setFingerprintOpen] = useState(false);
  const prevResonanceRef = useRef(physResonanceKey);
  const lab = useLabStore();
  const llmRaw = String(
    (lab.state.snapshot?.final_verdict as { llm_raw_response?: string } | undefined)?.llm_raw_response || "",
  );

  useEffect(() => {
    if (physResonanceKey === prevResonanceRef.current) return;
    prevResonanceRef.current = physResonanceKey;
    if (physResonanceKey <= 0) return;
    setVfResonance(true);
    const id = window.setTimeout(() => setVfResonance(false), 900);
    return () => window.clearTimeout(id);
  }, [physResonanceKey]);

  function renderPhysicalLine(line: string, idx: number, emphasizeSkeleton: boolean) {
    const parts = lang === "ZH" ? splitVerdictLine(line) : [t(line)];
    const isH3 = line.trim().startsWith("###");
    const isFingerprintLine = line.includes("qiazhi-fingerprint");
    const lineClass = `whitespace-pre-wrap leading-relaxed ${
      isH3 ? "border-l-2 border-zinc-500/50 pl-2 text-zinc-100/95 " : ""
    } text-zinc-300/95 text-sm ${
      emphasizeSkeleton && highlightVerdict ? "text-[1.05rem] font-medium" : ""
    } ${isFingerprintLine ? "break-all font-mono text-[10px] text-zinc-500" : "break-words"}`;
    return (
      <SkillLinkedAssertionLine
        key={`p-${idx}-${line.slice(0, 12)}`}
        line={line}
        className={lineClass}
        t={t}
      >
        {parts.map((part, i) => (
          isVerdictDeity(part) ? (
            <button
              key={`p-${idx}-${i}-${part}`}
              type="button"
              onClick={() => onVerdictDeityClick?.(part)}
              className="mx-[1px] rounded border border-sky-600/35 bg-sky-950/40 px-1 text-sky-200/95 hover:bg-sky-900/50"
              title={t("查看 {deity} 的演算路径").replace("{deity}", part)}
            >
              {part}
            </button>
          ) : (
            <span key={`p-${idx}-${i}`}>{part}</span>
          )
        ))}
      </SkillLinkedAssertionLine>
    );
  }

  function renderSemanticLine(line: string, idx: number) {
    const parts = lang === "ZH" ? splitVerdictLine(line) : [t(line)];
    const isH3 = line.trim().startsWith("###");
    const isFallbackLine = line.includes("[SYSTEM_FALLBACK]");
    const isFingerprintLine = line.includes("qiazhi-fingerprint");
    const lineClass = `whitespace-pre-wrap leading-relaxed ${
      isH3 ? "border-l-2 border-emerald-500/50 pl-2 text-emerald-100/95 " : ""
    }${
      summaryChanged
        ? "rounded-md bg-gradient-to-r from-amber-500/10 via-emerald-500/5 to-transparent px-2 py-1 text-emerald-200"
        : "text-emerald-300"
    } ${highlightVerdict ? "text-[1.2rem] font-semibold" : "text-sm"} ${
      isFallbackLine ? "animate-pulse rounded border border-rose-500/35 bg-rose-500/10 px-2 py-1 text-rose-300" : ""
    } ${isFingerprintLine ? "break-all font-mono text-[10px] text-zinc-500" : "break-words"}`;
    return (
      <SkillLinkedAssertionLine
        key={`s-${idx}-${line.slice(0, 12)}`}
        line={line}
        className={lineClass}
        t={t}
      >
        {parts.map((part, i) => (
          isVerdictDeity(part) ? (
            <button
              key={`s-${idx}-${i}-${part}`}
              type="button"
              onClick={() => onVerdictDeityClick?.(part)}
              className="mx-[1px] rounded border border-sky-500/30 bg-sky-500/10 px-1 text-sky-200 hover:bg-sky-500/20"
              title={t("查看 {deity} 的演算路径").replace("{deity}", part)}
            >
              {part}
            </button>
          ) : (
            <span key={`s-${idx}-${i}`}>{part}</span>
          )
        ))}
      </SkillLinkedAssertionLine>
    );
  }

  const sk = verdictSkeleton?.trim() || "";
  const body = useMemo(() => coerceVerdictDisplayBody(verdictBody).trim(), [verdictBody]);
  const hasSemanticBody = Boolean(body);
  const anchorFinal = String(
    (metadata as { verdict_anchor_layer?: { final_verdict?: string } } | undefined)?.verdict_anchor_layer?.final_verdict ||
      "",
  );
  const { semanticMarkdown, fingerprintComment, fingerprintPlain } = useMemo(() => {
    const fp =
      extractQiazhiVerdictFingerprintComment(body) ||
      extractQiazhiVerdictFingerprintComment(anchorFinal) ||
      extractQiazhiVerdictFingerprintComment(llmRaw);
    const enriched = ensureVerdictFingerprintSuffix(body, fp);
    const fpOut = extractQiazhiVerdictFingerprintComment(enriched);
    const fpPlain = fpOut
      ? fpOut
          .replace(/^<!--\s*/, "")
          .replace(/\s*-->$/, "")
          .trim()
      : "";
    const vis = enriched
      .split("\n")
      .filter((ln) => !String(ln).includes("qiazhi-fingerprint"))
      .join("\n");
    return { semanticMarkdown: vis, fingerprintComment: fpOut, fingerprintPlain: fpPlain };
  }, [body, anchorFinal, llmRaw]);

  const hasSkeleton = Boolean(sk);
  const streamingActive = Boolean(
    streamingText && (streamingText.includes("终审") || streamingText.includes("意志")) && !/已完成|保底断言|integration complete/i.test(streamingText),
  );
  const polishPhase = Boolean(body) || streamingActive;
  const emphasizePhysicalSkeleton = highlightVerdict && !hasSemanticBody;
  const showSkeletonProsecutorPulse = !hasSemanticBody || streamingActive;
  const { before: skBeforeRisk, riskBlock } = useMemo(() => splitSkeletonForWillRisk(sk), [sk]);
  const hasTrace =
    traceResultLogs.length > 0 || traceChipLogs.length > 0 || traceConflictLabels.length > 0;
  const canPreInjectToggle = Boolean(
    preInjectionDeityDisplay?.deity_scores && Object.keys(preInjectionDeityDisplay.deity_scores).length > 0,
  );

  const physicalChrome = `rounded-lg border p-2 pr-12 bg-zinc-950/95 border-zinc-700/90 ${
    vfResonance ? "shadow-[0_0_20px_rgba(34,211,238,0.35)] ring-1 ring-cyan-500/40" : "ring-0 shadow-none"
  }`;

  return (
    <div key={`live-verdict-${calculationNonce}-${verdictBodyRenderNonce}`} className="relative space-y-3">
      {hasTrace ? (
        <div className="absolute right-0 top-0 z-10 flex flex-col items-end gap-1">
          <button
            type="button"
            onClick={() => setTraceOpen((v) => !v)}
            className="rounded border border-zinc-600 bg-zinc-900/95 px-2 py-0.5 text-[9px] font-medium text-zinc-300 hover:border-emerald-500/40 hover:text-emerald-200"
          >
            {t("VF · 逻辑溯源")}
          </button>
          {traceOpen ? (
            <div className="max-h-56 w-[min(100%,20rem)] overflow-auto rounded-md border border-zinc-700 bg-zinc-950/98 p-2 text-[10px] text-zinc-300 shadow-xl">
              {traceConflictLabels.length ? (
                <div className="mb-2">
                  <p className="mb-0.5 font-semibold text-amber-200/90">{t("物理扫描点")}</p>
                  <ul className="list-inside list-disc text-zinc-400">
                    {traceConflictLabels.map((x, i) => (
                      <li key={`c-${i}`}>{x}</li>
                    ))}
                  </ul>
                </div>
              ) : null}
              {traceChipLogs.length ? (
                <div className="mb-2">
                  <p className="mb-0.5 font-semibold text-violet-200/90">{t("盲派芯片日志")}</p>
                  <ul className="space-y-0.5 text-zinc-400">
                    {traceChipLogs.map((x, i) => (
                      <li key={`m-${i}`} className="break-words">
                        {x}
                      </li>
                    ))}
                  </ul>
                </div>
              ) : null}
              {traceResultLogs.length ? (
                <div>
                  <p className="mb-0.5 font-semibold text-zinc-200">{t("管线日志")}</p>
                  <ul className="space-y-0.5 font-mono text-[9px] text-zinc-500">
                    {traceResultLogs.map((x, i) => (
                      <li key={`r-${i}`} className="break-words">
                        {x}
                      </li>
                    ))}
                  </ul>
                </div>
              ) : null}
            </div>
          ) : null}
        </div>
      ) : null}

      {canPreInjectToggle ? (
        <div className="absolute right-0 top-7 z-10 flex justify-end">
          <label className="flex cursor-pointer items-center gap-1 rounded border border-zinc-700 bg-zinc-900/90 px-1.5 py-0.5 text-[9px] text-zinc-400 hover:border-sky-500/35">
            <input
              type="checkbox"
              className="accent-sky-500"
              checked={showPreInjectionAbsSnapshot}
              onChange={(e) => onShowPreInjectionAbsSnapshotChange?.(e.target.checked)}
            />
            <span>{t("显示原始物理态")}</span>
          </label>
        </div>
      ) : null}

      {/* Upper · 物理层（事实 / 引擎直出，无内容过渡动画） */}
      {hasSkeleton ? (
        <div className={physicalChrome}>
          <div className="pointer-events-none absolute right-2 top-2 select-none font-mono text-[8px] font-bold uppercase tracking-widest text-zinc-500/90 [text-shadow:0_0_12px_rgba(0,0,0,0.85)]">
            {t("引擎直出")}
          </div>
          <div className="mb-1.5 flex flex-wrap items-center gap-2 border-b border-zinc-800/80 pb-1.5">
            <span className="rounded border border-zinc-600 bg-black/50 px-1.5 py-0.5 text-[9px] font-semibold text-zinc-200">
              {t("物理层 · 事实")}
            </span>
            <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-800/50 bg-emerald-950/40 px-2 py-0.5 text-[9px] text-emerald-200/95">
              <span className="relative flex h-2 w-2">
                {showSkeletonProsecutorPulse ? (
                  <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400/50 opacity-60" />
                ) : null}
                <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-400" />
              </span>
              {t("逻辑检察院 · 实时监控中")}
            </span>
          </div>
          <div className="relative z-[1]">
            {riskBlock ? (
              <div className="space-y-2">
                {skBeforeRisk ? (
                  <div className="space-y-1">
                    {skBeforeRisk.split("\n").map((line, idx) => renderPhysicalLine(line, 9000 + idx, emphasizePhysicalSkeleton))}
                  </div>
                ) : null}
                <div className="rounded-md border border-amber-800/45 bg-black/35 p-2">
                  {riskBlock.split("\n").map((line, idx) => renderPhysicalLine(line, 9500 + idx, emphasizePhysicalSkeleton))}
                </div>
              </div>
            ) : (
              <div className="max-h-52 space-y-1 overflow-y-auto pr-1">
                {sk.split("\n").map((line, idx) => renderPhysicalLine(line, 8000 + idx, emphasizePhysicalSkeleton))}
              </div>
            )}
          </div>
        </div>
      ) : null}

      {physicsAuditDiagnosis?.trim() ? (
        <div className="rounded-lg border border-amber-700/40 bg-amber-950/30 p-2">
          <div className="mb-1 flex flex-wrap items-center gap-2">
            <span className="rounded border border-amber-600/50 bg-amber-900/40 px-1.5 py-0.5 text-[9px] font-semibold text-amber-100">
              {t("审计备忘")}
            </span>
            <span className="text-[10px] text-amber-200/80">{t("物理审计 LLM 定性（终审前即可见）")}</span>
          </div>
          <p className="max-h-40 overflow-y-auto whitespace-pre-wrap text-[11px] leading-relaxed text-amber-50/95">
            {physicsAuditDiagnosis.trim()}
          </p>
        </div>
      ) : null}

      {/* Lower · 语义层（解释 / LLM） */}
      {streamingActive ? (
        <p className="text-[10px] text-cyan-300/90 animate-pulse">{streamingText}</p>
      ) : null}

      {body ? (
        <div className="relative space-y-1 rounded-lg border border-emerald-900/35 bg-zinc-950/80 p-2">
          <div className="mb-1 flex flex-wrap items-center gap-2">
            <span
              className={`rounded border px-1.5 py-0.5 text-[9px] font-semibold uppercase tracking-wide ${
                polishPhase
                  ? "border-emerald-500/50 bg-emerald-500/15 text-emerald-200"
                  : "border-zinc-600 bg-zinc-900 text-zinc-400"
              }`}
            >
              {t("语义层 · 解释")}
            </span>
            <span className="text-[10px] text-zinc-500">{t("流式叙事；与上方物理事实可对照，不替代引擎结论")}</span>
          </div>
          {semanticMarkdown.split("\n").map((x, i) => renderSemanticLine(x, i))}
          {fingerprintComment ? (
            <>
              <div
                className="pointer-events-none h-0 w-0 overflow-hidden opacity-0"
                aria-hidden
                dangerouslySetInnerHTML={{ __html: fingerprintComment }}
              />
              <div className="mt-1 border-t border-emerald-900/30 pt-1">
                <button
                  type="button"
                  onClick={() => setFingerprintOpen((v) => !v)}
                  className="text-[10px] text-emerald-400/90 underline-offset-2 hover:text-emerald-300 hover:underline"
                >
                  {fingerprintOpen ? t("收起逻辑指纹") : t("查看逻辑指纹")}
                </button>
                {fingerprintOpen ? (
                  <pre className="mt-1 max-h-28 overflow-auto rounded border border-zinc-700/80 bg-black/40 p-1.5 font-mono text-[9px] leading-snug text-zinc-400">
                    {fingerprintPlain}
                  </pre>
                ) : (
                  <p className="mt-0.5 text-[9px] text-zinc-600">{t("指纹已写入 DOM 注释，亦可在展开区复制用于审计。")}</p>
                )}
              </div>
            </>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
