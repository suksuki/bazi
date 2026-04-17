import { describe, expect, it } from "vitest";
import {
  coerceVerdictDisplayBody,
  extractQiazhiVerdictFingerprintComment,
  normalizeH3HeadingCore,
  stripLeadingH3PrefixIfRedundant,
  ensureVerdictFingerprintSuffix,
} from "./verdictBodyStream";

describe("normalizeH3HeadingCore", () => {
  it("strips trailing parenthetical suffixes", () => {
    expect(normalizeH3HeadingCore("### 核心气象 (物理预判)")).toBe("核心气象");
    expect(normalizeH3HeadingCore("### 裁决共识（系统预判）")).toBe("裁决共识");
  });
});

describe("stripLeadingH3PrefixIfRedundant", () => {
  it("aligns when LLM headings differ only by bracket suffix", () => {
    const sk = "### 核心气象 (物理预判)\n### 裁决共识\n";
    const full = "### 核心气象\n### 裁决共识\n\n正文第一段";
    const { prefix, rest } = stripLeadingH3PrefixIfRedundant(sk, full);
    expect(prefix).toBe("### 核心气象 (物理预判)\n### 裁决共识");
    expect(rest.trim()).toBe("正文第一段");
  });

  it("falls back to empty prefix when no heading match", () => {
    const sk = "### 完全不同\n";
    const full = "### 另一套\n\nx";
    const { prefix, rest } = stripLeadingH3PrefixIfRedundant(sk, full);
    expect(prefix).toBe("");
    expect(rest).toContain("### 另一套");
  });
});

describe("coerceVerdictDisplayBody", () => {
  it("extracts verdict_body from valid JSON", () => {
    const raw = JSON.stringify({ verdict_body: "### A\n正文", x: 1 });
    expect(coerceVerdictDisplayBody(raw)).toBe("### A\n正文");
  });

  it("recovers verdict_body from slightly broken JSON via regex", () => {
    const raw = '{"verdict_body":"### 核心\\n判词", "trailing": broken';
    expect(coerceVerdictDisplayBody(raw)).toContain("核心");
  });
});

describe("fingerprint helpers", () => {
  it("extracts and appends fingerprint comment", () => {
    const fp = "<!--qiazhi-fingerprint:v1 abc==-->";
    const raw = `### A\nhello\n\n${fp}`;
    expect(extractQiazhiVerdictFingerprintComment(raw)).toBe(fp);
    const body = "### A\nhello";
    expect(ensureVerdictFingerprintSuffix(body, fp).trimEnd().endsWith(fp)).toBe(true);
    expect(ensureVerdictFingerprintSuffix(`${body}\n\n${fp}`, fp)).toBe(`${body}\n\n${fp}`);
  });
});
