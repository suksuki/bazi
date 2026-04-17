export type DbStatus = {
  ok: boolean;
  db_url?: string;
  latency_ms?: number;
  counts?: { consultation: number; decision_step: number };
  recent_raw_data?: unknown[];
  error?: string;
  hint?: string;
  jsonb_check?: { ok?: boolean };
};

export type LlmResp = {
  ok: boolean;
  language: string;
  elapsed_ms: number;
  approx_tokens_per_sec?: number | null;
  content: string;
};

/** 可安全写入 localStorage 的管理页字段（不含 LLM API Key） */
export type PersistedAdminSettings = {
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
  /** Ollama `options` JSON（如 {"num_ctx":2048}），与后端 runtime / 环境变量合并 */
  ollamaOptionsJson?: string;
  /** 弱模型兼容开关；缺省由前端默认 true 处理 */
  llmFastPath?: boolean;
  /** 上次在本页点击 Test DB 的结果与时间（ISO），便于再次进入时提示 */
  lastDbVerifyOk?: boolean;
  lastDbVerifyAt?: string;
};

export type SaveState = "idle" | "saving" | "saved" | "error";
