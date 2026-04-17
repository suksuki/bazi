import { describe, expect, it } from "vitest";
import { formatShadowPreviewTemplate, resolveShadowPreviewPatternAlert } from "@/utils/shadowPreviewI18n";

describe("shadowPreviewI18n", () => {
  it("interpolates critical template in EN", () => {
    const s = formatShadowPreviewTemplate("EN", "shadowPreview.pattern.critical", {
      prev_tag: "Test",
      tail: "",
    });
    expect(s).toContain("Critical structure dissolution");
    expect(s).toContain("Test");
  });

  it("joins pattern i18n parts", () => {
    const out = resolveShadowPreviewPatternAlert("EN", "", {
      parts: [
        { template: "shadowPreview.pattern.l1Intro", params: {} },
        { template: "shadowPreview.pattern.l1Label", params: { label: "X" } },
      ],
    });
    expect(out).toContain("leap risk");
    expect(out).toContain("X");
  });
});
