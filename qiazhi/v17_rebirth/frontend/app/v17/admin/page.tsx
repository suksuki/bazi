"use client";

import { useCallback, useEffect, useState, type Dispatch, type SetStateAction } from "react";

type TabKey = "llm" | "db" | "plugins";

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
};

const LAYER_TABS: { key: string; label: string }[] = [
  { key: "L0", label: "L0 基础场" },
  { key: "L1", label: "L1 原子算子" },
  { key: "L2", label: "L2 格局做功" },
  { key: "L3", label: "L3 现代叙事" },
];

type ActionKey =
  | "loadModels"
  | "testLlm"
  | "testLlmChat"
  | "saveLlm"
  | "testDb"
  | "saveDb"
  | "loadPlugins"
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
      const [{ data: llmData }, { data: dbData }] = await Promise.all([
        requestJson("/api/v17-admin/llm-node?v17_origin=v17_rebirth"),
        requestJson("/api/v17-admin/db-bridge?v17_origin=v17_rebirth"),
      ]);
      const llmObj = (llmData as LooseObject) || {};
      const llmNode = (llmObj.node as LooseObject) || null;
      const dbObj = (dbData as LooseObject) || {};
      applyLlmNodeToState(llmNode, setLlm);
      if (dbObj.bridge) setDb(dbObj.bridge as DbBridge);
    })();
  }, []);

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
      setMsg(resp.ok ? `LLM 配置已保存，管线已重载 epoch=${obj.pipeline_epoch ?? "?"}` : `保存失败：${obj.detail || obj.error || "unknown"}`);
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
      setMsg(obj.ok ? `LLM 测试成功：${result.probe_url || ""} (${result.http_status || ""})` : `LLM 测试失败：${obj.error || obj.detail || "unknown"}`);
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
        setMsg(`模型拉取失败：${obj.error || obj.detail || "unknown"}`);
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
      setMsg(obj.ok ? `LLM 回复：${result.reply || "(空回复)"}` : `LLM 对话测试失败：${obj.error || obj.detail || "unknown"}`);
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
      setMsg(resp.ok ? "DB Bridge 配置已保存（V17 协议锁通过）" : `保存失败：${obj.detail || obj.error || "unknown"}`);
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
      setMsg(obj.ok ? `DB 测试成功：${result.host || ""}:${result.port || ""}` : `DB 测试失败：${obj.error || obj.detail || "unknown"}`);
    } finally {
      setBusy(null);
    }
  }

  return (
    <main className="min-h-screen bg-zinc-950 text-zinc-100">
      <section className="mx-auto grid max-w-6xl grid-cols-1 gap-4 p-6 md:grid-cols-[220px_1fr]">
        <aside className="rounded-xl border border-zinc-700 bg-zinc-900 p-3">
          <h1 className="mb-3 text-sm font-semibold text-zinc-300">V17 Admin</h1>
          <button
            type="button"
            onClick={() => setTab("llm")}
            className={`mb-2 w-full rounded-md px-3 py-2 text-left text-sm ${tab === "llm" ? "bg-zinc-700 text-white" : "bg-zinc-800 text-zinc-300"}`}
          >
            LLM Node
          </button>
          <button
            type="button"
            onClick={() => setTab("db")}
            className={`mb-2 w-full rounded-md px-3 py-2 text-left text-sm ${tab === "db" ? "bg-zinc-700 text-white" : "bg-zinc-800 text-zinc-300"}`}
          >
            DB Bridge
          </button>
          <button
            type="button"
            onClick={() => setTab("plugins")}
            className={`w-full rounded-md px-3 py-2 text-left text-sm ${tab === "plugins" ? "bg-zinc-700 text-white" : "bg-zinc-800 text-zinc-300"}`}
          >
            插件 L0–L3
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
                                  <span className="block text-zinc-100">{p.module}</span>
                                  <span className="text-xs text-zinc-500">
                                    tier {p.causal_tier} · reg_p {p.registry_priority?.toFixed(2) ?? "—"} · {p.activated ? "已触发" : "未触发"}
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
                      <p className="mb-1 font-semibold text-zinc-200">{selectedPlugin.plugin_id}</p>
                      <p className="mb-3 text-xs text-zinc-500">
                        模块 {selectedPlugin.module} · {selectedPlugin.layer_dir}
                      </p>
                      <dl className="space-y-2 text-zinc-300">
                        <div>
                          <dt className="text-xs uppercase tracking-wide text-zinc-500">执行序（全管线）</dt>
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
                          <dt className="text-xs uppercase tracking-wide text-zinc-500">权力等级（causal_tier）</dt>
                          <dd className="font-mono text-lg text-amber-200">{selectedPlugin.power_tier ?? selectedPlugin.causal_tier}</dd>
                        </div>
                        <div>
                          <dt className="text-xs uppercase tracking-wide text-zinc-500">同层细排序（registry_priority）</dt>
                          <dd className="font-mono text-sm text-zinc-200">{selectedPlugin.registry_priority?.toFixed(3) ?? "—"}</dd>
                        </div>
                        <div>
                          <dt className="text-xs uppercase tracking-wide text-zinc-500">因果溯源</dt>
                          <dd className="text-sm leading-relaxed text-zinc-200">{selectedPlugin.causal_trace_text || "—"}</dd>
                        </div>
                        {selectedPlugin.executed_before_plugin_ids && selectedPlugin.executed_before_plugin_ids.length > 0 ? (
                          <div>
                            <dt className="text-xs uppercase tracking-wide text-zinc-500">上游插件 ID</dt>
                            <dd className="break-all font-mono text-xs text-zinc-400">
                              {selectedPlugin.executed_before_plugin_ids.join(" → ")}
                            </dd>
                          </div>
                        ) : null}
                        <div>
                          <dt className="text-xs uppercase tracking-wide text-zinc-500">最近写入</dt>
                          <dd className="font-mono text-xs text-zinc-400">{selectedPlugin.last_at || "—"}</dd>
                        </div>
                        <div>
                          <dt className="mb-1 text-xs uppercase tracking-wide text-zinc-500">最近一次 Facts</dt>
                          <dd>
                            {(selectedPlugin.last_facts && selectedPlugin.last_facts.length > 0) ? (
                              <ul className="list-inside list-disc space-y-1 text-zinc-200">
                                {selectedPlugin.last_facts.map((t, i) => (
                                  <li key={i}>{t}</li>
                                ))}
                              </ul>
                            ) : (
                              <span className="text-zinc-500">本期测算尚未命中该插件（Hits 为空）。</span>
                            )}
                          </dd>
                        </div>
                        {!selectedPlugin.activated ? (
                          <div className="mt-3 rounded-md border border-zinc-600 bg-zinc-900/80 p-3 text-zinc-200">
                            <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-amber-400/90">未激活占位 · 功能描述</p>
                            <p className="text-sm leading-relaxed">{selectedPlugin.function_summary || "（未配置 PLUGIN_SUMMARY）"}</p>
                            <p className="mb-1 mt-3 text-xs font-semibold uppercase tracking-wide text-amber-400/90">设计初衷</p>
                            <p className="text-sm leading-relaxed">{selectedPlugin.design_rationale || "（未配置 PLUGIN_RATIONALE）"}</p>
                          </div>
                        ) : null}
                      </dl>
                    </>
                  )}
                </aside>
              </div>
            </div>
          ) : tab === "llm" ? (
            <div className="space-y-3">
              <h2 className="text-base font-semibold text-zinc-100">LLM Node Config Shard</h2>
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
          ) : (
            <div className="space-y-3">
              <h2 className="text-base font-semibold text-zinc-100">DB Bridge Config Shard</h2>
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
          )}

          <p className="mt-4 text-xs text-zinc-400">{msg || "配置提交将强制执行 v17_origin 协议锁。"}</p>
        </div>
      </section>
    </main>
  );
}
