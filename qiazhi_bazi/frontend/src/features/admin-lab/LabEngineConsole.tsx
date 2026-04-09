"use client";

import type { Dispatch, SetStateAction } from "react";
import type { PhysicsLabConfig } from "@/features/stream-board/models";
import type { PluginSwitches } from "@/features/stream-board/models";

type LabGroupKey = "timing" | "riskTomb" | "climateTopology";

export type LabEngineConsoleProps = {
  labOpen: boolean;
  setLabOpen: (v: boolean | ((p: boolean) => boolean)) => void;
  labGroupsOpen: Record<LabGroupKey, boolean>;
  setLabGroupsOpen: Dispatch<SetStateAction<Record<LabGroupKey, boolean>>>;
  labConfig: PhysicsLabConfig;
  setLabConfig: Dispatch<SetStateAction<PhysicsLabConfig>>;
  pluginSwitches: PluginSwitches;
  setPluginSwitches: Dispatch<SetStateAction<PluginSwitches>>;
  onApplyRecalculate: () => void | Promise<void>;
  variant?: "main" | "engineRoom";
};

const labGroups: {
  key: LabGroupKey;
  title: string;
  items: [keyof PhysicsLabConfig, number, number, number][];
}[] = [
  {
    key: "timing",
    title: "时运权重",
    items: [
      ["WEIGHT_LUCK", 0, 1, 0.01],
      ["WEIGHT_YEAR", 0, 1, 0.01],
    ],
  },
  {
    key: "riskTomb",
    title: "风险与墓库",
    items: [
      ["BASE_BACKFIRE_RISK", 0, 1, 0.01],
      ["HIGH_IMBALANCE_RISK", 0, 1, 0.01],
      ["TOMB_LOCK_RATE", 0, 1, 0.01],
    ],
  },
  {
    key: "climateTopology",
    title: "气候与拓扑",
    items: [
      ["CLIMATE_INTENSITY", 0, 1, 0.01],
      ["STEM_RESONANCE_BOOST", 1, 3, 0.05],
      ["TRANSFER_DISTANCE_DECAY", 0, 0.5, 0.01],
      ["WORK_MIN_THRESHOLD", 0, 3, 0.1],
    ],
  },
];

