"use client";

import { useCallback, useEffect, useState, type Dispatch, type SetStateAction } from "react";

type TabKey = "llm" | "db" | "plugins" | "physics" | "evolution";

type LlmNode = {
  provider: string;
  host: string;
  port: number;
  model: string;
  httpTimeoutSec: number;
  fuseWaitSec: number;
};

type DbBridge = {
  driver: string;
  host: string;
  port: number;
  database: string;
  username: string;
  password: string;
  sslmode: string;
  url: string;
  enabled: boolean;
};

type PluginAdminRow = {
  layer: string;
  layer_dir: string;
  module: string;
  plugin_id: string;
  display_name?: string;
  display_definition?: string;
  display_description?: string;
  technical_label?: string;
  family_label?: string;
  causal_tier: number;
  power_tier?: number;
  execution_order?: number;
  registry_priority?: number;
  kind: string;
  last_facts?: string[];
  last_at?: string;
  activated?: boolean;
  causal_active_path?: boolean;
  function_summary?: string;
  design_rationale?: string;
  causal_trace_text?: string;
  executed_before_plugin_ids?: string[];
  module_doc?: string;
  spec_doc?: string;
  definition_text?: string;
  trigger_condition_text?: string;
  detail_description?: string;
  declared_params?: Record<string, unknown>;
  skill_manifest?: Record<string, unknown>;
  is_standard_skill?: boolean;
};

function pluginCardTitle(row: PluginAdminRow): string {
  return String(row.display_name || row.definition_text || row.plugin_id || "未命名插件").trim();
}

function pluginCardDefinition(row: PluginAdminRow): string {
  return String(row.display_definition || row.definition_text || row.function_summary || row.plugin_id || "").trim();
}

function pluginCardDescription(row: PluginAdminRow): string {
  return String(row.display_description || row.detail_description || row.design_rationale || "暂无补充说明。").trim();
}

type PluginRuntimeStatus = {
  plugin_id: string;
  fact_count?: number;
  proposal_count?: number;
  decision_count?: number;
  status?: string;
  target_god?: string;
  reason?: string;
};

type PluginClaim = {
  claim_id: string;
  plugin_id: string;
  target_god?: string;
  logic_level?: string;
  claim_type?: string;
  source_event?: string;
};

type PluginConflict = {
  conflict_id: string;
  conflict_type?: string;
  severity?: string;
  conflict_score?: number;
  confidence_band?: string;
  source_event?: string;
  claims?: string[];
  plugins?: string[];
  target_god?: string;
  why_conflict?: string;
  recommended_arbiter?: string;
  resolution_status?: string;
};

type PluginConflictResolution = {
  conflict_id: string;
  resolved_by?: string;
  policy?: string;
  winner_claim_id?: string;
  applied_to_settlement?: boolean;
  next_queue?: string;
  reason?: string;
  status?: string;
};

type KnowledgeSnapshot = {
  claim_history?: {
    total_claims?: number;
    by_type?: Record<string, number>;
    top_targets?: Array<{ target_god?: string; count?: number }>;
  };
  conflict_history?: {
    total_conflicts?: number;
    by_type?: Record<string, number>;
    recommended_arbiters?: Record<string, number>;
    feedback_arbiters?: Record<string, number>;
    feedback_arbiter_scores?: Record<string, number>;
  };
  resolution_preview?: {
    total_suggestions?: number;
    resolved_by?: Record<string, number>;
  };
};

type BrainAction = {
  action_id?: string;
  conflict_id?: string;
  action_type?: string;
  queue?: string;
  confidence?: number;
  reason?: string;
  source_plugins?: string[];
};

type PluginPanelRow = {
  plugin: PluginAdminRow;
  runtime?: PluginRuntimeStatus;
  relatedClaims: PluginClaim[];
  relatedConflicts: PluginConflict[];
};

const LAYER_TABS: { key: string; label: string }[] = [
  { key: "L0", label: "L0 基础场" },
  { key: "L1", label: "L1 原子算子" },
  { key: "L2", label: "L2 格局做功" },
  { key: "L3", label: "L3 现代叙事" },
];

const KIND_LABELS: Record<string, string> = {
  spec: "标准插件",
  manifest_row: "清单挂载插件",
};

function tierLabel(tier: number | undefined) {
  const value = Number(tier || 0);
  if (value >= 5) return "最接近物理核";
  if (value === 4) return "高强度原子层";
  if (value === 3) return "结构判定层";
  if (value === 2) return "叙事辅助层";
  if (value === 1) return "话术收束层";
  return "未标注";
}

type ActionKey = "loadModels" | "testLlm" | "testLlmChat" | "saveLlm" | "testDb" | "saveDb" | "loadPlugins" | "savePhysics" | "loadEvolution" | null;
type LooseObject = Record<string, unknown>;
const ORACLE_SESSION_STORAGE_KEY = "v17.oracle.current_session_id";

async function requestJson(url: string, init?: RequestInit) {
  const resp = await fetch(url, init);
  const text = await resp.text();
  let data: unknown = {};
  try {
    data = text ? JSON.parse(text) : {};
  } catch {
    data = { ok: false, error: text.slice(0, 200) || "non-json response" };
  }
  return { resp, data };
}

