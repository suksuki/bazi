import { describe, expect, it } from "vitest";
import { buildInboxCards } from "@/features/stream-board/cardBuilder";
import { buildFallbackVerdict, calculateFireEnergyAfterConflicts } from "@/features/stream-board/utils";

describe("stream-board utils", () => {
  it("calculates fire energy after zi-wu clash based on month branch", () => {
    expect(
      calculateFireEnergyAfterConflicts(
        {
          year: { stem: "庚", branch: "午" },
          month: { stem: "甲", branch: "子" },
          day: { stem: "丙", branch: "寅" },
          hour: { stem: "辛", branch: "酉" },
        },
        ["子午冲"],
      ),
    ).toBe(40);

    expect(
      calculateFireEnergyAfterConflicts(
        {
          year: { stem: "庚", branch: "午" },
          month: { stem: "甲", branch: "辰" },
          day: { stem: "丙", branch: "寅" },
          hour: { stem: "辛", branch: "酉" },
        },
        ["子午冲"],
      ),
    ).toBe(55);
  });

  it("builds cards from detected conflicts, llm observations, and auditor proposals", () => {
    const cards = buildInboxCards({
      metadata: {
        version: "1",
        pillars: null,
        flow_state: "ready",
        notes: "",
        conflict_matrix: { points: [{ kind: "clash", positions: ["year_branch"], detail: "子午冲" }] },
      },
      firstPromptText: "第一句。第二句。第三句。",
      auditorProposalCards: [
        {
          id: "proposal-1",
          title: "参数校准",
          markdown: "建议修正",
          proposal: { param_key: "CF_FLOATING_DECAY", sql_patch: "update ..." },
        },
      ],
      resolvedCardIds: ["llm-observe-1"],
      lang: "ZH",
      t: (text) => text,
    });

    expect(cards.map((card) => card.id)).toEqual(["proposal-1", "conflict-0-子午冲", "llm-observe-0", "llm-observe-2"]);
  });

  it("returns a stable fallback verdict payload", () => {
    const verdict = buildFallbackVerdict(["子午冲"]);
    expect(verdict.body).toContain("子午冲");
    expect(verdict.changeLog.text_diff_hint).toContain("Fallback");
    expect(verdict.logicalEvidence).toEqual([]);
  });
});
