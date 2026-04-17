"use client";

import { useCallback, useMemo, useState } from "react";

export type ArbiterAuditEntry = {
  id?: string;
  at?: string;
  protocol?: string;
  arbitration_theme?: string;
  conflict_name?: string;
  gold_badge?: string;
  prompt_messages?: Array<{ role?: string; content?: string }>;
  raw_response?: string;
  raw_llm_reason?: string;
  conflict_context?: Record<string, unknown>;
  decision_plugin_id?: string;
  reason?: string;
  candidate_plugins?: string[];
  law_node_id?: string;
  overruled?: boolean;
  batch_id?: string;
  batch_index?: number;
  batch_total?: number;
};

function safeJson(obj: unknown, space = 2): string {
  try {
    return JSON.stringify(obj, null, space);
  } catch {
    return String(obj);
  }
}

function mergeSilentRowWithFeed(
  row: Record<string, unknown>,
  feed: ArbiterAuditEntry[],
): ArbiterAuditEntry {
  const aid = String(row.arbitration_audit_id || row.id || "").trim();
  const fromFeed = feed.find((e) => String(e.id || "").trim() === aid);
  return {
    ...(fromFeed || {}),
    ...row,
    id: aid || fromFeed?.id,
    arbitration_theme: String(row.arbitration_theme || fromFeed?.arbitration_theme || "").trim() || fromFeed?.arbitration_theme,
    prompt_messages: Array.isArray(row.prompt_messages)
      ? (row.prompt_messages as ArbiterAuditEntry["prompt_messages"])
      : fromFeed?.prompt_messages,
    raw_llm_reason: String(row.raw_llm_reason || fromFeed?.raw_llm_reason || "").trim() || fromFeed?.raw_llm_reason,
    reason: String(row.reason || fromFeed?.reason || "").trim() || fromFeed?.reason,
    gold_badge: String(row.gold_badge || fromFeed?.gold_badge || "").trim() || fromFeed?.gold_badge,
    decision_plugin_id: String(row.decision || fromFeed?.decision_plugin_id || "").trim() || fromFeed?.decision_plugin_id,
    conflict_name: fromFeed?.conflict_name,
    overruled: Boolean(fromFeed?.overruled) || Boolean(row.overruled),
    batch_id: String(row.batch_id || fromFeed?.batch_id || "").trim() || fromFeed?.batch_id,
    batch_index: typeof row.batch_index === "number" ? row.batch_index : fromFeed?.batch_index,
    batch_total: typeof row.batch_total === "number" ? row.batch_total : fromFeed?.batch_total,
  };
}

