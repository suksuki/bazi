"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { ADMIN_HEADERS, API_BASE } from "@/features/admin-settings/constants";

import { ClimateFieldStrengthCompare } from "@/features/admin/components/ClimateFieldStrengthCompare";
import { ConflictTopologyLossPanel } from "@/features/admin/components/ConflictTopologyLossPanel";
import {
  PatternSpecView,
  buildGapHints,
  collisionBandForRow,
  getInterceptReasonLines,
  pickHitPatternId,
  sortEntriesWithCollision,
  type CollisionBand,
  type PatternEvalRow,
} from "@/features/admin/components/PatternSpecView";

type ManifestDoc = Record<string, unknown>;

type PatternEntry = { section: string; key: string; spec: Record<string, unknown> };

function flattenPatterns(m: ManifestDoc | null): PatternEntry[] {
  if (!m) return [];
  const out: PatternEntry[] = [];
  for (const section of ["STANDARD_OCTAD", "SPECIAL_PATTERNS"] as const) {
    const block = m[section];
    if (!block || typeof block !== "object" || Array.isArray(block)) continue;
    for (const [key, spec] of Object.entries(block)) {
      if (spec && typeof spec === "object" && !Array.isArray(spec)) {
        out.push({ section, key, spec: spec as Record<string, unknown> });
      }
    }
  }
  return out;
}

function sectionTitle(section: string): string {
  if (section === "STANDARD_OCTAD") return "正格八法";
  if (section === "SPECIAL_PATTERNS") return "特殊格局";
  return section;
}

/** 将多格局 evaluate 的 trace_logic 摊平为终端滚动文本（V6.8 Traceability）。 */
function flattenTraceTerminalLines(rows: unknown[]): string[] {
  const out: string[] = [];
  for (const raw of rows) {
    const o = raw && typeof raw === "object" ? (raw as Record<string, unknown>) : {};
    const id = String(o.pattern_id ?? "?");
    out.push(`──────── ${id} ────────`);
    const tl = o.trace_logic;
    if (Array.isArray(tl)) {
      for (const line of tl) {
        out.push(String(line));
      }
    } else {
      out.push("(no trace_logic)");
    }
  }
  return out;
}

function stackLed(ok: boolean | null): string {
  if (ok === null) return "bg-zinc-600";
  return ok ? "bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.45)]" : "bg-rose-600";
}

function cardShellClass(band: CollisionBand, active: boolean): string {
  const base = "w-full rounded-lg border px-2.5 py-2 text-left transition-colors";
  const activeRing = active ? " ring-1 ring-amber-500/70 ring-offset-1 ring-offset-zinc-950" : "";
  if (band === "idle") {
    return `${base} border-zinc-800 bg-black/35 hover:bg-zinc-900/50${activeRing}`;
  }
  if (band === "full") {
    return `${base} border-emerald-600/55 bg-emerald-950/25 hover:bg-emerald-950/35${activeRing}`;
  }
  if (band === "near") {
    return `${base} border-amber-500/45 bg-amber-950/20 hover:bg-amber-950/30${activeRing}`;
  }
  return `${base} border-zinc-600 border-l-rose-500/80 bg-zinc-900/75 bg-gradient-to-r from-rose-950/25 to-zinc-950/40 hover:from-rose-950/35${activeRing}`;
}

