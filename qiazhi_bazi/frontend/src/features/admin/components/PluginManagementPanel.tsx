"use client";

import { useCallback, useMemo, useState } from "react";
import { CausalPluginCard } from "@/features/admin/components/CausalPluginCard";
import { PluginBlueprintModal } from "@/features/admin/components/PluginBlueprintModal";
import { useLabConfig } from "@/features/lab-config/LabConfigContext";
import {
  buildPluginManifestUrl,
  usePluginRegistry,
  type BlindSchoolSkillItem,
  type PluginManifestItem,
} from "@/features/admin/hooks/usePluginRegistry";
import { useLabStore } from "@/features/stream-board/stores/useLabStore";
import type { PhysicsLabConfig, PluginSwitches, PluginWeights } from "@/features/stream-board/models";

type UiLayer = "L1" | "L2" | "L3" | "L4";
const LAYER_LABEL: Record<UiLayer, string> = {
  L1: "L1 基础 (Base)",
  L2: "L2 功能 (Functional)",
  L3: "L3 现代 (Modern)",
  L4: "L4 战略 (Strategic)",
};

/** 与后端 DEFAULT_PHYSICS_SETTINGS 中可由 Lab 覆写的 η / 开关键对齐（用于一致性横幅） */
const ETA_ALIGNMENT_KEYS = [
  "L1_OP_PROD_ETA",
  "L1_OP_DEST_ETA",
  "L1_OP_CONN_ETA",
  "INTERDIMENSIONAL_CONDUCTIVITY",
  "INTERDIMENSIONAL_BARRIER_STRENGTH",
  "CONDUCTIVITY_DECAY_RATE",
  "GHOST_ENERGY_DAMPING",
  "MANGPAI_ETA_DIMENSIONAL_CRUSH",
  "MANGPAI_ROOT_RESONANCE",
  "INTERDIMENSIONAL_SHIELD_ENABLE",
  "STEM_BRANCH_ROOT_RESONANCE_ENABLE",
  "STEM_BRANCH_VERTICAL_CRUSH_ENABLE",
] as const satisfies readonly (keyof PhysicsLabConfig)[];

