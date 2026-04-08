import { describe, expect, it } from "vitest";

import { formatVal, getAuditorBriefingState } from "./utils";

describe("auditor briefing utils", () => {
  it("formats missing numeric values safely", () => {
    expect(formatVal(undefined)).toBe("—");
    expect(formatVal(0.123)).toBe("0.12");
  });

  it("derives briefing UI state", () => {
    const state = getAuditorBriefingState({
      logicProposal: { param_key: "CF_FLOATING_DECAY", suggested_value: 0.2, sql_patch: "UPDATE ..." },
      currentParams: { CF_FLOATING_DECAY: 0.1 },
      alignmentScore: 70,
      structuredHit: true,
      autoConverted: false,
      alreadyAdded: false,
    });
    expect(state.key).toBe("CF_FLOATING_DECAY");
    expect(state.currentValue).toBe(0.1);
    expect(state.nextValue).toBe(0.2);
    expect(state.hasSqlPatch).toBe(true);
    expect(state.aligned).toBe(true);
    expect(state.disableByState).toBe(false);
  });
});
