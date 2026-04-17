"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { API_BASE } from "@/features/admin-settings/constants";
import { useLabStore } from "@/features/stream-board/stores/useLabStore";
import type { FourPillars } from "@/types/bazi";

const HISTORY_KEY = "qiazhi_audit_chamber_history_v1";

type AuditHistoryItem = {
  id: string;
  at: string;
  label: string;
  summary: string;
};

type DiagnoseResponse = {
  ok?: boolean;
  logical_evidence?: string[];
  sys_core_physics?: {
    plugin_id?: string;
    l1_atomic_pipeline?: { steps?: unknown[]; version?: string };
    composite_field_impact?: { sanhe_clusters?: unknown[] };
    sanhe_clusters?: unknown[];
  };
  decision_inbox_gate?: Record<string, unknown>;
  l1_junction_flags?: Record<string, unknown>;
  narrative_diff?: { missing_evidence_lines?: { line: string; attribution: string }[]; verdict_provided?: boolean };
  audit_report_markdown?: string;
  confront_answer_markdown?: string;
  error?: string;
};

const defaultPillars: FourPillars = {
  year: { stem: "甲", branch: "子" },
  month: { stem: "丙", branch: "寅" },
  day: { stem: "戊", branch: "午" },
  hour: { stem: "庚", branch: "申" },
};

