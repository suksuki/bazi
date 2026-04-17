import { describe, expect, it } from "vitest";
import { inferPreviewHealSegmentIndices } from "@/utils/energyFlowPreviewHeal";

describe("inferPreviewHealSegmentIndices", () => {
  it("returns empty when no deltas", () => {
    expect(
      inferPreviewHealSegmentIndices(
        { segments: [{ from: "water", to: "wood", state: "BROKEN" }], break_indices: [0] },
        {},
      ).size,
    ).toBe(0);
  });

  it("marks water→wood broken segment when 印类 Δ% 合计超过阈值", () => {
    const audit = {
      segments: [
        { from: "water", to: "wood", state: "OK" },
        { from: "water", to: "wood", state: "BROKEN" },
      ],
      break_indices: [1],
    };
    const deltas = { 正印: 0.08, 偏印: 0.05 };
    const s = inferPreviewHealSegmentIndices(audit, deltas);
    expect(s.has(1)).toBe(true);
    expect(s.has(0)).toBe(false);
  });
});
