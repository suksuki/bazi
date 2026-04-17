"use client";

import { motion } from "framer-motion";
import { useEffect, useMemo, useRef, useState } from "react";
import type { Lang } from "@/types/bazi";
import type { DeityEnergyAxis, PatternThresholdRow } from "@/features/stream-board/models";
import { detectPhaseTransitionSurge, maxPatternProgress } from "@/features/stream-board/utils/LogicWarpingAura";
import { flashPhaseTransitionToast } from "@/utils/globalUiEvents";
import { isVerdictDeity, splitVerdictLine } from "@/features/decision-inbox/utils";
import { SkillLinkedAssertionLine } from "@/features/stream-board/components/ResultInterpretation";
import { useLabStore } from "@/features/stream-board/stores/useLabStore";
import {
  coerceVerdictDisplayBody,
  ensureVerdictFingerprintSuffix,
  extractQiazhiVerdictFingerprintComment,
} from "@/features/stream-board/controller/verdictBodyStream";
import { mapConflictDetail } from "@/constants/termMap";
import { translateVerdictSkeletonLine } from "@/utils/semanticTranslator";
import { WillCorrectionNarrative } from "@/features/stream-board/components/LogicAuditNarrator";
import type { UserIntentionId } from "@/features/stream-board/models";
import { ArbiterLogicDrawer } from "@/components/ArbiterLogicDrawer";

const WILL_RISK_HEADER = "### 风险预警 (意志对垒)";

