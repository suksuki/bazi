import { describe, expect, it } from "vitest";
import { detectBranchRelations, evaluateChartStructure } from "../lib/v19/chartStructureEngine";
import type { BirthInput } from "../lib/v19/chartStructureTypes";

describe("V19 Chart Structure Engine MVP", () => {
  it("generates four pillars from solar birth input", () => {
    const input: BirthInput = {
      year: 2000,
      month: 1,
      day: 1,
      hour: 12,
      calendar_type: "solar",
      gender: "male",
    };

    const result = evaluateChartStructure(input);

    expect(result.status).toBe("ok");
    if (result.status !== "ok") {
      return;
    }

    expect(result.pillars.year.display).toBe("己卯");
    expect(result.pillars.month.display).toBe("丙子");
    expect(result.pillars.day.display).toBe("戊午");
    expect(result.pillars.hour.display).toBe("戊午");
  });

  it("identifies day master from the day pillar", () => {
    const result = evaluateChartStructure({
      year: 2000,
      month: 1,
      day: 1,
      hour: 12,
      calendar_type: "solar",
      gender: "female",
    });

    expect(result.status).toBe("ok");
    if (result.status !== "ok") {
      return;
    }

    expect(result.day_master).toEqual({
      stem: "戊",
      element: "earth",
      yin_yang: "yang",
    });
  });

  it("outputs five element counts and ten god counts", () => {
    const result = evaluateChartStructure({
      year: 1990,
      month: 5,
      day: 12,
      hour: 10,
      calendar_type: "solar",
      gender: "male",
    });

    expect(result.status).toBe("ok");
    if (result.status !== "ok") {
      return;
    }

    expect(Object.values(result.five_element_counts).reduce((sum, value) => sum + value, 0)).toBe(8);
    expect(Object.values(result.ten_god_counts).reduce((sum, value) => sum + value, 0)).toBe(7);
    expect(result.chart_structure_summary.length).toBeGreaterThanOrEqual(5);
    expect(result.simplified_strength.tendency).toMatch(/weak|balanced|strong/);
  });

  it("detects six combination, six clash, and three harmony branch relations", () => {
    const relations = detectBranchRelations([
      { pillarName: "year", branch: "子" },
      { pillarName: "month", branch: "丑" },
      { pillarName: "day", branch: "午" },
      { pillarName: "hour", branch: "辰" },
      { pillarName: "hour", branch: "申" },
    ]);

    expect(relations).toEqual(
      expect.arrayContaining([
        expect.objectContaining({ type: "six_combination", branches: ["子", "丑"] }),
        expect.objectContaining({ type: "six_clash", branches: ["子", "午"] }),
        expect.objectContaining({ type: "three_harmony", branches: ["申", "子", "辰"], element: "water" }),
      ]),
    );
  });

  it("returns unsupported for lunar input", () => {
    const result = evaluateChartStructure({
      year: 1990,
      month: 4,
      day: 18,
      hour: 10,
      calendar_type: "lunar",
      gender: "female",
    });

    expect(result).toEqual(
      expect.objectContaining({
        status: "unsupported",
        reason: "lunar_calendar_not_supported",
      }),
    );
  });

  it("does not expose prediction fields in the structure result", () => {
    const result = evaluateChartStructure({
      year: 1990,
      month: 5,
      day: 12,
      hour: 10,
      calendar_type: "solar",
      gender: "male",
    });
    const serialized = JSON.stringify(result);

    expect(serialized).not.toContain("score");
    expect(serialized).not.toContain("fortune");
    expect(serialized).not.toContain("prediction");
    expect(serialized).not.toContain("llm_answer");
  });
});
