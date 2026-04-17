"use client";

import type { Dispatch, SetStateAction } from "react";
import type { PhysicsLabConfig } from "@/features/stream-board/models";
import type { PluginSwitches } from "@/features/stream-board/models";

export type LabEngineConsoleProps = {
  labOpen: boolean;
  setLabOpen: (v: boolean | ((p: boolean) => boolean)) => void;
  /** 仅用于引擎室只读提示（微弱路径开关状态）；调参请用插件治理台 */
  labConfig: PhysicsLabConfig;
  pluginSwitches: PluginSwitches;
  setPluginSwitches: Dispatch<SetStateAction<PluginSwitches>>;
  onApplyRecalculate: () => void | Promise<void>;
  variant?: "main" | "engineRoom";
};

/**
 * 引擎室侧栏：插件开关与重算入口。
 * 原「物理实验参数」折叠滑块区已迁至插件治理台 CausalPluginCard「实验交互」（法典 Skill + physics_setting_key）。
 */
export function LabEngineConsole({
  labOpen,
  setLabOpen,
  labConfig,
  pluginSwitches,
  setPluginSwitches,
  onApplyRecalculate,
  variant = "main",
}: LabEngineConsoleProps) {
  const title = variant === "engineRoom" ? "实验室会话（引擎室）" : "Lab Console";
  const hint =
    variant === "engineRoom" ? (
      <p className="mb-2 rounded border border-cyan-500/30 bg-cyan-500/5 px-2 py-1 text-[11px] text-cyan-200/90">
        数值 η 请在主屏「插件治理工作台」对应 L1 卡片展开「实验交互」调节；此处仅保留会话级开关与重算入口。
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
            <button
              type="button"
              onClick={() => void onApplyRecalculate()}
              className="rounded-md border border-cyan-500/40 bg-cyan-500/10 px-2 py-1 text-xs text-cyan-200"
            >
              {variant === "engineRoom" ? "前往主实验室重算" : "应用并重算"}
            </button>
          </div>
          <p className="text-[10px] leading-relaxed text-zinc-500">
            全局物理键（如 WEIGHT_LUCK、TOMB_LOCK_RATE）已注册为 Skill，见{" "}
            <span className="font-mono text-zinc-400">base.physics.op_lab_*</span> 卡片。
            {Number(labConfig.SHOW_WEAK_WORK_PATHS || 0) > 0.5 ? " 当前已开启微弱路径显示。" : ""}
          </p>
        </div>
      ) : null}
    </section>
  );
}