export type LiveVerdictDisplayProps = {
  verdictSkeleton: string | null;
  /** 影子预览：悬停 Inbox 卡时流式发现的 VF（淡紫斜体 + PREVIEW） */
  previewVfSkeleton?: string | null;
  /** 结构预览：格局跃迁 / 平衡点重塑预警（与 SkillLinkedAssertionLine 同语义高亮轨） */
  previewPatternAlert?: string | null;
  /** 预览态格局引力水位（相变探测器） */
  previewPatternThresholds?: PatternThresholdRow[] | null;
  verdictBody: string;
  /** 第二轮物理审计 LLM 定性（与终判解耦，先写裁决舱备忘） */
  physicsAuditDiagnosis?: string | null;
  metadata?: Record<string, unknown>;
  /** 与实验室 snapshot.physics_tensor 对齐：用于 [SYSTEM_FALLBACK] 时强制穿插 semantic_label_bundle_v1（意志对齐脱水） */
  physicsTensor?: Record<string, unknown> | null;
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
  /** V11：与 physics_config.user_intention 对齐，终审语义区插入意志修正说明 */
  userIntention?: UserIntentionId | "" | undefined;
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
  previewVfSkeleton = null,
  previewPatternAlert = null,
  previewPatternThresholds = null,
  verdictBody,
  physicsAuditDiagnosis = null,
  metadata = {},
  physicsTensor = null,
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
  userIntention,
}: LiveVerdictDisplayProps) {
  const [vfResonance, setVfResonance] = useState(false);
  const [auditDrawerOpen, setAuditDrawerOpen] = useState(false);
  const [phaseLockAura, setPhaseLockAura] = useState(false);
  const [phaseLockWarning, setPhaseLockWarning] = useState(false);
  const prevResonanceRef = useRef(physResonanceKey);
  const prevPreviewPatternMaxRef = useRef<number | null>(null);
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

  useEffect(() => {
    const rows = previewPatternThresholds;
    if (!rows?.length) {
      prevPreviewPatternMaxRef.current = null;
      return;
    }
    const nextMax = maxPatternProgress(rows);
    const prevMax = prevPreviewPatternMaxRef.current;
    prevPreviewPatternMaxRef.current = nextMax;
    if (prevMax == null) return;
    if (!detectPhaseTransitionSurge(prevMax, nextMax)) return;
    setPhaseLockAura(true);
    setPhaseLockWarning(true);
    flashPhaseTransitionToast(t("phase.lock.toast"));
    const a = window.setTimeout(() => {
      setPhaseLockAura(false);
      setPhaseLockWarning(false);
    }, 2800);
    return () => {
      window.clearTimeout(a);
    };
  }, [previewPatternThresholds, t]);

  function renderPhysicalLine(line: string, idx: number, emphasizeSkeleton: boolean) {
    const parts = splitVerdictLine(line);
    const hasDeityToken = parts.some((p) => isVerdictDeity(p));
    const isH3 = line.trim().startsWith("###");
    const isFingerprintLine = line.includes("qiazhi-fingerprint");
    const lineClass = `whitespace-pre-wrap leading-relaxed ${
      isH3 ? "border-l-2 border-zinc-500/50 pl-2 text-zinc-100/95 " : ""
    } text-zinc-300/95 text-sm ${
      emphasizeSkeleton && highlightVerdict ? "text-[1.05rem] font-medium" : ""
    } ${isFingerprintLine ? "break-all font-mono text-[10px] text-zinc-500" : "break-words"}`;
    const renderLocalized = () => {
      if (lang === "ZH") {
        return parts.map((part, i) =>
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
          ),
        );
      }
      if (!hasDeityToken) {
        return <span>{translateVerdictSkeletonLine(line, lang)}</span>;
      }
      return parts.map((part, i) =>
        isVerdictDeity(part) ? (
          <button
            key={`p-${idx}-${i}-${part}`}
            type="button"
            onClick={() => onVerdictDeityClick?.(part)}
            className="mx-[1px] rounded border border-sky-600/35 bg-sky-950/40 px-1 text-sky-200/95 hover:bg-sky-900/50"
            title={t("查看 {deity} 的演算路径").replace("{deity}", part)}
          >
            {mapConflictDetail(part, lang)}
          </button>
        ) : (
          <span key={`p-${idx}-${i}`}>{translateVerdictSkeletonLine(part, lang)}</span>
        ),
      );
    };
    return (
      <SkillLinkedAssertionLine
        key={`p-${idx}-${line.slice(0, 12)}`}
        line={line}
        className={lineClass}
        t={t}
      >
        {renderLocalized()}
      </SkillLinkedAssertionLine>
    );
  }

  function renderSemanticLine(line: string, idx: number) {
    const parts = splitVerdictLine(line);
    const hasDeityToken = parts.some((p) => isVerdictDeity(p));
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
    const renderSemanticLocalized = () => {
      if (lang === "ZH") {
        return parts.map((part, i) =>
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
          ),
        );
      }
      if (!hasDeityToken) {
        return <span>{t(line)}</span>;
      }
      return parts.map((part, i) =>
        isVerdictDeity(part) ? (
          <button
            key={`s-${idx}-${i}-${part}`}
            type="button"
            onClick={() => onVerdictDeityClick?.(part)}
            className="mx-[1px] rounded border border-sky-500/30 bg-sky-500/10 px-1 text-sky-200 hover:bg-sky-500/20"
            title={t("查看 {deity} 的演算路径").replace("{deity}", part)}
          >
            {mapConflictDetail(part, lang)}
          </button>
        ) : (
          <span key={`s-${idx}-${i}`}>{t(part)}</span>
        ),
      );
    };
    return (
      <SkillLinkedAssertionLine
        key={`s-${idx}-${line.slice(0, 12)}`}
        line={line}
        className={lineClass}
        t={t}
      >
        {renderSemanticLocalized()}
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
  const { semanticMarkdown, semanticMainPure, fingerprintComment, fingerprintPlain } = useMemo(() => {
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
    let vis = enriched
      .split("\n")
      .filter((ln) => !String(ln).includes("qiazhi-fingerprint"))
      .join("\n");
    const meta = physicsTensor?.meta as Record<string, unknown> | undefined;
    const bundle = meta?.semantic_label_bundle_v1 as { verified_fact_lines?: unknown } | undefined;
    const vfLines = Array.isArray(bundle?.verified_fact_lines)
      ? bundle!.verified_fact_lines!.map((x) => String(x).trim()).filter(Boolean).slice(0, 28)
      : [];
    if (vfLines.length && vis.includes("[SYSTEM_FALLBACK]")) {
      const inj = ["### 意志对齐（语义标签 VF）", ...vfLines.map((l) => `- ${l}`), ""];
      vis = [...inj, vis].join("\n");
    }
    const lines = vis.split("\n");
    const keepHeads = new Set(["【裁断】", "【证据】", "【行】", "【禁】"]);
    let keep = false;
    const pure: string[] = [];
    for (const rawLine of lines) {
      const ln = String(rawLine || "");
      const trimmed = ln.trim();
      if (keepHeads.has(trimmed)) {
        keep = true;
        pure.push(trimmed);
        continue;
      }
      if (trimmed.startsWith("【") && trimmed.endsWith("】")) {
        keep = false;
        continue;
      }
      if (!keep) continue;
      pure.push(
        ln
          .replace(/Fact_ID\s*[:=]?\s*[a-zA-Z0-9_-]*/gi, "证据锚点")
          .replace(/\b(sys\.core|metadata|trace|logic)\b/gi, "盘面脉络"),
      );
    }
    const pureBody = pure.join("\n").trim();
    return {
      semanticMarkdown: vis,
      semanticMainPure: pureBody || vis,
      fingerprintComment: fpOut,
      fingerprintPlain: fpPlain,
    };
  }, [body, anchorFinal, llmRaw, physicsTensor]);

  const previewSk = String(previewVfSkeleton || "").trim();
  const hasPreviewVf = Boolean(previewSk);
  const patternAlert = String(previewPatternAlert || "").trim();
  const hasPatternAlert = Boolean(patternAlert);
  const hasSkeleton = Boolean(sk);
  const streamingActive = Boolean(
    streamingText &&
      (streamingText.includes("终审") ||
        streamingText.includes("意志") ||
        /final\s*verdict|will\s+is|reshaping/i.test(streamingText) ||
        /최종\s*판|의지/.test(streamingText)) &&
      !/已完成|保底断言|integration complete|completed/i.test(streamingText),
  );
  const polishPhase = Boolean(body) || streamingActive;
  const emphasizePhysicalSkeleton = highlightVerdict && !hasSemanticBody;
  const showSkeletonProsecutorPulse = !hasSemanticBody || streamingActive;
  const { before: skBeforeRisk, riskBlock } = useMemo(() => splitSkeletonForWillRisk(sk), [sk]);
  const hasTrace = traceResultLogs.length > 0 || traceChipLogs.length > 0 || traceConflictLabels.length > 0;
  const hasAuditPayload = Boolean(fingerprintPlain || hasTrace || /Fact_ID\s*[:=]/i.test(semanticMarkdown));
  const canPreInjectToggle = Boolean(
    preInjectionDeityDisplay?.deity_scores && Object.keys(preInjectionDeityDisplay.deity_scores).length > 0,
  );

  const physicalChrome = useMemo(() => {
    const base = "rounded-lg border p-2 pr-12 bg-zinc-950/95 border-zinc-700/90";
    if (phaseLockAura) return `${base} phase-lock-aura ring-2 ring-amber-400/40`;
    if (vfResonance) return `${base} shadow-[0_0_20px_rgba(34,211,238,0.35)] ring-1 ring-cyan-500/40`;
    return `${base} ring-0 shadow-none`;
  }, [vfResonance, phaseLockAura]);

  const patternAlertCritical = patternAlert.includes("[CRITICAL]");
  const renderPatternAlertBand = () => (
    <div
      className={
        patternAlertCritical
          ? "relative rounded-lg border border-rose-500/45 bg-rose-950/35 p-2 pr-10"
          : "rounded-lg border border-amber-500/40 bg-amber-950/30 p-2 pr-10"
      }
    >
      <div className="mb-1 flex flex-wrap items-center gap-2">
        <span
          className={
            patternAlertCritical
              ? "rounded border border-rose-400/55 bg-rose-950/50 px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-wide text-rose-100"
              : "rounded border border-amber-400/55 bg-amber-950/45 px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-wide text-amber-100"
          }
        >
          {t("格局预警")}
        </span>
        <span
          className={
            patternAlertCritical
              ? "text-[10px] font-medium text-rose-200/90"
              : "text-[10px] font-medium text-amber-200/85"
          }
        >
          PREVIEW · {t("签发前风险提示")}
        </span>
      </div>
      <SkillLinkedAssertionLine
        line={patternAlert}
        className={
          patternAlertCritical
            ? "text-[11px] leading-relaxed text-rose-50/95"
            : "text-[11px] leading-relaxed text-amber-50/95"
        }
        t={t}
      >
        <span className="whitespace-pre-wrap">{patternAlert}</span>
      </SkillLinkedAssertionLine>
      {patternAlertCritical ? (
        <span
          className="absolute right-2 top-2 inline-flex h-5 w-5 cursor-help items-center justify-center rounded-full border border-rose-400/50 bg-rose-950/60 text-[11px] font-semibold text-rose-100/90 hover:border-rose-300/60 hover:bg-rose-900/70"
          title={t("critical.alert.help")}
          role="img"
          aria-label={t("critical.alert.help")}
        >
          ?
        </span>
      ) : null}
    </div>
  );

  return (
    <div key={`live-verdict-${calculationNonce}-${verdictBodyRenderNonce}`} className="relative space-y-3">
      {null}

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
      {hasPreviewVf ? (
        <div className="rounded-lg border border-fuchsia-500/35 bg-fuchsia-950/20 p-2 pr-10">
          <div className="mb-1 flex flex-wrap items-center gap-2">
            <span className="rounded border border-fuchsia-400/50 bg-fuchsia-950/50 px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-wide text-fuchsia-200">
              PREVIEW
            </span>
            <span className="text-[10px] italic text-fuchsia-200/85">{t("影子预览 · 未签发")}</span>
          </div>
          <div className="max-h-36 space-y-0.5 overflow-y-auto text-[11px] italic leading-relaxed text-fuchsia-100/90">
            {previewSk.split("\n").map((line, idx) => (
              <p
                key={`pvf-${idx}`}
                className={`whitespace-pre-wrap ${String(line).includes("[PREVIEW]") ? "animate-pulse" : ""}`}
              >
                {line}
              </p>
            ))}
          </div>
        </div>
      ) : null}
      {hasPatternAlert && !hasSemanticBody ? renderPatternAlertBand() : null}
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

      {physicsAuditDiagnosis?.trim() || phaseLockWarning ? (
        <div className="rounded-lg border border-amber-700/40 bg-amber-950/30 p-2">
          <div className="mb-1 flex flex-wrap items-center gap-2">
            <span className="rounded border border-amber-600/50 bg-amber-900/40 px-1.5 py-0.5 text-[9px] font-semibold text-amber-100">
              {t("审计备忘")}
            </span>
            <span className="text-[10px] text-amber-200/80">{t("物理审计 LLM 定性（终审前即可见）")}</span>
          </div>
          {phaseLockWarning ? (
            <p className="mb-1.5 text-[11px] font-medium leading-snug phase-lock-warning-blink">{t("phase.lock.warning")}</p>
          ) : null}
          {physicsAuditDiagnosis?.trim() ? (
            <p className="max-h-40 overflow-y-auto whitespace-pre-wrap text-[11px] leading-relaxed text-amber-50/95">
              {physicsAuditDiagnosis.trim()}
            </p>
          ) : null}
        </div>
      ) : null}

      {/* Lower · 语义层（解释 / LLM） */}
      {streamingActive ? (
        <motion.p
          layout="position"
          className="text-[10px] text-cyan-300/90"
          transition={{ layout: { duration: 0.28, ease: "easeOut" } }}
        >
          {streamingText}
        </motion.p>
      ) : null}

      {body ? (
        <motion.div
          key={`fv-sem-${verdictBodyRenderNonce}-${calculationNonce}-${body.length}`}
          className="relative space-y-1 rounded-lg border border-emerald-900/35 bg-zinc-950/80 p-2"
          initial={{ opacity: 0.88 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.38, ease: [0.22, 1, 0.36, 1] }}
        >
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
            {hasAuditPayload ? (
              <button
                type="button"
                onClick={() => setAuditDrawerOpen(true)}
                className="ml-auto rounded border border-zinc-700 bg-zinc-900/80 px-1.5 py-0.5 text-[9px] text-zinc-300 hover:border-emerald-500/40 hover:text-emerald-200"
              >
                {t("查看审计抽屉")}
              </button>
            ) : null}
          </div>
          {hasPatternAlert && hasSemanticBody ? <div className="mb-2">{renderPatternAlertBand()}</div> : null}
          <WillCorrectionNarrative userIntention={userIntention} t={t} className="mb-2" />
          {semanticMainPure.split("\n").map((x, i) => renderSemanticLine(x, i))}
          {fingerprintComment ? (
            <div
              className="pointer-events-none h-0 w-0 overflow-hidden opacity-0"
              aria-hidden
              dangerouslySetInnerHTML={{ __html: fingerprintComment }}
            />
          ) : null}
        </motion.div>
      ) : null}
      <ArbiterLogicDrawer
        open={auditDrawerOpen}
        title={t("Arbiter 审计抽屉")}
        focus={t("终判审计轨迹")}
        details={[
          ...traceConflictLabels.map((x) => `物理扫描点：${x}`),
          ...traceChipLogs.map((x) => `芯片日志：${x}`),
          ...traceResultLogs.map((x) => `管线日志：${x}`),
          ...(fingerprintPlain ? [`SHA-256：${fingerprintPlain}`] : []),
        ]}
        auditSource={{
          fingerprint: fingerprintPlain || null,
          fact_refs: (semanticMarkdown.match(/Fact_ID\s*[:=]?\s*[a-zA-Z0-9_-]+/gi) || []).slice(0, 32),
        }}
        onClose={() => setAuditDrawerOpen(false)}
      />
    </div>
  );
}
