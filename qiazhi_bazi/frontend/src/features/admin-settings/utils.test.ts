import { afterEach, describe, expect, it, vi } from "vitest";

import {
  buildPersistedAdminSettings,
  coerceLoopbackOllamaHttpsToHttp,
  looksLikeTutorialDatabaseUrl,
  makePgUrl,
  normalizeOllamaHostInput,
  parsePostgresUrlForWizard,
  resolveDatabaseUrlForTest,
} from "./utils";

describe("looksLikeTutorialDatabaseUrl", () => {
  it("detects doc placeholder url", () => {
    expect(looksLikeTutorialDatabaseUrl("postgresql://user:password@host:5432/qiazhi_bazi?sslmode=disable")).toBe(true);
  });

  it("does not flag real localhost urls", () => {
    expect(looksLikeTutorialDatabaseUrl("postgresql://app:secret@127.0.0.1:5432/qiazhi_bazi")).toBe(false);
  });
});

describe("admin settings utils", () => {
  it("parses postgres url into wizard fields", () => {
    const p = parsePostgresUrlForWizard("postgresql://tester:a%40b@127.0.0.1:5432/demo?sslmode=prefer");
    expect(p).toEqual({
      pgHost: "127.0.0.1",
      pgPort: "5432",
      pgDatabase: "demo",
      pgUser: "tester",
      pgPassword: "a@b",
      pgSslMode: "prefer",
    });
  });

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

  const demoWizard = {
    host: "127.0.0.1",
    port: "5432",
    database: "qiazhi_bazi",
    user: "qiazhi_admin",
    password: "secret",
    sslMode: "disable" as const,
  };

  it("resolveDatabaseUrlForTest uses wizard when dbUrl empty", () => {
    expect(resolveDatabaseUrlForTest("", demoWizard)).toBe(
      "postgresql://qiazhi_admin:secret@127.0.0.1:5432/qiazhi_bazi?sslmode=disable"
    );
  });

  it("resolveDatabaseUrlForTest prefers wizard when url omits password", () => {
    const userOnly = "postgresql://qiazhi_admin@127.0.0.1:5432/qiazhi_bazi?sslmode=disable";
    expect(resolveDatabaseUrlForTest(userOnly, demoWizard)).toBe(
      "postgresql://qiazhi_admin:secret@127.0.0.1:5432/qiazhi_bazi?sslmode=disable"
    );
  });

  it("resolveDatabaseUrlForTest keeps pasted url when it already has user and password", () => {
    const pasted = "postgresql://a:b@127.0.0.1:5432/otherdb?sslmode=require";
    expect(resolveDatabaseUrlForTest(pasted, demoWizard)).toBe(pasted);
  });

  it("resolveDatabaseUrlForTest keeps pasted url when wizard has no creds", () => {
    const pasted = "postgresql://app:pw@10.0.0.5:5432/db?sslmode=require";
    const emptyCreds = { ...demoWizard, user: "", password: "" };
    expect(resolveDatabaseUrlForTest(pasted, emptyCreds)).toBe(pasted);
  });

  it("returns a stable persisted admin settings payload (no api key field)", () => {
    const payload = buildPersistedAdminSettings({
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
    });
    expect(payload.pgDatabase).toBe("demo");
    expect(payload.llmModel).toBe("qwen");
    expect("llmApiKey" in payload).toBe(false);
  });
});

describe("coerceLoopbackOllamaHttpsToHttp", () => {
  it("rewrites https loopback Ollama port to http", () => {
    expect(coerceLoopbackOllamaHttpsToHttp("https://127.0.0.1:11434")).toBe("http://127.0.0.1:11434");
    expect(coerceLoopbackOllamaHttpsToHttp("https://localhost:11434/")).toBe("http://localhost:11434");
  });

  it("does not rewrite https on non-loopback", () => {
    expect(coerceLoopbackOllamaHttpsToHttp("https://api.openai.com")).toBe("https://api.openai.com");
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

  it("normalizes mistaken https Ollama loopback to http origin", () => {
    expect(normalizeOllamaHostInput("https://127.0.0.1:11434")).toBe("http://127.0.0.1:11434");
  });
});
