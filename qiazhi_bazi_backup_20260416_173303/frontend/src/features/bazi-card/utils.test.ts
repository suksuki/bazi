import { describe, expect, it } from "vitest";

import { branchInConflict, computeBranchEnergy, computeRootState, deityAbbr, splitGanZhi } from "./utils";

describe("bazi card utils", () => {
  it("splits gan-zhi safely", () => {
    expect(splitGanZhi("甲子")).toEqual({ stem: "甲", branch: "子" });
    expect(splitGanZhi("子")).toEqual({ stem: "?", branch: "子" });
  });

  it("detects branch conflicts", () => {
    expect(branchInConflict("子", [{ kind: "clash", positions: ["year_branch"], detail: "子午冲" }])).toBe(true);
  });

  it("computes root state and branch energy", () => {
    const rootState = computeRootState({
      dayStem: "甲",
      pillars: {
        year: { branch: "子" },
        month: { branch: "午" },
        day: { branch: "寅" },
        hour: { branch: "酉" },
      },
      timeline: { dayun: "庚申", liunian: "丙午", reference_year: 2026 },
      confirmedConflictDetails: ["子午冲"],
      deityScores: { 比肩: 10, 劫财: 5 },
      deityEnergyAxes: { 比肩: { absolute_energy: 0.4 }, 劫财: { absolute_energy: 0.1 } },
    });
    expect(rootState.roots).toContain("寅");
    expect(rootState.hasRootInNatal).toBe(true);
    expect(rootState.hasBingWuYear).toBe(true);

    const energy = computeBranchEnergy({
      pillars: {
        year: { branch: "子", energy_value: 100 },
        month: { branch: "午", energy_value: 100 },
        day: { branch: "寅", energy_value: 100 },
        hour: { branch: "酉", energy_value: 100 },
      },
      points: [{ kind: "clash", positions: ["year_branch", "month_branch"], detail: "子午冲" }],
      confirmedConflictDetails: ["子午冲"],
    });
    expect(energy.year_branch).toBe(70);
    expect(energy.month_branch).toBe(40);
    expect(deityAbbr("甲", "甲")).toBe("比");
  });
});
