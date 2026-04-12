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
};

export type SaveState = "idle" | "saving" | "saved" | "error";
