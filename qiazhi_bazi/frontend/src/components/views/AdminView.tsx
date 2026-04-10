"use client";

import { useState } from "react";
import { useActiveView } from "@/components/layout/ActiveViewContext";
import { EngineRoomPanel } from "@/features/admin/EngineRoomPanel";
import { PluginManagementPanel } from "@/features/admin/components/PluginManagementPanel";
import { AdminSettingsView } from "@/features/admin-settings/AdminSettingsView";
import { useAdminSettingsController } from "@/features/admin-settings/useAdminSettingsController";
import { useLabStore } from "@/features/stream-board/stores/useLabStore";

type AdminSection = "overview" | "engine" | "infra" | "plugins";

const sections: { id: AdminSection; label: string }[] = [
  { id: "overview", label: "概览" },
  { id: "engine", label: "引擎" },
  { id: "infra", label: "基础设施" },
  { id: "plugins", label: "插件" },
];

export function AdminView() {
  const { setActiveView } = useActiveView();
  const { state, requestCausalRevert } = useLabStore();
  const settings = useAdminSettingsController();
  const [section, setSection] = useState<AdminSection>("overview");

  const hasBaseline = Boolean(state.snapshot?.baseline_snapshot);
  const absDelta = state.snapshot?.logic_diff?.abs_delta;

  return (
    <div className="mx-auto min-h-dvh w-full max-w-5xl px-3 py-4 text-zinc-200">
      <div className="mb-4 flex flex-wrap items-end justify-between gap-3 border-b border-zinc-800 pb-3">
        <div>
          <h1 className="text-base font-semibold">机房</h1>
          <p className="mt-0.5 text-xs text-zinc-500">与实验室共用当前会话，不另开路由。</p>
        </div>
        <button
          type="button"
          onClick={() => setActiveView("lab")}
          className="rounded border border-zinc-600 bg-zinc-900 px-3 py-1.5 text-xs hover:bg-zinc-800"
        >
          回实验室
        </button>
      </div>

      <div className="mb-4 flex flex-wrap gap-1">
        {sections.map((s) => (
          <button
            key={s.id}
            type="button"
            onClick={() => setSection(s.id)}
            className={`rounded px-3 py-1.5 text-xs ${
              section === s.id ? "bg-amber-500/20 text-amber-200" : "text-zinc-400 hover:bg-zinc-800"
            }`}
          >
            {s.label}
          </button>
        ))}
      </div>

      <div className={section === "overview" ? "block" : "hidden"}>
        <div className="space-y-3 rounded border border-zinc-800 bg-zinc-900/40 p-4 text-sm">
          <p className="text-zinc-400">
            abs_delta：{typeof absDelta === "number" ? absDelta.toFixed(2) : "—"}
          </p>
          <p className="text-xs text-zinc-500">
            基线时间：
            {state.snapshot?.baseline_snapshot?.at
              ? new Date(state.snapshot.baseline_snapshot.at).toLocaleString()
              : "—"}
          </p>
          <button
            type="button"
            disabled={!hasBaseline}
            onClick={() => {
              requestCausalRevert();
              setActiveView("lab");
            }}
            className="rounded border border-fuchsia-600/50 bg-fuchsia-950/40 px-3 py-1.5 text-xs text-fuchsia-100 disabled:cursor-not-allowed disabled:opacity-40"
          >
            撤回到基线锚点
          </button>
        </div>
      </div>

      <div className={section === "engine" ? "block" : "hidden"}>
        <EngineRoomPanel />
      </div>

      <div className={section === "infra" ? "block" : "hidden"}>
        <AdminSettingsView controller={settings} />
      </div>

      <div className={section === "plugins" ? "block" : "hidden"}>
        <PluginManagementPanel />
      </div>
    </div>
  );
}
