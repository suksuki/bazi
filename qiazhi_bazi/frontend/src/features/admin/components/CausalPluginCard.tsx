"use client";

import Link from "next/link";
import { useMemo, useState, type Dispatch, type ReactNode, type SetStateAction } from "react";
import {
  boundsForPhysicsSettingKey,
  physicsSliderBindingForKey,
} from "@/features/admin/constants/physicsSkillSliderBounds";
import type { PluginManifestItem } from "@/features/admin/hooks/usePluginRegistry";
import { runtimePhysicsNumber } from "@/features/admin/utils/runtimePhysicsNumber";
import type { PhysicsLabConfig, PluginSwitches, PluginWeights } from "@/features/stream-board/models";

function IconZap({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" aria-hidden>
      <path d="M13 2L3 14h8l-1 8 10-12h-8l1-8z" strokeLinejoin="round" />
    </svg>
  );
}

function IconFileText({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" aria-hidden>
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" strokeLinejoin="round" />
      <path d="M14 2v6h6M16 13H8M16 17H8M10 9H8" strokeLinecap="round" />
    </svg>
  );
}

function statusTagClass(status: "HEALTHY" | "IDLE" | "ERROR"): string {
  if (status === "HEALTHY") return "border-emerald-500/40 bg-emerald-500/10 text-emerald-300";
  if (status === "ERROR") return "border-rose-500/40 bg-rose-500/10 text-rose-300";
  return "border-zinc-700 bg-zinc-800/80 text-zinc-300";
}

export type CausalPluginCardPlugin = PluginManifestItem & {
  switchKey?: keyof PluginSwitches;
  weightKey?: keyof PluginWeights;
  mutable: boolean;
  enabled: boolean;
};

type Props = {
  plugin: CausalPluginCardPlugin;
  isFinalized: boolean;
  lockTweaksClass: string;
  pluginWeights: PluginWeights;
  setPluginWeights: Dispatch<SetStateAction<PluginWeights>>;
  togglePlugin: (k: keyof PluginSwitches) => void;
  openBlueprint: (p: PluginManifestItem) => void;
  extraBody?: ReactNode;
  /** 依赖 / p95 等巡检信息，置于 Body 末尾 */
  diagnosticsSlot?: ReactNode;
  /** 与 `metadata.skills[].physics_setting_key` 联动：在卡片内渲染实验滑块 */
  labConfig?: PhysicsLabConfig;
  setLabConfig?: Dispatch<SetStateAction<PhysicsLabConfig>>;
  defaultPhysicsSettings?: Record<string, number>;
  /** 最近一次快照 physics_tensor，用于 η 实时读数 */
  physicsTensor?: Record<string, unknown> | undefined;
};

