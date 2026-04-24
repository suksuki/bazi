"use client";

import type { ReactNode } from "react";

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
    ? "border-cyan-400/45 bg-cyan-300 text-zinc-950 shadow-[0_10px_28px_rgba(34,211,238,0.22)]"
    : "border-transparent text-zinc-400 hover:bg-zinc-800/70 hover:text-zinc-100";
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

export function V17_SurfaceTabs<T extends string>({
  items,
  activeId,
  onChange,
  stickyTopClassName = "top-[90px]",
}: Props<T>) {
  const isScrollableMobile = items.length > 4;

  return (
    <div className={`sticky ${stickyTopClassName} z-20 border-b border-zinc-800 bg-zinc-950/96 px-3 py-2 backdrop-blur sm:static sm:rounded-2xl sm:border sm:bg-zinc-900/45 sm:p-2.5 sm:backdrop-blur-none`}>
      <div className="rounded-2xl border border-zinc-800 bg-zinc-900/80 p-1 shadow-[inset_0_1px_0_rgba(255,255,255,0.04)] sm:rounded-none sm:border-0 sm:bg-transparent sm:p-0 sm:shadow-none">
        <div
          role="tablist"
          className={`${mobileLayoutClass(items.length)} gap-1 sm:mx-0 sm:grid sm:gap-2 sm:overflow-visible sm:px-0 sm:pb-0 ${desktopGridClass(items.length)}`}
        >
          {items.map((item) => (
            <button
              key={item.id}
              role="tab"
              type="button"
              aria-selected={activeId === item.id}
              onClick={() => onChange(item.id)}
              className={`${isScrollableMobile ? "min-w-[38%] snap-start" : "min-w-0"} rounded-xl border px-2 py-2 text-center transition sm:min-w-0 sm:px-3 sm:py-3 sm:text-left ${mobileTabTone(activeId === item.id)} ${desktopTabTone(activeId === item.id)}`}
            >
              <div className="flex min-w-0 flex-col items-center justify-center gap-1 sm:flex-row sm:justify-between sm:gap-2">
                <span className="max-w-full truncate text-[12px] font-semibold leading-5 sm:text-sm">{item.label}</span>
                {item.badge ? (
                  <span className="max-w-full shrink-0 truncate rounded-full border border-black/10 bg-black/10 px-1.5 py-0.5 text-[9px] leading-3 text-current sm:border-white/10 sm:bg-black/20 sm:px-2 sm:text-[10px]">
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
          ))}
        </div>
      </div>
    </div>
  );
}