export function ArbiterAuditPanel(props: {
  entries: ArbiterAuditEntry[];
  /** 与 physics / 断言树镜像同源；可点击展开详情 */
  silentHistoryRows?: Record<string, unknown>[];
  feedEpoch?: number;
  consultationId?: number | null;
  onOverrule?: (auditId: string) => Promise<void>;
}) {
  const { entries, silentHistoryRows = [], feedEpoch = 0, consultationId, onOverrule } = props;
  const [detail, setDetail] = useState<ArbiterAuditEntry | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);

  const close = useCallback(() => {
    setDetail(null);
    setErr(null);
  }, []);

  const themeLabel = useMemo(() => {
    if (!detail) return "";
    const t = String(detail.arbitration_theme || "").trim();
    if (t) return t;
    return String(detail.conflict_name || "智能裁决").trim() || "智能裁决";
  }, [detail]);

  const reasonText = useMemo(() => {
    if (!detail) return "";
    const r = String(detail.raw_llm_reason || "").trim();
    if (r) return r;
    return String(detail.reason || "").trim();
  }, [detail]);

  const { entryBatchGroups, entrySingles } = useMemo(() => {
    const m = new Map<string, ArbiterAuditEntry[]>();
    const singles: ArbiterAuditEntry[] = [];
    for (const e of entries) {
      const b = String(e.batch_id || "").trim();
      if (!b) {
        singles.push(e);
        continue;
      }
      if (!m.has(b)) m.set(b, []);
      m.get(b)!.push(e);
    }
    return { entryBatchGroups: Array.from(m.entries()), entrySingles: singles };
  }, [entries]);

  const { silentBatches, silentRest } = useMemo(() => {
    const m = new Map<string, Record<string, unknown>[]>();
    const rest: Record<string, unknown>[] = [];
    for (const r of silentHistoryRows) {
      const b = String(r.batch_id || "").trim();
      if (!b) {
        rest.push(r);
        continue;
      }
      if (!m.has(b)) m.set(b, []);
      m.get(b)!.push(r);
    }
    return { silentBatches: Array.from(m.entries()), silentRest: rest };
  }, [silentHistoryRows]);

  const handleOverrule = useCallback(async () => {
    if (!detail?.id || !onOverrule) return;
    setErr(null);
    setBusyId(String(detail.id));
    try {
      await onOverrule(String(detail.id));
      close();
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setBusyId(null);
    }
  }, [close, detail, onOverrule]);

  const openFromEntry = (row: ArbiterAuditEntry) => {
    setErr(null);
    setDetail(row);
  };

  const openFromSilent = (row: Record<string, unknown>) => {
    setErr(null);
    setDetail(mergeSilentRowWithFeed(row, entries));
  };

  const goldFrame =
    "rounded-xl border-2 border-amber-400/75 bg-gradient-to-br from-zinc-950 via-zinc-950 to-amber-950/25 shadow-[0_0_28px_rgba(251,191,36,0.12)]";

  if (!entries.length && !silentHistoryRows.length) {
    return (
      <p className="text-xs text-zinc-500">
        暂无智能裁决审计。满足 V12.94/V12.95 静默仲裁条件并完成一次裁决后，将在此展示可回溯的 Prompt、候选与理由。
      </p>
    );
  }

  const renderEntryRow = (row: ArbiterAuditEntry, idx: number, globalNewest: boolean) => {
    const id = String(row.id || `idx-${idx}`);
    const overruled = Boolean(row.overruled);
    const bid = String(row.batch_id || "").trim();
    const batchHint =
      bid && row.batch_total != null && Number(row.batch_total) > 0
        ? `批量 ${Number(row.batch_index ?? 0) + 1}/${Number(row.batch_total)} · ${bid.slice(0, 28)}`
        : "";
    return (
      <li key={id}>
        <button
          type="button"
          onClick={() => openFromEntry(row)}
          className={
            "w-full rounded-lg border-2 border-amber-400/70 bg-gradient-to-br from-zinc-950 to-amber-950/20 p-3 text-left shadow-sm outline-none transition hover:border-amber-300/90 hover:shadow-[0_0_20px_rgba(251,191,36,0.18)] focus-visible:ring-2 focus-visible:ring-amber-400/80 " +
            (globalNewest ? "animate-arbiter-gold-in " : "") +
            (overruled ? "opacity-60 border-zinc-600 " : "")
          }
        >
          <div className="flex flex-wrap items-center justify-between gap-2">
            <p className="min-w-0 flex-1 font-medium text-amber-50/95">
              {String(row.arbitration_theme || row.conflict_name || "未命名主题")}
            </p>
            {row.gold_badge ? (
              <span className="shrink-0 rounded-full border border-amber-500/50 bg-amber-500/10 px-2 py-0.5 text-[10px] font-medium text-amber-200">
                {String(row.gold_badge)}
              </span>
            ) : null}
          </div>
          {batchHint ? <p className="mt-1 text-[10px] text-cyan-300/85">{batchHint}</p> : null}
          <p className="mt-1 font-mono text-[10px] text-zinc-500">{String(row.at || "—")}</p>
          {row.decision_plugin_id ? (
            <p className="mt-1 text-[11px] text-emerald-200/90">
              裁决插件：<span className="font-mono">{String(row.decision_plugin_id)}</span>
            </p>
          ) : null}
          {overruled ? <p className="mt-1 text-[10px] text-rose-300/90">已撤销并转人工</p> : null}
          <p className="mt-2 text-[10px] text-amber-200/70">点击查看完整提示词与裁决理由</p>
        </button>
      </li>
    );
  };

  return (
    <div className="space-y-4">
      {entries.length > 0 ? (
        <div className="space-y-4 text-xs text-zinc-300">
          {entryBatchGroups.map(([bid, rows]) => (
            <div key={bid} className="rounded-lg border border-cyan-700/45 bg-cyan-950/20 p-2 shadow-sm">
              <p className="mb-2 text-[10px] font-semibold uppercase tracking-wide text-cyan-200/90">
                批量仲裁 · <span className="font-mono">{bid}</span> · {rows.length} 条
              </p>
              <ul className="space-y-3">{rows.map((row, j) => renderEntryRow(row, j, false))}</ul>
            </div>
          ))}
          {entrySingles.length > 0 ? (
            <ul className="space-y-3">
              {entrySingles.map((row, idx) =>
                renderEntryRow(row, idx, idx === entrySingles.length - 1 && feedEpoch > 0 && entryBatchGroups.length === 0),
              )}
            </ul>
          ) : null}
        </div>
      ) : null}

      {silentHistoryRows.length > 0 && entries.length === 0 ? (
        <div className="border-t border-zinc-800 pt-3">
          <p className="mb-2 text-[10px] font-medium uppercase tracking-wide text-amber-200/80">智能裁决历史（镜像）</p>
          <div className="space-y-3">
            {silentBatches.map(([bid, rows]) => (
              <div key={bid} className="rounded-lg border border-cyan-700/40 bg-cyan-950/15 p-2">
                <p className="mb-2 text-[10px] font-semibold text-cyan-200/85">
                  批量 · <span className="font-mono">{bid}</span> · {rows.length} 条
                </p>
                <ul className="space-y-2">
                  {rows.map((row, i) => {
                    const k = `${bid}-${String(row.at ?? i)}-${String(row.decision ?? "")}`;
                    return (
                      <li key={k}>
                        <button
                          type="button"
                          onClick={() => openFromSilent(row)}
                          className="w-full rounded-lg border-2 border-amber-500/55 bg-zinc-950/80 p-2 text-left outline-none transition hover:border-amber-300/90 focus-visible:ring-2 focus-visible:ring-amber-400/80"
                        >
                          <p className="font-mono text-[10px] text-zinc-500">{String(row.at ?? "—")}</p>
                          <p className="mt-0.5 text-[11px] font-medium text-amber-100/90">
                            {String(row.arbitration_theme || `插件：${String(row.decision ?? "—")}`)}
                          </p>
                          {row.reason ? <p className="mt-0.5 line-clamp-2 text-zinc-500">{String(row.reason)}</p> : null}
                          <p className="mt-1 text-[10px] text-amber-200/70">点击查看审计详情</p>
                        </button>
                      </li>
                    );
                  })}
                </ul>
              </div>
            ))}
            {silentRest.length > 0 ? (
              <ul className="space-y-2">
                {silentRest.map((row, i) => {
                  const k = `${String(row.at ?? i)}-${String(row.decision ?? row.law_node_id ?? "")}`;
                  return (
                    <li key={k}>
                      <button
                        type="button"
                        onClick={() => openFromSilent(row)}
                        className="w-full rounded-lg border-2 border-amber-500/55 bg-zinc-950/80 p-2 text-left outline-none transition hover:border-amber-300/90 focus-visible:ring-2 focus-visible:ring-amber-400/80"
                      >
                        <p className="font-mono text-[10px] text-zinc-500">{String(row.at ?? "—")}</p>
                        <p className="mt-0.5 text-[11px] font-medium text-amber-100/90">
                          {String(row.arbitration_theme || `插件：${String(row.decision ?? "—")}`)}
                        </p>
                        {row.reason ? <p className="mt-0.5 line-clamp-2 text-zinc-500">{String(row.reason)}</p> : null}
                        <p className="mt-1 text-[10px] text-amber-200/70">点击查看审计详情</p>
                      </button>
                    </li>
                  );
                })}
              </ul>
            ) : null}
          </div>
        </div>
      ) : null}

      {detail ? (
        <div
          className="fixed inset-0 z-[220] flex items-center justify-center bg-black/75 p-3 sm:p-6"
          role="dialog"
          aria-modal="true"
          aria-labelledby="arbiter-detail-title"
          onClick={close}
        >
          <div
            className={`max-h-[min(92dvh,720px)] w-full max-w-2xl overflow-hidden ${goldFrame}`}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-start justify-between gap-2 border-b border-amber-900/40 px-4 py-3">
              <div className="min-w-0">
                <p id="arbiter-detail-title" className="text-sm font-semibold text-amber-50">
                  主题 · {themeLabel}
                </p>
                <p className="mt-0.5 font-mono text-[10px] text-zinc-500">{String(detail.at || "")}</p>
              </div>
              <button
                type="button"
                className="shrink-0 rounded-md border border-zinc-600 px-2 py-1 text-[10px] text-zinc-300 hover:bg-zinc-900"
                onClick={close}
              >
                关闭
              </button>
            </div>
            <div className="max-h-[min(72dvh,560px)] space-y-3 overflow-y-auto px-4 py-3">
              {detail.gold_badge ? (
                <p className="text-[11px] text-amber-200/90">
                  <span className="font-semibold text-amber-100">GOLD 偏好</span>：{String(detail.gold_badge)}
                </p>
              ) : null}
              {String(detail.batch_id || "").trim() ? (
                <p className="text-[11px] text-cyan-200/90">
                  批量 batch_id：<span className="font-mono break-all">{String(detail.batch_id)}</span>
                  {detail.batch_total != null && Number(detail.batch_total) > 0 ? (
                    <span className="text-zinc-400">
                      {" "}
                      （{Number(detail.batch_index ?? 0) + 1}/{Number(detail.batch_total)}）
                    </span>
                  ) : null}
                </p>
              ) : null}
              <div>
                <p className="text-[10px] font-semibold uppercase tracking-wide text-zinc-500">提示词（发往 LLM）</p>
                <pre className="mt-1 max-h-[min(36dvh,320px)] overflow-auto rounded border border-zinc-800 bg-black/50 p-2 font-mono text-[10px] text-zinc-300">
                  {safeJson(detail.prompt_messages ?? [])}
                </pre>
              </div>
              <div>
                <p className="text-[10px] font-semibold uppercase tracking-wide text-zinc-500">裁决理由（原件）</p>
                <article className="mt-1 whitespace-pre-wrap break-words rounded border border-zinc-800 bg-black/40 p-2 text-[11px] leading-relaxed text-zinc-200">
                  {reasonText || "—"}
                </article>
              </div>
              {Array.isArray(detail.candidate_plugins) && detail.candidate_plugins.length > 0 ? (
                <p className="text-[11px] text-zinc-400">
                  候选插件：<span className="font-mono text-zinc-200">{detail.candidate_plugins.join(" · ")}</span>
                </p>
              ) : null}
              {err ? <p className="text-[11px] text-rose-300">{err}</p> : null}
            </div>
            <div className="flex flex-wrap items-center justify-end gap-2 border-t border-amber-900/35 bg-black/20 px-4 py-3">
              {onOverrule && detail.id && !detail.overruled ? (
                <button
                  type="button"
                  disabled={busyId === detail.id}
                  className="rounded-md border border-rose-700/80 bg-rose-950/40 px-3 py-1.5 text-[11px] font-medium text-rose-100 hover:bg-rose-900/50 disabled:opacity-50"
                  onClick={() => void handleOverrule()}
                >
                  {busyId === detail.id ? "处理中…" : "撤销并转人工"}
                </button>
              ) : null}
              {consultationId ? (
                <span className="text-[10px] text-zinc-500">会话 {consultationId} · 否决将写入 arbitration_logs</span>
              ) : null}
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
