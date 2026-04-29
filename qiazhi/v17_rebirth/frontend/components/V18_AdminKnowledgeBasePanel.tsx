"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { AlertTriangle, BookOpen, CheckCircle2, FlaskConical, Loader2, RefreshCcw, ShieldCheck, Trash2 } from "lucide-react";

import { jsonPostInit, noStoreInit, requestJson } from "@/lib/apiClient";

type KnowledgeUnit = {
  knowledge_id: string;
  domain: string;
  category: string;
  title: string;
  statement: string;
  classical_source: string;
  modern_interpretation: string;
  conditions: Record<string, unknown>;
  feature_mapping: Record<string, unknown>;
  effects: Record<string, unknown>;
  risk_factors: string[];
  uncertainty_factors: string[];
  conflicts: string[];
  confidence_prior: number;
  status: string;
  created_by: string;
  reviewed_by: string;
  updated_at: string;
};

type AdminKnowledgeBasePanelProps = {
  displayName?: string;
  onLogout?: () => void | Promise<void>;
};

const CATEGORIES = [
  "",
  "wealth_star",
  "wealth_vault",
  "output_generate_wealth",
  "constraint_structure",
  "combination_clash_stability",
  "luck_flow_activation",
];

const STATUSES = ["", "draft", "reviewed", "deprecated"];

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value && typeof value === "object" && !Array.isArray(value));
}

function unwrapEnvelope(value: unknown): Record<string, unknown> {
  if (isRecord(value) && isRecord(value.data)) return value.data;
  return isRecord(value) ? value : {};
}

function readArray(source: unknown, key: string): unknown[] {
  if (!isRecord(source)) return [];
  const value = source[key];
  return Array.isArray(value) ? value : [];
}

function readRecord(source: unknown, key: string): Record<string, unknown> {
  if (!isRecord(source)) return {};
  const value = source[key];
  return isRecord(value) ? value : {};
}

function readString(source: unknown, keys: string[], fallback = ""): string {
  if (!isRecord(source)) return fallback;
  for (const key of keys) {
    const value = source[key];
    if (typeof value === "string" && value.trim()) return value.trim();
    if (typeof value === "number" && Number.isFinite(value)) return String(value);
  }
  return fallback;
}

function readNumber(source: unknown, keys: string[]): number {
  if (!isRecord(source)) return 0;
  for (const key of keys) {
    const value = source[key];
    if (typeof value === "number" && Number.isFinite(value)) return value;
    if (typeof value === "string" && value.trim() && Number.isFinite(Number(value))) return Number(value);
  }
  return 0;
}

function compactJson(value: unknown): string {
  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value);
  }
}

function apiFailureMessage(value: unknown, requestError: string | undefined, fallback: string): string {
  return requestError || readString(value, ["message", "detail", "error"]) || readString(unwrapEnvelope(value), ["message", "detail", "error"]) || fallback;
}

function normalizeUnit(row: unknown): KnowledgeUnit {
  const source = isRecord(row) ? row : {};
  return {
    knowledge_id: readString(source, ["knowledge_id"]),
    domain: readString(source, ["domain"]),
    category: readString(source, ["category"]),
    title: readString(source, ["title"]),
    statement: readString(source, ["statement"]),
    classical_source: readString(source, ["classical_source"]),
    modern_interpretation: readString(source, ["modern_interpretation"]),
    conditions: readRecord(source, "conditions"),
    feature_mapping: readRecord(source, "feature_mapping"),
    effects: readRecord(source, "effects"),
    risk_factors: readArray(source, "risk_factors").map(String),
    uncertainty_factors: readArray(source, "uncertainty_factors").map(String),
    conflicts: readArray(source, "conflicts").map(String),
    confidence_prior: readNumber(source, ["confidence_prior"]),
    status: readString(source, ["status"]),
    created_by: readString(source, ["created_by"]),
    reviewed_by: readString(source, ["reviewed_by"]),
    updated_at: readString(source, ["updated_at"]),
  };
}

function statusTone(status: string): string {
  if (status === "reviewed") return "border-emerald-300/20 bg-emerald-300/10 text-emerald-100";
  if (status === "deprecated") return "border-rose-300/20 bg-rose-500/10 text-rose-100";
  return "border-amber-300/20 bg-amber-300/10 text-amber-100";
}

