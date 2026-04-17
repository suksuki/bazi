"use client";

import dynamic from "next/dynamic";
import { useMemo, useState } from "react";
import { StreamBoard } from "@/components/StreamBoard";
import { ActiveViewContext, type ShellActiveView } from "@/components/layout/ActiveViewContext";
import { ShellDashboardTabs } from "@/components/layout/ShellDashboardTabs";

const DebugView = dynamic(() => import("@/components/views/DebugView").then((m) => m.DebugView), { ssr: false });
const AdminView = dynamic(() => import("@/components/views/AdminView").then((m) => m.AdminView), { ssr: false });

export default function HomePage() {
  const [activeView, setActiveView] = useState<ShellActiveView>("lab");
  const value = useMemo(() => ({ activeView, setActiveView }), [activeView]);

  return (
    <ActiveViewContext.Provider value={value}>
      <div className="flex min-h-dvh flex-col">
        <ShellDashboardTabs />
        <div className="min-h-0 flex-1 pb-[env(safe-area-inset-bottom,0px)]">
          {/* 实验室须保持挂载：用 Tab 切到黑匣子/机房再回来时，若此处曾渲染为 null 会卸载整棵 StreamBoard，排盘与终判等内存态会丢失。 */}
          <div
            className={activeView === "lab" ? "flex min-h-dvh flex-col" : "hidden"}
            aria-hidden={activeView !== "lab"}
          >
            <StreamBoard />
          </div>
          {activeView === "debug" ? <DebugView /> : null}
          {activeView === "admin" ? <AdminView /> : null}
        </div>
      </div>
    </ActiveViewContext.Provider>
  );
}
