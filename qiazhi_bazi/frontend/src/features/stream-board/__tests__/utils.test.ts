import { describe, expect, it } from "vitest";
import {
  buildInboxCards,
  expandResolvedInboxIds,
  normalizeBranchToken,
  stableSanheInboxCardId,
} from "@/features/stream-board/cardBuilder";
import { mergeDecisionIdsPreferLocal } from "@/features/stream-board/controller/streamBoardPure";
import { buildFallbackVerdict, calculateFireEnergyAfterConflicts } from "@/features/stream-board/utils";

describe("normalizeBranchToken / stableSanheInboxCardId", () => {
  it("trims ideographic space around branch chars", () => {
    expect(normalizeBranchToken("\u3000丑\u3000")).toBe("丑");
  });
  it("stable sanhe id is stable under NFKC-equivalent branch spellings when applicable", () => {
    expect(stableSanheInboxCardId(["丑", "巳", "酉"])).toMatch(/^inbox-sanhe-/);
  });
});

describe("mergeDecisionIdsPreferLocal", () => {
  it("keeps local ids when snapshot omits them (stale hydrate)", () => {
    expect(mergeDecisionIdsPreferLocal(["inbox-sanhe-丑巳酉"], [])).toEqual(["inbox-sanhe-丑巳酉"]);
  });
  it("merges when snapshot is a superset of local", () => {
    expect(mergeDecisionIdsPreferLocal(["a"], ["a", "b"])).toEqual(["a", "b"]);
  });
});

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
    const idx = cards.findIndex((c) => c.id === "inbox-pattern-sovereignty");
    expect(idx).toBeGreaterThanOrEqual(0);
    const pc = cards[idx];
    expect(pc?.skillId).toBe("PATTERN_SOVEREIGNTY");
    expect(pc?.sovereigntyMark).toBe("PATTERN_SOVEREIGNTY");
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

  it("hides sanhe card when decision_journal records semantic suppress without selection/resolved", () => {
    const physicsTensor = {
      plugin_outputs: {
        "sys.core.physics": {
          payload: {
            sanhe_clusters: [{ branches: ["丑", "巳", "酉"], energy_vault_status: "AGGREGATED", nodes: [] }],
          },
        },
      },
    };
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
      decisionSelectionIds: [],
      decisionJournal: [
        {
          ts: 1,
          action: "suppress_inbox",
          branch_set_key: "丑巳酉",
          inbox_card_id: "inbox-sanhe-丑巳酉",
        },
      ],
      t: (text) => text,
      physicsTensor,
    });
    expect(cards.some((c) => c.id === "inbox-sanhe-丑巳酉")).toBe(false);
  });

  it("hides inbox card ids listed in decisionSelectionIds without waiting for resolved_card_ids", () => {
    const physicsTensor = {
      plugin_outputs: {
        "sys.core.physics": {
          payload: {
            sanhe_clusters: [{ branches: ["丑", "巳", "酉"], energy_vault_status: "AGGREGATED", nodes: [] }],
          },
        },
      },
    };
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
      decisionSelectionIds: ["inbox-sanhe-丑巳酉"],
      t: (text) => text,
      physicsTensor,
    });
    expect(cards.some((c) => c.id === "inbox-sanhe-丑巳酉")).toBe(false);
  });

  it("prepends L1_STRUCTURE sanhe cards from physics_tensor even when inbox gate is closed", () => {
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
      physicsTensor: {
        plugin_outputs: {
          "sys.core.physics": {
            verdict: "三合",
            evidence: [],
            confidence_score: 0.95,
            payload: {
              sanhe_clusters: [
                {
                  branches: ["丑", "巳", "酉"],
                  energy_vault_status: "AGGREGATED",
                  nodes: [
                    { pillar: "year", branch: "巳" },
                    { pillar: "day", branch: "丑" },
                    { pillar: "hour", branch: "酉" },
                  ],
                },
              ],
            },
          },
        },
      },
    });
    expect(cards[0]?.id).toBe("inbox-sanhe-丑巳酉");
    expect(cards[0]?.cardType).toBe("L1_STRUCTURE");
    expect(cards[0]?.skillId).toBe("l1_branch_sanhe");
    expect(cards[0]?.pluginAuditAnchorId).toBe("sys.core.physics");
    expect(cards.some((c) => c.id === "fallback-deep-scan")).toBe(true);
  });

  it("stable sanhe id is independent of branch order in payload", () => {
    expect(stableSanheInboxCardId(["丑", "巳", "酉"])).toBe(stableSanheInboxCardId(["酉", "丑", "巳"]));
  });

  it("expandResolvedInboxIds maps legacy index id to stable id for filtering", () => {
    const pt = {
      plugin_outputs: {
        "sys.core.physics": {
          payload: {
            sanhe_clusters: [{ branches: ["丑", "巳", "酉"], energy_vault_status: "X", nodes: [] }],
          },
        },
      },
    } as Record<string, unknown>;
    const s = expandResolvedInboxIds(["inbox-sanhe-0"], pt);
    expect(s.has("inbox-sanhe-0")).toBe(true);
    expect(s.has("inbox-sanhe-丑巳酉")).toBe(true);
  });

  it("hides sanhe card when confirmed_verdicts carries suppressed_inbox_card_ids", () => {
    const physicsTensor = {
      plugin_outputs: {
        "sys.core.physics": {
          payload: {
            sanhe_clusters: [{ branches: ["丑", "巳", "酉"], energy_vault_status: "AGGREGATED", nodes: [] }],
          },
        },
      },
    };
    const cards = buildInboxCards({
      metadata: {
        version: "1",
        pillars: null,
        flow_state: "ready",
        notes: "",
        conflict_matrix: { points: [] },
        history_context: {
          confirmed_verdicts: [
            {
              verdict_id: "v1",
              body_excerpt: "",
              confirmed_at: "2026-01-01",
              source_metadata_hash: "h",
              evidence_refs: [],
              suppressed_inbox_card_ids: ["inbox-sanhe-丑巳酉"],
            },
          ],
        },
      },
      firstPromptText: "",
      auditorProposalCards: [],
      resolvedCardIds: [],
      t: (text) => text,
      physicsTensor,
    });
    expect(cards.some((c) => c.id === "inbox-sanhe-丑巳酉")).toBe(false);
  });

  it("returns a stable fallback verdict payload", () => {
    const verdict = buildFallbackVerdict(["子午冲"]);
    expect(verdict.body).toContain("子午冲");
    expect(verdict.changeLog.text_diff_hint).toContain("Fallback");
    expect(verdict.logicalEvidence).toEqual([]);
  });
});
