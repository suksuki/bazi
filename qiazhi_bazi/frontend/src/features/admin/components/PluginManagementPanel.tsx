"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { useLabConfig } from "@/features/lab-config/LabConfigContext";
import { usePluginRegistry, type BlindSchoolSkillItem } from "@/features/admin/hooks/usePluginRegistry";
import { useLabStore } from "@/features/stream-board/stores/useLabStore";
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

function runtimePhysicsNumber(
  pt: Record<string, unknown> | undefined,
  key: string,
): number | null {
  if (!pt) return null;
  const meta = (pt.meta || {}) as Record<string, unknown>;
  const rcfg = (meta.runtime_physics_config || {}) as Record<string, unknown>;
  const v = rcfg[key];
  if (typeof v === "number" && Number.isFinite(v)) return v;
  const plugins = (pt.plugin_outputs || {}) as Record<string, unknown>;
  const blind = (plugins["classical.blind_school.v1"] || {}) as Record<string, unknown>;
  const payload = (blind.payload || {}) as Record<string, unknown>;
  const wvCfg = (payload.runtime_physics_config || {}) as Record<string, unknown>;
  const w = wvCfg[key];
  if (typeof w === "number" && Number.isFinite(w)) return w;
  return null;
}

function BlindSchoolSkillList({
  skills,
  physicsTensor,
}: {
  skills: BlindSchoolSkillItem[];
  physicsTensor: Record<string, unknown> | undefined;
}) {
  const [openId, setOpenId] = useState<string | null>(null);
  if (!skills.length) return null;
  return (
    <div className="mt-2 rounded-lg border border-zinc-700/80 bg-zinc-900/60 px-2 py-2">
      <p className="mb-1.5 text-[10px] font-medium uppercase tracking-wide text-zinc-500">已加载 Skill 列表</p>
      <div className="flex flex-wrap gap-1.5">
        {skills.map((s) => {
          const active = openId === s.id;
          const settingKey = s.physics_setting_key;
          const live =
            settingKey != null && settingKey !== ""
              ? runtimePhysicsNumber(physicsTensor, settingKey)
              : null;
          return (
            <button
              key={s.id}
              type="button"
              onClick={() => setOpenId(active ? null : s.id)}
              className={`rounded-full border px-2 py-0.5 text-[10px] transition-colors ${
                active
                  ? "border-violet-400/60 bg-violet-500/20 text-violet-100"
                  : "border-zinc-600 bg-zinc-800/90 text-zinc-300 hover:border-zinc-500 hover:text-zinc-100"
              }`}
            >
              {s.name}
              {live != null ? (
                <span className="ml-1 font-mono text-[9px] text-amber-200/90">η≈{live.toFixed(2)}</span>
              ) : null}
            </button>
          );
        })}
      </div>
      {openId ? (
        <div className="mt-2 rounded-md border border-zinc-700 bg-zinc-950/90 p-2 text-[11px] leading-relaxed text-zinc-300">
          {(() => {
            const s = skills.find((x) => x.id === openId);
            if (!s) return null;
            return (
              <div className="space-y-1.5">
                <p className="font-medium text-zinc-100">{s.name}</p>
                <p className="text-zinc-400">
                  <span className="text-zinc-500">理论摘要：</span>
                  {s.description}
                </p>
                <p className="font-mono text-[10px] text-amber-200/85">
                  {s.impact_factor}
                  {s.physics_setting_key ? ` · ${s.physics_setting_key}` : ""}
                </p>
                <p className="border-t border-zinc-800 pt-1.5 font-mono text-[10px] text-cyan-200/80">
                  断言模板：{s.assertion_template}
                </p>
              </div>
            );
          })()}
        </div>
      ) : null}
    </div>
  );
}

