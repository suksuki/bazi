"use client";

type Mode = "VISION" | "COMMAND";

type Props = {
  viewMode: Mode;
  onToggle: () => void;
};

/** 移动端优先：右下角在「视觉↔指令」间切换（雷达 / 文档） */
export function LabViewModeFab({ viewMode, onToggle }: Props) {
  const nextIsCommand = viewMode === "VISION";
  return (
    <button
      type="button"
      aria-label={nextIsCommand ? "切换到指令舱" : "切换到视觉仪表盘"}
      onClick={onToggle}
      className="fixed bottom-[max(1rem,env(safe-area-inset-bottom))] right-4 z-[45] flex h-14 w-14 items-center justify-center rounded-full border border-amber-500/50 bg-zinc-950/95 text-xl shadow-lg shadow-amber-900/20 backdrop-blur-md transition hover:border-amber-400/70 hover:bg-zinc-900 md:hidden"
    >
      <span className="sr-only">{nextIsCommand ? "指令舱" : "视觉仪表盘"}</span>
      {nextIsCommand ? (
        <svg aria-hidden className="h-7 w-7 text-amber-200/95" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 8.25h4.125c.621 0 1.125.504 1.125 1.125v9.75c0 .621-.504 1.125-1.125 1.125H8.25a1.125 1.125 0 0 1-1.125-1.125V9.375c0-.621.504-1.125 1.125-1.125Z" />
        </svg>
      ) : (
        <svg aria-hidden className="h-7 w-7 text-amber-200/95" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M9.348 14.652a3.75 3.75 0 0 1 0-5.304m5.304 0a3.75 3.75 0 0 1 0 5.304m-7.425 2.121a6.75 6.75 0 0 1 0-9.546m9.546 0a6.75 6.75 0 0 1 0 9.546M5.106 18.894a9.75 9.75 0 0 1 0-13.788m13.788 0a9.75 9.75 0 0 1 0 13.788M12 12h.008v.008H12V12Z" />
        </svg>
      )}
    </button>
  );
}
