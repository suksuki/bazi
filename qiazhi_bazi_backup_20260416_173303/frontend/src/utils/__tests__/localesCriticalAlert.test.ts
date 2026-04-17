import { describe, expect, it } from "vitest";
import { STATIC_I18N } from "@/constants/locales";
import { formatShadowPreviewTemplate } from "@/utils/shadowPreviewI18n";

describe("EN · CRITICAL 预警帮助文案", () => {
  it("STATIC_I18N 含 critical.alert.help 且为英文说明", () => {
    const en = STATIC_I18N.EN?.["critical.alert.help"] ?? "";
    expect(en.length).toBeGreaterThan(10);
    expect(en).toMatch(/Structural conflict/i);
    expect(en).not.toMatch(/[\u4e00-\u9fff]/);
  });

  it("占位符插值在 EN 下稳定（shadow 模板管线）", () => {
    const s = formatShadowPreviewTemplate("EN", "流年 {liu} · 大运 {dy}", { liu: "甲子", dy: "乙丑" });
    expect(s).toContain("甲子");
    expect(s).toContain("乙丑");
  });
});
