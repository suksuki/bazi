"use client";

import { useEffect, useMemo, useRef, useState } from "react";

type Mode = "FULL" | "SEMANTIC" | "SYNCING" | "PARAMETER_DIRTY";

type Props = {
  mode: Mode;
  globalEntropy?: number | null;
  decisionDirty?: boolean;
  onRun: () => void | Promise<void>;
  onSetBaseline?: () => void;
  disabled?: boolean;
  sigShiftFlashKey?: number;
  /** 覆盖主按钮文案（终审状态机等） */
  labelOverride?: string;
  /** 已签发：主按钮锁定 */
  issued?: boolean;
  /** 可签发终审：紫色呼吸主按钮 */
  issueFinalPurplePulse?: boolean;
  /** UI 文案（ZH 为恒等，EN/KO 走静态表或翻译队列） */
  t?: (s: string) => string;
  /** 主操作下方脚注（如物理态「无变化」提示） */
  actionFootnote?: string;
  /** 错误脚注（优先于 successFootnote / actionFootnote 展示） */
  errorFootnote?: string;
  /** 成功/结果脚注（如「计算完成」或收敛稳态） */
  successFootnote?: string;
  /** 预留：主按钮额外灰态（与 issued 区分）；当前流式盘面对外恒为 false */
  mainActionConverged?: boolean;
  /** V13.05：SYNCING 时在主按钮左侧显示转圈（全量掐指等） */
  busySpinner?: boolean;
};

