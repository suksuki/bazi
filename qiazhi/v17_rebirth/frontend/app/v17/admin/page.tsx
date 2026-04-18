"use client";

import { useCallback, useEffect, useState, type Dispatch, type SetStateAction } from "react";

type TabKey = "llm" | "db" | "plugins" | "physics";

type LlmNode = {
  provider: string;
  host: string;
  port: number;
  model: string;
  /** 单次 HTTP 读超时（秒），默认 15；可由环境变量 QIAZHI_V17_LLM_HTTP_TIMEOUT_SEC 覆盖 */
  httpTimeoutSec: number;
  /** fuse 外层 asyncio.wait_for（秒），默认 30；可由 QIAZHI_V17_LLM_FUSE_WAIT_TIMEOUT_SEC 覆盖 */
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
  /** V17.14b：本期测算是否在该执行序节点产出事实 */
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

function layerLabel(layer: string) {
  return LAYER_TABS.find((item) => item.key === layer)?.label || layer;
}

type ActionKey =
  | "loadModels"
  | "testLlm"
  | "testLlmChat"
  | "saveLlm"
  | "testDb"
  | "saveDb"
  | "loadPlugins"
  | "savePhysics"
  | null;
type LooseObject = Record<string, unknown>;

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
  } catch {
    /* 保持默认 */
  }
  const httpRaw = Number(llmNode.http_timeout_sec);
  const fuseRaw = Number(llmNode.fuse_wait_timeout_sec);
  const httpTimeoutSec = Number.isFinite(httpRaw) && httpRaw > 0 ? httpRaw : 15;
  const fuseWaitSec = Number.isFinite(fuseRaw) && fuseRaw > 0 ? fuseRaw : 30;
  setLlm({
    provider: String(llmNode.provider || "ollama"),
    host,
    port,
    model: String(llmNode.model || ""),
    httpTimeoutSec,
    fuseWaitSec,
  });
}

