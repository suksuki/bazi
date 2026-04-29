import { describe, expect, it } from "vitest";
import { evaluateChartStructure } from "../lib/v19/chartStructureEngine";
import { deriveIncomeStabilityInference } from "../lib/v19/incomeStabilityInference";
import type { ChartStructureOk } from "../lib/v19/chartStructureTypes";

function okChart(input: Parameters<typeof evaluateChartStructure>[0]): ChartStructureOk {
  const chart = evaluateChartStructure(input);
  expect(chart.status).toBe("ok");
  if (chart.status !== "ok") {
    throw new Error("expected ok chart");
  }

  return chart;
}

describe("V19 income stability inference MVP", () => {
  it("derives bounded inference signals from chart structure", () => {
    const chart = okChart({
      year: 1990,
      month: 5,
      day: 12,
      hour: 10,
      calendar_type: "solar",
      gender: "male",
    });
    const bundle = deriveIncomeStabilityInference(chart);

    expect(bundle.status).toBe("ok");
    expect(bundle.supported_theme).toBe("income_stability");
    expect(bundle.signals.map((signal) => signal.key)).toEqual([
      "self_capacity",
      "wealth_presence",
      "wealth_accessibility",
      "volatility",
      "structure_binding",
      "income_stability",
    ]);
    expect(bundle.signals.every((signal) => signal.sources.length > 0)).toBe(true);
  });

  it("maps simplified day master strength to self_capacity", () => {
    const chart = okChart({
      year: 1990,
      month: 5,
      day: 12,
      hour: 10,
      calendar_type: "solar",
      gender: "male",
    });
    const bundle = deriveIncomeStabilityInference(chart);
    const selfCapacity = bundle.signals.find((signal) => signal.key === "self_capacity");

    expect(selfCapacity?.value).toMatch(/low|medium|high/);
    expect(selfCapacity?.sources).toEqual([{ source: "simplified_strength", path: "simplified_strength.tendency" }]);
  });

  it("maps direct and indirect wealth counts to wealth_presence", () => {
    const chart = okChart({
      year: 1990,
      month: 5,
      day: 12,
      hour: 10,
      calendar_type: "solar",
      gender: "male",
    });
    const bundle = deriveIncomeStabilityInference(chart);
    const wealthPresence = bundle.signals.find((signal) => signal.key === "wealth_presence");

    expect(wealthPresence?.value).toMatch(/none|low|medium|high/);
    expect(wealthPresence?.sources.map((source) => source.path)).toEqual([
      "ten_god_counts.direct_wealth",
      "ten_god_counts.indirect_wealth",
    ]);
  });

  it("detects wealth accessibility from clashes and combinations touching wealth pillars", () => {
    const chart = okChart({
      year: 2000,
      month: 1,
      day: 1,
      hour: 12,
      calendar_type: "solar",
      gender: "male",
    });
    const bundle = deriveIncomeStabilityInference(chart);
    const wealthAccessibility = bundle.signals.find((signal) => signal.key === "wealth_accessibility");

    expect(bundle.touched_wealth_pillars.length).toBeGreaterThan(0);
    expect(wealthAccessibility?.value).toMatch(/clear|bound|disrupted|conflicted|not_applicable/);
  });

  it("maps clash count to volatility and three harmony to structure_binding", () => {
    const chart = okChart({
      year: 2000,
      month: 1,
      day: 1,
      hour: 12,
      calendar_type: "solar",
      gender: "male",
    });
    const bundle = deriveIncomeStabilityInference(chart);
    const volatility = bundle.signals.find((signal) => signal.key === "volatility");
    const structureBinding = bundle.signals.find((signal) => signal.key === "structure_binding");

    expect(volatility?.value).toMatch(/low|medium|high/);
    expect(structureBinding?.value).toMatch(/none|present/);
  });

  it("does not expose score, fortune, narrative, prediction text, or llm answer", () => {
    const chart = okChart({
      year: 1990,
      month: 5,
      day: 12,
      hour: 10,
      calendar_type: "solar",
      gender: "male",
    });
    const serialized = JSON.stringify(deriveIncomeStabilityInference(chart));

    expect(serialized).not.toContain("score");
    expect(serialized).not.toContain("fortune");
    expect(serialized).not.toContain("narrative");
    expect(serialized).not.toContain("prediction");
    expect(serialized).not.toContain("llm_answer");
    expect(serialized).not.toContain("一生");
  });
});