export function LabEngineConsole({
  labOpen,
  setLabOpen,
  labGroupsOpen,
  setLabGroupsOpen,
  labConfig,
  setLabConfig,
  pluginSwitches,
  setPluginSwitches,
  onApplyRecalculate,
  variant = "main",
}: LabEngineConsoleProps) {
  const title = variant === "engineRoom" ? "物理实验参数（与主实验室共享会话）" : "Lab Console";
  const hint =
    variant === "engineRoom" ? (
      <p className="mb-2 rounded border border-cyan-500/30 bg-cyan-500/5 px-2 py-1 text-[11px] text-cyan-200/90">
        此处修改与主屏「实验室」实时同步。需重新排盘时，请返回主屏点击「应用并重算」。
      </p>
    ) : null;

  return (
    <section className="rounded-2xl border border-zinc-800 bg-zinc-900/60 p-3">
      <div className="mb-2 flex items-center justify-between">
        <button
          type="button"
          onClick={() => setLabOpen((v) => !v)}
          className="flex flex-1 items-center justify-between rounded-md border border-zinc-700 bg-zinc-900 px-3 py-2 text-left text-xs text-zinc-200 hover:bg-zinc-800"
        >
          <span className="text-sm font-medium text-zinc-200">{title}</span>
          <span>{labOpen ? "收起" : "展开"}</span>
        </button>
      </div>
      {hint}
      {labOpen ? (
        <div className="space-y-2">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="flex flex-wrap items-center gap-2 rounded border border-zinc-700 bg-zinc-900 px-2 py-1 text-[11px] text-zinc-300">
              <span>插件管理</span>
              <label className="inline-flex items-center gap-1">
                <input
                  type="checkbox"
                  checked={pluginSwitches.blindSchool}
                  onChange={(e) => setPluginSwitches((prev) => ({ ...prev, blindSchool: e.target.checked }))}
                />
                盲派
              </label>
              <label className="inline-flex items-center gap-1">
                <input
                  type="checkbox"
                  checked={pluginSwitches.wangshuai}
                  onChange={(e) => setPluginSwitches((prev) => ({ ...prev, wangshuai: e.target.checked }))}
                />
                旺衰
              </label>
              <label className="inline-flex items-center gap-1">
                <input
                  type="checkbox"
                  checked={pluginSwitches.wealthRisk}
                  onChange={(e) => setPluginSwitches((prev) => ({ ...prev, wealthRisk: e.target.checked }))}
                />
                财富评估
              </label>
            </div>
            <label className="inline-flex items-center gap-2 rounded border border-zinc-700 bg-zinc-900 px-2 py-1 text-[11px] text-zinc-300">
              <input
                type="checkbox"
                checked={Number(labConfig.SHOW_WEAK_WORK_PATHS || 0) > 0.5}
                onChange={(e) => {
                  setLabConfig((prev) => ({
                    ...prev,
                    SHOW_WEAK_WORK_PATHS: e.target.checked ? 1 : 0,
                  }));
                }}
              />
              逻辑透深（显示微弱路径）
            </label>
            <button
              type="button"
              onClick={() => setLabGroupsOpen({ timing: true, riskTomb: true, climateTopology: true })}
              className="rounded border border-zinc-700 bg-zinc-900 px-2 py-1 text-[11px] text-zinc-300 hover:bg-zinc-800"
            >
              展开全部参数组
            </button>
            <button
              type="button"
              onClick={() => setLabGroupsOpen({ timing: false, riskTomb: false, climateTopology: false })}
              className="rounded border border-zinc-700 bg-zinc-900 px-2 py-1 text-[11px] text-zinc-300 hover:bg-zinc-800"
            >
              收起全部参数组
            </button>
            <button
              type="button"
              onClick={() => void onApplyRecalculate()}
              className="rounded-md border border-cyan-500/40 bg-cyan-500/10 px-2 py-1 text-xs text-cyan-200"
            >
              {variant === "engineRoom" ? "前往主实验室重算" : "应用并重算"}
            </button>
          </div>
          {labGroups.map((group) => (
            <div key={group.key} className="rounded-xl border border-zinc-800 bg-zinc-950 p-2">
              <button
                type="button"
                onClick={() => setLabGroupsOpen((prev) => ({ ...prev, [group.key]: !prev[group.key] }))}
                className="flex w-full items-center justify-between rounded-md border border-zinc-700 bg-zinc-900 px-3 py-2 text-left text-xs text-zinc-200 hover:bg-zinc-800"
              >
                <span>{group.title}</span>
                <span>{labGroupsOpen[group.key] ? "收起" : "展开"}</span>
              </button>
              {labGroupsOpen[group.key] ? (
                <div className="mt-2 grid grid-cols-1 gap-2 md:grid-cols-2">
                  {group.items.map(([key, min, max, step]) => (
                    <label key={String(key)} className="text-xs text-zinc-300">
                      <div className="mb-1 flex items-center justify-between">
                        <span>{String(key)}</span>
                        <span className="text-zinc-500">{Number(labConfig[key]).toFixed(2)}</span>
                      </div>
                      <input
                        type="range"
                        min={Number(min)}
                        max={Number(max)}
                        step={Number(step)}
                        value={Number(labConfig[key])}
                        onChange={(e) => {
                          const value = Number(e.target.value);
                          setLabConfig((prev) => ({ ...prev, [key]: value }));
                        }}
                        className="w-full"
                      />
                    </label>
                  ))}
                </div>
              ) : null}
            </div>
          ))}
        </div>
      ) : null}
    </section>
  );
}
