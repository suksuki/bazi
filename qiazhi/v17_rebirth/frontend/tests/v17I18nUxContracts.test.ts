import { describe, expect, it } from "vitest";
import { t, type AppLanguage } from "../lib/i18n";

const LANGUAGES: AppLanguage[] = ["zh", "en", "ko"];

describe("V17 UX i18n contracts", () => {
  it("keeps primary oracle actions explicit in every language", () => {
    const keys = [
      "oracle.action.show_verdict",
      "oracle.action.show_verdict.loading",
      "oracle.action.retry",
      "oracle.action.retry.title",
    ];

    for (const lang of LANGUAGES) {
      for (const key of keys) {
        const value = t(lang, key);
        expect(value).not.toBe(key);
        expect(value.trim().length).toBeGreaterThan(0);
      }
    }

    expect(t("zh", "oracle.action.show_verdict")).toBe("掐指一算");
    expect(t("zh", "oracle.action.show_verdict.loading")).toBe("正在掐指一算");
    expect(t("zh", "oracle.action.retry")).toBe("返回填写八字");
  });

  it("keeps auth entry copy localized and not boilerplate", () => {
    const keys = [
      "auth.entry.hero",
      "auth.entry.hero_subtitle",
      "auth.entry.heading.login",
      "auth.entry.heading.register",
      "auth.entry.subtitle.login",
      "auth.entry.subtitle.register",
      "auth.error.required",
    ];

    for (const lang of LANGUAGES) {
      for (const key of keys) {
        const value = t(lang, key);
        expect(value).not.toBe(key);
        expect(value.trim().length).toBeGreaterThan(0);
      }
    }

    expect(t("zh", "auth.entry.heading.login")).toContain("欢迎");
    expect(t("en", "auth.entry.heading.login")).toContain("Welcome");
    expect(t("ko", "auth.entry.heading.login")).toContain("환영");
  });

  it("keeps concise verdict prompts visible to the UI layer", () => {
    expect(t("zh", "verdict.prompt.generate")).toContain("精炼");
    expect(t("en", "verdict.prompt.generate")).toContain("concise");
    expect(t("ko", "verdict.prompt.generate")).toContain("간결");
  });
});
