"use client";

import { useMemo, useState } from "react";
import { RotateCcw, Sparkles } from "lucide-react";

import { V17_DecisionInbox } from "@/components/V17_DecisionInbox";
import { V17_NatalInput } from "@/components/V17_NatalInput";
import { V17_PurpleVerdictCard } from "@/components/V17_PurpleVerdictCard";
import { V17_SixPillarsPanel } from "@/components/V17_SixPillarsPanel";
import { useV17WebStream } from "@/hooks/useV17WebStream";

export default function OraclePage() {
  const [sessionId, setSessionId] = useState("");
  const [running, setRunning] = useState(false);
  const [streamEndpoint, setStreamEndpoint] = useState<string | null>("/api/v17/stream?will_proxy=stable");
  const [streamBody, setStreamBody] = useState<Record<string, unknown> | null>(null);
  const [userMessage, setUserMessage] = useState("");
  const [adoptedDecisions, setAdoptedDecisions] = useState<Array<{ id: string; label: string }>>([]);
  const [freezing, setFreezing] = useState(false);
  const [freezeMsg, setFreezeMsg] = useState("");
  const [traceOpen, setTraceOpen] = useState(false);
  const [selectedLuckYear, setSelectedLuckYear] = useState<number>(new Date().getFullYear());
  const [birthTimeISO, setBirthTimeISO] = useState("");
  const { frames } = useV17WebStream({
    endpoint: streamEndpoint,
    enabled: running,
    method: "POST",
    body: streamBody,
  });

  const hasNarrative = useMemo(
    () => frames.some((f) => String(f?.payload?.render_text || "").trim().length > 0),
    [frames],
  );
  const latestRenderText = useMemo(
    () =>
      String(
        [...frames].reverse().find((f) => String(f?.payload?.render_text || "").trim().length > 0)?.payload?.render_text || "",
      ).trim(),
    [frames],
  );
  const latestSnapshot = useMemo(
    () => [...frames].reverse().find((f) => String(f?.layer || "").toUpperCase() === "SNAPSHOT"),
    [frames],
  );
  const latestNarrator = useMemo(
    () => [...frames].reverse().find((f) => String(f?.layer || "").toUpperCase() === "NARRATOR"),
    [frames],
  );
  const traceHits = latestSnapshot?.payload?.debug_trace?.hits || [];
  const traceFacts = (latestNarrator?.payload?.source_facts || latestSnapshot?.payload?.debug_trace?.facts || []).slice(0, 8);
  const llmMeta = latestNarrator?.payload?.llm_meta || {};
  const fourPillars = latestSnapshot?.payload?.four_pillars;

  function startRun(input: { birthTimeISO: string; gender: "male" | "female"; calendarType: "solar" | "lunar" }) {
    const query = new URLSearchParams({
      will_proxy: "stable",
      birth_time: input.birthTimeISO,
      gender: input.gender,
    });
    setStreamEndpoint(`/api/v17/stream?${query.toString()}`);
    const sid = crypto.randomUUID();
    setSessionId(sid);
    setBirthTimeISO(input.birthTimeISO);
    setSelectedLuckYear(new Date().getFullYear());
    setStreamBody({
      v17_origin: "v17_rebirth",
      calendar_type: input.calendarType,
      session_id: sid,
    });
    setAdoptedDecisions([]);
    setFreezeMsg("");
    setRunning(true);
  }

  function resetRun() {
    setRunning(false);
    setStreamBody(null);
    setUserMessage("");
    setAdoptedDecisions([]);
    setFreezeMsg("");
  }

  async function injectConversation() {
    const msg = userMessage.trim();
    if (!msg) return;
    const t0 = Date.now();
    await fetch("/api/v17/action", {
      method: "POST",
      headers: { "Content-Type": "application/json", v17_origin: "v17_rebirth" },
      body: JSON.stringify({
        signal: "INJECT_PATCH",
        action: msg,
        session_id: sessionId || "default",
        v17_origin: "v17_rebirth",
      }),
    }).catch(() => undefined);
    const base = streamEndpoint?.split("&_pulse=")[0] || "/api/v17/stream?will_proxy=stable";
    setStreamEndpoint(`${base}&_pulse=${Date.now()}`);
    setStreamBody((prev) => ({ ...(prev || {}), user_message: msg }));
    if (Date.now() - t0 > 100) {
      // Best-effort notice: network/runtime may exceed 100ms.
      setFreezeMsg("注入已触发，正在强制刷新叙事流。");
    }
    setUserMessage("");
  }

  function handleAdopted(decision: { id?: string; label?: string; title?: string }) {
    const id = String(decision.id || decision.title || `d_${Date.now()}`);
    const label = String(decision.label || decision.title || "").trim();
    if (!label) return;
    setAdoptedDecisions((prev) => (prev.some((x) => x.id === id) ? prev : [...prev, { id, label }]));
    const base = streamEndpoint?.split("&_pulse=")[0] || "/api/v17/stream?will_proxy=stable";
    setStreamEndpoint(`${base}&_pulse=${Date.now()}`);
    setStreamBody((prev) => ({
      ...(prev || {}),
      session_id: sessionId || "default",
      user_message: label,
    }));
  }

  async function freezeCausalReport() {
    if (!latestRenderText) {
      setFreezeMsg("当前尚无可定格判词。");
      return;
    }
    setFreezing(true);
    try {
      const resp = await fetch("/api/v17/freeze-report", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          v17_origin: "v17_rebirth",
          render_text: latestRenderText,
          decisions: adoptedDecisions,
        }),
      });
      const data = await resp.json().catch(() => ({}));
      setFreezeMsg(resp.ok ? `已定格：${String(data.report_id || "")}` : `定格失败：${String(data.detail || "unknown")}`);
    } finally {
      setFreezing(false);
    }
  }

  return (
    <main className="min-h-screen bg-zinc-950 p-6 text-zinc-100">
      <section className="mx-auto flex w-full max-w-4xl flex-col gap-4">
        <header className="flex items-center justify-between gap-2 text-violet-300">
          <div className="flex items-center gap-2">
            <Sparkles className="h-5 w-5" />
            <h1 className="text-lg font-semibold tracking-wide">V17 Oracle Temple</h1>
          </div>
          {running ? (
            <button
              type="button"
              onClick={resetRun}
              className="inline-flex items-center gap-1 rounded-md border border-violet-300/40 bg-violet-900/20 px-2 py-1 text-xs text-violet-100 hover:bg-violet-800/30"
            >
              <RotateCcw className="h-3.5 w-3.5" />
              重测
            </button>
          ) : null}
        </header>

        <div className="relative">
          {running ? (
            <div className="absolute inset-0 z-20 animate-[fadeOut_280ms_ease-out_forwards] rounded-2xl bg-black/50 backdrop-blur-[1px]" />
          ) : null}
          {!running ? <V17_NatalInput onStart={startRun} /> : null}
        </div>

        {running ? (
          <div className="grid min-h-[60vh] gap-3 md:grid-cols-[1fr_280px]">
            <div className="w-full space-y-3">
              <V17_SixPillarsPanel
                fourPillars={fourPillars}
                birthTimeISO={birthTimeISO}
                selectedYear={selectedLuckYear}
                onYearChange={setSelectedLuckYear}
              />
              <V17_PurpleVerdictCard frames={frames} onToggleTrace={() => setTraceOpen((v) => !v)} />
              <V17_DecisionInbox
                frames={frames}
                adoptedIds={adoptedDecisions.map((x) => x.id)}
                sessionId={sessionId}
                onAdopted={handleAdopted}
              />
              {!hasNarrative ? (
                <p className="mt-3 text-xs text-violet-200/80">V17 织造启动中，正在同步快照与叙事流...</p>
              ) : null}
            </div>
            <aside className="h-fit rounded-xl border border-violet-600/30 bg-zinc-900/70 p-3">
              <p className="mb-2 text-xs text-violet-200/80">意志注入补丁</p>
              <textarea
                value={userMessage}
                onChange={(e) => setUserMessage(e.target.value)}
                placeholder="输入一条意志补丁，影响后续判词色调"
                className="min-h-[100px] w-full rounded-md border border-violet-500/30 bg-zinc-900 px-3 py-2 text-sm text-zinc-100"
              />
              <button
                type="button"
                onClick={injectConversation}
                className="mt-2 w-full rounded-md border border-violet-400/40 bg-violet-900/30 px-3 py-2 text-xs text-violet-100 hover:bg-violet-800/40"
              >
                注入
              </button>
              <button
                type="button"
                onClick={freezeCausalReport}
                disabled={freezing}
                className="mt-2 w-full rounded-md border border-emerald-400/40 bg-emerald-900/20 px-3 py-2 text-xs text-emerald-100 hover:bg-emerald-800/30 disabled:opacity-60"
              >
                {freezing ? "定格中..." : "定格"}
              </button>
              {freezeMsg ? <p className="mt-2 text-[11px] text-emerald-200/90">{freezeMsg}</p> : null}
            </aside>
            {traceOpen ? (
              <aside className="h-fit rounded-xl border border-cyan-500/40 bg-zinc-900/85 p-3">
                <p className="mb-2 text-xs text-cyan-200">因果链路面板</p>
                <div className="space-y-1 text-[11px] text-zinc-200">
                  <p>模型：{String(llmMeta.model || "unknown")}</p>
                  <p>耗时：{Number(llmMeta.elapsed_ms || 0)} ms</p>
                  <p>状态：{String(llmMeta.engine_state || (llmMeta.ok ? "ok" : "unknown"))}</p>
                </div>
                <div className="mt-3">
                  <p className="text-[11px] text-cyan-300">命中插件</p>
                  <p className="mt-1 text-[11px] text-zinc-200">{traceHits.length ? traceHits.join(" / ") : "暂无命中"}</p>
                </div>
                <div className="mt-3">
                  <p className="text-[11px] text-cyan-300">织造 Fact</p>
                  <div className="mt-1 space-y-1">
                    {traceFacts.length ? (
                      traceFacts.map((x, idx) => (
                        <p key={`${idx}_${x}`} className="text-[11px] text-zinc-200">
                          {idx + 1}. {String(x)}
                        </p>
                      ))
                    ) : (
                      <p className="text-[11px] text-zinc-500">暂无 Fact</p>
                    )}
                  </div>
                </div>
              </aside>
            ) : null}
          </div>
        ) : null}
      </section>
    </main>
  );
}
