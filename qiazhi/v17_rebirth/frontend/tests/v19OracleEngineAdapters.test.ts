import { describe, expect, it } from "vitest";
import { computeOracleStateFromBirthInput } from "../components/v19/oracleEngineAdapters";

describe("V19 Oracle P3 engine adapters", () => {
  it("computes chart structure and income stability signals from solar birth input", () => {
    const state = computeOracleStateFromBirthInput({
      year: 1990,
      month: 5,
      day: 12,
      hour: 10,
      calendar_type: "solar",
      gender: "male",
    });

    expect(state.status).toBe("ok");
    if (state.status !== "ok") {
      return;
    }

    expect(state.chart.status).toBe("ok");
    expect(state.inference.supported_theme).toBe("income_stability");
    expect(state.chartSummary.signals.length).toBeGreaterThan(0);
    expect(state.inferenceSignals.defaultCollapsed).toBe(true);
    expect(state.result.summary.items.map((item) => item.key)).toEqual(["income_stability", "volatility"]);
    expect(state.evidence.evidence.length).toBe(state.inference.signals.length);
    expect(state.replay.publicSafe).toBe(true);
  });

  it("returns unsupported state for lunar input", () => {
    const state = computeOracleStateFromBirthInput({
      year: 1990,
      month: 4,
      day: 18,
      hour: 10,
      calendar_type: "lunar",
      gender: "female",
    });

    expect(state).toEqual(expect.objectContaining({ status: "unsupported", reason: "lunar_calendar_not_supported" }));
  });

  it("does not expose score, fortune, narrative, prediction, LLM, API, or DB fields", () => {
    const serialized = JSON.stringify(
      computeOracleStateFromBirthInput({
        year: 1990,
        month: 5,
        day: 12,
        hour: 10,
        calendar_type: "solar",
        gender: "male",
      }),
    );

    expect(serialized).not.toContain("score");
    expect(serialized).not.toContain("fortune");
    expect(serialized).not.toContain("narrative");
    expect(serialized).not.toContain("prediction_text");
    expect(serialized).not.toContain("llm_answer");
    expect(serialized).not.toContain("api");
    expect(serialized).not.toContain("database");
  });
});