function applyLlmNodeToState(llmNode: LooseObject | null, setLlm: Dispatch<SetStateAction<LlmNode>>) {
  if (!llmNode) return;
  const baseUrl = String(llmNode.base_url || "");
  let host = "127.0.0.1";
  let port = 11434;
  try {
    const parsed = new URL(baseUrl);
    host = parsed.hostname || host;
    port = Number(parsed.port || (parsed.protocol === "https:" ? 443 : 11434));
  } catch {}
  const httpRaw = Number(llmNode.http_timeout_sec);
  const fuseRaw = Number(llmNode.fuse_wait_timeout_sec);
  setLlm({
    provider: String(llmNode.provider || "ollama"),
    host,
    port,
    model: String(llmNode.model || ""),
    httpTimeoutSec: Number.isFinite(httpRaw) && httpRaw > 0 ? httpRaw : 15,
    fuseWaitSec: Number.isFinite(fuseRaw) && fuseRaw > 0 ? fuseRaw : 30,
  });
}

function normalizePluginKey(value: string | undefined): string {
  return String(value || "").trim().toLowerCase();
}

function conflictTone(severity: string | undefined): string {
  const value = String(severity || "").trim().toUpperCase();
  if (value === "P1") return "bg-rose-900/40 text-rose-300";
  if (value === "P2") return "bg-amber-900/40 text-amber-300";
  return "bg-cyan-900/40 text-cyan-300";
}

function brainStepTone(kind: string | undefined): string {
  const value = String(kind || "").trim().toLowerCase();
  if (value.includes("manual") || value === "user") return "text-violet-300";
  if (value.includes("system")) return "text-amber-300";
  if (value.includes("llm")) return "text-cyan-300";
  return "text-zinc-400";
}

type ConflictMergeGroup = {
  key: string;
  conflict_type: string;
  severity: string;
  target_god: string;
  recommended_arbiter: string;
  conflicts: PluginConflict[];
  conflict_ids: string[];
  max_conflict_score: number;
};

function isConflictPending(
  conflict: PluginConflict,
  resolution?: PluginConflictResolution | undefined,
) {
  const status = String(conflict.resolution_status || "").trim().toLowerCase();
  if (status) {
    if (status === "approved" || status === "resolved_system") return false;
    if (status.startsWith("queued_")) return false;
  }

  const resolutionStatus = String(resolution?.status || "").trim().toLowerCase();
  if (resolutionStatus) {
    if (resolutionStatus === "approved" || resolutionStatus === "resolved_system") return false;
    if (resolutionStatus.startsWith("queued_")) return false;
  }
  return true;
}

function conflictMergeKey(row: PluginConflict) {
  const target = String(row.target_god || "未定目标").trim();
  const severity = String(row.severity || "P3").trim().toUpperCase();
  const type = String(row.conflict_type || "unknown").trim().toLowerCase();
  const arbiter = String(row.recommended_arbiter || "system").trim().toLowerCase();
  return `${type}#${target}#${severity}#${arbiter}`;
}

function buildConflictGroups(
  conflicts: PluginConflict[],
  resolutions: PluginConflictResolution[],
): ConflictMergeGroup[] {
  const resolutionByConflict = new Map<string, PluginConflictResolution>();
  for (const resolution of resolutions || []) {
    const conflictId = String(resolution.conflict_id || "").trim();
    if (conflictId) resolutionByConflict.set(conflictId, resolution);
  }

  const bucket: Record<string, ConflictMergeGroup> = {};
  for (const row of conflicts || []) {
    const conflictId = String(row.conflict_id || "").trim();
    if (!conflictId) continue;
    const resolution = resolutionByConflict.get(conflictId);
    if (!isConflictPending(row, resolution)) {
      continue;
    }
    const key = conflictMergeKey(row);
    if (!bucket[key]) {
      bucket[key] = {
        key,
        conflict_type: String(row.conflict_type || "unknown").trim(),
        severity: String(row.severity || "P3").trim(),
        target_god: String(row.target_god || "未定目标").trim(),
        recommended_arbiter: String(row.recommended_arbiter || "system").trim().toLowerCase(),
        conflicts: [],
        conflict_ids: [],
        max_conflict_score: 0,
      };
    }
    bucket[key].conflicts.push(row);
    bucket[key].conflict_ids.push(conflictId);
    bucket[key].max_conflict_score = Math.max(
      bucket[key].max_conflict_score,
      Number(row.conflict_score || 0),
    );
  }

  const grouped = Object.values(bucket).sort((a, b) => {
    const sevA = String(a.severity || "P3").toUpperCase();
    const sevB = String(b.severity || "P3").toUpperCase();
    const severityValue = { P1: 3, P2: 2, P3: 1 };
    const score = (value: string) => severityValue[value as keyof typeof severityValue] || 0;
    return (
      score(sevB) - score(sevA) ||
      b.max_conflict_score - a.max_conflict_score ||
      b.conflict_ids.length - a.conflict_ids.length ||
      b.target_god.localeCompare(a.target_god)
    );
  });

  return grouped;
}

function isInboxRuntimeStatus(status: string | undefined): boolean {
  const value = String(status || "").trim().toLowerCase();
  return new Set([
    "manual_pending",
    "manual_committed",
    "manual_rejected",
    "await_review",
    "context_pending",
    "context_consumed",
    "proposal_pending",
    "auto_applied",
  ]).has(value);
}

function isHitRuntimeStatus(status: string | undefined): boolean {
  const value = String(status || "").trim().toLowerCase();
  return value !== "" && value !== "unknown";
}

