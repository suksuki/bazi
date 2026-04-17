import { describe, expect, it } from "vitest";
import { syncLlmRoundsCanonical } from "../labLlmRounds";
import type { LabSnapshot } from "@/features/stream-board/stores/LabSessionContext";

describe("syncLlmRoundsCanonical", () => {
  it("builds ordered rounds from first_observation, audit, and final_verdict", () => {
    const snap = {
      ts: 1,
      first_observation_llm: {
        messages: [{ role: "system", content: "S" }],
        response_text: "首观正文",
        meta: { prompt_scenario: "first_observation" },
      },
      physics_auditor_llm: {
        messages: [{ role: "user", content: "U" }],
        response_text: '{"diagnosis":"x"}',
        meta: { prompt_scenario: "physics_audit", audit_prompt_tier: "compact" },
      },
      final_verdict: {
        version_id: "v-99",
        llm_request_messages: [{ role: "system", content: "FV" }],
        llm_raw_response: '{"verdict_body":"ok"}',
        llm_meta: { prompt_scenario: "final_verdict_decision" },
      },
    } as unknown as LabSnapshot;
    const rounds = syncLlmRoundsCanonical(null, snap, false);
    expect(rounds.map((r) => r.id)).toEqual(["round:first_observation", "round:physics_audit", "round:final_verdict:v-99"]);
    expect(rounds[2].scenario).toBe("final_verdict_decision");
  });

  it("clears prior rounds when seed universe changes", () => {
    const prev = {
      ts: 1,
      llm_rounds: [{ id: "round:first_observation", scenario: "first_observation", title_zh: "x", at: 1 }],
    } as unknown as LabSnapshot;
    const next = {
      ts: 2,
      first_observation_llm: {
        messages: [{ role: "system", content: "N" }],
        response_text: "new",
      },
    } as unknown as LabSnapshot;
    const rounds = syncLlmRoundsCanonical(prev, next, true);
    expect(rounds.some((r) => r.id === "round:first_observation")).toBe(true);
    expect(rounds.length).toBe(1);
  });
});
