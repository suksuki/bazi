import { describe, expect, it } from "vitest";
import {
  buildStructuralPreviewHintForCard,
  snapshotPatternProfileForStructuralPreview,
} from "@/features/stream-board/controller/structuralPreviewHint";
import type { InboxCard } from "@/features/stream-board/models";

describe("buildStructuralPreviewHintForCard", () => {
  it("maps L1_STRUCTURE sanhe card", () => {
    const card: InboxCard = {
      id: "inbox-sanhe-午寅戌",
      title: "地支三合局锁定",
      markdown: "x",
      displayText: "寅午戌火局 · AGGREGATED",
      cardType: "L1_STRUCTURE",
    };
    const h = buildStructuralPreviewHintForCard(card);
    expect(h?.kind).toBe("L1_STRUCTURE");
    expect(h?.label).toContain("火局");
  });

  it("returns null for plain conflict card", () => {
    const card: InboxCard = { id: "llm-observe-0", title: "x", markdown: "y", cardType: "conflict" };
    expect(buildStructuralPreviewHintForCard(card)).toBeNull();
  });

  it("snapshots pattern_profile from physics tensor", () => {
    const snap = snapshotPatternProfileForStructuralPreview({
      meta: { pattern_profile: { pattern_kind: "cong_fire", pattern_name_zh: "从火格（能量集中度）" } },
    });
    expect(snap.baseline_pattern_kind).toBe("cong_fire");
    expect(snap.baseline_pattern_name_zh).toContain("从火格");
  });
});
