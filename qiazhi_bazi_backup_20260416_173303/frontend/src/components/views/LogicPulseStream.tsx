"use client";

import { useMemo, useState } from "react";

type TraceRow = {
  trace_id?: string;
  stage?: string;
  at?: string | number;
  messages?: Array<{ role?: string; content?: string }>;
  response_text?: string;
  rendered_verdict_body?: string;
  llm_meta?: Record<string, unknown>;
  fact_ids?: string[];
};

function safeJson(x: unknown): string {
  try {
    return JSON.stringify(x, null, 2);
  } catch {
    return String(x);
  }
}

function tsScore(at: string | number | undefined): number {
  if (typeof at === "number" && Number.isFinite(at)) return at;
  const t = Date.parse(String(at || ""));
  return Number.isFinite(t) ? t : 0;
}

function short(text: string, n: number): string {
  const s = String(text || "").trim();
  if (s.length <= n) return s;
  return `${s.slice(0, n)}...`;
}

function detectFactIds(row: TraceRow): string[] {
  const got = new Set<string>();
  const push = (v: string) => {
    const x = String(v || "").trim();
    if (x) got.add(x);
  };
  for (const x of row.fact_ids || []) push(x);
  for (const m of row.messages || []) {
    const c = String(m?.content || "");
    for (const mm of c.matchAll(/(?:Fact_ID|FACT_ID|fact_id)\s*[:=]\s*([A-Za-z0-9:_\-\[\]\.]+)/g)) {
      if (mm[1]) push(mm[1]);
    }
    for (const mm of c.matchAll(/conflict_matrix\.points\[\d+\]/g)) push(mm[0]);
  }
  return Array.from(got).slice(0, 24);
}

function topicOf(row: TraceRow): string {
  const meta = (row.llm_meta || {}) as Record<string, unknown>;
  const titleZh = String(meta.title_zh || "").trim();
  if (titleZh) return titleZh;
  const ps = String(meta.prompt_scenario || "").trim();
  if (ps) return ps;
  const stage = String(row.stage || "").trim();
  const s = stage.toUpperCase();
  if (s === "FIRST_OBSERVATION") return "首观 / Node_Chain_Execution";
  if (s === "ARBITRATION" || s === "ARBITER") return "仲裁 / conflict arbitration";
  if (s === "FINAL_VERDICT") return "终判 / final synthesis";
  return stage || "LLM 对话";
}

