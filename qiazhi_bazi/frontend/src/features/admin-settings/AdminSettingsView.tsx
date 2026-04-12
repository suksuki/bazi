"use client";

import { useAdminSettingsController } from "./useAdminSettingsController";

type Controller = ReturnType<typeof useAdminSettingsController>;

function MetricsCards({ controller }: { controller: Controller }) {
  const { dbConnected, db, llmResult } = controller;
  return (
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
  );
}

function DbSection({ controller }: { controller: Controller }) {
  const {
    db,
    dbInitMsg,
    dbUrl,
    loadingDb,
    pgDatabase,
    pgHost,
    pgPassword,
    pgPort,
    pgSslMode,
    pgUser,
    setDbUrl,
    setPgDatabase,
    setPgHost,
    setPgPassword,
    setPgPort,
    setPgSslMode,
    setPgUser,
    testDb,
    initDb,
    usePgPreset,
    buildPgUrlFromFields,
  } = controller;
  return (
    <section className="rounded-2xl border border-zinc-800 bg-zinc-900/50 p-5 shadow-lg shadow-black/20">
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-base font-medium">数据库监控（本地）</h3>
        <div className="flex gap-2">
          <button type="button" onClick={testDb} className="rounded-lg border border-zinc-700 bg-zinc-800 px-4 py-2 text-xs font-medium text-zinc-100 transition hover:bg-zinc-700">
            {loadingDb ? "Testing..." : "Test DB"}
          </button>
          <button type="button" onClick={initDb} className="rounded-lg bg-amber-500 px-4 py-2 text-xs font-semibold text-zinc-950 transition hover:bg-amber-400">
            Init / Migrate
          </button>
        </div>
      </div>
      <div className="mb-4 rounded-xl border border-zinc-800 bg-zinc-950/70 p-3">
        <div className="mb-2 flex items-center justify-between">
          <p className="text-xs uppercase tracking-wide text-zinc-500">PostgreSQL 向导</p>
          <button type="button" onClick={usePgPreset} className="rounded-md border border-zinc-700 bg-zinc-800 px-2 py-1 text-xs">
            使用本地预设
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
        <button type="button" onClick={buildPgUrlFromFields} className="mt-2 rounded-md bg-zinc-800 px-3 py-2 text-xs">
          生成 DATABASE_URL
        </button>
      </div>
      <label className="block text-xs text-zinc-400">Database URL</label>
      <input value={dbUrl} onChange={(e) => setDbUrl(e.target.value)} placeholder="postgresql://user:password@host:5432/qiazhi_bazi?sslmode=disable" className="mt-1 w-full rounded-xl border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm text-zinc-100 outline-none focus:border-amber-500/80" />
      <p className="mt-2 text-xs text-zinc-500">可直接粘贴完整连接串；建议使用最小权限账号并妥善保管凭据。</p>
      {dbInitMsg ? <p className="mt-2 rounded-md border border-zinc-700 bg-zinc-900 px-3 py-2 text-xs text-zinc-300">{dbInitMsg}</p> : null}
      <div className="mt-4 overflow-hidden rounded-xl border border-zinc-800">
        <table className="min-w-full text-left text-sm"><tbody className="divide-y divide-zinc-800">
          <tr><td className="w-44 bg-zinc-900/70 px-3 py-2 text-zinc-500">状态</td><td className="px-3 py-2">{db?.ok ? "OK" : "未检测 / FAIL"}</td></tr>
          <tr><td className="bg-zinc-900/70 px-3 py-2 text-zinc-500">连接</td><td className="break-all px-3 py-2 text-zinc-300">{db?.db_url ?? "-"}</td></tr>
          <tr><td className="bg-zinc-900/70 px-3 py-2 text-zinc-500">延迟</td><td className="px-3 py-2">{db?.latency_ms ?? "-"} ms</td></tr>
          <tr><td className="bg-zinc-900/70 px-3 py-2 text-zinc-500">错误</td><td className="px-3 py-2 text-rose-300">{db?.error ?? "-"}</td></tr>
          <tr><td className="bg-zinc-900/70 px-3 py-2 text-zinc-500">提示</td><td className="px-3 py-2 text-amber-300">{db?.hint ?? "-"}</td></tr>
        </tbody></table>
      </div>
      <p className="mt-2 text-xs text-zinc-500">JSONB 检查：{db?.jsonb_check?.ok ? "OK" : "待验证"}</p>
      <p className="mt-4 text-xs uppercase tracking-wide text-zinc-500">JSONB 浏览（recent_raw_data）</p>
      <pre className="mt-2 max-h-56 overflow-auto rounded-xl border border-zinc-800 bg-zinc-950 p-3 text-[12px] leading-relaxed text-zinc-300">{JSON.stringify(db?.recent_raw_data ?? [], null, 2)}</pre>
    </section>
  );
}