function runtimeStatusTone(status: string | undefined): string {
  const value = String(status || "").trim().toLowerCase();
  if (value === "auto_applied") return "bg-emerald-900/40 text-emerald-300";
  if (value === "manual_committed") return "bg-cyan-900/40 text-cyan-300";
  if (value === "manual_pending" || value === "await_review" || value === "proposal_pending") return "bg-amber-900/40 text-amber-300";
  if (value === "context_pending" || value === "context_consumed") return "bg-sky-900/40 text-sky-300";
  if (value === "manual_rejected") return "bg-rose-900/40 text-rose-300";
  if (value === "clamped") return "bg-fuchsia-900/40 text-fuchsia-300";
  if (value.startsWith("skipped")) return "bg-rose-900/40 text-rose-300";
  return "bg-zinc-800 text-zinc-400";
}

function runtimeStatusLabel(status: string | undefined): string {
  const value = String(status || "").trim().toLowerCase();
  if (value === "manual_pending") return "待手动处理";
  if (value === "manual_committed") return "已人工结算";
  if (value === "manual_rejected") return "已人工否决";
  if (value === "await_review") return "等待复核";
  if (value === "context_pending") return "上下文待消化";
  if (value === "context_consumed") return "上下文已消化";
  if (value === "proposal_pending") return "Proposal 待裁决";
  if (value === "auto_applied") return "自动已结算";
  if (value === "fact_only") return "仅命中事实";
  if (value === "clamped") return "护栏钳制";
  if (value === "skipped_dedup") return "重复跳过";
  if (value === "skipped_no_target") return "无目标跳过";
  return String(status || "unknown");
}

