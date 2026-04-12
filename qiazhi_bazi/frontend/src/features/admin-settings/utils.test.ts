import { afterEach, describe, expect, it, vi } from "vitest";

import { buildSavedSettings, makePgUrl, normalizeOllamaHostInput } from "./utils";

describe("admin settings utils", () => {
  it("builds postgres urls with encoded password", () => {
    expect(
      makePgUrl({
        host: "127.0.0.1",
        port: "5432",
        database: "demo",
        user: "tester",
        password: "a@b",
        sslMode: "disable",
      })
    ).toBe("postgresql://tester:a%40b@127.0.0.1:5432/demo?sslmode=disable");
  });

  it("returns a stable saved settings payload", () => {
    const payload = buildSavedSettings({
      dbUrl: "postgresql://demo",
      pgHost: "127.0.0.1",
      pgPort: "5432",
      pgDatabase: "demo",
      pgUser: "tester",
      pgPassword: "secret",
      pgSslMode: "disable",
      systemPrompt: "sys",
      userPrompt: "user",
      lang: "ZH",
      ollamaHost: "http://127.0.0.1:11434",
      llmModel: "qwen",
      llmApiKey: "key",
    });
    expect(payload.pgDatabase).toBe("demo");
    expect(payload.llmModel).toBe("qwen");
  });
});

describe("normalizeOllamaHostInput", () => {
  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it("returns empty when input empty and no origin env", () => {
    vi.stubEnv("NEXT_PUBLIC_QIAZHI_OLLAMA_ORIGIN", "");
    expect(normalizeOllamaHostInput("")).toBe("");
  });

  it("uses NEXT_PUBLIC_QIAZHI_OLLAMA_ORIGIN when input empty", () => {
    vi.stubEnv("NEXT_PUBLIC_QIAZHI_OLLAMA_ORIGIN", "http://localhost:11434/");
    expect(normalizeOllamaHostInput("")).toBe("http://localhost:11434");
  });
});
