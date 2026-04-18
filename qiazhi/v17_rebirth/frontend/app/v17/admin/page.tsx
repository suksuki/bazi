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

type PluginRuntimeStatus = {
  plugin_id: string;
  fact_count?: number;
  proposal_count?: number;
  status?: string;
  target_god?: string;
  reason?: string;
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
  const [pluginRuntimeSessionId, setPluginRuntimeSessionId] = useState("default");
  const [resolvedPluginRuntimeSessionId, setResolvedPluginRuntimeSessionId] = useState("default");
  const [selectedPlugin, setSelectedPlugin] = useState<PluginAdminRow | null>(null);
  const [physicsConstants, setPhysicsConstants] = useState<LooseObject>({});
  const [evolutionLogs, setEvolutionLogs] = useState<any[]>([]);
  const [l0Locked, setL0Locked] = useState(true);
  const [localConfig, setLocalConfig] = useState<LooseObject>({});
  const [localEnabled, setLocalEnabled] = useState(false);

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
      setPlugins(list);
      setPluginStatuses(statusList);
      setResolvedPluginRuntimeSessionId(String((statusData as any).session_id || pluginRuntimeSessionId || "default"));
    } finally { setBusy(null); }
  }, [pluginRuntimeSessionId]);

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
               <div className="space-y-2">
                  {plugins.map(p => {
                    const runtime = pluginStatuses.find((s) => {
                      const sid = normalizePluginKey(s.plugin_id);
                      const pid = normalizePluginKey(p.plugin_id);
                      const mod = normalizePluginKey(p.module);
                      return sid === pid || (sid && mod && (sid === mod || sid.endsWith(`.${mod}`) || mod.endsWith(`.${sid}`)));
                    });
                    const runtimeStatus = String(runtime?.status || "unknown");
                    const runtimeTone =
                      runtimeStatus === "auto_applied"
                        ? "bg-emerald-900/40 text-emerald-300"
                        : runtimeStatus === "proposal_pending"
                          ? "bg-amber-900/40 text-amber-300"
                          : runtimeStatus === "clamped"
                            ? "bg-fuchsia-900/40 text-fuchsia-300"
                            : runtimeStatus.startsWith("skipped")
                              ? "bg-rose-900/40 text-rose-300"
                              : "bg-zinc-800 text-zinc-400";
                    return (
                    <div key={p.plugin_id} className="p-3 bg-zinc-950/40 border border-zinc-800 rounded-xl">
                      <div className="flex justify-between items-center">
                       <div>
                          <div className="font-bold text-zinc-200">{p.definition_text || p.plugin_id}</div>
                          <div className="text-[10px] text-zinc-500">Tier: {p.causal_tier} · Order: {p.execution_order}</div>
                       </div>
                       <div className={`px-2 py-0.5 rounded text-[10px] ${p.activated ? "bg-emerald-900/40 text-emerald-400" : "bg-zinc-800 text-zinc-500"}`}>
                          {p.activated ? "ACTIVE" : "IDLE"}
                       </div>
                      </div>
                      <div className="mt-2 flex items-center gap-2 text-[10px]">
                        <span className={`rounded px-2 py-0.5 uppercase ${runtimeTone}`}>{runtimeStatus}</span>
                        {runtime?.target_god ? <span className="text-zinc-500">target {runtime.target_god}</span> : null}
                        {typeof runtime?.fact_count === "number" ? <span className="text-zinc-600">facts {runtime.fact_count}</span> : null}
                        {typeof runtime?.proposal_count === "number" ? <span className="text-zinc-600">proposals {runtime.proposal_count}</span> : null}
                      </div>
                      <div className="mt-1 text-[10px] text-zinc-500">{runtime?.reason || "暂无最近运行状态。打开 Oracle 跑一轮后会在这里同步。"}</div>
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
