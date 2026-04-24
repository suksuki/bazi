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

function tabTone(active: boolean): string {
  return active
    ? "border-cyan-400/40 bg-cyan-950/35 text-cyan-50 shadow-[0_0_24px_rgba(34,211,238,0.12)]"
    : "border-zinc-800 bg-zinc-950/55 text-zinc-400 hover:border-zinc-700 hover:text-zinc-200";
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
  return (
    <div className={`sticky ${stickyTopClassName} z-20 border-y border-zinc-800 bg-zinc-950/95 px-3 py-2 backdrop-blur sm:static sm:rounded-2xl sm:border sm:bg-zinc-900/45 sm:p-2.5 sm:backdrop-blur-none`}>
      <div className={`-mx-1 flex snap-x snap-mandatory gap-2 overflow-x-auto px-1 pb-1 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden sm:mx-0 sm:grid sm:overflow-visible sm:px-0 sm:pb-0 ${desktopGridClass(items.length)}`}>
        {items.map((item) => (
          <button
            key={item.id}
            type="button"
            aria-pressed={activeId === item.id}
            onClick={() => onChange(item.id)}
            className={`min-w-[46%] snap-start rounded-xl border px-3 py-2 text-left transition sm:min-w-0 sm:py-3 ${tabTone(activeId === item.id)}`}
          >
            <div className="flex items-center justify-between gap-2">
              <span className="truncate text-sm font-semibold">{item.label}</span>
              {item.badge ? (
                <span className="shrink-0 rounded-full border border-white/10 bg-black/20 px-2 py-0.5 text-[10px]">
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
  );
}
