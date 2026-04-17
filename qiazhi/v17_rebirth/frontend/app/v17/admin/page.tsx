"use client";

import { useEffect, useState } from "react";

type TabKey = "llm" | "db";

type LlmNode = {
  provider: string;
  base_url: string;
  username: string;
  password: string;
  api_key: string;
  model: string;
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

export default function V17AdminPage() {
  const [tab, setTab] = useState<TabKey>("llm");
  const [llm, setLlm] = useState<LlmNode>({
    provider: "ollama",
    base_url: "",
    username: "",
    password: "",
    api_key: "",
    model: "",
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

  useEffect(() => {
    void (async () => {
      const [llmResp, dbResp] = await Promise.all([
        fetch("/v17/admin/llm-node"),
        fetch("/v17/admin/db-bridge"),
      ]);
      const llmData = await llmResp.json();
      const dbData = await dbResp.json();
      if (llmData?.node) setLlm(llmData.node);
      if (dbData?.bridge) setDb(dbData.bridge);
    })();
  }, []);

  async function saveLlm() {
    const resp = await fetch("/v17/admin/llm-node", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ...llm, v17_origin: "v17_rebirth" }),
    });
    const data = await resp.json();
    setMsg(resp.ok ? `LLM 配置已保存，管线已重载 epoch=${data?.pipeline_epoch ?? "?"}` : `保存失败：${data?.detail || "unknown"}`);
  }

  async function testLlm() {
    const resp = await fetch("/v17/admin/llm-node/test", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ...llm, v17_origin: "v17_rebirth" }),
    });
    const data = await resp.json();
    setMsg(data?.ok ? `LLM 测试成功：${data?.result?.probe_url} (${data?.result?.http_status})` : `LLM 测试失败：${data?.error || data?.detail || "unknown"}`);
  }

  async function loadLlmModels() {
    const resp = await fetch("/v17/admin/llm-node/models", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ base_url: llm.base_url, v17_origin: "v17_rebirth" }),
    });
    const data = await resp.json();
    if (data?.ok) {
      const models = Array.isArray(data?.result?.models) ? data.result.models : [];
      setLlmModels(models);
      if (!llm.model && models.length > 0) {
        setLlm((s) => ({ ...s, model: String(models[0]) }));
      }
      setMsg(`模型拉取完成：${models.length} 个`);
    } else {
      setMsg(`模型拉取失败：${data?.error || data?.detail || "unknown"}`);
    }
  }

  async function saveDb() {
    const resp = await fetch("/v17/admin/db-bridge", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ...db, v17_origin: "v17_rebirth" }),
    });
    const data = await resp.json();
    setMsg(resp.ok ? "DB Bridge 配置已保存（V17 协议锁通过）" : `保存失败：${data?.detail || "unknown"}`);
  }

  async function testDb() {
    const resp = await fetch("/v17/admin/db-bridge/test", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ...db, v17_origin: "v17_rebirth" }),
    });
    const data = await resp.json();
    setMsg(data?.ok ? `DB 测试成功：${data?.result?.host}:${data?.result?.port}` : `DB 测试失败：${data?.error || data?.detail || "unknown"}`);
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
            className={`w-full rounded-md px-3 py-2 text-left text-sm ${tab === "db" ? "bg-zinc-700 text-white" : "bg-zinc-800 text-zinc-300"}`}
          >
            DB Bridge
          </button>
        </aside>

        <div className="rounded-xl border border-zinc-700 bg-zinc-900 p-5">
          {tab === "llm" ? (
            <div className="space-y-3">
              <h2 className="text-base font-semibold text-zinc-100">LLM Node Config Shard</h2>
              <input
                className="w-full rounded-md border border-zinc-600 bg-zinc-800 px-3 py-2 text-sm"
                placeholder="provider (ollama)"
                value={llm.provider}
                onChange={(e) => setLlm((s) => ({ ...s, provider: e.target.value }))}
              />
              <input
                className="w-full rounded-md border border-zinc-600 bg-zinc-800 px-3 py-2 text-sm"
                placeholder="url / base_url"
                value={llm.base_url}
                onChange={(e) => setLlm((s) => ({ ...s, base_url: e.target.value }))}
              />
              <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
                <input
                  className="w-full rounded-md border border-zinc-600 bg-zinc-800 px-3 py-2 text-sm"
                  placeholder="username"
                  value={llm.username}
                  onChange={(e) => setLlm((s) => ({ ...s, username: e.target.value }))}
                />
                <input
                  type="password"
                  className="w-full rounded-md border border-zinc-600 bg-zinc-800 px-3 py-2 text-sm"
                  placeholder="password"
                  value={llm.password}
                  onChange={(e) => setLlm((s) => ({ ...s, password: e.target.value }))}
                />
              </div>
              <input
                className="w-full rounded-md border border-zinc-600 bg-zinc-800 px-3 py-2 text-sm"
                placeholder="api_key"
                value={llm.api_key}
                onChange={(e) => setLlm((s) => ({ ...s, api_key: e.target.value }))}
              />
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
                <button type="button" onClick={loadLlmModels} className="rounded-md border border-zinc-500 px-4 py-2 text-sm font-semibold text-zinc-200">
                  拉取模型
                </button>
              </div>
              <div className="flex items-center gap-2">
                <button type="button" onClick={testLlm} className="rounded-md border border-zinc-500 px-4 py-2 text-sm font-semibold text-zinc-200">
                  测试连接
                </button>
                <button type="button" onClick={saveLlm} className="rounded-md bg-zinc-100 px-4 py-2 text-sm font-semibold text-zinc-900">
                  保存
                </button>
              </div>
            </div>
          ) : (
            <div className="space-y-3">
              <h2 className="text-base font-semibold text-zinc-100">DB Bridge Config Shard</h2>
              <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
                <input
                  className="w-full rounded-md border border-zinc-600 bg-zinc-800 px-3 py-2 text-sm"
                  placeholder="driver (postgres)"
                  value={db.driver}
                  onChange={(e) => setDb((s) => ({ ...s, driver: e.target.value }))}
                />
                <input
                  className="w-full rounded-md border border-zinc-600 bg-zinc-800 px-3 py-2 text-sm"
                  placeholder="host"
                  value={db.host}
                  onChange={(e) => setDb((s) => ({ ...s, host: e.target.value }))}
                />
              </div>
              <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
                <input
                  className="w-full rounded-md border border-zinc-600 bg-zinc-800 px-3 py-2 text-sm"
                  placeholder="port"
                  value={String(db.port)}
                  onChange={(e) => setDb((s) => ({ ...s, port: Number(e.target.value || 5432) }))}
                />
                <input
                  className="w-full rounded-md border border-zinc-600 bg-zinc-800 px-3 py-2 text-sm"
                  placeholder="database"
                  value={db.database}
                  onChange={(e) => setDb((s) => ({ ...s, database: e.target.value }))}
                />
              </div>
              <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
                <input
                  className="w-full rounded-md border border-zinc-600 bg-zinc-800 px-3 py-2 text-sm"
                  placeholder="username"
                  value={db.username}
                  onChange={(e) => setDb((s) => ({ ...s, username: e.target.value }))}
                />
                <input
                  type="password"
                  className="w-full rounded-md border border-zinc-600 bg-zinc-800 px-3 py-2 text-sm"
                  placeholder="password"
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
                <button type="button" onClick={testDb} className="rounded-md border border-zinc-500 px-4 py-2 text-sm font-semibold text-zinc-200">
                  测试连接
                </button>
                <button type="button" onClick={saveDb} className="rounded-md bg-zinc-100 px-4 py-2 text-sm font-semibold text-zinc-900">
                  保存
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
