"use client";

import type { ShellActiveView } from "@/components/layout/ActiveViewContext";
import { useActiveView } from "@/components/layout/ActiveViewContext";
import { staticT } from "@/features/stream-board/constants";
import { useUiLang } from "@/features/stream-board/stores/useLabStore";

const tabs: { id: ShellActiveView; labelZh: string }[] = [
  { id: "lab", labelZh: "实验室" },
  { id: "debug", labelZh: "黑匣子" },
  { id: "admin", labelZh: "机房" },
];

/**
 * 顶栏仪表盘式分段 Tab（与实验室内「视觉 / 指令」同系：圆角轨道 + 选中块高亮），仅切换 activeView，不做路由跳转。
 */
export function ShellDashboardTabs() {
  const { activeView, setActiveView } = useActiveView();
  const { uiLang } = useUiLang();

  return (
    <header className="sticky top-0 z-[60] border-b border-zinc-800/80 bg-zinc-950/95 backdrop-blur-md">
      <div className="mx-auto flex max-w-[1400px] justify-center px-3 pb-3 pt-[max(0.6rem,env(safe-area-inset-top))]">
        <div
          role="tablist"
          aria-label="主视图切换"
          className="flex w-full max-w-xl rounded-2xl border border-zinc-800 bg-zinc-950 p-1 shadow-[inset_0_1px_0_rgba(255,255,255,0.04)]"
        >
          {tabs.map((tab) => {
            const active = activeView === tab.id;
            const label = staticT(uiLang, tab.labelZh);
            return (
              <button
                key={tab.id}
                type="button"
                role="tab"
                aria-selected={active}
                className={`relative flex min-h-[2.75rem] flex-1 items-center justify-center rounded-xl px-2 py-2 text-center text-xs font-medium transition-colors sm:min-h-0 sm:px-3 sm:py-2.5 sm:text-sm ${
                  active
                    ? "bg-cyan-900/75 text-cyan-50 shadow-[0_1px_8px_rgba(6,78,95,0.45)]"
                    : "text-zinc-500 hover:text-zinc-300"
                }`}
                onClick={() => setActiveView(tab.id)}
              >
                {label}
              </button>
            );
          })}
        </div>
      </div>
    </header>
  );
}
