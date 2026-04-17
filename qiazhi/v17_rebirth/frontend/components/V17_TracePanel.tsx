"use client";

/**
 * V17.23 — V17_TracePanel
 *
 * 因果链路调试面板（原 OraclePage 第 365–505 行）。
 * Props 由 useOracleSession 直接传入，完全无状态。
 */

interface TracePanelProps {
  collapsed: boolean;
  onToggle: () => void;
  llmMeta: Record<string, unknown>;
  connectPhase: boolean;
  collapsePhase: boolean;
  modelLabel: string;
  connectTickMs: number;
  fullTrace: Record<string, unknown> | undefined;
  llmAuditSnapshot: unknown;
  latestNarrator: { payload?: Record<string, unknown> } | undefined;
  traceHits: unknown[];
  traceFacts: unknown[];
  birthTimeISO: string;
  natalGender: string | undefined;
  natalCalendar: string | undefined;
  selectedLuckYear: number;
  streamEndpoint: string | null;
  streamBody: Record<string, unknown> | null;
  streamQuery: { will_proxy: string; birth_time: string; gender: string; flow_year: string };
  physicsSnapshot?: {
    payload?: {
      causal_anchor?: unknown;
      physics_fingerprint?: unknown;
      deity_scores?: Record<string, number>;
      ten_gods_absolute_intensity?: Record<string, number>;
      total_energy_index?: number;
      ten_gods?: unknown[];
      pattern?: string;
      physics_tension?: number;
      four_pillars?: Record<string, unknown>;
      luck_pillar?: unknown;
      flow_pillar?: unknown;
      flow_year?: unknown;
      plugins?: {
        hits?: unknown[];
        rows?: Array<Record<string, unknown>>;
      };
      debug_trace?: {
        facts?: unknown[];
      };
    };
  };
}