export function V18_AdminKnowledgeBasePanel({ displayName, onLogout }: AdminKnowledgeBasePanelProps): ReactNode {
  const [units, setUnits] = useState<KnowledgeUnit[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [category, setCategory] = useState("");
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(false);
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [candidatePreviewById, setCandidatePreviewById] = useState<Record<string, Record<string, unknown>>>({});
  const [auditReportById, setAuditReportById] = useState<Record<string, Record<string, unknown>>>({});

  const selected = useMemo(() => units.find((unit) => unit.knowledge_id === selectedId) || units[0], [selectedId, units]);
  const reviewedCount = units.filter((unit) => unit.status === "reviewed").length;
  const draftCount = units.filter((unit) => unit.status === "draft").length;

  const loadUnits = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const params = new URLSearchParams({ domain: "wealth", limit: "200" });
      if (category) params.set("category", category);
      if (status) params.set("status", status);
      const resp = await requestJson<unknown>(`/api/v18.1/knowledge-base/units?${params.toString()}`, noStoreInit());
      if (!resp.ok) throw new Error(apiFailureMessage(resp.data, resp.error, "Knowledge Base 加载失败。"));
      const payload = unwrapEnvelope(resp.data);
      const rows = readArray(payload, "items").map(normalizeUnit);
      setUnits(rows);
      setSelectedId((prev) => (prev && rows.some((row) => row.knowledge_id === prev) ? prev : rows[0]?.knowledge_id || ""));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Knowledge Base 加载失败。");
    } finally {
      setLoading(false);
    }
  }, [category, status]);

  useEffect(() => {
    void loadUnits();
  }, [loadUnits]);

  const runAction = useCallback(
    async (action: "review" | "deprecate" | "to-rule-candidate" | "dry-run-audit", knowledgeId: string) => {
      setBusy(`${action}:${knowledgeId}`);
      setError("");
      setNotice("");
      try {
        const resp = await requestJson<unknown>(
          `/api/v18.1/knowledge-base/units/${encodeURIComponent(knowledgeId)}/${action}`,
          jsonPostInit({ reviewed_by: displayName || "admin", reason: "admin knowledge-base action" }, noStoreInit()),
        );
        if (!resp.ok) throw new Error(apiFailureMessage(resp.data, resp.error, "Knowledge Base 操作失败。"));
        const payload = unwrapEnvelope(resp.data);
        const candidateId = readString(payload, ["candidate_id"]);
        if (action === "to-rule-candidate") {
          setCandidatePreviewById((prev) => ({ ...prev, [knowledgeId]: payload }));
          setNotice(candidateId ? `已生成 sandbox rule candidate: ${candidateId}` : "Sandbox rule 逻辑已生成。");
        } else if (action === "dry-run-audit") {
          setAuditReportById((prev) => ({ ...prev, [knowledgeId]: payload }));
          const conflictCount = readArray(payload, "conflicts").length;
          setNotice(`Dry Run 审计完成，发现 ${conflictCount} 条审计记录。`);
        } else {
          setNotice("操作已完成。");
          await loadUnits();
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Knowledge Base 操作失败。");
      } finally {
        setBusy("");
      }
    },
    [displayName, loadUnits],
  );

  return (
    <main className="min-h-screen overflow-hidden bg-[#0b0f0a] text-slate-100">
      <div className="pointer-events-none fixed inset-0">
        <div className="absolute left-[-14%] top-[-20%] h-[34rem] w-[34rem] rounded-full bg-lime-400/14 blur-3xl" />
        <div className="absolute bottom-[-18%] right-[-12%] h-[34rem] w-[34rem] rounded-full bg-emerald-300/14 blur-3xl" />
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(255,255,255,0.08),transparent_36%)]" />
      </div>

      <section className="relative mx-auto w-full max-w-7xl px-4 py-5 sm:px-6 lg:px-8">
        <header className="rounded-[2rem] border border-white/10 bg-white/[0.07] p-6 shadow-2xl shadow-black/30 backdrop-blur">
          <div className="flex flex-col gap-5 md:flex-row md:items-start md:justify-between">
            <div>
              <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-lime-200/20 bg-lime-200/10 px-3 py-1 text-xs text-lime-100">
                <BookOpen className="h-3.5 w-3.5" />
                Bazi Knowledge Base v1
              </div>
              <h1 className="text-3xl font-semibold tracking-tight md:text-5xl">Wealth Knowledge Units</h1>
              <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-300 md:text-base">
                这里管理结构化、可审核、可转 sandbox rule candidate 的财富知识。KB 不直接参与预测裁决，正式预测仍走 Rule Kernel → Contract → Verifier → Ledger。
              </p>
            </div>
            <div className="flex flex-wrap items-center gap-2 text-sm">
              <span className="rounded-full border border-white/10 bg-black/20 px-3 py-2 text-slate-300">{displayName || "Admin"}</span>
              <button type="button" onClick={() => void loadUnits()} className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/10 px-3 py-2 text-slate-100 transition hover:bg-white/15">
                <RefreshCcw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
                刷新
              </button>
              {onLogout ? (
                <button type="button" onClick={() => void onLogout()} className="rounded-full border border-white/10 bg-black/20 px-3 py-2 text-slate-300 transition hover:bg-black/30">
                  退出
                </button>
              ) : null}
            </div>
          </div>
        </header>

        {error ? (
          <div className="mt-5 flex items-start gap-3 rounded-[1.5rem] border border-rose-300/20 bg-rose-500/10 p-4 text-sm text-rose-100">
            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
            <span>{error}</span>
          </div>
        ) : null}
        {notice ? (
          <div className="mt-5 flex items-start gap-3 rounded-[1.5rem] border border-emerald-300/20 bg-emerald-300/10 p-4 text-sm text-emerald-100">
            <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0" />
            <span>{notice}</span>
          </div>
        ) : null}

        <section className="mt-5 grid gap-5 lg:grid-cols-[22rem_minmax(0,1fr)]">
          <aside className="space-y-5">
            <div className="rounded-[2rem] border border-white/10 bg-white/[0.06] p-5 shadow-2xl shadow-black/20 backdrop-blur">
              <h2 className="mb-4 flex items-center gap-2 text-lg font-semibold">
                <ShieldCheck className="h-5 w-5 text-lime-200" />
                KB Snapshot
              </h2>
              <div className="grid grid-cols-3 gap-3">
                <Stat label="units" value={String(units.length)} />
                <Stat label="reviewed" value={String(reviewedCount)} />
                <Stat label="draft" value={String(draftCount)} />
              </div>
              <div className="mt-4 grid gap-3">
                <select value={category} onChange={(event) => setCategory(event.target.value)} className="rounded-2xl border border-white/10 bg-black/30 px-3 py-2 text-sm text-slate-100 outline-none">
                  {CATEGORIES.map((item) => (
                    <option key={item || "all"} value={item}>{item || "all categories"}</option>
                  ))}
                </select>
                <select value={status} onChange={(event) => setStatus(event.target.value)} className="rounded-2xl border border-white/10 bg-black/30 px-3 py-2 text-sm text-slate-100 outline-none">
                  {STATUSES.map((item) => (
                    <option key={item || "all"} value={item}>{item || "all statuses"}</option>
                  ))}
                </select>
              </div>
            </div>

            <div className="max-h-[46rem] overflow-auto rounded-[2rem] border border-white/10 bg-white/[0.06] p-3 shadow-2xl shadow-black/20 backdrop-blur">
              {loading ? (
                <div className="flex items-center gap-2 p-4 text-sm text-slate-400">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  加载中...
                </div>
              ) : units.length === 0 ? (
                <p className="rounded-2xl border border-dashed border-white/10 bg-black/20 p-4 text-sm text-slate-500">没有匹配的 Knowledge Unit。</p>
              ) : (
                units.map((unit) => (
                  <button
                    key={unit.knowledge_id}
                    type="button"
                    onClick={() => setSelectedId(unit.knowledge_id)}
                    className={`mb-2 block w-full rounded-2xl border p-3 text-left transition ${selected?.knowledge_id === unit.knowledge_id ? "border-lime-200/30 bg-lime-200/10" : "border-white/10 bg-black/20 hover:bg-white/10"}`}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span className="font-mono text-xs text-lime-100">{unit.knowledge_id}</span>
                      <span className={`rounded-full border px-2 py-0.5 text-[10px] ${statusTone(unit.status)}`}>{unit.status}</span>
                    </div>
                    <p className="mt-2 text-sm font-semibold text-white">{unit.title}</p>
                    <p className="mt-1 text-xs text-slate-500">{unit.category}</p>
                  </button>
                ))
              )}
            </div>
          </aside>

          <section className="rounded-[2rem] border border-white/10 bg-white/[0.06] p-5 shadow-2xl shadow-black/20 backdrop-blur">
            {selected ? (
              <KnowledgeDetail
                busy={busy}
                candidatePreview={candidatePreviewById[selected.knowledge_id] || {}}
                auditReport={auditReportById[selected.knowledge_id] || {}}
                unit={selected}
                onAction={(action) => void runAction(action, selected.knowledge_id)}
              />
            ) : (
              <p className="rounded-2xl border border-dashed border-white/10 bg-black/20 p-5 text-sm text-slate-500">请选择一条 Knowledge Unit。</p>
            )}
          </section>
        </section>
      </section>
    </main>
  );
}