export function PluginManagementPanel() {
  const { pluginSwitches, setPluginSwitches, pluginWeights, setPluginWeights, togglePlugin, applyPreset } = useLabConfig();
  const { manifest, isLoading, error, refresh } = usePluginRegistry();
  const { state: labState } = useLabStore();
  const isFinalized = labState.isFinalized;

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

  const lockTweaksClass = isFinalized ? "pointer-events-none opacity-50" : "";

  const sixHarmEtaDisplay = useMemo(() => {
    const pt = labState.snapshot?.physics_tensor as Record<string, unknown> | undefined;
    const pierce = runtimePhysicsNumber(pt, "MANGPAI_ETA_PIERCE");
    if (pierce != null) return pierce.toFixed(2);
    const legacy = runtimePhysicsNumber(pt, "MANGPAI_SIX_HARM_ETA");
    if (legacy != null) return legacy.toFixed(2);
    return "0.99";
  }, [labState.snapshot?.physics_tensor]);

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
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={refresh}
            className="rounded-lg border border-violet-500/40 bg-violet-500/10 px-3 py-1.5 text-xs text-violet-200 hover:bg-violet-500/20"
          >
            刷新逻辑注册表
          </button>
          <div className={`flex flex-wrap gap-2 ${lockTweaksClass}`}>
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
                    <div
                      className={`mt-3 flex items-center justify-between rounded-lg border border-zinc-800 bg-zinc-900/70 px-2 py-1.5 ${lockTweaksClass}`}
                    >
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
                    <div
                      className={`mt-2 rounded-lg border border-zinc-800 bg-zinc-900/70 px-2 py-2 ${
                        isFinalized ? "pointer-events-none opacity-60 grayscale-[0.5]" : ""
                      }`}
                    >
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
                            const key = plugin.weightKey!;
                            setPluginWeights((prev) => ({ ...prev, [key]: next }));
                            // eslint-disable-next-line no-console
                            console.info("[PLUGIN_INTERVENE] 权重已重置，Abs 场强重新排布中...");
                          }}
                          className="mt-1 w-full"
                        />
                      </label>
                    </div>
                  ) : null}

                  {plugin.id.includes("blind_school") ? (
                    <div
                      className={`mt-2 space-y-2 rounded-lg border border-violet-500/25 bg-violet-950/20 px-2 py-2 ${
                        isFinalized
                          ? "pointer-events-none border-zinc-600/90 bg-zinc-950/90 opacity-60 grayscale-[0.5] ring-1 ring-zinc-700/70"
                          : ""
                      }`}
                    >
                      <p className="text-[10px] font-medium uppercase tracking-wide text-violet-300/90">盲派灵魂算子</p>
                      {isFinalized ? (
                        <p className="text-[10px] text-zinc-500">终审已签发 · 规则已锁定，不可修改</p>
                      ) : null}
                      <div className="flex items-center gap-2 text-[11px] text-zinc-300">
                        <label className="flex min-w-0 flex-1 cursor-pointer items-center gap-2">
                          <input
                            type="checkbox"
                            className="rounded border-zinc-600"
                            checked={pluginSwitches.blindSchoolPierceHarm}
                            onChange={(e) =>
                              setPluginSwitches((prev) => ({ ...prev, blindSchoolPierceHarm: e.target.checked }))
                            }
                          />
                          <span className="min-w-0">启用穿破判定（六穿/害）</span>
                        </label>
                        <span className="relative inline-flex shrink-0 group">
                          <button
                            type="button"
                            tabIndex={0}
                            className="flex h-5 w-5 items-center justify-center rounded-full border border-amber-500/40 bg-amber-500/10 text-[10px] font-semibold text-amber-200/95"
                            aria-label="六穿物理损耗系数说明"
                          >
                            η
                          </button>
                          <span
                            role="tooltip"
                            className="pointer-events-none invisible absolute bottom-full right-0 z-30 mb-1 w-max max-w-[min(280px,calc(100vw-2rem))] rounded-md border border-amber-500/35 bg-zinc-950 px-2 py-1.5 text-left text-[10px] leading-snug text-amber-100/95 shadow-lg group-hover:visible group-focus-within:visible"
                          >
                            当前物理损耗系数：η_pierce = {sixHarmEtaDisplay}（Default，MANGPAI_ETA_PIERCE / 兼容 MANGPAI_SIX_HARM_ETA）
                          </span>
                        </span>
                      </div>
                      <label className="flex cursor-pointer items-center gap-2 text-[11px] text-zinc-300">
                        <input
                          type="checkbox"
                          className="rounded border-zinc-600"
                          checked={pluginSwitches.blindSchoolTombVault}
                          onChange={(e) =>
                            setPluginSwitches((prev) => ({ ...prev, blindSchoolTombVault: e.target.checked }))
                          }
                        />
                        识别墓库开闭
                      </label>
                      <label className="flex cursor-pointer items-center gap-2 text-[11px] text-zinc-300">
                        <input
                          type="checkbox"
                          className="rounded border-zinc-600"
                          checked={pluginSwitches.blindSchoolHostGuest}
                          onChange={(e) =>
                            setPluginSwitches((prev) => ({ ...prev, blindSchoolHostGuest: e.target.checked }))
                          }
                        />
                        宾主主权分析（财官日时红利）
                      </label>
                    </div>
                  ) : null}

                  {plugin.id.includes("blind_school") && Array.isArray(plugin.metadata?.skills) && plugin.metadata.skills.length > 0 ? (
                    <BlindSchoolSkillList
                      skills={plugin.metadata.skills}
                      physicsTensor={labState.snapshot?.physics_tensor as Record<string, unknown> | undefined}
                    />
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