function loadHistory(): AuditHistoryItem[] {
  try {
    const raw = localStorage.getItem(HISTORY_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as AuditHistoryItem[];
    return Array.isArray(parsed) ? parsed.slice(0, 40) : [];
  } catch {
    return [];
  }
}

function saveHistory(items: AuditHistoryItem[]) {
  try {
    localStorage.setItem(HISTORY_KEY, JSON.stringify(items.slice(0, 40)));
  } catch {
    /* ignore */
  }
}

/** 「逻辑检察院」完整 UI，嵌入 DebugView（黑匣子）；机房 Admin 不再挂载。 */
export function AuditChamberPanel() {
  const { state } = useLabStore();
  const labMetadata = state.snapshot?.metadata;
  const [pillars, setPillars] = useState<FourPillars>(defaultPillars);
  const [verdict, setVerdict] = useState("");
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<DiagnoseResponse | null>(null);
  const [reportMd, setReportMd] = useState("");
  const [history, setHistory] = useState<AuditHistoryItem[]>([]);

  useEffect(() => {
    setHistory(loadHistory());
  }, []);

  const pillarsLabel = useMemo(() => {
    const p = pillars;
    return `${p.year.stem}${p.year.branch}/${p.month.stem}${p.month.branch}/${p.day.stem}${p.day.branch}/${p.hour.stem}${p.hour.branch}`;
  }, [pillars]);

  const runDiagnose = useCallback(
    async (opts: { generateReport: boolean }) => {
      setLoading(true);
      setError(null);
      try {
        const url = `${API_BASE}/api/v1/audit/diagnose`;
        const res = await fetch(url, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            pillars,
            final_verdict_markdown: verdict,
            user_question: question,
            generate_report: opts.generateReport,
            enabled_plugins: ["classical.blind_school.v1"],
          }),
        });
        const data = (await res.json()) as DiagnoseResponse;
        if (!res.ok) {
          setError((data as { detail?: string }).detail || res.statusText || "请求失败");
          setResult(null);
          return;
        }
        setResult(data);
        if (opts.generateReport && data.audit_report_markdown) {
          setReportMd(data.audit_report_markdown);
        }
        const miss = data.narrative_diff?.missing_evidence_lines?.length ?? 0;
        const entry: AuditHistoryItem = {
          id: `${Date.now()}`,
          at: new Date().toISOString(),
          label: pillarsLabel,
          summary: `${miss} 条证据疑似未写入终判`,
        };
        setHistory((prev) => {
          const next = [entry, ...prev.filter((h) => h.label !== entry.label || h.summary !== entry.summary)].slice(0, 40);
          saveHistory(next);
          return next;
        });
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e));
        setResult(null);
      } finally {
        setLoading(false);
      }
    },
    [pillars, verdict, question, pillarsLabel],
  );

  const core = result?.sys_core_physics ?? {};
  const steps = core.l1_atomic_pipeline?.steps ?? [];
  const sanhe = core.sanhe_clusters ?? core.composite_field_impact?.sanhe_clusters ?? [];
  const gate = result?.decision_inbox_gate ?? {};

  return (
    <div className="flex min-h-0 flex-col gap-3 text-sm text-zinc-200 md:flex-row">
      <aside className="w-full shrink-0 rounded border border-zinc-800 bg-zinc-950/50 p-3 md:w-56">
        <div className="text-xs font-semibold text-amber-200/90">历史审计</div>
        <ul className="mt-2 max-h-48 space-y-1 overflow-y-auto text-xs text-zinc-500">
          {history.length === 0 ? <li>（暂无）</li> : null}
          {history.map((h) => (
            <li key={h.id} className="truncate rounded bg-zinc-900/60 px-1 py-0.5" title={h.summary}>
              <span className="text-zinc-400">{h.label}</span>
              <div className="text-[10px] text-zinc-600">{h.summary}</div>
            </li>
          ))}
        </ul>
        <div className="mt-4 text-xs font-semibold text-amber-200/90">存疑八字（四柱）</div>
        <p className="mt-1 text-[10px] text-zinc-600">每柱干支各一字；可从实验室一键载入。</p>
        <button
          type="button"
          className="mt-2 w-full rounded border border-zinc-700 bg-zinc-900 px-2 py-1 text-[11px] hover:bg-zinc-800"
          onClick={() => {
            const raw = labMetadata && typeof labMetadata === "object" ? labMetadata.pillars : null;
            if (raw && typeof raw === "object" && raw !== null && "year" in raw) {
              setPillars(raw as FourPillars);
            }
          }}
        >
          从实验室载入四柱
        </button>
        {(["year", "month", "day", "hour"] as const).map((pk) => (
          <div key={pk} className="mt-2 grid grid-cols-2 gap-1">
            <span className="col-span-2 text-[10px] uppercase text-zinc-500">{pk}</span>
            <input
              className="rounded border border-zinc-700 bg-zinc-900 px-1 py-0.5 text-xs"
              maxLength={1}
              value={pillars[pk].stem}
              onChange={(e) =>
                setPillars((prev) => ({ ...prev, [pk]: { ...prev[pk], stem: e.target.value.slice(0, 1) } }))
              }
            />
            <input
              className="rounded border border-zinc-700 bg-zinc-900 px-1 py-0.5 text-xs"
              maxLength={1}
              value={pillars[pk].branch}
              onChange={(e) =>
                setPillars((prev) => ({ ...prev, [pk]: { ...prev[pk], branch: e.target.value.slice(0, 1) } }))
              }
            />
          </div>
        ))}
      </aside>

      <main className="min-w-0 flex-1 space-y-3">
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            disabled={loading}
            onClick={() => runDiagnose({ generateReport: false })}
            className="rounded border border-amber-700/50 bg-amber-950/40 px-3 py-1.5 text-xs text-amber-100 disabled:opacity-40"
          >
            运行审计（拉物理层）
          </button>
          <button
            type="button"
            disabled={loading}
            onClick={() => runDiagnose({ generateReport: true })}
            className="rounded border border-zinc-600 bg-zinc-900 px-3 py-1.5 text-xs hover:bg-zinc-800 disabled:opacity-40"
          >
            生成审计报告（Markdown）
          </button>
        </div>
        {error ? <div className="rounded border border-red-900/60 bg-red-950/30 px-2 py-1 text-xs text-red-200">{error}</div> : null}

        <section className="rounded border border-zinc-800 bg-zinc-900/40 p-3">
          <h2 className="text-xs font-semibold text-zinc-300">[断言区] 终判原文（可选）</h2>
          <textarea
            className="mt-2 min-h-[100px] w-full resize-y rounded border border-zinc-700 bg-zinc-950 p-2 text-xs text-zinc-200"
            placeholder="粘贴 Final Verdict markdown，用于与 logical_evidence 对照……"
            value={verdict}
            onChange={(e) => setVerdict(e.target.value)}
          />
        </section>

        <section className="rounded border border-zinc-800 bg-zinc-900/40 p-3">
          <h2 className="text-xs font-semibold text-zinc-300">[物理证据瀑布流]</h2>
          <div className="mt-2 text-[11px] text-zinc-500">
            当前四柱：<span className="text-zinc-300">{pillarsLabel}</span> · L1 步数 {steps.length} · 三合簇 {sanhe.length}
          </div>
          <ul className="mt-2 max-h-56 space-y-1 overflow-y-auto font-mono text-[11px] text-emerald-200/90">
            {(result?.logical_evidence ?? []).map((line) => (
              <li key={line} className="break-all">
                {line}
              </li>
            ))}
            {!result?.logical_evidence?.length ? <li className="text-zinc-600">（先点击运行审计）</li> : null}
          </ul>
          <div className="mt-3 text-[11px] text-zinc-500">L1 steps（插件摘要，前 24 条）</div>
          <ul className="mt-1 max-h-40 space-y-0.5 overflow-y-auto font-mono text-[10px] text-cyan-200/80">
            {steps.slice(0, 24).map((s, i) => (
              <li key={i} className="break-all">
                {(s as { plugin?: string })?.plugin ?? "?"} · {JSON.stringify(s).slice(0, 160)}
                {JSON.stringify(s).length > 160 ? "…" : ""}
              </li>
            ))}
          </ul>
        </section>

        <section className="rounded border border-zinc-800 bg-zinc-900/40 p-3">
          <h2 className="text-xs font-semibold text-zinc-300">[逻辑漏斗分析] Decision Inbox 门控</h2>
          <pre className="mt-2 overflow-x-auto rounded bg-zinc-950 p-2 text-[11px] text-fuchsia-200/90">
            {JSON.stringify(gate, null, 2) || "{}"}
          </pre>
          <p className="mt-2 text-[11px] text-zinc-500">
            `inbox_conflict_cards_eligible=false` 时，流式判词观察项会被物理屏蔽；**三合 L1_STRUCTURE 卡仍可由 tensor
            直驱（与实验室 Inbox 一致）**。
          </p>
          <div className="mt-2 text-[11px] text-zinc-400">L1 Junction Flags</div>
          <pre className="mt-1 max-h-32 overflow-auto rounded bg-zinc-950 p-2 text-[10px] text-zinc-400">
            {JSON.stringify(result?.l1_junction_flags ?? {}, null, 2)}
          </pre>
          <div className="mt-2 text-[11px] text-amber-200/80">叙事差异（启发式）</div>
          <ul className="mt-1 list-disc pl-4 text-[11px] text-zinc-400">
            {(result?.narrative_diff?.missing_evidence_lines ?? []).map((m) => (
              <li key={m.line} className="break-words">
                <code className="text-zinc-300">{m.line}</code>
                <div className="text-zinc-500">{m.attribution}</div>
              </li>
            ))}
            {(result?.narrative_diff?.missing_evidence_lines?.length ?? 0) === 0 && result ? (
              <li>无缺失行或未提供终判文本。</li>
            ) : null}
          </ul>
        </section>

        <section className="rounded border border-zinc-800 bg-zinc-900/40 p-3">
          <h2 className="text-xs font-semibold text-zinc-300">[逻辑对质]</h2>
          <input
            className="mt-2 w-full rounded border border-zinc-700 bg-zinc-950 px-2 py-1 text-xs"
            placeholder="例如：为何此盘未强调三合金局？"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
          />
          <button
            type="button"
            disabled={loading || !question.trim()}
            onClick={() => runDiagnose({ generateReport: false })}
            className="mt-2 rounded border border-zinc-600 bg-zinc-900 px-2 py-1 text-[11px] hover:bg-zinc-800 disabled:opacity-40"
          >
            提交追问（随诊断返回规则草稿）
          </button>
          {result?.confront_answer_markdown ? (
            <div className="mt-2 rounded border border-zinc-700 bg-black/30 p-2 text-xs text-zinc-300 whitespace-pre-wrap">
              {result.confront_answer_markdown}
            </div>
          ) : null}
        </section>

        {reportMd ? (
          <section className="rounded border border-zinc-800 bg-zinc-900/40 p-3">
            <h2 className="text-xs font-semibold text-zinc-300">审计报告（Markdown）</h2>
            <pre className="mt-2 max-h-96 overflow-auto whitespace-pre-wrap rounded bg-zinc-950 p-2 text-[11px] text-zinc-300">
              {reportMd}
            </pre>
          </section>
        ) : null}
      </main>
    </div>
  );
}