function KnowledgeDetail({
  busy,
  candidatePreview,
  auditReport,
  unit,
  onAction,
}: {
  busy: string;
  candidatePreview: Record<string, unknown>;
  auditReport: Record<string, unknown>;
  unit: KnowledgeUnit;
  onAction: (action: "review" | "deprecate" | "to-rule-candidate" | "dry-run-audit") => void;
}): ReactNode {
  const featureType = readString(unit.feature_mapping, ["feature_type"], "n/a");
  const rulePayload = readRecord(candidatePreview, "rule_payload");
  const ruleCondition = readRecord(rulePayload, "condition");
  const compiledFromCandidate = readRecord(ruleCondition, "compiled_feature_logic");
  const compiledFromAudit = readRecord(auditReport, "compiled_rule_logic");
  const compiledLogic = Object.keys(compiledFromCandidate).length ? compiledFromCandidate : compiledFromAudit;
  const auditConflicts = readArray(auditReport, "conflicts");
  const auditStatus = readString(auditReport, ["audit_status"], "");
  return (
    <article>
      <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
        <div>
          <p className="font-mono text-sm text-lime-100">{unit.knowledge_id}</p>
          <h2 className="mt-2 text-3xl font-semibold text-white">{unit.title}</h2>
          <div className="mt-3 flex flex-wrap gap-2">
            <span className={`rounded-full border px-3 py-1 text-xs ${statusTone(unit.status)}`}>{unit.status}</span>
            <span className="rounded-full border border-cyan-200/20 bg-cyan-200/10 px-3 py-1 text-xs text-cyan-100">{unit.category}</span>
            <span className="rounded-full border border-white/10 bg-black/20 px-3 py-1 text-xs text-slate-300">{featureType}</span>
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          <ActionButton busy={busy === `review:${unit.knowledge_id}`} disabled={unit.status === "reviewed" || unit.status === "deprecated"} icon={<CheckCircle2 className="h-4 w-4" />} label="Review" onClick={() => onAction("review")} />
          <ActionButton busy={busy === `to-rule-candidate:${unit.knowledge_id}`} disabled={unit.status === "deprecated"} icon={<FlaskConical className="h-4 w-4" />} label="To sandbox candidate" onClick={() => onAction("to-rule-candidate")} />
          <ActionButton busy={busy === `dry-run-audit:${unit.knowledge_id}`} disabled={unit.status === "deprecated"} icon={<ShieldCheck className="h-4 w-4" />} label="Dry Run" onClick={() => onAction("dry-run-audit")} />
          <ActionButton busy={busy === `deprecate:${unit.knowledge_id}`} disabled={unit.status === "deprecated"} icon={<Trash2 className="h-4 w-4" />} label="Deprecate" onClick={() => onAction("deprecate")} />
        </div>
      </div>

      <div className="mt-6 grid gap-4 lg:grid-cols-2">
        <InfoCard title="Statement" body={unit.statement} />
        <InfoCard title="Modern interpretation" body={unit.modern_interpretation} />
        <InfoCard title="Classical source" body={unit.classical_source} />
        <InfoCard title="Confidence prior" body={String(unit.confidence_prior)} />
      </div>

      <div className="mt-5 grid gap-4 lg:grid-cols-2">
        <JsonCard title="Conditions" value={unit.conditions} />
        <JsonCard title="Feature Mapping" value={unit.feature_mapping} />
        <JsonCard title="Effects" value={unit.effects} />
        <JsonCard title="Conflicts" value={unit.conflicts} />
      </div>

      <div className="mt-5 rounded-[1.5rem] border border-lime-200/15 bg-lime-200/[0.06] p-4">
        <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
          <div>
            <h3 className="text-sm font-semibold text-lime-100">Diff View: Knowledge Unit → Sandbox Rule Logic</h3>
            <p className="mt-1 text-xs text-slate-400">只展示 sandbox 编译结果，不代表 active rule；正式预测仍必须走 Rule Test / Knowledge PR / Reviewer Activate。</p>
          </div>
          {auditStatus ? <span className="rounded-full border border-white/10 bg-black/20 px-3 py-1 text-xs text-slate-300">{auditStatus}</span> : null}
        </div>
        <div className="grid gap-4 lg:grid-cols-2">
          <JsonCard
            title="Original Knowledge Definition"
            value={{
              knowledge_id: unit.knowledge_id,
              statement: unit.statement,
              conditions: unit.conditions,
              feature_mapping: unit.feature_mapping,
              effects: unit.effects,
            }}
          />
          <JsonCard
            title="Compiled Sandbox Rule Logic"
            value={Object.keys(compiledLogic).length ? compiledLogic : { hint: "点击 To sandbox candidate 或 Dry Run 后显示编译逻辑。" }}
          />
        </div>
      </div>

      {auditConflicts.length ? (
        <div className="mt-5 rounded-[1.5rem] border border-amber-300/20 bg-amber-300/[0.06] p-4">
          <h3 className="text-sm font-semibold text-amber-100">Audit Conflict Report</h3>
          <div className="mt-3 grid gap-3">
            {auditConflicts.map((item, index) => (
              <pre key={`${unit.knowledge_id}:audit:${index}`} className="max-h-72 overflow-auto whitespace-pre-wrap break-words rounded-2xl border border-white/10 bg-black/25 p-3 text-xs leading-5 text-slate-300">{compactJson(item)}</pre>
            ))}
          </div>
        </div>
      ) : null}

      <div className="mt-5 grid gap-4 lg:grid-cols-2">
        <ListCard title="Risk factors" items={unit.risk_factors} />
        <ListCard title="Uncertainty factors" items={unit.uncertainty_factors} />
      </div>
    </article>
  );
}

