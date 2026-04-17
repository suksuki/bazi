"use client";

import { useEffect, useState } from "react";

type TabKey = "llm" | "db";

type LlmNode = {
  provider: string;
  host: string;
  port: number;
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

type ActionKey = "loadModels" | "testLlm" | "testLlmChat" | "saveLlm" | "testDb" | "saveDb" | null;
type LooseObject = Record<string, unknown>;

export default function V17AdminPage() {
  const [tab, setTab] = useState<TabKey>("llm");
  const [llm, setLlm] = useState<LlmNode>({
    provider: "ollama",
    host: "192.168.0.12",
    port: 11434,
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
  const [llmPrompt, setLlmPrompt] = useState("你好，请简单自我介绍。");
  const [busy, setBusy] = useState<ActionKey>(null);

  const llmBaseUrl = `http://${llm.host}:${llm.port}/v1`;

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

  const ghostBtn =
    "cursor-pointer rounded-md border border-zinc-500 px-4 py-2 text-sm font-semibold text-zinc-200 transition hover:border-zinc-300 hover:bg-zinc-800 active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-50";
  const solidBtn =
    "cursor-pointer rounded-md bg-zinc-100 px-4 py-2 text-sm font-semibold text-zinc-900 transition hover:bg-white active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-60";

  useEffect(() => {
    void (async () => {
      const [{ data: llmData }, { data: dbData }] = await Promise.all([
        requestJson("/api/v17-admin/llm-node"),
        requestJson("/api/v17-admin/db-bridge"),
      ]);
      const llmObj = (llmData as LooseObject) || {};
      const llmNode = (llmObj.node as LooseObject) || null;
      const dbObj = (dbData as LooseObject) || {};
      if (llmNode) {
        const baseUrl = String(llmNode.base_url || "");
        let host = "192.168.0.12";
        let port = 11434;
        try {
          const parsed = new URL(baseUrl);
          host = parsed.hostname || host;
          port = Number(parsed.port || 11434);
        } catch {}
        setLlm({ provider: String(llmNode.provider || "ollama"), host, port, model: String(llmNode.model || "") });
      }
      if (dbObj.bridge) setDb(dbObj.bridge as DbBridge);
    })();
  }, []);

  async function saveLlm() {
    setBusy("saveLlm");
    try {
      const { resp, data } = await requestJson("/api/v17-admin/llm-node", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ provider: llm.provider, base_url: llmBaseUrl, model: llm.model, v17_origin: "v17_rebirth" }),
      });
      const obj = (data as LooseObject) || {};
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