export function V17_TracePanel({
  collapsed,
  onToggle,
  llmMeta,
  connectPhase,
  collapsePhase,
  modelLabel,
  connectTickMs,
  fullTrace,
  llmAuditSnapshot,
  latestNarrator,
  traceHits,
  traceFacts,
  birthTimeISO,
  natalGender,
  natalCalendar,
  selectedLuckYear,
  streamEndpoint,
  streamBody,
  streamQuery,
  physicsSnapshot,
}: TracePanelProps) {
  const physicsPayload = (physicsSnapshot?.payload ?? {}) as Record<string, unknown>;
  const auditPayload =
    llmAuditSnapshot && typeof llmAuditSnapshot === "object"
      ? (((llmAuditSnapshot as { payload?: Record<string, unknown> }).payload ?? {}) as Record<string, unknown>)
      : {};
  const scoreMap =
    physicsSnapshot?.payload?.ten_gods_absolute_intensity || physicsSnapshot?.payload?.deity_scores || {};
  const deityScores = Object.entries(scoreMap)
    .map(([name, score]) => ({ name: String(name), score: Number(score || 0) }))
    .filter((row) => row.name && Number.isFinite(row.score))
    .sort((a, b) => b.score - a.score);
  const maxDeityScore = deityScores.length ? Math.max(...deityScores.map((row) => row.score), 1) : 1;
  const tenGods = Array.isArray(physicsSnapshot?.payload?.ten_gods)
    ? physicsSnapshot?.payload?.ten_gods.map((x) => String(x || "").trim()).filter(Boolean)
    : [];
  const pillars = physicsSnapshot?.payload?.four_pillars || {};
  const pillarText = ["year", "month", "day", "hour"]
    .map((k) => String((pillars as Record<string, unknown>)[k] || "").trim())
    .filter(Boolean)
    .join(" / ");
  const pluginRows = Array.isArray((physicsPayload.plugins as { rows?: unknown[] } | undefined)?.rows)
    ? (((physicsPayload.plugins as { rows?: unknown[] }).rows ?? []) as Array<Record<string, unknown>>)
    : [];
  const groupedPlugins = pluginRows.reduce<Record<string, string[]>>((acc, row) => {
    const plugin = String(row.plugin || row.source || "unknown").trim() || "unknown";
    const fact = String(row.fact || row.label || row.title || "").trim();
    if (!fact) return acc;
    acc[plugin] = [...(acc[plugin] || []), fact];
    return acc;
  }, {});
  const causalPhysicsAnchor = String(physicsPayload.causal_anchor || "—");
  const causalAuditAnchor = String(auditPayload.causal_anchor || "—");
  const causalPhysicsFp = String(physicsPayload.physics_fingerprint || "—");
  const causalAuditFp = String(
    auditPayload.physics_fingerprint ||
      (fullTrace?.physics_fingerprint as string | undefined) ||
      (llmMeta.physics_fingerprint as string | undefined) ||
      "—",
  );
  const causalAligned =
    causalPhysicsAnchor !== "—" &&
    causalAuditAnchor !== "—" &&
    causalPhysicsFp !== "—" &&
    causalAuditFp !== "—" &&
    causalPhysicsAnchor !== "" &&
    causalAuditAnchor !== "" &&
    causalPhysicsFp === causalAuditFp;
  const timelineItems = [
    {
      label: "SNAPSHOT",
      state: pillarText ? "已显影" : "未显影",
      meta: `${causalPhysicsAnchor} · ${causalPhysicsFp}`,
    },
    {
      label: "AUDIT_PREVIEW",
      state: Object.keys(auditPayload).length > 0 ? "已派发" : "未到达",
      meta: `${causalAuditAnchor} · ${causalAuditFp}`,
    },
    {
      label: "LLM",
      state: connectPhase
        ? "连接中"
        : collapsePhase
          ? "流式生成中"
          : String(llmMeta.engine_state || (llmMeta.ok ? "ok" : "待命")),
      meta: `${String(llmMeta.model || llmMeta.llm_endpoint_host || "叙事引擎")}`,
    },
    {
      label: "TERMINAL",
      state: llmMeta.ok === false ? "失败/降级" : llmMeta.elapsed_ms != null ? "完成" : "未终结",
      meta:
        llmMeta.error != null && String(llmMeta.error).trim()
          ? String(llmMeta.error)
          : `${Number(llmMeta.elapsed_ms || 0)} ms`,
    },
  ];

  if (collapsed) {
    return (
      <aside className="sticky top-6 flex h-fit min-h-[28rem] w-14 flex-col items-center rounded-2xl border border-cyan-500/25 bg-zinc-900/70 py-3 shadow-[0_18px_60px_rgba(8,145,178,0.12)]">
        <button
          type="button"
          onClick={onToggle}
          className="rounded-full border border-cyan-400/35 bg-cyan-950/55 px-3 py-2 text-[10px] tracking-[0.35em] text-cyan-200 transition hover:bg-cyan-900/70"
          title="展开调试边栏"
        >
          DEBUG
        </button>
        <div className="mt-4 flex flex-1 items-center">
          <span className="[writing-mode:vertical-rl] text-[10px] tracking-[0.4em] text-zinc-500">
            元数据 / 链路
          </span>
        </div>
      </aside>
    );
  }

  return (
    <aside className="sticky top-6 h-fit rounded-2xl border border-cyan-500/40 bg-[linear-gradient(180deg,rgba(10,18,24,0.96),rgba(9,14,19,0.88))] p-3 shadow-[0_22px_70px_rgba(8,145,178,0.16)]">
      <div className="mb-3 flex items-center justify-between gap-2">
        <div>
          <p className="text-xs tracking-[0.28em] text-cyan-200">DEBUG SIDEBAR</p>
          <p className="mt-1 text-[11px] text-zinc-500">元数据 / 因果链路 / LLM 调试</p>
        </div>
        <button
          type="button"
          onClick={onToggle}
          className="rounded-full border border-cyan-400/35 bg-cyan-950/50 px-3 py-1 text-[10px] text-cyan-200 transition hover:bg-cyan-900/70"
        >
          收起
        </button>
      </div>

      <div className="space-y-2 rounded-xl border border-cyan-500/20 bg-zinc-950/70 p-3">
        <p className="text-[11px] text-cyan-300">八字元数据</p>
        <div className="space-y-1 text-[11px] text-zinc-200">
          <p>格局：{String(physicsSnapshot?.payload?.pattern || "—")}</p>
          <p>张力：{Number(physicsSnapshot?.payload?.physics_tension || 0).toFixed(2)}</p>
          <p>六柱：{pillarText || "—"}</p>
          <p>
            运势：
            {String(physicsSnapshot?.payload?.luck_pillar || "—")} / {String(physicsSnapshot?.payload?.flow_pillar || "—")}
          </p>
          <p>流年锚年：{String(physicsSnapshot?.payload?.flow_year || "—")}</p>
          <p>十神主轴：{tenGods.length ? tenGods.join(" / ") : "—"}</p>
          <p>总能量指数：{Number(physicsSnapshot?.payload?.total_energy_index || 0).toFixed(2)}</p>
        </div>
        <div className="mt-2 space-y-1">
          <p className="text-[10px] uppercase tracking-[0.24em] text-zinc-500">Absolute Intensity</p>
          {deityScores.length ? (
            <div className="space-y-1">
              {deityScores.map((row) => (
                <div key={row.name} className="rounded-lg border border-cyan-500/15 bg-zinc-900/80 px-2 py-1.5">
                  <div className="mb-1 flex items-center justify-between text-[11px] text-zinc-200">
                    <span>{row.name}</span>
                    <span className="font-mono text-cyan-200">{row.score.toFixed(2)}</span>
                  </div>
                  <div className="h-1.5 overflow-hidden rounded-full bg-zinc-800">
                    <div
                      className="h-full rounded-full bg-[linear-gradient(90deg,rgba(34,211,238,0.65),rgba(103,232,249,0.95))]"
                      style={{ width: `${Math.max(4, Math.min(100, (row.score / maxDeityScore) * 100))}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-[11px] text-zinc-500">暂无十神数值</p>
          )}
        </div>
      </div>

      <div className="mt-3 space-y-2 rounded-xl border border-cyan-500/20 bg-zinc-950/70 p-3">
        <div className="flex items-center justify-between">
          <p className="text-[11px] text-cyan-300">因果锚点</p>
          <span
            className={`rounded-full px-2 py-0.5 text-[10px] ${
              causalAligned ? "bg-emerald-950/80 text-emerald-200" : "bg-amber-950/80 text-amber-200"
            }`}
          >
            {causalAligned ? "已对齐" : "待核对"}
          </span>
        </div>
        <div className="space-y-1 text-[11px] text-zinc-200">
          <p>物理快照：{causalPhysicsAnchor}</p>
          <p className="font-mono text-[10px] text-cyan-200/90 break-all">fp={causalPhysicsFp}</p>
          <p>审计快照：{causalAuditAnchor}</p>
          <p className="font-mono text-[10px] text-cyan-200/90 break-all">fp={causalAuditFp}</p>
        </div>
      </div>

      <div className="mt-3 space-y-2 rounded-xl border border-cyan-500/20 bg-zinc-950/70 p-3">
        <p className="text-[11px] text-cyan-300">LLM 链路时间线</p>
        <div className="space-y-2">
          {timelineItems.map((item) => (
            <div key={item.label} className="rounded-lg border border-cyan-500/10 bg-zinc-900/70 px-2 py-2">
              <div className="flex items-center justify-between gap-2">
                <span className="text-[10px] tracking-[0.24em] text-cyan-200">{item.label}</span>
                <span className="text-[11px] text-zinc-100">{item.state}</span>
              </div>
              <p className="mt-1 break-all text-[10px] text-zinc-500">{item.meta}</p>
            </div>
          ))}
        </div>
      </div>

      {/* ── LLM 状态概览 ── */}
      <div className="mt-3 space-y-1 text-[11px] text-zinc-200 rounded-xl border border-cyan-500/20 bg-zinc-950/70 p-3">
        <p className="text-[11px] text-cyan-300">LLM 状态概览</p>
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
        {llmMeta.http_timeout_sec != null ? (
          <p>HTTP 超时：{String(llmMeta.http_timeout_sec)} s</p>
        ) : null}
        {llmMeta.fuse_wait_timeout_sec != null ? (
          <p>Fuse 等待：{String(llmMeta.fuse_wait_timeout_sec)} s</p>
        ) : null}
        {llmMeta.error ? <p className="text-rose-300/90">错误：{String(llmMeta.error)}</p> : null}
      </div>

      {/* ── 初始请求参数 ── */}
      <div className="mt-3 space-y-2 rounded-xl border border-cyan-500/20 bg-zinc-950/70 p-3">
        <p className="text-[11px] text-cyan-300">初始请求参数</p>
        <pre className="max-h-40 overflow-auto whitespace-pre-wrap break-words rounded-md border border-cyan-500/20 bg-zinc-950/80 p-2 font-mono text-[10px] text-zinc-300">
          {JSON.stringify(
            {
              birth_time: streamQuery.birth_time || birthTimeISO || null,
              gender: streamQuery.gender || natalGender || null,
              calendar_type:
                natalCalendar ||
                (streamBody as { calendar_type?: string } | null)?.calendar_type ||
                null,
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

      <details className="mt-3 rounded-xl border border-cyan-500/20 bg-zinc-950/70 p-3" open>
        <summary className="cursor-pointer text-[11px] text-cyan-300">full_prompt_trace 审计</summary>
        <div className="mt-3 space-y-2">
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
            fullTrace?.system_role ??
              llmMeta.llm_system_prompt ??
              "（本期帧未携带，可能为缓存帧或非 LLM 路径）",
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
      </details>

      <details className="mt-3 rounded-xl border border-cyan-500/20 bg-zinc-950/70 p-3" open>
        <summary className="cursor-pointer text-[11px] text-cyan-300">插件 / Fact 分组</summary>
        <div className="mt-3">
        <p className="text-[11px] text-cyan-300">命中插件</p>
        <p className="mt-1 text-[11px] text-zinc-200">
          {traceHits.length ? (traceHits as string[]).join(" / ") : "暂无命中"}
        </p>
        </div>
        <div className="mt-3">
        <p className="text-[11px] text-cyan-300">织造 Fact</p>
        <div className="mt-1 space-y-1">
          {traceFacts.length ? (
            (traceFacts as string[]).map((x, idx) => (
              <p key={`${idx}_${x}`} className="text-[11px] text-zinc-200">
                {idx + 1}. {String(x)}
              </p>
            ))
          ) : (
            <p className="text-[11px] text-zinc-500">暂无 Fact</p>
          )}
        </div>
        </div>
        <div className="mt-3 space-y-2">
          <p className="text-[11px] text-cyan-300">插件分组</p>
          {Object.keys(groupedPlugins).length ? (
            Object.entries(groupedPlugins).map(([plugin, facts]) => (
              <details key={plugin} className="rounded-lg border border-cyan-500/15 bg-zinc-900/70 p-2">
                <summary className="cursor-pointer text-[11px] text-zinc-100">{plugin}</summary>
                <div className="mt-2 space-y-1">
                  {facts.map((fact, idx) => (
                    <p key={`${plugin}_${idx}`} className="text-[10px] text-zinc-300">
                      {idx + 1}. {fact}
                    </p>
                  ))}
                </div>
              </details>
            ))
          ) : (
            <p className="text-[11px] text-zinc-500">暂无插件分组</p>
          )}
        </div>
      </details>

      <details className="mt-3 rounded-xl border border-cyan-500/20 bg-zinc-950/70 p-3">
        <summary className="cursor-pointer text-[11px] text-cyan-300">四柱原始 payload</summary>
        <div className="mt-3 space-y-2">
          <p className="text-[10px] uppercase tracking-[0.22em] text-zinc-500">Physics SNAPSHOT</p>
          <pre className="max-h-56 overflow-auto whitespace-pre-wrap break-words rounded-md border border-zinc-700 bg-zinc-950/80 p-2 font-mono text-[10px] text-zinc-300">
            {JSON.stringify(physicsPayload, null, 2)}
          </pre>
          <p className="text-[10px] uppercase tracking-[0.22em] text-zinc-500">Audit SNAPSHOT</p>
          <pre className="max-h-56 overflow-auto whitespace-pre-wrap break-words rounded-md border border-zinc-700 bg-zinc-950/80 p-2 font-mono text-[10px] text-zinc-300">
            {JSON.stringify(auditPayload, null, 2)}
          </pre>
        </div>
      </details>

      {/* ── 展开式提示词 / 原始回复 ── */}
      <div className="mt-3 space-y-2 rounded-xl border border-cyan-500/20 bg-zinc-950/70 p-3">
        <details className="text-[11px] text-zinc-300">
          <summary className="cursor-pointer text-cyan-300/90">[查看完整提示词 (Prompt)]</summary>
          <p className="mt-1 text-[10px] text-cyan-400/80">System</p>
          <pre className="mt-0.5 max-h-36 overflow-auto whitespace-pre-wrap break-words rounded-md border border-zinc-700 bg-zinc-950/80 p-2 font-mono text-[10px] text-zinc-300">
            {String(fullTrace?.system_role ?? llmMeta.llm_system_prompt ?? "（等待终帧 llm_meta）")}
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
  );
}
