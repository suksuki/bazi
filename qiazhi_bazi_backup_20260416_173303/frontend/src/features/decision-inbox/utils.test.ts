import { describe, expect, it } from "vitest";

import {
  getCardElement,
  getCardLabel,
  getEvidenceTone,
  isAuditorProposal,
  isVerdictDeity,
  pruneSelectedIds,
  splitVerdictLine,
} from "./utils";

describe("decision inbox utils", () => {
  it("prunes removed card selections", () => {
    expect(pruneSelectedIds({ a: true, b: false }, ["b", "c"])).toEqual({ b: false });
  });

  it("extracts labels and proposal state", () => {
    const card = { title: "默认标题", conflictDetail: "子午冲", displayText: "寅木冲突" };
    expect(getCardLabel(card)).toBe("寅木冲突");
    expect(getCardElement(card)).toBe("wood");
    expect(isAuditorProposal("auditor-proposal")).toBe(true);
    expect(isAuditorProposal("conflict")).toBe(false);
  });

  it("splits verdict lines and recognizes deity tokens", () => {
    const parts = splitVerdictLine("比肩转弱，正官抬头");
    expect(parts).toContain("比肩");
    expect(parts).toContain("正官");
    expect(isVerdictDeity("比肩")).toBe(true);
    expect(isVerdictDeity("普通文本")).toBe(false);
  });

  it("assigns evidence tone from absolute energy", () => {
    expect(getEvidenceTone("Abs=0.3")).toContain("animate-pulse");
    expect(getEvidenceTone("Abs=3.2")).toContain("sky");
  });
});
