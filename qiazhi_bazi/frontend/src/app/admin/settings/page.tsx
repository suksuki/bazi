"use client";

import { useEffect, useState } from "react";

const API_BASE = process.env.NEXT_PUBLIC_QIAZHI_API ?? "http://127.0.0.1:8001";
const ADMIN_TOKEN = process.env.NEXT_PUBLIC_QIAZHI_ADMIN_TOKEN ?? "";
const adminHeaders: Record<string, string> = ADMIN_TOKEN ? { "X-Admin-Token": ADMIN_TOKEN } : {};

type DbStatus = {
  ok: boolean;
  db_url?: string;
  latency_ms?: number;
  counts?: { consultation: number; decision_step: number };
  recent_raw_data?: unknown[];
  error?: string;
};

type LlmResp = {
  ok: boolean;
  language: string;
  elapsed_ms: number;
  approx_tokens_per_sec?: number | null;
  content: string;
};

const SETTINGS_KEY = "qiazhi_admin_settings_v2";

type SavedSettings = {
  dbUrl: string;
  pgHost: string;
  pgPort: string;
  pgDatabase: string;
  pgUser: string;
  pgPassword: string;
  pgSslMode: string;
  systemPrompt: string;
  userPrompt: string;
  lang: "ZH" | "EN" | "KO";
  ollamaHost: string;
  llmModel: string;
  llmApiKey: string;
};

function makePgUrl(args: {
  host: string;
  port: string;
  database: string;
  user: string;
  password: string;
  sslMode: string;
}) {
  const pwd = encodeURIComponent(args.password);
  const ssl = args.sslMode ? `?sslmode=${args.sslMode}` : "";
  return `postgresql://${args.user}:${pwd}@${args.host}:${args.port}/${args.database}${ssl}`;
}