function ActionButton({ busy, disabled, icon, label, onClick }: { busy: boolean; disabled: boolean; icon: ReactNode; label: string; onClick: () => void }): ReactNode {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled || busy}
      className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-black/20 px-4 py-2 text-sm text-slate-100 transition hover:bg-white/10 disabled:cursor-not-allowed disabled:opacity-45"
    >
      {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : icon}
      {label}
    </button>
  );
}

function Stat({ label, value }: { label: string; value: string }): ReactNode {
  return (
    <div className="rounded-2xl border border-white/10 bg-black/20 p-3">
      <div className="text-[10px] uppercase tracking-[0.16em] text-slate-500">{label}</div>
      <div className="mt-1 text-xl font-semibold text-white">{value}</div>
    </div>
  );
}

function InfoCard({ title, body }: { title: string; body: string }): ReactNode {
  return (
    <section className="rounded-2xl border border-white/10 bg-black/20 p-4">
      <h3 className="text-xs uppercase tracking-[0.16em] text-slate-500">{title}</h3>
      <p className="mt-2 text-sm leading-6 text-slate-200">{body || "n/a"}</p>
    </section>
  );
}

function JsonCard({ title, value }: { title: string; value: unknown }): ReactNode {
  return (
    <section className="rounded-2xl border border-white/10 bg-black/20 p-4">
      <h3 className="text-xs uppercase tracking-[0.16em] text-slate-500">{title}</h3>
      <pre className="mt-2 max-h-72 overflow-auto whitespace-pre-wrap break-words text-xs leading-5 text-slate-300">{compactJson(value)}</pre>
    </section>
  );
}

function ListCard({ title, items }: { title: string; items: string[] }): ReactNode {
  return (
    <section className="rounded-2xl border border-white/10 bg-black/20 p-4">
      <h3 className="text-xs uppercase tracking-[0.16em] text-slate-500">{title}</h3>
      <ul className="mt-2 space-y-2 text-sm text-slate-300">
        {(items.length ? items : ["n/a"]).map((item) => (
          <li key={item} className="rounded-xl border border-white/10 bg-white/[0.04] px-3 py-2">{item}</li>
        ))}
      </ul>
    </section>
  );
}