export function UnifiedActionBar({
  mode,
  globalEntropy,
  decisionDirty = false,
  onRun,
  onSetBaseline,
  disabled = false,
  sigShiftFlashKey = 0,
  labelOverride,
  issued = false,
  issueFinalPurplePulse = false,
  t = (s: string) => s,
  actionFootnote,
  errorFootnote,
  successFootnote,
  mainActionConverged = false,
  busySpinner = false,
}: Props) {
  const label =
    labelOverride ??
    (mode === "SYNCING"
      ? t("逻辑坍缩中...")
      : mode === "FULL"
        ? t("物理排盘：开启因果")
        : mode === "PARAMETER_DIRTY"
          ? t("[因果确认：执行裁决]")
        : t("语义重构：重新裁决"));
  const entropyPct = typeof globalEntropy === "number" && Number.isFinite(globalEntropy)
    ? Math.max(0, Math.min(100, Math.round(globalEntropy * 100)))
    : 0;
  const entropy = typeof globalEntropy === "number" && Number.isFinite(globalEntropy) ? Math.max(0, Math.min(1, globalEntropy)) : 0;
  const activeMotion = mode === "SYNCING";
  const tremorIntensity = activeMotion && entropy > 0.8 ? Math.max(0, Math.min(1, (entropy - 0.8) / 0.2)) : 0;
  const glitchIntensity = activeMotion && entropy > 0.85 ? Math.max(0, Math.min(1, (entropy - 0.85) / 0.15)) : 0;
  const [offset, setOffset] = useState({ x: 0, y: 0 });
  const [glitchOn, setGlitchOn] = useState(false);
  const [burstOn, setBurstOn] = useState(false);
  const [willPulseOn, setWillPulseOn] = useState(false);
  const [baselineFlash, setBaselineFlash] = useState(false);
  const [baselineHint, setBaselineHint] = useState("");
  const [sigShiftShow, setSigShiftShow] = useState(false);
  const [sigShiftBright, setSigShiftBright] = useState(true);
  const jitterTimerRef = useRef<number | null>(null);
  const glitchTimerRef = useRef<number | null>(null);
  const burstTimerRef = useRef<number | null>(null);
  const willPulseTimerRef = useRef<number | null>(null);

  const reducedMotion = useMemo(() => {
    if (typeof window === "undefined" || !window.matchMedia) return false;
    return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  }, []);

  const ambientTremor = !reducedMotion && mode === "SYNCING" && entropy > 0.8;
  const decisionDirtyPulse = !reducedMotion && mode === "PARAMETER_DIRTY" && decisionDirty && !issueFinalPurplePulse;
  const issuePulse = !reducedMotion && issueFinalPurplePulse && mode !== "SYNCING" && !issued;
  const [issuePulseOn, setIssuePulseOn] = useState(false);
  const tremorStartedAtRef = useRef<number | null>(null);

  useEffect(() => {
    if (!decisionDirtyPulse) {
      setWillPulseOn(false);
      if (willPulseTimerRef.current) window.clearInterval(willPulseTimerRef.current);
      willPulseTimerRef.current = null;
      return;
    }
    const interval = Math.max(360, 1080 - Math.round(entropy * 520));
    if (willPulseTimerRef.current) window.clearInterval(willPulseTimerRef.current);
    willPulseTimerRef.current = window.setInterval(() => {
      setWillPulseOn((prev) => !prev);
    }, interval);
    return () => {
      if (willPulseTimerRef.current) window.clearInterval(willPulseTimerRef.current);
    };
  }, [decisionDirtyPulse, entropy]);

  useEffect(() => {
    if (!issuePulse) {
      setIssuePulseOn(false);
      return;
    }
    const interval = 520;
    const iv = window.setInterval(() => setIssuePulseOn((v) => !v), interval);
    return () => window.clearInterval(iv);
  }, [issuePulse]);

  useEffect(() => {
    if (!ambientTremor) {
      setOffset({ x: 0, y: 0 });
      tremorStartedAtRef.current = null;
      if (jitterTimerRef.current) window.clearInterval(jitterTimerRef.current);
      jitterTimerRef.current = null;
      return;
    }
    if (!tremorStartedAtRef.current) tremorStartedAtRef.current = Date.now();
    const maxShift = 1.5;
    if (jitterTimerRef.current) window.clearInterval(jitterTimerRef.current);
    jitterTimerRef.current = window.setInterval(() => {
      if (tremorStartedAtRef.current && Date.now() - tremorStartedAtRef.current > 1200) {
        setOffset({ x: 0, y: 0 });
        if (jitterTimerRef.current) window.clearInterval(jitterTimerRef.current);
        jitterTimerRef.current = null;
        return;
      }
      const x = (Math.random() * 2 - 1) * maxShift;
      const y = (Math.random() * 2 - 1) * maxShift;
      setOffset({ x, y });
    }, 145);
    return () => {
      if (jitterTimerRef.current) window.clearInterval(jitterTimerRef.current);
    };
  }, [ambientTremor, entropy, mode]);

  useEffect(() => {
    if (reducedMotion || glitchIntensity <= 0) {
      setGlitchOn(false);
      if (glitchTimerRef.current) window.clearInterval(glitchTimerRef.current);
      glitchTimerRef.current = null;
      return;
    }
    if (glitchTimerRef.current) window.clearInterval(glitchTimerRef.current);
    glitchTimerRef.current = window.setInterval(() => {
      setGlitchOn(true);
      window.setTimeout(() => setGlitchOn(false), 150);
    }, Math.max(500, 900 - Math.round(glitchIntensity * 260)));
    return () => {
      if (glitchTimerRef.current) window.clearInterval(glitchTimerRef.current);
    };
  }, [reducedMotion, glitchIntensity]);

  useEffect(() => {
    if (!activeMotion) {
      setOffset({ x: 0, y: 0 });
      setGlitchOn(false);
    }
  }, [activeMotion]);

  useEffect(() => {
    return () => {
      if (burstTimerRef.current) window.clearTimeout(burstTimerRef.current);
    };
  }, []);

  const mainButtonDisabled = disabled || mode === "SYNCING" || issued || mainActionConverged;

  useEffect(() => {
    if (sigShiftFlashKey < 1) return;
    setSigShiftShow(true);
    let ticks = 0;
    const iv = window.setInterval(() => {
      ticks += 1;
      setSigShiftBright((b) => !b);
      if (ticks >= 12) {
        window.clearInterval(iv);
        setSigShiftShow(false);
      }
    }, 200);
    return () => window.clearInterval(iv);
  }, [sigShiftFlashKey]);

  const handleRun = () => {
    if (mainActionConverged && mode !== "SYNCING") return;
    if (!reducedMotion) {
      setBurstOn(true);
      setGlitchOn(true);
      if (burstTimerRef.current) window.clearTimeout(burstTimerRef.current);
      burstTimerRef.current = window.setTimeout(() => {
        setBurstOn(false);
        if (glitchIntensity <= 0) setGlitchOn(false);
      }, 180);
    }
    void onRun();
  };
  const handleSetBaseline = () => {
    if (!onSetBaseline) return;
    onSetBaseline();
    setBaselineFlash(true);
    setGlitchOn(true);
    setBaselineHint(t("因果锚点已固化"));
    window.setTimeout(() => {
      setBaselineFlash(false);
      if (glitchIntensity <= 0) setGlitchOn(false);
    }, 150);
    window.setTimeout(() => setBaselineHint(""), 1200);
  };
  const glitchSlice = `polygon(0 ${12 + Math.random() * 40}%, 100% ${6 + Math.random() * 30}%, 100% ${48 + Math.random() * 30}%, 0 ${55 + Math.random() * 28}%)`;

  return (
    <section
      className="sticky bottom-[max(0.75rem,env(safe-area-inset-bottom))] rounded-2xl border border-zinc-700 bg-zinc-950/92 p-3 backdrop-blur-md transition-transform duration-150"
      style={{ transform: `translate(${offset.x}px, ${offset.y}px)`, zIndex: glitchOn || burstOn ? 60 : 30 }}
    >
      <div className="mb-2 h-1.5 w-full overflow-hidden rounded bg-zinc-800">
        <div
          className={`h-full rounded transition-all ${mode === "SYNCING" ? "animate-pulse bg-gradient-to-r from-violet-500 via-fuchsia-500 to-amber-400" : "bg-gradient-to-r from-cyan-500 to-violet-500"}`}
          style={{ width: `${entropyPct}%` }}
        />
      </div>
      <div className="flex items-center justify-between gap-3">
        <div className="relative flex-1">
          <button
            type="button"
            disabled={mainButtonDisabled}
            onClick={handleRun}
            className={`relative z-10 w-full rounded-xl py-2.5 text-sm font-semibold disabled:cursor-not-allowed ${
              issued
                ? "bg-zinc-700 text-zinc-200 disabled:opacity-60"
                : mainActionConverged && mode !== "SYNCING"
                  ? "cursor-not-allowed border border-zinc-600 bg-zinc-700 text-zinc-200 opacity-90 disabled:opacity-90"
                  : issueFinalPurplePulse
                    ? `bg-gradient-to-r from-violet-600 to-fuchsia-600 text-white shadow-lg transition-[box-shadow,filter] duration-500 disabled:opacity-60 ${
                        issuePulseOn ? "shadow-[0_0_22px_rgba(168,85,247,0.55)] brightness-110" : "shadow-[0_0_10px_rgba(168,85,247,0.25)]"
                      }`
                    : "bg-amber-500 text-zinc-950 disabled:opacity-60"
            }`}
            style={decisionDirtyPulse ? {
              border: `1px solid rgba(168,85,247,${willPulseOn ? 0.95 : 0.45})`,
              boxShadow: `0 0 ${willPulseOn ? 14 : 8}px rgba(168,85,247,${willPulseOn ? 0.42 : 0.18})`,
            } : undefined}
          >
            <span className="flex items-center justify-center gap-2">
              {busySpinner && mode === "SYNCING" ? (
                <span
                  className="inline-block size-3.5 shrink-0 animate-spin rounded-full border-2 border-current border-t-transparent opacity-90"
                  aria-hidden
                />
              ) : null}
              <span className="line-clamp-2 text-center leading-snug">{label}</span>
            </span>
          </button>
          {glitchOn || burstOn ? (
            <>
              <div
                className="pointer-events-none absolute inset-0 z-20 rounded-xl bg-fuchsia-400/15"
                style={{
                  clipPath: glitchSlice,
                  transform: `translateX(${(Math.random() * 2 - 1) * (2 + glitchIntensity * 3)}px)`,
                  mixBlendMode: "exclusion",
                  filter: "contrast(120%) saturate(150%)",
                }}
              />
              <div
                className="pointer-events-none absolute inset-0 z-30 rounded-xl"
                style={{
                  background: "rgba(255, 0, 80, 0.05)",
                  clipPath: glitchSlice,
                  transform: "translateX(-1.5px)",
                  mixBlendMode: "screen",
                  filter: "contrast(120%) saturate(150%)",
                }}
              />
              <div
                className="pointer-events-none absolute inset-0 z-30 rounded-xl"
                style={{
                  background: "rgba(0, 180, 255, 0.05)",
                  clipPath: glitchSlice,
                  transform: "translateX(1.5px)",
                  mixBlendMode: "screen",
                  filter: "contrast(120%) saturate(150%)",
                }}
              />
            </>
          ) : null}
        </div>
        <button
          type="button"
          onClick={handleSetBaseline}
          disabled={!onSetBaseline || disabled || mode === "SYNCING" || issued}
          aria-label={t("设置当前为基线")}
          className={`shrink-0 rounded-md border px-2 py-1 text-xs transition ${
            baselineFlash
              ? "border-[#A855F7] bg-fuchsia-500/20 text-fuchsia-100 shadow-[0_0_14px_rgba(168,85,247,0.55)]"
              : "border-zinc-700 bg-zinc-900 text-zinc-300 hover:bg-zinc-800"
          } disabled:cursor-not-allowed disabled:opacity-50`}
          title={baselineHint || t("设置当前为基线")}
        >
          ⚓
        </button>
      </div>
      {errorFootnote ? (
        <p className="mt-1 text-center text-[10px] leading-snug text-rose-300">{errorFootnote}</p>
      ) : successFootnote ? (
        <p className="mt-1 text-center text-[10px] leading-snug text-emerald-200/95">{successFootnote}</p>
      ) : actionFootnote ? (
        <p className="mt-1 text-center text-[10px] leading-snug text-cyan-200/90">{actionFootnote}</p>
      ) : null}
      {baselineHint ? <p className="mt-1 text-[10px] text-fuchsia-300">{baselineHint}</p> : null}
      {sigShiftShow ? (
        <p
          className={`mt-1 text-center font-mono text-[10px] text-[#A855F7] transition-opacity duration-150 ${
            sigShiftBright ? "opacity-100" : "opacity-30"
          }`}
        >
          [SIG_SHIFT]
        </p>
      ) : null}
    </section>
  );
}

