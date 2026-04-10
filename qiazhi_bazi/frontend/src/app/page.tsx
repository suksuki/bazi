"use client";

import { useMemo, useState } from "react";
import { StreamBoard } from "@/components/StreamBoard";
import { ActiveViewContext, type ShellActiveView } from "@/components/layout/ActiveViewContext";
import { ShellDashboardTabs } from "@/components/layout/ShellDashboardTabs";
import { AdminView } from "@/components/views/AdminView";
import { DebugView } from "@/components/views/DebugView";

export default function HomePage() {
  const [activeView, setActiveView] = useState<ShellActiveView>("lab");
  const value = useMemo(() => ({ activeView, setActiveView }), [activeView]);

  return (
    <ActiveViewContext.Provider value={value}>
      <div className="flex min-h-dvh flex-col">
        <ShellDashboardTabs />
        <div className="min-h-0 flex-1 pb-[env(safe-area-inset-bottom,0px)]">
          <div className={activeView === "lab" ? "block" : "hidden"} aria-hidden={activeView !== "lab"}>
            <div className="flex min-h-dvh flex-col">
              <StreamBoard />
            </div>
          </div>
          <div className={activeView === "debug" ? "block" : "hidden"} aria-hidden={activeView !== "debug"}>
            <DebugView />
          </div>
          <div className={activeView === "admin" ? "block" : "hidden"} aria-hidden={activeView !== "admin"}>
            <AdminView />
          </div>
        </div>
      </div>
    </ActiveViewContext.Provider>
  );
}
