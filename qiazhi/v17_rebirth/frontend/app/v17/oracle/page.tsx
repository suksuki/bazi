"use client";

import { useEffect, useMemo, useState } from "react";
import { RotateCcw, Sparkles } from "lucide-react";

import { V17_DecisionInbox } from "@/components/V17_DecisionInbox";
import { V17_NatalInput } from "@/components/V17_NatalInput";
import { V17_PurpleVerdictCard } from "@/components/V17_PurpleVerdictCard";
import { V17_SixPillarsPanel } from "@/components/V17_SixPillarsPanel";
import { mergeV17LlmMetaForUi, shouldReleaseDecisionInboxLock, useV17WebStream } from "@/hooks/useV17WebStream";

export default function OraclePage() {
  const [sessionId, setSessionId] = useState("");
  const [running, setRunning] = useState(false);
  const [streamEndpoint, setStreamEndpoint] = useState<string | null>(
    "/api/v17/stream?will_proxy=stable&v17_origin=v17_rebirth",
  );
  const [streamBody, setStreamBody] = useState<Record<string, unknown> | null>(null);
  const [userMessage, setUserMessage] = useState("");
  const [adoptedDecisions, setAdoptedDecisions] = useState<Array<{ id: string; label: string }>>([]);
  const [freezing, setFreezing] = useState(false);
  const [freezeMsg, setFreezeMsg] = useState("");
  const [traceOpen, setTraceOpen] = useState(false);
  const [selectedLuckYear, setSelectedLuckYear] = useState<number>(new Date().getFullYear());
  const [birthTimeISO, setBirthTimeISO] = useState("");
  const [natalGender, setNatalGender] = useState<"male" | "female" | undefined>(undefined);
  const [natalCalendar, setNatalCalendar] = useState<"solar" | "lunar" | undefined>(undefined);
  const [connectTickMs, setConnectTickMs] = useState(0);
  const [decisionLockStartedAtMs, setDecisionLockStartedAtMs] = useState<number | null>(null);
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
  /** 仅「格局物理」快照含四柱/大运/流年；AUDIT_PREVIEW / llm_audit_preview 在后序出现，不能用「非 audit」误选。 */
  const physicsSnapshot = useMemo(
    () =>
      [...frames].reverse().find((f) => {
        if (String(f?.layer || "").toUpperCase() !== "SNAPSHOT") return false;
        const sk = String((f?.payload as { snapshot_kind?: string })?.snapshot_kind || "").trim();
        return sk === "physics" || sk === "physical_void" || sk === "system_init_failure";
      }),
    [frames],
  );
  const llmAuditSnapshot = useMemo(
    () =>
      [...frames].reverse().find((f) => {
        if (String(f?.layer || "").toUpperCase() !== "SNAPSHOT") return false;
        return String((f?.payload as { snapshot_kind?: string })?.snapshot_kind || "") === "llm_audit_preview";
      }),
    [frames],
  );
  const latestNarrator = useMemo(
    () => [...frames].reverse().find((f) => String(f?.layer || "").toUpperCase() === "NARRATOR"),
    [frames],
  );
  const narratorForAudit = useMemo(
    () =>
      [...frames].reverse().find((f) => {
        if (String(f?.layer || "").toUpperCase() !== "NARRATOR") return false;
        const p = f?.payload;
        if (!p) return false;
        const rt = String(p.render_text || "").trim();
        const m = (p.llm_meta || {}) as Record<string, unknown>;
        const sp = String(
          m.llm_system_prompt || (m.full_prompt_trace as { system_role?: string } | undefined)?.system_role || "",
        ).trim();
        const unlock = m.prompt_dead_audit_unlock === true;
        return rt.length > 0 || sp.length > 0 || unlock;
      }) ||
      [...frames].reverse().find((f) => {
        if (String(f?.layer || "").toUpperCase() !== "SNAPSHOT") return false;
        return String((f?.payload as { snapshot_kind?: string })?.snapshot_kind || "") === "llm_audit_preview";
      }),
    [frames],
  );
  const traceHits = physicsSnapshot?.payload?.debug_trace?.hits || [];
  const traceFacts = (latestNarrator?.payload?.source_facts || physicsSnapshot?.payload?.debug_trace?.facts || []).slice(
    0,
    32,
  );
  const llmMeta = mergeV17LlmMetaForUi(narratorForAudit, latestNarrator, llmAuditSnapshot) as Record<
    string,
    unknown
  >;
  const narratorHasChunk = Boolean(String(latestNarrator?.payload?.render_text || "").trim());
  const streamPartial = llmMeta.stream_partial === true;
  const hasFinalLlmMeta =
    !streamPartial && typeof llmMeta.elapsed_ms === "number" && !Number.isNaN(Number(llmMeta.elapsed_ms));
  const llmTerminal = hasFinalLlmMeta || llmMeta.ok === false;
  const modelLabel = String(llmMeta.model || "").trim() || "叙事引擎";
  const connectPhase = running && !narratorHasChunk;
  const collapsePhase = running && narratorHasChunk && !hasFinalLlmMeta;
  const fullTrace = llmMeta.full_prompt_trace as Record<string, unknown> | undefined;
  const latestFrameTimestamp = useMemo(
    () => [...frames].reverse().find((f) => String(f?.timestamp || "").trim().length > 0)?.timestamp,
    [frames],
  );
  const initialVerdictLocked = running && frames.length > 0 && decisionLockStartedAtMs == null && !llmTerminal;
  const decisionInboxLocked = initialVerdictLocked || decisionLockStartedAtMs != null;
  const decisionInboxLockMessage = decisionLockStartedAtMs != null
    ? "上一条决策仍在织造中，待 LLM 完成后才可选择新的 item。"
    : initialVerdictLocked
      ? "首轮判词仍在织造中，待 LLM 完成后才可选择 decision item。"
      : "";

  useEffect(() => {
    if (
      shouldReleaseDecisionInboxLock({
        lockStartedAtMs: decisionLockStartedAtMs,
        latestFrameTimestamp,
        hasFinalLlmMeta,
        llmOk: llmMeta.ok as boolean | undefined,
      })
    ) {
      setDecisionLockStartedAtMs(null);
    }
  }, [decisionLockStartedAtMs, latestFrameTimestamp, hasFinalLlmMeta, llmMeta.ok]);

  useEffect(() => {
    if (!running) {
      setConnectTickMs(0);
      return;
    }
    const t0 = Date.now();
    const id = window.setInterval(() => setConnectTickMs(Date.now() - t0), 80);
    return () => window.clearInterval(id);
  }, [running, streamEndpoint]);

  const streamQuery = useMemo(() => {
    const u = streamEndpoint || "";
    try {
      const q = u.includes("?") ? new URLSearchParams(u.split("?")[1] || "") : new URLSearchParams();
      return {
        will_proxy: q.get("will_proxy") || "",
        birth_time: q.get("birth_time") || "",
        gender: q.get("gender") || "",
        flow_year: q.get("flow_year") || "",
      };
    } catch {
      return { will_proxy: "", birth_time: "", gender: "", flow_year: "" };
    }
  }, [streamEndpoint]);
  const fourPillars = physicsSnapshot?.payload?.four_pillars;
  const luckPillarSnap = physicsSnapshot?.payload?.luck_pillar;
  const flowPillarSnap = physicsSnapshot?.payload?.flow_pillar;

  function startRun(input: { birthTimeISO: string; gender: "male" | "female"; calendarType: "solar" | "lunar" }) {
    const fy = new Date().getFullYear();
    const query = new URLSearchParams({
      will_proxy: "stable",
      birth_time: input.birthTimeISO,
      gender: input.gender,
      flow_year: String(fy),
      v17_origin: "v17_rebirth",
    });
    setStreamEndpoint(`/api/v17/stream?${query.toString()}`);
    const sid = crypto.randomUUID();
    setSessionId(sid);
    setBirthTimeISO(input.birthTimeISO);
    setNatalGender(input.gender);
    setNatalCalendar(input.calendarType);
    setSelectedLuckYear(fy);
    setStreamBody({
      v17_origin: "v17_rebirth",
      calendar_type: input.calendarType,
      session_id: sid,
    });
    setDecisionLockStartedAtMs(null);
    setAdoptedDecisions([]);
    setFreezeMsg("");
    setRunning(true);
  }

  function resetRun() {
    setRunning(false);
    setStreamBody(null);
    setUserMessage("");
    setAdoptedDecisions([]);
    setDecisionLockStartedAtMs(null);
    setFreezeMsg("");
  }

  useEffect(() => {
    if (!running || !birthTimeISO || !natalGender) return;
    const u = streamEndpoint ?? "";
    const m = u.match(/[?&]flow_year=(\d+)/);
    if (m && Number(m[1]) === selectedLuckYear) return;
    const query = new URLSearchParams({
      will_proxy: "stable",
      birth_time: birthTimeISO,
      gender: natalGender,
      flow_year: String(selectedLuckYear),
      v17_origin: "v17_rebirth",
    });
    setStreamEndpoint(`/api/v17/stream?${query.toString()}`);
  }, [selectedLuckYear, running, birthTimeISO, natalGender, streamEndpoint]);

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
    const base =
      streamEndpoint?.split("&_pulse=")[0] || "/api/v17/stream?will_proxy=stable&v17_origin=v17_rebirth";
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
    if (!label || decisionLockStartedAtMs != null) return;
    setDecisionLockStartedAtMs(Date.now());
    setAdoptedDecisions((prev) => {
      if (prev.some((x) => x.id === id)) return prev;
      const next = [...prev, { id, label }];
      const base =
        streamEndpoint?.split("&_pulse=")[0] || "/api/v17/stream?will_proxy=stable&v17_origin=v17_rebirth";
      setStreamEndpoint(`${base}&_pulse=${Date.now()}`);
      setStreamBody((prevBody) => ({
        ...(prevBody || {}),
        v17_origin: "v17_rebirth",
        session_id: sessionId || "default",
        user_message: label,
        decisions: next,
      }));
      return next;
    });
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
        headers: { "Content-Type": "application/json", v17_origin: "v17_rebirth" },
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
                luckPillarFromServer={typeof luckPillarSnap === "string" ? luckPillarSnap : undefined}
                flowPillarFromServer={typeof flowPillarSnap === "string" ? flowPillarSnap : undefined}
                birthTimeISO={birthTimeISO}
                gender={natalGender}
                calendarType={natalCalendar}
                selectedYear={selectedLuckYear}
                onYearChange={setSelectedLuckYear}
              />
              <V17_PurpleVerdictCard
                frames={frames}
                onToggleTrace={() => setTraceOpen((v) => !v)}
                connectTickMs={connectTickMs}
                running={running}
              />
              <V17_DecisionInbox
                frames={frames}
                adoptedIds={adoptedDecisions.map((x) => x.id)}
                sessionId={sessionId}
                locked={decisionInboxLocked}
                lockMessage={decisionInboxLockMessage}
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
                  <p>
                    模型：
                    {connectPhase
                      ? `${modelLabel}（连接中）`
                      : String(llmMeta.model || llmMeta.llm_endpoint_host || "叙事引擎")}
                  </p>
                  <p>
                    耗时：
                    {connectPhase
                      ? `正在连接 ${modelLabel}… (${connectTickMs} ms)`
                      : collapsePhase
                        ? "计时中…"
                        : `${Number(llmMeta.elapsed_ms || 0)} ms`}
                  </p>
                  <p>
                    状态：
                    {connectPhase
                      ? `正在连接 ${modelLabel}…`
                      : collapsePhase
                        ? "意志坍缩中…"
                        : String(llmMeta.engine_state || (llmMeta.ok ? "ok" : "就绪"))}
                  </p>
                  {llmMeta.http_timeout_sec != null ? <p>HTTP 超时：{String(llmMeta.http_timeout_sec)} s</p> : null}
                  {llmMeta.fuse_wait_timeout_sec != null ? <p>Fuse 等待：{String(llmMeta.fuse_wait_timeout_sec)} s</p> : null}
                  {llmMeta.error ? <p className="text-rose-300/90">错误：{String(llmMeta.error)}</p> : null}
                </div>
                <div className="mt-3 space-y-2 border-t border-cyan-500/20 pt-3">
                  <p className="text-[11px] text-cyan-300">初始请求参数</p>
                  <pre className="max-h-40 overflow-auto whitespace-pre-wrap break-words rounded-md border border-cyan-500/20 bg-zinc-950/80 p-2 font-mono text-[10px] text-zinc-300">
                    {JSON.stringify(
                      {
                        birth_time: streamQuery.birth_time || birthTimeISO || null,
                        gender: streamQuery.gender || natalGender || null,
                        calendar_type: natalCalendar || (streamBody as { calendar_type?: string } | null)?.calendar_type || null,
                        flow_year: streamQuery.flow_year || String(selectedLuckYear),
                        will_proxy: streamQuery.will_proxy || null,
                        stream_endpoint: streamEndpoint,
                        session_id: (streamBody as { session_id?: string } | null)?.session_id || null,
                      },
                      null,
                      2,
                    )}
                  </pre>
                </div>
                <div className="mt-3 space-y-2 border-t border-cyan-500/20 pt-3">
                  {fullTrace ? (
                    <p className="text-[10px] text-amber-200/90">
                      full_prompt_trace：decision_anchor 位于 System Role —{" "}
                      {fullTrace.decision_anchor_literal_in_system_role ? "已验证" : "未命中（锚点为空或未写入 System）"}
                      {typeof fullTrace.decision_anchor_len === "number"
                        ? `（锚点长度 ${String(fullTrace.decision_anchor_len)}）`
                        : ""}
                    </p>
                  ) : collapsePhase || connectPhase ? (
                    <p className="text-[10px] text-zinc-500">
                      {llmAuditSnapshot
                        ? "full_prompt_trace：已由 SNAPSHOT（llm_audit_preview）在 fuse 前下发…"
                        : "full_prompt_trace：终帧到达后解锁审计字段…"}
                    </p>
                  ) : null}
                  <p className="text-[11px] text-cyan-300">LLM 系统提示词</p>
                  <pre className="max-h-32 overflow-auto whitespace-pre-wrap break-words rounded-md border border-cyan-500/20 bg-zinc-950/80 p-2 font-mono text-[10px] text-zinc-300">
                    {String(
                      fullTrace?.system_role ?? llmMeta.llm_system_prompt ?? "（本期帧未携带，可能为缓存帧或非 LLM 路径）",
                    )}
                  </pre>
                  <p className="text-[11px] text-cyan-300">LLM 用户提示词</p>
                  <pre className="max-h-40 overflow-auto whitespace-pre-wrap break-words rounded-md border border-cyan-500/20 bg-zinc-950/80 p-2 font-mono text-[10px] text-zinc-300">
                    {String(fullTrace?.user_role ?? llmMeta.llm_user_prompt ?? "（同上）")}
                  </pre>
                  {Array.isArray(llmMeta.llm_request_messages) ? (
                    <details className="text-[11px] text-zinc-400">
                      <summary className="cursor-pointer text-cyan-300/90">完整 messages JSON</summary>
                      <pre className="mt-1 max-h-36 overflow-auto whitespace-pre-wrap break-words rounded-md border border-zinc-700 bg-zinc-950/80 p-2 font-mono text-[10px] text-zinc-400">
                        {JSON.stringify(llmMeta.llm_request_messages, null, 2)}
                      </pre>
                    </details>
                  ) : null}
                  <p className="text-[11px] text-cyan-300">LLM 返回（模型正文，未经 Sanitizer）</p>
                  <pre className="max-h-40 overflow-auto whitespace-pre-wrap break-words rounded-md border border-cyan-500/20 bg-zinc-950/80 p-2 font-mono text-[10px] text-zinc-300">
                    {(() => {
                      const raw = String(llmMeta.llm_reply ?? "").trim();
                      if (raw) return raw;
                      if (llmMeta.ok === false) return "（LLM 调用失败，无模型正文；界面判词可能为降级拼接）";
                      return String(latestNarrator?.payload?.render_text || "").trim() || "（空）";
                    })()}
                  </pre>
                  <p className="text-[11px] text-cyan-300">上游原始 JSON / SSE（截断）</p>
                  <pre className="max-h-32 overflow-auto whitespace-pre-wrap break-words rounded-md border border-cyan-500/20 bg-zinc-950/80 p-2 font-mono text-[9px] text-zinc-400">
                    {String(llmMeta.llm_raw_response_json || "").trim() || "（无）"}
                  </pre>
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
                <div className="mt-3 space-y-2 border-t border-cyan-500/20 pt-3">
                  <details className="text-[11px] text-zinc-300">
                    <summary className="cursor-pointer text-cyan-300/90">[查看完整提示词 (Prompt)]</summary>
                    <p className="mt-1 text-[10px] text-cyan-400/80">System</p>
                    <pre className="mt-0.5 max-h-36 overflow-auto whitespace-pre-wrap break-words rounded-md border border-zinc-700 bg-zinc-950/80 p-2 font-mono text-[10px] text-zinc-300">
                      {String(
                        fullTrace?.system_role ?? llmMeta.llm_system_prompt ?? "（等待终帧 llm_meta）",
                      )}
                    </pre>
                    <p className="mt-2 text-[10px] text-cyan-400/80">User</p>
                    <pre className="mt-0.5 max-h-36 overflow-auto whitespace-pre-wrap break-words rounded-md border border-zinc-700 bg-zinc-950/80 p-2 font-mono text-[10px] text-zinc-300">
                      {String(fullTrace?.user_role ?? llmMeta.llm_user_prompt ?? "（等待终帧 llm_meta）")}
                    </pre>
                  </details>
                  <details className="text-[11px] text-zinc-300">
                    <summary className="cursor-pointer text-cyan-300/90">[查看原始回复 (Raw)]</summary>
                    <p className="mt-1 text-[10px] text-zinc-500">模型正文（未经 Sanitizer）</p>
                    <pre className="mt-0.5 max-h-28 overflow-auto whitespace-pre-wrap break-words rounded-md border border-zinc-700 bg-zinc-950/80 p-2 font-mono text-[10px] text-zinc-300">
                      {String(llmMeta.llm_reply || "").trim() || "（空）"}
                    </pre>
                    <p className="mt-2 text-[10px] text-zinc-500">上游 JSON / SSE</p>
                    <pre className="mt-0.5 max-h-28 overflow-auto whitespace-pre-wrap break-words rounded-md border border-zinc-700 bg-zinc-950/80 p-2 font-mono text-[9px] text-zinc-400">
                      {String(llmMeta.llm_raw_response_json || "").trim() || "（无）"}
                    </pre>
                  </details>
                </div>
              </aside>
            ) : null}
          </div>
        ) : null}
      </section>
    </main>
  );
}
