"use client";

import { useCallback, useMemo, useState } from "react";
import { humanizeProvenanceSnippet } from "./semanticLexicon";

export type ProvenanceKind = "system" | "llm";

export type NarrativeSegment = {
  id: string;
  traceId: string;
  kind: ProvenanceKind;
  /** 人话标题（含证据码语义化） */
  displayTitle: string;
  text: string;
  /** 供弹层展示的提示词/证据上下文 */
  contextSnippet: string;
};

function shortTraceId(text: string, salt: string): string {
  let h = 0;
  const s = `${salt}:${text}`;
  for (let i = 0; i < s.length; i++) h = (Math.imul(31, h) + s.charCodeAt(i)) | 0;
  return `TR-${Math.abs(h).toString(16).padStart(8, "0")}`;
}

function classifyLine(line: string, isFromVerdictBody: boolean): ProvenanceKind {
  const s = line.trim();
  if (isFromVerdictBody) return "llm";
  if (/^\[L1|Junction|junction|格局优先|伤官见官|三合|墓库|盲派规则|系统预设|physics_tensor\.evidence/i.test(s)) return "system";
  if (/^Evidence:|物理层|meta\.|audit_log|hard_route|causal_routing_audit/i.test(s)) return "system";
  return "llm";
}

type Props = {
  snapshot: Record<string, unknown> | null;
  llmPrompt?: string | null;
};

export function NarrativeProvenancePanel({ snapshot, llmPrompt }: Props) {
  const [open, setOpen] = useState<NarrativeSegment | null>(null);

  const segments = useMemo(() => {
    if (!snapshot) return [] as NarrativeSegment[];
    const out: NarrativeSegment[] = [];
    const physics = snapshot.physics_tensor as Record<string, unknown> | undefined;
    const ev = Array.isArray(physics?.evidence) ? (physics!.evidence as unknown[]) : [];
    ev.forEach((x, i) => {
      const text = String(x);
      const id = `sys-ev-${i}`;
      const { title, body } = humanizeProvenanceSnippet(text);
      out.push({
        id,
        traceId: shortTraceId(text, id),
        kind: "system",
        displayTitle: title,
        text: body || text,
        contextSnippet: `physics_tensor.evidence[${i}]`,
      });
    });

    const audit = (physics?.audit_log as Record<string, unknown> | undefined) || {};
    const cra = Array.isArray(audit.causal_routing_audit_items) ? audit.causal_routing_audit_items : [];
    cra.forEach((item, i) => {
      if (!item || typeof item !== "object") return;
      const row = item as Record<string, unknown>;
      const text = String(row.routing_decision || JSON.stringify(row)).slice(0, 400);
      const id = `sys-cr-${i}`;
      const { title, body } = humanizeProvenanceSnippet(text);
      out.push({
        id,
        traceId: shortTraceId(text, id),
        kind: "system",
        displayTitle: title.startsWith("[") ? title : `[路由审计#${i + 1}] ${title}`,
        text: body || text,
        contextSnippet: `audit_log.causal_routing_audit_items[${i}]`,
      });
    });

    const fv = snapshot.final_verdict as Record<string, unknown> | undefined;
    const le = Array.isArray(fv?.logical_evidence) ? (fv!.logical_evidence as unknown[]) : [];
    le.forEach((x, i) => {
      const text = String(x);
      const id = `llm-le-${i}`;
      const { title, body } = humanizeProvenanceSnippet(text);
      out.push({
        id,
        traceId: shortTraceId(text, id),
        kind: "llm",
        displayTitle: title,
        text: body || text,
        contextSnippet: `final_verdict.logical_evidence[${i}]`,
      });
    });

    const body = fv?.body ? String(fv.body) : "";
    if (body) {
      body
        .split(/\n+/)
        .map((p) => p.trim())
        .filter(Boolean)
        .slice(0, 24)
        .forEach((para, i) => {
          const id = `llm-body-${i}`;
          const kind = classifyLine(para, true);
          const { title, body } = humanizeProvenanceSnippet(para);
          out.push({
            id,
            traceId: shortTraceId(para, id),
            kind,
            displayTitle: title,
            text: body || para,
            contextSnippet: `final_verdict.body §${i + 1}`,
          });
        });
    }

    return out;
  }, [snapshot]);

  const promptHead = typeof llmPrompt === "string" ? llmPrompt.slice(0, 420) : "";

  const onKeyNavigate = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "Escape") setOpen(null);
    },
    [],
  );

  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-950/50 p-3">
      <p className="text-[10px] font-medium uppercase tracking-wide text-zinc-500">判语血统 · 溯源</p>
      <p className="mt-1 text-[11px] text-zinc-500">
        <span className="rounded bg-sky-950/60 px-1 py-0.5 text-sky-200/95">蓝底</span> 系统规则链（证据 / 路由审计）；{" "}
        <span className="rounded bg-violet-950/60 px-1 py-0.5 text-violet-200/95">紫底</span> LLM 终审装配。点击条目查看 Trace
        ID 与上下文键。
      </p>

      <ul className="mt-3 max-h-72 space-y-2 overflow-auto">
        {segments.length === 0 ? (
          <li className="text-[11px] text-zinc-600">尚无判语片段（排盘并生成终判后更丰富）。</li>
        ) : (
          segments.map((seg) => (
            <li key={seg.id}>
              <button
                type="button"
                onClick={() => setOpen(seg)}
                className={`w-full rounded-lg border px-2 py-2 text-left text-[11px] leading-snug transition-colors ${
                  seg.kind === "system"
                    ? "border-sky-800/60 bg-sky-950/35 text-sky-50 hover:bg-sky-900/40"
                    : "border-violet-800/60 bg-violet-950/35 text-violet-50 hover:bg-violet-900/40"
                }`}
              >
                <span className="font-mono text-[9px] text-zinc-500">{seg.traceId}</span>
                <p className="mt-1 text-[12px] font-medium leading-snug text-zinc-50">{seg.displayTitle}</p>
                <p className="mt-1 line-clamp-3 text-zinc-300">{seg.text}</p>
              </button>
            </li>
          ))
        )}
      </ul>

      {open ? (
        <div
          className="fixed inset-0 z-50 flex items-end justify-center bg-black/55 p-3 sm:items-center"
          role="dialog"
          aria-modal
          onKeyDown={onKeyNavigate}
          tabIndex={-1}
        >
          <div className="max-h-[min(80dvh,520px)] w-full max-w-lg overflow-auto rounded-xl border border-zinc-700 bg-zinc-950 p-4 text-xs shadow-xl">
            <div className="flex items-start justify-between gap-2">
              <p className="font-mono text-[10px] text-amber-200/90">{open.traceId}</p>
              <button
                type="button"
                className="rounded border border-zinc-700 px-2 py-0.5 text-[10px] text-zinc-400 hover:bg-zinc-900"
                onClick={() => setOpen(null)}
              >
                关闭
              </button>
            </div>
            <p className="mt-2 text-[10px] uppercase tracking-wide text-zinc-500">来源键</p>
            <p className="mt-0.5 font-mono text-[11px] text-cyan-200/90">{open.contextSnippet}</p>
            <p className="mt-3 text-[10px] uppercase tracking-wide text-zinc-500">提示词上下文（头部截断）</p>
            <pre className="mt-1 max-h-40 overflow-auto whitespace-pre-wrap break-all rounded border border-zinc-800 bg-black/40 p-2 font-mono text-[10px] text-zinc-400">
              {promptHead || "（当前快照无 llm_prompt）"}
            </pre>
            <p className="mt-3 text-[10px] uppercase tracking-wide text-zinc-500">判语片段</p>
            <p className="mt-1 whitespace-pre-wrap text-[12px] leading-relaxed text-zinc-200">{open.text}</p>
          </div>
        </div>
      ) : null}
    </div>
  );
}
