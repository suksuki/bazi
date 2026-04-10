"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";
import { EngineRoomPanel } from "@/features/admin/EngineRoomPanel";
import { WaterfallTopology } from "@/features/admin/components/WaterfallTopology";
import { useLabStore } from "@/features/stream-board/stores/useLabStore";

export default function AdminHomePage() {
  const router = useRouter();
  const { state, requestCausalRevert } = useLabStore();
  const [revertFlash, setRevertFlash] = useState(false);
  const [showCompare, setShowCompare] = useState(false);
  const absDelta = state.snapshot?.logic_diff?.abs_delta;
  const baselineAt = state.snapshot?.baseline_snapshot?.at;
  const hasBaseline = Boolean(state.snapshot?.baseline_snapshot);

  const baselinePhysicsDrift = useMemo(() => {
    const current = state.snapshot?.physics_tensor as Record<string, unknown> | undefined;
    const anchor = state.snapshot?.baseline_snapshot?.physics_tensor as Record<string, unknown> | null | undefined;
    if (!current || anchor == null || typeof anchor !== "object") return { hasDrift: false as const };
    const cMeta = (current.meta || {}) as Record<string, unknown>;
    const aMeta = (anchor.meta || {}) as Record<string, unknown>;
    const paramsDrift = JSON.stringify(cMeta.params ?? null) !== JSON.stringify(aMeta.params ?? null);
    const cEntropy = cMeta.global_entropy;
    const aEntropy = aMeta.global_entropy;
    const entropyDrift =
      typeof cEntropy === "number" && typeof aEntropy === "number" && Number.isFinite(cEntropy) && Number.isFinite(aEntropy)
        ? Math.abs(cEntropy - aEntropy) > 1e-6
        : String(cEntropy) !== String(aEntropy);
    const hasDrift = paramsDrift || entropyDrift;
    if (!hasDrift) return { hasDrift: false as const };
    return { hasDrift: true as const, paramsDrift, entropyDrift };
  }, [state.snapshot?.physics_tensor, state.snapshot?.baseline_snapshot?.physics_tensor]);

  const paramsDiffText = useMemo(() => {
    const current = state.snapshot?.physics_tensor as Record<string, unknown> | undefined;
    const anchor = state.snapshot?.baseline_snapshot?.physics_tensor as Record<string, unknown> | null | undefined;
    const cMeta = (current?.meta || {}) as Record<string, unknown>;
    const aMeta = (anchor?.meta || {}) as Record<string, unknown>;
    const cParams = (cMeta.params || {}) as Record<string, unknown>;
    const aParams = (aMeta.params || {}) as Record<string, unknown>;
    const keys = Array.from(new Set([...Object.keys(cParams), ...Object.keys(aParams)])).sort();
    const lines = keys
      .filter((key) => JSON.stringify(cParams[key]) !== JSON.stringify(aParams[key]))
      .map((key) => ({
        key,
        baseline: aParams[key],
        current: cParams[key],
      }));
    if (lines.length === 0) return "{}";
    return JSON.stringify(lines, null, 2);
  }, [state.snapshot?.physics_tensor, state.snapshot?.baseline_snapshot?.physics_tensor]);

  const handleCausalRevert = () => {
    if (!hasBaseline) return;
    setRevertFlash(true);
    window.setTimeout(() => setRevertFlash(false), 80);
    requestCausalRevert();
    router.push("/");
  };

  return (
    <div className="relative space-y-5">
      {revertFlash ? (
        <div
          className="pointer-events-none fixed inset-0 z-[9999] bg-[#A855F7]/40 mix-blend-difference"
          aria-hidden
        />
      ) : null}
      <nav className="flex flex-wrap gap-2">
        <Link href="/admin" className="rounded-lg border border-zinc-700 bg-zinc-800/70 px-3 py-1.5 text-xs text-zinc-200">
          系统设置
        </Link>
        <Link href="/admin/plugins" className="rounded-lg border border-amber-500/40 bg-amber-500/10 px-3 py-1.5 text-xs text-amber-200">
          插件管理
        </Link>
      </nav>

      <div className="rounded-2xl border border-zinc-800 bg-gradient-to-r from-zinc-900 to-zinc-900/50 p-5">
        <h2 className="text-xl font-semibold tracking-tight">管理端总览 · 机房</h2>
        <p className="mt-1 text-sm text-zinc-400">物理参数与插件与主实验室共享同一会话状态（LabConfig）。</p>
      </div>

      <section className="rounded-2xl border border-fuchsia-600/35 bg-fuchsia-950/15 p-4">
        <div className="flex flex-wrap items-start justify-between gap-2">
          <h3 className="text-sm font-medium text-fuchsia-200">基线状态 (Baseline Context)</h3>
          <button
            type="button"
            disabled={!hasBaseline}
            onClick={handleCausalRevert}
            className="shrink-0 rounded-lg border border-fuchsia-500/50 bg-fuchsia-950/40 px-2.5 py-1 text-xs text-fuchsia-100 disabled:cursor-not-allowed disabled:opacity-40"
          >
            ↺ 撤回到锚点
          </button>
        </div>
        <p className="mt-1 text-xs text-zinc-300">
          abs_delta: {typeof absDelta === "number" ? absDelta.toFixed(2) : "--"}
        </p>
        <p className="mt-1 text-xs text-zinc-400">
          baseline_snapshot.at: {baselineAt ? new Date(baselineAt).toLocaleString() : "--"}
        </p>
        {hasBaseline && baselinePhysicsDrift.hasDrift ? (
          <div className="mt-2 rounded-md border border-amber-500/40 bg-amber-500/10 px-2 py-1.5 text-[11px] text-amber-100">
            <div className="flex items-center justify-between gap-2">
              <p>
                基线对照：当前 <code className="text-amber-200">physics_tensor</code> 与锚点在
                {baselinePhysicsDrift.paramsDrift && baselinePhysicsDrift.entropyDrift
                  ? "meta.params 与 global_entropy "
                  : baselinePhysicsDrift.paramsDrift
                    ? "meta.params "
                    : "global_entropy "}
                上不一致，请核对插件权重与重算链。
              </p>
              <button
                type="button"
                onClick={() => setShowCompare((v) => !v)}
                className="shrink-0 rounded border border-amber-400/50 px-1.5 py-0.5 text-[10px] text-amber-200 hover:bg-amber-400/10"
                aria-label="对比详情"
                title="对比详情"
              >
                ≈ Compare
              </button>
            </div>
            {showCompare ? (
              <pre className="mt-2 max-h-44 overflow-auto rounded border border-amber-500/30 bg-zinc-950/60 p-2 text-[10px] leading-relaxed text-amber-100">
                {paramsDiffText}
              </pre>
            ) : null}
          </div>
        ) : null}
      </section>

      <WaterfallTopology />

      <EngineRoomPanel />

      <div className="grid gap-4 md:grid-cols-2">
        <article className="rounded-2xl border border-zinc-800 bg-zinc-900/50 p-5 shadow-lg shadow-black/20">
          <p className="text-xs uppercase tracking-wider text-zinc-500">Infrastructure</p>
          <h3 className="mt-2 text-base font-medium">DB + LLM Settings</h3>
          <p className="mt-2 text-sm text-zinc-400">连接检测、建表、Prompt 游乐场、多语言一致性测试。</p>
          <Link
            href="/admin/settings"
            className="mt-4 inline-flex rounded-lg bg-amber-500 px-4 py-2 text-sm font-medium text-zinc-950 transition hover:bg-amber-400"
          >
            打开设置面板
          </Link>
        </article>
        <article className="rounded-2xl border border-zinc-800 bg-zinc-900/50 p-5 shadow-lg shadow-black/20">
          <p className="text-xs uppercase tracking-wider text-zinc-500">Next</p>
          <h3 className="mt-2 text-base font-medium">逻辑插件准备</h3>
          <p className="mt-2 text-sm text-zinc-400">建议先接入“墓库开闭”插件，优先打通规则解释与决策回放。</p>
          <div className="mt-4 text-xs text-zinc-500">完成基础设施测试后即可进入插件联调。</div>
        </article>
      </div>
    </div>
  );
}