function LlmSection({ controller }: { controller: Controller }) {
  const { effectiveBaseUrl, lang, llmApiKey, serverApiKeyConfigured, llmErr, llmFastPath, llmModel, llmResult, llmSaveMsg, loadingLlm, loadingModels, modelLoadMsg, modelOptions, ollamaHost, saveState, setLang, setLlmApiKey, setLlmFastPath, setLlmModel, setOllamaHost, setSystemPrompt, setUserPrompt, systemPrompt, testLlm, loadModels, userPrompt } = controller;
  return (
    <section className="rounded-2xl border border-zinc-800 bg-zinc-900/50 p-5 shadow-lg shadow-black/20">
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-base font-medium">大模型审计（0.10 Prompt Playground）</h3>
        <button type="button" onClick={testLlm} className="rounded-lg border border-zinc-700 bg-zinc-800 px-4 py-2 text-xs font-medium text-zinc-100 transition hover:bg-zinc-700">
          {loadingLlm ? "Testing..." : "Test LLM"}
        </button>
      </div>
      <div className="mb-4 rounded-xl border border-zinc-800 bg-zinc-950/70 p-3">
        <p className="mb-2 text-xs uppercase tracking-wide text-zinc-500">Provider（固定 Ollama）</p>
        <div className="mt-3 grid gap-3 md:grid-cols-2">
          <div>
            <label className="text-xs text-zinc-400">Ollama Host</label>
            <input value={ollamaHost} onChange={(e) => setOllamaHost(e.target.value)} placeholder="http://主机:端口（或仅主机名 + 环境变量补端口）" className="mt-1 w-full rounded-xl border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm outline-none focus:border-amber-500/80" />
          </div>
          <div>
            <label className="text-xs text-zinc-400">Effective Base URL</label>
            <input value={effectiveBaseUrl} readOnly className="mt-1 w-full rounded-xl border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm text-zinc-400" />
          </div>
        </div>
        <p className="mt-2 text-xs text-zinc-500">URL 自动补全 `/v1`，模型会自动从服务端读取。</p>
        <p className="mt-2 text-xs text-zinc-400">运行配置同步：{saveState === "saving" ? "保存中..." : null}{saveState === "saved" ? "已保存到后端（用户端生效）" : null}{saveState === "error" ? "保存失败（检查 8001）" : null}{saveState === "idle" ? "待同步" : null}</p>
      </div>
      <div>
        <label className="text-xs text-zinc-400">Model（自动从 URL 拉取）</label>
        <select value={llmModel} onChange={(e) => setLlmModel(e.target.value)} disabled={modelOptions.length === 0} className="mt-1 w-full rounded-xl border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm outline-none focus:border-amber-500/80 disabled:opacity-60">
          {modelOptions.length === 0 ? <option value="">未读取到模型</option> : null}
          {modelOptions.map((m) => <option key={m} value={m}>{m}</option>)}
        </select>
      </div>
      <div className="mt-4">
        <label className="text-xs text-zinc-400">API Key</label>
        <input
          value={llmApiKey}
          onChange={(e) => setLlmApiKey(e.target.value)}
          placeholder={serverApiKeyConfigured && !llmApiKey ? "服务端已保存密钥（不回显）；填写新值可覆盖" : "可选，OpenAI 兼容网关 Bearer"}
          className="mt-1 w-full rounded-xl border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm outline-none focus:border-amber-500/80"
        />
        {serverApiKeyConfigured ? <p className="mt-1 text-[11px] text-zinc-500">当前运行时已配置 API Key（列表/测试仍使用你在此输入的值；留空保存不会清除服务端密钥）。</p> : null}
      </div>
      <div className="mt-2">
        <button type="button" onClick={() => loadModels(true)} className="rounded-md bg-zinc-800 px-3 py-2 text-xs">{loadingModels ? "连接中..." : "重新读取模型列表"}</button>
      </div>
      {modelLoadMsg ? <p className="mt-2 text-xs text-emerald-300">{modelLoadMsg}</p> : null}
      {llmSaveMsg ? <p className={`mt-2 text-xs ${saveState === "saved" ? "text-emerald-300" : "text-rose-300"}`}>{llmSaveMsg}</p> : null}
      <div className="mt-4 grid gap-4">
        <div><label className="text-xs text-zinc-400">System Prompt</label><textarea value={systemPrompt} onChange={(e) => setSystemPrompt(e.target.value)} rows={3} className="mt-1 w-full rounded-xl border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm outline-none focus:border-amber-500/80" /></div>
        <div><label className="text-xs text-zinc-400">User Prompt</label><textarea value={userPrompt} onChange={(e) => setUserPrompt(e.target.value)} rows={4} className="mt-1 w-full rounded-xl border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm outline-none focus:border-amber-500/80" /></div>
      </div>
      <div className="mt-4 flex flex-wrap items-center gap-3">
        {(["ZH", "EN", "KO"] as const).map((x) => (
          <button key={x} type="button" onClick={() => setLang(x)} className={`rounded-full px-3 py-1.5 text-xs font-medium transition ${lang === x ? "bg-amber-500 text-zinc-950" : "border border-zinc-700 bg-zinc-800 text-zinc-300 hover:bg-zinc-700"}`}>{x}</button>
        ))}
        <label className="flex cursor-pointer items-center gap-2 text-xs text-zinc-400">
          <input type="checkbox" checked={llmFastPath} onChange={(e) => setLlmFastPath(e.target.checked)} className="rounded border-zinc-600 bg-zinc-900" />
          弱模型兼容（单次主调用，跳过后端二次整理 LLM）
        </label>
      </div>
      {llmErr ? <p className="mt-4 rounded-lg border border-rose-500/30 bg-rose-500/10 px-3 py-2 text-sm text-rose-300">{llmErr}</p> : null}
      <div className="mt-4 overflow-hidden rounded-xl border border-zinc-800">
        <table className="min-w-full text-left text-sm"><tbody className="divide-y divide-zinc-800">
          <tr><td className="w-44 bg-zinc-900/70 px-3 py-2 text-zinc-500">语言</td><td className="px-3 py-2">{llmResult?.language ?? "-"}</td></tr>
          <tr><td className="bg-zinc-900/70 px-3 py-2 text-zinc-500">耗时</td><td className="px-3 py-2">{llmResult?.elapsed_ms ?? "-"} ms</td></tr>
          <tr><td className="bg-zinc-900/70 px-3 py-2 text-zinc-500">估算速度</td><td className="px-3 py-2">{llmResult?.approx_tokens_per_sec ?? "-"} tok/s</td></tr>
        </tbody></table>
      </div>
      <p className="mt-4 text-xs uppercase tracking-wide text-zinc-500">模型输出</p>
      <pre className="mt-2 max-h-64 overflow-auto rounded-xl border border-zinc-800 bg-zinc-950 p-3 text-[12px] leading-relaxed text-zinc-300">{llmResult?.content ?? "等待测试输出…"}</pre>
    </section>
  );
}

export function AdminSettingsView({ controller }: { controller: Controller }) {
  return (
    <div className="space-y-6">
      <div className="rounded-2xl border border-zinc-800 bg-gradient-to-r from-zinc-900 to-zinc-900/40 p-5">
        <h2 className="text-xl font-semibold tracking-tight">基础设施设置</h2>
        <p className="mt-1 text-sm text-zinc-400">先配地址，再点测试。默认不预填账号密码，避免敏感信息泄露。</p>
      </div>
      <MetricsCards controller={controller} />
      <DbSection controller={controller} />
      <LlmSection controller={controller} />
    </div>
  );
}
