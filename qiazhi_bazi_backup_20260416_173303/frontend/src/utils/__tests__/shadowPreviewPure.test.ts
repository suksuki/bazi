import { describe, expect, it } from "vitest";
import type { Lang } from "@/types/bazi";
import {
  interpolateNamedPlaceholders,
  lookupLocalizedPhrase,
  resolveTemplateBaseString,
  type StaticI18nTable,
} from "@/utils/shadowPreviewPure";

const miniTable: StaticI18nTable = {
  ZH: { greet: "你好 {name}", whole: "中文整句" },
  EN: { greet: "Hello {name}", whole: "EN phrase for same key" },
};

describe("interpolateNamedPlaceholders", () => {
  it("leaves template unchanged when params missing", () => {
    expect(interpolateNamedPlaceholders("a{b}c")).toBe("a{b}c");
  });
  it("replaces multiple occurrences and braces", () => {
    expect(interpolateNamedPlaceholders("{a}+{a}", { a: "1" })).toBe("1+1");
  });
});

describe("resolveTemplateBaseString", () => {
  it("falls back ZH then key", () => {
    expect(resolveTemplateBaseString(miniTable, "EN" as Lang, "greet")).toBe("Hello {name}");
    expect(resolveTemplateBaseString(miniTable, "KO" as Lang, "greet")).toBe("你好 {name}");
    expect(resolveTemplateBaseString(miniTable, "KO" as Lang, "missing")).toBe("missing");
  });
});

describe("lookupLocalizedPhrase", () => {
  it("maps whole-phrase key per lang", () => {
    expect(lookupLocalizedPhrase(miniTable, "EN" as Lang, "whole")).toBe("EN phrase for same key");
    expect(lookupLocalizedPhrase(miniTable, "ZH" as Lang, "whole")).toBe("中文整句");
  });
});
