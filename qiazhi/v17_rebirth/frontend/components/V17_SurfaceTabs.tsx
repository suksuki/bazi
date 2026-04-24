"use client";

import type { ReactNode } from "react";
import {
  Activity,
  BarChart3,
  BrainCircuit,
  BriefcaseBusiness,
  Database,
  FlaskConical,
  Gauge,
  KeyRound,
  PlugZap,
  ScrollText,
  Settings,
  Sparkles,
  Users,
} from "lucide-react";

export type V17SurfaceTabItem<T extends string> = {
  id: T;
  label: ReactNode;
  description?: ReactNode;
  badge?: ReactNode;
};

type Props<T extends string> = {
  items: Array<V17SurfaceTabItem<T>>;
  activeId: T;
  onChange: (id: T) => void;
  stickyTopClassName?: string;
};

function desktopTabTone(active: boolean): string {
  return active
    ? "sm:border-cyan-400/40 sm:bg-cyan-950/35 sm:text-cyan-50 sm:shadow-[0_0_24px_rgba(34,211,238,0.12)]"
    : "sm:border-zinc-800 sm:bg-zinc-950/55 sm:text-zinc-400 sm:hover:border-zinc-700 sm:hover:text-zinc-200";
}

function mobileTabTone(active: boolean): string {
  return active
    ? "border-amber-400/30 bg-amber-400/10 text-amber-300"
    : "border-transparent text-zinc-400 hover:bg-white/5 hover:text-zinc-100";
}

function mobileLayoutClass(count: number): string {
  if (count === 1) return "grid grid-cols-1";
  if (count === 2) return "grid grid-cols-2";
  if (count === 3) return "grid grid-cols-3";
  if (count === 4) return "grid grid-cols-4";
  return "flex snap-x snap-mandatory overflow-x-auto [scrollbar-width:none] [&::-webkit-scrollbar]:hidden";
}

function desktopGridClass(count: number): string {
  if (count >= 3) return "sm:grid-cols-3";
  if (count === 2) return "sm:grid-cols-2";
  return "sm:grid-cols-1";
}

function tabIcon(id: string, active: boolean) {
  const className = `h-4 w-4 ${active ? "text-amber-300" : "text-zinc-400"}`;
  if (id === "core") return <ScrollText className={className} />;
  if (id === "auxiliary") return <BarChart3 className={className} />;
  if (id === "trace") return <BriefcaseBusiness className={className} />;
  if (id === "llm") return <BrainCircuit className={className} />;
  if (id === "db") return <Database className={className} />;
  if (id === "plugins") return <PlugZap className={className} />;
  if (id === "physics") return <Gauge className={className} />;
  if (id === "evolution") return <Activity className={className} />;
  if (id === "learning") return <FlaskConical className={className} />;
  if (id === "users") return <Users className={className} />;
  if (id === "access") return <KeyRound className={className} />;
  return active ? <Sparkles className={className} /> : <Settings className={className} />;
}

export function V17_SurfaceTabs<T extends string>({
  items,
  activeId,
  onChange,
}: Props<T>) {
  const isScrollableMobile = items.length > 4;

  return (
    <div className="fixed inset-x-0 bottom-0 z-40 border-t border-white/10 bg-[#080d13]/92 px-3 pb-[calc(env(safe-area-inset-bottom)+8px)] pt-2 shadow-[0_-18px_48px_rgba(0,0,0,0.42)] backdrop-blur-xl sm:sticky sm:top-[90px] sm:z-20 sm:rounded-2xl sm:border sm:border-zinc-800 sm:bg-zinc-900/45 sm:p-2.5 sm:shadow-none sm:backdrop-blur-none">
      <div className="rounded-2xl border border-white/10 bg-white/[0.04] p-1 shadow-[inset_0_1px_0_rgba(255,255,255,0.04)] sm:rounded-none sm:border-0 sm:bg-transparent sm:p-0 sm:shadow-none">
        <div
          role="tablist"
          className={`${mobileLayoutClass(items.length)} gap-1 sm:mx-0 sm:grid sm:gap-2 sm:overflow-visible sm:px-0 sm:pb-0 ${desktopGridClass(items.length)}`}
        >
          {items.map((item) => {
            const active = activeId === item.id;
            return (
              <button
                key={item.id}
                role="tab"
                type="button"
                aria-selected={active}
                onClick={() => onChange(item.id)}
                className={`${isScrollableMobile ? "min-w-[38%] snap-start" : "min-w-0"} rounded-xl border px-2 py-2 text-center transition-all duration-200 active:scale-[0.98] sm:min-w-0 sm:px-3 sm:py-3 sm:text-left ${mobileTabTone(active)} ${desktopTabTone(active)}`}
              >
                <div className="flex min-w-0 flex-col items-center justify-center gap-1 sm:flex-row sm:justify-between sm:gap-2">
                  <span className="sm:hidden">{tabIcon(String(item.id), active)}</span>
                  <span className="max-w-full truncate text-[11px] font-semibold leading-4 sm:text-sm sm:leading-5">{item.label}</span>
                  {item.badge ? (
                    <span className="hidden max-w-full shrink-0 truncate rounded-full border border-white/10 bg-black/20 px-2 py-0.5 text-[10px] text-current sm:inline-flex">
                      {item.badge}
                    </span>
                  ) : null}
                </div>
                {item.description ? (
                  <p className="mt-1 hidden text-[11px] leading-5 text-inherit/80 sm:block">
                    {item.description}
                  </p>
                ) : null}
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