function labPhysicsEffective(
  cfg: PhysicsLabConfig,
  defaults: Record<string, number> | undefined,
  k: keyof PhysicsLabConfig,
): number | null {
  const raw = cfg[k];
  if (typeof raw === "number" && Number.isFinite(raw)) return raw;
  const d = defaults?.[k as string];
  return typeof d === "number" && Number.isFinite(d) ? d : null;
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
  const {
    labConfig,
    setLabConfig,
    pluginSwitches,
    setPluginSwitches,
    pluginWeights,
    setPluginWeights,
    togglePlugin,
    applyPreset,
  } = useLabConfig();
  const { manifest, isLoading, error, refresh } = usePluginRegistry();
  const { state: labState } = useLabStore();
  const isFinalized = labState.isFinalized;

  const [blueprintOpen, setBlueprintOpen] = useState(false);
  const [blueprintTitle, setBlueprintTitle] = useState("");
  const [blueprintMd, setBlueprintMd] = useState("");

  const openBlueprint = useCallback(
    async (plugin: PluginManifestItem) => {
      const meta = plugin.metadata;
      const fromMeta = typeof meta?.blueprint_markdown === "string" ? meta.blueprint_markdown.trim() : "";
      const rawManifest = manifest?.l1_physics_manifest;
      const overlays =
        rawManifest && typeof rawManifest === "object" && rawManifest !== null
          ? (rawManifest as { registry_overlays?: Record<string, { markdown?: string }> }).registry_overlays
          : undefined;
      const ov = overlays?.[plugin.id];
      const fromOverlay = typeof ov?.markdown === "string" ? ov.markdown.trim() : "";
      const localDoc = fromMeta || fromOverlay;
      const fallback =
        `## 暂无专用蓝图\n\n插件 \`${plugin.id}\` 未挂载 \`blueprint_markdown\`。维轴与传导率四档见 \`docs/causal-pulse/v0.13_interdimensional_protocol.md\` 及后端 \`l1_physics_manifest.json\`。`;
      setBlueprintTitle(String(meta?.label || plugin.id));
      setBlueprintMd("正在从 PluginRegistry 拉取蓝图…");
      setBlueprintOpen(true);
      try {
        const res = await fetch(buildPluginManifestUrl(plugin.id));
        if (res.ok) {
          const body = (await res.json()) as { blueprint_markdown?: string };
          const remote = typeof body.blueprint_markdown === "string" ? body.blueprint_markdown.trim() : "";
          if (remote) {
            setBlueprintMd(remote);
            return;
          }
        }
      } catch {
        /* 回退到本地已缓存 manifest */
      }
      setBlueprintMd(localDoc || fallback);
    },
    [manifest?.l1_physics_manifest],
  );

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

  const physicsLabVsRepoDrift = useMemo(() => {
    const defaults = manifest?.default_physics_settings;
    if (!defaults) return [] as Array<{ key: string; lab: number; repo: number }>;
    const out: Array<{ key: string; lab: number; repo: number }> = [];
    for (const k of ETA_ALIGNMENT_KEYS) {
      const repo = defaults[k as string];
      if (typeof repo !== "number" || !Number.isFinite(repo)) continue;
      const lab = labPhysicsEffective(labConfig, defaults, k);
      if (lab == null) continue;
      if (Math.abs(lab - repo) > 1e-5) out.push({ key: k, lab, repo });
    }
    return out;
  }, [labConfig, manifest?.default_physics_settings]);

  const physicsLabVsSnapshotDrift = useMemo(() => {
    const pt = labState.snapshot?.physics_tensor as Record<string, unknown> | undefined;
    const defaults = manifest?.default_physics_settings;
    if (!pt) return [] as Array<{ key: string; lab: number; snap: number }>;
    const out: Array<{ key: string; lab: number; snap: number }> = [];
    for (const k of ETA_ALIGNMENT_KEYS) {
      const snap = runtimePhysicsNumber(pt, k);
      if (snap == null) continue;
      const lab = labPhysicsEffective(labConfig, defaults, k);
      if (lab == null) continue;
      if (Math.abs(lab - snap) > 1e-4) out.push({ key: k, lab, snap });
    }
    return out;
  }, [labConfig, labState.snapshot?.physics_tensor, manifest?.default_physics_settings]);

  const pierceSnapVsRepo = useMemo(() => {
    const defaults = manifest?.default_physics_settings;
    const pt = labState.snapshot?.physics_tensor as Record<string, unknown> | undefined;
    if (!defaults || !pt) return null;
    const snap = runtimePhysicsNumber(pt, "MANGPAI_ETA_PIERCE") ?? runtimePhysicsNumber(pt, "MANGPAI_SIX_HARM_ETA");
    const repo = defaults.MANGPAI_ETA_PIERCE ?? defaults.MANGPAI_SIX_HARM_ETA;
    if (snap == null || typeof repo !== "number" || !Number.isFinite(repo)) return null;
    if (Math.abs(snap - repo) <= 1e-4) return null;
    return { snap, repo };
  }, [labState.snapshot?.physics_tensor, manifest?.default_physics_settings]);

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

      {manifest?.default_physics_settings ? (
        <div
          className={`rounded-xl border px-3 py-2 text-xs ${
            physicsLabVsRepoDrift.length
              ? "border-rose-500/50 bg-rose-950/40 text-rose-100"
              : "border-emerald-500/35 bg-emerald-950/20 text-emerald-100/90"
          }`}
        >
          <p className="font-medium text-zinc-100">逻辑一致性 · Lab 与仓库 DEFAULT_PHYSICS_SETTINGS（manifest）</p>
          {physicsLabVsRepoDrift.length ? (
            <ul className="mt-1.5 space-y-0.5 text-[11px] leading-snug">
              {physicsLabVsRepoDrift.map((row) => (
                <li key={row.key}>
                  <span className="font-mono text-rose-200/95">{row.key}</span>
                  <span className="text-zinc-400"> — Lab </span>
                  <span className="font-mono">{row.lab.toFixed(4)}</span>
                  <span className="text-zinc-400">，仓库默认 </span>
                  <span className="font-mono">{row.repo.toFixed(4)}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="mt-1 text-[11px] text-emerald-200/85">当前 Lab 中受检 η/开关与后端默认表一致。</p>
          )}
        </div>
      ) : !isLoading && !error ? (
        <div className="rounded-xl border border-zinc-700 bg-zinc-950/50 px-3 py-2 text-[11px] text-zinc-500">
          逻辑一致性：manifest 未返回 default_physics_settings，无法与仓库默认对齐校验。
        </div>
      ) : null}

      {physicsLabVsSnapshotDrift.length > 0 || pierceSnapVsRepo ? (
        <div className="rounded-xl border border-amber-500/45 bg-amber-950/25 px-3 py-2 text-xs text-amber-100">
          <p className="font-medium text-amber-50/95">逻辑一致性 · 最近一次快照与 Lab（或穿破 η 与仓库默认）</p>
          {physicsLabVsSnapshotDrift.length ? (
            <ul className="mt-1.5 space-y-0.5 text-[11px]">
              {physicsLabVsSnapshotDrift.map((row) => (
                <li key={row.key}>
                  <span className="font-mono text-amber-200/95">{row.key}</span>
                  <span className="text-amber-100/70"> — Lab </span>
                  <span className="font-mono">{row.lab.toFixed(4)}</span>
                  <span className="text-amber-100/70">，快照 </span>
                  <span className="font-mono">{row.snap.toFixed(4)}</span>
                </li>
              ))}
            </ul>
          ) : null}
          {pierceSnapVsRepo ? (
            <p className={`text-[11px] ${physicsLabVsSnapshotDrift.length ? "mt-1.5 border-t border-amber-800/50 pt-1.5" : "mt-1"}`}>
              <span className="font-mono text-amber-200/95">MANGPAI_η_pierce</span>
              <span className="text-amber-100/75"> — 快照 </span>
              <span className="font-mono">{pierceSnapVsRepo.snap.toFixed(4)}</span>
              <span className="text-amber-100/75">，仓库默认 </span>
              <span className="font-mono">{pierceSnapVsRepo.repo.toFixed(4)}</span>
              <span className="text-amber-100/60">（需重新跑 analyze-seed 以同步）</span>
            </p>
          ) : null}
        </div>
      ) : null}

      {isLoading ? <div className="text-xs text-zinc-400">同步后端 manifest 中…</div> : null}
      {error ? <div className="rounded-lg border border-rose-500/40 bg-rose-500/10 px-3 py-2 text-xs text-rose-200">manifest 拉取失败：{String(error)}</div> : null}

      <div
        className={`rounded-xl border border-sky-500/35 bg-sky-950/30 px-3 py-3 ${
          isFinalized
            ? "pointer-events-none border-zinc-600/80 bg-zinc-950/80 opacity-60 grayscale-[0.4] ring-1 ring-zinc-700/60"
            : ""
        }`}
      >
        <p className="text-[10px] font-medium uppercase tracking-wide text-sky-300/95">base_physics · L1 原子算子</p>
        {isFinalized ? <p className="mt-1 text-[10px] text-zinc-500">终审已签发 · 参数已锁定</p> : null}
        <p className="mt-1 text-[11px] text-sky-100/85">
          相生效率（L1_OP_PROD）、相克损耗（L1_OP_DEST）、合化能量系数（L1_OP_CONN）独立 η，写入 physics_config 参与 analyze-seed。
        </p>
        <div className="mt-3 grid gap-3 sm:grid-cols-3">
          <label className="block text-[11px] text-sky-100/90">
            <span className="font-mono text-[10px] text-sky-200/80">L1_OP_PROD_ETA</span>
            <span className="ml-1 text-zinc-400">相生效率 {(labConfig.L1_OP_PROD_ETA ?? 1).toFixed(2)}</span>
            <input
              type="range"
              min={0}
              max={3}
              step={0.05}
              disabled={isFinalized}
              value={labConfig.L1_OP_PROD_ETA ?? 1}
              onChange={(e) =>
                setLabConfig((prev) => ({ ...prev, L1_OP_PROD_ETA: Number(e.target.value) }))
              }
              className="mt-1 w-full accent-[#3B82F6]"
            />
          </label>
          <label className="block text-[11px] text-sky-100/90">
            <span className="font-mono text-[10px] text-sky-200/80">L1_OP_DEST_ETA</span>
            <span className="ml-1 text-zinc-400">相克损耗 {(labConfig.L1_OP_DEST_ETA ?? 1).toFixed(2)}</span>
            <input
              type="range"
              min={0}
              max={3}
              step={0.05}
              disabled={isFinalized}
              value={labConfig.L1_OP_DEST_ETA ?? 1}
              onChange={(e) =>
                setLabConfig((prev) => ({ ...prev, L1_OP_DEST_ETA: Number(e.target.value) }))
              }
              className="mt-1 w-full accent-[#3B82F6]"
            />
          </label>
          <label className="block text-[11px] text-sky-100/90">
            <span className="font-mono text-[10px] text-sky-200/80">L1_OP_CONN_ETA</span>
            <span className="ml-1 text-zinc-400">合化能量 {(labConfig.L1_OP_CONN_ETA ?? 1).toFixed(2)}</span>
            <input
              type="range"
              min={0}
              max={3}
              step={0.05}
              disabled={isFinalized}
              value={labConfig.L1_OP_CONN_ETA ?? 1}
              onChange={(e) =>
                setLabConfig((prev) => ({ ...prev, L1_OP_CONN_ETA: Number(e.target.value) }))
              }
              className="mt-1 w-full accent-[#3B82F6]"
            />
          </label>
        </div>

        <div className="mt-4 border-t border-sky-800/50 pt-3">
          <p className="text-[10px] font-medium uppercase tracking-wide text-sky-300/95">干支维轴算子</p>
          <p className="mt-1 text-[11px] text-sky-100/80">维度屏蔽、通根谐振、盖头截脚与跨维传导灵敏度（写入 physics_config）。</p>
          <div className={`mt-3 space-y-2 text-[11px] text-sky-100/90 ${isFinalized ? "pointer-events-none opacity-60" : ""}`}>
            <label className="flex cursor-pointer items-center gap-2">
              <input
                type="checkbox"
                disabled={isFinalized}
                checked={(labConfig.INTERDIMENSIONAL_SHIELD_ENABLE ?? 1) >= 0.5}
                onChange={(e) =>
                  setLabConfig((prev) => ({ ...prev, INTERDIMENSIONAL_SHIELD_ENABLE: e.target.checked ? 1 : 0 }))
                }
                className="accent-[#3B82F6]"
              />
              <span>启用维度屏蔽（防止伤官见官滥用）</span>
            </label>
            <label className="flex cursor-pointer items-center gap-2">
              <input
                type="checkbox"
                disabled={isFinalized}
                checked={(labConfig.STEM_BRANCH_ROOT_RESONANCE_ENABLE ?? 1) >= 0.5}
                onChange={(e) =>
                  setLabConfig((prev) => ({ ...prev, STEM_BRANCH_ROOT_RESONANCE_ENABLE: e.target.checked ? 1 : 0 }))
                }
                className="accent-[#3B82F6]"
              />
              <span>启用通根谐振判定</span>
            </label>
            <label className="flex cursor-pointer items-center gap-2">
              <input
                type="checkbox"
                disabled={isFinalized}
                checked={(labConfig.STEM_BRANCH_VERTICAL_CRUSH_ENABLE ?? 1) >= 0.5}
                onChange={(e) =>
                  setLabConfig((prev) => ({ ...prev, STEM_BRANCH_VERTICAL_CRUSH_ENABLE: e.target.checked ? 1 : 0 }))
                }
                className="accent-[#3B82F6]"
              />
              <span>启用盖头截脚损耗</span>
            </label>
          </div>
          <label className="mt-3 block text-[11px] text-sky-100/90">
            <span className="font-mono text-[10px] text-sky-200/80">INTERDIMENSIONAL_CONDUCTIVITY</span>
            <span className="ml-1 text-zinc-400">
              传导灵敏度（跨维渗透）{(labConfig.INTERDIMENSIONAL_CONDUCTIVITY ?? 0).toFixed(2)}
            </span>
            <input
              type="range"
              min={0}
              max={2}
              step={0.05}
              disabled={isFinalized}
              value={labConfig.INTERDIMENSIONAL_CONDUCTIVITY ?? 0}
              onChange={(e) =>
                setLabConfig((prev) => ({ ...prev, INTERDIMENSIONAL_CONDUCTIVITY: Number(e.target.value) }))
              }
              className="mt-1 w-full accent-[#3B82F6]"
            />
          </label>
        </div>
      </div>

      <PluginBlueprintModal
        open={blueprintOpen}
        title={blueprintTitle}
        markdown={blueprintMd}
        onClose={() => setBlueprintOpen(false)}
      />

      {(Object.keys(LAYER_LABEL) as UiLayer[]).map((layer) => (
        <div key={layer} className="space-y-2">
          <h4 className="text-sm font-medium text-zinc-200">{LAYER_LABEL[layer]}</h4>
          <div className="grid gap-3 md:grid-cols-2">
            {rendered
              .filter((p) => p.layer === layer)
              .map((plugin) => (
                <CausalPluginCard
                  key={plugin.id}
                  plugin={plugin}
                  isFinalized={isFinalized}
                  lockTweaksClass={lockTweaksClass}
                  pluginWeights={pluginWeights}
                  setPluginWeights={setPluginWeights}
                  togglePlugin={togglePlugin}
                  openBlueprint={openBlueprint}
                  diagnosticsSlot={
                    <div className="flex flex-wrap gap-2 text-[10px] text-zinc-500">
                      <span className="rounded border border-zinc-700/80 bg-zinc-900/60 px-1.5 py-0.5">
                        Priority: {Number(plugin.metadata?.priority || 0).toFixed(2)}
                      </span>
                      <span className="rounded border border-zinc-700/80 bg-zinc-900/60 px-1.5 py-0.5">
                        依赖：{plugin.dependencies.length ? plugin.dependencies.join(" / ") : "无"}
                      </span>
                      <span className="rounded border border-zinc-700/80 bg-zinc-900/60 px-1.5 py-0.5">
                        p95:{" "}
                        {plugin.performance_snapshot?.p95_ms != null
                          ? `${Number(plugin.performance_snapshot.p95_ms).toFixed(1)}ms`
                          : "--"}
                      </span>
                    </div>
                  }
                  extraBody={
                    plugin.id.includes("blind_school") ? (
                      <>
                        <div
                          className={`space-y-2 rounded-lg border border-violet-500/25 bg-violet-950/20 px-2 py-2 ${
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
                                当前物理损耗系数：η_pierce = {sixHarmEtaDisplay}（Default，MANGPAI_ETA_PIERCE / 兼容
                                MANGPAI_SIX_HARM_ETA）
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
                        {Array.isArray(plugin.metadata?.skills) && plugin.metadata.skills.length > 0 ? (
                          <BlindSchoolSkillList
                            skills={plugin.metadata.skills}
                            physicsTensor={labState.snapshot?.physics_tensor as Record<string, unknown> | undefined}
                          />
                        ) : null}
                      </>
                    ) : null
                  }
                />
              ))}
          </div>
        </div>
      ))}
    </section>
  );
}

