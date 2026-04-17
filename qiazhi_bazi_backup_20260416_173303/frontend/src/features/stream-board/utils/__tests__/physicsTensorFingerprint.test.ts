import { describe, expect, it } from "vitest";
import {
  buildFullRecalcInputBundle,
  extractPhysicsTensorConvergenceCore,
  physicsTensorFingerprint,
  stableStringifyForHash,
} from "../physicsTensorFingerprint";

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

describe("extractPhysicsTensorConvergenceCore", () => {
  it("drops meta keys that are not physics-convergence allowlist", () => {
    const t = {
      normalized: { wood: 1 },
      meta: { diagnosis: "x", causal_reasoning: "y", solar_term: "立春" },
    };
    const c = extractPhysicsTensorConvergenceCore(t);
    expect(c?.meta).toEqual({ solar_term: "立春" });
    expect((c?.meta as Record<string, unknown>).diagnosis).toBeUndefined();
  });
});

describe("physicsTensorFingerprint", () => {
  it("returns empty string for null/undefined/primitive", () => {
    expect(physicsTensorFingerprint(null)).toBe("");
    expect(physicsTensorFingerprint(undefined)).toBe("");
    expect(physicsTensorFingerprint("x")).toBe("");
    expect(physicsTensorFingerprint(42)).toBe("");
  });

  it("returns empty when tensor has no convergence-relevant fields", () => {
    expect(physicsTensorFingerprint({ audit_log: { trace: "noise" } })).toBe("");
  });

  it("is stable for same semantic convergence core with different key order", () => {
    const t1 = { confidence: 0.5, normalized: { b: 1, a: 2 } };
    const t2 = { normalized: { a: 2, b: 1 }, confidence: 0.5 };
    expect(physicsTensorFingerprint(t1)).toBe(physicsTensorFingerprint(t2));
  });

  it("changes when normalized numeric value changes", () => {
    const t1 = { normalized: { x: 1 } };
    const t2 = { normalized: { x: 2 } };
    expect(physicsTensorFingerprint(t1)).not.toBe(physicsTensorFingerprint(t2));
  });

  it("ignores LLM-only meta fields when normalized is unchanged", () => {
    const t1 = {
      normalized: { wood: 1, fire: 0.5 },
      meta: { diagnosis: "版本A", causal_reasoning: "长文本A" },
    };
    const t2 = {
      normalized: { wood: 1, fire: 0.5 },
      meta: { diagnosis: "版本B", causal_reasoning: "长文本B" },
    };
    expect(physicsTensorFingerprint(t1)).toBe(physicsTensorFingerprint(t2));
  });

  it("changes when allowlisted meta field changes", () => {
    const t1 = { normalized: { wood: 1 }, meta: { solar_term: "立春" } };
    const t2 = { normalized: { wood: 1 }, meta: { solar_term: "雨水" } };
    expect(physicsTensorFingerprint(t1)).not.toBe(physicsTensorFingerprint(t2));
  });

  it("returns 8-char lowercase hex", () => {
    const fp = physicsTensorFingerprint({ normalized: { wood: 1 } });
    expect(fp).toMatch(/^[0-9a-f]{8}$/);
  });
});
