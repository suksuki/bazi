"use client";

import Link from "next/link";
import { useMemo } from "react";
import { useLabConfig } from "@/features/lab-config/LabConfigContext";
import { usePluginRegistry } from "@/features/admin/hooks/usePluginRegistry";
import type { PluginSwitches, PluginWeights } from "@/features/stream-board/models";

type UiLayer = "L1" | "L2" | "L3" | "L4";
const LAYER_LABEL: Record<UiLayer, string> = {
  L1: "L1 基础 (Base)",
  L2: "L2 功能 (Functional)",
  L3: "L3 现代 (Modern)",
  L4: "L4 战略 (Strategic)",
};

function statusTagClass(status: "HEALTHY" | "IDLE" | "ERROR"): string {
  if (status === "HEALTHY") return "border-emerald-500/40 bg-emerald-500/10 text-emerald-300";
  if (status === "ERROR") return "border-rose-500/40 bg-rose-500/10 text-rose-300";
  return "border-zinc-700 bg-zinc-800/80 text-zinc-300";
}

export function PluginManagementPanel() {
  const {
    pluginSwitches,
    pluginWeights,
    setPluginWeights,
    togglePlugin,
    applyPreset,
  } = useLabConfig();
  const { manifest, isLoading, error, refresh } = usePluginRegistry();

  const rendered = useMemo(() => {
    const plugins = manifest?.plugins || [];
    const pickSwitchKey = (id: string): keyof PluginSwitches | undefined => {
      if (id.includes("blind_school")) return "blindSchool";
      if (id.includes("wangshuai")) return "wangshuai";
      if (id.includes("wealth_risk")) return "wealthRisk";
      return undefined;
    };
    const pickWeightKey = (id: string): keyof PluginWeights | undefined => {
      if (id.includes("blind_school")) return "blindSchool";
      if (id.includes("wangshuai")) return "wangshuai";
      return undefined;
    };

    return plugins.map((plugin) => {
      const switchKey = pickSwitchKey(plugin.id);
      const weightKey = pickWeightKey(plugin.id);
      const mutable = Boolean(switchKey);
      const enabled = switchKey ? Boolean(pluginSwitches[switchKey]) : true;
      return { ...plugin, switchKey, weightKey, mutable, enabled };
    });
  }, [manifest?.plugins, pluginSwitches]);

  const severePolarConflict = useMemo(() => {
    const blindOn = pluginSwitches.blindSchool;
    const wsOn = pluginSwitches.wangshuai;
    if (!blindOn || !wsOn) return false;
    const gap = Math.abs(pluginWeights.blindSchool - pluginWeights.wangshuai);
    return gap > 0.7;
  }, [pluginSwitches.blindSchool, pluginSwitches.wangshuai, pluginWeights.blindSchool, pluginWeights.wangshuai]);

  return (
    <section className="space-y-4 rounded-2xl border border-zinc-800 bg-zinc-900/50 p-4">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="text-lg font-semibold text-zinc-100">插件治理工作台</h3>
          <p className="text-xs text-zinc-400">选拔、挂载、权重校准与依赖巡检（与 LabConfig 实时联动）。</p>
        </div>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={refresh}
            className="rounded-lg border border-violet-500/40 bg-violet-500/10 px-3 py-1.5 text-xs text-violet-200 hover:bg-violet-500/20"
          >
            刷新逻辑注册表
          </button>
          <button
            type="button"
            onClick={() => applyPreset("blind_practical")}
            className="rounded-lg border border-amber-500/40 bg-amber-500/10 px-3 py-1.5 text-xs text-amber-200 hover:bg-amber-500/20"
          >
            预设A：实战盲派
          </button>
          <button
            type="button"
            onClick={() => applyPreset("health_audit")}
            className="rounded-lg border border-sky-500/40 bg-sky-500/10 px-3 py-1.5 text-xs text-sky-200 hover:bg-sky-500/20"
          >
            预设B：健康审计
          </button>
        </div>
      </header>

      <div className={`rounded-xl border px-3 py-2 text-xs ${severePolarConflict ? "border-rose-500/40 bg-rose-500/10 text-rose-200" : "border-emerald-500/30 bg-emerald-500/10 text-emerald-200"}`}>
        实时冲突预览：{severePolarConflict ? "检测到严重极性反转风险（盲派/旺衰权重差过大）" : "当前挂载组合稳定，无严重极性反转"}
      </div>
      {isLoading ? <div className="text-xs text-zinc-400">同步后端 manifest 中…</div> : null}
      {error ? <div className="rounded-lg border border-rose-500/40 bg-rose-500/10 px-3 py-2 text-xs text-rose-200">manifest 拉取失败：{String(error)}</div> : null}

      {(Object.keys(LAYER_LABEL) as UiLayer[]).map((layer) => (
        <div key={layer} className="space-y-2">
          <h4 className="text-sm font-medium text-zinc-200">{LAYER_LABEL[layer]}</h4>
          <div className="grid gap-3 md:grid-cols-2">
            {rendered
              .filter((p) => p.layer === layer)
              .map((plugin) => (
                <article id={`card-${plugin.id}`} key={plugin.id} className="rounded-xl border border-zinc-800 bg-zinc-950/70 p-3">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="text-sm font-medium text-zinc-100">{plugin.metadata?.label || plugin.id}</p>
                      <p className="mt-0.5 font-mono text-[11px] text-zinc-500">{plugin.id}</p>
                    </div>
                    <span className={`rounded-full border px-2 py-0.5 text-[11px] ${statusTagClass(plugin.status)}`}>{plugin.status}</span>
                  </div>

                  <div className="mt-2 flex flex-wrap gap-2 text-[11px] text-zinc-400">
                    <span className="rounded border border-zinc-700 bg-zinc-900 px-2 py-0.5">Priority: {Number(plugin.metadata?.priority || 0).toFixed(2)}</span>
                    <span className="rounded border border-zinc-700 bg-zinc-900 px-2 py-0.5">
                      依赖：{plugin.dependencies.length ? plugin.dependencies.join(" / ") : "无"}
                    </span>
                    <span className="rounded border border-zinc-700 bg-zinc-900 px-2 py-0.5">
                      p95: {plugin.performance_snapshot?.p95_ms != null ? `${Number(plugin.performance_snapshot.p95_ms).toFixed(1)}ms` : "--"}
                    </span>
                  </div>

                  {plugin.mutable ? (
                    <div className="mt-3 flex items-center justify-between rounded-lg border border-zinc-800 bg-zinc-900/70 px-2 py-1.5">
                      <p className="text-xs text-zinc-300">热插拔</p>
                      <button
                        type="button"
                        onClick={() => plugin.switchKey && togglePlugin(plugin.switchKey)}
                        className={`rounded-md px-2 py-1 text-xs ${plugin.enabled ? "bg-emerald-500/20 text-emerald-200" : "bg-zinc-800 text-zinc-300"}`}
                      >
                        {plugin.enabled ? "已启用" : "已停用"}
                      </button>
                    </div>
                  ) : (
                    <div className="mt-3 rounded-lg border border-zinc-800 bg-zinc-900/70 px-2 py-1.5 text-xs text-zinc-400">系统基座插件，不可关闭</div>
                  )}

                  {plugin.weightKey ? (
                    <div className="mt-2 rounded-lg border border-zinc-800 bg-zinc-900/70 px-2 py-2">
                      <label className="text-xs text-zinc-300">
                        初始话语权：{pluginWeights[plugin.weightKey].toFixed(2)}
                        <input
                          type="range"
                          min={0}
                          max={1}
                          step={0.05}
                          value={pluginWeights[plugin.weightKey]}
                          onChange={(e) => {
                            const next = Number(e.target.value);
                            setPluginWeights((prev) => ({ ...prev, [plugin.weightKey!]: next }));
                          }}
                          className="mt-1 w-full"
                        />
                      </label>
                    </div>
                  ) : null}

                  <div className="mt-3 flex items-center justify-between">
                    <span className={`text-xs ${plugin.status === "ERROR" ? "text-rose-300" : "text-emerald-300"}`}>
                      Hook: {plugin.metadata?.hook || "--"}
                    </span>
                    <Link
                      href={plugin.metadata?.doc_path || "/docs"}
                      className="text-xs text-amber-300 underline-offset-2 hover:underline"
                    >
                      查看理论手册
                    </Link>
                  </div>
                </article>
              ))}
          </div>
        </div>
      ))}
    </section>
  );
}

