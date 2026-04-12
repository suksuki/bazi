import { act, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { useAdminSettingsController } from "../useAdminSettingsController";

function jsonResponse(body: unknown, ok = true) {
  return {
    ok,
    status: ok ? 200 : 500,
    json: async () => body,
    text: async () => JSON.stringify(body),
  } as Response;
}

describe("useAdminSettingsController", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    localStorage.clear();
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
    localStorage.clear();
  });

  it("hydrates local settings and server runtime config", async () => {
    localStorage.setItem(
      "qiazhi_admin_settings_v2",
      JSON.stringify({
        dbUrl: "postgresql://local",
        pgHost: "127.0.0.2",
        pgPort: "5433",
        pgDatabase: "local_db",
        pgUser: "tester",
        pgPassword: "secret",
        pgSslMode: "prefer",
        systemPrompt: "sys-local",
        userPrompt: "user-local",
        lang: "KO",
        ollamaHost: "http://127.0.0.1:11435",
        llmModel: "local-model",
        llmApiKey: "local-key",
      })
    );

    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.endsWith("/api/admin/runtime-config") && (!init || init.method === undefined)) {
        return jsonResponse({
          config: { llm: { base_url: "http://10.0.0.8:11434/v1", api_key: "", api_key_configured: true, model: "server-model" } },
        });
      }
      if (url.endsWith("/api/admin/llm-models")) {
        return jsonResponse({ models: ["server-model", "other-model"] });
      }
      if (url.endsWith("/api/admin/runtime-config") && init?.method === "PUT") {
        return jsonResponse({ ok: true });
      }
      throw new Error(`Unexpected fetch: ${url}`);
    });

    vi.stubGlobal("fetch", fetchMock);

    const { result } = renderHook(() => useAdminSettingsController());

    await act(async () => {
      await vi.runAllTimersAsync();
    });

    expect(result.current.dbUrl).toBe("postgresql://local");
    expect(result.current.pgHost).toBe("127.0.0.2");
    expect(result.current.lang).toBe("KO");
    expect(result.current.ollamaHost).toBe("http://10.0.0.8:11434");
    expect(result.current.llmModel).toBe("server-model");
    expect(result.current.llmApiKey).toBe("local-key");
    expect(result.current.serverApiKeyConfigured).toBe(true);
    expect(result.current.modelOptions).toContain("server-model");
  });

  it("tests llm and persists verified runtime config", async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.endsWith("/api/admin/runtime-config") && (!init || init.method === undefined)) {
        return jsonResponse({ config: { llm: { base_url: "http://127.0.0.1:11434/v1", api_key: "", api_key_configured: false, model: "qwen2.5:32b" } } });
      }
      if (url.endsWith("/api/admin/llm-models")) {
        return jsonResponse({ models: ["qwen2.5:32b"] });
      }
      if (url.endsWith("/api/admin/llm-test")) {
        return jsonResponse({ ok: true, language: "ZH", elapsed_ms: 120, approx_tokens_per_sec: 18, content: "测试通过" });
      }
      if (url.endsWith("/api/admin/runtime-config") && init?.method === "PUT") {
        return jsonResponse({ ok: true });
      }
      throw new Error(`Unexpected fetch: ${url}`);
    });
    vi.stubGlobal("fetch", fetchMock);

    const { result } = renderHook(() => useAdminSettingsController());

    await act(async () => {
      await vi.runAllTimersAsync();
    });

    await act(async () => {
      await result.current.testLlm();
      await vi.runAllTimersAsync();
    });

    expect(result.current.llmResult?.content).toBe("测试通过");
    expect(result.current.saveState).toBe("saved");
    expect(result.current.llmSaveMsg).toContain("配置已保存");
    expect(fetchMock.mock.calls.some(([url, init]) => String(url).endsWith("/api/admin/llm-test") && (init as RequestInit)?.method === "POST")).toBe(true);
  });

  it("shows readable error when llm-test body is HTML not JSON", async () => {
    vi.useRealTimers();
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.endsWith("/api/admin/runtime-config") && (!init || init.method === undefined)) {
        return jsonResponse({ config: { llm: { base_url: "http://127.0.0.1:11434/v1", api_key: "", api_key_configured: false, model: "qwen2.5:32b" } } });
      }
      if (url.endsWith("/api/admin/llm-models")) {
        return jsonResponse({ models: ["qwen2.5:32b"] });
      }
      if (url.endsWith("/api/admin/llm-test")) {
        return {
          ok: false,
          status: 404,
          text: async () => "<html><body>Not Found</body></html>",
        } as Response;
      }
      if (url.endsWith("/api/admin/runtime-config") && init?.method === "PUT") {
        return jsonResponse({ ok: true });
      }
      throw new Error(`Unexpected fetch: ${url}`);
    });
    vi.stubGlobal("fetch", fetchMock);

    const { result } = renderHook(() => useAdminSettingsController());

    await act(async () => {
      await new Promise<void>((resolve) => {
        setTimeout(resolve, 0);
      });
    });

    expect(result.current.llmModel).toBe("qwen2.5:32b");

    await act(async () => {
      await result.current.testLlm();
    });

    expect(result.current.llmResult).toBeNull();
    expect(result.current.llmErr).toContain("不是合法 JSON");
    expect(result.current.llmErr).toContain("原文片段");
    expect(result.current.llmErr).toContain("<html>");
  });
});
