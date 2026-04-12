import { describe, expect, it } from "vitest";
import { buildFullRecalcInputBundle, physicsTensorFingerprint, stableStringifyForHash } from "../physicsTensorFingerprint";

describe("stableStringifyForHash", () => {
  it("sorts object keys so different declaration order yields same string", () => {
    const a = { z: 1, a: 2 };
    const b = { a: 2, z: 1 };
    expect(stableStringifyForHash(a)).toBe(stableStringifyForHash(b));
  });

  it("handles nested objects and arrays", () => {
    const x = { m: [{ b: 2, a: 1 }] };
    expect(stableStringifyForHash(x)).toContain('"a"');
  });
});

describe("buildFullRecalcInputBundle", () => {
  it("treats labConfig with different key order as the same bundle", () => {
    const lab1 = { z: 1, a: 2 };
    const lab2 = { a: 2, z: 1 };
    const b1 = buildFullRecalcInputBundle({
      seedSignature: "{}",
      paramSignature: "{}",
      referenceYear: 2026,
      labConfig: lab1,
    });
    const b2 = buildFullRecalcInputBundle({
      seedSignature: "{}",
      paramSignature: "{}",
      referenceYear: 2026,
      labConfig: lab2,
    });
    expect(b1).toBe(b2);
  });
});

describe("physicsTensorFingerprint", () => {
  it("returns empty string for null/undefined/primitive", () => {
    expect(physicsTensorFingerprint(null)).toBe("");
    expect(physicsTensorFingerprint(undefined)).toBe("");
    expect(physicsTensorFingerprint("x")).toBe("");
    expect(physicsTensorFingerprint(42)).toBe("");
  });

  it("is stable for same semantic tensor with different key order", () => {
    const t1 = { confidence: 0.5, meta: { b: 1, a: 2 } };
    const t2 = { meta: { a: 2, b: 1 }, confidence: 0.5 };
    expect(physicsTensorFingerprint(t1)).toBe(physicsTensorFingerprint(t2));
  });

  it("changes when a nested value changes", () => {
    const t1 = { confidence: 0.5, meta: { x: 1 } };
    const t2 = { confidence: 0.5, meta: { x: 2 } };
    expect(physicsTensorFingerprint(t1)).not.toBe(physicsTensorFingerprint(t2));
  });

  it("returns 8-char lowercase hex", () => {
    const fp = physicsTensorFingerprint({ a: 1 });
    expect(fp).toMatch(/^[0-9a-f]{8}$/);
  });
});
