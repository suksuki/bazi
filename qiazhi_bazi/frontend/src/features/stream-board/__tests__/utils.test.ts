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
      t: (text) => text,
    });

    expect(cards.map((card) => card.id)).toEqual(["proposal-1", "llm-observe-0", "llm-observe-2"]);
  });

  it("prepends PATTERN_SOVEREIGNTY card when从格主权与伤官见官同时成立", () => {
    const cards = buildInboxCards({
      metadata: {
        version: "1",
        pillars: null,
        flow_state: "ready",
        notes: "",
        conflict_matrix: { points: [] },
      },
      firstPromptText: "",
      auditorProposalCards: [],
      resolvedCardIds: [],
      t: (text) => text,
      patternProfile: {
        sovereignty_priority: true,
        xi_ji_reversal_lines: ["测试：喜忌反转说明"],
      },
      l1JunctionFlags: { SHANG_GUAN_JIAN_GUAN: true },
    });
    expect(cards[0]?.id).toBe("inbox-pattern-sovereignty");
    expect(cards[0]?.skillId).toBe("PATTERN_SOVEREIGNTY");
    expect(cards[0]?.sovereigntyMark).toBe("PATTERN_SOVEREIGNTY");
  });

  it("suppresses LLM observation cards when decision signal-to-noise gate is closed", () => {
    const cards = buildInboxCards({
      metadata: {
        version: "1",
        pillars: null,
        flow_state: "ready",
        notes: "",
        conflict_matrix: { points: [] },
      },
      firstPromptText: "第一句。第二句。",
      auditorProposalCards: [],
      resolvedCardIds: [],
      t: (text) => text,
      decisionSignalToNoise: { inbox_conflict_cards_eligible: false },
    });
    expect(cards.map((c) => c.id)).toEqual(["fallback-deep-scan"]);
  });

  it("returns a stable fallback verdict payload", () => {
    const verdict = buildFallbackVerdict(["子午冲"]);
    expect(verdict.body).toContain("子午冲");
    expect(verdict.changeLog.text_diff_hint).toContain("Fallback");
    expect(verdict.logicalEvidence).toEqual([]);
  });
});
