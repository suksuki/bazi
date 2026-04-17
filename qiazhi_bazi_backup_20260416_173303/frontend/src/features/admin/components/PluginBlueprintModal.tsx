"use client";

import { useEffect, type ReactNode } from "react";

function renderInlineBold(text: string): ReactNode {
  const parts = text.split(/\*\*([^*]+)\*\*/g);
  return parts.map((bit, bi) =>
    bi % 2 === 1 ? (
      <strong key={bi} className="font-semibold text-zinc-100">
        {bit}
      </strong>
    ) : (
      <span key={bi}>{bit}</span>
    ),
  );
}

/** 轻量 Markdown：``` 代码块 + **粗体** + 换行，无额外依赖。 */
export function SimpleBlueprintMarkdown({ text }: { text: string }) {
  const chunks = text.split(/```/);
  return (
    <div className="space-y-2 text-[12px] leading-relaxed text-zinc-300">
      {chunks.map((chunk, i) => {
        if (i % 2 === 1) {
          const body = chunk.replace(/^\w*\n/, "").trimEnd();
          return (
            <pre
              key={i}
              className="overflow-x-auto rounded-lg border border-zinc-800 bg-zinc-950/90 p-3 font-mono text-[11px] leading-snug text-cyan-100/95"
            >
              {body}
            </pre>
          );
        }
        return (
          <div key={i} className="whitespace-pre-wrap [text-wrap:pretty]">
            {chunk.split("\n").map((line, li) => (
              <p key={li} className={li > 0 ? "mt-1.5" : ""}>
                {line.startsWith("|") ? (
                  <span className="font-mono text-[11px] text-zinc-400">{line}</span>
                ) : (
                  renderInlineBold(line)
                )}
              </p>
            ))}
          </div>
        );
      })}
    </div>
  );
}

export function PluginBlueprintModal(props: {
  open: boolean;
  title: string;
  markdown: string;
  onClose: () => void;
}) {
  const { open, title, markdown, onClose } = props;

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-[80] flex items-center justify-center bg-black/70 px-3 py-8"
      role="dialog"
      aria-modal="true"
      aria-labelledby="blueprint-modal-title"
      onClick={onClose}
    >
      <div
        className="max-h-[min(88vh,760px)] w-full max-w-2xl overflow-hidden rounded-xl border border-zinc-600 bg-zinc-950 shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <header className="flex items-start justify-between gap-3 border-b border-zinc-800 bg-zinc-900/80 px-4 py-3">
          <div>
            <p id="blueprint-modal-title" className="text-sm font-semibold text-zinc-100">
              逻辑蓝图
            </p>
            <p className="mt-0.5 font-mono text-[10px] text-violet-300/90">{title}</p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-md border border-zinc-700 px-2 py-1 text-xs text-zinc-300 hover:bg-zinc-800"
          >
            关闭
          </button>
        </header>
        <div className="max-h-[min(72vh,640px)] overflow-y-auto px-4 py-4">
          <SimpleBlueprintMarkdown text={markdown} />
        </div>
      </div>
    </div>
  );
}
