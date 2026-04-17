"use client";

import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";

import { ADMIN_HEADERS, API_BASE, SETTINGS_KEY } from "./constants";
import { DbStatus, LlmResp, PersistedAdminSettings, SaveState } from "./types";
import {
  buildPersistedAdminSettings,
  looksLikeTutorialDatabaseUrl,
  makePgUrl,
  normalizeOllamaHostInput,
  parsePostgresUrlForWizard,
  resolveDatabaseUrlForTest,
} from "./utils";

export function useAdminSettingsController() {
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
  const [ollamaHost, setOllamaHost] = useState("");
  const [llmModel, setLlmModel] = useState("");
  const [llmApiKey, setLlmApiKey] = useState("");
  /** 服务端已持久化 api_key（GET 不再回显明文） */
  const [serverApiKeyConfigured, setServerApiKeyConfigured] = useState(false);
  /** 默认开启：跳过后端二次 LLM 重写/压缩，减轻弱模型与 nginx 超时压力 */
  const [ollamaOptionsJson, setOllamaOptionsJson] = useState("");
  const [llmFastPath, setLlmFastPath] = useState(true);
  /** 首屏先从 localStorage 恢复，再允许写入，避免默认值覆盖已存配置 */
  const [localPrefsReady, setLocalPrefsReady] = useState(false);
  const persistedOllamaRef = useRef(false);
  const persistedModelRef = useRef(false);
  const [lastDbVerifyOk, setLastDbVerifyOk] = useState(false);
  const [lastDbVerifyAt, setLastDbVerifyAt] = useState("");
  const [modelOptions, setModelOptions] = useState<string[]>([]);
  const [loadingModels, setLoadingModels] = useState(false);
  const [modelLoadMsg, setModelLoadMsg] = useState("");
  const [llmResult, setLlmResult] = useState<LlmResp | null>(null);
  const [llmErr, setLlmErr] = useState("");
  const [llmSaveMsg, setLlmSaveMsg] = useState("");
  const [saveState, setSaveState] = useState<SaveState>("idle");

  const dbConnected = Boolean(db?.ok);
  const normalizedOllamaHost = useMemo(() => normalizeOllamaHostInput(ollamaHost), [ollamaHost]);
  const lastDbVerifySummary = useMemo(() => {
    if (!lastDbVerifyAt.trim()) return "";
    let when = lastDbVerifyAt;
    try {
      when = new Intl.DateTimeFormat("zh-CN", { dateStyle: "short", timeStyle: "short" }).format(new Date(lastDbVerifyAt));
    } catch {
      /* keep ISO */
    }
    return lastDbVerifyOk ? `上次在本页 Test DB：成功（${when}）` : `上次在本页 Test DB：失败（${when}）`;
  }, [lastDbVerifyAt, lastDbVerifyOk]);
  const effectiveBaseUrl = useMemo(() => {
    const root = normalizedOllamaHost.replace(/\/$/, "");
    if (!root) return "";
    return `${root}/v1`;
  }, [normalizedOllamaHost]);

  useLayoutEffect(() => {
    persistedOllamaRef.current = false;
    persistedModelRef.current = false;
    try {
      const raw = localStorage.getItem(SETTINGS_KEY);
      if (!raw) return;
      const parsed = JSON.parse(raw) as Partial<PersistedAdminSettings> & { llmApiKey?: string };
      let migrated = false;
      if ("llmApiKey" in parsed) {
        delete (parsed as { llmApiKey?: string }).llmApiKey;
        migrated = true;
      }
      if (migrated) {
        try {
          localStorage.setItem(SETTINGS_KEY, JSON.stringify(parsed));
        } catch {
          /* ignore quota / private mode */
        }
      }
      const urlParts = parsed.dbUrl ? parsePostgresUrlForWizard(parsed.dbUrl) : null;
      if (parsed.dbUrl) setDbUrl(parsed.dbUrl);
      if (parsed.pgHost) setPgHost(parsed.pgHost);
      else if (urlParts?.pgHost) setPgHost(urlParts.pgHost);
      if (parsed.pgPort) setPgPort(parsed.pgPort);
      else if (urlParts?.pgPort) setPgPort(urlParts.pgPort);
      if (parsed.pgDatabase) setPgDatabase(parsed.pgDatabase);
      else if (urlParts?.pgDatabase) setPgDatabase(urlParts.pgDatabase);
      if (parsed.pgUser !== undefined && String(parsed.pgUser).trim() !== "") setPgUser(String(parsed.pgUser));
      else if (urlParts) setPgUser(urlParts.pgUser);
      if (typeof parsed.pgPassword === "string" && parsed.pgPassword !== "") setPgPassword(parsed.pgPassword);
      else if (urlParts) setPgPassword(urlParts.pgPassword);
      if (parsed.pgSslMode) setPgSslMode(parsed.pgSslMode);
      else if (urlParts?.pgSslMode) setPgSslMode(urlParts.pgSslMode);
      if (parsed.systemPrompt) setSystemPrompt(parsed.systemPrompt);
      if (parsed.userPrompt) setUserPrompt(parsed.userPrompt);
      if (parsed.lang) setLang(parsed.lang);
      if (typeof parsed.ollamaHost === "string" && parsed.ollamaHost.trim()) {
        persistedOllamaRef.current = true;
        setOllamaHost(normalizeOllamaHostInput(parsed.ollamaHost));
      }
      if (typeof parsed.llmModel === "string" && parsed.llmModel.trim()) {
        persistedModelRef.current = true;
        setLlmModel(parsed.llmModel);
      }
      if (typeof parsed.ollamaOptionsJson === "string") setOllamaOptionsJson(parsed.ollamaOptionsJson);
      if (typeof parsed.llmFastPath === "boolean") setLlmFastPath(parsed.llmFastPath);
      if (typeof parsed.lastDbVerifyOk === "boolean") setLastDbVerifyOk(parsed.lastDbVerifyOk);
      if (typeof parsed.lastDbVerifyAt === "string") setLastDbVerifyAt(parsed.lastDbVerifyAt);
      /* llmApiKey 仅内存态，不从 localStorage 回填、也不持久化 */
    } catch {
      // ignore broken local cache
    } finally {
      setLocalPrefsReady(true);
    }
  }, []);

  useEffect(() => {
    let cancelled = false;
    async function loadServerConfig() {
      try {
        const response = await fetch(`${API_BASE}/api/admin/runtime-config`, { headers: ADMIN_HEADERS });
        if (!response.ok) return;
        const json = await response.json();
        const llm = json?.config?.llm ?? {};
        if (cancelled) return;
        if (typeof llm.base_url === "string" && llm.base_url && !persistedOllamaRef.current) {
          const root = llm.base_url.endsWith("/v1") ? llm.base_url.slice(0, -3) : llm.base_url;
          setOllamaHost(normalizeOllamaHostInput(root));
        }
        setServerApiKeyConfigured(Boolean(llm.api_key_configured));
        if (typeof llm.model === "string" && llm.model && !persistedModelRef.current) {
          setLlmModel(llm.model);
        }
        const oo = llm?.ollama_options;
        if (oo && typeof oo === "object" && !Array.isArray(oo)) {
          setOllamaOptionsJson((prev) => (prev.trim() ? prev : JSON.stringify(oo, null, 2)));
        }
      } catch {
        // ignore backend outages on page load
      }
    }
    void loadServerConfig();
    return () => {
      cancelled = true;
    };
  }, []);

  function wizardPgFields() {
    return {
      host: pgHost,
      port: pgPort,
      database: pgDatabase,
      user: pgUser,
      password: pgPassword,
      sslMode: pgSslMode,
    };
  }

  async function testDb() {
    setLoadingDb(true);
    try {
      const effectiveUrl = resolveDatabaseUrlForTest(dbUrl, wizardPgFields());
      if (effectiveUrl.trim() !== dbUrl.trim()) {
        setDbUrl(effectiveUrl);
      }
      if (looksLikeTutorialDatabaseUrl(effectiveUrl)) {
        setLastDbVerifyOk(false);
        setLastDbVerifyAt(new Date().toISOString());
        setDb({
          ok: false,
          error: "Database URL 仍是文档示例占位符",
          hint: "向导里用户名/密码为空，且连接串里是字面量 user:password@host。请填写真实账号并点「生成 DATABASE_URL」，或粘贴真实 postgresql:// 连接串。",
        });
        return;
      }
      const response = await fetch(`${API_BASE}/api/admin/db-status`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...ADMIN_HEADERS },
        body: JSON.stringify({ db_url: effectiveUrl.trim() || undefined }),
      });
      const raw = await response.text();
      let json: Record<string, unknown>;
      try {
        json = raw.trim() ? (JSON.parse(raw) as Record<string, unknown>) : {};
      } catch {
        const snippet = raw.replace(/\s+/g, " ").trim().slice(0, 400);
        setLastDbVerifyOk(false);
        setLastDbVerifyAt(new Date().toISOString());
        setDb({
          ok: false,
          error: `响应不是合法 JSON（HTTP ${response.status}）`,
          hint: `多为管理接口未指到 FastAPI、未带 X-Admin-Token（NEXT_PUBLIC_QIAZHI_ADMIN_TOKEN）或网关返回了 HTML。片段：${snippet || "(空)"}`,
        });
        return;
      }
      if (!response.ok) {
        const d = json.detail;
        const detailStr =
          d == null
            ? ""
            : typeof d === "string"
              ? d
              : Array.isArray(d)
                ? d.map((x) => (typeof x === "object" && x && "msg" in x ? String((x as { msg: string }).msg) : String(x))).join("; ")
                : JSON.stringify(d);
        setLastDbVerifyOk(false);
        setLastDbVerifyAt(new Date().toISOString());
        setDb({
          ok: false,
          error: detailStr || `Test DB 失败（HTTP ${response.status}）`,
          hint: "请确认 FastAPI 已启动、NEXT_PUBLIC_QIAZHI_API 指向后端，且前后端 QIAZHI_ADMIN_TOKEN / NEXT_PUBLIC_QIAZHI_ADMIN_TOKEN 一致。",
        });
        return;
      }
      setLastDbVerifyOk(Boolean((json as DbStatus).ok));
      setLastDbVerifyAt(new Date().toISOString());
      setDb(json as DbStatus);
    } catch (error) {
      setLastDbVerifyOk(false);
      setLastDbVerifyAt(new Date().toISOString());
      setDb({
        ok: false,
        error: error instanceof Error ? error.message : String(error),
        hint: "浏览器无法访问 API（Failed to fetch 等）。请检查 NEXT_PUBLIC_QIAZHI_API、HTTPS/混合内容、防火墙与后端是否监听。",
      });
    } finally {
      setLoadingDb(false);
    }
  }

  async function initDb() {
    setDbInitMsg("执行中…");
    const effectiveUrl = resolveDatabaseUrlForTest(dbUrl, wizardPgFields());
    if (effectiveUrl.trim() !== dbUrl.trim()) {
      setDbUrl(effectiveUrl);
    }
    const response = await fetch(`${API_BASE}/api/admin/db-init`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...ADMIN_HEADERS },
      body: JSON.stringify({ db_url: effectiveUrl.trim() || undefined }),
    });
    const json = await response.json();
    setDbInitMsg(response.ok ? json.message || "完成" : `失败：${json.detail ?? "unknown error"}`);
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

  function buildPgUrlFromFields() {
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

  const loadModels = useCallback(async (showSuccessMsg = true) => {
    setLoadingModels(true);
    setLlmErr("");
    if (showSuccessMsg) setModelLoadMsg("");
    if (!effectiveBaseUrl.trim()) {
      if (showSuccessMsg) {
        setModelLoadMsg("请填写 LLM 服务地址，或设置 NEXT_PUBLIC_QIAZHI_OLLAMA_ORIGIN。");
      }
      setLoadingModels(false);
      return;
    }
    try {
      const ctrl = new AbortController();
      const timer = window.setTimeout(() => ctrl.abort(), 45_000);
      let response: Response;
      try {
        response = await fetch(`${API_BASE}/api/admin/llm-models`, {
          method: "POST",
          headers: { "Content-Type": "application/json", ...ADMIN_HEADERS },
          body: JSON.stringify({
            base_url: effectiveBaseUrl,
            api_key: llmApiKey.trim() || undefined,
          }),
          signal: ctrl.signal,
        });
      } finally {
        window.clearTimeout(timer);
      }
      let json: { detail?: unknown; models?: unknown } = {};
      try {
        json = (await response.json()) as typeof json;
      } catch {
        json = {};
      }
      const detailStr = (() => {
        const d = json?.detail;
        if (d == null) return "";
        if (typeof d === "string") return d;
        if (Array.isArray(d)) return d.map((x) => (typeof x === "object" && x && "msg" in x ? String((x as { msg: string }).msg) : String(x))).join("; ");
        return JSON.stringify(d);
      })();
      if (!response.ok) throw new Error(detailStr || `模型列表读取失败（HTTP ${response.status}）`);
      const items = (json.models ?? []) as string[];
      const current = llmModel.trim();
      const merged = current && !items.includes(current) ? [current, ...items] : items;
      setModelOptions(merged);
      if (merged.length > 0) {
        setLlmModel((prev) => {
          const p = (prev || "").trim();
          if (p && merged.includes(p)) return p;
          return merged[0];
        });
        if (showSuccessMsg) setModelLoadMsg(`已读取 ${items.length} 个模型`);
      } else if (showSuccessMsg) {
        setModelLoadMsg(
          "未读取到模型：请确认服务已监听、后端 QIAZHI_ALLOWED_HOSTS 包含该主机，或在本机 backend 运行 scripts/smoke_llm_models_fetch.py 并传入 --base-url。",
        );
      }
    } catch (error) {
      if (error instanceof Error && error.name === "AbortError") {
        setLlmErr("拉取模型超时（45s）。请检查 API 网关与后端到 Ollama 的网络。");
      } else {
        setLlmErr(error instanceof Error ? error.message : String(error));
      }
    } finally {
      setLoadingModels(false);
    }
  }, [effectiveBaseUrl, llmApiKey, llmModel]);

  const syncRuntimeConfig = useCallback(async ({ showSavedMessage }: { showSavedMessage: boolean }) => {
    if (!effectiveBaseUrl.trim()) {
      setSaveState("idle");
      return true;
    }
    setSaveState("saving");
    try {
      const llmPayload: Record<string, unknown> = {
        provider: "ollama",
        base_url: effectiveBaseUrl,
        model: llmModel,
      };
      if (llmApiKey.trim()) {
        llmPayload.api_key = llmApiKey.trim();
      }
      const ooRaw = ollamaOptionsJson.trim();
      if (ooRaw) {
        try {
          const parsed = JSON.parse(ooRaw) as unknown;
          if (parsed && typeof parsed === "object" && !Array.isArray(parsed)) {
            llmPayload.ollama_options = parsed;
          }
        } catch {
          if (showSavedMessage) {
            setSaveState("error");
            setLlmSaveMsg("Ollama options 不是合法 JSON，已跳过写入 runtime。");
            return false;
          }
        }
      }
      const response = await fetch(`${API_BASE}/api/admin/runtime-config`, {
        method: "PUT",
        headers: { "Content-Type": "application/json", ...ADMIN_HEADERS },
        body: JSON.stringify({ llm: llmPayload }),
      });
      if (!response.ok) throw new Error("save failed");
      if (showSavedMessage) {
        const verifyResponse = await fetch(`${API_BASE}/api/admin/runtime-config`, { headers: { ...ADMIN_HEADERS } });
        const verifyJson = await verifyResponse.json();
        const llm = verifyJson?.config?.llm ?? {};
        const baseModelOk =
          String(llm?.base_url ?? "") === String(effectiveBaseUrl) && String(llm?.model ?? "") === String(llmModel);
        if (!baseModelOk) {
          setSaveState("error");
          setLlmSaveMsg("测试已通过，但配置回读校验失败（未真正保存）。");
          return false;
        }
        setSaveState("saved");
        setLlmSaveMsg("测试通过，配置已保存并与主程序同步。");
        setServerApiKeyConfigured(Boolean(llm?.api_key_configured));
        return true;
      }
      setSaveState("saved");
      return true;
    } catch {
      setSaveState("error");
      if (showSavedMessage) {
        setLlmSaveMsg(
          `测试通过，但保存 runtime_config 失败。请确认 FastAPI 已启动、${API_BASE || "NEXT_PUBLIC_QIAZHI_API"} 可访问，并已配置 NEXT_PUBLIC_QIAZHI_ADMIN_TOKEN。`,
        );
      }
      return false;
    }
  }, [effectiveBaseUrl, llmApiKey, llmModel, ollamaOptionsJson]);

  async function testLlm() {
    setLoadingLlm(true);
    setLlmErr("");
    setLlmSaveMsg("");
    try {
      if (!effectiveBaseUrl.trim()) throw new Error("请先填写 LLM 服务地址（或设置 NEXT_PUBLIC_QIAZHI_OLLAMA_ORIGIN）并读取模型列表");
      if (!llmModel) throw new Error("未找到可用模型，请先确认 URL 可访问并读取模型列表");
      let ollamaOptions: Record<string, unknown> | undefined;
      const ooTrim = ollamaOptionsJson.trim();
      if (ooTrim) {
        try {
          const parsed = JSON.parse(ooTrim) as unknown;
          if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
            throw new Error("须为 JSON 对象");
          }
          ollamaOptions = parsed as Record<string, unknown>;
        } catch {
          throw new Error("Ollama options（JSON）解析失败，请检查语法或留空。");
        }
      }
      const response = await fetch(`${API_BASE}/api/admin/llm-test`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...ADMIN_HEADERS },
        body: JSON.stringify({
          system_prompt: systemPrompt,
          user_prompt: userPrompt,
          language: lang,
          temperature: 0.3,
          max_tokens: 256,
          base_url: effectiveBaseUrl,
          api_key: llmApiKey.trim(),
          model: llmModel.trim(),
          fast_path: llmFastPath,
          ...(ollamaOptions ? { ollama_options: ollamaOptions } : {}),
        }),
      });
      const raw = await response.text();
      let json: Record<string, unknown>;
      try {
        json = raw.trim() ? (JSON.parse(raw) as Record<string, unknown>) : {};
      } catch {
        const snippet = raw.replace(/\s+/g, " ").trim().slice(0, 400);
        const is504 = response.status === 504 || /504|Gateway Time-?out/i.test(snippet);
        const nginxHint = is504
          ? " 若为 nginx 504，多为上游推理超时：可提高 `proxy_read_timeout`（如 300s），并在本页开启「弱模型兼容」以只跑一次主模型。"
          : "";
        setLlmErr(
          `响应不是合法 JSON（HTTP ${response.status}）。多为管理接口未指到 FastAPI 而返回了 HTML，或网关超时。请检查 NEXT_PUBLIC_QIAZHI_API / 反向代理。${nginxHint}原文片段：${snippet || "(空)"}`,
        );
        setLlmResult(null);
        return;
      }
      if (!response.ok) {
        const d = json.detail;
        const detailStr =
          d == null
            ? ""
            : typeof d === "string"
              ? d
              : Array.isArray(d)
                ? d.map((x) => (typeof x === "object" && x && "msg" in x ? String((x as { msg: string }).msg) : String(x))).join("; ")
                : JSON.stringify(d);
        setLlmErr(detailStr || `LLM 测试失败（HTTP ${response.status}）`);
        setLlmResult(null);
        return;
      }
      setLlmResult(json as LlmResp);
      const saved = await syncRuntimeConfig({ showSavedMessage: true });
      if (!saved && !llmSaveMsg) {
        setLlmSaveMsg("测试通过，但保存失败。请检查 admin token 或后端日志。");
      }
    } catch (error) {
      setLlmErr(error instanceof Error ? error.message : String(error));
      setLlmResult(null);
    } finally {
      setLoadingLlm(false);
    }
  }

  useEffect(() => {
    const timer = setTimeout(() => {
      void loadModels(false);
    }, 450);
    return () => clearTimeout(timer);
  }, [effectiveBaseUrl, llmApiKey, loadModels]);

  useEffect(() => {
    if (!localPrefsReady) return;
    const payload = buildPersistedAdminSettings({
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
      ollamaOptionsJson,
      llmFastPath,
      lastDbVerifyOk,
      lastDbVerifyAt,
    });
    try {
      localStorage.setItem(SETTINGS_KEY, JSON.stringify(payload));
    } catch {
      // ignore local storage failures
    }
  }, [
    localPrefsReady,
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
    ollamaOptionsJson,
    llmFastPath,
    lastDbVerifyOk,
    lastDbVerifyAt,
  ]);

  useEffect(() => {
    const timer = setTimeout(() => {
      void syncRuntimeConfig({ showSavedMessage: false });
    }, 500);
    return () => clearTimeout(timer);
  }, [effectiveBaseUrl, llmApiKey, llmModel, ollamaOptionsJson, syncRuntimeConfig]);

  return {
    db,
    lastDbVerifySummary,
    dbConnected,
    dbInitMsg,
    dbUrl,
    effectiveBaseUrl,
    lang,
    llmApiKey,
    serverApiKeyConfigured,
    llmErr,
    llmFastPath,
    llmModel,
    ollamaOptionsJson,
    llmResult,
    llmSaveMsg,
    loadingDb,
    loadingLlm,
    loadingModels,
    modelLoadMsg,
    modelOptions,
    ollamaHost,
    pgDatabase,
    pgHost,
    pgPassword,
    pgPort,
    pgSslMode,
    pgUser,
    saveState,
    systemPrompt,
    testDb,
    initDb,
    usePgPreset,
    buildPgUrlFromFields,
    loadModels,
    testLlm,
    setDbUrl,
    setLang,
    setLlmApiKey,
    setLlmFastPath,
    setLlmModel,
    setOllamaOptionsJson,
    setOllamaHost,
    setPgDatabase,
    setPgHost,
    setPgPassword,
    setPgPort,
    setPgSslMode,
    setPgUser,
    setSystemPrompt,
    setUserPrompt,
    userPrompt,
  };
}