export default function V17AdminPage() {
  const [tab, setTab] = useState<TabKey>("llm");
  const [llm, setLlm] = useState<LlmNode>({ provider: "ollama", host: "192.168.0.12", port: 11434, model: "", httpTimeoutSec: 15, fuseWaitSec: 30 });
  const [db, setDb] = useState<DbBridge>({ driver: "postgres", host: "127.0.0.1", port: 5432, database: "v17_rebirth", username: "postgres", password: "", sslmode: "prefer", url: "", enabled: false });
  const [msg, setMsg] = useState("");
  const [llmModels, setLlmModels] = useState<string[]>([]);
  const [llmPrompt, setLlmPrompt] = useState("你好，请简单自我介绍。");
  const [busy, setBusy] = useState<ActionKey>(null);
  const [plugins, setPlugins] = useState<PluginAdminRow[]>([]);
  const [pluginStatuses, setPluginStatuses] = useState<PluginRuntimeStatus[]>([]);
  const [pluginClaims, setPluginClaims] = useState<PluginClaim[]>([]);
  const [pluginConflicts, setPluginConflicts] = useState<PluginConflict[]>([]);
  const [pluginConflictResolutions, setPluginConflictResolutions] = useState<PluginConflictResolution[]>([]);
  const [knowledgeSnapshot, setKnowledgeSnapshot] = useState<KnowledgeSnapshot>({});
  const [brainActionQueue, setBrainActionQueue] = useState<BrainAction[]>([]);
  const [pluginRuntimeSessionId, setPluginRuntimeSessionId] = useState("default");
  const [resolvedPluginRuntimeSessionId, setResolvedPluginRuntimeSessionId] = useState("default");
  const [selectedPlugin, setSelectedPlugin] = useState<PluginAdminRow | null>(null);
  const [physicsConstants, setPhysicsConstants] = useState<LooseObject>({});
  const [evolutionLogs, setEvolutionLogs] = useState<any[]>([]);
  const [l0Locked, setL0Locked] = useState(true);
  const [localConfig, setLocalConfig] = useState<LooseObject>({});
  const [localEnabled, setLocalEnabled] = useState(false);
  const [resolveBusyKeys, setResolveBusyKeys] = useState<string[]>([]);

  useEffect(() => {
    try {
      const stored = window.localStorage.getItem(ORACLE_SESSION_STORAGE_KEY);
      if (stored && stored.trim()) {
        setPluginRuntimeSessionId(stored.trim());
      }
    } catch {}

    const syncFromStorage = () => {
      try {
        const stored = window.localStorage.getItem(ORACLE_SESSION_STORAGE_KEY);
        if (stored && stored.trim()) {
          setPluginRuntimeSessionId(stored.trim());
        }
      } catch {}
    };

    window.addEventListener("storage", syncFromStorage);
    return () => window.removeEventListener("storage", syncFromStorage);
  }, []);

  const llmBaseUrl = `http://${llm.host}:${llm.port}/v1`;
  const ghostBtn = "cursor-pointer rounded-md border border-zinc-700 bg-zinc-900 px-4 py-2 text-sm font-semibold text-zinc-200 transition hover:border-zinc-500 hover:bg-zinc-800 disabled:opacity-50";
  const solidBtn = "cursor-pointer rounded-md bg-zinc-100 px-4 py-2 text-sm font-semibold text-zinc-900 transition hover:bg-white disabled:opacity-60";

  const loadPlugins = useCallback(async () => {
    setBusy("loadPlugins");
    try {
      const [{ data }, { data: statusData }] = await Promise.all([
        requestJson("/api/v17-admin/plugins?v17_origin=v17_rebirth"),
        requestJson(`/api/v17-admin/plugin-runtime-status?v17_origin=v17_rebirth&session_id=${encodeURIComponent(pluginRuntimeSessionId || "default")}`),
      ]);
      const list = ((data as any).plugins || []) as PluginAdminRow[];
      const statusList = ((statusData as any).statuses || []) as PluginRuntimeStatus[];
      const claimList = ((statusData as any).claims || []) as PluginClaim[];
      const conflictList = ((statusData as any).conflicts || []) as PluginConflict[];
      const resolutionList = ((statusData as any).conflict_resolutions || []) as PluginConflictResolution[];
      const knowledge = ((statusData as any).knowledge_snapshot || {}) as KnowledgeSnapshot;
      const actions = ((statusData as any).brain_action_queue || []) as BrainAction[];
      setPlugins(list);
      setPluginStatuses(statusList);
      setPluginClaims(claimList);
      setPluginConflicts(conflictList);
      setPluginConflictResolutions(resolutionList);
      setKnowledgeSnapshot(knowledge);
      setBrainActionQueue(actions);
      setResolvedPluginRuntimeSessionId(String((statusData as any).session_id || pluginRuntimeSessionId || "default"));
    } finally { setBusy(null); }
  }, [pluginRuntimeSessionId]);

  async function resolveConflictBatch(
    conflictIds: string[],
    arbiter: "system" | "llm" | "user",
    batchKey: string,
  ) {
    const ids = [...new Set((conflictIds || []).map((value) => String(value || "").trim()).filter(Boolean))];
    if (!ids.length || resolveBusyKeys.includes(batchKey)) return;
    setResolveBusyKeys((prev) => [...prev, batchKey]);
    try {
      const body: Record<string, unknown> = {
        session_id: resolvedPluginRuntimeSessionId || pluginRuntimeSessionId || "default",
        arbiter,
        v17_origin: "v17_rebirth",
      };
      if (ids.length === 1) {
        body.conflict_id = ids[0];
      } else {
        body.conflict_ids = ids;
      }

      const { resp, data } = await requestJson("/api/v17-admin/conflict-resolve", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!resp.ok || !(data as { ok?: boolean }).ok) {
        setMsg(`冲突裁决失败：${String((data as { detail?: string }).detail || "unknown error")}`);
        return;
      }
      setMsg(`已提交 ${ids.length} 条冲突给 ${arbiter.toUpperCase()}。`);
      await loadPlugins();
    } finally {
      setResolveBusyKeys((prev) => prev.filter((item) => item !== batchKey));
    }
  }

  const loadEvolution = useCallback(async () => {
    setBusy("loadEvolution");
    try {
      const { data } = await requestJson("/api/v17/admin/evolution-logs?v17_origin=v17_rebirth&limit=50");
      if ((data as any).ok) setEvolutionLogs((data as any).logs || []);
    } finally { setBusy(null); }
  }, []);

  useEffect(() => {
    void (async () => {
      const [{ data: llmData }, { data: dbData }, { data: physicsData }] = await Promise.all([
        requestJson("/api/v17-admin/llm-node?v17_origin=v17_rebirth"),
        requestJson("/api/v17-admin/db-bridge?v17_origin=v17_rebirth"),
        requestJson("/api/v17-admin/physics-constants?v17_origin=v17_rebirth"),
      ]);
      applyLlmNodeToState(((llmData as any).node || null), setLlm);
      if ((dbData as any).bridge) setDb((dbData as any).bridge);
      if ((physicsData as any).constants) setPhysicsConstants((physicsData as any).constants);
    })();
  }, []);

  useEffect(() => {
    if (tab === "plugins") loadPlugins();
    if (tab === "evolution") loadEvolution();
  }, [tab, loadPlugins, loadEvolution]);

  async function saveLlm() {
    setBusy("saveLlm");
    try {
      const { resp, data } = await requestJson("/api/v17-admin/llm-node", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...llm, base_url: llmBaseUrl, v17_origin: "v17_rebirth" }),
      });
      setMsg(resp.ok ? "LLM 配置已保存" : "保存失败");
    } finally { setBusy(null); }
  }

  async function savePhysics() {
    setBusy("savePhysics");
    try {
      await requestJson("/api/v17-admin/physics-constants", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ constants: physicsConstants, v17_origin: "v17_rebirth" }),
      });
      setMsg("物理定律已同步");
    } finally { setBusy(null); }
  }

  const brainTimeline = pluginConflicts.slice(0, 10).map((conflict) => {
    const conflictId = String(conflict.conflict_id || "").trim();
    const resolution = pluginConflictResolutions.find((item) => item.conflict_id === conflictId);
    const action = brainActionQueue.find((item) => String(item.conflict_id || "").trim() === conflictId);
    return { conflict, resolution, action };
  }).filter((row) => String(row.conflict.conflict_id || "").trim());

  const pluginPanelRows: PluginPanelRow[] = plugins.map((plugin) => {
    const pluginKey = normalizePluginKey(plugin.plugin_id);
    const moduleKey = normalizePluginKey(plugin.module);
    const runtime = pluginStatuses.find((row) => {
      const statusKey = normalizePluginKey(row.plugin_id);
      return statusKey === pluginKey || (statusKey && moduleKey && (statusKey === moduleKey || statusKey.endsWith(`.${moduleKey}`) || moduleKey.endsWith(`.${statusKey}`)));
    });
    const relatedClaims = pluginClaims.filter((row) => {
      const rowKey = normalizePluginKey(row.plugin_id);
      return rowKey === pluginKey || (rowKey && moduleKey && (rowKey === moduleKey || rowKey.endsWith(`.${moduleKey}`) || moduleKey.endsWith(`.${rowKey}`)));
    });
    const relatedConflicts = pluginConflicts.filter((row) => {
      const rows = Array.isArray(row.plugins) ? row.plugins : [];
      return rows.some((item) => {
        const itemKey = normalizePluginKey(item);
        return itemKey === pluginKey || (itemKey && moduleKey && (itemKey === moduleKey || itemKey.endsWith(`.${moduleKey}`) || moduleKey.endsWith(`.${itemKey}`)));
      });
    });
    return { plugin, runtime, relatedClaims, relatedConflicts };
  });
  const scannedPluginCount = pluginPanelRows.length;
  const hitPluginRows = pluginPanelRows.filter((row) => {
    const factCount = Number(row.runtime?.fact_count || 0);
    return factCount > 0 || isHitRuntimeStatus(row.runtime?.status) || row.plugin.activated;
  });
  const inboxPluginRows = pluginPanelRows.filter((row) => {
    const decisionCount = Number(row.runtime?.decision_count || 0);
    return decisionCount > 0 || isInboxRuntimeStatus(row.runtime?.status);
  });

  return (
    <main className="min-h-screen bg-zinc-950 text-zinc-100 font-sans p-6 text-sm">
      <div className="mx-auto max-w-7xl grid grid-cols-1 md:grid-cols-[240px_1fr] gap-6">
        <aside className="space-y-2">
          <h1 className="text-sm font-bold text-zinc-500 mb-6 px-4">V17 CEREBRUM ADMIN</h1>
          {[
            { id: "llm", label: "LLM 节点", icon: "🧠" },
            { id: "db", label: "数据库桥接", icon: "💎" },
            { id: "plugins", label: "插件链", icon: "🧬" },
            { id: "physics", label: "宇宙常数", icon: "⚛️" },
            { id: "evolution", label: "演化审计", icon: "📜" },
          ].map((t) => (
            <button key={t.id} onClick={() => setTab(t.id as TabKey)} className={`w-full text-left px-4 py-2.5 rounded-xl transition ${tab === t.id ? "bg-zinc-100 text-black font-bold" : "text-zinc-400 hover:bg-zinc-900"}`}>
              {t.icon} <span className="ml-2">{t.label}</span>
            </button>
          ))}
        </aside>

        <div className="bg-zinc-900/50 border border-zinc-800 rounded-2xl p-6 min-h-[600px]">
          {tab === "llm" && (
            <div className="space-y-4">
              <h2 className="text-lg font-bold border-b border-zinc-800 pb-2">LLM Node Config</h2>
              <div className="grid grid-cols-2 gap-4">
                <input className="bg-zinc-950 border border-zinc-800 p-2 rounded" placeholder="Host" value={llm.host} onChange={e => setLlm(s => ({...s, host: e.target.value}))} />
                <input className="bg-zinc-950 border border-zinc-800 p-2 rounded" placeholder="Port" value={llm.port} onChange={e => setLlm(s => ({...s, port: Number(e.target.value)}))} />
              </div>
              <button onClick={saveLlm} className={solidBtn}>Save LLM Config</button>
            </div>
          )}

          {tab === "physics" && (
            <div className="space-y-4">
              <h2 className="text-lg font-bold border-b border-zinc-800 pb-2">V17 Physics Constants</h2>
              <button onClick={() => setL0Locked(!l0Locked)} className="text-xs text-red-500 underline mb-4">{l0Locked ? "Unlock L0 Matrix" : "Lock L0 Matrix"}</button>
              <div className="grid grid-cols-2 gap-6">
                <div className="bg-zinc-950/40 p-4 border border-zinc-800 rounded-xl">
                    <h3 className="text-xs text-zinc-500 font-bold mb-4">L0 FOUNDATION</h3>
                    <label className="block text-xs mb-1">STEM_BASE</label>
                    <input type="number" disabled={l0Locked} className="w-full bg-zinc-900 border border-zinc-800 p-2 rounded mb-3" value={(physicsConstants.L0_FOUNDATION as any)?.STEM_BASE || 0} onChange={e => setPhysicsConstants(s => ({...s, L0_FOUNDATION: {...(s.L0_FOUNDATION as any), STEM_BASE: Number(e.target.value)}}))} />
                    <label className="block text-xs mb-1">BRANCH_BASE</label>
                    <input type="number" disabled={l0Locked} className="w-full bg-zinc-900 border border-zinc-800 p-2 rounded mb-3" value={(physicsConstants.L0_FOUNDATION as any)?.BRANCH_BASE || 0} onChange={e => setPhysicsConstants(s => ({...s, L0_FOUNDATION: {...(s.L0_FOUNDATION as any), BRANCH_BASE: Number(e.target.value)}}))} />
                </div>
              </div>
              <button onClick={savePhysics} className={solidBtn}>Apply Universal Laws</button>
            </div>
          )}

          {tab === "evolution" && (
            <div className="space-y-4">
              <div className="flex justify-between items-center border-b border-zinc-800 pb-2">
                <h2 className="text-lg font-bold">Evolution Ledger (The Causal Trace)</h2>
                <button onClick={loadEvolution} className="text-sky-500 text-xs">REFRESH</button>
              </div>
              <div className="bg-zinc-950 rounded-xl overflow-hidden border border-zinc-800">
                <table className="w-full text-xs text-left">
                  <thead className="bg-zinc-900/80 text-zinc-500 uppercase font-bold text-[10px]">
                    <tr>
                      <th className="px-4 py-3">Time</th>
                      <th className="px-4 py-3">God</th>
                      <th className="px-4 py-3">Delta</th>
                      <th className="px-4 py-3">Plugin / Step</th>
                      <th className="px-4 py-3">Reason</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-zinc-900">
                    {evolutionLogs.map(log => (
                      <tr key={log.id} className="hover:bg-zinc-800/20">
                        <td className="px-4 py-3 text-zinc-500">{new Date(log.timestamp).toLocaleTimeString()}</td>
                        <td className="px-4 py-3 font-bold text-zinc-200">{log.ten_god}</td>
                        <td className={`px-4 py-3 font-mono ${log.delta > 0 ? "text-emerald-400" : "text-rose-400"}`}>
                          {log.delta > 0 ? "+" : ""}{log.delta.toFixed(2)}
                        </td>
                        <td className="px-4 py-3">
                          <span className="text-sky-400">{log.plugin_id}</span>
                          <div className="text-[9px] text-zinc-600">{log.step}</div>
                        </td>
                        <td className="px-4 py-3 text-zinc-400 whitespace-nowrap overflow-hidden text-ellipsis max-w-[200px]">{log.reason}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {tab === "plugins" && (
            <div className="space-y-4">
               <h2 className="text-lg font-bold border-b border-zinc-800 pb-2">Plugin Causal Tiers (L0-L3)</h2>
               <div className="flex items-center gap-2">
                  <input
                    className="bg-zinc-950 border border-zinc-800 p-2 rounded text-xs w-72"
                    placeholder="session_id（留 default 自动回退最近活跃会话）"
                    value={pluginRuntimeSessionId}
                    onChange={e => setPluginRuntimeSessionId(e.target.value)}
                  />
                  <button onClick={() => void loadPlugins()} className={solidBtn}>刷新运行态</button>
                  <span className="text-[10px] text-zinc-500">当前解析会话：{resolvedPluginRuntimeSessionId || "default"}</span>
               </div>
               <div className="rounded-xl border border-zinc-800 bg-zinc-950/40 p-3 text-[11px] text-zinc-400">
                 <div className="flex flex-wrap items-center gap-4">
                   <span>scanned {scannedPluginCount}</span>
                   <span>hit {hitPluginRows.length}</span>
                   <span>inbox {inboxPluginRows.length}</span>
                   <span>claims {Number(knowledgeSnapshot.claim_history?.total_claims || 0)}</span>
                   <span>conflicts {Number(knowledgeSnapshot.conflict_history?.total_conflicts || 0)}</span>
                   <span>suggestions {Number(knowledgeSnapshot.resolution_preview?.total_suggestions || 0)}</span>
                   <span>brain actions {brainActionQueue.length}</span>
                 </div>
                 <div className="mt-1 flex flex-wrap items-center gap-3 text-[10px] text-zinc-500">
                   <span>arbiter bias: system {Number(knowledgeSnapshot.conflict_history?.recommended_arbiters?.system || 0)}</span>
                   <span>llm {Number(knowledgeSnapshot.conflict_history?.recommended_arbiters?.llm || 0)}</span>
                   <span>user {Number(knowledgeSnapshot.conflict_history?.recommended_arbiters?.user || 0)}</span>
                 </div>
                 <div className="mt-1 flex flex-wrap items-center gap-3 text-[10px] text-zinc-400">
                   <span>feedback system {Number((knowledgeSnapshot.conflict_history?.feedback_arbiters || {}).system || 0)}</span>
                   <span>llm {Number((knowledgeSnapshot.conflict_history?.feedback_arbiters || {}).llm || 0)}</span>
                   <span>user {Number((knowledgeSnapshot.conflict_history?.feedback_arbiters || {}).user || 0)}</span>
                   <span>score system {Number((knowledgeSnapshot.conflict_history?.feedback_arbiter_scores || {}).system || 0).toFixed(2)}</span>
                   <span>llm {Number((knowledgeSnapshot.conflict_history?.feedback_arbiter_scores || {}).llm || 0).toFixed(2)}</span>
                   <span>user {Number((knowledgeSnapshot.conflict_history?.feedback_arbiter_scores || {}).user || 0).toFixed(2)}</span>
                 </div>
                </div>
               {brainActionQueue.length ? (
                 <div className="rounded-xl border border-zinc-800 bg-zinc-950/40 p-3">
                   <div className="mb-2 text-[11px] font-semibold text-zinc-300">Brain Action Queue</div>
                   <div className="space-y-2">
                     {brainActionQueue.slice(0, 6).map((row, idx) => (
                       <div key={row.action_id || `brain_${idx}`} className="rounded-lg border border-zinc-800 bg-zinc-950/70 p-2">
                         <div className="flex items-center justify-between gap-2">
                           <span className="text-[10px] uppercase text-sky-300">{row.action_type || "brain_action"}</span>
                           <span className="text-[10px] uppercase text-zinc-500">{row.queue || "llm"}</span>
                         </div>
                         <div className="mt-1 text-[10px] text-zinc-300">{row.reason || "—"}</div>
                         <div className="mt-1 text-[10px] text-zinc-500">
                           conflict {row.conflict_id || "—"} / confidence {Number(row.confidence || 0).toFixed(2)}
                         </div>
                       </div>
                     ))}
                   </div>
                 </div>
               ) : null}
               {brainTimeline.length ? (
                 <div className="rounded-xl border border-zinc-800 bg-zinc-950/40 p-3">
                   <div className="mb-2 text-[11px] font-semibold text-zinc-300">Brain Flow Timeline</div>
                   <div className="space-y-2">
                     {brainTimeline.map((row, idx) => (
                       <div key={row.conflict.conflict_id || `timeline_${idx}`} className="rounded-lg border border-zinc-800 bg-zinc-950/70 p-2">
                         <div className="text-[10px] uppercase text-zinc-400">
                           {row.conflict.conflict_type || "conflict"} · {row.conflict.conflict_id || "—"}
                         </div>
                         <div className="mt-2 flex flex-wrap items-center gap-2 text-[10px]">
                           <span className="rounded border border-zinc-700 px-2 py-1 text-rose-300">
                             Conflict · {row.conflict.severity || "P?"}
                           </span>
                           <span className={`rounded border border-zinc-700 px-2 py-1 ${brainStepTone(row.resolution?.resolved_by || row.conflict.recommended_arbiter)}`}>
                             Resolution · {row.resolution?.resolved_by || row.conflict.recommended_arbiter || "pending"}
                           </span>
                           <span className={`rounded border border-zinc-700 px-2 py-1 ${brainStepTone(row.action?.action_type || row.resolution?.policy)}`}>
                             Brain Action · {row.action?.action_type || row.resolution?.policy || "waiting"}
                           </span>
                           <span className={`rounded border border-zinc-700 px-2 py-1 ${brainStepTone(row.action?.queue || row.resolution?.resolved_by)}`}>
                             Queue · {row.action?.queue || row.resolution?.next_queue || "pending"}
                           </span>
                         </div>
                         <div className="mt-2 text-[10px] text-zinc-400">
                           {row.action?.reason || row.resolution?.reason || row.conflict.why_conflict || "—"}
                         </div>
                       </div>
                     ))}
                   </div>
                </div>
               ) : null}
               <div className="grid gap-3 md:grid-cols-3">
                 <div className="rounded-xl border border-zinc-800 bg-zinc-950/40 p-3">
                   <div className="text-[11px] font-semibold text-zinc-300">扫描层</div>
                   <div className="mt-1 text-[10px] text-zinc-500">插件注册表中被扫描到的总量。</div>
                   <div className="mt-3 text-2xl font-semibold text-zinc-100">{scannedPluginCount}</div>
                 </div>
                 <div className="rounded-xl border border-zinc-800 bg-zinc-950/40 p-3">
                   <div className="text-[11px] font-semibold text-zinc-300">命中层</div>
                   <div className="mt-1 text-[10px] text-zinc-500">本轮确实产出 facts / proposal / claim 的插件。</div>
                   <div className="mt-3 text-2xl font-semibold text-emerald-300">{hitPluginRows.length}</div>
                 </div>
                 <div className="rounded-xl border border-zinc-800 bg-zinc-950/40 p-3">
                   <div className="text-[11px] font-semibold text-zinc-300">Inbox 层</div>
                   <div className="mt-1 text-[10px] text-zinc-500">已经进入手动、自动或上下文队列的插件。</div>
                   <div className="mt-3 text-2xl font-semibold text-amber-300">{inboxPluginRows.length}</div>
                 </div>
               </div>
               <div className="grid gap-3 lg:grid-cols-3">
                 <div className="rounded-xl border border-zinc-800 bg-zinc-950/40 p-3">
                   <div className="mb-2 text-[11px] font-semibold text-zinc-300">扫描到的插件</div>
                   <div className="space-y-1 text-[10px] text-zinc-500">
                     {pluginPanelRows.slice(0, 12).map((row) => (
                       <div key={`scan_${row.plugin.plugin_id}`} className="flex items-center justify-between gap-2">
                         <span className="truncate">{pluginCardTitle(row.plugin)}</span>
                         <span className="text-zinc-700">L{row.plugin.causal_tier}</span>
                       </div>
                     ))}
                   </div>
                 </div>
                 <div className="rounded-xl border border-zinc-800 bg-zinc-950/40 p-3">
                   <div className="mb-2 text-[11px] font-semibold text-zinc-300">命中并产出事实</div>
                   <div className="space-y-1 text-[10px] text-zinc-500">
                     {hitPluginRows.slice(0, 12).map((row) => (
                       <div key={`hit_${row.plugin.plugin_id}`} className="flex items-center justify-between gap-2">
                         <span className="truncate">{pluginCardTitle(row.plugin)}</span>
                         <span>{Number(row.runtime?.fact_count || 0)} facts</span>
                       </div>
                     ))}
                   </div>
                 </div>
                 <div className="rounded-xl border border-zinc-800 bg-zinc-950/40 p-3">
                   <div className="mb-2 text-[11px] font-semibold text-zinc-300">已进入 Inbox</div>
                   <div className="space-y-1 text-[10px] text-zinc-500">
                     {inboxPluginRows.slice(0, 12).map((row) => (
                       <div key={`inbox_${row.plugin.plugin_id}`} className="flex items-center justify-between gap-2">
                         <span className="truncate">{pluginCardTitle(row.plugin)}</span>
                         <span>{runtimeStatusLabel(row.runtime?.status)}</span>
                       </div>
                     ))}
                   </div>
                 </div>
               </div>
               <div className="space-y-2">
                  {pluginPanelRows.map(({ plugin: p, runtime, relatedClaims, relatedConflicts }) => {
                    const runtimeStatus = String(runtime?.status || "unknown");
                    const runtimeTone = runtimeStatusTone(runtimeStatus);
                    return (
                    <div key={p.plugin_id} className="p-3 bg-zinc-950/40 border border-zinc-800 rounded-xl">
                      <div className="flex justify-between items-center">
                       <div>
                          <div className="font-bold text-zinc-200">{pluginCardTitle(p)}</div>
                          <div className="text-[10px] text-zinc-500">Tier: {p.causal_tier} · Order: {p.execution_order}</div>
                          <div className="mt-1 text-[10px] text-zinc-400">{p.technical_label || p.plugin_id}</div>
                       </div>
                       <div className={`px-2 py-0.5 rounded text-[10px] ${p.activated ? "bg-emerald-900/40 text-emerald-400" : "bg-zinc-800 text-zinc-500"}`}>
                          {p.activated ? "ACTIVE" : "IDLE"}
                       </div>
                      </div>
                      <div className="mt-2 flex items-center gap-2 text-[10px]">
                        <span className={`rounded px-2 py-0.5 uppercase ${runtimeTone}`}>{runtimeStatusLabel(runtimeStatus)}</span>
                        {runtime?.target_god ? <span className="text-zinc-500">target {runtime.target_god}</span> : null}
                        {typeof runtime?.fact_count === "number" ? <span className="text-zinc-600">facts {runtime.fact_count}</span> : null}
                        {typeof runtime?.proposal_count === "number" ? <span className="text-zinc-600">proposals {runtime.proposal_count}</span> : null}
                        {typeof runtime?.decision_count === "number" ? <span className="text-zinc-600">decisions {runtime.decision_count}</span> : null}
                        <span className="text-zinc-600">claims {relatedClaims.length}</span>
                        <span className="text-zinc-600">conflicts {relatedConflicts.length}</span>
                      </div>
                      <div className="mt-1 text-[10px] text-zinc-300">{pluginCardDefinition(p)}</div>
                      <div className="mt-1 text-[10px] text-zinc-500">{runtime?.reason || pluginCardDescription(p)}</div>
                      {(() => {
                        const relatedGroups = buildConflictGroups(relatedConflicts, pluginConflictResolutions);
                        return relatedGroups.length ? (
                          <div className="mt-2 space-y-2">
                            {relatedGroups.slice(0, 5).map((group) => {
                              const sample = group.conflicts[0];
                              const firstConflictId = String(sample.conflict_id || "").trim();
                              const busyKey = `${p.plugin_id}|${group.key}`;
                              const isBusy = resolveBusyKeys.includes(busyKey);
                              return (
                                <div key={group.key} className="rounded-lg border border-zinc-800 bg-zinc-950/70 p-2">
                                  <div className="flex items-center justify-between gap-2">
                                    <span className={`rounded px-2 py-0.5 text-[10px] uppercase ${conflictTone(group.severity)}`}>
                                      {group.severity || "P3"} · {group.recommended_arbiter || "system"}
                                    </span>
                                    <span className="rounded border border-zinc-700 px-2 py-1 text-[10px] text-zinc-500">
                                      {group.conflict_type || "conflict"}
                                    </span>
                                  </div>
                                  <div className="mt-1 text-[10px] text-zinc-300">
                                    target {group.target_god} · {group.conflict_ids.length} 条
                                    · 评分 {group.max_conflict_score.toFixed(3)}
                                  </div>
                                  <div className="mt-1 text-[10px] text-zinc-500">
                                    {sample?.why_conflict || "—"}
                                  </div>
                                  {firstConflictId ? (
                                    <div className="mt-1 text-[10px] text-zinc-500">
                                      示例冲突 {firstConflictId}
                                    </div>
                                  ) : null}
                                  {group.conflicts.slice(0, 2).map((conflict) => {
                                    const plugins = Array.isArray(conflict.plugins) ? conflict.plugins : [];
                                    return (
                                      <div key={conflict.conflict_id} className="mt-1 text-[10px] text-zinc-400">
                                        · {conflict.why_conflict || conflict.conflict_id || "—"}
                                        {plugins.length ? `（来源插件 ${plugins.length} 个）` : ""}
                                      </div>
                                    );
                                  })}
                                  <div className="mt-2 flex items-center gap-2">
                                    <button
                                      type="button"
                                      disabled={isBusy}
                                      onClick={() => void resolveConflictBatch(group.conflict_ids, "system", busyKey)}
                                      className="rounded border border-zinc-700 px-2 py-1 text-[10px] text-zinc-300 disabled:opacity-40"
                                    >
                                      System 批裁
                                    </button>
                                    <button
                                      type="button"
                                      disabled={isBusy}
                                      onClick={() => void resolveConflictBatch(group.conflict_ids, "llm", busyKey)}
                                      className="rounded border border-zinc-700 px-2 py-1 text-[10px] text-zinc-300 disabled:opacity-40"
                                      title="按冲突批量提交给 LLM"
                                    >
                                      LLM 批裁
                                    </button>
                                    <button
                                      type="button"
                                      disabled={isBusy}
                                      onClick={() => void resolveConflictBatch(group.conflict_ids, "user", busyKey)}
                                      className="rounded border border-zinc-700 px-2 py-1 text-[10px] text-zinc-300 disabled:opacity-40"
                                    >
                                      用户批裁
                                    </button>
                                  </div>
                                </div>
                              );
                            })}
                          </div>
                        ) : null;
                      })()}
                    </div>
                  )})}
               </div>
            </div>
          )}

          <p className="mt-8 text-xs text-zinc-600 italic">{msg || "Waiting for command..."}</p>
        </div>
      </div>
    </main>
  );
}