export function LogicPulseStream(props: {
  rows: TraceRow[];
  onHoverFacts?: (factIds: string[]) => void;
}) {
  const { rows, onHoverFacts } = props;
  const [openRawId, setOpenRawId] = useState<string>("");
  const [openPromptId, setOpenPromptId] = useState<string>("");
  const [openRespId, setOpenRespId] = useState<string>("");
  const [finalViewMode, setFinalViewMode] = useState<Record<string, "raw" | "rendered">>({});
  const [expandAll, setExpandAll] = useState(false);
  const ordered = useMemo(() => [...rows].sort((a, b) => tsScore(a.at) - tsScore(b.at)), [rows]);

  if (!ordered.length) {
    return <p className="text-xs text-zinc-500">暂无 full_trace 记录（执行首观/仲裁/终判后会在此聚合）。</p>;
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-end">
        <button
          type="button"
          className="rounded border border-zinc-700 px-2 py-1 text-[10px] text-zinc-300 hover:bg-zinc-900"
          onClick={() => {
            const next = !expandAll;
            setExpandAll(next);
            if (!next) {
              setOpenPromptId("");
              setOpenRespId("");
              setOpenRawId("");
            }
          }}
        >
          {expandAll ? "收起全部" : "一键展开全部"}
        </button>
      </div>
      {ordered.map((row, i) => {
        const id = String(row.trace_id || `trace-${i}`);
        const facts = detectFactIds(row);
        const messages = Array.isArray(row.messages) ? row.messages : [];
        const rawOpen = expandAll || openRawId === id;
        const promptOpen = expandAll || openPromptId === id;
        const respOpen = expandAll || openRespId === id;
        const stage = String(row.stage || "").toUpperCase();
        const isFinalVerdict = stage === "FINAL_VERDICT";
        const viewMode = finalViewMode[id] || "raw";
        const renderedText = String(row.rendered_verdict_body || "");
        const responseText = String(row.response_text || "");
        const shownText = isFinalVerdict && viewMode === "rendered" ? renderedText : responseText;
        return (
          <div
            key={id}
            className="rounded-lg border border-zinc-800/80 bg-zinc-950/60 p-2"
            onMouseEnter={() => onHoverFacts?.(facts)}
            onMouseLeave={() => onHoverFacts?.([])}
          >
            <div className="flex items-center justify-between gap-2">
              <p className="text-[11px] text-cyan-200/90">
                [{String(row.stage || "llm")}] {String(row.at || "no-ts")}
              </p>
              <div className="flex items-center gap-1">
                {isFinalVerdict ? (
                  <div className="mr-1 inline-flex rounded border border-violet-700/70 bg-violet-950/30 p-0.5 text-[10px]">
                    <button
                      type="button"
                      className={`rounded px-1.5 py-0.5 ${
                        viewMode === "raw" ? "bg-violet-700/40 text-violet-100" : "text-zinc-300 hover:bg-zinc-900"
                      }`}
                      onClick={() => setFinalViewMode((prev) => ({ ...prev, [id]: "raw" }))}
                    >
                      原始模型回复
                    </button>
                    <button
                      type="button"
                      className={`rounded px-1.5 py-0.5 ${
                        viewMode === "rendered"
                          ? "bg-violet-700/40 text-violet-100"
                          : "text-zinc-300 hover:bg-zinc-900"
                      }`}
                      onClick={() => setFinalViewMode((prev) => ({ ...prev, [id]: "rendered" }))}
                    >
                      最终渲染断言
                    </button>
                  </div>
                ) : null}
                <button
                  type="button"
                  className="rounded border border-zinc-700 px-2 py-0.5 text-[10px] text-zinc-300 hover:bg-zinc-900"
                  onClick={() => setOpenPromptId(promptOpen ? "" : id)}
                >
                  Prompt
                </button>
                <button
                  type="button"
                  className="rounded border border-zinc-700 px-2 py-0.5 text-[10px] text-zinc-300 hover:bg-zinc-900"
                  onClick={() => setOpenRespId(respOpen ? "" : id)}
                >
                  Full Response
                </button>
                <button
                  type="button"
                  className="rounded border border-zinc-700 px-2 py-0.5 text-[10px] text-zinc-300 hover:bg-zinc-900"
                  onClick={() => setOpenRawId(rawOpen ? "" : id)}
                >
                  Raw Trace
                </button>
              </div>
            </div>
            <p className="mt-1 text-[10px] text-violet-200/90">议题：{topicOf(row)}</p>
            <p className="mt-1 text-[10px] text-zinc-500">标题：{topicOf(row)}</p>
            <p className="mt-1 whitespace-pre-wrap text-[11px] text-zinc-300">
              <span className="text-emerald-300/90">
                {isFinalVerdict && viewMode === "rendered" ? "最终渲染断言：" : "LLM 返回："}
              </span>
              {isFinalVerdict && viewMode === "rendered"
                ? shownText || "（无 rendered_verdict_body）"
                : short(shownText, 220) || "（无 response_text）"}
            </p>
            {facts.length ? (
              <p className="mt-1 text-[10px] text-amber-200/85">Fact_ID: {facts.join(", ")}</p>
            ) : null}
            {respOpen ? (
              <div className="mt-2 space-y-2 rounded border border-emerald-900/40 bg-emerald-950/10 p-2">
                <p className="text-[10px] uppercase tracking-wide text-emerald-300/90">
                  {isFinalVerdict && viewMode === "rendered" ? "Rendered Verdict Body" : "Model Full Response"}
                </p>
                <pre className="max-h-[46dvh] overflow-auto whitespace-pre-wrap rounded border border-zinc-800/70 bg-black/30 p-2 font-mono text-[10px] text-zinc-200">
                  {shownText || "（空）"}
                </pre>
              </div>
            ) : null}
            {promptOpen ? (
              <div className="mt-2 space-y-2 rounded border border-cyan-900/40 bg-cyan-950/10 p-2">
                <p className="text-[10px] uppercase tracking-wide text-cyan-300/90">Prompt / Messages</p>
                {messages.length === 0 ? (
                  <p className="text-[10px] text-zinc-500">（该条无 messages）</p>
                ) : (
                  messages.map((m, idx) => (
                    <div key={`${id}-m-${idx}`} className="rounded border border-zinc-800/70 bg-black/30 p-2">
                      <p className="text-[10px] text-cyan-200/90">[{String(m.role || "unknown").toUpperCase()}]</p>
                      <pre className="mt-1 max-h-[24dvh] overflow-auto whitespace-pre-wrap font-mono text-[10px] text-zinc-300">
                        {String(m.content || "")}
                      </pre>
                    </div>
                  ))
                )}
              </div>
            ) : null}
            {rawOpen ? (
              <pre className="mt-2 max-h-[46dvh] overflow-auto rounded border border-zinc-800 bg-black/40 p-2 font-mono text-[10px] text-zinc-300">
                {safeJson({
                  messages,
                  llm_meta: row.llm_meta || {},
                  response_text: row.response_text || "",
                  rendered_verdict_body: row.rendered_verdict_body || "",
                })}
              </pre>
            ) : null}
          </div>
        );
      })}
    </div>
  );
}