export default function V17AdminPage() {
  const [tab, setTab] = useState<TabKey>("llm");
  const [llm, setLlm] = useState<LlmNode>({
    provider: "ollama",
    host: "192.168.0.12",
    port: 11434,
    model: "",
    httpTimeoutSec: 15,
    fuseWaitSec: 30,
  });
  const [db, setDb] = useState<DbBridge>({
    driver: "postgres",
    host: "127.0.0.1",
    port: 5432,
    database: "v17_rebirth",
    username: "postgres",
    password: "",
    sslmode: "prefer",
    url: "",
    enabled: false,
  });
  const [msg, setMsg] = useState("");
  const [llmModels, setLlmModels] = useState<string[]>([]);
  const [llmPrompt, setLlmPrompt] = useState("你好，请简单自我介绍。");
  const [busy, setBusy] = useState<ActionKey>(null);
  const [plugins, setPlugins] = useState<PluginAdminRow[]>([]);
  const [selectedPlugin, setSelectedPlugin] = useState<PluginAdminRow | null>(null);
  const [physicsConstants, setPhysicsConstants] = useState<LooseObject>({});
  const [l0Locked, setL0Locked] = useState(true);
  const [localConfig, setLocalConfig] = useState<LooseObject>({});
  const [localEnabled, setLocalEnabled] = useState(false);
  const [standardParams, setStandardParams] = useState<LooseObject>({});

  const llmBaseUrl = `http://${llm.host}:${llm.port}/v1`;

  const ghostBtn =
    "cursor-pointer rounded-md border border-zinc-500 px-4 py-2 text-sm font-semibold text-zinc-200 transition hover:border-zinc-300 hover:bg-zinc-800 active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-50";
  const solidBtn =
    "cursor-pointer rounded-md bg-zinc-100 px-4 py-2 text-sm font-semibold text-zinc-900 transition hover:bg-white active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-60";

  const loadPlugins = useCallback(async () => {
    setBusy("loadPlugins");
    try {
      const { data } = await requestJson("/api/v17-admin/plugins?v17_origin=v17_rebirth");
      const obj = (data as LooseObject) || {};
      const raw = obj.plugins;
      const list = Array.isArray(raw) ? (raw as PluginAdminRow[]) : [];
      setPlugins(list);
      setSelectedPlugin((cur) => {
        if (!cur) return list[0] ?? null;
        const hit = list.find((p) => p.plugin_id === cur.plugin_id);
        return hit ?? list[0] ?? null;
      });
      setMsg(obj.ok ? `已加载 ${list.length} 个插件（L0–L3）` : `插件列表失败：${obj.error || obj.detail || "unknown"}`);
    } finally {
      setBusy(null);
    }
  }, []);

  useEffect(() => {
    void (async () => {
      const [{ data: llmData }, { data: dbData }, { data: physicsData }] = await Promise.all([
        requestJson("/api/v17-admin/llm-node?v17_origin=v17_rebirth"),
        requestJson("/api/v17-admin/db-bridge?v17_origin=v17_rebirth"),
        requestJson("/api/v17-admin/physics-constants?v17_origin=v17_rebirth"),
      ]);
      const llmObj = (llmData as LooseObject) || {};
      const llmNode = (llmObj.node as LooseObject) || null;
      const dbObj = (dbData as LooseObject) || {};
      const physicsObj = (physicsData as LooseObject) || {};
      applyLlmNodeToState(llmNode, setLlm);
      if (dbObj.bridge) setDb(dbObj.bridge as DbBridge);
      if (physicsObj.constants) setPhysicsConstants(physicsObj.constants as LooseObject);
    })();
  }, []);

  useEffect(() => {
    if (selectedPlugin) {
      void (async () => {
        const { data } = await requestJson(`/api/v17/admin/plugin-config/${selectedPlugin.plugin_id}?v17_origin=v17_rebirth`);
        const obj = (data as LooseObject) || {};
        const cfg = (obj.config as LooseObject) || {};
        
        // 自动发现模式：合规插件自动合并声明参数
        const declared = (selectedPlugin.declared_params as LooseObject) || {};
        setStandardParams(declared);
        
        const hasLocal = Object.keys(cfg).length > 0;
        setLocalEnabled(hasLocal);
        
        // 如果开启了局部覆盖但配置为空，则注入默认声明值
        if (hasLocal) {
          setLocalConfig(cfg);
        } else {
          setLocalConfig(declared);
        }
      })();
    }
  }, [selectedPlugin]);

  useEffect(() => {
    if (tab !== "plugins") return;
    void loadPlugins();
  }, [tab, loadPlugins]);

  async function saveLlm() {
    setBusy("saveLlm");
    try {
      const { resp, data } = await requestJson("/api/v17-admin/llm-node", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          provider: llm.provider,
          base_url: llmBaseUrl,
          model: llm.model,
          http_timeout_sec: String(llm.httpTimeoutSec),
          fuse_wait_timeout_sec: String(llm.fuseWaitSec),
          v17_origin: "v17_rebirth",
        }),
      });
      const obj = (data as LooseObject) || {};
      if (resp.ok) {
        applyLlmNodeToState((obj.node as LooseObject) || null, setLlm);
      }
      setMsg(resp.ok ? `LLM 配置已保存，管线已重载 epoch=${obj.pipeline_epoch ?? "?"}` : `保存失败：${obj.detail || obj.error || "未知错误"}`);
    } finally {
      setBusy(null);
    }
  }

  async function testLlm() {
    setBusy("testLlm");
    try {
      const { data } = await requestJson("/api/v17-admin/llm-node/test", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ base_url: llmBaseUrl, v17_origin: "v17_rebirth" }),
      });
      const obj = (data as LooseObject) || {};
      const result = ((obj.result as LooseObject) || {}) as LooseObject;
      setMsg(obj.ok ? `LLM 测试成功：${result.probe_url || ""} (${result.http_status || ""})` : `LLM 测试失败：${obj.error || obj.detail || "未知错误"}`);
    } finally {
      setBusy(null);
    }
  }

  async function loadLlmModels() {
    setBusy("loadModels");
    try {
      const { data } = await requestJson("/api/v17-admin/llm-node/models", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ base_url: llmBaseUrl, v17_origin: "v17_rebirth" }),
      });
      const obj = (data as LooseObject) || {};
      const result = ((obj.result as LooseObject) || {}) as LooseObject;
      if (obj.ok) {
        const models = Array.isArray(result.models) ? (result.models as string[]) : [];
        setLlmModels(models);
        if (!llm.model && models.length > 0) {
          setLlm((s) => ({ ...s, model: String(models[0]) }));
        }
        setMsg(`模型拉取完成：${models.length} 个`);
      } else {
        setMsg(`模型拉取失败：${obj.error || obj.detail || "未知错误"}`);
      }
    } finally {
      setBusy(null);
    }
  }

  async function testLlmChat() {
    setBusy("testLlmChat");
    try {
      const { data } = await requestJson("/api/v17-admin/llm-node/chat-test", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ base_url: llmBaseUrl, model: llm.model, prompt: llmPrompt, v17_origin: "v17_rebirth" }),
      });
      const obj = (data as LooseObject) || {};
      const result = ((obj.result as LooseObject) || {}) as LooseObject;
      setMsg(obj.ok ? `LLM 回复：${result.reply || "(空回复)"}` : `LLM 对话测试失败：${obj.error || obj.detail || "未知错误"}`);
    } finally {
      setBusy(null);
    }
  }

  async function saveDb() {
    setBusy("saveDb");
    try {
      const { resp, data } = await requestJson("/api/v17-admin/db-bridge", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...db, v17_origin: "v17_rebirth" }),
      });
      const obj = (data as LooseObject) || {};
      if (resp.ok && obj.bridge) {
        setDb(obj.bridge as DbBridge);
      }
      setMsg(resp.ok ? "DB Bridge 配置已保存（V17 协议锁通过）" : `保存失败：${obj.detail || obj.error || "未知错误"}`);
    } finally {
      setBusy(null);
    }
  }

  async function savePhysics() {
    setBusy("savePhysics");
    try {
      const { resp, data } = await requestJson("/api/v17-admin/physics-constants", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ constants: physicsConstants, v17_origin: "v17_rebirth" }),
      });
      const obj = (data as LooseObject) || {};
      if (resp.ok && obj.constants) {
        setPhysicsConstants(obj.constants as LooseObject);
      }
      setMsg(resp.ok ? "宇宙常数已热更新，物理管线已重启" : `保存失败：${obj.detail || obj.error || "未知错误"}`);
    } finally {
      setBusy(null);
    }
  }

  async function saveLocalConfig() {
    if (!selectedPlugin) return;
    setBusy("savePhysics"); // 复用物理繁忙状态
    try {
      const { data } = await requestJson(`/api/v17/admin/plugin-config/${selectedPlugin.plugin_id}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ v17_origin: "v17_rebirth", config: localEnabled ? localConfig : {} }),
      });
      const obj = (data as LooseObject) || {};
      setMsg(obj.ok ? `插件 [${selectedPlugin.plugin_id}] 局部裁量权已同步` : `保存失败：${obj.detail || obj.error || "未知错误"}`);
    } finally {
      setBusy(null);
    }
  }

  async function testDb() {
    setBusy("testDb");
    try {
      const { data } = await requestJson("/api/v17-admin/db-bridge/test", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...db, v17_origin: "v17_rebirth" }),
      });
      const obj = (data as LooseObject) || {};
      const result = ((obj.result as LooseObject) || {}) as LooseObject;
      setMsg(obj.ok ? `DB 测试成功：${result.host || ""}:${result.port || ""}` : `DB 测试失败：${obj.error || obj.detail || "未知错误"}`);
    } finally {
      setBusy(null);
    }
  }

  return (
    <main className="min-h-screen bg-zinc-950 text-zinc-100">
      <section className="mx-auto grid max-w-6xl grid-cols-1 gap-4 p-6 md:grid-cols-[220px_1fr]">
        <aside className="rounded-xl border border-zinc-700 bg-zinc-900 p-3">
          <h1 className="mb-3 text-sm font-semibold text-zinc-300">V17 物理引擎管理后台</h1>
          <button
            type="button"
            onClick={() => setTab("llm")}
            className={`mb-2 w-full rounded-md px-3 py-2 text-left text-sm ${tab === "llm" ? "bg-zinc-700 text-white" : "bg-zinc-800 text-zinc-300"}`}
          >
            LLM 节点配置
          </button>
          <button
            type="button"
            onClick={() => setTab("db")}
            className={`mb-2 w-full rounded-md px-3 py-2 text-left text-sm ${tab === "db" ? "bg-zinc-700 text-white" : "bg-zinc-800 text-zinc-300"}`}
          >
            数据库桥接
          </button>
          <button
            type="button"
            onClick={() => setTab("plugins")}
            className={`mb-2 w-full rounded-md px-3 py-2 text-left text-sm ${tab === "plugins" ? "bg-zinc-700 text-white" : "bg-zinc-800 text-zinc-300"}`}
          >
            插件 L0–L3
          </button>
          <button
            type="button"
            onClick={() => setTab("physics")}
            className={`w-full rounded-md px-3 py-2 text-left text-sm ${tab === "physics" ? "bg-zinc-700 text-white" : "bg-zinc-800 text-zinc-300"}`}
          >
            V17 宇宙常数
          </button>
        </aside>

        <div className="rounded-xl border border-zinc-700 bg-zinc-900 p-5">
          {tab === "plugins" ? (
            <div className="space-y-4">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <h2 className="text-base font-semibold text-zinc-100">插件挂载（按 L0–L3）</h2>
                <button type="button" disabled={busy !== null} onClick={loadPlugins} className={ghostBtn}>
                  {busy === "loadPlugins" ? "刷新中..." : "刷新列表"}
                </button>
              </div>
              <div className="grid grid-cols-1 gap-4 lg:grid-cols-[1fr_320px]">
                <div className="space-y-4">
                  {LAYER_TABS.map(({ key, label }) => {
                    const rows = plugins
                      .filter((p) => p.layer === key)
                      .sort((a, b) => (a.execution_order ?? 999) - (b.execution_order ?? 999));
                    if (rows.length === 0) return null;
                    return (
                      <div key={key} className="rounded-lg border border-zinc-700 bg-zinc-950/40 p-3">
                        <h3 className="mb-2 text-sm font-semibold text-zinc-300">{label}</h3>
                        <ul className="space-y-1">
                          {rows.map((p) => {
                            const active = selectedPlugin?.plugin_id === p.plugin_id;
                            const live = Boolean(p.causal_active_path);
                            return (
                              <li key={p.plugin_id}>
                                <button
                                  type="button"
                                  onClick={() => setSelectedPlugin(p)}
                                  className={`w-full rounded-md px-3 py-2 text-left text-sm transition ${
                                    active
                                      ? "bg-amber-900/40 text-amber-100 ring-1 ring-amber-600/60"
                                      : live
                                        ? "bg-emerald-950/50 text-emerald-50 ring-2 ring-emerald-500/55 hover:bg-emerald-900/40"
                                        : "bg-zinc-800 text-zinc-200 hover:bg-zinc-700"
                                  }`}
                                >
                                  <span
                                    className={`font-mono text-xs ${live ? "text-emerald-300/90" : "text-zinc-400"}`}
                                  >
                                    #{p.execution_order ?? "?"} · {p.plugin_id}
                                    {live ? " · 活跃" : ""}
                                  </span>
                                  <span className="mt-1 block text-sm text-zinc-100">
                                    {p.definition_text || p.function_summary || p.module_doc || p.module}
                                  </span>
                                  <span className="mt-1 block text-xs text-zinc-500">
                                    模块：{p.module} · {p.activated ? "已触发" : "未触发"} · {KIND_LABELS[p.kind] || p.kind}
                                  </span>
                                  <span className="text-xs text-zinc-500">
                                    因果层级 {p.causal_tier} · 同层优先级 {p.registry_priority?.toFixed(2) ?? "—"}
                                  </span>
                                </button>
                              </li>
                            );
                          })}
                        </ul>
                      </div>
                    );
                  })}
                </div>
                <aside className="rounded-lg border border-zinc-700 bg-zinc-950/60 p-4 text-sm">
                  {!selectedPlugin ? (
                    <p className="text-zinc-500">请从左侧选择一个插件。</p>
                  ) : (
                    <>
                      <div className="mb-4 rounded-lg border border-zinc-700 bg-zinc-900/70 p-3">
                        <div className="flex items-center justify-between">
                          <p className="text-base font-semibold text-zinc-100">{selectedPlugin.definition_text || selectedPlugin.plugin_id}</p>
                          {selectedPlugin.is_standard_skill && (
                            <span className="rounded bg-sky-900/40 px-1.5 py-0.5 text-[9px] font-bold text-sky-400 ring-1 ring-sky-500/50">
                              V17 STANDARD
                            </span>
                          )}
                        </div>
                        <p className="mt-1 font-mono text-xs text-zinc-400">{selectedPlugin.plugin_id}</p>
                        <p className="mt-1 text-xs text-zinc-500">{selectedPlugin.detail_description}</p>
                      </div>

                      {/* 因果链路追踪 (Formula Preview) */}
                      <div className="mb-4 rounded-lg border border-zinc-700 bg-zinc-950/20 p-4">
                        <h3 className="mb-2 text-xs font-semibold text-zinc-400">因果链路追踪 (Formula Trace)</h3>
                        <div className="font-mono text-[11px] text-sky-400">
                          {selectedPlugin.plugin_id === "three_harmony" ? (
                            `E_mid = Base * (1 + ${(physicsConstants.L1_ATOMIC as LooseObject)?.["FUSION_MID_GAIN"] || "1.35"}[Fusion] + {{Induction}}[Induction])`
                          ) : selectedPlugin.plugin_id === "six_pierce" ? (
                            `E_target = E_initial * (1 - 0.12[Dissipation])`
                          ) : (
                            `δE = f(Physics_Tensor, ${selectedPlugin.plugin_id}.config)`
                          )}
                        </div>
                      </div>

                      {/* 局部裁量权 (Local Override) */}
                      <div className="mb-4 rounded-lg border border-emerald-900/40 bg-emerald-950/10 p-4">
                        <div className="mb-4 flex items-center justify-between">
                          <h3 className="text-xs font-semibold uppercase tracking-wider text-emerald-500">算法局部裁量面板 (The Court)</h3>
                          <label className="flex items-center gap-2 text-xs text-zinc-400">
                            启用局部覆盖
                            <input type="checkbox" checked={localEnabled} onChange={(e) => setLocalEnabled(e.target.checked)} />
                          </label>
                        </div>
                        
                        {localEnabled ? (
                          <div className="space-y-4">
                            {/* 动态表单渲染引擎 (Auto-Discovery UI) */}
                            <div className="grid grid-cols-2 gap-3">
                              {Object.entries(localConfig).map(([k, v]) => {
                                const isRef = String(v).startsWith("ref(global.");
                                return (
                                  <div key={k} className="relative">
                                    <label className="block text-[10px] text-zinc-500 uppercase flex items-center justify-between">
                                      {k}
                                      {isRef && <span className="text-[9px] text-amber-500">GLOBAL LINKED</span>}
                                    </label>
                                    <input 
                                      className={`mt-1 w-full rounded border px-2 py-1 text-sm ${isRef ? "border-amber-900/50 bg-amber-950/20 text-amber-200" : "border-zinc-600 bg-zinc-800 text-zinc-200"}`}
                                      value={String(v)}
                                      title={isRef ? "此项受全局 Physics Hub 同名常数控制，编辑将转化为局部 Override。" : ""}
                                      onChange={(e) => setLocalConfig(s => ({...s, [k]: e.target.value}))}
                                    />
                                  </div>
                                );
                              })}
                              {Object.keys(localConfig).length === 0 && (
                                <p className="col-span-2 py-4 text-center text-xs text-zinc-600 italic">该插件未声明任何物理常数。</p>
                              )}
                            </div>
                            <button type="button" onClick={saveLocalConfig} className="w-full rounded bg-emerald-600 py-1.5 text-xs font-bold text-white hover:bg-emerald-500">
                              应用局部算法修正
                            </button>
                          </div>
                        ) : (
                          <p className="text-center text-[11px] text-zinc-500 italic">当前听从全局 Physics Hub 指挥，未开启特异化修正。</p>
                        )}
                      </div>

                      <div className="space-y-3">
                        <section className="rounded-lg border border-zinc-700 bg-zinc-900/50 p-3">
                          <p className="mb-2 text-xs font-semibold tracking-wide text-amber-300">插件定义</p>
                          <p className="text-sm leading-6 text-zinc-200">
                            {selectedPlugin.definition_text || selectedPlugin.function_summary || selectedPlugin.module_doc || "暂无定义说明。"}
                          </p>
                        </section>

                        <section className="rounded-lg border border-zinc-700 bg-zinc-900/50 p-3">
                          <p className="mb-2 text-xs font-semibold tracking-wide text-sky-300">功能描述</p>
                          <p className="text-sm leading-6 text-zinc-200">
                            {selectedPlugin.function_summary || selectedPlugin.detail_description || "暂无功能描述。"}
                          </p>
                        </section>

                        <section className="rounded-lg border border-zinc-700 bg-zinc-900/50 p-3">
                          <p className="mb-2 text-xs font-semibold tracking-wide text-emerald-300">触发条件</p>
                          <p className="text-sm leading-6 text-zinc-200">
                            {selectedPlugin.trigger_condition_text || selectedPlugin.causal_trace_text || "暂无触发条件说明。"}
                          </p>
                        </section>

                        <section className="rounded-lg border border-zinc-700 bg-zinc-900/50 p-3">
                          <p className="mb-2 text-xs font-semibold tracking-wide text-fuchsia-300">设计缘由</p>
                          <p className="text-sm leading-6 text-zinc-200">
                            {selectedPlugin.design_rationale || selectedPlugin.detail_description || "暂无设计缘由说明。"}
                          </p>
                        </section>

                        <section className="rounded-lg border border-zinc-700 bg-zinc-900/50 p-3">
                          <p className="mb-2 text-xs font-semibold tracking-wide text-zinc-300">运行信息</p>
                          <dl className="space-y-2 text-zinc-300">
                            <div>
                              <dt className="text-xs text-zinc-500">执行序</dt>
                              <dd
                                className={`font-mono text-lg ${
                                  selectedPlugin.causal_active_path ? "text-emerald-300" : "text-sky-200"
                                }`}
                              >
                                #{selectedPlugin.execution_order ?? "—"}
                                {selectedPlugin.causal_active_path ? " · 本期有事实输出" : ""}
                              </dd>
                            </div>
                            <div>
                              <dt className="text-xs text-zinc-500">因果层级</dt>
                              <dd className="text-sm text-zinc-200">
                                {selectedPlugin.power_tier ?? selectedPlugin.causal_tier} · {tierLabel(selectedPlugin.power_tier ?? selectedPlugin.causal_tier)}
                              </dd>
                            </div>
                            <div>
                              <dt className="text-xs text-zinc-500">同层优先级</dt>
                              <dd className="font-mono text-sm text-zinc-200">{selectedPlugin.registry_priority?.toFixed(3) ?? "—"}</dd>
                            </div>
                            <div>
                              <dt className="text-xs text-zinc-500">挂载位置</dt>
                              <dd className="text-sm text-zinc-200">{selectedPlugin.layer_dir} / {selectedPlugin.module}</dd>
                            </div>
                            <div>
                              <dt className="text-xs text-zinc-500">运行状态</dt>
                              <dd className="text-sm text-zinc-200">
                                {selectedPlugin.activated ? "本期已触发" : "本期未触发"}
                                {selectedPlugin.causal_active_path ? "，且已写出事实" : ""}
                              </dd>
                            </div>
                          </dl>
                        </section>

                        <section className="rounded-lg border border-zinc-700 bg-zinc-900/50 p-3">
                          <p className="mb-2 text-xs font-semibold tracking-wide text-zinc-300">因果链路</p>
                          <p className="text-sm leading-6 text-zinc-200">{selectedPlugin.causal_trace_text || "暂无因果链路说明。"}</p>
                          {selectedPlugin.executed_before_plugin_ids && selectedPlugin.executed_before_plugin_ids.length > 0 ? (
                            <div className="mt-3">
                              <p className="mb-1 text-xs text-zinc-500">上游插件链</p>
                              <p className="break-all font-mono text-xs text-zinc-400">
                                {selectedPlugin.executed_before_plugin_ids.join(" → ")}
                              </p>
                            </div>
                          ) : null}
                        </section>

                        <section className="rounded-lg border border-zinc-700 bg-zinc-900/50 p-3">
                          <p className="mb-2 text-xs font-semibold tracking-wide text-zinc-300">最近一次命中</p>
                          <p className="mb-2 font-mono text-xs text-zinc-400">最近写入：{selectedPlugin.last_at || "—"}</p>
                          {(selectedPlugin.last_facts && selectedPlugin.last_facts.length > 0) ? (
                            <ul className="list-inside list-disc space-y-1 text-zinc-200">
                              {selectedPlugin.last_facts.map((t, i) => (
                                <li key={i}>{t}</li>
                              ))}
                            </ul>
                          ) : (
                            <span className="text-zinc-500">本期尚未命中该插件，暂无事实输出。</span>
                          )}
                        </section>
                      </div>
                    </>
                  )}
                </aside>
              </div>
            </div>
          ) : tab === "llm" ? (
            <div className="space-y-3">
              <h2 className="text-base font-semibold text-zinc-100">LLM 节点配置 (Node Config)</h2>
              <input
                className="w-full rounded-md border border-zinc-600 bg-zinc-800 px-3 py-2 text-sm"
                placeholder="provider (ollama)"
                value={llm.provider}
                onChange={(e) => setLlm((s) => ({ ...s, provider: e.target.value }))}
              />
              <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
                <input
                  className="w-full rounded-md border border-zinc-600 bg-zinc-800 px-3 py-2 text-sm"
                  placeholder="ollama 地址 (如 192.168.0.12)"
                  title="LLM 地址，例如 192.168.0.12"
                  value={llm.host}
                  onChange={(e) => setLlm((s) => ({ ...s, host: e.target.value }))}
                />
                <input
                  className="w-full rounded-md border border-zinc-600 bg-zinc-800 px-3 py-2 text-sm"
                  placeholder="端口 (默认 11434)"
                  title="LLM 端口，Ollama 默认 11434"
                  value={String(llm.port)}
                  onChange={(e) => setLlm((s) => ({ ...s, port: Number(e.target.value || 11434) }))}
                />
              </div>
              <p className="text-xs text-zinc-400">当前连接：{llmBaseUrl}</p>
              <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
                <label className="block text-xs text-zinc-400">
                  HTTP 单次超时（秒）
                  <input
                    type="number"
                    min={1}
                    max={600}
                    step={1}
                    className="mt-1 w-full rounded-md border border-zinc-600 bg-zinc-800 px-3 py-2 text-sm"
                    value={llm.httpTimeoutSec}
                    onChange={(e) => setLlm((s) => ({ ...s, httpTimeoutSec: Number(e.target.value) || 15 }))}
                  />
                </label>
                <label className="block text-xs text-zinc-400">
                  Fuse 总等待 asyncio.wait_for（秒）
                  <input
                    type="number"
                    min={1}
                    max={600}
                    step={1}
                    className="mt-1 w-full rounded-md border border-zinc-600 bg-zinc-800 px-3 py-2 text-sm"
                    value={llm.fuseWaitSec}
                    onChange={(e) => setLlm((s) => ({ ...s, fuseWaitSec: Number(e.target.value) || 30 }))}
                  />
                </label>
              </div>
              <p className="text-[11px] text-zinc-500">
                未在 Admin 填写时，服务端默认 15 / 30；可用环境变量 QIAZHI_V17_LLM_HTTP_TIMEOUT_SEC、QIAZHI_V17_LLM_FUSE_WAIT_TIMEOUT_SEC 覆盖默认值。
              </p>
              <div className="grid grid-cols-1 gap-3 md:grid-cols-[1fr_auto]">
                <select
                  className="w-full rounded-md border border-zinc-600 bg-zinc-800 px-3 py-2 text-sm"
                  value={llm.model}
                  onChange={(e) => setLlm((s) => ({ ...s, model: e.target.value }))}
                >
                  <option value="">请选择模型</option>
                  {llmModels.map((name) => (
                    <option key={name} value={name}>
                      {name}
                    </option>
                  ))}
                </select>
                <button type="button" disabled={busy !== null} onClick={loadLlmModels} className={ghostBtn}>
                  {busy === "loadModels" ? "拉取中..." : "拉取模型"}
                </button>
              </div>
              <div className="flex items-center gap-2">
                <button type="button" disabled={busy !== null} onClick={testLlm} className={ghostBtn}>
                  {busy === "testLlm" ? "测试中..." : "测试连接"}
                </button>
                <button type="button" disabled={busy !== null || !llm.model} onClick={testLlmChat} className={ghostBtn}>
                  {busy === "testLlmChat" ? "问答中..." : "测试问答"}
                </button>
                <button type="button" disabled={busy !== null || !llm.model} onClick={saveLlm} className={solidBtn}>
                  {busy === "saveLlm" ? "保存中..." : "保存"}
                </button>
              </div>
              <textarea
                className="min-h-[80px] w-full rounded-md border border-zinc-600 bg-zinc-800 px-3 py-2 text-sm"
                placeholder="输入测试问题"
                value={llmPrompt}
                onChange={(e) => setLlmPrompt(e.target.value)}
              />
            </div>
          ) : tab === "db" ? (
            <div className="space-y-3">
              <h2 className="text-base font-semibold text-zinc-100">数据库桥接配置 (DB Bridge)</h2>
              <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
                <input
                  className="w-full rounded-md border border-zinc-600 bg-zinc-800 px-3 py-2 text-sm"
                  placeholder="driver (postgres)"
                  title="数据库驱动，一般为 postgres"
                  value={db.driver}
                  onChange={(e) => setDb((s) => ({ ...s, driver: e.target.value }))}
                />
                <input
                  className="w-full rounded-md border border-zinc-600 bg-zinc-800 px-3 py-2 text-sm"
                  placeholder="host"
                  title="数据库地址，例如 127.0.0.1 或内网 IP"
                  value={db.host}
                  onChange={(e) => setDb((s) => ({ ...s, host: e.target.value }))}
                />
              </div>
              <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
                <input
                  className="w-full rounded-md border border-zinc-600 bg-zinc-800 px-3 py-2 text-sm"
                  placeholder="port"
                  title="数据库端口，Postgres 默认 5432"
                  value={String(db.port)}
                  onChange={(e) => setDb((s) => ({ ...s, port: Number(e.target.value || 5432) }))}
                />
                <input
                  className="w-full rounded-md border border-zinc-600 bg-zinc-800 px-3 py-2 text-sm"
                  placeholder="database"
                  title="数据库名称"
                  value={db.database}
                  onChange={(e) => setDb((s) => ({ ...s, database: e.target.value }))}
                />
              </div>
              <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
                <input
                  className="w-full rounded-md border border-zinc-600 bg-zinc-800 px-3 py-2 text-sm"
                  placeholder="username"
                  title="数据库用户名"
                  value={db.username}
                  onChange={(e) => setDb((s) => ({ ...s, username: e.target.value }))}
                />
                <input
                  type="password"
                  className="w-full rounded-md border border-zinc-600 bg-zinc-800 px-3 py-2 text-sm"
                  placeholder="password"
                  title="数据库密码"
                  value={db.password}
                  onChange={(e) => setDb((s) => ({ ...s, password: e.target.value }))}
                />
              </div>
              <input
                className="w-full rounded-md border border-zinc-600 bg-zinc-800 px-3 py-2 text-sm"
                placeholder="sslmode (disable|allow|prefer|require|verify-ca|verify-full)"
                value={db.sslmode}
                onChange={(e) => setDb((s) => ({ ...s, sslmode: e.target.value }))}
              />
              <input
                className="w-full rounded-md border border-zinc-600 bg-zinc-800 px-3 py-2 text-sm"
                placeholder="url (postgresql://user:pass@host:port/db)"
                value={db.url}
                onChange={(e) => setDb((s) => ({ ...s, url: e.target.value }))}
              />
              <label className="flex items-center gap-2 text-sm text-zinc-300">
                <input type="checkbox" checked={db.enabled} onChange={(e) => setDb((s) => ({ ...s, enabled: e.target.checked }))} />
                启用桥接
              </label>
              <div className="flex items-center gap-2">
                <button type="button" disabled={busy !== null} onClick={testDb} className={ghostBtn}>
                  {busy === "testDb" ? "测试中..." : "测试连接"}
                </button>
                <button type="button" disabled={busy !== null} onClick={saveDb} className={solidBtn}>
                  {busy === "saveDb" ? "保存中..." : "保存"}
                </button>
              </div>
            </div>
          ) : tab === "physics" ? (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h2 className="text-base font-semibold text-zinc-100">V17 宇宙常数控制塔 (The Law)</h2>
                <div className="flex gap-2">
                  <button type="button" onClick={() => setBusy("savePhysics")} className={ghostBtn}>
                    同步至全节点 (Sync All)
                  </button>
                  <button type="button" disabled={busy !== null} onClick={savePhysics} className={solidBtn}>
                    {busy === "savePhysics" ? "保存中..." : "应用物理定律"}
                  </button>
                </div>
              </div>
              
              <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
                {/* 1. L0 质量场（核心锁定） */}
                <div className={`rounded-lg border p-4 transition ${l0Locked ? "border-zinc-700 bg-zinc-900/20" : "border-red-900/50 bg-red-950/20"}`}>
                  <div className="mb-3 flex items-center justify-between">
                    <h3 className="text-xs font-semibold uppercase tracking-wider text-zinc-400">L0 质量场 (Mass Field)</h3>
                    <label className="flex items-center gap-1.5 text-[10px] text-red-500">
                      <input type="checkbox" checked={!l0Locked} onChange={(e) => setL0Locked(!e.target.checked)} />
                      解除高危锁定
                    </label>
                  </div>
                  <div className="space-y-3">
                    <label className="block text-xs text-zinc-500">
                      天干基础质量 (STEM_BASE)
                      <input 
                        type="number" disabled={l0Locked}
                        className="mt-1 w-full rounded border border-zinc-700 bg-zinc-800 px-3 py-1.5 text-sm disabled:opacity-50"
                        value={(physicsConstants.L0_FOUNDATION as LooseObject)?.STEM_BASE as number || 0}
                        onChange={(e) => setPhysicsConstants(s => ({...s, L0_FOUNDATION: {...(s.L0_FOUNDATION as LooseObject), STEM_BASE: Number(e.target.value)}}))}
                      />
                    </label>
                    <label className="block text-xs text-zinc-500">
                      地支基础质量 (BRANCH_BASE)
                      <input 
                        type="number" disabled={l0Locked}
                        className="mt-1 w-full rounded border border-zinc-700 bg-zinc-800 px-3 py-1.5 text-sm disabled:opacity-50"
                        value={(physicsConstants.L0_FOUNDATION as LooseObject)?.BRANCH_BASE as number || 0}
                        onChange={(e) => setPhysicsConstants(s => ({...s, L0_FOUNDATION: {...(s.L0_FOUNDATION as LooseObject), BRANCH_BASE: Number(e.target.value)}}))}
                      />
                    </label>
                    <label className="block text-xs text-zinc-500">
                      距离衰减指数 (DISTANCE_DECAY_EXPONENT)
                      <input 
                        type="number" step="0.05" disabled={l0Locked}
                        className="mt-1 w-full rounded border border-zinc-700 bg-zinc-800 px-3 py-1.5 text-sm disabled:opacity-50"
                        value={(physicsConstants.L0_FOUNDATION as LooseObject)?.DISTANCE_DECAY_EXPONENT as number || 0}
                        onChange={(e) => setPhysicsConstants(s => ({...s, L0_FOUNDATION: {...(s.L0_FOUNDATION as LooseObject), DISTANCE_DECAY_EXPONENT: Number(e.target.value)}}))}
                      />
                    </label>
                  </div>
                </div>

                {/* 2. L1 原子算子比例 */}
                <div className="rounded-lg border border-zinc-700 bg-zinc-950/40 p-4">
                  <h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-amber-500">L1 原子算子 (Atomic Phase)</h3>
                  <div className="space-y-3">
                    <label className="block text-xs text-zinc-400">
                      三合核心增益 (FUSION_MID_GAIN)
                      <input 
                        type="number" step="0.01"
                        className="mt-1 w-full rounded border border-zinc-600 bg-zinc-800 px-3 py-1.5 text-sm"
                        value={(physicsConstants.L1_ATOMIC as LooseObject)?.FUSION_MID_GAIN as number || 0}
                        onChange={(e) => setPhysicsConstants(s => ({...s, L1_ATOMIC: {...(s.L1_ATOMIC as LooseObject), FUSION_MID_GAIN: Number(e.target.value)}}))}
                      />
                    </label>
                    <div className="mt-2 rounded bg-zinc-900/60 p-2">
                       <p className="mb-2 text-[10px] text-emerald-500 font-bold">引雷针映射 (Induction Map)</p>
                       <div className="grid grid-cols-2 gap-2">
                         {Object.entries(((physicsConstants.L1_ATOMIC as LooseObject)?.INDUCTION_MAP as LooseObject) || {}).map(([key, val]) => (
                            <label key={key} className="block text-[10px] text-zinc-400">
                              {key}
                              <input 
                                type="number" step="0.05"
                                className="mt-1 w-full rounded border border-zinc-600 bg-zinc-800 px-2 py-1 text-xs"
                                value={val as number || 0}
                                onChange={(e) => {
                                  const newMap = { ...((physicsConstants.L1_ATOMIC as LooseObject)?.INDUCTION_MAP as LooseObject || {}), [key]: Number(e.target.value) };
                                  setPhysicsConstants(s => ({ ...s, L1_ATOMIC: {...(s.L1_ATOMIC as LooseObject), INDUCTION_MAP: newMap} }));
                                }}
                              />
                            </label>
                         ))}
                       </div>
                    </div>
                  </div>
                </div>

                {/* 3. L2 结构探测 */}
                <div className="rounded-lg border border-zinc-700 bg-zinc-950/40 p-4">
                  <h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-sky-500">L2 结构参数 (Pattern Phase)</h3>
                  <div className="space-y-3">
                    <label className="block text-xs text-zinc-400">
                      应力激活阈值 (STRESS_THRESHOLD)
                      <input 
                        type="number" step="0.1"
                        className="mt-1 w-full rounded border border-zinc-600 bg-zinc-800 px-3 py-1.5 text-sm"
                        value={(physicsConstants.L2_PATTERN as LooseObject)?.STRESS_THRESHOLD as number || 0}
                        onChange={(e) => setPhysicsConstants(s => ({...s, L2_PATTERN: {...(s.L2_PATTERN as LooseObject), STRESS_THRESHOLD: Number(e.target.value)}}))}
                      />
                    </label>
                    <label className="block text-xs text-zinc-400">
                      格局主导系数 (DOMINANT_RATIO)
                      <input 
                        type="number" step="0.01"
                        className="mt-1 w-full rounded border border-zinc-600 bg-zinc-800 px-3 py-1.5 text-sm"
                        value={(physicsConstants.L2_PATTERN as LooseObject)?.DOMINANT_RATIO as number || 0}
                        onChange={(e) => setPhysicsConstants(s => ({...s, L2_PATTERN: {...(s.L2_PATTERN as LooseObject), DOMINANT_RATIO: Number(e.target.value)}}))}
                      />
                    </label>
                  </div>
                </div>

                {/* 4. L3 系统阻尼 */}
                <div className="rounded-lg border border-zinc-700 bg-zinc-950/40 p-4">
                  <h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-fuchsia-500">L3 系统阻尼 (Narrative Phase)</h3>
                  <div className="space-y-3">
                    <label className="block text-xs text-zinc-400 flex items-center justify-between">
                      系统主摩擦力 (SYSTEM_FRICTION)
                      <input 
                        type="number" step="0.01" min="0" max="1"
                        className="mt-1 w-24 rounded border border-zinc-600 bg-zinc-800 px-2 py-1 text-sm text-right"
                        value={(physicsConstants.L3_NARRATIVE as LooseObject)?.SYSTEM_FRICTION as number || 0}
                        onChange={(e) => setPhysicsConstants(s => ({...s, L3_NARRATIVE: {...(s.L3_NARRATIVE as LooseObject), SYSTEM_FRICTION: Number(e.target.value)}}))}
                      />
                    </label>
                    <label className="flex items-center gap-2 text-xs text-zinc-300">
                      <input type="checkbox" checked={!!(physicsConstants.L3_NARRATIVE as LooseObject)?.SAFETY_CAP_ENABLED} 
                        onChange={(e) => setPhysicsConstants(s => ({...s, L3_NARRATIVE: {...(s.L3_NARRATIVE as LooseObject), SAFETY_CAP_ENABLED: e.target.checked}}))} 
                      />
                      启用身强安全阻尼 (SAFETY_CAP)
                    </label>
                    <label className="block text-xs text-zinc-400">
                      最低能级保底 (MIN_ABSOLUTE_ENERGY)
                      <input 
                        type="number" step="0.05"
                        className="mt-1 w-full rounded border border-zinc-600 bg-zinc-800 px-3 py-1.5 text-sm"
                        value={(physicsConstants.L3_NARRATIVE as LooseObject)?.MIN_ABSOLUTE_ENERGY as number || 0}
                        onChange={(e) => setPhysicsConstants(s => ({...s, L3_NARRATIVE: {...(s.L3_NARRATIVE as LooseObject), MIN_ABSOLUTE_ENERGY: Number(e.target.value)}}))}
                      />
                    </label>
                  </div>
                </div>
              </div>

              {/* 能量结算审计 */}
              <div className="rounded-lg border border-zinc-700 bg-zinc-900/40 p-4">
                <h3 className="mb-2 text-xs font-semibold text-zinc-300">仲裁序列自检 (Settlement Arbitration)</h3>
                <div className="flex flex-wrap gap-2">
                  {((physicsConstants.CALCULATION_ORDER as string[]) || []).map((step, i) => (
                    <span key={step} className="rounded border border-zinc-600 bg-zinc-800 px-2 py-1 font-mono text-[10px] text-zinc-100">
                      {i + 1}. {step}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          ) : null}

          <p className="mt-4 text-xs text-zinc-400">{msg || "配置提交将强制执行 v17_origin 协议锁。"}</p>
        </div>
      </section>
    </main>
  );
}