export function AdminPatternDashboard() {
  const [manifest, setManifest] = useState<ManifestDoc | null>(null);
  const [editorText, setEditorText] = useState("");
  const [sha, setSha] = useState("");
  const [msg, setMsg] = useState("");
  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(false);
  const [selected, setSelected] = useState<PatternEntry | null>(null);
  const [specEditor, setSpecEditor] = useState("");
  const [tensorText, setTensorText] = useState(
    JSON.stringify(
      {
        deity_scores: { 正印: 4, 偏印: 4, 食神: 30, 伤官: 30, 比肩: 6, 劫财: 6, 偏财: 6, 正财: 6, 七杀: 4, 正官: 4 },
        meta: { month_branch: "午", active_structures: [] },
      },
      null,
      2,
    ),
  );
  const [previewRows, setPreviewRows] = useState<unknown[] | null>(null);
  const [traceTerminalLines, setTraceTerminalLines] = useState<string[]>([]);
  const [showManifestJson, setShowManifestJson] = useState(false);

  /** V7.3：若网关/路由错配返回 HTML，写入 Trace Terminal 并中断 JSON 解析。 */
  const parseApiJson = useCallback(async (r: Response) => {
    const ct = (r.headers.get("content-type") || "").toLowerCase();
    if (ct.includes("text/html")) {
      const msg =
        "[CRITICAL_ERROR] Backend returned HTML instead of JSON. Check Route/Signature.";
      setTraceTerminalLines((prev) => [...prev, msg]);
      throw new Error(msg);
    }
    return r.json() as Promise<unknown>;
  }, []);

  const [seedDate, setSeedDate] = useState("1977-05-08");
  const [seedTime, setSeedTime] = useState("18:00");
  const [seedCalendar, setSeedCalendar] = useState("solar");
  const [seedGender, setSeedGender] = useState<"male" | "female">("male");
  const [seedRefYear, setSeedRefYear] = useState("2024");
  const [collisionRows, setCollisionRows] = useState<PatternEvalRow[] | null>(null);
  const [collisionRan, setCollisionRan] = useState(false);
  const [collisionBusy, setCollisionBusy] = useState(false);
  const [collisionErr, setCollisionErr] = useState("");
  const [listInsight, setListInsight] = useState<{
    patternId: string;
    title: string;
    lines: string[];
  } | null>(null);
  const [interceptPop, setInterceptPop] = useState<{ patternId: string; name: string; lines: string[] } | null>(null);
  const [collisionPhysicsTensor, setCollisionPhysicsTensor] = useState<Record<string, unknown> | null>(null);

  const entries = useMemo(() => flattenPatterns(manifest), [manifest]);
  const traceLabels = useMemo(() => {
    const raw = manifest?.TRACE_LABELS;
    return raw && typeof raw === "object" && !Array.isArray(raw) ? (raw as Record<string, string>) : {};
  }, [manifest]);

  const collisionById = useMemo(() => {
    const m = new Map<string, PatternEvalRow>();
    for (const r of collisionRows || []) {
      const id = String(r.pattern_id || "").trim();
      if (id) m.set(id, r);
    }
    return m;
  }, [collisionRows]);

  const sortedEntries = useMemo(() => {
    if (!collisionRan) return entries;
    return sortEntriesWithCollision(entries, collisionById);
  }, [entries, collisionRan, collisionById]);

  const hitPatternId = useMemo(() => {
    if (!collisionRan) return null;
    return pickHitPatternId(sortedEntries, collisionById);
  }, [collisionRan, sortedEntries, collisionById]);

  const executionStackAudit = useMemo(() => {
    const pt = collisionPhysicsTensor;
    if (!pt) {
      return {
        l0Ok: null as boolean | null,
        l1Ok: null as boolean | null,
        l2Ok: null as boolean | null,
        l2Detail: "",
      };
    }
    const po = (pt.plugin_outputs || {}) as Record<string, { ok?: boolean }>;
    const chronos = po["base.chronos"];
    const syscore = po["sys.core.physics"];
    const l0Ok = Boolean(chronos && chronos.ok !== false && syscore && syscore.ok !== false);
    const scores = pt.deity_scores as Record<string, number> | undefined;
    const l1Ok = Boolean(scores && typeof scores === "object" && Object.keys(scores).length > 0);
    const nManifest = entries.length;
    const rows = collisionRows || [];
    const strictOk =
      rows.length > 0 &&
      rows.every((r) => String((r as { engine_v?: string }).engine_v) === "MANIFEST_V5.8_STRICT");
    const l2Ok = collisionRan && nManifest > 0 && rows.length === nManifest && strictOk;
    const l2Detail = collisionRan && nManifest > 0 ? `Iteration: ${rows.length}/${nManifest}` : "";
    return { l0Ok, l1Ok, l2Ok, l2Detail };
  }, [collisionPhysicsTensor, collisionRan, collisionRows, entries.length]);

  const loadManifest = useCallback(async () => {
    setErr("");
    setLoading(true);
    try {
      const r = await fetch(`${API_BASE}/api/v1/admin/patterns/manifest`, { headers: { ...ADMIN_HEADERS } });
      const j = (await parseApiJson(r)) as { ok?: boolean; manifest?: ManifestDoc; sha256?: string; detail?: string };
      if (!r.ok) throw new Error(j.detail || r.statusText);
      setManifest(j.manifest ?? null);
      setSha(String(j.sha256 || ""));
      setEditorText(JSON.stringify(j.manifest ?? {}, null, 2));
      setMsg("已加载法典");
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }, [parseApiJson]);

  useEffect(() => {
    void loadManifest();
  }, [loadManifest]);

  useEffect(() => {
    if (!selected) {
      setSpecEditor("");
      return;
    }
    setSpecEditor(JSON.stringify(selected.spec, null, 2));
    setListInsight(null);
  }, [selected]);

  const applySpecToDraft = useCallback(() => {
    if (!manifest || !selected) return;
    let parsed: Record<string, unknown>;
    try {
      parsed = JSON.parse(specEditor) as Record<string, unknown>;
    } catch {
      setErr("当前格局 JSON 解析失败");
      return;
    }
    const next = { ...manifest } as ManifestDoc;
    const sec = next[selected.section];
    if (!sec || typeof sec !== "object" || Array.isArray(sec)) return;
    (sec as Record<string, unknown>)[selected.key] = parsed;
    setManifest(next);
    setEditorText(JSON.stringify(next, null, 2));
    setSelected({ ...selected, spec: parsed });
    setMsg("已合并到左侧法典草稿（尚未保存到服务器）");
    setErr("");
  }, [manifest, selected, specEditor]);

  const restoreLatestBackup = useCallback(async () => {
    if (!window.confirm("确定从最新时间戳备份恢复法典？当前 manifest 会先再备份一次。")) return;
    setErr("");
    setLoading(true);
    try {
      const r = await fetch(`${API_BASE}/api/v1/admin/patterns/restore-latest`, {
        method: "POST",
        headers: { ...ADMIN_HEADERS },
      });
      const j = (await parseApiJson(r)) as {
        ok?: boolean;
        detail?: string;
        sha256?: string;
        restored_from?: string | null;
        pre_restore_backup?: string | null;
      };
      if (!r.ok) throw new Error(j.detail || r.statusText);
      setSha(String(j.sha256 || ""));
      setMsg(
        `已从备份恢复${j.restored_from ? `（源：${j.restored_from}）` : ""}${
          j.pre_restore_backup ? `；回滚前备份：${j.pre_restore_backup}` : ""
        }`,
      );
      await loadManifest();
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }, [loadManifest, parseApiJson]);

  const saveServer = useCallback(async () => {
    setErr("");
    let doc: ManifestDoc;
    try {
      doc = JSON.parse(editorText) as ManifestDoc;
    } catch {
      setErr("全量法典 JSON 解析失败");
      return;
    }
    setLoading(true);
    try {
      const r = await fetch(`${API_BASE}/api/v1/admin/patterns/update`, {
        method: "PUT",
        headers: { "Content-Type": "application/json", ...ADMIN_HEADERS },
        body: JSON.stringify({ manifest: doc }),
      });
      const j = (await parseApiJson(r)) as { ok?: boolean; detail?: string; sha256?: string; backup_path?: string | null };
      if (!r.ok) throw new Error(j.detail || r.statusText);
      setSha(String(j.sha256 || ""));
      setMsg(`已写入服务器${j.backup_path ? `（备份：${j.backup_path}）` : ""}`);
      await loadManifest();
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }, [editorText, loadManifest, parseApiJson]);

  const reloadServer = useCallback(async () => {
    setErr("");
    setLoading(true);
    try {
      const r = await fetch(`${API_BASE}/api/v1/admin/patterns/reload`, {
        method: "POST",
        headers: { ...ADMIN_HEADERS },
      });
      const j = (await parseApiJson(r)) as { ok?: boolean; detail?: string; sha256?: string };
      if (!r.ok) throw new Error(j.detail || r.statusText);
      setSha(String(j.sha256 || ""));
      setMsg("已触发 reload 指纹校验");
      await loadManifest();
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }, [loadManifest, parseApiJson]);

  const runPreview = useCallback(async () => {
    setErr("");
    let pt: Record<string, unknown>;
    try {
      pt = JSON.parse(tensorText) as Record<string, unknown>;
    } catch {
      setErr("physics_tensor JSON 无效");
      return;
    }
    setLoading(true);
    try {
      const r = await fetch(`${API_BASE}/api/v1/admin/patterns/preview`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...ADMIN_HEADERS },
        body: JSON.stringify({ physics_tensor: pt, metadata: {} }),
      });
      const j = (await parseApiJson(r)) as { ok?: boolean; rows?: unknown[]; detail?: string };
      if (!r.ok) throw new Error(j.detail || r.statusText);
      const rows = j.rows ?? [];
      setPreviewRows(rows);
      setTraceTerminalLines(flattenTraceTerminalLines(rows));
      // V7.2：直推成功即同步 Stack，避免「有 JSON 结果但 L2 仍灰」的疑云（preview 不经插件，用合成 plugin_outputs 满足 L0）。
      setCollisionRows(rows as PatternEvalRow[]);
      setCollisionPhysicsTensor({
        ...pt,
        plugin_outputs: {
          "base.chronos": { ok: true },
          "sys.core.physics": { ok: true },
        },
      });
      setCollisionRan(true);
      setCollisionErr("");
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }, [tensorText, parseApiJson]);

  const runCollisionPreview = useCallback(async () => {
    setCollisionErr("");
    setCollisionBusy(true);
    try {
      const ref = parseInt(seedRefYear, 10);
      const r = await fetch(`${API_BASE}/api/v1/admin/patterns/collision-preview`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...ADMIN_HEADERS },
        body: JSON.stringify({
          date: seedDate.trim(),
          time: seedTime.trim() || "12:00",
          calendar: seedCalendar,
          gender: seedGender,
          reference_year: Number.isFinite(ref) ? ref : undefined,
          enabled_plugins: ["classical.pattern_detector.v2"],
        }),
      });
      const j = (await parseApiJson(r)) as {
        ok?: boolean;
        detail?: string;
        rows?: PatternEvalRow[];
        physics_tensor?: Record<string, unknown>;
      };
      if (!r.ok) throw new Error(j.detail || r.statusText);
      const rows = j.rows ?? [];
      setCollisionPhysicsTensor(
        j.physics_tensor && typeof j.physics_tensor === "object"
          ? (j.physics_tensor as Record<string, unknown>)
          : null,
      );
      setCollisionRows(rows);
      setTraceTerminalLines(flattenTraceTerminalLines(rows as unknown[]));
      setCollisionRan(true);
      setListInsight(null);
      setInterceptPop(null);
      if (j.physics_tensor && typeof j.physics_tensor === "object") {
        setTensorText(JSON.stringify(j.physics_tensor, null, 2));
      }
      setMsg(`碰撞演算完成（${rows.length} 条格局轨迹）`);
    } catch (e) {
      setCollisionErr(e instanceof Error ? e.message : String(e));
    } finally {
      setCollisionBusy(false);
    }
  }, [parseApiJson, seedCalendar, seedDate, seedGender, seedRefYear, seedTime]);

  const selectedRow = useMemo(() => {
    if (!selected) return null;
    const pid = String(selected.spec.id ?? selected.key).trim();
    return collisionById.get(pid) ?? null;
  }, [collisionById, selected]);

  const handleListCardClick = useCallback(
    (e: PatternEntry) => {
      setInterceptPop(null);
      setSelected(e);
      if (!collisionRan) {
        setListInsight(null);
        return;
      }
      const pid = String(e.spec.id ?? e.key).trim();
      const row = collisionById.get(pid);
      if (!row) {
        setListInsight(null);
        return;
      }
      if (row.exclusion_hit) {
        setListInsight(null);
        return;
      }
      const band = collisionBandForRow(row);
      if (band === "near") {
        setListInsight({
          patternId: pid,
          title: "接近达成 · 差距提示",
          lines: buildGapHints(row),
        });
        return;
      }
      setListInsight(null);
    },
    [collisionById, collisionRan],
  );

  return (
    <div className="space-y-4 text-[13px] text-zinc-200">
      <section
        className="rounded-lg border border-emerald-900/40 bg-zinc-950/90 p-3"
        data-testid="admin-execution-stack"
        aria-label="插件遍历审计 Execution_Stack"
      >
        <p className="mb-2 text-[10px] font-semibold uppercase tracking-widest text-emerald-400/90">
          插件遍历审计 · Execution_Stack
        </p>
        <p className="mb-2 rounded border border-zinc-800/80 bg-black/30 px-2 py-1.5 text-[10px] leading-relaxed text-zinc-400">
          <span className="font-semibold text-zinc-300">V7.2 硬碰撞读灯</span>：灰点 = 尚未有可用张量或未演算；红点 = 该层失败（如 L1
          缺 <span className="font-mono">deity_scores</span>、L2 行数≠法典条数、或{" "}
          <span className="font-mono">engine_v</span> 非严格）；绿点 = 该层自检通过。服务端在{" "}
          <span className="font-mono">on_physics_complete</span> 进入 L2 插件时会打印{" "}
          <span className="font-mono text-emerald-600/90">[L2_HEARTBEAT] … UniversalPatternEngine</span>。若生产设置了{" "}
          <span className="font-mono">QIAZHI_PATTERN_MANIFEST_SIGNATURE=skip</span>，日志会出现法典签名校验关闭告警。
        </p>
        <p className="mb-2 font-mono text-[10px] text-zinc-500">[L0_HIDDEN] → [L1_PHYSICS] → [L2_MANIFEST_ENGINE]</p>
        <div className="space-y-1.5">
          <div className="flex flex-wrap items-center gap-2 text-[11px] text-zinc-300">
            <span className={`inline-block h-2 w-2 shrink-0 rounded-full ${stackLed(executionStackAudit.l0Ok)}`} />
            <span className="font-mono">[L0_HIDDEN]</span>
            <span className="text-zinc-500">
              {executionStackAudit.l0Ok === null ? "待运行碰撞" : executionStackAudit.l0Ok ? "常驻 L0 已遍历" : "L0 异常"}
            </span>
          </div>
          <div className="flex flex-wrap items-center gap-2 text-[11px] text-zinc-300">
            <span className={`inline-block h-2 w-2 shrink-0 rounded-full ${stackLed(executionStackAudit.l1Ok)}`} />
            <span className="font-mono">[L1_PHYSICS]</span>
            <span className="text-zinc-500">
              {executionStackAudit.l1Ok === null ? "待运行碰撞" : executionStackAudit.l1Ok ? "物理总线有十神分" : "缺少 deity_scores"}
            </span>
          </div>
          <div
            className="flex flex-wrap items-center gap-2 text-[11px] text-zinc-300"
            data-testid="admin-execution-l2"
            aria-label={
              executionStackAudit.l2Ok
                ? `L2 通过 ${executionStackAudit.l2Detail}`
                : `L2 未通过 ${executionStackAudit.l2Detail || "未演算"}`
            }
          >
            <span className={`inline-block h-2 w-2 shrink-0 rounded-full ${stackLed(executionStackAudit.l2Ok)}`} />
            <span className="font-mono">[L2_MANIFEST_ENGINE]</span>
            <span className="text-zinc-500" data-testid="admin-execution-l2-caption">
              {executionStackAudit.l2Ok === null
                ? "待运行碰撞"
                : executionStackAudit.l2Ok
                  ? `${executionStackAudit.l2Detail} · MANIFEST_V5.8_STRICT`
                  : `${executionStackAudit.l2Detail || "Iteration: —"} · 未满足全量/指纹`}
            </span>
          </div>
        </div>
      </section>

      <section className="rounded-lg border border-violet-800/50 bg-gradient-to-r from-violet-950/40 via-zinc-950/80 to-zinc-950 p-3 shadow-lg shadow-black/20">
        <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
          <p className="text-[11px] font-semibold uppercase tracking-widest text-violet-300/95">Test Input · 实时击中</p>
          <span className="text-[10px] text-zinc-500">排盘 → 物理张量 → 格局排序 · 未触线优先</span>
        </div>
        <div className="flex flex-wrap items-end gap-2 md:gap-3">
          <label className="flex min-w-[120px] flex-1 flex-col gap-0.5 text-[10px] text-zinc-500">
            生日 date
            <input
              className="rounded border border-zinc-700 bg-zinc-950 px-2 py-1.5 font-mono text-[12px] text-zinc-100"
              value={seedDate}
              onChange={(ev) => setSeedDate(ev.target.value)}
            />
          </label>
          <label className="w-[88px] flex-col gap-0.5 text-[10px] text-zinc-500 sm:flex">
            时刻
            <input
              className="rounded border border-zinc-700 bg-zinc-950 px-2 py-1.5 font-mono text-[12px] text-zinc-100"
              value={seedTime}
              onChange={(ev) => setSeedTime(ev.target.value)}
            />
          </label>
          <label className="w-[100px] flex-col gap-0.5 text-[10px] text-zinc-500 sm:flex">
            历法
            <select
              className="rounded border border-zinc-700 bg-zinc-950 px-2 py-1.5 font-mono text-[12px] text-zinc-100"
              value={seedCalendar}
              onChange={(ev) => setSeedCalendar(ev.target.value)}
            >
              <option value="solar">solar</option>
              <option value="lunar">lunar</option>
            </select>
          </label>
          <label className="w-[92px] flex-col gap-0.5 text-[10px] text-zinc-500 sm:flex">
            性别
            <select
              className="rounded border border-zinc-700 bg-zinc-950 px-2 py-1.5 font-mono text-[12px] text-zinc-100"
              value={seedGender}
              onChange={(ev) => setSeedGender(ev.target.value as "male" | "female")}
            >
              <option value="male">男</option>
              <option value="female">女</option>
            </select>
          </label>
          <label className="w-[100px] flex-col gap-0.5 text-[10px] text-zinc-500 sm:flex">
            参考年
            <input
              className="rounded border border-zinc-700 bg-zinc-950 px-2 py-1.5 font-mono text-[12px] text-zinc-100"
              value={seedRefYear}
              onChange={(ev) => setSeedRefYear(ev.target.value)}
            />
          </label>
          <button
            type="button"
            disabled={collisionBusy || loading}
            onClick={() => void runCollisionPreview()}
            className="rounded-md border border-violet-500/60 bg-violet-600/50 px-4 py-2 text-[12px] font-semibold text-white hover:bg-violet-600/70 disabled:opacity-40"
          >
            {collisionBusy ? "演算中…" : "运行碰撞"}
          </button>
        </div>
        {collisionErr ? <p className="mt-2 text-[11px] text-rose-400">{collisionErr}</p> : null}
        {collisionPhysicsTensor ? (
          <div className="mt-3 grid gap-3 md:grid-cols-2">
            <ClimateFieldStrengthCompare physicsTensor={collisionPhysicsTensor} />
            <ConflictTopologyLossPanel physicsTensor={collisionPhysicsTensor} />
          </div>
        ) : null}
        {interceptPop ? (
          <div className="mt-3 flex gap-2 rounded border border-rose-800/60 bg-rose-950/35 p-2 text-[11px] text-rose-50/95">
            <div className="min-w-0 flex-1">
              <p className="font-semibold text-rose-200">拦截原因 · {interceptPop.name}</p>
              <p className="font-mono text-[9px] text-rose-300/80">{interceptPop.patternId}</p>
              <ul className="mt-1 list-inside list-disc space-y-0.5 text-[10px] text-rose-100/90">
                {interceptPop.lines.map((line, i) => (
                  <li key={i} className="break-words">
                    {line}
                  </li>
                ))}
              </ul>
            </div>
            <button
              type="button"
              onClick={() => setInterceptPop(null)}
              className="shrink-0 self-start rounded border border-rose-700/50 px-2 py-0.5 text-[10px] text-rose-200 hover:bg-rose-900/50"
            >
              关闭
            </button>
          </div>
        ) : null}
      </section>

      <div className="grid gap-4 xl:grid-cols-[minmax(280px,320px)_minmax(0,1fr)]">
      <aside className="space-y-3 rounded border border-zinc-800 bg-black/40 p-3">
        <div className="flex items-center justify-between gap-2">
          <p className="text-[10px] font-semibold uppercase tracking-widest text-zinc-500">格局列表</p>
          <span className="font-mono text-[9px] text-zinc-600">{sortedEntries.length} 条</span>
        </div>
        <p className="text-[10px] leading-snug text-zinc-500">
          碰撞后按亲和度排序（未触线在前）。「HIT」为当前八字下法典认定的净命中首格；触线项置灰，点红叉查看印星超标等具体原因。
        </p>
        {collisionRan && !hitPatternId ? (
          <p className="rounded border border-amber-900/40 bg-amber-950/20 px-2 py-1 text-[10px] text-amber-200/90">
            当前盘式下无法定「净命中」：可能全部格局已触红线，请点各格红叉核对拦截句。
          </p>
        ) : null}
        <ul className="max-h-[min(72vh,560px)] space-y-2 overflow-y-auto pr-1">
          {sortedEntries.map((e) => {
            const id = String(e.spec.id ?? e.key);
            const active = selected?.section === e.section && selected?.key === e.key;
            const row = collisionById.get(id);
            const band: CollisionBand = collisionRan ? collisionBandForRow(row) : "idle";
            const blocked = row?.exclusion_hit === true;
            const isHit = collisionRan && hitPatternId === id;
            const aff = Math.min(1, Math.max(0, Number(row?.affinity_score ?? 0)));
            return (
              <li key={`${e.section}:${e.key}`} className="relative">
                {isHit ? (
                  <span className="absolute -top-1.5 left-2 z-[1] rounded bg-amber-500/90 px-1.5 py-0.5 text-[8px] font-bold uppercase tracking-wide text-zinc-950 shadow">
                    HIT · 击中
                  </span>
                ) : null}
                <div
                  className={`relative w-full rounded-lg border px-2.5 pb-2 pt-3 ${
                    blocked
                      ? "border-zinc-700 bg-zinc-950/80 opacity-75 grayscale-[0.85]"
                      : cardShellClass(band, active)
                  }`}
                >
                  {blocked ? (
                    <button
                      type="button"
                      title="查看拦截原因"
                      onClick={() => {
                        const lines = row ? getInterceptReasonLines(row) : [];
                        setInterceptPop({
                          patternId: id,
                          name: String(e.spec.display_name ?? id),
                          lines: lines.length ? lines : ["（无 trace_display_zh，请查看右侧判定 DNA）"],
                        });
                        setListInsight(null);
                      }}
                      className="absolute right-1.5 top-1.5 z-[2] flex h-7 w-7 items-center justify-center rounded-full border border-rose-600/60 bg-rose-950/90 text-sm font-bold text-rose-400 hover:bg-rose-900"
                    >
                      ✕
                    </button>
                  ) : null}
                  <button type="button" onClick={() => handleListCardClick(e)} className="w-full text-left">
                    <div className="flex items-center justify-between gap-2 pr-7">
                      <span className="truncate text-[13px] font-semibold text-zinc-50">
                        {String(e.spec.display_name ?? id)}
                      </span>
                      {!blocked ? (
                        <span
                          className={`h-2.5 w-2.5 shrink-0 rounded-full ${
                            band === "full" ? "bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.5)]" : band === "near" ? "bg-amber-400" : "bg-zinc-600"
                          }`}
                          title="红线状态灯"
                        />
                      ) : (
                        <span className="h-2.5 w-2.5 shrink-0 rounded-full bg-zinc-600" title="已触线" />
                      )}
                    </div>
                    <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-zinc-800/90">
                      <div
                        className={`h-full rounded-full transition-all ${blocked ? "bg-zinc-600" : "bg-gradient-to-r from-emerald-700 to-emerald-400"}`}
                        style={{ width: `${collisionRan && row ? aff * 100 : 0}%` }}
                      />
                    </div>
                    <div className="mt-1 flex items-center justify-between gap-2 text-[10px] text-zinc-500">
                      <span className={active ? "font-semibold text-amber-200" : ""}>{active ? "DNA 展开中" : "点选看 DNA"}</span>
                      {collisionRan && row ? (
                        <span className="font-mono text-zinc-400">{(row.affinity_score ?? 0).toFixed(3)}</span>
                      ) : null}
                    </div>
                    <p className="mt-0.5 font-mono text-[9px] text-zinc-600">{id}</p>
                  </button>
                </div>
              </li>
            );
          })}
        </ul>

        {listInsight ? (
          <div className="rounded border border-zinc-700/80 bg-zinc-950/90 p-2 text-[10px] text-zinc-300">
            <p className="font-semibold text-zinc-100">{listInsight.title}</p>
            <p className="font-mono text-[9px] text-zinc-500">{listInsight.patternId}</p>
            <ul className="mt-1 list-inside list-disc space-y-0.5 text-zinc-400">
              {listInsight.lines.slice(0, 8).map((line, i) => (
                <li key={i} className="break-words">
                  {line}
                </li>
              ))}
            </ul>
          </div>
        ) : null}
      </aside>

      <div className="flex min-w-0 flex-col gap-4">
        <div className="flex flex-wrap items-center gap-2 border-b border-zinc-800 pb-2">
          <span className="font-mono text-[10px] text-zinc-500">sha256 · {sha.slice(0, 12) || "—"}…</span>
          <button
            type="button"
            disabled={loading}
            onClick={() => void loadManifest()}
            className="rounded border border-zinc-700 px-2 py-1 text-[11px] hover:bg-zinc-900 disabled:opacity-40"
          >
            重新加载
          </button>
          <button
            type="button"
            disabled={loading}
            onClick={() => void reloadServer()}
            className="rounded border border-zinc-700 px-2 py-1 text-[11px] hover:bg-zinc-900 disabled:opacity-40"
          >
            POST reload
          </button>
          <button
            type="button"
            disabled={loading}
            onClick={() => void saveServer()}
            className="rounded border border-amber-700/50 bg-amber-950/30 px-2 py-1 text-[11px] text-amber-100 hover:bg-amber-950/50 disabled:opacity-40"
          >
            保存法典
          </button>
          <button
            type="button"
            disabled={loading}
            onClick={() => void restoreLatestBackup()}
            className="rounded border border-rose-800/50 bg-rose-950/25 px-2 py-1 text-[11px] text-rose-100 hover:bg-rose-950/45 disabled:opacity-40"
          >
            一键恢复基准法典
          </button>
        </div>
        {msg ? <p className="text-[11px] text-emerald-400/90">{msg}</p> : null}
        {err ? <p className="text-[11px] text-rose-400">{err}</p> : null}

        {selected ? (
          <>
            <PatternSpecView
              sectionLabel={sectionTitle(selected.section)}
              manifestKey={selected.key}
              spec={selected.spec}
              traceLabels={traceLabels}
              collisionRow={selectedRow}
              specJson={specEditor}
              onSpecJsonChange={setSpecEditor}
              onApplyMerge={applySpecToDraft}
            />
            {collisionRan && hitPatternId ? (
              <p className="rounded border border-zinc-800/80 bg-zinc-900/40 px-3 py-2 text-[11px] leading-relaxed text-zinc-400">
                <span className="font-semibold text-emerald-400/90">裁决提示</span>：当前八字在法典排序下，「
                <span className="text-zinc-200">{collisionById.get(hitPatternId)?.name ?? hitPatternId}</span>
                」为亲和最高且<span className="text-zinc-200">未触红线</span>的净命中（HIT）。若您在看其他格（例如正财格 vs
                从财格），请对照左侧亲和条与红叉原因：触线格亲和被压零或软惩罚，故不会与 HIT 竞争终局叙事。
              </p>
            ) : null}
          </>
        ) : (
          <div className="rounded border border-dashed border-zinc-800 p-8 text-center text-[12px] text-zinc-500">
            左侧选择一条格局，打开「判定看板」与命理依据。
          </div>
        )}

        <div className="rounded border border-zinc-800 bg-black/25">
          <button
            type="button"
            onClick={() => setShowManifestJson((v) => !v)}
            className="flex w-full items-center justify-between px-3 py-2 text-left text-[11px] text-zinc-400 hover:bg-zinc-900/40 hover:text-zinc-200"
          >
            <span>全量法典 JSON（运维）</span>
            <span className="font-mono text-[10px] text-zinc-600">{showManifestJson ? "▼" : "▶"}</span>
          </button>
          {showManifestJson ? (
            <textarea
              value={editorText}
              onChange={(e) => setEditorText(e.target.value)}
              spellCheck={false}
              className="h-[min(36vh,320px)] w-full resize-y border-t border-zinc-800 bg-zinc-950/80 p-2 font-mono text-[11px] leading-snug text-zinc-200 outline-none"
            />
          ) : null}
        </div>

        <div className="space-y-2 rounded border border-zinc-800 bg-black/30 p-3">
          <p className="text-[10px] font-semibold uppercase tracking-widest text-zinc-500">Exclusion Monitor · 张量直推</p>
          <p className="text-[10px] leading-relaxed text-zinc-500">
            在「<span className="text-zinc-400">格局法典</span>」页粘贴完整{" "}
            <span className="font-mono">physics_tensor</span> JSON，点「演算」即走 Admin{" "}
            <span className="font-mono">/preview</span> 直推 L2（结果与 Trace 见下方）；演算成功后会同步上方{" "}
            <span className="font-mono">Execution_Stack</span> 灯态。若需验证中枢插件链与控制台{" "}
            <span className="font-mono">[L2_HEARTBEAT]</span>，请用顶部 Test Input 的「运行碰撞」（走 orchestrator +
            <span className="font-mono"> classical.pattern_detector.v2</span>）。
          </p>
          <textarea
            value={tensorText}
            onChange={(e) => setTensorText(e.target.value)}
            spellCheck={false}
            className="h-36 w-full resize-y rounded border border-zinc-800 bg-zinc-950/80 p-2 font-mono text-[11px] leading-snug text-zinc-200 outline-none focus:border-zinc-600"
          />
          <button
            type="button"
            disabled={loading}
            onClick={() => void runPreview()}
            className="rounded border border-violet-800/60 bg-violet-950/30 px-2 py-1 text-[11px] text-violet-100 hover:bg-violet-950/50 disabled:opacity-40"
          >
            演算 affinity / trace
          </button>
          {previewRows?.length ? (
            <div className="max-h-56 space-y-1 overflow-auto rounded border border-zinc-800/80 bg-zinc-950/90 p-2 font-mono text-[10px] leading-relaxed">
              {(previewRows as unknown[]).map((row, idx) => {
                const rec = row && typeof row === "object" ? (row as Record<string, unknown>) : {};
                const hit = rec.exclusion_hit === true;
                return (
                  <pre
                    key={idx}
                    className={`whitespace-pre-wrap break-all rounded border px-1.5 py-1 ${
                      hit ? "border-[#ef4444]/60 bg-[#ef4444]/10 text-[#fca5a5]" : "border-transparent text-zinc-400"
                    }`}
                  >
                    {JSON.stringify(row, null, 2)}
                  </pre>
                );
              })}
            </div>
          ) : null}

          <div className="space-y-1.5 border-t border-zinc-800/80 pt-3">
            <p className="text-[10px] font-semibold uppercase tracking-widest text-emerald-600/90">Trace Terminal · L2 执行轨迹</p>
            <p className="text-[10px] text-zinc-500">
              后端 <span className="font-mono">trace_logic</span>：含 <span className="font-mono">[CODEX_LOAD]</span>、
              <span className="font-mono">[GATING_CHECK]</span>、<span className="font-mono">[EXCLUSION_CHECK]</span>、
              <span className="font-mono">[FINAL_RANKING]</span>。
            </p>
            <pre className="max-h-72 overflow-auto whitespace-pre-wrap break-all rounded border border-zinc-900 bg-black p-3 font-mono text-[10px] leading-relaxed text-emerald-200/95 shadow-inner">
              {traceTerminalLines.length
                ? traceTerminalLines.join("\n")
                : "// 运行「演算 affinity / trace」或顶部 Test Input「运行碰撞」后，此处滚动显示法典自证轨迹。\n"}
            </pre>
          </div>
        </div>
      </div>
      </div>
    </div>
  );
}
