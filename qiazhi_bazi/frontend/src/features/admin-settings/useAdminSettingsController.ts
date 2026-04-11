"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { ADMIN_HEADERS, API_BASE, SETTINGS_KEY } from "./constants";
import { DbStatus, LlmResp, SaveState, SavedSettings } from "./types";
import { buildSavedSettings, makePgUrl } from "./utils";

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
  const [ollamaHost, setOllamaHost] = useState("http://127.0.0.1:11434");
  const [llmModel, setLlmModel] = useState("qwen2.5:32b");
  const [llmApiKey, setLlmApiKey] = useState("");
  const [modelOptions, setModelOptions] = useState<string[]>([]);
  const [loadingModels, setLoadingModels] = useState(false);
  const [modelLoadMsg, setModelLoadMsg] = useState("");
  const [llmResult, setLlmResult] = useState<LlmResp | null>(null);
  const [llmErr, setLlmErr] = useState("");
  const [llmSaveMsg, setLlmSaveMsg] = useState("");
  const [saveState, setSaveState] = useState<SaveState>("idle");

  const dbConnected = Boolean(db?.ok);
  const effectiveBaseUrl = useMemo(() => `${ollamaHost.replace(/\/$/, "")}/v1`, [ollamaHost]);

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
        if (typeof llm.api_key === "string") setLlmApiKey(llm.api_key);
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
    try {
      const response = await fetch(`${API_BASE}/api/admin/llm-models`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...ADMIN_HEADERS },
        body: JSON.stringify({
          base_url: effectiveBaseUrl,
          api_key: llmApiKey.trim() || undefined,
        }),
      });
      const json = await response.json();
      if (!response.ok) throw new Error(json.detail ?? "模型列表读取失败");
      const items = (json.models ?? []) as string[];
      setModelOptions(items);
      if (items.length > 0) {
        setLlmModel((prev) => (prev && items.includes(prev) ? prev : items[0]));
        if (showSuccessMsg) setModelLoadMsg(`已读取 ${items.length} 个模型`);
      } else if (showSuccessMsg) {
        setModelLoadMsg("未读取到模型，请检查 URL 或服务状态");
      }
    } catch (error) {
      setLlmErr(error instanceof Error ? error.message : String(error));
    } finally {
      setLoadingModels(false);
    }
  }, [effectiveBaseUrl, llmApiKey]);

  const syncRuntimeConfig = useCallback(async ({ showSavedMessage }: { showSavedMessage: boolean }) => {
    setSaveState("saving");
    try {
      const response = await fetch(`${API_BASE}/api/admin/runtime-config`, {
        method: "PUT",
        headers: { "Content-Type": "application/json", ...ADMIN_HEADERS },
        body: JSON.stringify({
          llm: {
            provider: "ollama",
            base_url: effectiveBaseUrl,
            api_key: llmApiKey,
            model: llmModel,
          },
        }),
      });
      if (!response.ok) throw new Error("save failed");
      if (showSavedMessage) {
        const verifyResponse = await fetch(`${API_BASE}/api/admin/runtime-config`, { headers: { ...ADMIN_HEADERS } });
        const verifyJson = await verifyResponse.json();
        const llm = verifyJson?.config?.llm ?? {};
        const ok =
          String(llm?.base_url ?? "") === String(effectiveBaseUrl) &&
          String(llm?.model ?? "") === String(llmModel) &&
          String(llm?.api_key ?? "") === String(llmApiKey);
        if (!ok) {
          setSaveState("error");
          setLlmSaveMsg("测试已通过，但配置回读校验失败（未真正保存）。");
          return false;
        }
        setSaveState("saved");
        setLlmSaveMsg("测试通过，配置已保存并与主程序同步。");
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
        }),
      });
      const json = await response.json();
      if (!response.ok) {
        setLlmErr(json.detail ?? "LLM 测试失败");
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
  }, [effectiveBaseUrl, llmApiKey]);

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
  }, [effectiveBaseUrl, llmApiKey, llmModel]);

  return {
    db,
    dbConnected,
    dbInitMsg,
    dbUrl,
    effectiveBaseUrl,
    lang,
    llmApiKey,
    llmErr,
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
