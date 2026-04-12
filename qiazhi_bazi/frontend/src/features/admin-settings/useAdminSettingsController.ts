"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { ADMIN_HEADERS, API_BASE, SETTINGS_KEY } from "./constants";
import { DbStatus, LlmResp, SaveState, SavedSettings } from "./types";
import { buildSavedSettings, makePgUrl, normalizeOllamaHostInput } from "./utils";

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
  const [llmFastPath, setLlmFastPath] = useState(true);
  const [modelOptions, setModelOptions] = useState<string[]>([]);
  const [loadingModels, setLoadingModels] = useState(false);
  const [modelLoadMsg, setModelLoadMsg] = useState("");
  const [llmResult, setLlmResult] = useState<LlmResp | null>(null);
  const [llmErr, setLlmErr] = useState("");
  const [llmSaveMsg, setLlmSaveMsg] = useState("");
  const [saveState, setSaveState] = useState<SaveState>("idle");

  const dbConnected = Boolean(db?.ok);
  const normalizedOllamaHost = useMemo(() => normalizeOllamaHostInput(ollamaHost), [ollamaHost]);
  const effectiveBaseUrl = useMemo(() => {
    const root = normalizedOllamaHost.replace(/\/$/, "");
    if (!root) return "";
    return `${root}/v1`;
  }, [normalizedOllamaHost]);

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
      // ignore broken local cache
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
        if (typeof llm.base_url === "string" && llm.base_url) {
          setOllamaHost(llm.base_url.endsWith("/v1") ? llm.base_url.slice(0, -3) : llm.base_url);
        }
        setServerApiKeyConfigured(Boolean(llm.api_key_configured));
        if (typeof llm.model === "string") setLlmModel(llm.model);
      } catch {
        // ignore backend outages on page load
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
      const response = await fetch(`${API_BASE}/api/admin/db-status`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...ADMIN_HEADERS },
        body: JSON.stringify({ db_url: dbUrl.trim() || undefined }),
      });
      setDb((await response.json()) as DbStatus);
    } finally {
      setLoadingDb(false);
    }
  }

  async function initDb() {
    setDbInitMsg("执行中…");
    const response = await fetch(`${API_BASE}/api/admin/db-init`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...ADMIN_HEADERS },
      body: JSON.stringify({ db_url: dbUrl.trim() || undefined }),
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
      setModelOptions(items);
      if (items.length > 0) {
        setLlmModel((prev) => (prev && items.includes(prev) ? prev : items[0]));
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
  }, [effectiveBaseUrl, llmApiKey]);

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
        setLlmSaveMsg("测试通过，但保存异常。请检查 8001 或网络连接。");
      }
      return false;
    }
  }, [effectiveBaseUrl, llmApiKey, llmModel]);

  async function testLlm() {
    setLoadingLlm(true);
    setLlmErr("");
    setLlmSaveMsg("");
    try {
      if (!effectiveBaseUrl.trim()) throw new Error("请先填写 LLM 服务地址（或设置 NEXT_PUBLIC_QIAZHI_OLLAMA_ORIGIN）并读取模型列表");
      if (!llmModel) throw new Error("未找到可用模型，请先确认 URL 可访问并读取模型列表");
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
    const payload = buildSavedSettings({
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
    });
    try {
      localStorage.setItem(SETTINGS_KEY, JSON.stringify(payload));
    } catch {
      // ignore local storage failures
    }
  }, [dbUrl, pgHost, pgPort, pgDatabase, pgUser, pgPassword, pgSslMode, systemPrompt, userPrompt, lang, ollamaHost, llmModel, llmApiKey]);

  useEffect(() => {
    const timer = setTimeout(() => {
      void syncRuntimeConfig({ showSavedMessage: false });
    }, 500);
    return () => clearTimeout(timer);
  }, [effectiveBaseUrl, llmApiKey, llmModel, syncRuntimeConfig]);

  return {
    db,
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
