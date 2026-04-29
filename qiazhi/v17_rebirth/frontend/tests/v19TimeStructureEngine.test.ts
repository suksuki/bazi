import { describe, expect, it } from "vitest";
import type { ChartStructureOk, EarthlyBranch, PillarName } from "../lib/v19/chartStructureTypes";
import { deriveFlowYear } from "../lib/v19/timeStructureEngine";

describe("V19 P4 time structure engine", () => {
  it("derives flow year pillar and structural relations without meaning fields", () => {
    const chart = chartWithBranches({
      year: "亥",
      month: "申",
      day: "酉",
      hour: "丑",
    });

    const flowYear = deriveFlowYear(chart, 2025);

    expect(flowYear).toEqual({
      year: 2025,
      pillar: { stem: "乙", branch: "巳" },
      relations_with_natal: {
        clashes: ["巳亥"],
        combinations: ["巳申", "巳酉丑"],
      },
    });
    expect(JSON.stringify(flowYear)).not.toContain("meaning");
    expect(JSON.stringify(flowYear)).not.toContain("summary");
    expect(JSON.stringify(flowYear)).not.toContain("conclusion");
  });

  it("changes pillar when selected year changes", () => {
    const chart = chartWithBranches({
      year: "子",
      month: "丑",
      day: "寅",
      hour: "卯",
    });

    expect(deriveFlowYear(chart, 2024).pillar).toEqual({ stem: "甲", branch: "辰" });
    expect(deriveFlowYear(chart, 2025).pillar).toEqual({ stem: "乙", branch: "巳" });
  });
});

function chartWithBranches(branches: Record<PillarName, EarthlyBranch>): ChartStructureOk {
  return {
    status: "ok",
    pillars: {
      year: { branch: branches.year },
      month: { branch: branches.month },
      day: { branch: branches.day },
      hour: { branch: branches.hour },
    },
  } as ChartStructureOk;
}