export default function AdminSettingsPage() {
  const [db, setDb] = useState<DbStatus | null>(null);
  const [dbInitMsg, setDbInitMsg] = useState("");
  const [loadingDb, setLoadingDb] = useState(false);
  const [loadingLlm, setLoadingLlm] = useState(false);
  const [dbUrl, setDbUrl] = useState("");
  const [pgHost, setPgHost] = useState("127.0.0.1");
  const [pgPort, setPgPort] = useState("5432");
  const [pgDatabase, setPgDatabase] = useState("qiazhi_bazi");
  const [pgUser, setPgUser] = useState("");
  const [pgPassword, setPgPassword] = useState("");
  const [pgSslMode, setPgSslMode] = useState("disable");

  const [systemPrompt, setSystemPrompt] = useState("你是严谨的命理分析助手。");
  const [userPrompt, setUserPrompt] = useState("请评估‘墓库开闭’对命盘稳定性的影响。");
  const [lang, setLang] = useState<"ZH" | "EN" | "KO">("ZH");
  const [ollamaHost, setOllamaHost] = useState("http://127.0.0.1:11434");
  const [llmModel, setLlmModel] = useState("qwen2.5:32b");
  const [llmApiKey, setLlmApiKey] = useState("");
  const [modelOptions, setModelOptions] = useState<string[]>([]);
  const [loadingModels, setLoadingModels] = useState(false);
  const [modelLoadMsg, setModelLoadMsg] = useState("");
  const [llmResult, setLlmResult] = useState<LlmResp | null>(null);
  const [llmErr, setLlmErr] = useState("");
  const [llmSaveMsg, setLlmSaveMsg] = useState("");
  const [saveState, setSaveState] = useState<"idle" | "saving" | "saved" | "error">("idle");

  const dbConnected = Boolean(db?.ok);
  const effectiveBaseUrl = `${ollamaHost.replace(/\/$/, "")}/v1`;

  // 初次加载：恢复本地设置
  useEffect(() => {
    try {
      const raw = localStorage.getItem(SETTINGS_KEY);
      if (!raw) return;
      const s = JSON.parse(raw) as Partial<SavedSettings>;
      if (s.dbUrl) setDbUrl(s.dbUrl);
      if (s.pgHost) setPgHost(s.pgHost);
      if (s.pgPort) setPgPort(s.pgPort);
      if (s.pgDatabase) setPgDatabase(s.pgDatabase);
      if (s.pgUser) setPgUser(s.pgUser);
      if (typeof s.pgPassword === "string") setPgPassword(s.pgPassword);
      if (s.pgSslMode) setPgSslMode(s.pgSslMode);
      if (s.systemPrompt) setSystemPrompt(s.systemPrompt);
      if (s.userPrompt) setUserPrompt(s.userPrompt);
      if (s.lang) setLang(s.lang);
      if (s.ollamaHost) setOllamaHost(s.ollamaHost);
      if (s.llmModel) setLlmModel(s.llmModel);
      if (typeof s.llmApiKey === "string") setLlmApiKey(s.llmApiKey);
    } catch {
      // 忽略损坏的本地缓存，继续使用默认值
    }
  }, []);

  // 从后端恢复运行时配置（优先级高于本地）
  useEffect(() => {
    let cancelled = false;
    async function loadServerConfig() {
      try {
        const r = await fetch(`${API_BASE}/api/admin/runtime-config`, { headers: adminHeaders });
        if (!r.ok) return;
        const j = await r.json();
        const llm = j?.config?.llm ?? {};
        if (cancelled) return;
        if (llm.base_url && typeof llm.base_url === "string") {
          const v = llm.base_url as string;
          if (v.endsWith("/v1")) setOllamaHost(v.slice(0, -3));
          else setOllamaHost(v);
        }
        if (typeof llm.api_key === "string") setLlmApiKey(llm.api_key);
        if (typeof llm.model === "string") setLlmModel(llm.model);
      } catch {
        // 后端不可达时不阻断页面
      }
    }
    void loadServerConfig();
    return () => {
      cancelled = true;
    };
  }, []);

  async function testDb() {
    setLoadingDb(true);
    try {
      const url = dbUrl.trim();
      const r = await fetch(`${API_BASE}/api/admin/db-status`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...adminHeaders },
        body: JSON.stringify({ db_url: url || undefined }),
      });
      const j = (await r.json()) as DbStatus;
      setDb(j);
    } finally {
      setLoadingDb(false);
    }
  }

  async function initDb() {
    setDbInitMsg("执行中…");
    const url = dbUrl.trim();
    const r = await fetch(`${API_BASE}/api/admin/db-init`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...adminHeaders },
      body: JSON.stringify({ db_url: url || undefined }),
    });
    const j = await r.json();
    if (r.ok) setDbInitMsg(j.message || "完成");
    else setDbInitMsg(`失败：${j.detail ?? "unknown error"}`);
  }

  function usePgPreset() {
    setPgHost("127.0.0.1");
    setPgPort("5432");
    setPgDatabase("qiazhi_bazi");
    setPgUser("");
    setPgPassword("");
    setPgSslMode("disable");
    setDbUrl(
      makePgUrl({
        host: "127.0.0.1",
        port: "5432",
        database: "qiazhi_bazi",
        user: "",
        password: "",
        sslMode: "disable",
      })
    );
  }

  function buildPgUrl() {
    setDbUrl(
      makePgUrl({
        host: pgHost,
        port: pgPort,
        database: pgDatabase,
        user: pgUser,
        password: pgPassword,
        sslMode: pgSslMode,
      })
    );
  }

  async function loadModels(showSuccessMsg = true) {
    setLoadingModels(true);
    setLlmErr("");
    if (showSuccessMsg) setModelLoadMsg("");
    try {
      const r = await fetch(`${API_BASE}/api/admin/llm-models`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...adminHeaders },
        body: JSON.stringify({
          base_url: effectiveBaseUrl,
          api_key: llmApiKey.trim() || undefined,
        }),
      });
      const j = await r.json();
      if (!r.ok) throw new Error(j.detail ?? "模型列表读取失败");
      const items = (j.models ?? []) as string[];
      setModelOptions(items);
      if (items.length > 0) {
        setLlmModel((prev) => (prev && items.includes(prev) ? prev : items[0]));
        if (showSuccessMsg) setModelLoadMsg(`已读取 ${items.length} 个模型`);
      } else {
        if (showSuccessMsg) setModelLoadMsg("未读取到模型，请检查 URL 或服务状态");
      }
    } catch (e) {
      setLlmErr(e instanceof Error ? e.message : String(e));
    } finally {
      setLoadingModels(false);
    }
  }

  async function testLlm() {
    setLoadingLlm(true);
    setLlmErr("");
    setLlmSaveMsg("");
    try {
      if (!llmModel) {
        throw new Error("未找到可用模型，请先确认 URL 可访问并读取模型列表");
      }
      const r = await fetch(`${API_BASE}/api/admin/llm-test`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...adminHeaders },
        body: JSON.stringify({
          system_prompt: systemPrompt,
          user_prompt: userPrompt,
          language: lang,
          temperature: 0.3,
          max_tokens: 256,
          base_url: effectiveBaseUrl,
          api_key: llmApiKey.trim(),
          model: llmModel.trim(),
        }),
      });
      const j = await r.json();
      if (!r.ok) {
        setLlmErr(j.detail ?? "LLM 测试失败");
        setLlmResult(null);
        return;
      }
      setLlmResult(j as LlmResp);
      // 测试通过后立即持久化，确保与主程序 runtime config 同步
      try {
        setSaveState("saving");
        const saveR = await fetch(`${API_BASE}/api/admin/runtime-config`, {
          method: "PUT",
          headers: { "Content-Type": "application/json", ...adminHeaders },
          body: JSON.stringify({
            llm: {
              provider: "ollama",
              base_url: effectiveBaseUrl,
              api_key: llmApiKey,
              model: llmModel,
            },
          }),
        });
        if (saveR.ok) {
          // 回读核验，避免“看起来成功但其实未保存”
          const verifyR = await fetch(`${API_BASE}/api/admin/runtime-config`, {
            headers: { ...adminHeaders },
          });
          const verifyJ = await verifyR.json();
          const llm = verifyJ?.config?.llm ?? {};
          const ok =
            String(llm?.base_url ?? "") === String(effectiveBaseUrl) &&
            String(llm?.model ?? "") === String(llmModel) &&
            String(llm?.api_key ?? "") === String(llmApiKey);
          if (!ok) {
            setSaveState("error");
            setLlmSaveMsg("测试已通过，但配置回读校验失败（未真正保存）。");
            return;
          }
          setSaveState("saved");
          setLlmSaveMsg("测试通过，配置已保存并与主程序同步。");
        } else {
          setSaveState("error");
          setLlmSaveMsg("测试通过，但保存失败。请检查 admin token 或后端日志。");
        }
      } catch {
        setSaveState("error");
        setLlmSaveMsg("测试通过，但保存异常。请检查 8001 或网络连接。");
      }
    } catch (e) {
      setLlmErr(e instanceof Error ? e.message : String(e));
      setLlmResult(null);
    } finally {
      setLoadingLlm(false);
    }
  }

  // 只要 URL 变化，就自动读取模型（防抖）
  useEffect(() => {
    const t = setTimeout(() => {
      void loadModels(false);
    }, 450);
    return () => clearTimeout(t);
  }, [effectiveBaseUrl, llmApiKey]);

  // 自动保存：关键配置变化后写入本地
  useEffect(() => {
    const payload: SavedSettings = {
      dbUrl,
      pgHost,
      pgPort,
      pgDatabase,
      pgUser,
      pgPassword,
      pgSslMode,
      systemPrompt,
      userPrompt,
      lang,
      ollamaHost,
      llmModel,
      llmApiKey,
    };
    try {
      localStorage.setItem(SETTINGS_KEY, JSON.stringify(payload));
    } catch {
      // 存储失败时静默，不影响联调
    }
  }, [
    dbUrl,
    pgHost,
    pgPort,
    pgDatabase,
    pgUser,
    pgPassword,
    pgSslMode,
    systemPrompt,
    userPrompt,
    lang,
    ollamaHost,
    llmModel,
    llmApiKey,
  ]);

  // 同步 LLM 配置到后端：用户端推演读取这份配置
  useEffect(() => {
    const t = setTimeout(async () => {
      setSaveState("saving");
      try {
        const r = await fetch(`${API_BASE}/api/admin/runtime-config`, {
          method: "PUT",
          headers: { "Content-Type": "application/json", ...adminHeaders },
          body: JSON.stringify({
            llm: {
              provider: "ollama",
              base_url: effectiveBaseUrl,
              api_key: llmApiKey,
              model: llmModel,
            },
          }),
        });
        if (!r.ok) throw new Error("save failed");
        setSaveState("saved");
      } catch {
        setSaveState("error");
      }
    }, 500);
    return () => clearTimeout(t);
  }, [effectiveBaseUrl, llmApiKey, llmModel]);

  return (
    <div className="space-y-6">
      <div className="rounded-2xl border border-zinc-800 bg-gradient-to-r from-zinc-900 to-zinc-900/40 p-5">
        <h2 className="text-xl font-semibold tracking-tight">基础设施设置</h2>
        <p className="mt-1 text-sm text-zinc-400">先配地址，再点测试。默认不预填账号密码，避免敏感信息泄露。</p>
      </div>

      <div className="grid gap-3 md:grid-cols-3">
        <article className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-4">
          <p className="text-xs uppercase tracking-wide text-zinc-500">DB STATUS</p>
          <p className={`mt-2 text-lg font-semibold ${dbConnected ? "text-emerald-300" : "text-rose-300"}`}>
            {dbConnected ? "Connected" : "Unavailable"}
          </p>
          <p className="mt-1 text-xs text-zinc-500">{db?.latency_ms ?? "-"} ms</p>
        </article>
        <article className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-4">
          <p className="text-xs uppercase tracking-wide text-zinc-500">DB RECORDS</p>
          <p className="mt-2 text-lg font-semibold text-zinc-100">
            {db?.counts?.consultation ?? "-"} / {db?.counts?.decision_step ?? "-"}
          </p>
          <p className="mt-1 text-xs text-zinc-500">consultation / decision_step</p>
        </article>
        <article className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-4">
          <p className="text-xs uppercase tracking-wide text-zinc-500">LLM RESPONSE</p>
          <p className="mt-2 text-lg font-semibold text-zinc-100">{llmResult?.elapsed_ms ?? "-"} ms</p>
          <p className="mt-1 text-xs text-zinc-500">{llmResult?.approx_tokens_per_sec ?? "-"} tok/s</p>
        </article>
      </div>

      <section className="rounded-2xl border border-zinc-800 bg-zinc-900/50 p-5 shadow-lg shadow-black/20">
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-base font-medium">数据库监控（0.13）</h3>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={testDb}
              className="rounded-lg border border-zinc-700 bg-zinc-800 px-4 py-2 text-xs font-medium text-zinc-100 transition hover:bg-zinc-700"
            >
              {loadingDb ? "Testing..." : "Test DB"}
            </button>
            <button
              type="button"
              onClick={initDb}
              className="rounded-lg bg-amber-500 px-4 py-2 text-xs font-semibold text-zinc-950 transition hover:bg-amber-400"
            >
              Init / Migrate
            </button>
          </div>
        </div>
        <div className="mb-4 rounded-xl border border-zinc-800 bg-zinc-950/70 p-3">
          <div className="mb-2 flex items-center justify-between">
            <p className="text-xs uppercase tracking-wide text-zinc-500">PostgreSQL 向导</p>
            <button
              type="button"
              onClick={usePgPreset}
              className="rounded-md border border-zinc-700 bg-zinc-800 px-2 py-1 text-xs"
            >
              使用 0.13 预设
            </button>
          </div>
          <div className="grid gap-2 md:grid-cols-2">
            <input value={pgHost} onChange={(e) => setPgHost(e.target.value)} placeholder="Host" className="rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-xs outline-none focus:border-amber-500/80" />
            <input value={pgPort} onChange={(e) => setPgPort(e.target.value)} placeholder="Port" className="rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-xs outline-none focus:border-amber-500/80" />
            <input value={pgDatabase} onChange={(e) => setPgDatabase(e.target.value)} placeholder="Database" className="rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-xs outline-none focus:border-amber-500/80" />
            <input value={pgUser} onChange={(e) => setPgUser(e.target.value)} placeholder="User" className="rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-xs outline-none focus:border-amber-500/80" />
            <input value={pgPassword} onChange={(e) => setPgPassword(e.target.value)} type="password" placeholder="Password" className="rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-xs outline-none focus:border-amber-500/80" />
            <select value={pgSslMode} onChange={(e) => setPgSslMode(e.target.value)} className="rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-xs outline-none focus:border-amber-500/80">
              <option value="disable">sslmode=disable</option>
              <option value="prefer">sslmode=prefer</option>
              <option value="require">sslmode=require</option>
            </select>
          </div>
          <button
            type="button"
            onClick={buildPgUrl}
            className="mt-2 rounded-md bg-zinc-800 px-3 py-2 text-xs"
          >
            生成 DATABASE_URL
          </button>
        </div>
        <label className="block text-xs text-zinc-400">Database URL</label>
        <input
          value={dbUrl}
          onChange={(e) => setDbUrl(e.target.value)}
          placeholder="postgresql://user:password@host:5432/qiazhi_bazi?sslmode=disable"
          className="mt-1 w-full rounded-xl border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm text-zinc-100 outline-none focus:border-amber-500/80"
        />
        <p className="mt-2 text-xs text-zinc-500">可直接粘贴完整连接串；建议使用最小权限账号并妥善保管凭据。</p>
        {dbInitMsg ? (
          <p className="mt-2 rounded-md border border-zinc-700 bg-zinc-900 px-3 py-2 text-xs text-zinc-300">{dbInitMsg}</p>
        ) : null}

        <div className="mt-4 overflow-hidden rounded-xl border border-zinc-800">
          <table className="min-w-full text-left text-sm">
            <tbody className="divide-y divide-zinc-800">
              <tr>
                <td className="w-44 bg-zinc-900/70 px-3 py-2 text-zinc-500">状态</td>
                <td className="px-3 py-2">{db?.ok ? "OK" : "未检测 / FAIL"}</td>
              </tr>
              <tr>
                <td className="bg-zinc-900/70 px-3 py-2 text-zinc-500">连接</td>
                <td className="break-all px-3 py-2 text-zinc-300">{db?.db_url ?? "-"}</td>
              </tr>
              <tr>
                <td className="bg-zinc-900/70 px-3 py-2 text-zinc-500">延迟</td>
                <td className="px-3 py-2">{db?.latency_ms ?? "-"} ms</td>
              </tr>
              <tr>
                <td className="bg-zinc-900/70 px-3 py-2 text-zinc-500">错误</td>
                <td className="px-3 py-2 text-rose-300">{db?.error ?? "-"}</td>
              </tr>
              <tr>
                <td className="bg-zinc-900/70 px-3 py-2 text-zinc-500">提示</td>
                <td className="px-3 py-2 text-amber-300">{(db as { hint?: string } | null)?.hint ?? "-"}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <p className="mt-2 text-xs text-zinc-500">
          JSONB 检查：{(db as { jsonb_check?: { ok?: boolean } } | null)?.jsonb_check?.ok ? "OK" : "待验证"}
        </p>

        <p className="mt-4 text-xs uppercase tracking-wide text-zinc-500">JSONB 浏览（recent_raw_data）</p>
        <pre className="mt-2 max-h-56 overflow-auto rounded-xl border border-zinc-800 bg-zinc-950 p-3 text-[12px] leading-relaxed text-zinc-300">
          {JSON.stringify(db?.recent_raw_data ?? [], null, 2)}
        </pre>
      </section>

      <section className="rounded-2xl border border-zinc-800 bg-zinc-900/50 p-5 shadow-lg shadow-black/20">
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-base font-medium">大模型审计（0.10 Prompt Playground）</h3>
          <button
            type="button"
            onClick={testLlm}
            className="rounded-lg border border-zinc-700 bg-zinc-800 px-4 py-2 text-xs font-medium text-zinc-100 transition hover:bg-zinc-700"
          >
            {loadingLlm ? "Testing..." : "Test LLM"}
          </button>
        </div>

        <div className="mb-4 rounded-xl border border-zinc-800 bg-zinc-950/70 p-3">
          <p className="mb-2 text-xs uppercase tracking-wide text-zinc-500">Provider（固定 Ollama）</p>
          <div className="mt-3 grid gap-3 md:grid-cols-2">
            <div>
              <label className="text-xs text-zinc-400">Ollama Host</label>
              <input
                value={ollamaHost}
                onChange={(e) => setOllamaHost(e.target.value)}
                placeholder="http://192.168.0.10:11434"
                className="mt-1 w-full rounded-xl border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm outline-none focus:border-amber-500/80"
              />
            </div>
            <div>
              <label className="text-xs text-zinc-400">Effective Base URL</label>
              <input
                value={effectiveBaseUrl}
                readOnly
                className="mt-1 w-full rounded-xl border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm text-zinc-400"
              />
            </div>
          </div>
          <p className="mt-2 text-xs text-zinc-500">URL 自动补全 `/v1`，模型会自动从服务端读取。</p>
          <p className="mt-2 text-xs text-zinc-400">
            运行配置同步：
            {saveState === "saving" ? "保存中..." : null}
            {saveState === "saved" ? "已保存到后端（用户端生效）" : null}
            {saveState === "error" ? "保存失败（检查 8001）" : null}
            {saveState === "idle" ? "待同步" : null}
          </p>
        </div>

        <div>
          <label className="text-xs text-zinc-400">Model（自动从 URL 拉取）</label>
          <select
            value={llmModel}
            onChange={(e) => setLlmModel(e.target.value)}
            disabled={modelOptions.length === 0}
            className="mt-1 w-full rounded-xl border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm outline-none focus:border-amber-500/80 disabled:opacity-60"
          >
            {modelOptions.length === 0 ? <option value="">未读取到模型</option> : null}
            {modelOptions.map((m) => (
              <option key={m} value={m}>
                {m}
              </option>
            ))}
          </select>
        </div>
        <div className="mt-4">
          <label className="text-xs text-zinc-400">API Key</label>
          <input
            value={llmApiKey}
            onChange={(e) => setLlmApiKey(e.target.value)}
            className="mt-1 w-full rounded-xl border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm outline-none focus:border-amber-500/80"
          />
        </div>
        <div className="mt-2">
          <button type="button" onClick={() => loadModels(true)} className="rounded-md bg-zinc-800 px-3 py-2 text-xs">
            {loadingModels ? "连接中..." : "重新读取模型列表"}
          </button>
        </div>
        {modelLoadMsg ? <p className="mt-2 text-xs text-emerald-300">{modelLoadMsg}</p> : null}
        {llmSaveMsg ? (
          <p className={`mt-2 text-xs ${saveState === "saved" ? "text-emerald-300" : "text-rose-300"}`}>{llmSaveMsg}</p>
        ) : null}

        <div className="mt-4 grid gap-4">
          <div>
            <label className="text-xs text-zinc-400">System Prompt</label>
            <textarea
              value={systemPrompt}
              onChange={(e) => setSystemPrompt(e.target.value)}
              rows={3}
              className="mt-1 w-full rounded-xl border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm outline-none focus:border-amber-500/80"
            />
          </div>
          <div>
            <label className="text-xs text-zinc-400">User Prompt</label>
            <textarea
              value={userPrompt}
              onChange={(e) => setUserPrompt(e.target.value)}
              rows={4}
              className="mt-1 w-full rounded-xl border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm outline-none focus:border-amber-500/80"
            />
          </div>
        </div>

        <div className="mt-4 flex items-center gap-2">
          {(["ZH", "EN", "KO"] as const).map((x) => (
            <button
              key={x}
              type="button"
              onClick={() => setLang(x)}
              className={`rounded-full px-3 py-1.5 text-xs font-medium transition ${
                lang === x ? "bg-amber-500 text-zinc-950" : "border border-zinc-700 bg-zinc-800 text-zinc-300 hover:bg-zinc-700"
              }`}
            >
              {x}
            </button>
          ))}
        </div>

        {llmErr ? (
          <p className="mt-4 rounded-lg border border-rose-500/30 bg-rose-500/10 px-3 py-2 text-sm text-rose-300">{llmErr}</p>
        ) : null}

        <div className="mt-4 overflow-hidden rounded-xl border border-zinc-800">
          <table className="min-w-full text-left text-sm">
            <tbody className="divide-y divide-zinc-800">
              <tr>
                <td className="w-44 bg-zinc-900/70 px-3 py-2 text-zinc-500">语言</td>
                <td className="px-3 py-2">{llmResult?.language ?? "-"}</td>
              </tr>
              <tr>
                <td className="bg-zinc-900/70 px-3 py-2 text-zinc-500">耗时</td>
                <td className="px-3 py-2">{llmResult?.elapsed_ms ?? "-"} ms</td>
              </tr>
              <tr>
                <td className="bg-zinc-900/70 px-3 py-2 text-zinc-500">估算速度</td>
                <td className="px-3 py-2">{llmResult?.approx_tokens_per_sec ?? "-"} tok/s</td>
              </tr>
            </tbody>
          </table>
        </div>

        <p className="mt-4 text-xs uppercase tracking-wide text-zinc-500">模型输出</p>
        <pre className="mt-2 max-h-64 overflow-auto rounded-xl border border-zinc-800 bg-zinc-950 p-3 text-[12px] leading-relaxed text-zinc-300">
          {llmResult?.content ?? "等待测试输出…"}
        </pre>
      </section>
    </div>
  );
}
