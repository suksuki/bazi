"use client";

import { useId, useState } from "react";

type Props = {
  id?: string;
  title: string;
  subtitle?: string;
  defaultOpen?: boolean;
  children: React.ReactNode;
};

export function SemanticAccordion({ id: idProp, title, subtitle, defaultOpen = false, children }: Props) {
  const gen = useId().replace(/:/g, "");
  const baseId = idProp ?? `acc-${gen}`;
  const [open, setOpen] = useState(Boolean(defaultOpen));
  const panelId = `${baseId}-panel`;

  return (
    <section className="rounded-xl border border-zinc-800/90 bg-zinc-950/45">
      <button
        type="button"
        className="flex w-full items-start justify-between gap-3 px-3 py-2.5 text-left hover:bg-zinc-900/40"
        aria-expanded={open}
        aria-controls={panelId}
        onClick={() => setOpen((v) => !v)}
      >
        <div className="min-w-0">
          <h2 className="text-sm font-semibold text-zinc-100">{title}</h2>
          {subtitle ? <p className="mt-0.5 text-[11px] leading-snug text-zinc-500">{subtitle}</p> : null}
        </div>
        <span className="shrink-0 pt-0.5 font-mono text-[11px] text-zinc-500">{open ? "▼" : "▶"}</span>
      </button>
      {open ? (
        <div id={panelId} className="border-t border-zinc-800/80 px-3 py-3">
          {children}
        </div>
      ) : null}
    </section>
  );
}
