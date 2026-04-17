import { describe, expect, it } from "vitest";

import {
  augmentDiagnosisWithMangpaiManifest,
  inferMangpaiChipTemplateKey,
  MANGPAI_CHIP_MANIFEST,
  mangpaiChipSemanticLine,
  semanticAnchorForBlindWorkVectorItem,
} from "./mangpaiChipManifest";

describe("mangpaiChipManifest", () => {
  it("exposes semantic_templates as given contract", () => {
    expect(MANGPAI_CHIP_MANIFEST.id).toBe("mp_v1");
    expect(MANGPAI_CHIP_MANIFEST.semantic_templates.tomb_locked).toContain("墓库");
  });

  it("mangpaiChipSemanticLine resolves known keys", () => {
    expect(mangpaiChipSemanticLine("pierce_active")).toContain("六穿");
    expect(mangpaiChipSemanticLine("unknown")).toBeUndefined();
  });

  it("inferMangpaiChipTemplateKey maps chip log heuristics", () => {
    expect(inferMangpaiChipTemplateKey("[MANGPAI_CHIP] 墓库闭锁")).toBe("tomb_locked");
    expect(inferMangpaiChipTemplateKey("[MANGPAI_CHIP] 发现穿局")).toBe("pierce_active");
    expect(inferMangpaiChipTemplateKey("宾主矢量")).toBe("gain_positive");
  });

  it("augmentDiagnosisWithMangpaiManifest prepends chip-derived prefix once", () => {
    const logs = ["[MANGPAI_CHIP] 墓库闭锁"];
    const out = augmentDiagnosisWithMangpaiManifest("日主偏弱，宜抑扶。", logs);
    expect(out.startsWith("墓库势能闭锁")).toBe(true);
    expect(out).toContain("日主偏弱");
    expect(augmentDiagnosisWithMangpaiManifest(out, logs)).toBe(out);
  });

  it("semanticAnchorForBlindWorkVectorItem maps type/detail", () => {
    expect(semanticAnchorForBlindWorkVectorItem({ type: "穿", detail: "子未相穿" })).toContain("六穿");
  });
});