export function CausalPluginCard({
  plugin,
  isFinalized,
  lockTweaksClass,
  pluginWeights,
  setPluginWeights,
  togglePlugin,
  openBlueprint,
  extraBody,
  diagnosticsSlot,
  labConfig,
  setLabConfig,
  defaultPhysicsSettings,
  physicsTensor,
}: Props) {
  const [canonOpen, setCanonOpen] = useState(false);
  const [labInteractOpen, setLabInteractOpen] = useState(false);
  const meta = plugin.metadata || ({} as PluginManifestItem["metadata"]);
  const display = meta.display_name || meta.label || plugin.id;
  const useCase = meta.use_case || "";
  const detailed = meta.detailed_description || "";
  const physical = meta.physical_impact || "";
  const canonMd = [detailed, meta.governance_notes ? `**裁决合规**\n${meta.governance_notes}` : ""].filter(Boolean).join("\n\n---\n\n");

  const footerSkills = useMemo(() => (Array.isArray(meta.skills) ? meta.skills : []), [meta.skills]);

  const physicsSliderRows = useMemo(() => {
    if (!setLabConfig) return [];
    return footerSkills
      .map((s) => {
        const pkRaw = s.physics_setting_key?.trim();
        if (!pkRaw) return null;
        const binding = physicsSliderBindingForKey(pkRaw);
        const bounds = boundsForPhysicsSettingKey(pkRaw);
        if (!binding || !bounds) return null;
        return { skill: s, pk: pkRaw as keyof PhysicsLabConfig, bounds, binding };
      })
      .filter((row): row is NonNullable<typeof row> => row != null);
  }, [footerSkills, setLabConfig]);

  return (
    <article
      id={`card-${plugin.id}`}
      className="relative flex flex-col overflow-hidden rounded-xl border border-zinc-800/95 bg-gradient-to-b from-zinc-950/90 to-zinc-950/70 shadow-[0_0_0_1px_rgba(39,39,42,0.4)]"
    >
      <header className="flex flex-wrap items-start justify-between gap-2 border-b border-zinc-800/80 bg-zinc-900/40 px-3 py-2.5">
        <div className="min-w-0 flex-1">
          <p className="text-sm font-semibold text-zinc-50">{display}</p>
          <p className="mt-0.5 font-mono text-[10px] text-zinc-500">{plugin.id}</p>
          {meta.description_tags && meta.description_tags.length > 0 ? (
            <div className="mt-1 flex flex-wrap gap-1">
              {meta.description_tags.map((tag) => (
                <span key={tag} className="rounded border border-zinc-700/80 px-1 py-0 text-[9px] text-zinc-500">
                  {tag}
                </span>
              ))}
            </div>
          ) : null}
        </div>
        <div className="flex shrink-0 flex-wrap items-center gap-2">
          <button
            type="button"
            onClick={() => openBlueprint(plugin)}
            className="rounded-md border border-violet-500/35 bg-violet-500/10 px-2 py-1 text-[10px] text-violet-200 hover:bg-violet-500/20"
          >
            蓝图
          </button>
          <span className={`rounded-full border px-2 py-0.5 text-[10px] ${statusTagClass(plugin.status)}`}>{plugin.status}</span>
          {plugin.mutable ? (
            <span className={lockTweaksClass}>
              <button
                type="button"
                onClick={() => plugin.switchKey && togglePlugin(plugin.switchKey)}
                className={`rounded-md px-2 py-1 text-[10px] ${plugin.enabled ? "bg-emerald-500/25 text-emerald-200" : "bg-zinc-800 text-zinc-400"}`}
              >
                {plugin.enabled ? "开" : "关"}
              </button>
            </span>
          ) : (
            <span className="rounded-md border border-zinc-700/90 bg-zinc-900/80 px-2 py-1 text-[9px] text-zinc-500">基座</span>
          )}
        </div>
        {plugin.weightKey ? (
          <div
            className={`mt-2 w-full basis-full ${lockTweaksClass} ${isFinalized ? "opacity-60 grayscale-[0.35]" : ""}`}
          >
            <label className="text-[10px] text-zinc-400">
              权重 {pluginWeights[plugin.weightKey].toFixed(2)}
              <input
                type="range"
                min={0}
                max={1}
                step={0.05}
                disabled={isFinalized}
                value={pluginWeights[plugin.weightKey]}
                onChange={(e) => {
                  const next = Number(e.target.value);
                  const key = plugin.weightKey!;
                  setPluginWeights((prev) => ({ ...prev, [key]: next }));
                  // eslint-disable-next-line no-console
                  console.info("[PLUGIN_INTERVENE] 权重已重置，Abs 场强重新排布中...");
                }}
                className="mt-1 w-full accent-amber-500/80"
              />
            </label>
          </div>
        ) : null}
      </header>

      <div className="flex-1 space-y-2.5 px-3 py-2.5 text-[11px] leading-relaxed text-zinc-300">
        {useCase ? (
          <div className="flex gap-2">
            <IconZap className="mt-0.5 h-4 w-4 shrink-0 text-amber-400/90" />
            <div className="min-w-0">
              <p className="text-[10px] font-medium uppercase tracking-wide text-amber-200/80">使用场景</p>
              <div className="mt-0.5 whitespace-pre-wrap text-zinc-300/95">{useCase}</div>
            </div>
          </div>
        ) : null}
        {(detailed || physical) ? (
          <div className="flex gap-2">
            <IconFileText className="mt-0.5 h-4 w-4 shrink-0 text-sky-400/90" />
            <div className="min-w-0 space-y-1.5">
              {detailed ? (
                <div>
                  <p className="text-[10px] font-medium uppercase tracking-wide text-sky-200/80">核心逻辑</p>
                  <p className="mt-0.5 text-zinc-300/95">{detailed}</p>
                </div>
              ) : null}
              {physical ? (
                <div>
                  <p className="text-[10px] font-medium uppercase tracking-wide text-sky-200/80">对 Abs 的作用</p>
                  <p className="mt-0.5 text-zinc-300/95">{physical}</p>
                </div>
              ) : null}
            </div>
          </div>
        ) : null}
        {canonMd ? (
          <div>
            <button
              type="button"
              onClick={() => setCanonOpen((o) => !o)}
              className="text-[10px] font-medium text-amber-300/90 underline-offset-2 hover:underline"
            >
              {canonOpen ? "收起法典" : "查看法典（全文）"}
            </button>
            {canonOpen ? (
              <div className="mt-1.5 max-h-48 overflow-y-auto rounded-md border border-zinc-700/80 bg-zinc-950/90 p-2 whitespace-pre-wrap text-[10px] text-zinc-400">
                {canonMd}
              </div>
            ) : null}
          </div>
        ) : null}
        {physicsSliderRows.length > 0 && labConfig && setLabConfig ? (
          <div
            className={`rounded-lg border border-cyan-900/45 bg-cyan-950/25 px-2 py-2 ${
              isFinalized ? "pointer-events-none opacity-55 grayscale-[0.35]" : ""
            }`}
          >
            <button
              type="button"
              onClick={() => setLabInteractOpen((o) => !o)}
              className="text-[10px] font-medium text-cyan-200/90 underline-offset-2 hover:underline"
            >
              {labInteractOpen ? "收起实验交互" : "展开实验交互（physics_setting_key）"}
            </button>
            {labInteractOpen ? (
              <div className="mt-2 space-y-2.5">
                {physicsSliderRows.map(({ skill, pk, bounds, binding }) => {
                  const cur =
                    typeof labConfig[pk] === "number" && Number.isFinite(labConfig[pk] as number)
                      ? (labConfig[pk] as number)
                      : (defaultPhysicsSettings?.[pk as string] ?? bounds[0]);
                  const live = runtimePhysicsNumber(physicsTensor, pk as string);
                  const titleLine = binding.label ? binding.label : skill.name;
                  return (
                    <label key={`${skill.id}-${pk}`} className="block text-[10px] text-zinc-300">
                      <span className="font-medium text-cyan-100/90">{titleLine}</span>
                      {binding.label ? (
                        <span className="ml-1 text-[9px] text-zinc-500">（{skill.name}）</span>
                      ) : null}
                      <span className="ml-1 font-mono text-[9px] text-zinc-500">{pk as string}</span>
                      {live != null ? (
                        <span className="ml-1 font-mono text-[9px] text-amber-200/85">η≈{live.toFixed(2)}</span>
                      ) : null}
                      <span className="ml-1 text-zinc-500">= {Number(cur).toFixed(2)}</span>
                      <input
                        type="range"
                        min={bounds[0]}
                        max={bounds[1]}
                        step={bounds[2]}
                        disabled={isFinalized}
                        value={cur}
                        onChange={(e) => {
                          const next = Number(e.target.value);
                          setLabConfig((prev) => ({ ...prev, [pk]: next } as PhysicsLabConfig));
                        }}
                        className="mt-1 w-full accent-cyan-500/80"
                      />
                    </label>
                  );
                })}
              </div>
            ) : null}
          </div>
        ) : null}
        {extraBody}
        {diagnosticsSlot ? <div className="border-t border-zinc-800/60 pt-2">{diagnosticsSlot}</div> : null}
      </div>

      <footer className="border-t border-zinc-800/80 bg-zinc-900/35 px-3 py-2">
        <p className="text-[9px] font-medium uppercase tracking-wide text-zinc-500">Skill · 物理键</p>
        <div className="mt-1 flex flex-wrap gap-1.5">
          {footerSkills.length ? (
            footerSkills.map((s) => (
              <span
                key={s.id}
                className="inline-flex max-w-full items-baseline gap-1 rounded border border-cyan-900/60 bg-cyan-950/40 px-1.5 py-0.5 font-mono text-[9px] text-cyan-100/90"
                title={s.name}
              >
                <span className="truncate">{s.id}</span>
                {s.physics_setting_key ? <span className="text-zinc-500">·{s.physics_setting_key}</span> : null}
              </span>
            ))
          ) : (
            <span className="text-[10px] text-zinc-600">—</span>
          )}
        </div>
        <div className="mt-2 flex flex-wrap items-center justify-between gap-2">
          <span className={`text-[10px] ${plugin.status === "ERROR" ? "text-rose-300" : "text-emerald-300/90"}`}>
            Hook: {meta.hook || "—"}
          </span>
          <Link href={meta.doc_path || "/docs"} className="text-[10px] text-amber-300/90 underline-offset-2 hover:underline">
            理论手册
          </Link>
        </div>
      </footer>
    </article>
  );
}
