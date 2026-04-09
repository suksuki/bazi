"use client";

import { usePathname } from "next/navigation";

const tabs = [
  { href: "/", label: "实验室", short: "Lab" },
  { href: "/debug", label: "黑匣子", short: "Dbg" },
  { href: "/admin", label: "机房", short: "Ops" },
] as const;

export function BottomNav() {
  const pathname = usePathname() || "/";
  const markReturnRestore = (targetHref: string) => {
    if (typeof window === "undefined") return;
    if (pathname !== "/") return;
    if (targetHref === "/debug" || targetHref === "/admin") {
      sessionStorage.setItem("qiazhi_return_restore_once", "1");
    }
  };

  return (
    <nav
      className="pointer-events-auto fixed bottom-0 left-0 right-0 z-[200] border-t border-zinc-800/90 bg-zinc-950/95 backdrop-blur-md md:px-4"
      aria-label="主导航"
    >
      <div className="mx-auto flex max-w-[1400px] items-stretch justify-around pb-[env(safe-area-inset-bottom,0px)] pt-1">
        {tabs.map((tab) => {
          const active = tab.href === "/" ? pathname === "/" : pathname.startsWith(tab.href);
          const href = tab.href === "/" && pathname !== "/" ? "/?resume=1" : tab.href;
          return (
            <a
              key={tab.href}
              href={href}
              onClick={() => markReturnRestore(tab.href)}
              className={`pointer-events-auto relative z-[210] flex min-h-[3rem] flex-1 flex-col items-center justify-center gap-0.5 px-2 text-[10px] font-medium transition-colors md:text-xs ${
                active ? "text-amber-400" : "text-zinc-500 hover:text-zinc-300"
              }`}
            >
              <span className="hidden sm:inline">{tab.label}</span>
              <span className="sm:hidden">{tab.short}</span>
            </a>
          );
        })}
      </div>
    </nav>
  );
}
