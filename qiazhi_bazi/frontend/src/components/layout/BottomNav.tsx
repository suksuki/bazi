"use client";

import { usePathname, useRouter } from "next/navigation";

const tabs = [
  { href: "/", label: "实验室", short: "Lab" },
  { href: "/debug", label: "黑匣子", short: "Dbg" },
  { href: "/admin", label: "机房", short: "Ops" },
] as const;

export function BottomNav() {
  const pathname = usePathname() || "/";
  const router = useRouter();

  const handleNav = (href: string) => {
    console.log(`[NAV_DISPATCH] 目标: ${href}`);
    try {
      router.push(href);
    } catch (e) {
      console.error("[NAV_ERROR] 路由被阻塞:", e);
    }
  };

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-50 border-t border-zinc-800/90 bg-zinc-950/95 backdrop-blur-md md:px-4" aria-label="主导航">
      <div className="mx-auto flex max-w-[1400px] items-stretch justify-around pb-[env(safe-area-inset-bottom,0px)] pt-1">
        {tabs.map((tab) => {
          const active = tab.href === "/" ? pathname === "/" : pathname.startsWith(tab.href);
          return (
            <button
              key={tab.href}
              type="button"
              className={`flex min-h-[3rem] flex-1 flex-col items-center justify-center gap-0.5 px-2 text-[10px] font-medium transition-colors transition-transform active:scale-90 md:text-xs ${
                active ? "text-amber-400" : "text-zinc-500 hover:text-zinc-300"
              }`}
              aria-label={tab.label}
              onClick={() => handleNav(tab.href)}
            >
              <span className="hidden sm:inline">{tab.label}</span>
              <span className="sm:hidden">{tab.short}</span>
            </button>
          );
        })}
      </div>
    </nav>
  );
}
