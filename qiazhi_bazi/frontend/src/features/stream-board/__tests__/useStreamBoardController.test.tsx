import { act, renderHook } from "@testing-library/react";
import React, { type ReactNode } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { LabConfigProvider } from "@/features/lab-config/LabConfigContext";
import { useStreamBoardController } from "@/features/stream-board/useStreamBoardController";
import { LabStoreProvider } from "@/features/stream-board/stores/useLabStore";

function hookWrapper({ children }: { children: ReactNode }) {
  return (
    <LabStoreProvider>
      <LabConfigProvider>{children}</LabConfigProvider>
    </LabStoreProvider>
  );
}

vi.mock("swr", () => ({
  default: () => ({
    data: null,
    mutate: vi.fn(),
  }),
}));
vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: vi.fn(), push: vi.fn() }),
  usePathname: () => "/",
  useSearchParams: () => new URLSearchParams(),
}));

function jsonResponse(body: unknown, ok = true) {
  return {
    ok,
    status: ok ? 200 : 500,
    json: async () => body,
    text: async () => JSON.stringify(body),
  } as Response;
}

describe("useStreamBoardController regression", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  it("keeps the analyze-seed flow stable and auto-converts severe auditor proposals", async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.endsWith("/api/admin/db-status")) return jsonResponse({ ok: true });
      if (url.endsWith("/api/admin/runtime-config")) return jsonResponse({ config: { llm: { model: "gpt-5", base_url: "http://llm", api_key: "key" } } });
      if (url.endsWith("/api/admin/llm-models")) return jsonResponse({ ok: true, models: ["gpt-5"] });
      if (url.endsWith("/api/consultations")) return jsonResponse({ id: 99 });
      if (url.endsWith("/api/v1/analyze-seed")) {
        return jsonResponse({
          metadata: {
            version: "1",
            pillars: {
              year: { stem: "庚", branch: "午" },
              month: { stem: "甲", branch: "子" },
              day: { stem: "丙", branch: "寅" },
              hour: { stem: "辛", branch: "酉" },
            },
            flow_state: "ready",
            notes: "",
            conflict_matrix: { points: [{ kind: "clash", positions: ["year_branch", "month_branch"], detail: "子午冲" }] },
          },
          timeline: { dayun: "庚申", liunian: "丙午", reference_year: 2026 },
          llm_prompt: "系统检测到 子午冲。请选择是否深入分析该局部。",
          audit_summary: [
            { step: "01", role: "Arbiter", action: "提交输入", timestamp: "2026-04-07T00:00:00Z" },
            { step: "02", role: "Core", action: "完成排盘", timestamp: "2026-04-07T00:00:01Z" },
            { step: "03", role: "Auditor", action: "完成审计", timestamp: "2026-04-07T00:00:02Z", payload: { model_name: "gpt-5" } },
          ],
          physics_tensor: {
            normalized: { wood: 1, fire: 2, earth: 3, metal: 4, water: 5 },
            deity_scores: { 比肩: 10, 劫财: 5 },
            deity_energy_axes: { 比肩: { absolute_energy: 0.4, relative_percentage: 10 } },
            deity_components: { 比肩: { total_score: 10, root_sources: ["year_branch"] } },
            deity_trace_details: { 比肩: { stage: "rooted" } },
            audit_log: { param_version_id: "abcdef123456", trace: { hard_route_logs: ["CF_FLOATING_DECAY"] } },
            meta: { params: { CF_FLOATING_DECAY: 0.1 } },
          },
        });
      }
      if (url.endsWith("/api/v1/audit-physics-with-llm")) {
        return jsonResponse({
          alignment_score: 20,
          structured_hit: true,
          logic_proposal: {
            title: "参数校准",
            param_key: "CF_FLOATING_DECAY",
            suggested_value: 0.15,
            reason: "火势漂浮偏高",
            expected_impact: "削弱浮火",
            sql_patch: "update physics_params set value = 0.15",
          },
          causal_reasoning: "物理张量与语义张量偏离。",
          tuning_suggestions: ["降低浮火衰减"],
          top_anomaly: "火势异常",
        });
      }
      throw new Error(`Unexpected fetch: ${url}`);
    });

    vi.stubGlobal("fetch", fetchMock);

    const { result } = renderHook(() => useStreamBoardController(), { wrapper: hookWrapper });

    await act(async () => {
      const promise = result.current.onSeedSubmit({
        date: "1990-01-01",
        time: "00:00",
        calendar: "solar",
        gender: "male",
      });
      await vi.runAllTimersAsync();
      await promise;
      await vi.runAllTimersAsync();
    });

    expect(result.current.metadata?.conflict_matrix.points[0].detail).toBe("子午冲");
    expect(result.current.deityScores["比肩"]).toBe(10);
    expect(result.current.cards.some((card) => card.id.includes("llm-observe-0"))).toBe(true);
    expect(result.current.auditorProposalCards[0].proposal?.param_key).toBe("CF_FLOATING_DECAY");
    expect(result.current.autoConvertedParamKey).toBe("CF_FLOATING_DECAY");
  });
});
